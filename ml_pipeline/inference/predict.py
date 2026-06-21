import os
import json
import numpy as np
from typing import List, Dict, Any
from pathlib import Path

import torch
import torch.nn as nn
from PIL import Image

import torchvision
from torchvision import transforms

try:
    import albumentations as A
    from albumentations.pytorch import ToTensorV2
except Exception:
    A = None
    ToTensorV2 = None


def load_config(config_path: str) -> Dict[str, Any]:
    import yaml

    with open(config_path, 'r', encoding='utf-8') as f:
        return yaml.safe_load(f)


def build_inference_transform(input_size: int, resize_shorter_side: int, crop_size: int):
    # Keep same preprocessing as validation transforms in training.
    if A is not None:
        tf = A.Compose(
            [
                A.SmallestMaxSize(resize_shorter_side),
                A.CenterCrop(crop_size, crop_size),
                A.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
                ToTensorV2(),
            ]
        )

        def run(pil_img: Image.Image):
            arr = pil_img.convert('RGB')
            out = tf(image=np.array(arr))
            return out['image']

        return run

    return transforms.Compose(
        [
            transforms.Resize(resize_shorter_side),
            transforms.CenterCrop(crop_size),
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ]
    )


def build_backbone(backbone: str, num_classes: int, pretrained: bool):
    # Must match training code.
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

    model = torchvision.models.resnet50(weights='DEFAULT' if pretrained else None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model


@torch.no_grad()
def predict_image(model: nn.Module, image: Image.Image, transform, class_names: List[str], device: str):
    model.eval()
    x = transform(image)
    if isinstance(x, torch.Tensor):
        tensor = x.unsqueeze(0).to(device)
    else:
        tensor = torch.tensor(x).unsqueeze(0).to(device)

    logits = model(tensor)
    probs = torch.softmax(logits, dim=1).squeeze(0).cpu().tolist()

    top_idx = int(torch.tensor(probs).argmax().item())
    return {
        'top_class': class_names[top_idx],
        'top_prob': probs[top_idx],
        'probs': {class_names[i]: float(probs[i]) for i in range(len(class_names))},
    }


def main():
    import argparse

    repo_root = Path(__file__).resolve().parents[2]
    parser = argparse.ArgumentParser()
    parser.add_argument('--image', required=True)
    parser.add_argument('--config', default=str(repo_root / 'ml_pipeline' / 'train' / 'config.yaml'))
    parser.add_argument('--checkpoint', default=str(repo_root / 'ml_pipeline' / 'checkpoints' / 'best.pth'))
    args = parser.parse_args()

    cfg = load_config(args.config)

    class_names = cfg['dataset']['class_names']
    num_classes = cfg['model']['num_classes']

    device = 'cuda' if torch.cuda.is_available() else 'cpu'

    ckpt = torch.load(args.checkpoint, map_location=device)
    backbone = ckpt.get('backbone', cfg['model']['backbone'])
    pretrained = ckpt.get('config', {}).get('model', {}).get('pretrained', cfg['model']['pretrained'])

    model = build_backbone(backbone, num_classes=num_classes, pretrained=pretrained)
    model.load_state_dict(ckpt['model_state_dict'], strict=True)
    model = model.to(device)

    aug = cfg['augmentation']
    transform = transforms.Compose(
        [
            transforms.Resize(aug['resize_shorter_side']),
            transforms.CenterCrop(aug['crop_size'], aug['crop_size']),
            transforms.ToTensor(),
            transforms.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ]
    )

    img = Image.open(args.image).convert('RGB')
    res = predict_image(model, img, transform, class_names, device)
    print(json.dumps(res, indent=2))


if __name__ == '__main__':
    main()

