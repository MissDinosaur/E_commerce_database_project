import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text

# Load environment variables
POSTGRES_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', 'password')}@{os.getenv('POSTGRES_HOST', 'postgres')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'ecommerce')}"
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "/app/data/olist.sqlite")

# Connect to SQLite
sqlite_connector = sqlite3.connect(SQLITE_DB_PATH)

# Connect to PostgreSQL
pg_engine = create_engine(POSTGRES_URL)

# Fetch all tables from SQLite
query = "SELECT name FROM sqlite_master WHERE type='table';"
tables = pd.read_sql(query, sqlite_connector)["name"].tolist()

LIMIT_NUM = 100000
# Store all tables in PostgreSQL
for table in tables:
    try:
        df = pd.read_sql(f"SELECT * FROM {table} LIMIT {LIMIT_NUM}", con=sqlite_connector)
        with pg_engine.connect() as conn:
            # empty table before insert data 
            conn.execute(text(f"DELETE FROM {table};"))
            conn.commit()

        df.to_sql(table, pg_engine, if_exists="append", index=False)
        print(f"{table} is cleared and new data is inserted into PostgreSQL.")
    except Exception as e:
        print(f"Error storing {table} in PostgreSQL: {e}")

# Close connections
sqlite_connector.close()
print("📌 All tables migrated to PostgreSQL successfully!")
