"""
Phase 4: Unified batch ingestion for AQI, Weather, Traffic.
Collects all three with aligned timestamps for Bengaluru.
"""
import logging
from datetime import datetime

from config import AQI_API_KEY, WEATHER_API_KEY, CITY
from aqi_client import fetch_aqi
from weather_client import fetch_weather
from traffic_ingestion import fetch_traffic
from transformer import transform_aqi, transform_weather
from loader import (
    insert_raw,
    insert_structured_aqi,
    insert_structured_weather,
    insert_traffic,
)
from location_service import get_or_create_location

logger = logging.getLogger(__name__)

# Bengaluru coordinates (aligned across all data sources)
BENGALURU_LAT, BENGALURU_LON = 12.9716, 77.5946


def run_batch_ingestion() -> dict:
    """
    Collect AQI, Weather, Traffic for Bengaluru with aligned timestamps.
    Returns summary of what was ingested.
    """
    location_id = get_or_create_location(
        city=CITY,
        country="India",
        lat=BENGALURU_LAT,
        lon=BENGALURU_LON,
    )

    # Single timestamp for all records (aligned for correlation)
    recorded_at = datetime.utcnow()

    results = {"aqi": False, "weather": False, "traffic": False, "errors": []}

    # 1. AQI
    try:
        aqi_raw = fetch_aqi(CITY, AQI_API_KEY)
        insert_raw("raw_aqi_data", location_id, aqi_raw)
        structured_aqi = transform_aqi(aqi_raw)
        structured_aqi["recorded_at"] = recorded_at  # Override for alignment
        insert_structured_aqi(location_id, structured_aqi)
        results["aqi"] = True
        logger.info("AQI ingested for %s at %s", CITY, recorded_at)
    except Exception as e:
        results["errors"].append(f"AQI: {e}")
        logger.exception("AQI ingestion failed")

    # 2. Weather
    try:
        weather_raw = fetch_weather(WEATHER_API_KEY)
        insert_raw("raw_weather_data", location_id, weather_raw)
        structured_weather = transform_weather(weather_raw)
        structured_weather["recorded_at"] = recorded_at
        insert_structured_weather(location_id, structured_weather)
        results["weather"] = True
        logger.info("Weather ingested for %s at %s", CITY, recorded_at)
    except Exception as e:
        results["errors"].append(f"Weather: {e}")
        logger.exception("Weather ingestion failed")

    # 3. Traffic
    try:
        traffic_data = fetch_traffic()
        traffic_data["recorded_at"] = recorded_at  # Align timestamp
        insert_traffic(location_id, CITY, traffic_data)
        results["traffic"] = True
        logger.info("Traffic ingested for %s at %s", CITY, recorded_at)
    except Exception as e:
        results["errors"].append(f"Traffic: {e}")
        logger.exception("Traffic ingestion failed")

    return results
