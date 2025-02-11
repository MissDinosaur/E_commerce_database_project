db = db.getSiblingDB("fraud_detection");

db.createCollection("cursor_logs");

db.cursor_logs.createIndex({ customer_id: 1, timestamp: 1 });

print("MongoDB initialized with cursor_logs collection.");
