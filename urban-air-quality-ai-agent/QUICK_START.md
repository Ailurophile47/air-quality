# Urban Air Quality AI Agent - Quick Start Guide

## Project Structure at a Glance

```
📁 Project Root
├── 📄 CODE_DOCUMENTATION.md ← READ THIS FIRST (comprehensive guide)
├── 📄 QUICK_START.md ← You are here
├── 🐳 docker-compose.yml ← Run all services
├── 📁 frontend/ ← React dashboard (UI)
│   ├── src/
│   │   ├── App.js ← MAIN COMPONENT (all commented)
│   │   └── App.css
│   └── package.json
├── 📁 src/ ← Python backend (API + logic)
│   ├── api/
│   │   └── main.py ← FASTAPI APPLICATION (all endpoints commented)
│   ├── database/
│   │   ├── db_connector.py ← Database connection pooling (fully explained)
│   │   ├── models.py ← Database tables (all models documented)
│   │   └── db_connector.py
│   ├── agent/ ← AI agent logic
│   ├── ingestion/ ← Data producers
│   └── processing/ ← Data processing jobs
├── 📁 infra/ ← Infrastructure configs
│   ├── airflow/ ← Data ingestion scheduler
│   ├── kafka/ ← Message streaming
│   ├── spark/ ← Data processing
│   └── docker-compose.yml
└── 📁 data/ ← Data storage
    ├── raw/ ← Original data
    ├── processed/ ← Cleaned data
    └── external/ ← External datasets
```

---

## Start the Application (3 Easy Steps)

### Step 1: Start All Services
```bash
# Navigate to project root
cd urban-air-quality-ai-agent

# Start all Docker services (Postgres, Redis, Kafka, Spark, Airflow, etc.)
docker-compose up -d

# Verify all services are healthy
docker-compose ps
# All should show "Up" status
```

### Step 2: Start Backend API
```bash
# Terminal 1: Backend API
cd urban-air-quality-ai-agent
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000 --reload

# Expected output:
# Uvicorn running on http://0.0.0.0:8000
# 🚀 Starting Urban Air Quality API...
# ✅ Database initialized successfully
```

### Step 3: Start Frontend
```bash
# Terminal 2: Frontend
cd urban-air-quality-ai-agent/frontend
npm start

# Expected output:
# Compiled successfully!
# Open http://localhost:3000 to view it in the browser.
```

✅ **Done!** Open **http://localhost:3000** in your browser

---

## What You're Looking At

### Frontend Dashboard (http://localhost:3000)
- **Top Section**: City selector + Refresh interval dropdown
- **Data Cards**: AQI color-coded circle + metrics (Temperature, Humidity, Wind, PM2.5)
- **Statistics**: Average AQI, Most/Least polluted cities
- **AI Insights**: Sample forecasts and health recommendations (currently static)

### API Documentation (http://localhost:8000/docs)
- Interactive Swagger UI with all endpoints
- Try out endpoints without coding
- See request/response formats

### Airflow UI (http://localhost:8080)
- View data ingestion DAGs
- Monitor Spark correlation jobs
- Username: `airflow` / Password: `airflow`

---

## File-by-File Quick Reference

### Frontend Components

**`frontend/src/App.js`** (445 lines, FULLY COMMENTED)
- What: Main React component rendering the dashboard
- Where to find: City selector, data cards, statistics
- Key hooks: useState (state), useEffect (auto-refresh), useCallback (memoize functions)
- How it works: Fetches from `/aqi/latest` → normalizes → displays

**Example**: Adding a new city to dropdown:
```javascript
// Line ~310 in App.js - add new option:
<option value="tokyo">Tokyo</option>  // New line
```

---

### Backend Endpoints

**`src/api/main.py`** (522 lines, FULLY COMMENTED)

| Endpoint | What It Does | Frontend Uses |
|----------|-------------|---|
| `/aqi/latest?limit=50` | Latest AQI from all cities | City cards |
| `/aqi/location/{city}?hours=24` | Historical data for city | City selector |
| `/aqi/statistics/{city}?hours=24` | Min/max/avg AQI | Statistics section |
| `/weather/latest` | Current weather data | Metrics display |
| `/traffic/latest` | Traffic congestion data | (Currently unused) |
| `/correlations/latest` | Spark analysis results | AI Insights section |
| `/locations` | List of monitored cities | City dropdown |
| `/ai-agent/history` | Past AI queries | (Currently unused) |

