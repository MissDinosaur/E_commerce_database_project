import os
import subprocess

print("🚀 Running setup script...")

# 1️⃣ Setup PostgreSQL (Run init.sql)
print("📌 Setting up PostgreSQL...")
subprocess.run(["psql", "-h", "postgres_db", "-U", "postgres", "-d", "ecommerce_db", "-f", "databases/postgres/init.sql"])

# 2️⃣ Setup MongoDB (Run init.js)
print("📌 Setting up MongoDB...")
subprocess.run(["mongo", "mongo_db/fraud_logs", "databases/mongo/init.js"])

# 3️⃣ Setup Neo4j (Run init.cypher)
print("📌 Setting up Neo4j...")
subprocess.run(["cypher-shell", "-u", "neo4j", "-p", "password", "-f", "databases/neo4j/init.cypher"])

# 4️⃣ Run Data Ingestion Scripts
print("📌 Running data ingestion scripts...")
subprocess.run(["python", "data_pipeline/ingestion/postgres_ingest.py"])
subprocess.run(["python", "data_pipeline/ingestion/mongo_ingest.py"])
subprocess.run(["python", "data_pipeline/ingestion/neo4j_ingest.py"])

print("✅ Setup and initialization completed!")
