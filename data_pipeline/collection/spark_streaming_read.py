from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col
from pyspark.sql.types import StructType, StringType, StructField


## ================== read data from Kafka ================================================
POSTGRES_USER = "postgres"
POSTGRES_PASSWORD = "password"
KAFKA_BOOTSTRAP_SERVERS = "kafka:9092" 
KAFKA_TOPIC = "orders_stream" 
POSTGRES_URL = "postgresql://postgres:password@postgres:5432/ecommerce"
JDBC_POSTGRES_URL = "jdbc:postgresql://postgres:5432/ecommerce"
# Clean data rules
#pattern = re.compile(r'^[a-zA-Z0-9\s.,!?\'"()-]*$')


print(f"KAFKA_BOOTSTRAP_SERVERS: {KAFKA_BOOTSTRAP_SERVERS}\n JDBC_POSTGRES_URL: {JDBC_POSTGRES_URL}")
# Initialize Spark session
# set the config: if local resource is running out then close the check point. 
print("Start a spark serssion")
spark = SparkSession.builder \
    .appName("KafkaSparkStreamingECommerce") \
    .config("spark.jars.packages", 
            "org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1,org.postgresql:postgresql:42.5.0") \
    .getOrCreate()

# Define the schema of incoming Kafka messages
orders_schema = StructType([
    StructField("order_id", StringType(), True),
    StructField("customer_id", StringType(), True),
    StructField("product_id", StringType(), True)
])

# Set log level to WARN to reduce verbosity
spark.sparkContext.setLogLevel("WARN")


## ================== Store data into PostgreSQL ================================================

# Write Streaming Data to PostgreSQL
def write_to_postgres(batch_df, batch_id):
    batch_df.write \
        .format("jdbc") \
        .option("url", JDBC_POSTGRES_URL) \
        .option("dbtable", KAFKA_TOPIC) \
        .option("user", POSTGRES_USER) \
        .option("password", POSTGRES_PASSWORD) \
        .option("driver", "org.postgresql.Driver") \
        .mode("append") \
        .save()

def parse_streaming_data(binary_df):
    # Kafka messages have the value in binary, so cast it to string
    print("Start to parse binary_df successfully")
    orders_df = binary_df.selectExpr("CAST(value AS STRING) as json_str")
    print(f"orders_df is: {orders_df}")
    ## column name should aligh with th field names of customer in PostgreSQL
    # convert key and value from binary to string
    # Parse the JSON messages using the schema defined above
    orders_parsed_df = orders_df.select(from_json(col("json_str"), orders_schema).alias("order_data")) \
        .select("order_data.*")
    print("Parse binary_df successfully")
    print(f"orders_parsed_df is: {orders_parsed_df}")

    return orders_parsed_df


if __name__ == "__main__":
    print("Kafka and Spark streaming")

    print("Start to read Kafka data into binary_df")
    binary_df = spark \
      .readStream \
      .format("kafka") \
      .option("kafka.bootstrap.servers", KAFKA_BOOTSTRAP_SERVERS) \
      .option("subscribe", KAFKA_TOPIC) \
      .option("startingOffsets", "earliest") \
      .load()
    print("Read Kafka data into binary_df successfully")
    print(f"binary_df is {binary_df}")

    orders_parsed_df = parse_streaming_data(binary_df)

    print("Start to store orders_parsed_df into Postgresql")
    # Apply function to write in micro-batches
    query = orders_parsed_df.writeStream \
        .foreachBatch(write_to_postgres) \
        .outputMode("append") \
        .trigger(processingTime="10 seconds") \
        .start() \

    print("Store orders_parsed_df into Postgresql successfully")
    
    query.awaitTermination()
    print("Success")