// 1️⃣ Create Indexes for Faster Querying
CREATE INDEX FOR (c:Customer) ON (c.customer_id);
CREATE INDEX FOR (o:Order) ON (o.order_id);
CREATE INDEX FOR (p:Payment) ON (p.payment_id);
CREATE INDEX FOR (l:Log) ON (l.log_id);

// 2️⃣ Load Data from PostgreSQL
// Customers
MERGE (c:Customer {customer_id: row.customer_id})
ON CREATE SET c.customer_unique_id = row.customer_unique_id, c.customer_zip_code_prefix = row.customer_zip_code_prefix,
c.customer_city = row.customer_city, c.customer_state = row.customer_state;

// Orders
MERGE (o:Order {order_id: row.order_id})
ON CREATE SET o.customer_id = row.customer_id, o.order_status = row.order_status, 
o.order_purchase_timestamp = datetime(row.order_purchase_timestamp);

// Payments
MERGE (p:Payment {payment_id: row.payment_id})
ON CREATE SET p.payment_value = toFloat(row.payment_value), p.installments = toInteger(row.payment_installments);

// Logs
MERGE (l:Log {log_id: row.log_id})
ON CREATE SET l.event_type = row.event_type, l.event_time = datetime(row.event_time);

// Establish relationships
MATCH (c:Customer {customer_id: row.customer_id})
MATCH (o:Order {order_id: row.order_id})
MATCH (p:Payment {payment_id: row.payment_id})
MATCH (l:Log {log_id: row.log_id})
MERGE (c)-[:PLACED]->(o)
MERGE (o)-[:PAID_WITH]->(p)
MERGE (c)-[:GENERATED]->(l)
MERGE (l)-[:RELATED_TO]->(o);