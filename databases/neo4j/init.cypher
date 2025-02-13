// 1️⃣ Create Indexes for Faster Querying
CREATE INDEX FOR (c:Customer) ON (c.customer_id);
CREATE INDEX FOR (o:Order) ON (o.order_id);
CREATE INDEX FOR (p:Payment) ON (p.payment_id);

// 2️⃣ Load Transactions & Payments (from PostgreSQL Data)
LOAD CSV WITH HEADERS FROM 'file:///transactions.csv' AS row
MERGE (c:Customer {customer_id: row.customer_id})
MERGE (o:Order {order_id: row.order_id})
MERGE (p:Payment {payment_id: row.payment_id, payment_value: toFloat(row.payment_value), installments: toInteger(row.installments)})
MERGE (c)-[:MADE]->(o)
MERGE (o)-[:HAS_PAYMENT]->(p);

// 3️⃣ Compute Fraud Risk Scores Using Transaction Patterns
MATCH (c:Customer)-[:MADE]->(o:Order)-[:HAS_PAYMENT]->(p:Payment)
WITH c, 
     COUNT(o) AS total_orders, 
     SUM(p.payment_value) AS total_spent, 
     SUM(CASE WHEN p.payment_value > 1000 THEN 1 ELSE 0 END) AS high_value_txn
WITH c, total_orders, total_spent, high_value_txn,
     (0.5 * high_value_txn + 0.3 * total_orders + 0.2 * total_spent / 5000) AS fraud_score
MERGE (c)-[:FRAUD_SCORE]->(:FraudProfile {fraud_score: fraud_score});
