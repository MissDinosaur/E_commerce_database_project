from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pymongo
from neo4j import GraphDatabase
import os
#from kafka import KafkaProducer


POSTGRES_URL = f"postgresql://{os.getenv('POSTGRES_USER', 'postgres')}:{os.getenv('POSTGRES_PASSWORD', 'password')}@{os.getenv('POSTGRES_HOST', 'postgres')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'ecommerce')}"
# PostgreSQL Connection
# POSTGRES_URL = "postgresql://postgres:yourpassword@postgres_db/ecommerce"
postgres_engine = create_engine(POSTGRES_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=postgres_engine)

# MongoDB Connection
MONGO_HOST = os.getenv("MONGO_HOST", "localhost")
MONGO_PORT = int(os.getenv("MONGO_PORT", "27017"))
mongo_client = pymongo.MongoClient(f"mongodb://{MONGO_HOST}:{MONGO_PORT}/")
mongo_db = mongo_client["fraud_logs"]

# Neo4j Connection
NEO4J_HOST = os.getenv("NEO4J_HOST", "localhost")  # neo4j_db
neo4j_driver = GraphDatabase.driver(f"bolt://{NEO4J_HOST}:7687", auth=("neo4j", "password"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
