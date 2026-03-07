"""Weather data client for Bengaluru. Returns raw JSON for pipeline integration."""
import requests
import logging
from tenacity import retry, stop_after_attempt, wait_exponential

LAT, LON = 12.9716, 77.5946  # Bengaluru coordinates (aligned with AQI/traffic)


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
def fetch_weather(api_key: str) -> dict:
    """Fetch weather from OpenWeatherMap. Returns raw API response."""
    url = (
        f"http://api.openweathermap.org/data/2.5/weather"
        f"?lat={LAT}&lon={LON}&appid={api_key}&units=metric"
    )
    response = requests.get(url, timeout=10)
    response.raise_for_status()
    return response.json()


if __name__ == "__main__":
    import os
    from dotenv import load_dotenv
    load_dotenv()
    key = os.getenv("WEATHER_API_KEY")
    if key:
        print(fetch_weather(key))