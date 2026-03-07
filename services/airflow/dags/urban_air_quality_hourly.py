from airflow import DAG
try:
    from airflow.operators.python import PythonOperator  # Airflow 2.x
except (ImportError, ModuleNotFoundError):  # pragma: no cover
    from airflow.operators.python_operator import PythonOperator  # Airflow 1.x
from datetime import timedelta, datetime
import requests

default_args = {
    "owner": "data_engineering",
    "retries": 3,
    "retry_delay": timedelta(minutes=5),
    "retry_exponential_backoff": True,
}

def trigger_ingestion():
    """Trigger batch ingestion (AQI + Weather + Traffic) every 3 hours."""
    response = requests.post("http://ingestion_service:5050/ingest", timeout=60)
    if response.status_code not in (200, 207):
        raise Exception(f"Ingestion failed: {response.text}")


def run_retention():
    """Run 7-day retention cleanup."""
    response = requests.post("http://ingestion_service:5050/retention", timeout=60)
    if response.status_code != 200:
        raise Exception(f"Retention failed: {response.text}")


def run_aggregation():
    """Compute hourly/daily aggregates, correlation, and anomaly detection."""
    response = requests.post("http://ingestion_service:5050/aggregate", timeout=120)
    if response.status_code != 200:
        raise Exception(f"Aggregation failed: {response.text}")


def run_ml_train():
    """Train AQI prediction model on rolling 7-day data."""
    response = requests.post("http://ml_service:5051/train?location_id=1&days=7", timeout=300)
    if response.status_code != 200:
        raise Exception(f"ML train failed: {response.text}")
    data = response.json()
    if data.get("status") not in ("ok", "skipped"):
        raise Exception(f"ML train failed: {data}")


def run_ml_predict():
    """Predict next 3-hour AQI and store in aqi_predictions."""
    response = requests.post("http://ml_service:5051/predict?location_id=1", timeout=60)
    if response.status_code != 200:
        raise Exception(f"ML predict failed: {response.text}")
    data = response.json()
    if data.get("status") not in ("ok", "skipped"):
        raise Exception(f"ML predict failed: {data}")

with DAG(
    dag_id="urban_air_quality_phase5_pipeline",
    default_args=default_args,
    schedule_interval="0 */3 * * *",  # Every 3 hours
    start_date=datetime(2026, 2, 16),
    catchup=True,
    max_active_runs=1,
    tags=["air_quality"],
) as dag:

    ingest_task = PythonOperator(
        task_id="trigger_ingestion",
        python_callable=trigger_ingestion,
        execution_timeout=timedelta(minutes=10),
        sla=timedelta(minutes=15),
    )

    retention_task = PythonOperator(
        task_id="run_retention",
        python_callable=run_retention,
        execution_timeout=timedelta(minutes=5),
    )

    aggregation_task = PythonOperator(
        task_id="run_aggregation",
        python_callable=run_aggregation,
        execution_timeout=timedelta(minutes=10),
    )

    ml_train_task = PythonOperator(
        task_id="run_ml_train",
        python_callable=run_ml_train,
        execution_timeout=timedelta(minutes=5),
    )

    ml_predict_task = PythonOperator(
        task_id="run_ml_predict",
        python_callable=run_ml_predict,
        execution_timeout=timedelta(minutes=2),
    )

    ingest_task >> retention_task >> aggregation_task >> ml_train_task >> ml_predict_task