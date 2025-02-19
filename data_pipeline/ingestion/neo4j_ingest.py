from neo4j import GraphDatabase
import os
import pymongo
import psycopg2
from psycopg2.extras import DictCursor

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
    return psycopg2.connect(
        host=env["POSTGRES_HOST"],
        port=env["POSTGRES_PORT"],
        dbname=env["POSTGRES_DB"],
        user=env["POSTGRES_USER"],
        password=env["POSTGRES_PASSWORD"]
    )

def connect_mongo(env):
    return pymongo.MongoClient(host=env["MONGO_HOST"], port=env["MONGO_PORT"])

def connect_neo4j(env):
    return GraphDatabase.driver(env["NEO4J_URI"], auth=(env["NEO4J_USER"], env["NEO4J_PASSWORD"]))

# Main ingestion function
def ingest_data():
    try:
        print("🔄 Starting Neo4j Ingestion Script...")
        pg_conn = connect_postgres(env_vars)
        mongo_client = connect_mongo(env_vars)
        neo4j_driver = connect_neo4j(env_vars)
        
        print("✅ All databases connected.")
        with pg_conn, pg_conn.cursor(cursor_factory=DictCursor) as pg_cursor, neo4j_driver.session() as session:
            # PostgreSQL data fetching and ingestion to Neo4j
            queries = {
                "customers": "SELECT customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state FROM customers limit 2",
                "orders": "SELECT order_id, customer_id, order_status, order_purchase_timestamp FROM orders limit 2",
                "payments": "SELECT order_id, payment_type, payment_installments, payment_value FROM order_payments limit 2",
                "fraud_alerts": "SELECT customer_id, fraud_score FROM fraud_alerts WHERE fraud_score IS NOT NULL limit 2"
            }

            for table, query in queries.items():
                pg_cursor.execute(query)
                records = pg_cursor.fetchmany(1000)  # Batch processing
                
                while records:
                    for record in records:
                        ingest_to_neo4j(session, table, record)
                    records = pg_cursor.fetchmany(1000)
            # MongoDB log ingestion to Neo4j
            db = mongo_client["ecommerce"]
            logs_collection = db["cursor_logs"]
            ingest_logs_to_neo4j(session, logs_collection)
            
    except Exception as e:
        print(f"❌ Error during ingestion: {e}")
def ingest_to_neo4j(session, table, record):
    # Neo4j ingestion logic based on table
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

def ingest_logs_to_neo4j(session, logs_collection):
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

if __name__ == "__main__":
    ingest_data()