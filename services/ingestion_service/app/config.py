import os
from dotenv import load_dotenv

load_dotenv()

POSTGRES_CONFIG = {
    "host": os.getenv("POSTGRES_HOST"),
    "port": os.getenv("POSTGRES_PORT"),
    "user": os.getenv("POSTGRES_USER"),
    "password": os.getenv("POSTGRES_PASSWORD"),
    "dbname": os.getenv("POSTGRES_DB"),
}

AQI_API_KEY = os.getenv("AQI_API_KEY")
WEATHER_API_KEY = os.getenv("WEATHER_API_KEY")

if not AQI_API_KEY or not WEATHER_API_KEY:
    raise ValueError("Missing API keys in environment.")