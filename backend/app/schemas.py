from pydantic import BaseModel, Field
from typing import List, Dict, Any, Optional

class PredictionCorrection(BaseModel):
    correctedStatus: str = Field(..., description="The corrected classification status, e.g. healthy, dirty, inflamed, prolapse")

class PredictionReview(BaseModel):
    reviewed: bool = Field(..., description="Review status of the prediction")

class PredictionFlag(BaseModel):
    flagged: bool = Field(..., description="Flag status of the prediction")

class PredictionResponse(BaseModel):
    id: str
    date: str
    time: str
    image: str
    imageName: str
    status: str
    confidence: float
    title: str
    findings: List[str]
    actions: List[str]
    reviewed: bool
    flagged: bool
    modelVersion: str
    analysisTime: str
    box: Optional[List[float]] = None
    originalImage: Optional[str] = None

class NotificationRead(BaseModel):
    read: bool = Field(..., description="Read status of the notification")

class NotificationResponse(BaseModel):
    id: str
    title: str
    message: str
    type: str
    time: str
    read: bool

class ModelStatusResponse(BaseModel):
    dataset_counts: Dict[str, int]
    total_images: int
    metrics: Dict[str, Any]
    is_training: bool

class RetrainTriggerResponse(BaseModel):
    status: str
    log_file: str

class RetrainLogsResponse(BaseModel):
    logs: str

class HealthSuccessResponse(BaseModel):
    status: str
    device: str
    class_names: List[str]

class HealthErrorResponse(BaseModel):
    status: str
    device: str
    message: str
    detail: str

class ActionStatusResponse(BaseModel):
    status: str = "ok"
    id: Optional[str] = None

class PredictionCorrectionResponse(BaseModel):
    status: str = "ok"
    id: str
    correctedStatus: str
    title: str
    findings: List[str]
    actions: List[str]

class PredictionReviewResponse(BaseModel):
    status: str = "ok"
    id: str
    reviewed: bool

class PredictionFlagResponse(BaseModel):
    status: str = "ok"
    id: str
    flagged: bool

class NotificationReadResponse(BaseModel):
    status: str = "ok"
    id: str
    read: bool



