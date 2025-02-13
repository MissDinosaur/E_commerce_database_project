import psycopg2

# Connect to PostgreSQL
conn = psycopg2.connect("dbname=ecommerce_db user=postgres password=password host=postgres_db")
cur = conn.cursor()

# Function to store fraud alerts in PostgreSQL
def log_fraud_alert(order_id, customer_id, fraud_score, alert_flag):
    cur.execute(
        "INSERT INTO fraud_alerts (order_id, customer_id, fraud_score, alert_flag) VALUES (%s, %s, %s, %s)",
        (order_id, customer_id, fraud_score, alert_flag),
    )
    conn.commit()

print("✅ PostgreSQL fraud logging system ready.")
