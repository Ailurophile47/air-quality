"""
Kafka Consumer for Urban Air Quality Data
Consumes messages from Kafka topics and stores them in PostgreSQL
"""

import os
import json
import signal
import sys
from datetime import datetime
from typing import Dict, Any

from kafka import KafkaConsumer
from kafka.errors import KafkaError
from dotenv import load_dotenv

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database.db_connection import get_db_session
from database.models import AQIData, WeatherData, TrafficData

# Load environment variables
load_dotenv()


class DataConsumer:
    """
    Multi-topic Kafka consumer
    Consumes AQI, weather, and traffic data and stores in PostgreSQL
    """
    
    def __init__(self):
        """Initialize Kafka consumer and database connection"""
        self.bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
        
        # Kafka topics
        self.topics = [
            os.getenv('KAFKA_TOPIC_AQI', 'aqi_data'),
            os.getenv('KAFKA_TOPIC_WEATHER', 'weather_data'),
            os.getenv('KAFKA_TOPIC_TRAFFIC', 'traffic_data')
        ]
        
        # Consumer group
        self.group_id = 'airquality_consumer_group'
        
        # Initialize consumer
        self.consumer = self._create_consumer()
        
        # Graceful shutdown handler
        signal.signal(signal.SIGINT, self._shutdown_handler)
        signal.signal(signal.SIGTERM, self._shutdown_handler)
        
        self.running = True
    
    def _create_consumer(self) -> KafkaConsumer:
        """Create and configure Kafka consumer with retry logic"""
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                consumer = KafkaConsumer(
                    *self.topics,
                    bootstrap_servers=self.bootstrap_servers,
                    group_id=self.group_id,
                    value_deserializer=lambda m: json.loads(m.decode('utf-8')),
                    auto_offset_reset='earliest',  # Start from beginning if no offset
                    enable_auto_commit=True,
                    auto_commit_interval_ms=5000,
                    max_poll_records=100,
                    session_timeout_ms=30000,
                    heartbeat_interval_ms=10000
                )
                print(f"✅ Kafka consumer connected to {self.bootstrap_servers}")
                print(f"📚 Subscribed to topics: {', '.join(self.topics)}")
                return consumer
            except KafkaError as e:
                print(f"❌ Kafka connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    import time
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise
    
    def _shutdown_handler(self, signum, frame):
        """Handle graceful shutdown on SIGINT/SIGTERM"""
        print("\n⏸️  Shutdown signal received. Closing consumer...")
        self.running = False
    
    def store_aqi_data(self, data: Dict[str, Any]) -> bool:
        """
        Store AQI data in PostgreSQL
        
        Args:
            data: AQI data dictionary
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            with get_db_session() as session:
                aqi_record = AQIData(
                    location=data.get('location'),
                    latitude=data.get('latitude'),
                    longitude=data.get('longitude'),
                    aqi=data.get('aqi'),
                    pm25=data.get('pm25'),
                    pm10=data.get('pm10'),
                    no2=data.get('no2'),
                    so2=data.get('so2'),
                    co=data.get('co'),
                    o3=data.get('o3'),
                    timestamp=datetime.fromisoformat(data.get('timestamp')),
                    source=data.get('source', 'UNKNOWN')
                )
                session.add(aqi_record)
                print(f"💾 Stored AQI: {data['location']} | AQI: {data['aqi']}")
                return True
        except Exception as e:
            print(f"❌ Error storing AQI data: {e}")
            return False
    
    def store_weather_data(self, data: Dict[str, Any]) -> bool:
        """
        Store weather data in PostgreSQL
        
        Args:
            data: Weather data dictionary
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            with get_db_session() as session:
                weather_record = WeatherData(
                    location=data.get('location'),
                    latitude=data.get('latitude'),
                    longitude=data.get('longitude'),
                    temperature=data.get('temperature'),
                    feels_like=data.get('feels_like'),
                    humidity=data.get('humidity'),
                    pressure=data.get('pressure'),
                    wind_speed=data.get('wind_speed'),
                    wind_direction=data.get('wind_direction'),
                    clouds=data.get('clouds'),
                    visibility=data.get('visibility'),
                    weather_main=data.get('weather_main'),
                    weather_description=data.get('weather_description'),
                    timestamp=datetime.fromisoformat(data.get('timestamp')),
                    source=data.get('source', 'UNKNOWN')
                )
                session.add(weather_record)
                print(f"💾 Stored Weather: {data['location']} | Temp: {data['temperature']}°C")
                return True
        except Exception as e:
            print(f"❌ Error storing weather data: {e}")
            return False
    
    def store_traffic_data(self, data: Dict[str, Any]) -> bool:
        """
        Store traffic data in PostgreSQL
        
        Args:
            data: Traffic data dictionary
            
        Returns:
            True if stored successfully, False otherwise
        """
        try:
            with get_db_session() as session:
                traffic_record = TrafficData(
                    location=data.get('location'),
                    latitude=data.get('latitude'),
                    longitude=data.get('longitude'),
                    congestion_level=data.get('congestion_level'),
                    congestion_score=data.get('congestion_score'),
                    average_speed=data.get('average_speed'),
                    vehicle_count=data.get('vehicle_count'),
                    timestamp=datetime.fromisoformat(data.get('timestamp')),
                    source=data.get('source', 'UNKNOWN')
                )
                session.add(traffic_record)
                print(f"💾 Stored Traffic: {data['location']} | Congestion: {data['congestion_level']}")
                return True
        except Exception as e:
            print(f"❌ Error storing traffic data: {e}")
            return False
    
    def process_message(self, message) -> None:
        """
        Process a single Kafka message and route to appropriate handler
        
        Args:
            message: Kafka message object
        """
        try:
            topic = message.topic
            data = message.value
            
            # Route to appropriate handler based on topic
            if 'aqi' in topic:
                self.store_aqi_data(data)
            elif 'weather' in topic:
                self.store_weather_data(data)
            elif 'traffic' in topic:
                self.store_traffic_data(data)
            else:
                print(f"⚠️  Unknown topic: {topic}")
                
        except Exception as e:
            print(f"❌ Error processing message: {e}")
    
    def consume(self) -> None:
        """
        Start consuming messages from Kafka topics
        Runs continuously until interrupted
        """
        print(f"\n🚀 Starting Kafka consumer")
        print(f"🔗 Kafka broker: {self.bootstrap_servers}")
        print(f"👥 Consumer group: {self.group_id}")
        print(f"📊 Listening to topics: {', '.join(self.topics)}\n")
        
        message_count = 0
        
        try:
            while self.running:
                # Poll for messages (timeout in milliseconds)
                messages = self.consumer.poll(timeout_ms=1000, max_records=50)
                
                for topic_partition, records in messages.items():
                    for message in records:
                        self.process_message(message)
                        message_count += 1
                        
                        # Print status every 50 messages
                        if message_count % 50 == 0:
                            print(f"📊 Processed {message_count} messages so far...")
                
        except KeyboardInterrupt:
            print("\n⏸️  Consumer interrupted by user")
        except Exception as e:
            print(f"\n❌ Consumer error: {e}")
        finally:
            self.close()
            print(f"\n✅ Total messages processed: {message_count}")
    
    def close(self) -> None:
        """Close Kafka consumer and cleanup resources"""
        if self.consumer:
            print("Closing Kafka consumer...")
            self.consumer.close()
            print("✅ Consumer closed successfully")


def main():
    """Main entry point for the consumer"""
    # Initialize database tables if not exists
    from database.db_connection import init_db, test_connection
    
    print("🔧 Checking database connection...")
    if test_connection():
        print("🔧 Initializing database schema...")
        init_db()
        
        # Start consumer
        consumer = DataConsumer()
        consumer.consume()
    else:
        print("❌ Cannot connect to database. Please check configuration.")
        sys.exit(1)


if __name__ == "__main__":
    main()