from fastapi import APIRouter
import app.services.inference as inference

router = APIRouter()

@router.get("/health")
def health():
    try:
        inference.ensure_loaded()
        return {"status": "ok", "device": inference.device, "class_names": inference.bundle["class_names"]}
    except Exception as e:
        return {
            "status": "model_not_found",
            "device": inference.device,
            "message": "Model bundle is missing. Please run training first.",
            "detail": str(e)
        }

