"""
HTTP server for Phase 4 batch ingestion.
Exposes POST /ingest for Airflow to trigger AQI + Weather + Traffic collection.
Runs Kafka producer in background for continuous AQI streaming (existing behavior).
"""
import logging
import threading

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from batch_ingestion import run_batch_ingestion
from producer import run_producer
from retention import run_retention
from aggregation import run_aggregation
from seed_dummy_data import seed_data, SeedConfig

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)
logger = logging.getLogger(__name__)

app = FastAPI(title="Urban Air Quality Ingestion Service")


def _run_producer_loop():
    """Run Kafka producer in background (existing AQI streaming)."""
    try:
        run_producer()
    except Exception as e:
        logger.exception("Producer loop failed: %s", e)


@app.on_event("startup")
def startup():
    """Start Kafka producer in background thread."""
    t = threading.Thread(target=_run_producer_loop, daemon=True)
    t.start()
    logger.info("Kafka producer started in background")


@app.post("/ingest")
def ingest():
    """Trigger batch ingestion (AQI + Weather + Traffic) for Bengaluru."""
    try:
        results = run_batch_ingestion()
        if results["errors"]:
            return JSONResponse(
                status_code=207,
                content={
                    "status": "partial",
                    "aqi": results["aqi"],
                    "weather": results["weather"],
                    "traffic": results["traffic"],
                    "errors": results["errors"],
                },
            )
        return {
            "status": "ok",
            "aqi": results["aqi"],
            "weather": results["weather"],
            "traffic": results["traffic"],
        }
    except Exception as e:
        logger.exception("Batch ingestion failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/retention")
def retention():
    """Run 7-day retention cleanup (delete data older than 7 days)."""
    try:
        results = run_retention()
        return {"status": "ok", "deleted": results}
    except Exception as e:
        logger.exception("Retention failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/aggregate")
def aggregate():
    """Compute hourly/daily aggregates, correlation metrics, and anomaly detection."""
    try:
        results = run_aggregation()
        return {"status": "ok", "results": results}
    except Exception as e:
        logger.exception("Aggregation failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.post("/seed")
def seed():
    """Seed 48 hours of deterministic dummy data for training/testing."""
    try:
        config = SeedConfig(hours=48, seed=42)
        result = seed_data(config)
        return {"status": "ok", "seeding": result}
    except Exception as e:
        logger.exception("Seeding failed")
        return JSONResponse(status_code=500, content={"error": str(e)})


@app.get("/health")
def health():
    return {"status": "ok"}
