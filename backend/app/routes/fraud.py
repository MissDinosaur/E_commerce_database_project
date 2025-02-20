from fastapi import APIRouter, HTTPException
from app.models.database import neo4j_driver, get_db
from predict import predict_fraud  # Import fraud prediction function

router = APIRouter()

@router.get("/fraud_detection/{order_id}")
def detect_fraud(order_id: str):
    # Run fraud detection model
    fraud_result = predict_fraud(order_id)

    if "error" in fraud_result:
        raise HTTPException(status_code=404, detail=fraud_result["error"])

    # Extract prediction results
    customer_id = fraud_result["customer_id"]
    fraud_score = fraud_result["fraud_score"]
    is_fraud = fraud_result["is_fraud"]

    # Get Fraud Network Size from Neo4j
    with neo4j_driver.session() as session:
        result = session.run("""
            MATCH (c:Customer {customer_id: $customer_id})-[:FRAUD_SCORE]->(f:FraudProfile)
            RETURN f.fraud_score AS fraud_network_size
        """, customer_id=customer_id)
        fraud_network_size = result.single()["fraud_network_size"] if result.single() else 0

    # Determine Fraud Alert
    fraud_threshold = 0.5  # Consider fraud score > 0.5 as fraudulent
    alert_flag = is_fraud or fraud_network_size > 5  # If fraud model OR network is high risk

    # Store Fraud Alert in PostgreSQL
    db = next(get_db())
    try:
        db.execute("""
            INSERT INTO fraud_alerts (order_id, customer_id, fraud_score, alert_flag)
            VALUES (%s, %s, %s, %s)
        """, (order_id, customer_id, fraud_score, alert_flag))
        db.commit()
    except Exception as e:
        print(f"Error executing query for fraud_alerts in PostgreSQL: {e}")

    # Return Fraud Status
    return {
        "order_id": order_id,
        "customer_id": customer_id,
        "fraud_score": fraud_score,
        "fraud_network_size": fraud_network_size,
        "alert_flag": alert_flag,
        "risk_level": "HIGH" if alert_flag else "LOW"
    }
