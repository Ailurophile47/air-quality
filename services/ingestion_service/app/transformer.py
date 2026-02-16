from datetime import datetime

def transform_aqi(data):
    iaqi = data["data"].get("iaqi", {})
    return {
        "aqi_value": data["data"].get("aqi"),
        "pm2_5": iaqi.get("pm25", {}).get("v"),
        "pm10": iaqi.get("pm10", {}).get("v"),
        "no2": iaqi.get("no2", {}).get("v"),
        "o3": iaqi.get("o3", {}).get("v"),
        "co": iaqi.get("co", {}).get("v"),
        "dominant_pollutant": data["data"].get("dominentpol"),
        "recorded_at": datetime.utcnow()
    }

def transform_weather(data):
    return {
        "temperature": data["main"]["temp"],
        "humidity": data["main"]["humidity"],
        "wind_speed": data["wind"]["speed"],
        "pressure": data["main"]["pressure"],
        "visibility": data.get("visibility"),
        "recorded_at": datetime.utcnow()
    }