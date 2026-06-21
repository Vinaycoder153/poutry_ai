"""Export a stable deployable bundle for inference + FastAPI.

Creates: ml_pipeline/checkpoints/final/model_bundle.pth

Bundle fields:
- backbone
- pretrained
- num_classes
- class_names
- image_size / preprocess params
- model_state_dict
"""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path

import torch


def build_backbone(backbone: str, num_classes: int, pretrained: bool):
    import torch.nn as nn
    import torchvision

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


def load_config(config_path: Path) -> dict:
    import yaml

    return yaml.safe_load(config_path.read_text(encoding='utf-8'))


def main():
    # export_final_bundle.py -> ml_pipeline/export -> ml_pipeline -> repo_root
    repo_root = Path(__file__).resolve().parents[2]

    ap = argparse.ArgumentParser()
    ap.add_argument('--config', default=str(repo_root / 'ml_pipeline' / 'train' / 'config.yaml'))

    ap.add_argument('--checkpoint', default=str(repo_root / 'ml_pipeline' / 'checkpoints' / 'best.pth'))
    ap.add_argument('--out', default=str(repo_root / 'ml_pipeline' / 'checkpoints' / 'final' / 'model_bundle.pth'))
    args = ap.parse_args()

    config_path = Path(args.config)
    ckpt_path = Path(args.checkpoint)
    out_path = Path(args.out)

    if not ckpt_path.exists():
        raise FileNotFoundError(f"Checkpoint not found: {ckpt_path}")
    if not config_path.exists():
        raise FileNotFoundError(f"Config not found: {config_path}")

    cfg = load_config(config_path)

    class_names = cfg['dataset']['class_names']
    num_classes = int(cfg['model']['num_classes'])
    backbone = cfg['model']['backbone']
    pretrained = bool(cfg['model']['pretrained'])

    aug = cfg.get('augmentation', {})
    resize_shorter_side = int(aug.get('resize_shorter_side', 256))
    crop_size = int(aug.get('crop_size', 224))

    ckpt = torch.load(str(ckpt_path), map_location='cpu')

    bundle = {
        'version': 'poutry-ai-model-bundle-v1',
        'class_names': class_names,
        'num_classes': num_classes,
        'backbone': backbone,
        'pretrained': pretrained,
        'preprocess': {
            'resize_shorter_side': resize_shorter_side,
            'crop_size': crop_size,
            'mean': [0.485, 0.456, 0.406],
            'std': [0.229, 0.224, 0.225],
        },
        'model_state_dict': ckpt['model_state_dict'],
        'training_summary': {
            'best_val_acc': ckpt.get('best_val_acc', None),
            'best_epoch': ckpt.get('epoch', None),
            'backbone_in_ckpt': ckpt.get('backbone', None),
        },
    }

    out_path.parent.mkdir(parents=True, exist_ok=True)
    torch.save(bundle, str(out_path))

    # Write a sidecar json for quick inspection
    sidecar = out_path.with_suffix('.json')
    sidecar.write_text(json.dumps({
        'out': str(out_path),
        'class_names': class_names,
        'backbone': backbone,
        'num_classes': num_classes,
        'preprocess': bundle['preprocess'],
        'training_summary': bundle['training_summary'],
    }, indent=2), encoding='utf-8')

    print(f"Exported model bundle to: {out_path}")
    print(f"Sidecar written to: {sidecar}")


if __name__ == '__main__':
    main()

