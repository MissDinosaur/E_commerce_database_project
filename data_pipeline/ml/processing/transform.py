import os
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import pymongo
from neo4j import GraphDatabase
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler

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

def connect_to_databases():
    """Establish connections to all required databases."""
    env_vars = load_env_vars()
    pg_engine = create_engine(
        f"postgresql://{env_vars['POSTGRES_USER']}:{env_vars['POSTGRES_PASSWORD']}@{env_vars['POSTGRES_HOST']}:{env_vars['POSTGRES_PORT']}/{env_vars['POSTGRES_DB']}",
        future=True
    )
    mongo_client = pymongo.MongoClient(host=env_vars["MONGO_HOST"], port=env_vars["MONGO_PORT"])
    neo4j_driver = GraphDatabase.driver(env_vars["NEO4J_URI"], auth=(env_vars["NEO4J_USER"], env_vars["NEO4J_PASSWORD"]))
    return pg_engine, mongo_client, neo4j_driver

def fetch_data(pg_engine, mongo_db, neo4j_driver):
    """Fetch and combine data from all sources."""
    # PostgreSQL query
    query = text("SELECT * FROM orders JOIN order_payments ON orders.order_id = order_payments.order_id;")
    with pg_engine.connect() as connection:
        df_pg = pd.read_sql_query(query, connection)
    
    # MongoDB query
    cursor_logs = mongo_db.cursor_logs.find({})
    df_mongo = pd.DataFrame(list(cursor_logs))
    
    if "_id" in df_mongo.columns:
        df_mongo.drop(columns=["_id"], inplace=True)
    
    # Keep only numeric and ID columns from PostgreSQL
    numeric_cols = df_pg.select_dtypes(include=['int64', 'float64']).columns
    id_cols = ['customer_id', 'order_id']
    keep_cols = list(set(numeric_cols).union(set(id_cols)))
    df_pg = df_pg[keep_cols]
    
    # Merge PostgreSQL and MongoDB data
    df = df_pg.merge(df_mongo, on="customer_id", how="left")
    
    # Neo4j data fetch (if still needed for other features)
    neo4j_query = "MATCH (c:Customer)-[r:MADE]->(o:Order) RETURN c.customer_id, o.order_id, o.fraud_score"
    with neo4j_driver.session() as session:
        results = session.run(neo4j_query)
        df_neo4j = pd.DataFrame([record.values() for record in results], 
                               columns=["customer_id", "order_id", "fraud_score"])
    
    # Merge Neo4j data if needed
    df = df.merge(df_neo4j, on="customer_id", how="left")
    
    # Prepare final features and target
    X = df.select_dtypes(include=['int64', 'float64'])
    
    # Use fraud_label from MongoDB as the target variable
    y = df["fraud_label"]  # Ensure this column exists in df
    
    # Drop fraud_score if it exists in X
    if 'fraud_score' in X.columns:
        X = X.drop(columns=['fraud_score'])
    
    return X, y

def prepare_data(X, y):
    """Prepare data for modeling by handling missing values and scaling."""
    if isinstance(X, pd.DataFrame):
        numeric_columns = X.select_dtypes(include=['int64', 'float64']).columns
        X = X[numeric_columns]
    
    # Handle missing values
    imputer = SimpleImputer(strategy='mean')
    X = imputer.fit_transform(X)
    
    # Scale features
    scaler = StandardScaler()
    X = scaler.fit_transform(X)
    
    return X, y

def get_transformed_data():
    """Main function to get transformed data ready for modeling."""
    pg_engine, mongo_client, neo4j_driver = connect_to_databases()
    mongo_db = mongo_client['ecommerce']
    X, y = fetch_data(pg_engine, mongo_db, neo4j_driver)
    
    # Validate data
    if len(np.unique(y)) < 2:
        print("Warning: Dataset contains only one class!")
        print(f"Total samples: {len(y)}")
        print(f"Unique classes: {np.unique(y)}")
        raise ValueError("Dataset must contain samples from at least 2 classes")
    
    X, y = prepare_data(X, y)
    return X, y