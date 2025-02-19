import os
import sqlite3
import pymongo
import pandas as pd
import numpy as np
import time
from datetime import datetime, timedelta

def mongo():
    # ✅ Load environment variables (default values)
    MONGO_HOST = os.getenv("MONGO_HOST", "mongo_db")
    MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "/app/data/olist.sqlite")

    # ✅ Wait to ensure SQLite is ready
    time.sleep(10)

    # ✅ Connect to SQLite Database
    try:
        sqlite_connector = sqlite3.connect(SQLITE_DB_PATH)
        cursor = sqlite_connector.cursor()
        print(f"📌 Connected to SQLite at {SQLITE_DB_PATH}")
    except Exception as e:
        print(f"❌ SQLite connection error: {e}")
        exit(1)

    # ✅ Check if "orders" table exists in SQLite
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='orders';")
    table_exists = cursor.fetchone()
    if not table_exists:
        print("⚠️ Error: Table 'orders' does not exist in SQLite!")
        sqlite_connector.close()
        exit(1)

    # ✅ Connect to MongoDB
    try:
        mongo_client = pymongo.MongoClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}/")
        mongo_db = mongo_client["ecommerce"]  # Use "ecommerce" database
        print("📌 Connected to MongoDB")
    except Exception as e:
        print(f"❌ MongoDB connection error: {e}")
        exit(1)

    # ✅ Check if cursor logs already exist
    existing_count = mongo_db["cursor_logs"].count_documents({})
    if existing_count >= 99441:
        print(f"📌 Cursor logs already exist in MongoDB ({existing_count} records). Skipping insertion.")
        sqlite_connector.close()
        mongo_client.close()
        exit(0)  # Stop execution if logs already exist

    # ✅ Fetch Customer IDs from Orders Table
    orders_df = pd.read_sql("SELECT DISTINCT customer_id FROM orders LIMIT 100000", con=sqlite_connector)

    print("📌 Generating new cursor logs for MongoDB...")

    # ✅ Cursor Log Generation (80% Normal, 20% Fraud)
    cursor_logs = []
    batch_size = 20000  # Optimized batch size for MongoDB

    for _, row in orders_df.iterrows():
        customer_id = row["customer_id"]

        # Assign 80% normal behavior, 20% fraud behavior
        is_fraud = int(np.random.choice([0, 1], p=[0.5, 0.5]))

        # Simulate session time (1-5 min)
        session_start = datetime.utcnow()
        session_duration = np.random.randint(60, 300)  # 1-5 minutes
        timestamp = session_start + timedelta(seconds=session_duration)

        # Normal users have smooth movement, fraud users have erratic jumps
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
            "x": int(x),
            "y": int(y),
            "timestamp": timestamp.isoformat(),
            "cursor_speed": float(speed),
            "click_intensity": int(click_intensity),
            "fraud_label": int(is_fraud)
        })

        # ✅ Batch insert to MongoDB for performance
        if len(cursor_logs) >= batch_size:
            mongo_db["cursor_logs"].insert_many(cursor_logs)
            print(f"📌 Inserted {len(cursor_logs)} logs into MongoDB...")
            cursor_logs = []  # Reset batch

    # ✅ Insert remaining logs
    if cursor_logs:
        mongo_db["cursor_logs"].insert_many(cursor_logs)
        print(f"📌 Inserted final batch of {len(cursor_logs)} logs into MongoDB.")

    print("✅ Cursor logs (80-20 fraud split) generated and stored in MongoDB.")

    # ✅ Close Connections
    sqlite_connector.close()
    mongo_client.close()
    
if __name__ == "__main__":
    mongo()
