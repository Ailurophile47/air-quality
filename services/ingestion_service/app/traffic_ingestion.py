"""Traffic data generation for Bengaluru. Returns structured dict for pipeline integration."""
import random
from datetime import datetime


def fetch_traffic() -> dict:
    """
    Generate simulated traffic metrics for Bengaluru.
    In production, replace with real traffic API (e.g. Google, TomTom).
    Returns dict with vehicle_count, congestion_index, avg_speed, recorded_at.
    """
    return {
        "vehicle_count": random.randint(2000, 10000),
        "congestion_index": round(random.uniform(0, 1), 4),  # 0=free, 1=heavy
        "avg_speed": round(random.uniform(20, 60), 2),  # km/h
        "recorded_at": datetime.utcnow(),
    }


if __name__ == "__main__":
    print(fetch_traffic())