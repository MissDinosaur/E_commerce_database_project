from fastapi import APIRouter
from pydantic import BaseModel
from app.models.database import mongo_db
import datetime

router = APIRouter()

class CursorLog(BaseModel):
    customer_id: str
    x: float
    y: float

@router.post("/log_cursor")
def log_cursor_activity(request: CursorLog):
    cursor_data = {
        "customer_id": request.customer_id,
        "x": request.x,
        "y": request.y,
        "timestamp": datetime.utcnow()
    }
    mongo_db["cursor_logs"].insert_one(cursor_data)
    return {"success": True, "message": "Cursor activity logged"}
