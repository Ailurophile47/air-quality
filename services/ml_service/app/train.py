"""
Phase 5: Train AQI prediction model on rolling 7-day data.
Uses Ridge Regression (stable for small data); model saved to disk for prediction service.
"""
import os
import logging
from datetime import datetime

import joblib
import numpy as np
from sklearn.linear_model import Ridge
from sklearn.preprocessing import StandardScaler

from feature_engineering import get_training_data, FEATURE_COLUMNS

logger = logging.getLogger(__name__)
MODEL_DIR = os.getenv("MODEL_DIR", "/app/models")
MODEL_VERSION = "ridge_v1"


def _ensure_model_dir():
    os.makedirs(MODEL_DIR, exist_ok=True)


def train(location_id: int = 1, days: int = 7) -> dict:
    """
    Train Ridge model on last 7 days of hourly aggregates. Save model and scaler.
    Returns dict with status, samples_used, and metrics (if enough data).
    """
    _ensure_model_dir()
    X, y, _ = get_training_data(location_id=location_id, days=days)
    if X is None or len(X) < 10:
        logger.warning("Insufficient training data (need at least 10 samples)")
        return {"status": "skipped", "reason": "insufficient_data", "samples": len(X) if X is not None else 0}

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)
    model = Ridge(alpha=1.0, random_state=42)
    model.fit(X_scaled, y)

    model_path = os.path.join(MODEL_DIR, "aqi_model.joblib")
    scaler_path = os.path.join(MODEL_DIR, "aqi_scaler.joblib")
    joblib.dump(model, model_path)
    joblib.dump(scaler, scaler_path)

    # Simple metric: MAE on training set (for logging only)
    pred = model.predict(X_scaled)
    mae = float(np.mean(np.abs(pred - y)))
    logger.info("Model trained: samples=%d, MAE=%.2f", len(X), mae)

    return {
        "status": "ok",
        "model_version": MODEL_VERSION,
        "samples_used": len(X),
        "mae": round(mae, 2),
    }
