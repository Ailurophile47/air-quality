"""
Airflow DAG for Air Quality Data Ingestion Pipeline
Orchestrates data ingestion from various sources into Kafka and PostgreSQL
"""

from datetime import datetime, timedelta
from airflow import DAG
from airflow.operators.python import PythonOperator
from airflow.operators.bash import BashOperator
from airflow.providers.apache.kafka.operators.produce import ProduceToTopicOperator
from airflow.utils.task_group import TaskGroup
from airflow.exceptions import AirflowException
import logging

logger = logging.getLogger(__name__)

# Default arguments for the DAG
default_args = {
    'owner': 'air-quality-team',
    'retries': 2,
    'retry_delay': timedelta(minutes=5),
    'start_date': datetime(2025, 1, 1),
    'email_on_failure': True,
    'email': ['admin@airquality.com'],
    'timeout': 3600,
}

# DAG definition
dag = DAG(
    dag_id='air_quality_ingestion_pipeline',
    default_args=default_args,
    description='Ingests air quality data from multiple sources',
    schedule_interval='0 */6 * * *',  # Every 6 hours
    catchup=False,
    tags=['data-ingestion', 'air-quality'],
)


def validate_data_source(**context):
    """Validate that data sources are available"""
    logger.info("Validating data sources...")
    try:
        # Add your data source validation logic here
        import requests
        # Example: Check if external API is available
        response = requests.get('https://api.waqi.info/status/json', timeout=5)
        if response.status_code != 200:
            raise AirflowException("External data source unavailable")
        logger.info("Data sources validated successfully")
        return True
    except Exception as e:
        logger.error(f"Data source validation failed: {str(e)}")
        raise