**Example API Call**:
```bash
# Get latest AQI data for Delhi
curl "http://localhost:8000/aqi/location/delhi?hours=24"

# Response:
# {
#   "location": "delhi",
#   "period_hours": 24,
#   "count": 24,
#   "data": [
#     {"aqi": 157, "pm25": 45.5, "timestamp": "2024-01-15T10:30:00"},
#     ...
#   ]
# }
```

---

### Database Models

**`src/database/models.py`** (422 lines, FULLY COMMENTED)

| Table | Purpose | Key Columns |
|-------|---------|------------|
| `aqi_data` | Air quality measurements | aqi, pm25, pm10, no2, so2, co, o3, location, timestamp |
| `weather_data` | Temperature, humidity, wind | temperature, humidity, wind_speed, weather_main |
| `traffic_data` | Vehicle congestion | congestion_level, congestion_score, vehicle_count |
| `correlation_analysis` | Spark job results | aqi_traffic_correlation, peak_pollution_hour, insight_summary |
| `ai_agent_queries` | AI conversation history | user_query, agent_response, response_time_ms |

**Example Query**:
```python
# In any Python file, after importing
from src.database.db_connector import SessionLocal
from src.database.models import AQIData

session = SessionLocal()
# Get latest AQI in Delhi
latest = session.query(AQIData)\
    .filter(AQIData.location == "delhi")\
    .order_by(AQIData.timestamp.desc())\
    .first()
print(f"Delhi AQI: {latest.aqi}")
```

---

### Database Connection

**`src/database/db_connector.py`** (Fully Documented)
- Manages PostgreSQL connection pooling
- Provides session management for FastAPI
- Initializes tables on startup
- Tests database connectivity

---

## Understanding the Data Flow

### From Data Ingestion to Display

```
1. INGESTION (Airflow DAG runs hourly)
   └─ airflow/dags/ingestion_dag.py
      ├─ Fetches from AQICN API
      ├─ Fetches from OpenWeather API
      ├─ Fetches from Google Maps API
      └─ Sends to Kafka topics

2. STREAMING (Kafka)
   └─ Messages queued in Kafka topics
      └─ consumer_to_postgres.py consumes

3. STORAGE (PostgreSQL)
   └─ Data inserted into tables:
      ├─ aqi_data ← Latest pollution readings
      ├─ weather_data ← Temperature, humidity
      ├─ traffic_data ← Congestion levels
      └─ (Others)

4. ANALYSIS (Spark Jobs)
   └─ correlation_job.py runs (scheduled by Airflow)
      ├─ Reads all tables
      ├─ Calculates correlations
      ├─ Finds patterns
      └─ Stores in correlation_analysis table

5. API (FastAPI)
   └─ /aqi/latest queries aqi_data table
   └─ /correlations/latest queries correlation_analysis table
   └─ Returns JSON responses

6. FRONTEND (React)
   └─ Fetches from API
   └─ Displays in dashboard
```

---

## Common Tasks

### See What Data Exists in Database

```bash
# Connect to PostgreSQL
docker exec -it urban-air-quality-postgres psql -U airflow -d airflow

# In PostgreSQL shell:
SELECT COUNT(*) FROM aqi_data;
SELECT DISTINCT location FROM aqi_data;
SELECT * FROM aqi_data ORDER BY timestamp DESC LIMIT 5;

# Exit
\q
```

### Check API is Working

```bash
# Method 1: Browser
# Open http://localhost:8000/docs
# Click on an endpoint → Click "Try it out" → Click "Execute"

# Method 2: Command line
curl http://localhost:8000/health
curl "http://localhost:8000/aqi/latest?limit=3"

# Method 3: Python
import requests
response = requests.get("http://localhost:8000/aqi/latest?limit=5")
print(response.json())
```

### See Real-Time API Logs

```bash
# FastAPI logs should appear in Terminal 1
# Look for:
# GET /aqi/latest - 200 OK
# POST /weather/latest - 201 Created
```

### Reload Code Changes

**Backend**: Already set with `--reload` flag
- Changes in `src/` auto-reload FastAPI

**Frontend**: Auto-reloads on file save
- Changes in `frontend/src/` auto-refresh browser

---

## Troubleshooting

### Frontend shows "Loading..." but never loads

