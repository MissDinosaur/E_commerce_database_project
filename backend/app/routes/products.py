from fastapi import APIRouter
from app.models.database import get_db, postgres_engine
from sqlalchemy import MetaData, Table, select, func


router = APIRouter()

@router.get("/products")
def get_products():
    LIMIT_NUM = 5  # limit the number of product list
    metadata = MetaData()
    products = Table('products', metadata, autoload_with=postgres_engine)
    order_items = Table('order_items', metadata, autoload_with=postgres_engine)
    
    # products left join order_items to get the item price
    stmt = select(products.c.product_id, products.c.product_category_name, order_items.c.product_id, order_items.c.price) \
                .select_from(products.outerjoin(order_items, order_items.c.product_id == products.c.product_id)) \
                .order_by(func.random()).limit(LIMIT_NUM)
    
    # create the connection with Postgresql
    with postgres_engine.connect() as conn:
        results = conn.execute(stmt).fetchall()
        products_list = [{"product_id": row[0], "product_category_name": row[1], "price": row[3]} for row in results]
        print("generate products_list successfully")
    return products_list
