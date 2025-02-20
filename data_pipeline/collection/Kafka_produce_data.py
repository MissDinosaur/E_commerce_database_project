from kafka.admin import KafkaAdminClient, NewTopic
from kafka import KafkaProducer
import json
import time
import argparse


KAFKA_BOOTSTRAP_SERVERS = "kafka:9092"
KAFKA_TOPIC = "orders_stream"
DEFAULT_DATA = '[{"customer_id": "C012", "product_id": "P012", "order_id": "O012"}, \
                 {"customer_id": "C034", "product_id": "P034", "order_id": "O034"}]'

client = KafkaAdminClient(bootstrap_servers='kafka:9092')

new_topic = NewTopic(
    name=KAFKA_TOPIC,
    num_partitions=1,
    replication_factor=1
)

if KAFKA_TOPIC in client.list_topics():
    print(f"topic: {KAFKA_TOPIC} has existed.")
else:
    client.create_topics(new_topics=[new_topic], validate_only=False)
#client.list_topics()

# simulation the streaming data
def streaming_data_generator(sample_data):
    for record in sample_data:
        yield record
        time.sleep(1)  

def kafka_sent(streaming_data):
    try:
        # create Kafka producer，message code as UTF-8
        producer = KafkaProducer(bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
                                 value_serializer=lambda m: json.dumps(m).encode('utf-8') )
        for data in streaming_data:
            print("send streaming_data: ", data)
            producer.send(KAFKA_TOPIC, value=data)
            producer.flush()  # make sure message has been sent
    except Exception as e:
        print(e)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Kafka producing data script")
    parser.add_argument("data", 
                        nargs='?', 
                        default=DEFAULT_DATA, 
                        help="JSON string representing a list of dictionaries. Default value is: " + DEFAULT_DATA)
    args = parser.parse_args()
    
    try:
        # The argument should be a JSON string representing a list of dictionaries.
        sample_data = json.loads(args.data)
    except json.JSONDecodeError as e:
        print("Error: The provided argument is not valid JSON. Will use the default sample_data")
        print(e)

    streaming_data = streaming_data_generator(sample_data)
    kafka_sent(streaming_data)
    print("Kafka sent all the data out.")
