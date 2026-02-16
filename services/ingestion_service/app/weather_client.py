import requests
import logging

def fetch_weather(city, api_key):
    url = (
        f"https://api.openweathermap.org/data/2.5/weather"
        f"?q={city}&appid={api_key}&units=metric"
    )

    response = requests.get(url, timeout=10)

    if response.status_code != 200:
        logging.error("Weather API failure")
        raise Exception("Weather API error")

    return response.json()