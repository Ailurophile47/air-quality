C:.
│   .dockerignore
│   .env
│   .gitignore
│   docker-compose.yml
│   README.md
│
├───infrastructure
│   ├───kakfa
│   └───postgres
│           init.sql
│           roles.sql
│
└───services
    ├───airflow
    │   │   Dockerfile
    │   │   requirements.txt
    │   │
    │   ├───dags
    │   │   │   urban_air_quality_hourly.py
    │   │   │
    │   │   └───__pycache__
    │   │           urban_air_quality_hourly.cpython-38.pyc
    │   │
    │   ├───logs
    │   │   ├───dag_id=urban_air_quality_hourly_pipeline
    │   │   │   ├───run_id=manual__2026-02-28T055816.991178+0000
    │   │   │   │   └───task_id=trigger_ingestion_service
    │   │   │   │           attempt=1.log
    │   │   │   │           attempt=2.log
    │   │   │   │           attempt=3.log
    │   │   │   │           attempt=4.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-02-28T055822.994694+0000
    │   │   │   │   └───task_id=trigger_ingestion_service
    │   │   │   │           attempt=1.log
    │   │   │   │           attempt=2.log
    │   │   │   │           attempt=3.log
    │   │   │   │           attempt=4.log
    │   │   │   │
    │   │   │   ├───run_id=manual__2026-02-28T055824.969395+0000
    │   │   │   │   └───task_id=trigger_ingestion_service
    │   │   │   │           attempt=1.log
    │   │   │   │           attempt=2.log
    │   │   │   │
    │   │   │   ├───run_id=scheduled__2024-01-01T000000+0000
    │   │   │   │   └───task_id=trigger_ingestion_service
    │   │   │   │           attempt=1.log
    │   │   │   │           attempt=2.log
    │   │   │   │
    │   │   │   ├───run_id=scheduled__2026-02-02T000000+0000
    │   │   │   │   └───task_id=trigger_ingestion_service
    │   │   │   │           attempt=1.log
    │   │   │   │           attempt=2.log
    │   │   │   │           attempt=3.log
    │   │   │   │
    │   │   │   └───run_id=scheduled__2026-02-16T000000+0000
    │   │   │       └───task_id=trigger_ingestion_service
    │   │   │               attempt=1.log
    │   │   │               attempt=2.log
    │   │   │               attempt=3.log
    │   │   │               attempt=4.log
    │   │   │
    │   │   ├───dag_processor_manager
    │   │   │       dag_processor_manager.log
    │   │   │
    │   │   └───scheduler
    │   │       ├───2026-02-15
    │   │       ├───2026-02-16
    │   │       │       urban_air_quality_hourly.py.log
    │   │       │
    │   │       ├───2026-02-25
    │   │       │       urban_air_quality_hourly.py.log
    │   │       │
    │   │       ├───2026-02-28
    │   │       │       urban_air_quality_hourly.py.log
    │   │       │
    │   │       └───latest
    │   │               urban_air_quality_hourly.py.log
    │   │
    │   └───plugins
    ├───api_service
    │   │   Dockerfile
    │   │   requirements.txt
    │   │
    │   └───app
    │       │   database.py
    │       │   main.py
    │       │   __init__.py
    │       │
    │       ├───middleware
    │       └───routes
    │               aqi.py
    │               health.py
    │               weather.py
    │               __init__.py
    │
    ├───ingestion_service
    │   │   Dockerfile
    │   │   requirements.txt
    │   │
    │   └───app
    │           aqi_client.py
    │           config.py
    │           loader.py
    │           location_service.py
    │           main.py
    │           producer.py
    │           transformer.py
    │           weather_client.py
    │
    └───kafka_consumer
        │   Dockerfile
        │   requirements.txt
        │
        └───app
                consumer.py
                database.py
