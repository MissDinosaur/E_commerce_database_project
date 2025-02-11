CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    customer_unique_id TEXT,
    customer_zip_code_prefix TEXT,
    customer_city TEXT,
    customer_state TEXT
);

CREATE TABLE IF NOT EXISTS orders (
    order_id TEXT PRIMARY KEY,
    customer_id TEXT REFERENCES customers(customer_id),
    order_status TEXT,
    order_purchase_timestamp TIMESTAMP,
    order_approved_at TIMESTAMP,
    order_delivered_carrier_date TIMESTAMP,
    order_delivered_customer_date TIMESTAMP,
    order_estimated_delivery_date TIMESTAMP
);

CREATE TABLE IF NOT EXISTS order_items (
    order_id TEXT REFERENCES orders(order_id),
    order_item_id INT,
    product_id TEXT,
    seller_id TEXT,
    shipping_limit_date TIMESTAMP,
    price FLOAT,
    freight_value FLOAT,
    PRIMARY KEY (order_id, order_item_id)
);

CREATE TABLE IF NOT EXISTS fraud_alerts (
    fraud_id SERIAL PRIMARY KEY,
    order_id TEXT REFERENCES orders(order_id),
    customer_id TEXT REFERENCES customers(customer_id),
    fraud_score FLOAT,
    alert_flag BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
