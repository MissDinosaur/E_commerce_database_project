import joblib
import pandas as pd
import psycopg2
import pymongo
from sqlalchemy import create_engine
from neo4j import GraphDatabase

# Load Fraud Model
model = joblib.load("app/ml/fraud_model.pkl")  # "should be ml/fraud_model.pkl" or /app/ml/fraud_model.pkl

# Connect to PostgreSQL
POSTGRES_URL = "postgresql://postgres:password@postgres_db/ecommerce"
pg_engine = create_engine(POSTGRES_URL)

# Connect to MongoDB
mongo_client = pymongo.MongoClient("mongodb://mongo_db:27017/")
mongo_db = mongo_client["fraud_logs"]

# Connect to Neo4j
NEO4J_URI = "bolt://neo4j_db:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"
neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Function to Fetch Fraud Network Data from Neo4j
def get_neo4j_fraud_data(customer_id):
    with neo4j_driver.session() as session:
        result = session.run("""
            MATCH (c:Customer {customer_id: $customer_id})-[:FRAUD_SCORE]->(f:FraudProfile)
            RETURN f.fraud_score AS fraud_score
        """, customer_id=customer_id)
        record = result.single()
        return record["fraud_score"] if record else 0  # Default fraud score = 0 if no record

# Function to Predict Fraud for a Transaction
def predict_fraud(order_id):
    # Fetch Transaction Data from PostgreSQL
    query = f"""
    SELECT o.order_id, o.customer_id, p.payment_value, p.payment_installments 
    FROM order_payments p
    JOIN orders o ON o.order_id = p.order_id
    WHERE o.order_id = '{order_id}'
    """
    transactions_df = pd.read_sql(query, pg_engine)

    if transactions_df.empty:
        return {"error": "Order ID not found"}

    # Fetch Cursor Logs from MongoDB
    customer_id = transactions_df["customer_id"].iloc[0]
    cursor_data = mongo_db["test_cursor_logs"].find_one({"customer_id": customer_id})
    
    if cursor_data:
        cursor_features = pd.DataFrame([cursor_data])
    else:
        cursor_features = pd.DataFrame([{"customer_id": customer_id, "cursor_avg_speed": 0}])  # Default values

    # Fetch Fraud Risk Score from Neo4j
    fraud_score = get_neo4j_fraud_data(customer_id)

    # Merge Features
    transactions_df = transactions_df.merge(cursor_features, on="customer_id", how="left")
    transactions_df["fraud_score"] = fraud_score  # Add fraud risk score from Neo4j

    # Drop Unnecessary Columns
    X = transactions_df.drop(columns=["order_id", "customer_id"])

    # Make Prediction
    prediction = model.predict(X)
    fraud_probability = model.predict_proba(X)[:, 1][0]
    is_fraud = bool(prediction[0])

    return {
        "order_id": order_id,
        "customer_id": customer_id,
        "fraud_score": fraud_probability,
        "is_fraud": is_fraud
    }

# Example Usage
if __name__ == "__main__":
    test_order_id = "example_order_id"  # Replace with actual test order ID
    result = predict_fraud(test_order_id)
    print(result)
