import logging
from config import AQI_API_KEY, WEATHER_API_KEY
from aqi_client import fetch_aqi
from weather_client import fetch_weather
from transformer import transform_aqi, transform_weather
from loader import insert_raw, insert_structured_aqi

from location_service import get_or_create_location

CITY = "Bangalore"

location_id = get_or_create_location(
    city=CITY,
    country="India",
    lat=12.9716,
    lon=77.5946,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s"
)
logger = logging.getLogger(__name__)

def run():
    logging.info("Starting ingestion")
    print("Starting ingestion")

    aqi_raw = fetch_aqi(CITY, AQI_API_KEY)
    weather_raw = fetch_weather(CITY, WEATHER_API_KEY)

    insert_raw("raw_aqi_data", location_id, aqi_raw)
    insert_raw("raw_weather_data", location_id, weather_raw)

    structured_aqi = transform_aqi(aqi_raw)
    insert_structured_aqi(location_id, structured_aqi)

    logging.info("Ingestion complete")
    print("Ingestion complete")

if __name__ == "__main__":
    run()