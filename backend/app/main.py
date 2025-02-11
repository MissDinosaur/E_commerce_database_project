from fastapi import FastAPI, HTTPException, Depends
from pydantic import BaseModel
import sqlite3
from datetime import datetime

app = FastAPI()

def get_db_connection():
    conn = sqlite3.connect("/mnt/data/extracted_files/olist.sqlite")
    conn.row_factory = sqlite3.Row
    return conn

# User Registration
class RegisterRequest(BaseModel):
    username: str

@app.post("/api/register")
def register_user(request: RegisterRequest):
    customer_id = request.username  # Username is used as Customer ID
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO customers (customer_id, customer_unique_id, customer_city, customer_state)
            VALUES (?, ?, ?, ?)
        """, (customer_id, customer_id, "Unknown City", "Unknown State"))
        conn.commit()
    except sqlite3.IntegrityError:
        raise HTTPException(status_code=400, detail="Customer already exists")
    finally:
        conn.close()
    return {"customer_id": customer_id}

# User Login
class LoginRequest(BaseModel):
    customer_id: str

@app.post("/api/login")
def login_user(request: LoginRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT 1 FROM customers WHERE customer_id = ?", (request.customer_id,))
    user = cursor.fetchone()
    conn.close()
    if user:
        return {"success": True}
    raise HTTPException(status_code=401, detail="Invalid credentials")

# Fetch Products
@app.get("/api/products")
def get_products():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT product_id, product_category_name, product_weight_g AS price FROM products LIMIT 10")
    products = cursor.fetchall()
    conn.close()
    return [dict(product) for product in products]

# Purchase API
class PurchaseRequest(BaseModel):
    product_id: str
    customer_id: str

@app.post("/api/purchase")
def make_purchase(request: PurchaseRequest):
    order_id = str(datetime.timestamp(datetime.now())).replace('.', '')[:10]  # Unique order ID
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("SELECT product_weight_g AS price FROM products WHERE product_id = ?", (request.product_id,))
        product = cursor.fetchone()
        if not product:
            raise HTTPException(status_code=404, detail="Product not found")
        
        cursor.execute("""
            INSERT INTO orders (order_id, customer_id, order_status, order_purchase_timestamp)
            VALUES (?, ?, ?, ?)
        """, (order_id, request.customer_id, "processing", datetime.now()))
        
        cursor.execute("""
            INSERT INTO order_items (order_id, product_id, price, freight_value)
            VALUES (?, ?, ?, ?)
        """, (order_id, request.product_id, product["price"], 5))  # Dummy freight value
        conn.commit()
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
    return {"message": "Order placed successfully", "order_id": order_id}

# Cursor Tracking API
class CursorLogRequest(BaseModel):
    x: int
    y: int
    customer_id: str

@app.post("/api/log_cursor")
def log_cursor_position(request: CursorLogRequest):
    conn = get_db_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO geolocation (geolocation_zip_code_prefix, geolocation_lat, geolocation_lng, geolocation_city, geolocation_state)
            VALUES (?, ?, ?, ?, ?)
        """, ("00000", request.x, request.y, "Unknown City", "Unknown State"))  # Dummy data for city/state
        conn.commit()
    except sqlite3.Error as e:
        raise HTTPException(status_code=500, detail=str(e))
    finally:
        conn.close()
    return {"message": "Cursor position logged"}
