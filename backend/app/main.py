from __future__ import annotations

import io
import time
import uuid
import datetime
import os
import shutil
import subprocess
import sys
import json
import numpy as np
from pathlib import Path

import torch
import torch.nn as nn
from fastapi import FastAPI, File, UploadFile, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

# Import SQLite database module
import app.db as db

# Resolve paths
repo_root = Path(__file__).resolve().parents[2]
if repo_root == Path("/") and Path("/app").exists():
    repo_root = Path("/app")
uploads_dir = repo_root / "backend" / "uploads"
uploads_dir.mkdir(parents=True, exist_ok=True)

# Initialize database tables on startup
db.init_db()

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


bundle = None
model = None
transform = None
last_bundle_mtime = 0.0
device = "cuda" if torch.cuda.is_available() else "cpu"

retrain_proc = None
retrain_log_path = repo_root / "ml_pipeline" / "runs" / "retrain_live.log"


def calculate_bbox_from_cam(cam, threshold=0.45):
    if cam is None:
        return [38.0, 36.0, 24.0, 22.0]
        
    y_indices, x_indices = np.where(cam >= threshold)
    
    if len(x_indices) == 0 or len(y_indices) == 0:
        return [38.0, 36.0, 24.0, 22.0]
        
    # Scale from 7x7 grid to 100x100 percentage coordinates
    xmin = float(x_indices.min()) / 7.0 * 100.0
    xmax = float(x_indices.max() + 1) / 7.0 * 100.0
    ymin = float(y_indices.min()) / 7.0 * 100.0
    ymax = float(y_indices.max() + 1) / 7.0 * 100.0
    
    # Bounding box dimensions
    width = max(15.0, xmax - xmin)
    height = max(15.0, ymax - ymin)
    
    # Clip coordinates to boundaries
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


app = FastAPI(title="Poultry AI API", version="1.0")

# Static files for serving uploaded images
app.mount("/uploads", StaticFiles(directory=str(uploads_dir)), name="uploads")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health():
    try:
        ensure_loaded()
        return {"status": "ok", "device": device, "class_names": bundle["class_names"]}
    except Exception as e:
        return {
            "status": "model_not_found",
            "device": device,
            "message": "Model bundle is missing. Please run training first.",
            "detail": str(e)
        }


