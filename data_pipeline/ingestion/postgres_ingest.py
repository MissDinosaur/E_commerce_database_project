import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine

# Load environment variables
POSTGRES_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', 'password')} \
    @{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'ecommerce')}"
SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "./olist.sqlite")

sqlit_connector = sqlite3.connect(SQLITE_DB_PATH)
cursor = sqlit_connector.cursor()

pg_engine = create_engine(POSTGRES_URL)

# Store PostgreSQL Tables
pg_tables = ["customers", "leads_closed", "leads_qualified", "order_items", 
             "order_payments", "orders", "product_category_name_translation", "sellers"]

for table in pg_tables:
    df = pd.read_sql(sql=f"SELECT * FROM {table}", con=sqlit_connector)
    df.to_sql(table, pg_engine, if_exists="replace", index=False)
    print(f"{table} stored in PostgreSQL.")

# Close connections
sqlit_connector.close()

print("🎯 Data migration to PostgreSQL completed successfully!")