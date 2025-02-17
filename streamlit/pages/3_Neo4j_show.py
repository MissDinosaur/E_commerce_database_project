import os
from neo4j import GraphDatabase
import pandas as pd
import streamlit as st

NEO4J_URI = os.getenv("NEO4J_URI", "bolt://localhost:7687")
NEO4J_USER = os.getenv("NEO4J_USER", "neo4j")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD", "password")


driver = GraphDatabase.driver("bolt://localhost:7687", auth=("neo4j", "password"))


# Query function
def query_neo4j(query, parameters={}):
    with driver.session() as session:
        result = session.run(query, parameters)
        return pd.DataFrame([record.data() for record in result])  # Convert result to data frame

# Example: Get data
def check_data(table_option, size):
    query = ""
    if table_option == "Customer":
        query = f"MATCH (c:Customer) RETURN c.customer_unique_id, c.customer_zip_code_prefix, c.customer_city, c.customer_state LIMIT {size}"
    elif table_option == "Order":
        query = f"MATCH (o:Order) RETURN o.order_id AS order_id, o.order_status AS status LIMIT {size}"
    else:
        query = f"MATCH (p:Payment) RETURN p.order_id AS order_id, p.payment_value AS payment_value, p.installments LIMIT {size}"
    
    results = query_neo4j(query)
    st.dataframe(results, use_container_width=True)
    

if __name__ == "__main__":  
    st.write("# Welcme to Neo4J")

    table_option = st.selectbox("Which table you wanna check?", ("Customer", "Order", "Payment"))
    size = st.slider("How old are you?", 1, 100, 10)
    st.write("You selected:", table_option) 

    check_button = st.button("Check", type="primary")
    if check_button:
        check_data(table_option, size)