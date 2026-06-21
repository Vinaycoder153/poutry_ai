import json
from app.database.connection import get_db, qp, IS_POSTGRES

def add_prediction(
    pred_id, date, time, image, image_name, status, confidence, 
    title, findings, actions, reviewed, flagged, model_version, analysis_time, box=None, original_image=None
):
    conn, cursor = get_db()
    if IS_POSTGRES:
        query = """
        INSERT INTO predictions (
            id, date, time, image, image_name, status, confidence, 
            title, findings, actions, reviewed, flagged, model_version, analysis_time, box, original_image
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            date = EXCLUDED.date,
            time = EXCLUDED.time,
            image = EXCLUDED.image,
            image_name = EXCLUDED.image_name,
            status = EXCLUDED.status,
            confidence = EXCLUDED.confidence,
            title = EXCLUDED.title,
            findings = EXCLUDED.findings,
            actions = EXCLUDED.actions,
            reviewed = EXCLUDED.reviewed,
            flagged = EXCLUDED.flagged,
            model_version = EXCLUDED.model_version,
            analysis_time = EXCLUDED.analysis_time,
            box = EXCLUDED.box,
            original_image = EXCLUDED.original_image
        """
    else:
        query = """
        INSERT OR REPLACE INTO predictions (
            id, date, time, image, image_name, status, confidence, 
            title, findings, actions, reviewed, flagged, model_version, analysis_time, box, original_image
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
    
    cursor.execute(
        query,
        (
            pred_id,
            date,
            time,
            image,
            image_name,
            status,
            confidence,
            title,
            json.dumps(findings),
            json.dumps(actions),
            1 if reviewed else 0,
            1 if flagged else 0,
            model_version,
            analysis_time,
            json.dumps(box) if box else None,
            original_image
        )
    )
    if not IS_POSTGRES:
        conn.commit()
    conn.close()

def get_predictions():
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM predictions ORDER BY id DESC")
    rows = cursor.fetchall()
    predictions = []
    for r in rows:
        row_keys = r.keys()
        predictions.append({
            "id": r["id"],
            "date": r["date"],
            "time": r["time"],
            "image": r["image"],
            "imageName": r["image_name"],
            "status": r["status"],
            "confidence": r["confidence"],
            "title": r["title"],
            "findings": json.loads(r["findings"]) if r["findings"] else [],
            "actions": json.loads(r["actions"]) if r["actions"] else [],
            "reviewed": bool(r["reviewed"]),
            "flagged": bool(r["flagged"]),
            "modelVersion": r["model_version"],
            "analysisTime": r["analysis_time"],
            "box": json.loads(r["box"]) if ("box" in row_keys and r["box"]) else None,
            "originalImage": r["original_image"] if ("original_image" in row_keys and r["original_image"]) else None
        })
    conn.close()
    return predictions

def delete_prediction(pred_id):
    conn, cursor = get_db()
    cursor.execute(qp("DELETE FROM predictions WHERE id = ?"), (pred_id,))
    if not IS_POSTGRES:
        conn.commit()
    conn.close()

def update_prediction_reviewed(pred_id, reviewed):
    conn, cursor = get_db()
    cursor.execute(qp("UPDATE predictions SET reviewed = ? WHERE id = ?"), (1 if reviewed else 0, pred_id))
    if not IS_POSTGRES:
        conn.commit()
    conn.close()

def update_prediction_flagged(pred_id, flagged):
    conn, cursor = get_db()
    cursor.execute(qp("UPDATE predictions SET flagged = ? WHERE id = ?"), (1 if flagged else 0, pred_id))
    if not IS_POSTGRES:
        conn.commit()
    conn.close()

def update_prediction_class(pred_id, status, title, findings, actions):
    conn, cursor = get_db()
    cursor.execute(
        qp("""
        UPDATE predictions
        SET status = ?, title = ?, findings = ?, actions = ?
        WHERE id = ?
        """),
        (status, title, json.dumps(findings), json.dumps(actions), pred_id)
    )
    if not IS_POSTGRES:
        conn.commit()
    conn.close()

def get_notifications():
    conn, cursor = get_db()
    cursor.execute("SELECT * FROM notifications ORDER BY id DESC")
    rows = cursor.fetchall()
    notifications = []
    for r in rows:
        notifications.append({
            "id": r["id"],
            "title": r["title"],
            "message": r["message"],
            "type": r["type"],
            "time": r["time"],
            "read": bool(r["read"])
        })
    conn.close()
    return notifications

def add_notification(notif_id, title, message, notif_type, time_str, read):
    conn, cursor = get_db()
    if IS_POSTGRES:
        query = """
        INSERT INTO notifications (id, title, message, type, time, read)
        VALUES (%s, %s, %s, %s, %s, %s)
        ON CONFLICT (id) DO UPDATE SET
            title = EXCLUDED.title,
            message = EXCLUDED.message,
            type = EXCLUDED.type,
            time = EXCLUDED.time,
            read = EXCLUDED.read
        """
    else:
        query = """
        INSERT OR REPLACE INTO notifications (id, title, message, type, time, read)
        VALUES (?, ?, ?, ?, ?, ?)
        """
    cursor.execute(
        query,
        (notif_id, title, message, notif_type, time_str, 1 if read else 0)
    )
    if not IS_POSTGRES:
        conn.commit()
    conn.close()

def update_notification_read(notif_id, read):
    conn, cursor = get_db()
    cursor.execute(qp("UPDATE notifications SET read = ? WHERE id = ?"), (1 if read else 0, notif_id))
    if not IS_POSTGRES:
        conn.commit()
    conn.close()

def clear_notifications():
    conn, cursor = get_db()
    cursor.execute("DELETE FROM notifications")
    if not IS_POSTGRES:
        conn.commit()
    conn.close()
