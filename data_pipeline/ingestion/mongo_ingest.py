import os
import sqlite3
import pymongo
import pandas as pd
import numpy as np

# Load environment variables
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./olist.sqlite")

# Connect to SQLite
sqlite_connector = sqlite3.connect(SQLITE_DB_PATH)

# Connect to MongoDB
mongo_client = pymongo.MongoClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}/")
mongo_db = mongo_client["ecommerce"]  # Set default database

# 1️⃣ Generate Cursor Log Data (80% Normal, 20% Fraud)
orders_df = pd.read_sql("SELECT DISTINCT customer_id FROM orders", con=sqlite_connector)

cursor_logs = []
for _, row in orders_df.iterrows():
    customer_id = row["customer_id"]
    
    # Generate random cursor movement data
    avg_speed = np.random.uniform(0.2, 2.5)  # Normal browsing speed
    click_intensity = np.random.randint(1, 10)  # Number of rapid clicks
    
    # 80-20 fraud split
    is_fraud = np.random.choice([0, 1], p=[0.8, 0.2])
    
    if is_fraud:
        avg_speed *= 2  # Fraudulent behavior: erratic fast movement
        click_intensity *= 2  # Fraudulent: very high click intensity

    cursor_logs.append({
        "customer_id": customer_id,
        "cursor_avg_speed": avg_speed,
        "click_intensity": click_intensity,
        "fraud_label": is_fraud  # Label fraud for training
    })

# 2️⃣ Store Cursor Logs in MongoDB
mongo_db["cursor_logs"].insert_many(cursor_logs)

# Close connections
sqlite_connector.close()
mongo_client.close()

print("📌 Cursor logs generated and stored in MongoDB (80-20 fraud split).")
