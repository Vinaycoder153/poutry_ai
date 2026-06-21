import uuid
import datetime
import io
import time
import shutil
import torch
from pathlib import Path
from PIL import Image
from fastapi import APIRouter, File, UploadFile, HTTPException, Request
from typing import List, Dict, Any
import app.database.crud as db
import app.services.inference as inference
from app.core.config import uploads_dir, repo_root
from app.schemas import (
    PredictionResponse,
    PredictionCorrection,
    PredictionReview,
    PredictionFlag,
    ActionStatusResponse,
    PredictionCorrectionResponse,
    PredictionReviewResponse,
    PredictionFlagResponse
)


router = APIRouter()

@router.post("/predict", response_model=PredictionResponse)
async def predict(request: Request, file: UploadFile = File(...)):
    inference.ensure_loaded()

    # 1. Content Type Check
    if file.content_type and not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File must be an image.")

    # 2. Extension Check
    file_ext = Path(file.filename).suffix.lower() if file.filename else ".jpg"
    if file_ext not in [".jpg", ".jpeg", ".png"]:
        raise HTTPException(status_code=400, detail="Only JPG, JPEG, and PNG images are supported.")

    raw = await file.read()
    if raw is None:
        raise HTTPException(status_code=400, detail="Upload read returned None")
    if not raw:
        raise HTTPException(status_code=400, detail=f"Empty upload (filename={file.filename})")

    try:
        img = Image.open(io.BytesIO(raw)).convert("RGB")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Could not read image: {e}")

    # 3. Quality Validation Check (Resolution, Brightness, Blurriness)
    passed, error_msg = inference.check_image_quality(img)
    if not passed:
        raise HTTPException(status_code=400, detail=error_msg)

    # 4. Vent Visibility / AI Detection Check
    detected, box, cropped_img = inference.detect_vent(img)
    if not detected:
        raise HTTPException(
            status_code=422,
            detail="Vent region not detected. Please upload a clearer chicken vent/cloaca image."
        )

    # 5. Save the original and cropped files
    unique_id = uuid.uuid4().hex
    original_filename = f"original_{unique_id}{file_ext}"
    cropped_filename = f"cropped_{unique_id}{file_ext}"
    
    original_saved_path = uploads_dir / original_filename
    cropped_saved_path = uploads_dir / cropped_filename

    try:
        with open(original_saved_path, "wb") as out_f:
            out_f.write(raw)
        cropped_img.save(cropped_saved_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Could not save images: {e}")

    base_url = str(request.base_url).rstrip("/")
    image_url = f"{base_url}/uploads/{cropped_filename}"
    original_image_url = f"{base_url}/uploads/{original_filename}"

    # 6. Run Prediction on Cropped Image
    t0 = time.time()
    x = inference.transform(cropped_img).unsqueeze(0).to(inference.device)

    with torch.no_grad():
        logits = inference.model(x)
        probs = torch.softmax(logits, dim=1).squeeze(0).cpu().tolist()

    class_names = inference.bundle["class_names"]
    top_idx = int(torch.tensor(probs).argmax().item())

    top_class = class_names[top_idx]
    top_prob = float(probs[top_idx])

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
        image_name=file.filename or cropped_filename,
        status=status,
        confidence=round(top_prob * 100, 1),
        title=title,
        findings=findings,
        actions=actions,
        reviewed=False,
        flagged=(status == "danger"),
        model_version=inference.bundle.get("version", "V2.4-CLOACA-NET"),
        analysis_time=f"{elapsed:.2f}s",
        box=box,
        original_image=original_image_url
    )

    if status == "danger":
        db.add_notification(
            notif_id=f"notif-{uuid.uuid4().hex[:6]}",
            title="CRITICAL SALMONELLA RISK DETECTED",
            message=f"High risk score ({round(top_prob * 100, 1)}%) mapped in Case {pred_id} ({file.filename or cropped_filename}).",
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
        "imageName": file.filename or cropped_filename,
        "status": status,
        "confidence": round(top_prob * 100, 1),
        "title": title,
        "findings": findings,
        "actions": actions,
        "reviewed": False,
        "flagged": status == "danger",
        "modelVersion": inference.bundle.get("version", "V2.4-CLOACA-NET"),
        "analysisTime": f"{elapsed:.2f}s",
        "box": box,
        "originalImage": original_image_url
    }

@router.get("/history", response_model=List[PredictionResponse])
def get_history():
    return db.get_predictions()

@router.put("/history/{id}/correct", response_model=PredictionCorrectionResponse)
async def correct_prediction(id: str, payload: PredictionCorrection):
    corrected_status = payload.correctedStatus
    if corrected_status not in ["healthy", "dirty", "inflamed", "prolapse"]:
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

    return PredictionCorrectionResponse(
        status="ok",
        id=id,
        correctedStatus=corrected_status,
        title=title,
        findings=findings,
        actions=actions
    )

@router.put("/history/{id}/reviewed", response_model=PredictionReviewResponse)
def update_reviewed(id: str, payload: PredictionReview):
    reviewed = payload.reviewed
    db.update_prediction_reviewed(id, reviewed)
    return PredictionReviewResponse(status="ok", id=id, reviewed=reviewed)

@router.put("/history/{id}/flagged", response_model=PredictionFlagResponse)
def update_flagged(id: str, payload: PredictionFlag):
    flagged = payload.flagged
    db.update_prediction_flagged(id, flagged)
    return PredictionFlagResponse(status="ok", id=id, flagged=flagged)

@router.delete("/history/{id}", response_model=ActionStatusResponse)
def delete_item(id: str):
    db.delete_prediction(id)
    return ActionStatusResponse(status="ok", id=id)

