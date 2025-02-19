import os
import sqlite3
import pandas as pd
from sqlalchemy import create_engine, text

def postgres():
    # Load environment variables
    POSTGRES_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', 'password')}@{os.getenv('POSTGRES_HOST', 'postgres')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'ecommerce')}"
    SQLITE_DB_PATH = os.getenv("SQLITE_DB_PATH", "/app/data/olist.sqlite")

    # Connect to SQLite
    sqlite_connector = sqlite3.connect(SQLITE_DB_PATH)

    # Connect to PostgreSQL
    pg_engine = create_engine(POSTGRES_URL)

    # Fetch all tables from SQLite
    #query = "SELECT name FROM sqlite_master WHERE type='table';"
    #sqlite_tables = pd.read_sql(query, sqlite_connector)["name"].tolist()
    ordered_tables = ['order_items', 'order_payments', 'order_reviews', 'orders', 'customers', 'geolocation', 'products', 'product_category_name_translation', 'sellers', 'leads_qualified', 'leads_closed']

    LIMIT_NUM = 100000

    for table in ordered_tables:
        with pg_engine.connect() as conn:
            # empty table but not destroy the table structure before insert data 
            conn.execute(text(f"DELETE FROM {table};"))
            conn.commit()
    print("All table are cleared for the data ingestion.")

    existing_customer_ids = pd.read_sql(f"SELECT customer_id FROM customers", con=sqlite_connector)['customer_id'].tolist()
    existing_order_ids = pd.read_sql("SELECT order_id FROM orders", con=sqlite_connector)['order_id'].tolist()
    orders_tables_names = ["order_items", "order_payments", "order_reviews"]
    other_table_names = ['product_category_name_translation', 'sellers', 'geolocation', 'products', 'leads_qualified', 'leads_closed']

    customers_df = pd.read_sql(f"SELECT * FROM customers", con=sqlite_connector)
    orders_df = pd.read_sql(f"SELECT * FROM orders", con=sqlite_connector)

    customers_df.to_sql("customers", pg_engine, if_exists="append", index=False)
    print(f"New data is inserted into PostgreSQL table: customers.")

    # Store orders and it has REFERENCES with customers in PostgreSQL
    orders_df[orders_df['order_id'].isin(existing_order_ids)].to_sql("orders", pg_engine, if_exists="append", index=False)
    print(f"New data is inserted into PostgreSQL table: orders.")

    # Store tables having REFERENCES with orders in PostgreSQL
    for table in orders_tables_names:
        try:
            df = pd.read_sql(f"SELECT * FROM {table}", con=sqlite_connector)
            if table == "order_reviews":
                df = df.drop_duplicates(subset='review_id', keep='first') # remove duplicates of primary key
            df[df['order_id'].isin(existing_order_ids)].to_sql(table, pg_engine, if_exists="append", index=False)
            print(f"New data is inserted into PostgreSQL table: {table}.")
        except Exception as e:
            print(f"Error storing {table} in PostgreSQL: {e}")


    # Store all other tables without REFERENCES in PostgreSQL
    for table in other_table_names:
        try: 
            df = pd.read_sql(f"SELECT * FROM {table}", con=sqlite_connector)
            df.to_sql(table, pg_engine, if_exists="append", index=False)
            print(f"New data is inserted into PostgreSQL table: {table}.")
        except Exception as e:
            print(f"Error storing {table} in PostgreSQL: {e}")



    # Close connections
    sqlite_connector.close()
    print("📌 All tables migrated to PostgreSQL successfully!")

if __name__ == "__main__":
    postgres()