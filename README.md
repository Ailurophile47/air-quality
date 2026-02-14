air-quality/
│
├── docker-compose.yml
├── .env
├── .dockerignore
│
├── services/
│   │
│   ├── api_service/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   │       ├── main.py
│   │       ├── database.py
│   │       ├── models.py
│   │       ├── schemas.py
│   │       ├── routes/
│   │       │   ├── aqi.py
│   │       │   ├── weather.py
│   │       │   └── health.py
│   │       └── middleware/
│   │
│   ├── ingestion_service/
│   │   ├── Dockerfile
│   │   ├── requirements.txt
│   │   └── app/
│   │       ├── main.py
│   │       ├── config.py
│   │       ├── aqi_client.py
│   │       ├── weather_client.py
│   │       ├── transformer.py
│   │       └── loader.py
│   │
│   ├── airflow/
│   │   ├── Dockerfile
│   │   └── dags/
│   │
│   ├── spark/
│   │   ├── Dockerfile
│   │   └── jobs/
│   │
│   └── streaming/
│       ├── producer/
│       ├── consumer/
│       └── schemas/
│
└── infrastructure/
    ├── postgres/
    │   ├── init.sql
    │   └── roles.sql
    └── kafka/
