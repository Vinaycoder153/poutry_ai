from fastapi import APIRouter
from app.services.inference import ensure_loaded, device, bundle

router = APIRouter()

@router.get("/health")
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
