import psycopg
import json
from config import POSTGRES_CONFIG

def get_connection():
    return psycopg.connect(**POSTGRES_CONFIG)

def insert_raw(table, location_id, payload):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                f"""
                INSERT INTO {table} (location_id, raw_payload)
                VALUES (%s, %s)
                """,
                (location_id, json.dumps(payload))
            )
            conn.commit()

def insert_structured_aqi(location_id, data):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO aqi_measurements
                (location_id, aqi_value, pm2_5, pm10, no2, o3, co, dominant_pollutant, recorded_at)
                VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)
                ON CONFLICT (location_id, recorded_at) DO NOTHING
            """, (
                location_id,
                data["aqi_value"],
                data["pm2_5"],
                data["pm10"],
                data["no2"],
                data["o3"],
                data["co"],
                data["dominant_pollutant"],
                data["recorded_at"]
            ))
            conn.commit() 

def get_or_create_location(city, lat, lon, country):
    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO locations (city_name, latitude, longitude, country)
                VALUES (%s,%s,%s,%s)
                ON CONFLICT (city_name)
                DO UPDATE SET city_name=EXCLUDED.city_name
                RETURNING id;
            """, (city, lat, lon, country))
            location_id = cur.fetchone()[0]
            conn.commit()
            return location_id