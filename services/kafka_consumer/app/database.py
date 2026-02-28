import psycopg2
import os

def insert_record(data):
    conn = psycopg2.connect(
        host="postgres",
        dbname="airflow",
        user="airflow",
        password="airflow"
    )

    aqi_data = data.get("data", {})
    aqi_value = aqi_data.get("aqi")
    dominant_pollutant = aqi_data.get("dominentpol")

    iaqi = aqi_data.get("iaqi", {})
    pm25 = iaqi.get("pm25", {}).get("v")
    pm10 = iaqi.get("pm10", {}).get("v")
    no2 = iaqi.get("no2", {}).get("v")
    o3 = iaqi.get("o3", {}).get("v")
    co = iaqi.get("co", {}).get("v")

    recorded_at = aqi_data.get("time", {}).get("iso")

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO aqi_measurements
        (location_id, aqi_value, pm2_5, pm10, no2, o3, co, dominant_pollutant, recorded_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s);
        """,
        (1, aqi_value, pm25, pm10, no2, o3, co, dominant_pollutant, recorded_at)
    )

    conn.commit()
    cursor.close()
    conn.close()