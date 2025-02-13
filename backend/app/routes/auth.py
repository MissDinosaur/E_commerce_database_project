from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from app.models.database import get_db

router = APIRouter()

class RegisterRequest(BaseModel):
    username: str
    customer_id: str

@router.post("/register")
def register_user(request: RegisterRequest):
    # Store user in the PostgreSQL database
    db = next(get_db())
    db.execute("INSERT INTO customers (customer_id, customer_unique_id) VALUES (%s, %s)",
               (request.customer_id, request.username))
    db.commit()
    return {"success": True, "customer_id": request.customer_id}

class LoginRequest(BaseModel):
    username: str

@router.post("/login")
def login_user(request: LoginRequest):
    return {"success": True, "customer_id": request.username}
