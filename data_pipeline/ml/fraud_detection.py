import pandas as pd
import joblib
from app.models.database import get_db, mongo_db, neo4j_driver

# Load trained fraud model
model = joblib.load("app/ml/fraud_model.pkl")

def load_latest_data():
    db = next(get_db())
    latest_order = db.execute(
        "SELECT order_id, customer_id, payment_value, payment_installments FROM order_payments ORDER BY order_id DESC LIMIT 1"
    ).fetchone()

    cursor_logs = list(mongo_db["cursor_logs"].find({"customer_id": latest_order.customer_id}))

    with neo4j_driver.session() as session:
        result = session.run("""
            MATCH (c:Customer)-[:MADE]->(o:Order) 
            WHERE c.customer_id = $customer_id
            RETURN COUNT(o) AS order_count
        """, customer_id=latest_order.customer_id)
        fraud_connections = result.single()["order_count"] if result.single() else 0

    return latest_order, cursor_logs, fraud_connections

def extract_features(order, cursor_logs, fraud_connections):
    cursor_avg_speed = sum(log["x"] + log["y"] for log in cursor_logs) / len(cursor_logs) if cursor_logs else 0

    features = {
        "order_id": order.order_id,
        "customer_id": order.customer_id,
        "payment_value": order.payment_value,
        "installments": order.payment_installments,
        "order_count": fraud_connections,
        "cursor_avg_speed": cursor_avg_speed,
    }
    return pd.DataFrame([features])

def predict_fraud():
    order, cursor_logs, fraud_connections = load_latest_data()
    features = extract_features(order, cursor_logs, fraud_connections)
    fraud_score = model.predict_proba(features)[0][1]

    return {
        "order_id": order.order_id,
        "customer_id": order.customer_id,
        "fraud_score": fraud_score,
        "risk_level": "HIGH" if fraud_score > 0.7 else "LOW"
    }
