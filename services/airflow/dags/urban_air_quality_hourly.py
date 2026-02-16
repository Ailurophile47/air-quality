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
    response = requests.post("http://api_service:8000/ingest")
    if response.status_code != 200:
        raise Exception("Ingestion failed")

with DAG(
    dag_id="urban_air_quality_hourly_pipeline",
    default_args=default_args,
    schedule_interval="0 * * * *",
    start_date=datetime(2026, 2, 16),
    catchup=True,
    max_active_runs=1,
    tags=["air_quality"],
) as dag:

    run_pipeline = PythonOperator(
        task_id="trigger_ingestion_service",
        python_callable=trigger_ingestion,
        execution_timeout=timedelta(minutes=10),
        sla=timedelta(minutes=15),
    )

    run_pipeline