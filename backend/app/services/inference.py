import os
import io
import time
import torch
import torch.nn as nn
import numpy as np
from pathlib import Path
from fastapi import HTTPException
from app.core.config import repo_root

device = "cuda" if torch.cuda.is_available() else "cpu"
bundle = None
model = None
transform = None
last_bundle_mtime = 0.0

def build_backbone(backbone: str, num_classes: int, pretrained: bool):
    import torchvision
    import torch.nn as nn

    if backbone.lower() == "resnet50":
        model = torchvision.models.resnet50(weights="DEFAULT" if pretrained else None)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
        return model

    if backbone.lower() == "efficientnet_b0":
        model = torchvision.models.efficientnet_b0(weights="DEFAULT" if pretrained else None)
        model.classifier[1] = nn.Linear(model.classifier[1].in_features, num_classes)
        return model

    if backbone.lower() == "densenet121":
        model = torchvision.models.densenet121(weights="DEFAULT" if pretrained else None)
        model.classifier = nn.Linear(model.classifier.in_features, num_classes)
        return model

    model = torchvision.models.resnet50(weights="DEFAULT" if pretrained else None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    return model


def build_transform(preprocess: dict):
    import torchvision.transforms as T

    resize_shorter_side = int(preprocess["resize_shorter_side"])
    crop_size = int(preprocess["crop_size"])
    mean = tuple(preprocess["mean"])
    std = tuple(preprocess["std"])

    return T.Compose(
        [
            T.Resize(resize_shorter_side),
            T.CenterCrop(crop_size),
            T.ToTensor(),
            T.Normalize(mean=mean, std=std),
        ]
    )


def load_bundle():
    bundle_path = repo_root / "ml_pipeline" / "checkpoints" / "final" / "model_bundle.pth"

    if not bundle_path.exists():
        raise FileNotFoundError(
            f"Model bundle not found at {bundle_path}. Run training then export_final_bundle.py first."
        )

    bundle = torch.load(str(bundle_path), map_location="cpu")
    return bundle


def calculate_bbox_from_cam(cam, threshold=0.45):
    if cam is None:
        return [38.0, 36.0, 24.0, 22.0]
        
    y_indices, x_indices = np.where(cam >= threshold)
    
    if len(x_indices) == 0 or len(y_indices) == 0:
        return [38.0, 36.0, 24.0, 22.0]
        
    xmin = float(x_indices.min()) / 7.0 * 100.0
    xmax = float(x_indices.max() + 1) / 7.0 * 100.0
    ymin = float(y_indices.min()) / 7.0 * 100.0
    ymax = float(y_indices.max() + 1) / 7.0 * 100.0
    
    width = max(15.0, xmax - xmin)
    height = max(15.0, ymax - ymin)
    
    xmin = max(5.0, min(xmin, 80.0))
    ymin = max(5.0, min(ymin, 80.0))
    width = min(width, 100.0 - xmin)
    height = min(height, 100.0 - ymin)
    
    return [round(xmin, 1), round(ymin, 1), round(width, 1), round(height, 1)]


def get_class_details(class_name: str):
    status = "healthy"
    title = "Normal Healthy Cloaca"
    findings = [
        "Anatomical borders of the cloacal sphincter are clean and well-defined.",
        "No evidence of feather pasting, soil buildup, or fecal accumulation.",
        "Normal mucous membrane color without swelling or inflammatory erythema."
    ]
    actions = [
        "Maintain standard farm hygiene and litter status.",
        "Check feed line sanitize metrics.",
        "Log as standard healthy baseline."
    ]

    if class_name == "dirty":
        status = "warning"
        title = "Mild Soiling & Pasted Feathers"
        findings = [
            "Moderate feather pasting identified along the lower cloacal margins.",
            "Soil or organic build-up visible on adjacent feathers.",
            "Sphere mucosal lining is otherwise normal."
        ]
        actions = [
            "Wipe the vent clean with a sanitized warm compress.",
            "Check pen litter quality and dampness levels.",
            "Monitor feed quality for digestion issues."
        ]
    elif class_name == "inflamed":
        status = "warning"
        title = "Cloacal Inflammation / Erythema"
        findings = [
            "Significant redness (erythema) noted around the sphincter border.",
            "Mild swelling of the mucosal tissues.",
            "Feather dusting and slight discharge staining detected."
        ]
        actions = [
            "Isolate subject for detailed physical examination.",
            "Apply veterinary-approved soothing ointment to the sphincter area.",
            "Assess flock droppings for signs of enteritis or diarrhea.",
            "Review biosecurity measures and litter hygiene."
        ]
    elif class_name == "prolapse":
        status = "danger"
        title = "Severe Cloacal Prolapse (High Salmonella Risk)"
        findings = [
            "Pronounced protrusion of cloacal/oviduct tissue.",
            "Severe swelling, dilation, or bleeding of the sphincter ring.",
            "Dense, white pasty discharge indicating high physiological stress."
        ]
        actions = [
            "IMMEDIATE ISOLATION: Remove the chicken from the main flock immediately.",
            "ALERT VET: Forward report directly to attending flock veterinarian.",
            "DIAGNOSTIC TEST: Collect fecal swabs for Salmonella PCR.",
            "Rest subject in a dark, quiet pen to reduce egg-laying strain.",
            "Disinfect roosting bars and water nipples in affected house."
        ]
    return status, title, findings, actions


def ensure_loaded(force_reload=False):
    global bundle, model, transform, last_bundle_mtime
    bundle_path = repo_root / "ml_pipeline" / "checkpoints" / "final" / "model_bundle.pth"

    if not bundle_path.exists():
        raise FileNotFoundError(
            f"Model bundle not found at {bundle_path}. Run training then export_final_bundle.py first."
        )

    mtime = os.path.getmtime(str(bundle_path))
    if model is not None and mtime <= last_bundle_mtime and not force_reload:
        return

    try:
        bundle = load_bundle()
    except FileNotFoundError as e:
        raise HTTPException(
            status_code=503,
            detail="Model bundle not found. Please train and export the model first."
        ) from e

    class_names = bundle["class_names"]
    num_classes = int(bundle["num_classes"])
    backbone = bundle["backbone"]
    pretrained = bool(bundle.get("pretrained", True))

    model_local = build_backbone(backbone, num_classes=num_classes, pretrained=pretrained)
    model_local.load_state_dict(bundle["model_state_dict"], strict=True)
    model_local.eval().to(device)

    transform_local = build_transform(bundle["preprocess"])

    model = model_local
    transform = transform_local
    last_bundle_mtime = mtime
