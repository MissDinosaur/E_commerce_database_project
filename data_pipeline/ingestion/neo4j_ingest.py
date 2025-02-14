from neo4j import GraphDatabase
import pandas as pd
import os
import pymongo
import time

# Load environment variables
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j_db:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
MONGO_HOST = os.getenv("MONGO_HOST", "mongo_db")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))

print("🔄 Starting Neo4j Ingestion Script...")
try:
    # Connect to MongoDB
    print("📌 Connecting to MongoDB...")
    mongo_client = pymongo.MongoClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}/")
    mongo_db = mongo_client["ecommerce"]
    time.sleep(15)

    # Fetch cursor logs from MongoDB
    cursor_logs = list(mongo_db["cursor_logs"].find({}, {"_id": 0, "customer_id": 1, "fraud_label": 1}))
    cursor_logs_df = pd.DataFrame(cursor_logs)
    print(f"📌 Found {len(cursor_logs_df)} records in cursor_logs.")

except Exception as e:
    print(f"❌ MongoDB Connection Failed: {e}")
    exit(1)

try:
    # Connect to Neo4j
    print(f"📌 Connecting to Neo4j at {NEO4J_URI}...")
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))
    print("✅ Connected to Neo4j successfully!")

except Exception as e:
    print(f"❌ Neo4j Connection Failed: {e}")
    exit(1)


# Connect to Neo4j
neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def insert_fraud_relationship(tx, batch_data):
    """
    Inserts fraud risk information in Neo4j in batch.
    """
    query = """
    UNWIND $batch as record
    CREATE (c:Customer {customer_id: record.customer_id, fraud_risk: CASE record.fraud_label WHEN 1 THEN 'HIGH' ELSE 'LOW' END});
    """

    try:
        tx.run(query, batch=batch_data)
    except Exception as e:
        print(f"❌ Error inserting batch: {e}")

# Batch Processing for Better Performance
batch_size = 1000
inserted_count = 0
failed_batches = 0

with neo4j_driver.session() as session:
    batch = []
    for index, row in cursor_logs_df.iterrows():
        if pd.isna(row["customer_id"]) or pd.isna(row["fraud_label"]):
            print(f"⚠️ Skipping record with missing data: {row}")
            continue  # Skip invalid records

        batch.append({"customer_id": row["customer_id"], "fraud_label": int(row["fraud_label"])})

        if len(batch) >= batch_size:
            print(f"🔄 Inserting batch of {len(batch)} records... (Index {index})")
            try:
                session.write_transaction(insert_fraud_relationship, batch)
                inserted_count += len(batch)
                print(f"✅ Successfully inserted {len(batch)} records. Total: {inserted_count}")
            except Exception as e:
                failed_batches += 1
                print(f"❌ Batch failed! Error: {e}")
            batch = []

    # Insert remaining batch
    if batch:
        print(f"🔄 Inserting final batch of {len(batch)} records...")
        try:
            session.write_transaction(insert_fraud_relationship, batch)
            inserted_count += len(batch)
            print(f"✅ Successfully inserted final {len(batch)} records. Total: {inserted_count}")
        except Exception as e:
            failed_batches += 1
            print(f"❌ Final batch failed! Error: {e}")

print(f"✅ Total {inserted_count} customer fraud risk records stored in Neo4j.")
if failed_batches > 0:
    print(f"⚠️ Warning: {failed_batches} batches failed.")

# Close connections
neo4j_driver.close()
mongo_client.close()
