from neo4j import GraphDatabase
import pandas as pd
import os
import sqlite3

# Load environment variables
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./olist.sqlite")
NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")

# Connect to SQLite
sqlite_connector = sqlite3.connect(SQLITE_DB_PATH)

# Load fraud-labeled customer data
cursor_logs_df = pd.read_sql("SELECT customer_id, fraud_label FROM cursor_logs", con=sqlite_connector)

df_list = cursor_logs_df.values.tolist()

# Connect to Neo4j
neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def insert_fraud_relationship(tx, data):
    customer_id, fraud_label = data

    if fraud_label == 1:
        tx.run("""
            MERGE (c:Customer {customer_id: $customer_id})
            SET c.fraud_risk = 'HIGH'
        """, customer_id=customer_id)
    else:
        tx.run("""
            MERGE (c:Customer {customer_id: $customer_id})
            SET c.fraud_risk = 'LOW'
        """, customer_id=customer_id)

# Execute insertions
with neo4j_driver.session() as session:
    for record in df_list:
        session.write_transaction(insert_fraud_relationship, record)

print("📌 Customer fraud risk stored in Neo4j.")

# Close connections
sqlite_connector.close()
neo4j_driver.close()
