import os
import sqlite3
import pymongo
import pandas as pd

# Load environment variables
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./olist.sqlite")

# Connect to SQLite
sqlite_connector = sqlite3.connect(SQLITE_DB_PATH)

# Connect to MongoDB
mongo_client = pymongo.MongoClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}/")
mongo_db = mongo_client["ecommerce"]  # Set default database

# Tables to store in MongoDB
mongo_tables = ["geolocation", "order_reviews", "products"]

for table in mongo_tables:
    try:
        df = pd.read_sql(f"SELECT * FROM {table}", con=sqlite_connector)
        records = df.to_dict(orient="records")
        mongo_db[table].insert_many(records)
        print(f"{table} stored in MongoDB.")
    except Exception as e:
        print(f"Error storing {table} in MongoDB: {e}")

# Close connections
sqlite_connector.close()
mongo_client.close()
