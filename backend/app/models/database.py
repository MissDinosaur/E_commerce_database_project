from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
import pymongo
from neo4j import GraphDatabase

# PostgreSQL Connection
DATABASE_URL = "postgresql://postgres:yourpassword@postgres_db/ecommerce"
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# MongoDB Connection
mongo_client = pymongo.MongoClient("mongodb://mongo_db:27017/")
mongo_db = mongo_client["fraud_logs"]

# Neo4j Connection
neo4j_driver = GraphDatabase.driver("bolt://neo4j_db:7687", auth=("neo4j", "password"))

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
