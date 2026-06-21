from fastapi import APIRouter
from typing import Union
import app.services.inference as inference
from app.schemas import HealthSuccessResponse, HealthErrorResponse

router = APIRouter()

@router.get("/health", response_model=Union[HealthSuccessResponse, HealthErrorResponse])
def health():
    try:
        inference.ensure_loaded()
        return HealthSuccessResponse(
            status="ok",
            device=inference.device,
            class_names=inference.bundle["class_names"]
        )
    except Exception as e:
        return HealthErrorResponse(
            status="model_not_found",
            device=inference.device,
            message="Model bundle is missing. Please run training first.",
            detail=str(e)
        )


