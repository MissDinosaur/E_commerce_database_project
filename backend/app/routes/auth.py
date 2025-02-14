from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.database import get_db, postgres_engine
from sqlalchemy import Table, MetaData

router = APIRouter()

class RegisterRequest(BaseModel):
    username: str
    customer_id: str

@router.post("/register")
def register_user(request: RegisterRequest):
    # Store user in the PostgreSQL database
    metadata = MetaData()
    customers = Table('customers', metadata, autoload_with=postgres_engine)
    with postgres_engine.connect() as conn:
        insert_stmt = customers.insert().values(customer_id=request.customer_id, customer_unique_id=request.username)
        conn.execute(insert_stmt)
        conn.commit()
    return {"success": True, "customer_id": request.customer_id}

class LoginRequest(BaseModel):
    username: str

@router.post("/login")
def login_user(request: LoginRequest):
    return {"success": True, "customer_id": request.username}
