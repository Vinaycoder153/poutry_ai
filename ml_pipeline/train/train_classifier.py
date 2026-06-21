import os
import json
import time
import math
from dataclasses import dataclass

import torch
import torch.nn as nn
from torch.utils.data import Dataset, DataLoader

from PIL import Image

import torchvision
from torchvision import transforms

try:
    import albumentations as A
    from albumentations.pytorch import ToTensorV2
except Exception as e:
    A = None
    ToTensorV2 = None

import numpy as np


@dataclass
class Config:
    task: str
    dataset_root_dir: str
    class_names: list
    image_exts: list
    val_ratio: float
    seed: int

    backbone: str
    pretrained: bool
    num_classes: int

    batch_size: int
    num_epochs: int
    lr: float
    weight_decay: float
    num_workers: int
    early_stopping_patience: int
    label_smoothing: float

    input_size: int
    resize_shorter_side: int
    crop_size: int

    rotation_deg: int
    hflip_prob: float
    vflip_prob: float
    random_erasing_prob: float
    color_jitter: float
    noise_injection_prob: float

    cutmix_alpha: float
    mixup_alpha: float

    tensorboard_dir: str
    checkpoints_dir: str


def set_seed(seed: int):
    import random

    random.seed(seed)
    np.random.seed(seed)
    torch.manual_seed(seed)
    torch.cuda.manual_seed_all(seed)


def list_images(root_dir, class_names, image_exts):
    exts = tuple([e.lower() for e in image_exts])
    items = []
    for idx, cls in enumerate(class_names):
        cdir = os.path.join(root_dir, cls)
        for fn in os.listdir(cdir):
            if fn.lower().endswith(exts):
                items.append((os.path.join(cdir, fn), idx, cls))
    return items


def stratified_split(items, val_ratio: float, seed: int):
    # simple stratified split by class
    rng = np.random.default_rng(seed)
    by_class = {}
    for path, y, cls in items:
        by_class.setdefault(y, []).append((path, y, cls))

    train, val = [], []
    for y, arr in by_class.items():
        arr = np.array(arr, dtype=object)
        idx = np.arange(len(arr))
        rng.shuffle(idx)
        n_val = int(round(len(arr) * val_ratio))
        val_idx = idx[:n_val]
        tr_idx = idx[n_val:]
        val.extend(arr[val_idx].tolist())
        train.extend(arr[tr_idx].tolist())
    return train, val


class ImageFolderDataset(Dataset):
    def __init__(self, items, transform=None):
        self.items = items
        self.transform = transform

    def __len__(self):
        return len(self.items)

    def __getitem__(self, idx):
        path, y, cls = self.items[idx]
        img = Image.open(path).convert('RGB')
        if self.transform is not None:
            img = self.transform(img)
        return img, y


