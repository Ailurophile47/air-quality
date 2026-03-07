"""
Phase 5: ML service API — train and predict AQI.
Exposes POST /train and POST /predict for Airflow.
"""
import logging

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from train import train
from predict import predict_and_store

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Urban Air Quality ML Service")


@app.post("/train")
def train_model(location_id: int = 1, days: int = 7):
    """Train Ridge model on last N days of hourly aggregates. Saves model to disk."""
    try:
        result = train(location_id=location_id, days=days)
        return result
    except Exception as e:
        logger.exception("Train failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/predict")
def run_predict(location_id: int = 1):
    """Predict next 3-hour AQI and store in aqi_predictions."""
    try:
        result = predict_and_store(location_id=location_id)
        return result
    except Exception as e:
        logger.exception("Predict failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/health")
def health():
    return {"status": "ok"}
