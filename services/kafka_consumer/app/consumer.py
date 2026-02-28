import json
import time
from kafka import KafkaConsumer
from database import insert_record

while True:
    try:
        consumer = KafkaConsumer(
            "aqi_stream",
            bootstrap_servers="kafka:9092",
            auto_offset_reset="earliest",
            enable_auto_commit=True,
            group_id="aqi_group",
            value_deserializer=lambda x: json.loads(x.decode("utf-8"))
        )
        print("Connected to Kafka!")
        break
    except Exception as e:
        print("Waiting for Kafka...", e)
        time.sleep(5)

for message in consumer:
    data = message.value
    insert_record(data)
    print("Inserted into Postgres")