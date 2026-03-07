"""
Phase 5: Predict next 3-hour AQI and store in aqi_predictions.
Loads trained model and scaler, builds features from latest hourly data, predicts and writes to DB.
"""
import os
import logging
from datetime import datetime, timedelta

import joblib
import psycopg

from feature_engineering import get_prediction_features, FEATURE_COLUMNS

logger = logging.getLogger(__name__)
MODEL_DIR = os.getenv("MODEL_DIR", "/app/models")


def get_connection():
    return psycopg.connect(
        host=os.getenv("POSTGRES_HOST", "postgres"),
        port=int(os.getenv("POSTGRES_PORT", 5432)),
        dbname=os.getenv("POSTGRES_DB", "airquality"),
        user=os.getenv("POSTGRES_USER", "airuser"),
        password=os.getenv("POSTGRES_PASSWORD", "airpass"),
    )


def predict_and_store(location_id: int = 1, model_version: str = "ridge_v1") -> dict:
    """
    Load model, get latest features, predict AQI for next 3-hour bucket, insert into aqi_predictions.
    Next 3-hour bucket = ceil(current hour to next 3h boundary (0,3,6,9,12,15,18,21).
    """
    model_path = os.path.join(MODEL_DIR, "aqi_model.joblib")
    scaler_path = os.path.join(MODEL_DIR, "aqi_scaler.joblib")
    if not os.path.isfile(model_path) or not os.path.isfile(scaler_path):
        logger.warning("Model or scaler not found; run train first")
        return {"status": "skipped", "reason": "model_not_found"}

    X, last_bucket = get_prediction_features(location_id=location_id)
    if X is None:
        return {"status": "skipped", "reason": "insufficient_features"}

    model = joblib.load(model_path)
    scaler = joblib.load(scaler_path)
    X_scaled = scaler.transform(X)
    predicted_aqi = float(model.predict(X_scaled)[0])
    predicted_aqi = max(0, min(500, predicted_aqi))  # Clamp to valid AQI range

    # Predict for next 3-hour window: e.g. if now is 11:00, predict for 12:00–15:00 bucket at 12:00
    if last_bucket is None:
        return {"status": "error", "reason": "no_last_bucket"}
    # Use UTC; next 3h bucket from last_bucket
    if hasattr(last_bucket, "to_pydatetime"):
        last_ts = last_bucket.to_pydatetime()
    else:
        last_ts = last_bucket
    hours_ahead = 3
    predicted_at = last_ts + timedelta(hours=hours_ahead)
    # Normalize to 3-hour boundary (0,3,6,9,12,15,18,21)
    predicted_at = predicted_at.replace(
        minute=0, second=0, microsecond=0
    )
    h = predicted_at.hour
    predicted_at = predicted_at.replace(hour=(h // 3) * 3)

    with get_connection() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO aqi_predictions (location_id, predicted_at, predicted_aqi, model_version)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (location_id, predicted_at) DO UPDATE SET
                    predicted_aqi = EXCLUDED.predicted_aqi,
                    model_version = EXCLUDED.model_version
                """,
                (location_id, predicted_at, round(predicted_aqi, 2), model_version),
            )
            conn.commit()

    logger.info("Prediction stored: predicted_at=%s, predicted_aqi=%.1f", predicted_at, predicted_aqi)
    return {
        "status": "ok",
        "predicted_at": predicted_at.isoformat(),
        "predicted_aqi": round(predicted_aqi, 2),
        "model_version": model_version,
    }
