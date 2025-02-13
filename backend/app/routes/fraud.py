from fastapi import APIRouter
from app.models.database import neo4j_driver, get_db, mongo_db
from app.ml.fraud_detection import predict_fraud

router = APIRouter()

@router.get("/fraud_detection")
def detect_fraud():
    # 1️⃣ Run the ML Model for Fraud Prediction
    fraud_result = predict_fraud()

    # 2️⃣ Get Neo4j Fraud Risk (Customer's Fraud Network Size)
    with neo4j_driver.session() as session:
        result = session.run("""
            MATCH (c:Customer)-[:MADE]->(o:Order) 
            WHERE c.customer_id = $customer_id
            RETURN COUNT(o) AS order_count
        """, customer_id=fraud_result["customer_id"])
        fraud_network_size = result.single()["order_count"] if result.single() else 0

    # 3️⃣ Combine Neo4j Graph Analysis & ML Model
    final_risk_level = "HIGH" if fraud_result["fraud_score"] > 0.7 or fraud_network_size > 5 else "LOW"

    # 4️⃣ Log High-Risk Transactions for Manual Review (Optional)
    if final_risk_level == "HIGH":
        db = next(get_db())
        db.execute("INSERT INTO fraud_alerts (customer_id, fraud_score, risk_level) VALUES (%s, %s, %s)",
                   (fraud_result["customer_id"], fraud_result["fraud_score"], final_risk_level))
        db.commit()

    return {
        "customer_id": fraud_result["customer_id"],
        "fraud_score": fraud_result["fraud_score"],
        "fraud_network_size": fraud_network_size,
        "risk_level": final_risk_level
    }
