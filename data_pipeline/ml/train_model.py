from sqlalchemy import create_engine
import pandas as pd
import joblib
import pymongo
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
import os

# PostgreSQL Connection
POSTGRES_URL = "postgresql://postgres:password@postgres_db/ecommerce"
pg_engine = create_engine(POSTGRES_URL)

# Fetch Transactions from PostgreSQL
transactions_query = """
SELECT o.order_id, o.customer_id, p.payment_value, p.payment_installments 
FROM order_payments p
JOIN orders o ON o.order_id = p.order_id
"""
transactions_df = pd.read_sql(transactions_query, pg_engine)

# Fetch Fraud Scores from PostgreSQL
fraud_query = """
SELECT customer_id, fraud_score FROM fraud_alerts WHERE fraud_score IS NOT NULL;
"""
fraud_df = pd.read_sql(fraud_query, pg_engine)

# Connect to MongoDB for Cursor Logs
mongo_client = pymongo.MongoClient("mongodb://mongo_db:27017/")
mongo_db = mongo_client["ecommerce"]
cursor_logs = list(mongo_db["cursor_logs"].find())

# Convert Cursor Logs to DataFrame and remove `_id`
cursor_df = pd.DataFrame(cursor_logs)

# Remove `_id` column since it's an ObjectId
if "_id" in cursor_df.columns:
    cursor_df.drop(columns=["_id"], inplace=True)

# Ensure 'customer_id' exists before merging
if "customer_id" not in cursor_df.columns:
    cursor_df["customer_id"] = None  # Create empty column if missing

# Merge PostgreSQL + MongoDB Data
merged_df = transactions_df.merge(cursor_df, on="customer_id", how="left")
merged_df = merged_df.merge(fraud_df, on="customer_id", how="left")

# Convert fraud_score to float (fixing future warning)
merged_df["fraud_score"] = merged_df["fraud_score"].fillna(0).astype(float)

# Select only numeric columns for model training
X = merged_df.select_dtypes(include=["number"]).drop(columns=["order_id", "customer_id"], errors="ignore")

# Define Labels
y = (merged_df["fraud_score"] > 0.5).astype(int)  # Label fraud if fraud score > 0.5

# Train/Test Split
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train Fraud Model
model = RandomForestClassifier(n_estimators=100, random_state=42)
model.fit(X_train, y_train)

# Define Save Paths
container_model_path = "/app/ml/fraud_model.pkl"
local_model_path = "fraud_model.pkl"

# Ensure the directory exists
os.makedirs(os.path.dirname(container_model_path), exist_ok=True)

# Save Model in Container
joblib.dump(model, container_model_path)

# Save Model Locally
joblib.dump(model, local_model_path)

print(f"✅ Fraud model trained and saved successfully.")
print(f"📌 Inside container: {container_model_path}")
print(f"📌 Locally: {local_model_path}")
