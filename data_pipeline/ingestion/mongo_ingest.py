import os
import sqlite3
import pymongo
import pandas as pd


# Load environment variables
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./olist.sqlite")


sqlit_connector = sqlite3.connect(SQLITE_DB_PATH)
cursor = sqlit_connector.cursor()

mongo_clinet = pymongo.MongoClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}/")
mongo_db = mongo_clinet['ecommerce']

# Store MongoDB Collections
mongo_tables = ["geolocation", "order_reviews", "products"]

for table in mongo_tables:
    df = pd.read_sql(f"SELECT * FROM {table}", con=sqlit_connector)
    records = df.to_dict(orient="records")
    mongo_db[table].insert_many(records)
    print(f" {table} stored in MongoDB.")

# Close connections
sqlit_connector.close()
mongo_clinet.close()

print("🎯 Data migration to MongoDB completed successfully!")
