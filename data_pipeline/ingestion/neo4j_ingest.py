from neo4j import GraphDatabase
import pandas as pd
import os
import sqlite3


# Load environment variables
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./olist.sqlite")
NEO4J_URI = ""
NEO4J_USER = ""
NEO4J_PASSWORD = ""

sqlit_connector = sqlite3.connect(SQLITE_DB_PATH)
cursor = sqlit_connector.cursor()

neo4j_table = "order_payments"
df = pd.read_sql(sql=f"SELECT * FROM {neo4j_table}", con=sqlit_connector)
df_list = df.values.tolist()

execution_commands = []
for ele in df_list: 
    # columns: order_id, payment_sequential, payment_type, payment_installments, payment_value
    neo4j_create_statement = "create (t: order_payments {order_id:" + str(ele[0]) \
                            + ", payment_sequential:" + str(ele[1]) \
                            + "payment_type:" + str(ele[2]) \
                            + "payment_installments: " + str(ele[3]) \
                            + "payment_value: "+ str(ele[3]) +"})"
    execution_commands.append(neo4j_create_statement)

def execute_commands(commands):
    connection = GraphDatabase.driver(uri = NEO4J_URI, auth={NEO4J_USER, NEO4J_PASSWORD})
    session = connection.session()
    for command in commands:
        session.run(command)
    
execute_commands(commands=execution_commands)

print(f"{neo4j_table} stored in Neo4j.")