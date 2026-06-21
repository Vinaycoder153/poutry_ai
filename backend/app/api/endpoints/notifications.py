from fastapi import APIRouter
import app.database.crud as db

router = APIRouter()

@router.get("/notifications")
def get_notifications():
    return db.get_notifications()

@router.put("/notifications/{id}/read")
def update_notif_read(id: str, payload: dict):
    read = payload.get("read", False)
    db.update_notification_read(id, read)
    return {"status": "ok", "id": id, "read": read}

@router.delete("/notifications/clear")
def clear_notifs():
    db.clear_notifications()
    return {"status": "ok"}
