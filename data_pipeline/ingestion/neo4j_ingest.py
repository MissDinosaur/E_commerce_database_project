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

# Load data from SQLite
neo4j_table = "order_payments"
df = pd.read_sql(sql=f"SELECT * FROM {neo4j_table}", con=sqlite_connector)
df_list = df.values.tolist()

# Connect to Neo4j
neo4j_driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def insert_into_neo4j(tx, data):
    tx.run("""
        MERGE (o:Order {order_id: $order_id})
        SET o.payment_sequential = $payment_sequential,
            o.payment_type = $payment_type,
            o.payment_installments = $payment_installments,
            o.payment_value = $payment_value
    """, order_id=data[0], payment_sequential=data[1], payment_type=data[2], 
         payment_installments=data[3], payment_value=data[4])

# Execute insertions
with neo4j_driver.session() as session:
    for record in df_list:
        session.write_transaction(insert_into_neo4j, record)

print("order_payments data stored in Neo4j.")

# Close connections
sqlite_connector.close()
neo4j_driver.close()
