from fastapi import APIRouter, Depends
from app.models.database import get_db, postgres_engine
from sqlalchemy import MetaData, Table, select, func

router = APIRouter()

@router.get("/products")
def get_products():
    LIMIT_NUM = 5
    metadata = MetaData()
    products = Table('products', metadata, autoload_with=postgres_engine)
    order_items = Table('order_items', metadata, autoload_with=postgres_engine)
    stmt = select(products.c.product_id, products.c.product_category_name, order_items.c.product_id, order_items.c.price) \
                .select_from(products.outerjoin(order_items, order_items.c.product_id == products.c.product_id)) \
                .order_by(func.random()).limit(LIMIT_NUM)
    with postgres_engine.connect() as conn:
        results = conn.execute(stmt).fetchall()
        products_list = [{"product_id": row[0], "product_category_name": row[1], "price": row[3]} for row in results]
    return products_list
