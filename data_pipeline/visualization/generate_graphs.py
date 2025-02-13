import pandas as pd
import matplotlib.pyplot as plt
from sqlalchemy import create_engine

# 📌 Connect to PostgreSQL
POSTGRES_URL = "postgresql://postgres:password@postgres_db/ecommerce"
pg_engine = create_engine(POSTGRES_URL)

# 📌 Load Fraud Data
query = "SELECT fraud_score FROM fraud_alerts"
df = pd.read_sql(query, pg_engine)

# 📌 Plot Fraud Score Distribution
plt.hist(df["fraud_score"], bins=20, color="red", alpha=0.7)
plt.title("Fraud Score Distribution")
plt.xlabel("Fraud Score")
plt.ylabel("Count")
plt.show()