@app.post("/api/predict")
async def predict(request: Request, file: UploadFile = File(...)):
    # Dynamically verify that model bundle is loaded
    ensure_loaded()

    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    raw = await file.read()
    if raw is None:
        raise HTTPException(status_code=400, detail="Upload read returned None")
    if not raw:
        raise HTTPException(status_code=400, detail=f"Empty upload (filename={file.filename})")

    from PIL import Image

    try:
        img = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read image: {e}")

    # Generate unique filename and save image to uploads directory
    file_ext = Path(file.filename).suffix if file.filename else ".jpg"
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    saved_path = uploads_dir / unique_filename
    with open(saved_path, "wb") as out_f:
        out_f.write(raw)

    base_url = str(request.base_url).rstrip("/")
    image_url = f"{base_url}/uploads/{unique_filename}"

    # Perform inference
    t0 = time.time()
    x = transform(img).unsqueeze(0).to(device)

    # Trace features to get Class Activation Map (CAM)
    features = None
    def hook(module, input, output):
        nonlocal features
        features = output

    hook_handle = None
    if hasattr(model, "layer4"):
        hook_handle = model.layer4.register_forward_hook(hook)

    with torch.no_grad():
        logits = model(x)
        probs = torch.softmax(logits, dim=1).squeeze(0).cpu().tolist()

    if hook_handle is not None:
        hook_handle.remove()

    class_names = bundle["class_names"]
    top_idx = int(torch.tensor(probs).argmax().item())

    top_class = class_names[top_idx]
    top_prob = float(probs[top_idx])

    # Extract bounding box from CAM
    box = [38.0, 36.0, 24.0, 22.0]
    if features is not None and hasattr(model, "fc") and hasattr(model.fc, "weight"):
        try:
            features_squeezed = features.squeeze(0)
            weights = model.fc.weight[top_idx].detach()
            cam = (features_squeezed * weights.view(-1, 1, 1)).sum(0)
            cam = cam - cam.min()
            cam_max = cam.max()
            if cam_max > 0:
                cam = cam / cam_max
            cam_np = cam.cpu().numpy()
            box = calculate_bbox_from_cam(cam_np)
        except Exception as cam_err:
            print(f"CAM localization error: {cam_err}")

    elapsed = time.time() - t0

    # Determine status, clinical findings, and actions based on predicted class
    status, title, findings, actions = get_class_details(top_class)

    # Save to SQLite Database
    now = datetime.datetime.now()
    date_str = now.strftime("%b %d, %Y")
    time_str = now.strftime("%I:%M %p")
    pred_id = f"CS-{uuid.uuid4().hex[:6].upper()}"

    db.add_prediction(
        pred_id=pred_id,
        date=date_str,
        time=time_str,
        image=image_url,
        image_name=file.filename or unique_filename,
        status=status,
        confidence=round(top_prob * 100, 1),
        title=title,
        findings=findings,
        actions=actions,
        reviewed=False,
        flagged=(status == "danger"),
        model_version=bundle.get("version", "V2.4-CLOACA-NET"),
        analysis_time=f"{elapsed:.2f}s",
        box=box
    )

    # Automatically create alerts / notifications
    if status == "danger":
        db.add_notification(
            notif_id=f"notif-{uuid.uuid4().hex[:6]}",
            title="CRITICAL SALMONELLA RISK DETECTED",
            message=f"High risk score ({round(top_prob * 100, 1)}%) mapped in Case {pred_id} ({file.filename or unique_filename}).",
            notif_type="danger",
            time_str="Just Now",
            read=False
        )
    elif status == "warning":
        db.add_notification(
            notif_id=f"notif-{uuid.uuid4().hex[:6]}",
            title="Mild Pasting Warning",
            message=f"Warning status calibrated in Case {pred_id}. Confidence level {round(top_prob * 100, 1)}%.",
            notif_type="warning",
            time_str="Just Now",
            read=False
        )

    # Return prediction JSON
    return {
        "id": pred_id,
        "date": date_str,
        "time": time_str,
        "image": image_url,
        "imageName": file.filename or unique_filename,
        "status": status,
        "confidence": round(top_prob * 100, 1),
        "title": title,
        "findings": findings,
        "actions": actions,
        "reviewed": False,
        "flagged": status == "danger",
        "modelVersion": bundle.get("version", "V2.4-CLOACA-NET"),
        "analysisTime": f"{elapsed:.2f}s",
        "box": box
    }


@app.put("/api/history/{id}/correct")
async def correct_prediction(id: str, payload: dict):
    corrected_status = payload.get("correctedStatus")
    if not corrected_status or corrected_status not in ["healthy", "dirty", "inflamed", "prolapse"]:
        raise HTTPException(status_code=400, detail="Invalid corrected status")

    # Fetch original prediction item
    predictions = db.get_predictions()
    pred_item = None
    for p in predictions:
        if p["id"] == id:
            pred_item = p
            break

    if not pred_item:
        raise HTTPException(status_code=404, detail="Prediction not found")

    status, title, findings, actions = get_class_details(corrected_status)
    db.update_prediction_class(id, status, title, findings, actions)

    # Copy image file to corresponding training dataset folder
    image_url = pred_item["image"]
    filename = image_url.split("/")[-1]
    source_file = uploads_dir / filename
    dest_dir = repo_root / "poutry_ai" / "dataset" / corrected_status
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest_file = dest_dir / f"corrected_{filename}"

    if source_file.exists() and not dest_file.exists():
        try:
            shutil.copy(str(source_file), str(dest_file))
        except Exception as e:
            print(f"Failed to copy image to dataset folder: {e}")

    return {
        "status": "ok",
        "id": id,
        "correctedStatus": corrected_status,
        "title": title,
        "findings": findings,
        "actions": actions
    }


