import uuid
import datetime
import io
import time
import shutil
import torch
from pathlib import Path
from PIL import Image
from fastapi import APIRouter, File, UploadFile, HTTPException, Request
import app.database.crud as db
import app.services.inference as inference
from app.core.config import uploads_dir, repo_root

router = APIRouter()

@router.post("/predict")
async def predict(request: Request, file: UploadFile = File(...)):
    inference.ensure_loaded()

    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image")

    raw = await file.read()
    if raw is None:
        raise HTTPException(status_code=400, detail="Upload read returned None")
    if not raw:
        raise HTTPException(status_code=400, detail=f"Empty upload (filename={file.filename})")

    try:
        img = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read image: {e}")

    file_ext = Path(file.filename).suffix if file.filename else ".jpg"
    unique_filename = f"{uuid.uuid4().hex}{file_ext}"
    saved_path = uploads_dir / unique_filename
    with open(saved_path, "wb") as out_f:
        out_f.write(raw)

    base_url = str(request.base_url).rstrip("/")
    image_url = f"{base_url}/uploads/{unique_filename}"

    t0 = time.time()
    x = inference.transform(img).unsqueeze(0).to(inference.device)

    features = None
    def hook(module, input, output):
        nonlocal features
        features = output

    hook_handle = None
    if hasattr(inference.model, "layer4"):
        hook_handle = inference.model.layer4.register_forward_hook(hook)

    with torch.no_grad():
        logits = inference.model(x)
        probs = torch.softmax(logits, dim=1).squeeze(0).cpu().tolist()

    if hook_handle is not None:
        hook_handle.remove()

    class_names = inference.bundle["class_names"]
    top_idx = int(torch.tensor(probs).argmax().item())

    top_class = class_names[top_idx]
    top_prob = float(probs[top_idx])

    box = [38.0, 36.0, 24.0, 22.0]
    if features is not None and hasattr(inference.model, "fc") and hasattr(inference.model.fc, "weight"):
        try:
            features_squeezed = features.squeeze(0)
            weights = inference.model.fc.weight[top_idx].detach()
            cam = (features_squeezed * weights.view(-1, 1, 1)).sum(0)
            cam = cam - cam.min()
            cam_max = cam.max()
            if cam_max > 0:
                cam = cam / cam_max
            cam_np = cam.cpu().numpy()
            box = inference.calculate_bbox_from_cam(cam_np)
        except Exception as cam_err:
            print(f"CAM localization error: {cam_err}")

    elapsed = time.time() - t0
    status, title, findings, actions = inference.get_class_details(top_class)

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
        model_version=inference.bundle.get("version", "V2.4-CLOACA-NET"),
        analysis_time=f"{elapsed:.2f}s",
        box=box
    )

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
        "modelVersion": inference.bundle.get("version", "V2.4-CLOACA-NET"),
        "analysisTime": f"{elapsed:.2f}s",
        "box": box
    }

@router.get("/history")
def get_history():
    return db.get_predictions()

@router.put("/history/{id}/correct")
async def correct_prediction(id: str, payload: dict):
    corrected_status = payload.get("correctedStatus")
    if not corrected_status or corrected_status not in ["healthy", "dirty", "inflamed", "prolapse"]:
        raise HTTPException(status_code=400, detail="Invalid corrected status")

    predictions = db.get_predictions()
    pred_item = None
    for p in predictions:
        if p["id"] == id:
            pred_item = p
            break

    if not pred_item:
        raise HTTPException(status_code=404, detail="Prediction not found")

    status, title, findings, actions = inference.get_class_details(corrected_status)
    db.update_prediction_class(id, status, title, findings, actions)

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

@router.put("/history/{id}/reviewed")
def update_reviewed(id: str, payload: dict):
    reviewed = payload.get("reviewed", False)
    db.update_prediction_reviewed(id, reviewed)
    return {"status": "ok", "id": id, "reviewed": reviewed}

@router.put("/history/{id}/flagged")
def update_flagged(id: str, payload: dict):
    flagged = payload.get("flagged", False)
    db.update_prediction_flagged(id, flagged)
    return {"status": "ok", "id": id, "flagged": flagged}

@router.delete("/history/{id}")
def delete_item(id: str):
    db.delete_prediction(id)
    return {"status": "ok", "id": id}
