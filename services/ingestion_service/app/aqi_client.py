import requests
import logging
import time
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=10),
)
def fetch_aqi(city, api_key, retries=3):
    url = f"https://api.waqi.info/feed/{city}/?token={api_key}"
    for attempt in range(retries):
        try:
            response = requests.get(url, timeout=10)
            response.raise_for_status()
            return response.json()
        except Exception:
            if attempt < retries - 1:
                logging.error(f"AQI API attempt {attempt + 1} failed, retrying...")
                time.sleep(2 ** attempt)
    raise Exception("AQI API failed after retries")