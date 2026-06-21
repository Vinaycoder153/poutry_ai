from fastapi import APIRouter
import app.services.retraining as retraining

router = APIRouter()

@router.get("/model/status")
def model_status():
    class_counts, total_images, metrics = retraining.get_dataset_statistics()
    is_training = retraining.get_retrain_status()

    return {
        "dataset_counts": class_counts,
        "total_images": total_images,
        "metrics": metrics,
        "is_training": is_training
    }

@router.post("/model/retrain")
def trigger_retrain():
    log_file = retraining.start_retrain()
    return {"status": "started", "log_file": log_file}

@router.get("/model/retrain/logs")
def get_retrain_logs():
    logs = retraining.read_retrain_logs()
    return {"logs": logs}
