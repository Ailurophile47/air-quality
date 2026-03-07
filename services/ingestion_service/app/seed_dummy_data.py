"""
Seed deterministic dummy air-quality data for model training/testing.
Creates complete rows for locations, raw payloads, aqi_measurements,
weather_measurements, traffic_data, and then computes phase-4 aggregates.
"""

from __future__ import annotations

import argparse
import json
import math
import random
from dataclasses import dataclass
from datetime import datetime, timedelta

from aggregation import run_aggregation
from loader import get_connection, get_or_create_location


@dataclass
class SeedConfig:
    city: str = "Bangalore"
    country: str = "India"
    latitude: float = 12.9716
    longitude: float = 77.5946
    hours: int = 48
    seed: int = 42


def _hourly_timestamps(hours: int) -> list[datetime]:
    now = datetime.utcnow().replace(minute=0, second=0, microsecond=0)
    start = now - timedelta(hours=hours - 1)
    return [start + timedelta(hours=offset) for offset in range(hours)]


def _build_row(index: int, ts: datetime, rng: random.Random, city: str) -> dict:
    diurnal = math.sin((index / 24.0) * 2 * math.pi)
    traffic_peak = max(0.0, math.sin(((index % 24) - 7) / 4.0) + math.sin(((index % 24) - 17) / 4.0))

    temperature = round(22 + 6 * diurnal + rng.uniform(-1.2, 1.2), 2)
    humidity = round(68 - 14 * diurnal + rng.uniform(-3.0, 3.0), 2)
    vehicle_count = max(80, int(220 + 180 * traffic_peak + rng.uniform(-25, 25)))

    pm2_5 = round(max(8.0, 24 + vehicle_count * 0.06 + (32 - temperature) * 0.8 + rng.uniform(-3.5, 3.5)), 2)
    pm10 = round(pm2_5 * 1.45 + rng.uniform(-2.0, 2.0), 2)
    no2 = round(max(5.0, 10 + vehicle_count * 0.03 + rng.uniform(-1.5, 1.5)), 2)
    o3 = round(max(4.0, 16 + (temperature - 18) * 1.3 + rng.uniform(-2.0, 2.0)), 2)
    co = round(max(0.2, 0.6 + vehicle_count * 0.002 + rng.uniform(-0.1, 0.1)), 2)

    # AQI proxy with strong relation to PM2.5 and traffic
    aqi_value = int(max(25, min(450, 0.95 * pm2_5 + 0.08 * vehicle_count + rng.uniform(-10, 10))))

    congestion_index = round(min(1.0, max(0.05, vehicle_count / 520.0 + rng.uniform(-0.05, 0.05))), 3)
    avg_speed = round(max(8.0, 42 - congestion_index * 22 + rng.uniform(-3.0, 3.0)), 2)

    raw_aqi = {
        "city": city,
        "timestamp": ts.isoformat(),
        "aqi": aqi_value,
        "components": {
            "pm2_5": pm2_5,
            "pm10": pm10,
            "no2": no2,
            "o3": o3,
            "co": co,
        },
        "dominant_pollutant": "pm2_5",
        "source": "dummy-seed",
    }

    raw_weather = {
        "city": city,
        "timestamp": ts.isoformat(),
        "temperature": temperature,
        "humidity": humidity,
        "wind_speed": round(max(0.5, 2.8 + rng.uniform(-1.1, 1.1)), 2),
        "pressure": round(1008 + rng.uniform(-8, 8), 2),
        "visibility": round(max(2.0, 8.0 - congestion_index * 2.5 + rng.uniform(-0.8, 0.8)), 2),
        "source": "dummy-seed",
    }

    return {
        "recorded_at": ts,
        "raw_aqi": raw_aqi,
        "raw_weather": raw_weather,
        "aqi": {
            "aqi_value": aqi_value,
            "pm2_5": pm2_5,
            "pm10": pm10,
            "no2": no2,
            "o3": o3,
            "co": co,
            "dominant_pollutant": "pm2_5",
        },
        "weather": {
            "temperature": temperature,
            "humidity": humidity,
            "wind_speed": raw_weather["wind_speed"],
            "pressure": raw_weather["pressure"],
            "visibility": raw_weather["visibility"],
        },
        "traffic": {
            "city": city,
            "vehicle_count": vehicle_count,
            "congestion_index": congestion_index,
            "avg_speed": avg_speed,
        },
    }


