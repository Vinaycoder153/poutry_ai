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


def check_image_quality(img) -> tuple[bool, str]:
    """
    Validates resolution, average brightness, and sharpness (blurriness) of the image.
    Returns (True, "Quality checks passed") or (False, error_message).
    """
    # 1. Resolution Check
    w, h = img.size
    if w < 200 or h < 200:
        return False, f"Image resolution is too low ({w}x{h}). Please upload an image of at least 200x200 pixels."

    # Convert to grayscale for brightness and blurriness checks
    gray_img = img.convert("L")
    pixels = np.array(gray_img)

    # 2. Brightness Check
    mean_brightness = float(np.mean(pixels))
    if mean_brightness < 40.0:
        return False, f"Image is too dark (average brightness {mean_brightness:.1f}/255). Please upload a well-lit image."
    if mean_brightness > 240.0:
        return False, f"Image is too bright (average brightness {mean_brightness:.1f}/255). Please upload an image with balanced lighting."

    # 3. Blurriness Check using 2D Laplacian convolution in PyTorch
    import torch.nn.functional as F

    img_tensor = torch.from_numpy(pixels).float().unsqueeze(0).unsqueeze(0)  # Shape (1, 1, H, W)
    padded = F.pad(img_tensor, (1, 1, 1, 1), mode='replicate')
    laplacian_kernel = torch.tensor(
        [[0, 1, 0], [1, -4, 1], [0, 1, 0]], dtype=torch.float32
    ).view(1, 1, 3, 3)
    laplacian = F.conv2d(padded, laplacian_kernel, padding=0)
    variance = float(laplacian.var().item())

    if variance < 50.0:
        return False, f"Image is too blurry (blur metric {variance:.1f}). Please upload a sharp, in-focus image."

    return True, "Quality checks passed"


def detect_vent(img) -> tuple[bool, list[float] | None, any]:
    """
    Checks if a chicken vent is visible in the image using CAM.
    If visible, returns (True, box, cropped_image).
    Otherwise returns (False, None, None).
    """
    ensure_loaded()

    import torchvision.transforms as T

    # Direct resize to preserve the entire aspect ratio of the image for detection pass
    resize_tf = T.Compose(
        [
            T.Resize((224, 224)),
            T.ToTensor(),
            T.Normalize(
                mean=tuple(bundle["preprocess"]["mean"]),
                std=tuple(bundle["preprocess"]["std"]),
            ),
        ]
    )

    x = resize_tf(img).unsqueeze(0).to(device)

    features = None

    def hook(module, input, output):
        nonlocal features
        features = output

    hook_handle = None
    if hasattr(model, "layer4"):
        hook_handle = model.layer4.register_forward_hook(hook)

    try:
        with torch.no_grad():
            logits = model(x)
            probs = torch.softmax(logits, dim=1).squeeze(0).cpu().tolist()
    finally:
        if hook_handle is not None:
            hook_handle.remove()

    top_idx = int(torch.tensor(probs).argmax().item())
    top_prob = probs[top_idx]

    # We require a baseline classification confidence
    if top_prob < 0.35:
        return False, None, None

    # Extract Class Activation Map
    if (
        features is None
        or not hasattr(model, "fc")
        or not hasattr(model.fc, "weight")
    ):
        return False, None, None

    try:
        features_squeezed = features.squeeze(0)
        weights = model.fc.weight[top_idx].detach()
        cam = (features_squeezed * weights.view(-1, 1, 1)).sum(0)

        # Check raw CAM peak activation value
        raw_cam_max = float(cam.max().item())
        if raw_cam_max < 1.2:
            return False, None, None

        # Normalize CAM
        cam = cam - cam.min()
        cam_max = cam.max()
        if cam_max > 0:
            cam = cam / cam_max

        cam_np = cam.cpu().numpy()

        # Calculate bounding box percentages relative to the original image shape
        box = calculate_bbox_from_cam(cam_np, threshold=0.45)

        # Verify box size to reject scattered attention (OOD)
        xmin, ymin, width, height = box

        # If the box is too tiny (e.g. < 8% of size) or spans almost the entire image (uniform attention, > 92%), reject it.
        if width < 8.0 or height < 8.0 or width > 92.0 or height > 92.0:
            return False, None, None

        # Crop the original image using pixel coordinates
        img_w, img_h = img.size

        # Compute pixel coordinates
        x1 = max(0, int(xmin * img_w / 100.0))
        y1 = max(0, int(ymin * img_h / 100.0))
        x2 = min(img_w, int((xmin + width) * img_w / 100.0))
        y2 = min(img_h, int((ymin + height) * img_h / 100.0))

        # Prevent degenerate crops
        if (x2 - x1) < 20 or (y2 - y1) < 20:
            return False, None, None

        cropped_img = img.crop((x1, y1, x2, y2))
        return True, box, cropped_img

    except Exception as e:
        print(f"Error in detect_vent: {e}")
        return False, None, None