def fetch_aqi_data(**context):
    """Fetch Air Quality Index data from external sources"""
    logger.info("Fetching AQI data from external sources...")
    try:
        import requests
        from datetime import datetime
        
        # Example: Fetch from WAQI API
        stations = ['beijing', 'delhi', 'shanghai', 'lagos', 'dhaka']
        aqi_data = []
        
        for station in stations:
            try:
                response = requests.get(
                    f'https://api.waqi.info/feed/{station}/?token=demo',
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    if data.get('status') == 'ok':
                        aqi_data.append({
                            'timestamp': datetime.utcnow().isoformat(),
                            'city': station,
                            'aqi': data.get('data', {}).get('aqi'),
                            'source': 'waqi'
                        })
            except Exception as e:
                logger.warning(f"Failed to fetch data for {station}: {str(e)}")
        
        logger.info(f"Fetched AQI data for {len(aqi_data)} stations")
        context['task_instance'].xcom_push(key='aqi_records', value=aqi_data)
        return len(aqi_data)
    
    except Exception as e:
        logger.error(f"AQI data fetch failed: {str(e)}")
        raise


def fetch_weather_data(**context):
    """Fetch weather data from external sources"""
    logger.info("Fetching weather data...")
    try:
        import requests
        from datetime import datetime
        
        # Example: Fetch from OpenWeather API
        cities = ['Beijing', 'Delhi', 'Shanghai', 'Lagos', 'Dhaka']
        weather_data = []
        
        for city in cities:
            try:
                response = requests.get(
                    f'https://api.openweathermap.org/data/2.5/weather?q={city}&appid=demo',
                    timeout=10
                )
                if response.status_code == 200:
                    data = response.json()
                    weather_data.append({
                        'timestamp': datetime.utcnow().isoformat(),
                        'city': city,
                        'temperature': data.get('main', {}).get('temp'),
                        'humidity': data.get('main', {}).get('humidity'),
                        'wind_speed': data.get('wind', {}).get('speed'),
                        'source': 'openweather'
                    })
            except Exception as e:
                logger.warning(f"Failed to fetch weather for {city}: {str(e)}")
        
        logger.info(f"Fetched weather data for {len(weather_data)} cities")
        context['task_instance'].xcom_push(key='weather_records', value=weather_data)
        return len(weather_data)
    
    except Exception as e:
        logger.error(f"Weather data fetch failed: {str(e)}")
        raise


def transform_data(**context):
    """Transform and enrich data from multiple sources"""
    logger.info("Transforming data...")
    try:
        # Get data from previous tasks
        aqi_records = context['task_instance'].xcom_pull(
            task_ids='fetch_aqi_data', 
            key='aqi_records'
        ) or []
        weather_records = context['task_instance'].xcom_pull(
            task_ids='fetch_weather_data',
            key='weather_records'
        ) or []
        
        # Combine and transform data
        transformed_records = []
        aqi_dict = {record['city']: record for record in aqi_records}
        
        for weather in weather_records:
            city = weather['city'].lower()
            aqi = aqi_dict.get(city, {})
            
            transformed_records.append({
                'timestamp': weather['timestamp'],
                'city': weather['city'],
                'aqi': aqi.get('aqi'),
                'temperature': weather['temperature'],
                'humidity': weather['humidity'],
                'wind_speed': weather['wind_speed'],
                'data_quality_score': 0.95
            })
        
        logger.info(f"Transformed {len(transformed_records)} records")
        context['task_instance'].xcom_push(key='transformed_data', value=transformed_records)
        return len(transformed_records)
    
    except Exception as e:
        logger.error(f"Data transformation failed: {str(e)}")
        raise


def push_to_kafka(**context):
    """Push transformed data to Kafka topic"""
    logger.info("Pushing data to Kafka...")
    try:
        from kafka import KafkaProducer
        import json
        
        transformed_data = context['task_instance'].xcom_pull(
            task_ids='transform_data',
            key='transformed_data'
        ) or []
        
        producer = KafkaProducer(
            bootstrap_servers=['kafka:9092'],
            value_serializer=lambda v: json.dumps(v).encode('utf-8'),
            acks='all',
            retries=3
        )
        
        for record in transformed_data:
            producer.send('air-quality-topic', value=record)
            logger.debug(f"Sent record for {record['city']}")
        
        producer.flush()
        producer.close()
        
        logger.info(f"Pushed {len(transformed_data)} records to Kafka")
        return len(transformed_data)
    
    except Exception as e:
        logger.error(f"Kafka push failed: {str(e)}")
        raise


def quality_checks(**context):
    """Perform quality checks on ingested data"""
    logger.info("Running quality checks...")
    try:
        transformed_data = context['task_instance'].xcom_pull(
            task_ids='transform_data',
            key='transformed_data'
        ) or []
        
        issues = []
        
        # Check for null values
        for record in transformed_data:
            if record.get('aqi') is None:
                issues.append(f"Missing AQI for {record['city']}")
            if record.get('temperature') is None:
                issues.append(f"Missing temperature for {record['city']}")
        
        # Check data ranges
        for record in transformed_data:
            if record.get('aqi') and (record['aqi'] < 0 or record['aqi'] > 500):
                issues.append(f"Invalid AQI range for {record['city']}: {record['aqi']}")
        
        if issues:
            logger.warning(f"Quality check issues found: {issues}")
        
        logger.info("Quality checks completed")
        return len(issues)
    
    except Exception as e:
        logger.error(f"Quality checks failed: {str(e)}")
        raise


# Task definitions
validate_source = PythonOperator(
    task_id='validate_data_source',
    python_callable=validate_data_source,
    dag=dag,
)

fetch_aqi = PythonOperator(
    task_id='fetch_aqi_data',
    python_callable=fetch_aqi_data,
    dag=dag,
)

fetch_weather = PythonOperator(
    task_id='fetch_weather_data',
    python_callable=fetch_weather_data,
    dag=dag,
)

transform = PythonOperator(
    task_id='transform_data',
    python_callable=transform_data,
    dag=dag,
)

quality_check = PythonOperator(
    task_id='quality_checks',
    python_callable=quality_checks,
    dag=dag,
)

push_kafka = PythonOperator(
    task_id='push_to_kafka',
    python_callable=push_to_kafka,
    dag=dag,
)

notify_completion = BashOperator(
    task_id='notify_completion',
    bash_command='echo "Data ingestion pipeline completed successfully at $(date)"',
    dag=dag,
)

# DAG dependencies
validate_source >> [fetch_aqi, fetch_weather]
[fetch_aqi, fetch_weather] >> transform
transform >> quality_check
quality_check >> push_kafka
push_kafka >> notify_completion
