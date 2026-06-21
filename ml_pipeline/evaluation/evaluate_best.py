"""Evaluate best checkpoint and write metrics.

Outputs:
- ml_pipeline/checkpoints/eval/eval_best.json
- ml_pipeline/checkpoints/eval/confusion_matrix.json

Metrics:
- accuracy
- macro precision/recall/f1
- confusion matrix

Usage:
  python ml_pipeline/evaluation/evaluate_best.py --checkpoint ml_pipeline/checkpoints/best.pth --config ml_pipeline/train/config.yaml
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import numpy as np
import torch
import torch.nn as nn


def load_config(config_path: Path) -> dict:
    import yaml

    return yaml.safe_load(config_path.read_text(encoding="utf-8"))


def build_backbone(backbone: str, num_classes: int, pretrained: bool):
    import torchvision

    if backbone.lower() == "resnet50":
        import torch.nn as nn

        model = torchvision.models.resnet50(weights="DEFAULT" if pretrained else None)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
        return model

    if backbone.lower() == "efficientnet_b0":
        import torch.nn as nn

        model = torchvision.models.efficientnet_b0(weights="DEFAULT" if pretrained else None)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
        return model

    if backbone.lower() == "densenet121":
        import torch.nn as nn

        model = torchvision.models.densenet121(weights="DEFAULT" if pretrained else None)
        model.classifier = nn.Linear(model.classifier.in_features, num_classes)
        return model

    import torch.nn as nn

    model = torchvision.models.resnet50(weights="DEFAULT" if pretrained else None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model


def build_val_transform(aug_cfg: dict):
    from PIL import Image

    import torchvision.transforms as T

    resize_shorter_side = int(aug_cfg["resize_shorter_side"])
    crop_size = int(aug_cfg["crop_size"])

    # Standard ImageNet stats
    return T.Compose(
        [
            T.Resize(resize_shorter_side),
            T.CenterCrop(crop_size),
            T.ToTensor(),
            T.Normalize(mean=(0.485, 0.456, 0.406), std=(0.229, 0.224, 0.225)),
        ]
    )


def list_images(root_dir: str, class_names: list[str], image_exts: list[str]):
    exts = tuple([e.lower() for e in image_exts])
    items = []
    for idx, cls in enumerate(class_names):
        cdir = Path(root_dir) / cls
        if not cdir.exists():
            continue
        for fn in cdir.iterdir():
            if fn.is_file() and fn.suffix.lower() in exts:
                items.append((str(fn), idx))
    return items


def stratified_split(items, val_ratio: float, seed: int):
    rng = np.random.default_rng(seed)
    by_class = {}
    for path, y in items:
        by_class.setdefault(y, []).append((path, y))

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


def confusion_matrix(y_true: np.ndarray, y_pred: np.ndarray, num_classes: int):
    cm = np.zeros((num_classes, num_classes), dtype=int)
    for t, p in zip(y_true, y_pred):
        cm[int(t), int(p)] += 1
    return cm


def macro_precision_recall_f1(cm: np.ndarray):
    # cm rows=true, cols=pred
    num_classes = cm.shape[0]
    precisions = []
    recalls = []
    f1s = []

    for c in range(num_classes):
        tp = cm[c, c]
        fp = cm[:, c].sum() - tp
        fn = cm[c, :].sum() - tp

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0.0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        precisions.append(precision)
        recalls.append(recall)
        f1s.append(f1)

    return {
        "precision_macro": float(np.mean(precisions)),
        "recall_macro": float(np.mean(recalls)),
        "f1_macro": float(np.mean(f1s)),
    }


def main():
    ap = argparse.ArgumentParser()
    repo_root = Path(__file__).resolve().parents[2]
    ap.add_argument("--config", default=str(repo_root / "ml_pipeline" / "train" / "config.yaml"))
    ap.add_argument("--checkpoint", default=str(repo_root / "ml_pipeline" / "checkpoints" / "best.pth"))
    ap.add_argument("--out_dir", default=str(repo_root / "ml_pipeline" / "checkpoints" / "eval"))
    args = ap.parse_args()

    cfg = load_config(Path(args.config))
    class_names = cfg["dataset"]["class_names"]
    num_classes = int(cfg["model"]["num_classes"])
    backbone = cfg["model"]["backbone"]
    pretrained = bool(cfg["model"]["pretrained"])

    # Build val set deterministically using same seed/val_ratio
    dataset_root = str(repo_root / cfg["dataset"]["root_dir"])
    image_exts = cfg["dataset"]["image_exts"]
    val_ratio = float(cfg["dataset"]["split"]["val_ratio"])
    seed = int(cfg["dataset"]["split"]["seed"])

    items = list_images(dataset_root, class_names, image_exts)
    if len(items) == 0:
        raise RuntimeError(f"No images found under dataset root: {dataset_root}")

    _, val_items = stratified_split(items, val_ratio=val_ratio, seed=seed)

    import PIL
    from PIL import Image

    tfm = build_val_transform(cfg["augmentation"])

    device = "cuda" if torch.cuda.is_available() else "cpu"

    ckpt = torch.load(args.checkpoint, map_location=device)

    model = build_backbone(backbone, num_classes=num_classes, pretrained=pretrained)
    model.load_state_dict(ckpt["model_state_dict"], strict=True)
    model = model.to(device)
    model.eval()

    y_true = []
    y_pred = []

    with torch.no_grad():
        for path, y in val_items:
            img = Image.open(path).convert("RGB")
            x = tfm(img).unsqueeze(0).to(device)
            logits = model(x)
            pred = int(torch.argmax(logits, dim=1).item())
            y_true.append(int(y))
            y_pred.append(pred)

    y_true = np.array(y_true, dtype=int)
    y_pred = np.array(y_pred, dtype=int)

    cm = confusion_matrix(y_true, y_pred, num_classes=num_classes)
    acc = float((y_true == y_pred).mean())
    pr = macro_precision_recall_f1(cm)

    out_dir = Path(args.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    metrics = {
        "accuracy": acc,
        **pr,
        "num_samples": int(len(y_true)),
        "class_names": class_names,
        "checkpoint": args.checkpoint,
    }

    (out_dir / "eval_best.json").write_text(json.dumps(metrics, indent=2), encoding="utf-8")
    (out_dir / "confusion_matrix.json").write_text(
        json.dumps({"confusion_matrix": cm.tolist(), "class_names": class_names}, indent=2),
        encoding="utf-8",
    )

    print("Wrote:", out_dir / "eval_best.json")
    print("Wrote:", out_dir / "confusion_matrix.json")
    print("Metrics:", metrics)


if __name__ == "__main__":
    main()

