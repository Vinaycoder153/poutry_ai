from fastapi import APIRouter
import app.services.retraining as retraining
from app.schemas import ModelStatusResponse, RetrainTriggerResponse, RetrainLogsResponse

router = APIRouter()

@router.get("/model/status", response_model=ModelStatusResponse)
def model_status():
    class_counts, total_images, metrics = retraining.get_dataset_statistics()
    is_training = retraining.get_retrain_status()

    return ModelStatusResponse(
        dataset_counts=class_counts,
        total_images=total_images,
        metrics=metrics,
        is_training=is_training
    )

@router.post("/model/retrain", response_model=RetrainTriggerResponse)
def trigger_retrain():
    log_file = retraining.start_retrain()
    return RetrainTriggerResponse(status="started", log_file=log_file)

@router.get("/model/retrain/logs", response_model=RetrainLogsResponse)
def get_retrain_logs():
    logs = retraining.read_retrain_logs()
    return RetrainLogsResponse(logs=logs)

