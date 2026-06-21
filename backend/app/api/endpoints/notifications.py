from fastapi import APIRouter
from typing import List
import app.database.crud as db
from app.schemas import NotificationResponse, NotificationRead, NotificationReadResponse, ActionStatusResponse

router = APIRouter()

@router.get("/notifications", response_model=List[NotificationResponse])
def get_notifications():
    return db.get_notifications()

@router.put("/notifications/{id}/read", response_model=NotificationReadResponse)
def update_notif_read(id: str, payload: NotificationRead):
    read = payload.read
    db.update_notification_read(id, read)
    return NotificationReadResponse(status="ok", id=id, read=read)

@router.delete("/notifications/clear", response_model=ActionStatusResponse)
def clear_notifs():
    db.clear_notifications()
    return ActionStatusResponse(status="ok")

