from neo4j import GraphDatabase
import pandas as pd
import joblib
import psycopg2
import pymongo
from sqlalchemy import create_engine
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier

# Connect to PostgreSQL
POSTGRES_URL = "postgresql://postgres:password@postgres_db/ecommerce_db"
pg_engine = create_engine(POSTGRES_URL)

# Fetch Transactions from PostgreSQL
query = """
SELECT o.order_id, o.customer_id, p.payment_value, p.payment_installments 
FROM order_payments p
JOIN orders o ON o.order_id = p.order_id
"""
transactions_df = pd.read_sql(query, pg_engine)

# Connect to MongoDB for Cursor Logs
mongo_client = pymongo.MongoClient("mongodb://mongo_db:27017/")
mongo_db = mongo_client["fraud_logs"]
cursor_logs = list(mongo_db["train_cursor_logs"].find())

# Convert Cursor Logs to DataFrame
cursor_df = pd.DataFrame(cursor_logs)

# Connect to Neo4j
NEO4J_URI = "bolt://neo4j_db:7687"
NEO4J_USER = "neo4j"
NEO4J_PASSWORD = "password"
neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

# Fetch Fraud Network Data from Neo4j
def get_neo4j_fraud_data(tx):
    result = tx.run("""
        MATCH (c:Customer)-[:FRAUD_SCORE]->(f:FraudProfile)
        RETURN c.customer_id AS customer_id, f.fraud_score AS fraud_score
    """)
    return pd.DataFrame(result.data())

with neo4j_driver.session() as session:
    fraud_df = session.read_transaction(get_neo4j_fraud_data)

# Merge PostgreSQL + MongoDB + Neo4j Data
merged_df = transactions_df.merge(cursor_df, on="customer_id", how="left")
merged_df = merged_df.merge(fraud_df, on="customer_id", how="left")

# Fill missing fraud scores with 0
merged_df["fraud_score"].fillna(0, inplace=True)

# Define Features & Labels
X = merged_df.drop(columns=["order_id", "customer_id"])
y = (merged_df["fraud_score"] > 0.5).astype(int)  # Label fraud if fraud score > 0.5

# Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Fraud Model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Save Model
joblib.dump(model, "app/ml/fraud_model.pkl")
print("✅ Fraud model trained with Neo4j data and saved.")
