from fastapi import APIRouter, Depends
from app.models.database import get_db

router = APIRouter()

@router.get("/products")
def get_products():
    db = next(get_db())
    result = db.execute("SELECT product_id, product_category_name, price FROM products LIMIT 2").fetchall()
    products = [{"product_id": row[0], "product_category_name": row[1], "price": row[2]} for row in result]
    return products