@app.get("/api/model/status")
def model_status():
    global retrain_proc

    dataset_dir = repo_root / "poutry_ai" / "dataset"
    class_counts = {}
    total_images = 0
    class_names = ["healthy", "dirty", "inflamed", "prolapse"]

    for cls in class_names:
        cdir = dataset_dir / cls
        count = 0
        if cdir.exists():
            exts = {".png", ".jpg", ".jpeg", ".webp"}
            count = len([f for f in cdir.iterdir() if f.is_file() and f.suffix.lower() in exts])
        class_counts[cls] = count
        total_images += count

    eval_path = repo_root / "ml_pipeline" / "checkpoints" / "eval" / "eval_best.json"
    metrics = {}
    if eval_path.exists():
        try:
            with open(eval_path, "r", encoding="utf-8") as f:
                metrics = json.load(f)
        except Exception:
            pass

    is_training = False
    if retrain_proc is not None:
        if retrain_proc.poll() is None:
            is_training = True
        else:
            retrain_proc = None

    return {
        "dataset_counts": class_counts,
        "total_images": total_images,
        "metrics": metrics,
        "is_training": is_training
    }


@app.post("/api/model/retrain")
def trigger_retrain():
    global retrain_proc
    if retrain_proc is not None and retrain_proc.poll() is None:
        raise HTTPException(status_code=400, detail="Retraining is already in progress.")

    retrain_log_path.parent.mkdir(parents=True, exist_ok=True)
    with open(retrain_log_path, "w", encoding="utf-8") as f:
        f.write("Starting AI Model Retraining...\n")

    train_script = repo_root / "ml_pipeline" / "train" / "train_classifier.py"
    log_file = open(retrain_log_path, "a", encoding="utf-8", buffering=1)

    retrain_proc = subprocess.Popen(
        [sys.executable, "-u", str(train_script)],
        stdout=log_file,
        stderr=subprocess.STDOUT,
        cwd=str(repo_root),
        text=True
    )

    return {"status": "started", "log_file": str(retrain_log_path)}


@app.get("/api/model/retrain/logs")
def get_retrain_logs():
    if not retrain_log_path.exists():
        return {"logs": "No training logs found."}

    try:
        with open(retrain_log_path, "r", encoding="utf-8") as f:
            logs = f.read()
        return {"logs": logs}
    except Exception as e:
        return {"logs": f"Error reading logs: {str(e)}"}


@app.get("/api/history")
def get_history():
    return db.get_predictions()


@app.put("/api/history/{id}/reviewed")
def update_reviewed(id: str, payload: dict):
    reviewed = payload.get("reviewed", False)
    db.update_prediction_reviewed(id, reviewed)
    return {"status": "ok", "id": id, "reviewed": reviewed}


@app.put("/api/history/{id}/flagged")
def update_flagged(id: str, payload: dict):
    flagged = payload.get("flagged", False)
    db.update_prediction_flagged(id, flagged)
    return {"status": "ok", "id": id, "flagged": flagged}


@app.delete("/api/history/{id}")
def delete_item(id: str):
    db.delete_prediction(id)
    return {"status": "ok", "id": id}


@app.get("/api/notifications")
def get_notifications():
    return db.get_notifications()


@app.put("/api/notifications/{id}/read")
def update_notif_read(id: str, payload: dict):
    read = payload.get("read", False)
    db.update_notification_read(id, read)
    return {"status": "ok", "id": id, "read": read}


@app.delete("/api/notifications/clear")
def clear_notifs():
    db.clear_notifications()
    return {"status": "ok"}
