-- Customers Table
CREATE TABLE IF NOT EXISTS customers (
    customer_id TEXT PRIMARY KEY,
    customer_unique_id TEXT,
    customer_zip_code_prefix TEXT,
    customer_city TEXT,
    customer_state TEXT
);

-- Geolocation Table
CREATE TABLE IF NOT EXISTS geolocation (
    geolocation_zip_code_prefix TEXT,
    geolocation_lat FLOAT,
    geolocation_lng FLOAT,
    geolocation_city TEXT,
    geolocation_state TEXT
);

-- Leads Closed Table
CREATE TABLE IF NOT EXISTS leads_closed (
    mql_id TEXT PRIMARY KEY,
    seller_id TEXT,
    sdr_id TEXT,
    sr_id TEXT,
    won_date TIMESTAMP,
    business_segment TEXT,
    lead_type TEXT,
    lead_behaviour_profile TEXT,
    has_company BOOLEAN,
    has_gtin BOOLEAN
);

-- Leads Qualified Table
CREATE TABLE IF NOT EXISTS leads_qualified (
    mql_id TEXT PRIMARY KEY,
    first_contact_date TIMESTAMP,
    landing_page_id TEXT,
    origin TEXT
);

-- Orders Table
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

-- Order Items Table
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

-- ✅ Order Payments Table (Fix for Missing Table)
CREATE TABLE IF NOT EXISTS order_payments (
    order_id TEXT REFERENCES orders(order_id),
    payment_sequential INT,
    payment_type TEXT,
    payment_installments INT,
    payment_value FLOAT
);

-- Order Reviews Table
CREATE TABLE IF NOT EXISTS order_reviews (
    review_id TEXT PRIMARY KEY,
    order_id TEXT REFERENCES orders(order_id),
    review_score INT,
    review_comment_title TEXT,
    review_comment_message TEXT,
    review_creation_date TIMESTAMP,
    review_answer_timestamp TIMESTAMP
);

-- Product Category Translation Table
CREATE TABLE IF NOT EXISTS product_category_name_translation (
    product_category_name TEXT PRIMARY KEY,
    product_category_name_english TEXT
);

-- Products Table
CREATE TABLE IF NOT EXISTS products (
    product_id TEXT PRIMARY KEY,
    product_category_name TEXT,
    product_name_lenght INT,
    product_description_lenght INT,
    product_photos_qty INT,
    product_weight_g FLOAT,
    product_length_cm FLOAT,
    product_height_cm FLOAT,
    product_width_cm FLOAT
);

-- Sellers Table
CREATE TABLE IF NOT EXISTS sellers (
    seller_id TEXT PRIMARY KEY,
    seller_zip_code_prefix TEXT,
    seller_city TEXT,
    seller_state TEXT
);

-- ✅ Fraud Alerts Table (Extra Table for Fraud Detection)
CREATE TABLE IF NOT EXISTS fraud_alerts (
    fraud_id SERIAL PRIMARY KEY,
    order_id TEXT REFERENCES orders(order_id),
    customer_id TEXT REFERENCES customers(customer_id),
    fraud_score FLOAT,
    alert_flag BOOLEAN,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
