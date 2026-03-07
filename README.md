# Urban Air Quality Intelligence Platform

End-to-end data platform for urban air quality monitoring, analytics, and AQI forecasting.

This project includes:
- Real-time and batch ingestion (AQI, weather, traffic)
- Kafka pipeline + PostgreSQL storage
- Hourly/daily aggregations with anomaly and correlation analytics
- ML model training + prediction (Ridge Regression)
- Airflow orchestration (scheduled + one-click manual DAG)
- Modern React dashboard for visualization

---

## Architecture

Data flow:
1. Ingestion service collects AQI/weather/traffic data
2. Kafka consumer persists stream data to PostgreSQL
3. Aggregation job computes hourly and daily metrics
4. ML service trains model and writes predictions
5. API service serves data to the React dashboard
6. Airflow orchestrates full pipeline and retention jobs

Core technologies:
- Python (FastAPI, psycopg, pandas, scikit-learn)
- React + Vite + Tailwind + Recharts
- PostgreSQL 15
- Kafka + Zookeeper
- Apache Airflow
- Docker Compose

---

## Services and URLs

| Service | Port | URL |
|---|---:|---|
| React Dashboard | 3000 | http://localhost:3000 |
| API Service (FastAPI) | 8000 | http://localhost:8000 |
| Ingestion Service | 5050 | http://localhost:5050 |
| ML Service | 5051 | http://localhost:5051 |
| Airflow UI | 8080 | http://localhost:8080 |
| PostgreSQL | 5432 | localhost:5432 |
| Kafka Broker | 9092 | localhost:9092 |

---

## Repository Structure

```text
air quality/
├── docker-compose.yml
├── README.md
├── infrastructure/
│   └── postgres/
│       ├── init.sql
│       ├── roles.sql
│       └── migrations/
│           └── 001_traffic_and_phase4_tables.sql
└── services/
        ├── airflow/
        │   └── dags/
        │       ├── urban_air_quality_hourly.py
        │       └── model_training_manual.py
        ├── api_service/
        ├── frontend/
        ├── ingestion_service/
        ├── kafka_consumer/
        └── ml_service/
```

---

## Quick Start

### 1) Prerequisites
- Docker Desktop (running)
- Git
- Windows PowerShell (commands below are PowerShell-friendly)

### 2) Start the platform

```bash
docker-compose up -d --build
```

### 3) Verify containers

```bash
docker ps
```

### 4) Open applications
- Dashboard: http://localhost:3000
- Airflow: http://localhost:8080

---

## One-Click ML Workflow (Recommended)

Use Airflow DAG `model_training_manual` for complete ML flow:

Flow:
`Seed -> Aggregate -> Train -> Predict`

Steps:
1. Open Airflow UI http://localhost:8080
2. Find DAG: `model_training_manual`
3. Click **Trigger DAG**
4. Wait for all tasks to become green
5. Open dashboard to view predictions

---

## Manual API Workflow

PowerShell users should use `curl.exe` (not `curl`).

### Seed deterministic dummy data
```bash
curl.exe -X POST "http://localhost:5050/seed"
```

### Train model
```bash
curl.exe -X POST "http://localhost:5051/train?location_id=1&days=7"
```

### Predict AQI
```bash
curl.exe -X POST "http://localhost:5051/predict?location_id=1"
```

---

## Scheduled Pipeline

DAG: `urban_air_quality_phase5_pipeline`

Schedule: every 3 hours (`0 */3 * * *`)

Pipeline order:
1. Ingest
2. Retention cleanup
3. Aggregation
4. ML train
5. ML predict

---

## Data Retention

Retention is automatic.

- Window: last 7 days
- Cleanup endpoint: `POST /retention`
- Old rows are deleted from:
    - `aqi_measurements`
    - `weather_measurements`
    - `traffic_data`
    - `raw_aqi_data`
    - `raw_weather_data`

---

## Key API Endpoints

### API Service (`:8000`)
- `GET /aqi/latest?city=Bangalore`
- `GET /aqi/history?city=Bangalore&limit=50&offset=0`
- `GET /dashboard/predictions?city=Bangalore&limit=24`
- `GET /dashboard/hourly?city=Bangalore&limit=168`
- `GET /dashboard/daily?city=Bangalore&limit=30`
- `GET /dashboard/anomalies?city=Bangalore&limit=50`
- `GET /dashboard/correlation?city=Bangalore`

### Ingestion Service (`:5050`)
- `POST /ingest`
- `POST /seed`
- `POST /aggregate`
- `POST /retention`
- `GET /health`

### ML Service (`:5051`)
- `POST /train?location_id=1&days=7`
- `POST /predict?location_id=1`
- `GET /health`

---

## Database Tables

Primary tables:
- `locations`
- `aqi_measurements`
- `weather_measurements`
- `traffic_data`
- `raw_aqi_data`
- `raw_weather_data`
- `hourly_aggregates`
- `daily_aggregates`
- `correlation_metrics`
- `anomaly_events`
- `aqi_predictions`

---

## Frontend Highlights

React dashboard features:
- Real-time AQI metrics
- ML prediction highlight card
- Prediction trend chart
- Hourly AQI trend chart
- Daily + rolling-7-day chart
- Correlation metrics panel
- Anomaly events panel
- Auto refresh every 30 seconds

---

## Troubleshooting

### Dashboard loads but no data
1. Ensure API is running: `docker ps`
2. Test API: `curl.exe "http://localhost:8000/aqi/latest?city=Bangalore"`
3. Hard refresh browser (`Ctrl+Shift+R`)

### No predictions visible
1. Run train endpoint
2. Run predict endpoint
3. Check DB table `aqi_predictions`

### Airflow DAG missing
1. Check container logs: `docker logs airflow_webserver`
2. Confirm DAG exists in `services/airflow/dags/`

---

## Development Commands

```bash
# Rebuild specific services
docker-compose up -d --build api_service dashboard ml_service ingestion_service

# View logs
docker logs air_dashboard
docker logs air_api
docker logs air_ingestion
docker logs air_ml

# Stop all
docker-compose down

# Stop all + remove volumes (fresh reset)
docker-compose down -v
```

---

## Notes

- `services/dashboard/` (old Streamlit app) was retired and replaced by `services/frontend/`.
- Python cache files (`__pycache__`, `*.pyc`) are safe to delete and ignored via `.gitignore`.
- For Windows PowerShell, always prefer `curl.exe`.
