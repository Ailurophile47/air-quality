"""
One-click model training and prediction pipeline.
Manually triggered (no schedule) — click "Trigger DAG" in Airflow UI.
Flow: Seed data → Aggregate → Train → Predict → Done

Usage: Go to Airflow UI (localhost:8080), find dag_id='model_training_manual', click Trigger.
"""
from airflow import DAG
try:
    from airflow.operators.python import PythonOperator
except (ImportError, ModuleNotFoundError):
    from airflow.operators.python_operator import PythonOperator
from datetime import timedelta, datetime
import requests
import logging

logger = logging.getLogger(__name__)

default_args = {
    "owner": "data_engineering",
    "retries": 2,
    "retry_delay": timedelta(minutes=2),
}


def seed_training_data():
    """Seed 48 hours of deterministic dummy data."""
    response = requests.post("http://ingestion_service:5050/seed", timeout=120)
    if response.status_code not in (200, 207):
        raise Exception(f"Seeding failed: {response.status_code} {response.text}")
    data = response.json()
    if data.get("status") != "ok":
        raise Exception(f"Seeding returned error: {data}")
    logger.info(f"Seeding complete: {data['seeding']}")


def run_aggregation():
    """Compute hourly/daily aggregates from seeded data."""
    response = requests.post("http://ingestion_service:5050/aggregate", timeout=120)
    if response.status_code != 200:
        raise Exception(f"Aggregation failed: {response.status_code} {response.text}")
    data = response.json()
    if data.get("status") != "ok":
        raise Exception(f"Aggregation returned error: {data}")
    logger.info(f"Aggregation complete: {data['results']}")


def run_ml_train():
    """Train Ridge model on 7 days of hourly aggregates."""
    response = requests.post("http://ml_service:5051/train?location_id=1&days=7", timeout=300)
    if response.status_code != 200:
        raise Exception(f"ML train failed: {response.status_code} {response.text}")
    data = response.json()
    if data.get("status") not in ("ok", "skipped"):
        raise Exception(f"ML train returned error: {data}")
    logger.info(f"Training complete: {data}")


def run_ml_predict():
    """Predict next 3-hour AQI using trained model."""
    response = requests.post("http://ml_service:5051/predict?location_id=1", timeout=60)
    if response.status_code != 200:
        raise Exception(f"ML predict failed: {response.status_code} {response.text}")
    data = response.json()
    if data.get("status") not in ("ok", "skipped"):
        raise Exception(f"ML predict returned error: {data}")
    logger.info(f"Prediction complete: {data}")


with DAG(
    dag_id="model_training_manual",
    default_args=default_args,
    schedule_interval=None,  # Manual trigger only
    start_date=datetime(2026, 3, 7),
    catchup=False,
    max_active_runs=1,
    tags=["ml", "manual", "air_quality"],
    description="One-click: Seed data → Aggregate → Train → Predict. No schedule, manual trigger only.",
) as dag:

    seed_task = PythonOperator(
        task_id="seed_data",
        python_callable=seed_training_data,
        execution_timeout=timedelta(minutes=5),
    )

    aggregate_task = PythonOperator(
        task_id="aggregate_data",
        python_callable=run_aggregation,
        execution_timeout=timedelta(minutes=5),
    )

    train_task = PythonOperator(
        task_id="train_model",
        python_callable=run_ml_train,
        execution_timeout=timedelta(minutes=10),
    )

    predict_task = PythonOperator(
        task_id="predict_aqi",
        python_callable=run_ml_predict,
        execution_timeout=timedelta(minutes=2),
    )

    seed_task >> aggregate_task >> train_task >> predict_task