**Possible causes**:
1. Backend API not running → Start Terminal 1 (see Step 2 above)
2. API connection error → Check `http://localhost:8000/health` in browser
3. CORS error → Check browser console (F12 → Console tab) for red messages

**Solution**:
```bash
# Check if API is running
curl http://localhost:8000/health

# If failed, check port 8000 is not in use
netstat -ano | findstr :8000  # Windows
lsof -i :8000  # Mac/Linux
```

### Database connection failed

**Check**:
```bash
# 1. Is Postgres running?
docker-compose ps  # Look for "airflow-postgres" → "Up"

# 2. Are credentials correct in .env?
cat .env | grep POSTGRES

# 3. Can you connect?
docker exec -it urban-air-quality-postgres psql -U airflow -d airflow
```

### API returns 500 error

**Check logs**:
```bash
# Terminal 1 should show error stack trace
# Look for:
# - "connection refused" → Postgres not running
# - "Table not found" → Tables not created (run init_db)
# - "HTTP error" → API logic error (check inline comments)
```

---

## Next Steps

### Understanding the Code
1. Open `CODE_DOCUMENTATION.md` for detailed guide
2. Read inline comments in each file:
   - `App.js` → React patterns
   - `main.py` → FastAPI endpoint structure
   - `models.py` → Database schema
   - `db_connector.py` → Connection management

### Making Changes
1. **Add new endpoint**: Edit `src/api/main.py`, restart API
2. **Change UI**: Edit `frontend/src/App.js`, auto-reloads
3. **Add database field**: Edit `src/database/models.py`, delete DB, restart API
4. **Test API**: Use http://localhost:8000/docs swagger UI

### Running Specific Commands
```bash
# Build frontend for production
cd frontend && npm run build

# Test backend endpoints
pytest src/  # If tests exist

# Check code quality
# (Add linting tools like pylint, eslint as needed)
```

---

## Architecture Diagram

```
┌─ FRONTEND ─────────────────┐
│ React Dashboard            │
│ App.js (445 lines)         │
│ - City selector            │
│ - AQI cards                │
│ - Statistics               │
└────────────┬────────────────┘
             │ HTTP GET
             ▼
┌─ BACKEND ──────────────────┐
│ FastAPI (main.py)          │
│ 8 Endpoint groups          │
│ - /aqi/*                   │
│ - /weather/*               │
│ - /traffic/*               │
│ - /correlations/*          │
└────────────┬────────────────┘
             │ SQL
             ▼
┌─ DATABASE ─────────────────┐
│ PostgreSQL                 │
│ 5 tables:                  │
│ - aqi_data                 │
│ - weather_data             │
│ - traffic_data             │
│ - correlation_analysis     │
│ - ai_agent_queries         │
└────────────────────────────┘
             ▲
             │ Data Producers
      ┌──────┴──────┐
      │             │
┌─ AIRFLOW ──┐  ┌─ KAFKA ─┐
│ Ingestion  │  │ Streaming│
│ DAG        │  │ Message  │
└────────────┘  │ Broker  │
                └─────────┘
```

---

## Key Files to Study

| Priority | File | Why | Lines |
|----------|------|-----|-------|
| 🔴 High | `App.js` | Shows how frontend fetches & displays data | 445 |
| 🔴 High | `main.py` | Shows all API endpoints & database queries | 522 |
| 🔴 High | `models.py` | Shows database schema & relationships | 422 |
| 🟡 Medium | `db_connector.py` | Shows database connection pooling | - |
| 🟡 Medium | `ingestion_dag.py` | Shows data ingestion pipeline | - |
| 🟢 Low | `correlation_job.py` | Shows Spark data analysis | - |

---

## Tips for Learning

1. **Start with**: `CODE_DOCUMENTATION.md` for architecture overview
2. **Then read**: Inline comments in `App.js` to understand React
3. **Then read**: Inline comments in `main.py` to understand API
4. **Then read**: Inline comments in `models.py` to understand database
5. **Experiment**: Make small changes (add city, change color) and see results
6. **Debug**: Use browser console (F12) and API logs to understand data flow

---

## Support

- **API Docs**: http://localhost:8000/docs
- **Code Comments**: Every function has detailed comments
- **Inline Examples**: Check `CODE_DOCUMENTATION.md` for examples

---

**Last Updated**: 2024-01-15  
**Project Status**: ✅ Complete with full documentation  
**All code files are comprehensively commented for easy understanding**
