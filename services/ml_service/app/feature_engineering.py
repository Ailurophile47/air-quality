"""
Phase 5: Feature engineering for AQI prediction.
Builds training/prediction dataset from hourly_aggregates with lagged AQI and env features.
"""
import os
from datetime import datetime, timedelta

import psycopg
import numpy as np
import pandas as pd


def get_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        dbname=os.getenv("POSTGRES_DB", "airquality"),
        user=os.getenv("POSTGRES_USER", "airuser"),
        password=os.getenv("POSTGRES_PASSWORD", "airpass"),
    )


# Features used for prediction
FEATURE_COLUMNS = [
    "avg_temp",
    "avg_humidity",
    "avg_vehicle_count",
    "aqi_lag_1h",
    "aqi_lag_3h",
    "aqi_lag_6h",
]
TARGET_COLUMN = "avg_aqi"


def load_hourly_aggregates(location_id: int = 1, days: int = 7) -> pd.DataFrame:
    """Load hourly_aggregates for the last `days` days, ordered by hour_bucket."""
    with get_connection() as conn:
        df = pd.read_sql(
            """
            SELECT hour_bucket, avg_aqi, avg_pm2_5, avg_temp, avg_humidity, avg_vehicle_count
            FROM hourly_aggregates
            WHERE location_id = %(loc_id)s
              AND hour_bucket >= NOW() - INTERVAL '1 day' * %(days)s
            ORDER BY hour_bucket
            """,
            conn,
            params={"loc_id": location_id, "days": days},
            parse_dates=["hour_bucket"],
        )
    return df


def build_features(df: pd.DataFrame) -> pd.DataFrame:
    """
    Build feature matrix with lags. Drops rows with NaN (e.g. first rows without lags).
    """
    df = df.sort_values("hour_bucket").reset_index(drop=True)
    df["aqi_lag_1h"] = df["avg_aqi"].shift(1)
    df["aqi_lag_3h"] = df["avg_aqi"].shift(3)
    df["aqi_lag_6h"] = df["avg_aqi"].shift(6)
    # Fill missing env with column mean (for prediction time when we might have gaps)
    for col in ["avg_temp", "avg_humidity", "avg_vehicle_count"]:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(df[col].mean())
    df = df.dropna(subset=FEATURE_COLUMNS + [TARGET_COLUMN])
    return df


def get_training_data(location_id: int = 1, days: int = 7):
    """Return (X, y, hour_buckets) for training. X and y are numpy arrays."""
    df = load_hourly_aggregates(location_id=location_id, days=days)
    if len(df) < 10:
        return None, None, None
    df = build_features(df)
    if len(df) == 0:
        return None, None, None
    X = df[FEATURE_COLUMNS].astype(float).values
    y = df[TARGET_COLUMN].values
    return X, y, df["hour_bucket"].values


def get_prediction_features(location_id: int = 1, hours_back: int = 24):
    """
    Get latest feature row for predicting next 3-hour AQI.
    Uses most recent hourly aggregates to build one feature vector.
    Returns (X, last_hour_bucket) or (None, None) if insufficient data.
    """
    with get_connection() as conn:
        df = pd.read_sql(
            """
            SELECT hour_bucket, avg_aqi, avg_temp, avg_humidity, avg_vehicle_count
            FROM hourly_aggregates
            WHERE location_id = %(loc_id)s
              AND hour_bucket >= NOW() - INTERVAL '1 hour' * %(hours)s
            ORDER BY hour_bucket DESC
            """,
            conn,
            params={"loc_id": location_id, "hours": hours_back},
            parse_dates=["hour_bucket"],
        )
    if len(df) < 7:
        return None, None
    df = df.sort_values("hour_bucket").reset_index(drop=True)
    # Latest row is "current" hour; we need lags from previous hours
    df["aqi_lag_1h"] = df["avg_aqi"].shift(1)
    df["aqi_lag_3h"] = df["avg_aqi"].shift(3)
    df["aqi_lag_6h"] = df["avg_aqi"].shift(6)
    for col in ["avg_temp", "avg_humidity", "avg_vehicle_count"]:
        df[col] = pd.to_numeric(df[col], errors="coerce").fillna(df[col].mean())
    last = df.dropna(subset=FEATURE_COLUMNS).iloc[-1:]
    if last.empty:
        return None, None
    X = last[FEATURE_COLUMNS].astype(float).values
    last_bucket = last["hour_bucket"].iloc[0]
    return X, last_bucket
