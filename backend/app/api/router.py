from fastapi import APIRouter
from app.api.endpoints import health, predictions, notifications, model

api_router = APIRouter()

api_router.include_router(health.router)
api_router.include_router(predictions.router)
api_router.include_router(notifications.router)
api_router.include_router(model.router)
