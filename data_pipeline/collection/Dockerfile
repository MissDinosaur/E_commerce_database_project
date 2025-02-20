# Use Bitnami's Spark image as a base
FROM bitnami/spark:latest

# Switch to root to install extra packages if needed
USER root

# Install additional Python packages
RUN pip install pyspark kafka-python psycopg2-binary

# Set the working directory
WORKDIR /app

# Copy your Spark streaming script into the image
COPY Kafka_produce_data.py spark_streaming_read.py /app/

# Switch back to the non-root user if needed (check Bitnami's documentation for the correct user)
USER 1001


# Define the default command to run the Spark streaming job
CMD ["spark-submit", \
     "--master", "spark://spark-master:7077", \
     "--packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.0.1,org.postgresql:postgresql:42.5.0", \
     "/app/spark_streaming_read.py"]
