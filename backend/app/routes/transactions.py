from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.database import get_db, mongo_db
from data_pipeline.ml.predict import predict_fraud
from datetime import datetime

router = APIRouter()

# Purchase Request Model
class PurchaseRequest(BaseModel):
    customer_id: str
    product_id: str
    order_id: str  # Ensure frontend provides an order_id

@router.post("/checkout")
def purchase_product(request: PurchaseRequest):
    # Step 1️⃣: Run Fraud Detection
    fraud_result = predict_fraud(request.order_id)

    if "error" in fraud_result:
        raise HTTPException(status_code=404, detail=fraud_result["error"])

    # Step 2️⃣: Check if Transaction is Fraudulent
    is_fraud = fraud_result["is_fraud"]
    fraud_score = fraud_result["fraud_score"]

    # Step 3️⃣: Log Transaction in MongoDB
    order = {
        "customer_id": request.customer_id,
        "product_id": request.product_id,
        "order_id": request.order_id,
        "timestamp": datetime.utcnow(),
        "fraud_score": fraud_score,
        "fraud_flag": is_fraud  # True if flagged as fraud
    }
    mongo_db["orders"].insert_one(order)

    # Step 4️⃣: Determine Payment Status
    if is_fraud:
        return {
            "success": False,
            "message": "🚨 Transaction logged but marked as fraud!",
            "fraud_score": fraud_score
        }

    return {
        "success": True,
        "message": "✅ Purchase successful!",
        "fraud_score": fraud_score
    }
