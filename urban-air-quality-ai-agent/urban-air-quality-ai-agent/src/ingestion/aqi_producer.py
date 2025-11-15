"""
Kafka Producer for Urban Air Quality Data
Fetches real-time AQI, weather, and traffic data and publishes to Kafka topics
"""

import os
import json
import time
import random
from datetime import datetime
from typing import Dict, Any, Optional

import requests
from kafka import KafkaProducer
from kafka.errors import KafkaError
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class DataProducer:
    """
    Multi-source data producer for Kafka
    Fetches and publishes AQI, weather, and traffic data
    """
    
    def __init__(self):
        """Initialize Kafka producer and API configurations"""
        self.bootstrap_servers = os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'kafka:9092')
        
        # Kafka topics
        self.aqi_topic = os.getenv('KAFKA_TOPIC_AQI', 'aqi_data')
        self.weather_topic = os.getenv('KAFKA_TOPIC_WEATHER', 'weather_data')
        self.traffic_topic = os.getenv('KAFKA_TOPIC_TRAFFIC', 'traffic_data')
        
        # API keys
        self.openweather_key = os.getenv('OPENWEATHER_API_KEY')
        self.aqicn_key = os.getenv('AQICN_API_KEY')
        self.google_maps_key = os.getenv('GOOGLE_MAPS_API_KEY')
        
        # Locations (Bangalore areas)
        self.locations = [
            {"name": "Koramangala", "lat": 12.9352, "lon": 77.6245},
            {"name": "Indiranagar", "lat": 12.9784, "lon": 77.6408},
            {"name": "Whitefield", "lat": 12.9698, "lon": 77.7500},
            {"name": "BTM Layout", "lat": 12.9165, "lon": 77.6101},
            {"name": "Electronic City", "lat": 12.8456, "lon": 77.6603},
        ]
        
        # Initialize Kafka producer
        self.producer = self._create_producer()
        
    def _create_producer(self) -> KafkaProducer:
        """Create and configure Kafka producer with retry logic"""
        max_retries = 5
        retry_delay = 5
        
        for attempt in range(max_retries):
            try:
                producer = KafkaProducer(
                    bootstrap_servers=self.bootstrap_servers,
                    value_serializer=lambda v: json.dumps(v).encode('utf-8'),
                    acks='all',  # Wait for all replicas to acknowledge
                    retries=3,
                    max_in_flight_requests_per_connection=1,
                    compression_type='gzip'
                )
                print(f"✅ Kafka producer connected to {self.bootstrap_servers}")
                return producer
            except KafkaError as e:
                print(f"❌ Kafka connection attempt {attempt + 1}/{max_retries} failed: {e}")
                if attempt < max_retries - 1:
                    print(f"Retrying in {retry_delay} seconds...")
                    time.sleep(retry_delay)
                else:
                    raise
    
    def fetch_aqi_data(self, location: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fetch AQI data from AQICN API
        Falls back to mock data if API unavailable
        """
        try:
            if self.aqicn_key and self.aqicn_key != "your_aqicn_api_key_here":
                # Real API call
                url = f"https://api.waqi.info/feed/geo:{location['lat']};{location['lon']}/"
                params = {"token": self.aqicn_key}
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    if data['status'] == 'ok':
                        aqi_data = data['data']
                        return {
                            "location": location['name'],
                            "latitude": location['lat'],
                            "longitude": location['lon'],
                            "aqi": aqi_data.get('aqi', 0),
                            "pm25": aqi_data.get('iaqi', {}).get('pm25', {}).get('v'),
                            "pm10": aqi_data.get('iaqi', {}).get('pm10', {}).get('v'),
                            "no2": aqi_data.get('iaqi', {}).get('no2', {}).get('v'),
                            "so2": aqi_data.get('iaqi', {}).get('so2', {}).get('v'),
                            "co": aqi_data.get('iaqi', {}).get('co', {}).get('v'),
                            "o3": aqi_data.get('iaqi', {}).get('o3', {}).get('v'),
                            "timestamp": datetime.utcnow().isoformat(),
                            "source": "AQICN"
                        }
            
            # Mock data (for testing or when API key not available)
            return self._generate_mock_aqi(location)
            
        except Exception as e:
            print(f"⚠️ Error fetching AQI data: {e}. Using mock data.")
            return self._generate_mock_aqi(location)
    
    def fetch_weather_data(self, location: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Fetch weather data from OpenWeather API
        Falls back to mock data if API unavailable
        """
        try:
            if self.openweather_key and self.openweather_key != "your_openweather_api_key_here":
                # Real API call
                url = "https://api.openweathermap.org/data/2.5/weather"
                params = {
                    "lat": location['lat'],
                    "lon": location['lon'],
                    "appid": self.openweather_key,
                    "units": "metric"
                }
                response = requests.get(url, params=params, timeout=10)
                
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "location": location['name'],
                        "latitude": location['lat'],
                        "longitude": location['lon'],
                        "temperature": data['main']['temp'],
                        "feels_like": data['main']['feels_like'],
                        "humidity": data['main']['humidity'],
                        "pressure": data['main']['pressure'],
                        "wind_speed": data['wind']['speed'],
                        "wind_direction": data['wind'].get('deg', 0),
                        "clouds": data['clouds']['all'],
                        "visibility": data.get('visibility', 10000),
                        "weather_main": data['weather'][0]['main'],
                        "weather_description": data['weather'][0]['description'],
                        "timestamp": datetime.utcnow().isoformat(),
                        "source": "OpenWeather"
                    }
            
            # Mock data
            return self._generate_mock_weather(location)
            
        except Exception as e:
            print(f"⚠️ Error fetching weather data: {e}. Using mock data.")
            return self._generate_mock_weather(location)
    
    def fetch_traffic_data(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """
        Fetch traffic data (using mock data for now)
        Google Maps API can be integrated later
        """
        # Mock traffic data (Google Maps API would require origin/destination)
        return self._generate_mock_traffic(location)
    
    def _generate_mock_aqi(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic mock AQI data"""
        # Time-based variation (higher pollution during peak hours)
        hour = datetime.now().hour
        peak_multiplier = 1.5 if (7 <= hour <= 10) or (17 <= hour <= 20) else 1.0
        
        base_aqi = random.randint(50, 150)
        aqi = int(base_aqi * peak_multiplier)
        
        return {
            "location": location['name'],
            "latitude": location['lat'],
            "longitude": location['lon'],
            "aqi": aqi,
            "pm25": round(random.uniform(20, 80) * peak_multiplier, 2),
            "pm10": round(random.uniform(30, 100) * peak_multiplier, 2),
            "no2": round(random.uniform(10, 50), 2),
            "so2": round(random.uniform(5, 30), 2),
            "co": round(random.uniform(200, 800), 2),
            "o3": round(random.uniform(20, 80), 2),
            "timestamp": datetime.utcnow().isoformat(),
            "source": "MOCK"
        }
    
    def _generate_mock_weather(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic mock weather data for Bangalore"""
        return {
            "location": location['name'],
            "latitude": location['lat'],
            "longitude": location['lon'],
            "temperature": round(random.uniform(20, 32), 1),
            "feels_like": round(random.uniform(22, 35), 1),
            "humidity": round(random.uniform(40, 80), 1),
            "pressure": round(random.uniform(1010, 1020), 1),
            "wind_speed": round(random.uniform(2, 8), 1),
            "wind_direction": random.randint(0, 360),
            "clouds": random.randint(0, 100),
            "visibility": random.randint(5000, 10000),
            "weather_main": random.choice(["Clear", "Clouds", "Rain", "Haze"]),
            "weather_description": random.choice(["clear sky", "few clouds", "scattered clouds", "light rain", "haze"]),
            "timestamp": datetime.utcnow().isoformat(),
            "source": "MOCK"
        }
    
    def _generate_mock_traffic(self, location: Dict[str, Any]) -> Dict[str, Any]:
        """Generate realistic mock traffic data"""
        hour = datetime.now().hour
        
        # Peak hours: 7-10 AM and 5-8 PM
        if (7 <= hour <= 10) or (17 <= hour <= 20):
            congestion = random.choice(["high", "severe"])
            score = random.randint(70, 95)
            speed = random.randint(15, 30)
            vehicles = random.randint(800, 1200)
        else:
            congestion = random.choice(["low", "moderate"])
            score = random.randint(20, 50)
            speed = random.randint(40, 60)
            vehicles = random.randint(200, 500)
        
        return {
            "location": location['name'],
            "latitude": location['lat'],
            "longitude": location['lon'],
            "congestion_level": congestion,
            "congestion_score": score,
            "average_speed": speed,
            "vehicle_count": vehicles,
            "timestamp": datetime.utcnow().isoformat(),
            "source": "MOCK"
        }
    
    def publish_to_kafka(self, topic: str, data: Dict[str, Any]) -> None:
        """
        Publish data to specified Kafka topic
        
        Args:
            topic: Kafka topic name
            data: Data dictionary to publish
        """
        try:
            future = self.producer.send(topic, value=data)
            # Block until message is sent or timeout
            record_metadata = future.get(timeout=10)
            print(f"✅ Published to {topic}: {data['location']} | "
                  f"Partition: {record_metadata.partition} | "
                  f"Offset: {record_metadata.offset}")
        except KafkaError as e:
            print(f"❌ Failed to publish to {topic}: {e}")
        except Exception as e:
            print(f"❌ Unexpected error publishing to {topic}: {e}")
    
    def produce_data_cycle(self) -> None:
        """
        Fetch and publish one cycle of data for all locations
        """
        print(f"\n🔄 Starting data collection cycle at {datetime.now()}")
        
        for location in self.locations:
            # Fetch AQI data
            aqi_data = self.fetch_aqi_data(location)
            if aqi_data:
                self.publish_to_kafka(self.aqi_topic, aqi_data)
            
            # Fetch weather data
            weather_data = self.fetch_weather_data(location)
            if weather_data:
                self.publish_to_kafka(self.weather_topic, weather_data)
            
            # Fetch traffic data
            traffic_data = self.fetch_traffic_data(location)
            if traffic_data:
                self.publish_to_kafka(self.traffic_topic, traffic_data)
            
            # Small delay between locations
            time.sleep(0.5)
        
        print(f"✅ Cycle completed for {len(self.locations)} locations\n")
    
    def run_continuous(self, interval_seconds: int = 300) -> None:
        """
        Run producer continuously with specified interval
        
        Args:
            interval_seconds: Time between data collection cycles (default: 5 minutes)
        """
        print(f"🚀 Starting continuous data producer")
        print(f"📍 Monitoring locations: {[loc['name'] for loc in self.locations]}")
        print(f"⏱️  Collection interval: {interval_seconds} seconds")
        print(f"🔗 Kafka broker: {self.bootstrap_servers}")
        print(f"📊 Topics: {self.aqi_topic}, {self.weather_topic}, {self.traffic_topic}\n")
        
        try:
            while True:
                self.produce_data_cycle()
                time.sleep(interval_seconds)
        except KeyboardInterrupt:
            print("\n⏸️  Producer stopped by user")
        except Exception as e:
            print(f"\n❌ Producer error: {e}")
        finally:
            self.close()
    
    def close(self) -> None:
        """Close Kafka producer and cleanup resources"""
        if self.producer:
            print("Flushing remaining messages...")
            self.producer.flush()
            self.producer.close()
            print("✅ Kafka producer closed")


def main():
    """Main entry point for the producer"""
    producer = DataProducer()
    
    # Run continuously with 5-minute intervals (300 seconds)
    # For testing, you can use shorter intervals like 60 seconds
    producer.run_continuous(interval_seconds=60)


if __name__ == "__main__":
    main()