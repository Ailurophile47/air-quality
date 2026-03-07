import psycopg2
import os

def insert_record(data):
    conn = psycopg2.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        dbname=os.getenv("POSTGRES_DB", "airquality"),
        user=os.getenv("POSTGRES_USER", "airuser"),
        password=os.getenv("POSTGRES_PASSWORD", "airpass"),
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
    if not recorded_at or aqi_value is None:
        conn.close()
        return  # Skip malformed or incomplete messages

    cursor = conn.cursor()
    cursor.execute(
        """
        INSERT INTO aqi_measurements
        (location_id, aqi_value, pm2_5, pm10, no2, o3, co, dominant_pollutant, recorded_at)
        VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ON CONFLICT (location_id, recorded_at) DO NOTHING
        """,
        (1, aqi_value, pm25, pm10, no2, o3, co, dominant_pollutant, recorded_at)
    )

    conn.commit()
    cursor.close()
    conn.close()