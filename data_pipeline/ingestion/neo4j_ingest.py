from neo4j import GraphDatabase
import os
import pymongo
import psycopg2

# Load environment variables
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://neo4j_db:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")
MONGO_HOST = os.getenv("MONGO_HOST", "mongo_db")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
POSTGRES_HOST = os.getenv("POSTGRES_HOST", "postgres_db")
POSTGRES_PORT = int(os.getenv("POSTGRES_PORT", "5432"))
POSTGRES_DB = os.getenv("POSTGRES_DB", "ecommerce")
POSTGRES_USER = os.getenv("POSTGRES_USER", "postgres")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "password")

print("🔄 Starting Neo4j Ingestion Script...")
try:
    # Connect to PostgreSQL
    print("📌 Connecting to PostgreSQL...")
    pg_conn = psycopg2.connect(
        host=POSTGRES_HOST,
        port=POSTGRES_PORT,
        dbname=POSTGRES_DB,
        user=POSTGRES_USER,
        password=POSTGRES_PASSWORD,
    )
    pg_cursor = pg_conn.cursor()
    print("✅ Connected to PostgreSQL.")
    
    # Connect to MongoDB
    print("📌 Connecting to MongoDB...")
    mongo_client = pymongo.MongoClient(host=MONGO_HOST, port=MONGO_PORT)
    db = mongo_client["ecommerce"]
    logs_collection = db["cursor_logs"]  # ✅ Fetch logs from MongoDB
    print("✅ Connected to MongoDB.")
    
    # Connect to Neo4j
    print("📌 Connecting to Neo4j...")
    neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD), max_connection_lifetime=30)
    print("✅ Connected to Neo4j.")
    
    def ingest_to_neo4j(tx, query, parameters):
        tx.run(query, **parameters)
    
    # Fetch and insert data from PostgreSQL
    queries = {
        "customers": "SELECT customer_id, customer_unique_id, customer_zip_code_prefix, customer_city, customer_state FROM customers",
        "orders": "SELECT order_id, customer_id, order_status, order_purchase_timestamp FROM orders",
        "payments": "SELECT order_id, payment_type, payment_installments, payment_value FROM order_payments",
        "fraud_alerts": "SELECT customer_id, fraud_score FROM fraud_alerts WHERE fraud_score IS NOT NULL"
    }
    
    with neo4j_driver.session() as session:
        for table, query in queries.items():
            pg_cursor.execute(query)
            records = pg_cursor.fetchall()
            
            for record in records:
                if table == "customers":
                    session.execute_write(ingest_to_neo4j, """
                        MERGE (c:Customer {customer_id: $customer_id})
                        ON CREATE SET c.customer_unique_id = $customer_unique_id, c.customer_zip_code_prefix = $customer_zip_code_prefix,
                        c.customer_city = $customer_city, c.customer_state = $customer_state
                    """, {
                        "customer_id": record[0],
                        "customer_unique_id": record[1],
                        "customer_zip_code_prefix": record[2],
                        "customer_city": record[3],
                        "customer_state": record[4]
                    })
                elif table == "orders":
                    session.execute_write(ingest_to_neo4j, """
                        MERGE (o:Order {order_id: $order_id})
                        ON CREATE SET o.order_status = $order_status, 
                        o.order_purchase_timestamp = datetime($order_purchase_timestamp)
                        WITH o
                        MATCH (c:Customer {customer_id: $customer_id})
                        MERGE (c)-[:PLACED]->(o)
                    """, {
                        "order_id": record[0],
                        "customer_id": record[1],
                        "order_status": record[2],
                        "order_purchase_timestamp": record[3]
                    })
                elif table == "payments":
                    session.execute_write(ingest_to_neo4j, """
                        MERGE (p:Payment {payment_id: $order_id})
                        ON CREATE SET p.payment_value = toFloat($payment_value), p.installments = toInteger($payment_installments)
                        WITH p
                        MATCH (o:Order {order_id: $order_id})
                        MERGE (o)-[:PAID_WITH]->(p)
                    """, {
                        "order_id": record[0],
                        "payment_value": record[3],
                        "payment_installments": record[2]
                    })
                elif table == "fraud_alerts":
                    session.execute_write(ingest_to_neo4j, """
                        MATCH (c:Customer {customer_id: $customer_id})
                        SET c.fraud_score = $fraud_score
                    """, {
                        "customer_id": record[0],
                        "fraud_score": record[1]
                    })

        # ✅ Insert `cursor_logs` from MongoDB into Neo4j
        logs_cursor = logs_collection.find()
        count = 0
        for log in logs_cursor:
            log_id = str(log["_id"])  # ✅ Convert `_id` (ObjectId) to string

            count += 1
            session.execute_write(ingest_to_neo4j, """
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
                "log_id": log_id,  # ✅ Converted `_id`
                "customer_id": log.get("customer_id", None),
                "x": log.get("x", None),
                "y": log.get("y", None),
                "event_time": log["timestamp"],  # ✅ Ensure timestamp format is valid
                "cursor_speed": log.get("cursor_speed", None),
                "click_intensity": log.get("click_intensity", None),
                "fraud_label": log.get("fraud_label", None)
            })
            print("✅ Log inserted successfully!")

    print(f"✅ {count} logs inserted into Neo4j.")
    print("✅ Data successfully ingested into Neo4j.")
    pg_cursor.close()
    pg_conn.close()
    mongo_client.close()
    neo4j_driver.close()

except Exception as e:
    print(f"❌ Error: {e}")
