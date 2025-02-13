from fastapi import APIRouter
from app.models.database import neo4j_driver, get_db
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

    # 3️⃣ Determine Fraud Alert Flag (High-Risk Transactions)
    fraud_threshold = 0.7
    alert_flag = fraud_result["fraud_score"] > fraud_threshold or fraud_network_size > 5

    # 4️⃣ Store Fraud Alert in PostgreSQL
    db = next(get_db())
    db.execute("""
        INSERT INTO fraud_alerts (order_id, customer_id, fraud_score, alert_flag)
        VALUES (%s, %s, %s, %s)
    """, (fraud_result["order_id"], fraud_result["customer_id"], fraud_result["fraud_score"], alert_flag))
    db.commit()

    return {
        "customer_id": fraud_result["customer_id"],
        "order_id": fraud_result["order_id"],
        "fraud_score": fraud_result["fraud_score"],
        "fraud_network_size": fraud_network_size,
        "alert_flag": alert_flag,
        "risk_level": "HIGH" if alert_flag else "LOW"
    }