def seed_data(config: SeedConfig) -> dict:
    location_id = get_or_create_location(
        city=config.city,
        lat=config.latitude,
        lon=config.longitude,
        country=config.country,
    )

    timestamps = _hourly_timestamps(config.hours)
    rng = random.Random(config.seed)
    rows = [_build_row(index=i, ts=ts, rng=rng, city=config.city) for i, ts in enumerate(timestamps)]

    start_ts = timestamps[0]
    end_ts = timestamps[-1]

    with get_connection() as conn:
        with conn.cursor() as cur:
            # Keep this deterministic on repeated runs.
            cur.execute(
                """
                DELETE FROM traffic_data
                WHERE location_id = %s
                  AND recorded_at BETWEEN %s AND %s
                """,
                (location_id, start_ts, end_ts),
            )
            cur.execute(
                """
                DELETE FROM raw_aqi_data
                WHERE location_id = %s
                  AND ingestion_time BETWEEN %s AND %s
                """,
                (location_id, start_ts, end_ts),
            )
            cur.execute(
                """
                DELETE FROM raw_weather_data
                WHERE location_id = %s
                  AND ingestion_time BETWEEN %s AND %s
                """,
                (location_id, start_ts, end_ts),
            )

            cur.executemany(
                """
                INSERT INTO aqi_measurements
                (location_id, aqi_value, pm2_5, pm10, no2, o3, co, dominant_pollutant, recorded_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (location_id, recorded_at) DO UPDATE SET
                    aqi_value = EXCLUDED.aqi_value,
                    pm2_5 = EXCLUDED.pm2_5,
                    pm10 = EXCLUDED.pm10,
                    no2 = EXCLUDED.no2,
                    o3 = EXCLUDED.o3,
                    co = EXCLUDED.co,
                    dominant_pollutant = EXCLUDED.dominant_pollutant
                """,
                [
                    (
                        location_id,
                        row["aqi"]["aqi_value"],
                        row["aqi"]["pm2_5"],
                        row["aqi"]["pm10"],
                        row["aqi"]["no2"],
                        row["aqi"]["o3"],
                        row["aqi"]["co"],
                        row["aqi"]["dominant_pollutant"],
                        row["recorded_at"],
                    )
                    for row in rows
                ],
            )

            cur.executemany(
                """
                INSERT INTO weather_measurements
                (location_id, temperature, humidity, wind_speed, pressure, visibility, recorded_at)
                VALUES (%s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (location_id, recorded_at) DO UPDATE SET
                    temperature = EXCLUDED.temperature,
                    humidity = EXCLUDED.humidity,
                    wind_speed = EXCLUDED.wind_speed,
                    pressure = EXCLUDED.pressure,
                    visibility = EXCLUDED.visibility
                """,
                [
                    (
                        location_id,
                        row["weather"]["temperature"],
                        row["weather"]["humidity"],
                        row["weather"]["wind_speed"],
                        row["weather"]["pressure"],
                        row["weather"]["visibility"],
                        row["recorded_at"],
                    )
                    for row in rows
                ],
            )

            cur.executemany(
                """
                INSERT INTO traffic_data
                (location_id, city, recorded_at, vehicle_count, congestion_index, avg_speed)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        location_id,
                        row["traffic"]["city"],
                        row["recorded_at"],
                        row["traffic"]["vehicle_count"],
                        row["traffic"]["congestion_index"],
                        row["traffic"]["avg_speed"],
                    )
                    for row in rows
                ],
            )

            cur.executemany(
                """
                INSERT INTO raw_aqi_data (location_id, raw_payload, ingestion_time)
                VALUES (%s, %s::jsonb, %s)
                """,
                [
                    (
                        location_id,
                        json.dumps(row["raw_aqi"]),
                        row["recorded_at"],
                    )
                    for row in rows
                ],
            )

            cur.executemany(
                """
                INSERT INTO raw_weather_data (location_id, raw_payload, ingestion_time)
                VALUES (%s, %s::jsonb, %s)
                """,
                [
                    (
                        location_id,
                        json.dumps(row["raw_weather"]),
                        row["recorded_at"],
                    )
                    for row in rows
                ],
            )

            conn.commit()

    aggregation_result = run_aggregation(location_id=location_id)

    return {
        "location_id": location_id,
        "city": config.city,
        "rows_seeded_per_table": len(rows),
        "from": start_ts.isoformat(),
        "to": end_ts.isoformat(),
        "aggregation": aggregation_result,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Seed dummy air-quality data for training/testing")
    parser.add_argument("--city", default="Bangalore")
    parser.add_argument("--country", default="India")
    parser.add_argument("--lat", type=float, default=12.9716)
    parser.add_argument("--lon", type=float, default=77.5946)
    parser.add_argument("--hours", type=int, default=48, help="Number of hourly records to generate")
    parser.add_argument("--seed", type=int, default=42, help="Deterministic seed for synthetic data")
    return parser.parse_args()


def main() -> None:
    args = _parse_args()
    config = SeedConfig(
        city=args.city,
        country=args.country,
        latitude=args.lat,
        longitude=args.lon,
        hours=max(24, args.hours),
        seed=args.seed,
    )
    result = seed_data(config)
    print(json.dumps(result, indent=2, default=str))


if __name__ == "__main__":
    main()
