from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.database import get_db, postgres_engine
from sqlalchemy import Table, MetaData, select

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
        stmt = select(customers).where(customers.c.customer_id == request.customer_id)
        result = conn.execute(stmt).fetchone()

        if result is not None:
            print(f"customer_id: {request.customer_id} already exists and will not be inserted")
        else:
            insert_stmt = customers.insert().values(customer_id=request.customer_id, customer_unique_id=request.username)
            conn.execute(insert_stmt)
            conn.commit()
            print(f"customer_id: {request.customer_id} and customer_unique_id: {request.username} is inserted successfully.")
        return {"success": True, "customer_id": request.customer_id}

class LoginRequest(BaseModel):
    username: str

@router.post("/login")
def login_user(request: LoginRequest):
    return {"success": True, "customer_id": request.username}