def build_backbone(backbone: str, num_classes: int, pretrained: bool):
    if backbone.lower() == 'resnet50':
        model = torchvision.models.resnet50(weights='DEFAULT' if pretrained else None)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
        return model
    if backbone.lower() == 'efficientnet_b0':
        model = torchvision.models.efficientnet_b0(weights='DEFAULT' if pretrained else None)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
        return model
    if backbone.lower() == 'densenet121':
        model = torchvision.models.densenet121(weights='DEFAULT' if pretrained else None)
        model.classifier = nn.Linear(model.classifier.in_features, num_classes)
        return model
    # Fallback
    model = torchvision.models.resnet50(weights='DEFAULT' if pretrained else None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model


def get_transforms(cfg: Config):
    # Prefer Albumentations (requested), but fall back to torchvision if unavailable.
    if A is not None:
        train_tf = A.Compose(
            [
                A.SmallestMaxSize(cfg.resize_shorter_side),
                A.CenterCrop(cfg.crop_size, cfg.crop_size),
                A.Rotate(limit=cfg.rotation_deg, p=0.5),
                A.HorizontalFlip(p=cfg.hflip_prob),
                A.VerticalFlip(p=cfg.vflip_prob),
                A.ColorJitter(brightness=cfg.color_jitter, contrast=cfg.color_jitter, saturation=cfg.color_jitter, hue=0.0, p=0.8),
                A.GaussNoise(var_limit=(10.0, 50.0), p=cfg.noise_injection_prob),
                A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
                ToTensorV2(),
            ]
        )
        val_tf = A.Compose(
            [
                A.SmallestMaxSize(cfg.resize_shorter_side),
                A.CenterCrop(cfg.crop_size, cfg.crop_size),
                A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
                ToTensorV2(),
            ]
        )

        def train_wrap(pil_img):
            arr = np.array(pil_img)
            out = train_tf(image=arr)
            return out['image']

        def val_wrap(pil_img):
            arr = np.array(pil_img)
            out = val_tf(image=arr)
            return out['image']

        return train_wrap, val_wrap

    # torchvision fallback (no Albumentations)
    train_tf = transforms.Compose(
        [
            transforms.Resize(cfg.resize_shorter_side),
            transforms.CenterCrop(cfg.crop_size),
            transforms.RandomRotation(cfg.rotation_deg),
            transforms.RandomHorizontalFlip(p=cfg.hflip_prob),
            transforms.ColorJitter(brightness=cfg.color_jitter, contrast=cfg.color_jitter, saturation=cfg.color_jitter),
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ]
    )
    val_tf = transforms.Compose(
        [
            transforms.Resize(cfg.resize_shorter_side),
            transforms.CenterCrop(cfg.crop_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ]
    )
    return train_tf, val_tf


def mixup_cutmix(inputs, targets, num_classes, cutmix_alpha=1.0, mixup_alpha=0.2):
    # Apply either cutmix or mixup. This is batch-level augmentation.
    # Returns mixed_inputs, targets_a, targets_b, lam
    if cutmix_alpha <= 0 and mixup_alpha <= 0:
        return inputs, targets, targets, 1.0

    r = torch.rand(1).item()
    if r < 0.5 and cutmix_alpha > 0:
        # cutmix
        lam = np.random.beta(cutmix_alpha, cutmix_alpha)
        bsz, c, h, w = inputs.shape
        rand_index = torch.randperm(bsz).to(inputs.device)
        target_a = targets
        target_b = targets[rand_index]

        cut_w = int(w * math.sqrt(1 - lam))
        cut_h = int(h * math.sqrt(1 - lam))

        cx = np.random.randint(w)
        cy = np.random.randint(h)

        x1 = np.clip(cx - cut_w // 2, 0, w)
        y1 = np.clip(cy - cut_h // 2, 0, h)
        x2 = np.clip(cx + cut_w // 2, 0, w)
        y2 = np.clip(cy + cut_h // 2, 0, h)

        inputs = inputs.clone()
        inputs[:, :, y1:y2, x1:x2] = inputs[rand_index, :, y1:y2, x1:x2]

        lam_adjusted = 1 - ((x2 - x1) * (y2 - y1) / (w * h))
        return inputs, target_a, target_b, lam_adjusted

    # mixup
    if mixup_alpha <= 0:
        return inputs, targets, targets, 1.0

    lam = np.random.beta(mixup_alpha, mixup_alpha)
    bsz = inputs.size(0)
    rand_index = torch.randperm(bsz).to(inputs.device)
    target_a = targets
    target_b = targets[rand_index]
    inputs = lam * inputs + (1 - lam) * inputs[rand_index]
    return inputs, target_a, target_b, lam


def train_one_epoch(model, loader, optimizer, criterion, device, cfg: Config):
    model.train()
    running_loss = 0.0
    correct = 0
    total = 0

    for inputs, targets in loader:
        inputs = inputs.to(device)
        targets = targets.to(device)

        optimizer.zero_grad(set_to_none=True)

        inputs_mixed, targets_a, targets_b, lam = mixup_cutmix(
            inputs,
            targets,
            cfg.num_classes,
            cutmix_alpha=cfg.cutmix_alpha,
            mixup_alpha=cfg.mixup_alpha,
        )

        outputs = model(inputs_mixed)

        loss = lam * criterion(outputs, targets_a) + (1.0 - lam) * criterion(outputs, targets_b)
        loss.backward()
        optimizer.step()

        running_loss += loss.item() * inputs.size(0)

        # For accuracy, use hard labels from targets_a (approx)
        preds = outputs.argmax(dim=1)
        correct += (preds == targets).sum().item()
        total += targets.size(0)

    return {
        'loss': running_loss / max(1, total),
        'acc': correct / max(1, total),
    }


@torch.no_grad()
def validate(model, loader, criterion, device):
    model.eval()
    running_loss = 0.0
    correct = 0
    total = 0

    for inputs, targets in loader:
        inputs = inputs.to(device)
        targets = targets.to(device)
        outputs = model(inputs)
        loss = criterion(outputs, targets)

        running_loss += loss.item() * inputs.size(0)
        preds = outputs.argmax(dim=1)
        correct += (preds == targets).sum().item()
        total += targets.size(0)

    return {
        'val_loss': running_loss / max(1, total),
        'val_acc': correct / max(1, total),
    }


def save_checkpoint(state, checkpoints_dir, tag='latest'):
    os.makedirs(checkpoints_dir, exist_ok=True)
    path = os.path.join(checkpoints_dir, f'{tag}.pth')
    torch.save(state, path)
    return path


def main():
    # Load YAML manually (minimal) - avoid extra deps.
    import yaml
    from pathlib import Path

    repo_root = Path(__file__).resolve().parents[2]
    cfg_path = repo_root / 'ml_pipeline' / 'train' / 'config.yaml'

    with open(cfg_path, 'r', encoding='utf-8') as f:
        raw = yaml.safe_load(f)


    task = raw['task']
    dataset_root_dir = raw['dataset']['root_dir']
    class_names = raw['dataset']['class_names']
    image_exts = raw['dataset']['image_exts']

    val_ratio = raw['dataset']['split']['val_ratio']
    seed = raw['dataset']['split']['seed']

    backbone = raw['model']['backbone']
    pretrained = raw['model']['pretrained']
    num_classes = raw['model']['num_classes']

    training = raw['training']
    aug = raw['augmentation']

    cfg = Config(
        task=task,
        dataset_root_dir=str(repo_root / dataset_root_dir),
        class_names=class_names,
        image_exts=image_exts,
        val_ratio=val_ratio,
        seed=seed,
        backbone=backbone,
        pretrained=pretrained,
        num_classes=num_classes,
        batch_size=int(training['batch_size']),
        num_epochs=int(training['num_epochs']),
        lr=float(training['lr']),
        weight_decay=float(training['weight_decay']),
        num_workers=int(training['num_workers']),
        early_stopping_patience=int(training['early_stopping_patience']),
        label_smoothing=float(training.get('label_smoothing', 0.0)),
        input_size=int(aug['input_size']),
        resize_shorter_side=int(aug['resize_shorter_side']),
        crop_size=int(aug['crop_size']),
        rotation_deg=int(aug['rotation_deg']),
        hflip_prob=float(aug['hflip_prob']),
        vflip_prob=float(aug['vflip_prob']),
        random_erasing_prob=float(aug['random_erasing_prob']),
        color_jitter=float(aug['color_jitter']),
        noise_injection_prob=float(aug['noise_injection_prob']),
        cutmix_alpha=float(aug['cutmix_alpha']),
        mixup_alpha=float(aug['mixup_alpha']),
        tensorboard_dir=str(repo_root / raw['logging']['tensorboard_dir']),
        checkpoints_dir=str(repo_root / raw['logging']['checkpoints_dir']),
    )

    set_seed(cfg.seed)

    items = list_images(cfg.dataset_root_dir, cfg.class_names, cfg.image_exts)
    if len(items) == 0:
        raise RuntimeError(f'No images found under {cfg.dataset_root_dir}')

    train_items, val_items = stratified_split(items, cfg.val_ratio, cfg.seed)

    train_tf, val_tf = get_transforms(cfg)

    train_ds = ImageFolderDataset(train_items, transform=train_tf)
    val_ds = ImageFolderDataset(val_items, transform=val_tf)

    # Windows + Py3.14: avoid multiprocessing pickling issues with lambda/inner functions.
    # Use single-process dataloading.
    train_loader = DataLoader(train_ds, batch_size=cfg.batch_size, shuffle=True, num_workers=0, pin_memory=True)
    val_loader = DataLoader(val_ds, batch_size=cfg.batch_size, shuffle=False, num_workers=0, pin_memory=True)


    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    model = build_backbone(cfg.backbone, cfg.num_classes, cfg.pretrained)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss(label_smoothing=cfg.label_smoothing)

    optimizer = torch.optim.AdamW(model.parameters(), lr=cfg.lr, weight_decay=cfg.weight_decay)
    scheduler = torch.optim.lr_scheduler.ReduceLROnPlateau(optimizer, mode='max', patience=2, factor=0.5)

    os.makedirs(cfg.checkpoints_dir, exist_ok=True)
    writer = None
    try:
        from torch.utils.tensorboard import SummaryWriter

        writer = SummaryWriter(cfg.tensorboard_dir)
    except Exception:
        writer = None

    best_val_acc = -1.0
    best_epoch = -1
    patience = 0

    for epoch in range(cfg.num_epochs):
        t0 = time.time()
        train_metrics = train_one_epoch(model, train_loader, optimizer, criterion, device, cfg)
        val_metrics = validate(model, val_loader, criterion, device)

        val_acc = val_metrics['val_acc']
        scheduler.step(val_acc)

        if writer is not None:
            writer.add_scalar('loss/train', train_metrics['loss'], epoch)
            writer.add_scalar('acc/train', train_metrics['acc'], epoch)
            writer.add_scalar('loss/val', val_metrics['val_loss'], epoch)
            writer.add_scalar('acc/val', val_metrics['val_acc'], epoch)
            writer.add_scalar('lr', optimizer.param_groups[0]['lr'], epoch)

        improved = val_acc > best_val_acc
        if improved:
            best_val_acc = val_acc
            best_epoch = epoch
            patience = 0
            save_checkpoint(
                {
                    'epoch': epoch,
                    'model_state_dict': model.state_dict(),
                    'optimizer_state_dict': optimizer.state_dict(),
                    'best_val_acc': best_val_acc,
                    'class_names': cfg.class_names,
                    'backbone': cfg.backbone,
                    'config': raw,
                },
                cfg.checkpoints_dir,
                tag='best',
            )
        else:
            patience += 1

        # latest checkpoint every epoch
        save_checkpoint(
            {
                'epoch': epoch,
                'model_state_dict': model.state_dict(),
                'optimizer_state_dict': optimizer.state_dict(),
                'best_val_acc': best_val_acc,
                'class_names': cfg.class_names,
                'backbone': cfg.backbone,
                'config': raw,
            },
            cfg.checkpoints_dir,
            tag='latest',
        )

        dt = time.time() - t0
        print(
            f"Epoch {epoch+1}/{cfg.num_epochs} | train_loss={train_metrics['loss']:.4f} train_acc={train_metrics['acc']:.4f} "
            f"| val_loss={val_metrics['val_loss']:.4f} val_acc={val_metrics['val_acc']:.4f} | time={dt:.1f}s"
        )

        if patience >= cfg.early_stopping_patience:
            print(f'Early stopping at epoch {epoch+1}, best_val_acc={best_val_acc:.4f} (epoch {best_epoch+1})')
            break

    if writer is not None:
        writer.close()

    # Write final summary
    summary = {
        'best_val_acc': best_val_acc,
        'best_epoch': best_epoch,
        'class_names': cfg.class_names,
        'backbone': cfg.backbone,
        'checkpoints_dir': cfg.checkpoints_dir,
    }
    with open(os.path.join(cfg.checkpoints_dir, 'summary.json'), 'w', encoding='utf-8') as f:
        json.dump(summary, f, indent=2)

    print('Training complete. Summary:', summary)

    # Automatically run evaluation and export
    import sys
    import subprocess
    
    print("\nRunning evaluation on best checkpoint...")
    eval_script = repo_root / 'ml_pipeline' / 'evaluation' / 'evaluate_best.py'
    subprocess.run([sys.executable, str(eval_script)], check=True)

    print("\nExporting final model bundle...")
    export_script = repo_root / 'ml_pipeline' / 'export' / 'export_final_bundle.py'
    subprocess.run([sys.executable, str(export_script)], check=True)


if __name__ == '__main__':
    main()

