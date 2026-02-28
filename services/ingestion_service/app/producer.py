import json
import time
from kafka import KafkaProducer
from config import KAFKA_BOOTSTRAP_SERVERS, KAFKA_TOPIC, AQI_API_KEY, CITY
from aqi_client import fetch_aqi

producer = KafkaProducer(
    bootstrap_servers=KAFKA_BOOTSTRAP_SERVERS,
    value_serializer=lambda v: json.dumps(v).encode("utf-8")
)

def run_producer():
    while True:
        data = fetch_aqi(CITY, AQI_API_KEY)
        producer.send(KAFKA_TOPIC, value=data)
        print("Produced message:", data)
        producer.flush()
        print(f"Message sent to Kafka for city: {CITY}")
        time.sleep(15)

if __name__ == "__main__":
    run_producer()