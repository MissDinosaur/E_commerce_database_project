import pandas as pd
from sqlalchemy import create_engine

# 📌 Connect to PostgreSQL
POSTGRES_URL = "postgresql://postgres:password@postgres_db/ecommerce_db"
pg_engine = create_engine(POSTGRES_URL)

# 📌 Load Transactions
query = "SELECT * FROM order_payments"
df = pd.read_sql(query, pg_engine)

# 📌 Transform Data
df["payment_category"] = df["payment_value"].apply(lambda x: "HIGH" if x > 500 else "LOW")

# 📌 Save Transformed Data
df.to_sql("transformed_order_payments", pg_engine, if_exists="replace", index=False)
print("✅ Data transformation complete.")
