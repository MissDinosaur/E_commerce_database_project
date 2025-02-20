import pymongo

# Connect to MongoDB
mongo_client = pymongo.MongoClient("mongodb://mongo_db:27017/")
mongo_db = mongo_client["fraud_logs"]

# Function to log cursor activity in Neo4j
def log_cursor_activity(customer_id, x, y):
    log_entry = {"customer_id": customer_id, "x": x, "y": y}
    mongo_db["cursor_logs"].insert_one(log_entry)

print("✅ Neo4j logs system ready.")
