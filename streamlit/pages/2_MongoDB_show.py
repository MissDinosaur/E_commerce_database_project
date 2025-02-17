import pandas as pd
from pymongo import MongoClient
import streamlit as st

mongo_client = MongoClient("mongodb://localhost:27017")    
#ecommerce_db = mongo_client["ecommerce"] 
#mongo_db_names = mongo_client.list_database_names()
created_db_names = ["ecommerce", "fraud_detection"]


def show_mongodb_all_tables():
    for db_name in created_db_names:
        print(f"DB_names: {db_name}")
        db = mongo_client[db_name] 
        collection_names = db.list_collection_names()
        for collection_name in collection_names:
            collection = db[collection_name]
            count = collection.count_documents({})
            st.write(f"databse: {db_name}, collection: {collection_name}, dcoument count: {count}")


def check_data(db_name, collection_name, size, query_filter, projection):
    db = mongo_client[db_name]
    collection = db[collection_name]
    #documents  = list(collection.find({}, limit=size))
    documents = None
    print(f"query_filter {query_filter}, projection: {projection}")
    if query_filter is not None and query_filter != "":
        key, value = query_filter.split(":", 1)  # split into two parts
        query_filter = {key: value}
        if projection is not None and projection != "":
            key, value = projection.split(":", 1)  # split into two parts
            projection = {key: value}
            documents = collection.find(query_filter, projection, limit=size)
        else:
            documents = collection.find(query_filter, limit=size)        
    else:
        if projection is not None and projection != "":
            key, value = projection.split(":", 1)  # split into two parts
            projection = {key: value}
            documents = collection.find(projection, limit=size)
        else:
            documents = collection.find(limit=size)
    st.json(list(documents))


if __name__ == "__main__":   
    st.write("# Welcme to PostgreSQL")
    #st.write("All the collections in the 'ecommerce' DB")
    #show_mongodb_all_tables()

    st.write("* Check data")
    db_option = st.selectbox("Which DB you wanna check?", tuple(created_db_names))
    collection_option = st.selectbox("Which collection you wanna check?", tuple(mongo_client[db_option].list_collection_names()))
    
    st.write("Filter condition")
    col1, col2 = st.columns(2)
    with col1:
        example_filter = "customer_id: 12345678"
        filter = st.text_input("Type into the filter", placeholder=example_filter)
    with col2:
        example_projection = "_id: 0"
        #customer_id:9ef432eb6251297304e76186b10a928d
        projection = st.text_input("Type into projection", placeholder=example_projection)

    size = st.slider("How many rows you wanna check?", 1, 100, 5)
    
    st.write(f"You selected to check data of tabel: {collection_option} in databse: {db_option}")
    
    check_button = st.button("Check", type="primary")
    if check_button:
        check_data(db_option, collection_option, size, filter, projection)