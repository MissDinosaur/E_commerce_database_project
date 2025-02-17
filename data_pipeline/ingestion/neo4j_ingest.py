from neo4j import GraphDatabase
import os
import pymongo
import psycopg2
from psycopg2.extras import DictCursor
from concurrent.futures import ThreadPoolExecutor
import logging

# Set up logging
logging.basicConfig(filename='ingestion_errors.log', level=logging.ERROR, format='%(asctime)s:%(levelname)s:%(message)s')

# Load environment variables
def load_env_vars():
    return {
        "NEO4J_URI": os.getenv("NEO4J_URI", "bolt://neo4j_db:7687"),
        "NEO4J_USER": os.getenv("NEO4J_USER", "neo4j"),
        "NEO4J_PASSWORD": os.getenv("NEO4J_PASSWORD", "password"),
        "MONGO_HOST": os.getenv("MONGO_HOST", "mongo_db"),
        "MONGO_PORT": int(os.getenv("MONGO_PORT", "27017")),
        "POSTGRES_HOST": os.getenv("POSTGRES_HOST", "postgres_db"),
        "POSTGRES_PORT": int(os.getenv("POSTGRES_PORT", "5432")),
        "POSTGRES_DB": os.getenv("POSTGRES_DB", "ecommerce"),
        "POSTGRES_USER": os.getenv("POSTGRES_USER", "postgres"),
        "POSTGRES_PASSWORD": os.getenv("POSTGRES_PASSWORD", "password")
    }

env_vars = load_env_vars()

# Database connection setup
def connect_postgres(env):
    try:
        return psycopg2.connect(
            host=env["POSTGRES_HOST"],
            port=env["POSTGRES_PORT"],
            dbname=env["POSTGRES_DB"],
            user=env["POSTGRES_USER"],
            password=env["POSTGRES_PASSWORD"]
        )
    except psycopg2.Error as e:
        logging.error(f"Failed to connect to PostgreSQL: {e}")
        return None

def connect_mongo(env):
    try:
        return pymongo.MongoClient(host=env["MONGO_HOST"], port=env["MONGO_PORT"])
    except Exception as e:
        logging.error(f"Failed to connect to MongoDB: {e}")
        return None

def connect_neo4j(env):
    try:
        return GraphDatabase.driver(env["NEO4J_URI"], auth=(env["NEO4J_USER"], env["NEO4J_PASSWORD"]))
    except Exception as e:
        logging.error(f"Failed to connect to Neo4j: {e}")
        return None

# Neo4j ingestion logic based on table
def ingest_to_neo4j(session, table, record):
    try:
        if table == "customers":
            session.run("""
                MERGE (c:Customer {customer_id: $customer_id})
                ON CREATE SET c.customer_unique_id = $customer_unique_id, c.customer_zip_code_prefix = $customer_zip_code_prefix,
                c.customer_city = $customer_city, c.customer_state = $customer_state
            """, dict(record))
        elif table == "orders":
            session.run("""
                MERGE (o:Order {order_id: $order_id})
                ON CREATE SET o.order_status = $order_status, 
                o.order_purchase_timestamp = datetime($order_purchase_timestamp)
                WITH o
                MATCH (c:Customer {customer_id: $customer_id})
                MERGE (c)-[:PLACED]->(o)
            """, dict(record))
        elif table == "payments":
            session.run("""
                MERGE (p:Payment {payment_id: $order_id})
                ON CREATE SET p.payment_value = toFloat($payment_value), p.installments = toInteger($payment_installments)
                WITH p
                MATCH (o:Order {order_id: $order_id})
                MERGE (o)-[:PAID_WITH]->(p)
            """, dict(record))
        elif table == "fraud_alerts":
            session.run("""
                MATCH (c:Customer {customer_id: $customer_id})
                SET c.fraud_score = $fraud_score
            """, dict(record))
    except Exception as e:
        logging.error(f"Error ingesting data to Neo4j for table {table}: {e}")

# Fetch and process table data in batches using concurrent processing
def process_queries(pg_cursor, session, query_info):
    table, query = query_info
    try:
        pg_cursor.execute(query)
        records = pg_cursor.fetchmany(10000)
        while records:
            for record in records:
                ingest_to_neo4j(session, table, record)
            records = pg_cursor.fetchmany(10000)
    except Exception as e:
        logging.error(f"Error processing table {table}: {e}")

# Main ingestion function with error handling
def ingest_data():
    pg_conn = connect_postgres(env_vars)
    mongo_client = connect_mongo(env_vars)
    neo4j_driver = connect_neo4j(env_vars)

    if not pg_conn or not mongo_client or not neo4j_driver:
        logging.error("Database connection failed, terminating script.")
        return

    try:
        print("🔄 Starting Neo4j Ingestion Script...")
        with pg_conn, pg_conn.cursor(cursor_factory=DictCursor) as pg_cursor, neo4j_driver.session() as session:
            queries = {
                "customers": "SELECT customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state FROM customers limit 1000",
                "orders": "SELECT order_id, customer_id, order_status, order_purchase_timestamp FROM orders limit 1000",
                "payments": "SELECT order_id, payment_type, payment_installments, payment_value FROM order_payments limit 1000",
                "fraud_alerts": "SELECT customer_id, fraud_score FROM fraud_alerts WHERE fraud_score IS NOT NULL limit 1000"
            }
            with ThreadPoolExecutor(max_workers=4) as executor:
                executor.map(lambda x: process_queries(pg_cursor, session, x), queries.items())

        # MongoDB log ingestion to Neo4j
        db = mongo_client["ecommerce"]
        logs_collection = db["cursor_logs"]
        ingest_logs_to_neo4j(session, logs_collection)
        
    except Exception as e:
        logging.error(f"Unhandled error during data ingestion: {e}")
    finally:
        if pg_conn:
            pg_conn.close()
        if mongo_client:
            mongo_client.close()
        if neo4j_driver:
            neo4j_driver.close()
        print("✅ Ingestion process completed.")

# MongoDB log ingestion
def ingest_logs_to_neo4j(session, logs_collection):
    try:
        logs_cursor = logs_collection.find()
        for log in logs_cursor:
            log_id = str(log["_id"])  # Convert _id (ObjectId) to string
            session.run("""
                MERGE (l:Log {log_id: $log_id})
                ON CREATE SET 
                    l.customer_id = $customer_id, 
                    l.x = $x,
                    l.y = $y,
                    l.event_time = datetime($event_time),
                    l.cursor_speed = $cursor_speed,
                    l.click_intensity = $click_intensity,
                    l.fraud_label = $fraud_label
                WITH l
                MATCH (c:Customer {customer_id: $customer_id})
                MERGE (c)-[:GENERATED]->(l)
            """, {
                "log_id": log_id,
                "customer_id": log.get("customer_id", None),
                "x": log.get("x", None),
                "y": log.get("y", None),
                "event_time": log["timestamp"],
                "cursor_speed": log.get("cursor_speed", None),
                "click_intensity": log.get("click_intensity", None),
                "fraud_label": log.get("fraud_label", None)
            })
    except Exception as e:
        logging.error(f"Error ingesting logs to Neo4j: {e}")

if __name__ == "__main__":
    ingest_data()
