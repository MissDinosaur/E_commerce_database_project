from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.database import get_db, mongo_db
from datetime import datetime

router = APIRouter()

class PurchaseRequest(BaseModel):
    customer_id: str
    product_id: str

@router.post("/checkout")
def purchase_product(request: PurchaseRequest):
    order = {
        "customer_id": request.customer_id,
        "product_id": request.product_id,
        "timestamp": datetime.utcnow()
    }
    mongo_db["orders"].insert_one(order)
    return {"success": True, "message": "Purchase completed successfully"}
