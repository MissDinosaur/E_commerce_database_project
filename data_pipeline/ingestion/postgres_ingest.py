import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine

# Load environment variables
POSTGRES_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', 'password')}@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'ecommerce')}"
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./olist.sqlite")

# Connect to SQLite
sqlite_connector = sqlite3.connect(SQLITE_DB_PATH)

# Connect to PostgreSQL
pg_engine = create_engine(POSTGRES_URL)

# Fetch all tables from SQLite
query = "SELECT name FROM sqlite_master WHERE type='table';"
tables = pd.read_sql(query, sqlite_connector)["name"].tolist()

# Store all tables in PostgreSQL
for table in tables:
    try:
        df = pd.read_sql(sql=f"SELECT * FROM {table}", con=sqlite_connector)
        df.to_sql(table, pg_engine, if_exists="replace", index=False)
        print(f"{table} stored in PostgreSQL.")
    except Exception as e:
        print(f"Error storing {table} in PostgreSQL: {e}")

# Close connections
sqlite_connector.close()
print("📌 All tables migrated to PostgreSQL successfully!")
