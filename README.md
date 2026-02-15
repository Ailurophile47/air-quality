air quality/
├── .dockerignore
├── .env
├── docker-compose.yml
│
├── infrastructure/
│   ├── kakfa/
│   └── postgres/
│       ├── init.sql
│       └── roles.sql
│
└── services/
    ├── api_service/
    │   ├── Dockerfile
    │   ├── requirements.txt
    │   └── app/
    │       ├── __init__.py
    │       ├── database.py
    │       ├── main.py
    │       ├── middleware/
    │       └── routes/
    │           ├── __init__.py
    │           ├── aqi.py
    │           ├── health.py
    │           └── weather.py
    │
    └── ingestion_service/
        ├── Dockerfile
        ├── requirements.txt
        └── app/
            ├── __init__.py
            ├── aqi_client.py
            ├── config.py
            ├── loader.py
            ├── location_service.py
            ├── main.py
            ├── transformer.py
            └── weather_client.py
