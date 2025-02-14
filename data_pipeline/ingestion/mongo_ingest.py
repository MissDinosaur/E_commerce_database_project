import os
import sqlite3
import pymongo
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

# Load environment variables
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "/app/data/olist.sqlite")    #"../data/olist.sqlite"

# Connect to SQLite
sqlite_connector = sqlite3.connect(SQLITE_DB_PATH)
time.sleep(10)  # Ensure the DB is ready

# Connect to MongoDB
mongo_client = pymongo.MongoClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}/")
mongo_db = mongo_client["ecommerce"]  # Set default database

# Check if table exists
cursor = sqlite_connector.cursor()
cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders';")
table_exists = cursor.fetchone()

if not table_exists:
    raise Exception("⚠️ Error: Table 'orders' does not exist in SQLite!")

# 1️⃣ Generate Cursor Log Data (80% Normal, 20% Fraud)  # count: 12392782, LIMIT 100000
orders_df = pd.read_sql("SELECT DISTINCT customer_id FROM orders LIMIT 100000", con=sqlite_connector)

cursor_logs = []
batch_size = 5000  # Store logs in batches

for _, row in orders_df.iterrows():
    customer_id = row["customer_id"]

    # Assign 80% normal behavior, 20% fraud behavior
    is_fraud = np.random.choice([0, 1], p=[0.8, 0.2])

    # Simulate session time (1-5 min)
    session_start = datetime.utcnow()
    session_duration = np.random.randint(60, 300)  # 1-5 minutes

    # Generate random cursor movement data
    for i in range(np.random.randint(50, 200)):  # 50 to 200 cursor events per session
        time_offset = timedelta(seconds=np.random.randint(session_duration))
        timestamp = session_start + time_offset

        # Normal users have smoother movement, fraud users have erratic jumps
        if is_fraud:
            x = np.random.randint(0, 1920)  # Random erratic movement (Full screen range)
            y = np.random.randint(0, 1080)
            speed = np.random.uniform(3, 8)  # High speed for fraud
            click_intensity = np.random.randint(10, 50)  # Heavy clicks
        else:
            x = np.random.randint(100, 1800)  # More controlled movement
            y = np.random.randint(100, 900)
            speed = np.random.uniform(0.5, 3)  # Normal speed
            click_intensity = np.random.randint(1, 10)  # Normal clicking

        cursor_logs.append({
            "customer_id": customer_id,
            "x": x,
            "y": y,
            "timestamp": timestamp.isoformat(),
            "cursor_speed": speed,
            "click_intensity": click_intensity,
            "fraud_label": int(is_fraud)
        })

    # Batch insert to MongoDB for performance
    if len(cursor_logs) >= batch_size:
        mongo_db["cursor_logs"].insert_many(cursor_logs)
        cursor_logs = []

# Insert remaining logs
if cursor_logs:
    mongo_db["cursor_logs"].insert_many(cursor_logs)

# Close connections
sqlite_connector.close()
mongo_client.close()

print("📌 Cursor logs (80-20 fraud split) generated and stored in MongoDB.")
