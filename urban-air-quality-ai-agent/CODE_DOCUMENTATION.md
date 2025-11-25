# Urban Air Quality AI Agent - Code Documentation

## Overview

This document provides a comprehensive guide to understanding the codebase of the Urban Air Quality AI Agent project. The project is a full-stack application that monitors air quality, weather, and traffic data, then uses AI to generate insights.

---

## Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────┐
│                     React Frontend (localhost:3000)                 │
│                                                                     │
│  - Air Quality Dashboard                                           │
│  - City Selector & Auto-Refresh                                    │
│  - AQI Color-Coded Display                                         │
│  - Statistics & Insights                                           │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │ HTTP GET/POST
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│           FastAPI Backend (localhost:8000 / src/api/main.py)        │
│                                                                     │
│  8 Endpoint Groups:                                                │
│  - /health          → Database connection check                    │
│  - /aqi/*           → Air quality data (latest, history, stats)    │
│  - /weather/*       → Weather conditions (temp, humidity, wind)    │
│  - /traffic/*       → Traffic congestion data                      │
│  - /correlations/*  → Statistical relationships (from Spark)       │
│  - /locations       → List of monitored cities                     │
│  - /ai-agent/*      → AI query history                             │
└──────────────────────────────────┬──────────────────────────────────┘
                                   │ SQL Queries (SQLAlchemy ORM)
                                   ▼
┌─────────────────────────────────────────────────────────────────────┐
│        PostgreSQL Database (localhost:5432 / airflow database)      │
│                                                                     │
│  Tables:                                                           │
│  - aqi_data              → Air quality measurements                │
│  - weather_data          → Temperature, humidity, wind             │
│  - traffic_data          → Congestion, vehicle counts              │
│  - correlation_analysis  → Spark job results                       │
│  - ai_agent_queries      → User questions and AI responses         │
└─────────────────────────────────────────────────────────────────────┘
                                   ▲
                                   │ Data Producers
                                   │
┌─────────────────────────────────────────────────────────────────────┐
│              Data Ingestion Pipeline (Infrastructure)               │
│                                                                     │
│  - Airflow DAGs (airflow/dags/ingestion_dag.py)                    │
│    → Fetches data from AQICN, OpenWeather, Google Maps APIs       │
│    → Streams to Kafka topics                                       │
│                                                                     │
│  - Kafka (Real-time message broker)                                │
│    → ingestion_dag.py produces messages                            │
│    → consumer_to_postgres.py consumes & stores in DB               │
│                                                                     │
│  - Spark (Data processing)                                         │
│    → Runs correlation analysis jobs                                │
│    → Stores results back to correlation_analysis table             │
│                                                                     │
│  - Redis (Caching layer - optional)                                │
│    → Cache frequently accessed queries                             │
└─────────────────────────────────────────────────────────────────────┘
```

---

## File Structure & Documentation

### 1. Frontend

#### `frontend/src/App.js` (445 lines, FULLY DOCUMENTED)

**Purpose**: Main React component rendering the air quality dashboard

**Key Concepts**:
- **State Management**: React Hooks (useState, useEffect, useCallback)
- **Data Fetching**: Fetch API calls to FastAPI backend
- **Auto-Refresh**: Configurable interval timer for updating data
- **AQI Color-Coding**: Maps pollution levels to colors (green=good, red=hazardous)
- **Responsive Design**: CSS Grid layout for mobile/desktop

**State Variables**:
```javascript
data              // Air quality records from API
loading           // Loading indicator state
error             // Error message if fetch fails
selectedCity      // Currently selected city (dropdown)
refreshInterval   // How often to refresh (1-30 minutes)
alerts            // Pollution alerts from API
```

**Main Functions**:
- `fetchData()` - Fetches from `/aqi/latest` or `/aqi/location/{city}`
- `fetchInsights()` - Fetches AI insights (currently stubbed)
- `getAQICategory(aqi)` - Maps AQI number to category + color

**Data Flow**:
```
User selects city → fetchData() → API call → Parse response → 
Normalize data → setData() → React re-renders → Display cards
```

---

### 2. Backend API

#### `src/api/main.py` (522 lines, FULLY DOCUMENTED)

**Purpose**: FastAPI application providing REST endpoints for air quality data

**Architecture**:
- FastAPI framework (async, automatic OpenAPI docs at `/docs`)
- SQLAlchemy ORM for database queries
- CORS middleware (allows frontend requests)
- Dependency injection for database sessions

**Startup Flow**:
```python
1. @app.on_event("startup") runs when server starts
2. test_connection() → verify PostgreSQL is accessible
3. init_db() → create tables (idempotent, skips if exist)
4. API ready to accept requests
```

**Endpoint Groups**:

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/health` | GET | Check database connectivity |
| `/aqi/latest` | GET | Get latest AQI from all/filtered locations |
| `/aqi/location/{location}` | GET | Get 24-hour history for specific city |
| `/aqi/statistics/{location}` | GET | Get min/max/avg AQI for time period |
| `/weather/latest` | GET | Get latest weather data |
| `/traffic/latest` | GET | Get latest traffic congestion data |
| `/correlations/latest` | GET | Get Spark analysis results |
| `/locations` | GET | List all monitored cities |
| `/ai-agent/history` | GET | Get past AI queries & responses |

**Key Query Patterns**:
```python
# Get latest records
db.query(AQIData).order_by(desc(AQIData.timestamp)).limit(10).all()

# Filter + aggregate
db.query(func.avg(AQIData.aqi)).filter(AQIData.location == "delhi").first()

# Time-based filtering
time_filter = datetime.utcnow() - timedelta(hours=24)
db.query(...).filter(AQIData.timestamp >= time_filter).all()
```

---

### 3. Database

#### `src/database/models.py` (422 lines, FULLY DOCUMENTED)

**Purpose**: SQLAlchemy ORM model definitions mapping Python classes to database tables

**Tables**:

##### `AQIData` (Air Quality Index)
```python
Columns:
  id            → Primary key
  location      → City name (indexed)
  latitude      → Geographic coordinate
  longitude     → Geographic coordinate
  aqi           → Air Quality Index (0-500+)
  pm25, pm10    → Particulate matter concentration
  no2, so2, co, o3 → Individual pollutants
  timestamp     → When measured (indexed)
  source        → Data source (AQICN, etc.)

Indexes:
  (location, timestamp) → Fast queries like "Delhi's last 24 hours"
  timestamp → For time-based sorting
```

**Usage**: `/aqi/*` endpoints query this table

##### `WeatherData` (Temperature, Humidity, Wind)
```python
Columns:
  location, latitude, longitude → Geographic data
  temperature, feels_like → Temperature in Celsius
  humidity, pressure → Atmospheric conditions
  wind_speed, wind_direction → Wind measurements
  clouds, visibility → Sky conditions
  weather_main, weather_description → Conditions (Clear, Rain, etc.)
  timestamp → When recorded

Index: (location, timestamp)
```

**Usage**: `/weather/*` endpoints; correlated with AQI in analysis

##### `TrafficData` (Congestion, Vehicle Counts)
```python
Columns:
  location, latitude, longitude → Geographic data
  congestion_level → Categorical (low, moderate, high, severe)
  congestion_score → Numeric 0-100
  average_speed → km/h (lower = more congestion)
  vehicle_count → Number of vehicles detected
  timestamp → When recorded

Index: (location, timestamp)
```

**Usage**: `/traffic/*` endpoints; correlated with AQI to understand pollution sources

##### `CorrelationAnalysis` (Spark Job Results)
```python
Columns:
  location → City analyzed
  start_time, end_time → Analysis period
  aqi_traffic_correlation → Coefficient (-1 to 1)
  aqi_temperature_correlation → Coefficient
  aqi_humidity_correlation → Coefficient
  aqi_wind_correlation → Coefficient
  avg_aqi, max_aqi, min_aqi → Statistical summaries
  peak_pollution_hour → Hour of day with worst pollution (0-23)
  peak_traffic_hour → Hour of day with most traffic
  insight_summary → AI-generated text explanation
  analysis_timestamp → When analysis ran
  job_id → Spark job identifier

Index: (location, analysis_timestamp)
```

**Usage**: `/correlations/*` endpoints; displays relationships discovered by Spark

##### `AIAgentQuery` (Question-Answer History)
```python
Columns:
  id → Primary key
  user_query → The question asked
  agent_response → The AI-generated answer
  location → City the question was about
  query_timestamp → When asked
  response_time_ms → Milliseconds to generate response
  tokens_used → LLM tokens consumed (for cost)
  model_used → Which LLM (e.g., gpt-3.5-turbo)

Index: query_timestamp
```

**Usage**: `/ai-agent/history` endpoint; auditing & learning

#### `src/database/db_connector.py` (Full Connection Management, FULLY DOCUMENTED)

**Purpose**: Manage PostgreSQL connection pooling and session lifecycle

**Key Components**:

1. **Database URL Building**
```python
DATABASE_URL = f"postgresql://{user}:{password}@{host}:{port}/{database}"
```

2. **Connection Pool (QueuePool)**
```python
engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,      # Queue-based connection management
    pool_size=10,              # Keep 10 idle connections ready
    max_overflow=20,           # Allow 20 extra if needed (30 max total)
    pool_pre_ping=True         # Verify connections before using
)
```

3. **Session Factory**
```python
SessionLocal = sessionmaker(
    autocommit=False,          # Manual commit/rollback control
    autoflush=False,           # Explicit flush on commit
    bind=engine                # Use the connection pool
)
```

4. **Dependency Injection for FastAPI**
```python
def get_db():
    db = SessionLocal()
    try:
        yield db              # Provide to endpoint
    finally:
        db.close()           # Clean up (return to pool)

# Usage in endpoint:
@app.get("/endpoint")
def endpoint(db: Session = Depends(get_db)):
    # db is automatically injected by FastAPI
    records = db.query(Model).all()
```

5. **Functions**:
- `init_db()` → Create all tables from models
- `test_connection()` → Verify database accessibility
- `get_db()` → FastAPI dependency for sessions
- `get_db_session()` → Context manager for manual control

---

## Data Flow Examples

### Example 1: Frontend Displays Latest Air Quality

```
1. User opens app or clicks "Refresh"
   
2. React calls fetchData()
   → GET http://localhost:8000/aqi/latest?limit=50
   
3. FastAPI endpoint handler:
   a. get_db dependency provides database session
   b. db.query(AQIData).order_by(desc(timestamp)).limit(50).all()
   c. Format results as JSON
   d. Return response
   
4. Frontend receives JSON:
   {
     count: 50,
     data: [
       { location: "delhi", aqi: 157, pm25: 45.5, timestamp: "2024-01-15T10:30:00" },
       { location: "beijing", aqi: 201, pm25: 89.2, timestamp: "2024-01-15T10:30:00" },
       ...
     ]
   }
   
5. React normalizes data
   → Convert API response to internal format
   
6. React renders:
   a. Create card for each city
   b. getAQICategory(aqi) → determines color
   c. Color circle shows AQI, text shows category
   d. Display metrics (PM2.5, temperature, etc.)
   
7. Auto-refresh timer triggers in 5 minutes → repeat
```

### Example 2: Get Correlation Analysis

```
1. Spark job runs (scheduled by Airflow)
   a. Queries AQIData, WeatherData, TrafficData
   b. Calculates correlation coefficients
   c. Finds peak pollution/traffic hours
   d. Generates insight text
   e. Inserts into correlation_analysis table
   
2. Frontend calls: GET /correlations/latest?limit=5
   
3. FastAPI returns:
   {
     count: 1,
     data: [{
       location: "delhi",
       aqi_traffic_correlation: 0.87,
       aqi_temperature_correlation: -0.45,
       peak_pollution_hour: 18,
       peak_traffic_hour: 17,
       insight_summary: "High traffic (peak at 5pm) correlates strongly with pollution..."
     }]
   }
   
4. Frontend displays insights
```

---

## Key Concepts Explained

### AQI (Air Quality Index)

**What is it?**: A number representing overall air pollution level

**Scale**:
- 0-50: Good (Green) ✅
- 51-100: Moderate (Yellow) ⚠️
- 101-150: Unhealthy for Sensitive Groups (Orange) ⚠️⚠️
- 151-200: Unhealthy (Red) 🔴
- 201-300: Very Unhealthy (Purple) 🔴🔴
- 301+: Hazardous (Maroon) 🔴🔴🔴

**Components**:
- PM2.5 (fine dust)
- PM10 (coarse dust)
- NO₂ (nitrogen dioxide from vehicles)
- SO₂ (sulfur dioxide from industry)
- CO (carbon monoxide)
- O₃ (ozone)

### Correlation Coefficient

**Range**: -1.0 to 1.0

**Interpretation**:
- **+1.0**: Perfect positive (both increase together)
- **+0.7 to +1.0**: Strong positive relationship
- **+0.3 to +0.7**: Moderate positive
- **0**: No relationship
- **-0.3 to -0.7**: Moderate negative
- **-0.7 to -1.0**: Strong negative (one increases while other decreases)

**Example**: `aqi_traffic_correlation = 0.85` means:
- When traffic increases, pollution increases
- They move together 85% of the time
- Interpretation: Vehicle emissions are a major pollution driver

### CORS (Cross-Origin Resource Sharing)

**Problem**: Browser blocks requests from `localhost:3000` (frontend) to `localhost:8000` (backend)

**Solution**: Add CORS headers in FastAPI
```python
app.add_middleware(CORSMiddleware, allow_origins=["*"], ...)
# Tells browser: "It's OK to accept responses from this API"
```

---

## Common Tasks

### Adding a New Endpoint

```python
# 1. Create function in main.py
@app.get("/new-endpoint", tags=["Group"])
async def get_new_data(db: Session = Depends(get_db)):
    """Docstring with description and return format"""
    results = db.query(Model).all()
    return {"data": results}

# 2. Frontend calls it
fetch('http://localhost:8000/new-endpoint')
```

### Querying the Database

```python
# All records
db.query(AQIData).all()

# Filter
db.query(AQIData).filter(AQIData.location == "delhi").all()

# Order by
db.query(AQIData).order_by(desc(AQIData.timestamp)).all()

# Limit
db.query(AQIData).limit(10).all()

# Combine
db.query(AQIData)\
    .filter(AQIData.location == "delhi")\
    .order_by(desc(AQIData.timestamp))\
    .limit(10)\
    .all()

# Aggregate
db.query(
    func.avg(AQIData.aqi),
    func.max(AQIData.aqi),
    func.min(AQIData.aqi)
).filter(...).first()
```

### Adding a New Database Field

```python
# 1. Add field to model in models.py
class AQIData(Base):
    __tablename__ = "aqi_data"
    id = Column(Integer, primary_key=True)
    new_field = Column(String(100))  # New field

# 2. Migrations (Alembic) needed for production
# For development: delete database, re-create
# init_db() will create new schema

# 3. Update API endpoint to return new field
return {
    "data": [{
        "aqi": r.aqi,
        "new_field": r.new_field  # Include in response
    }]
}
```

---

## Debugging Guide

### API Not Responding

```bash
# Check if server is running
# Terminal 1: Start API
cd src
python -m uvicorn api.main:app --host 0.0.0.0 --port 8000 --reload

# Try health check
curl http://localhost:8000/health
```

### Database Connection Failed

```bash
# 1. Check PostgreSQL is running
# 2. Check .env file has correct credentials
POSTGRES_HOST=localhost
POSTGRES_USER=airflow
POSTGRES_PASSWORD=8520
POSTGRES_DB=airflow

# 3. Test connection directly
python -c "from src.database.db_connector import test_connection; test_connection()"

# 4. Check Docker container if using Docker
docker ps  # Verify postgres container running
docker logs airflow-postgres  # Check for errors
```

### Frontend Not Getting Data

```bash
# 1. Check browser console (F12)
# 2. Check API is running (see above)
# 3. Check CORS is enabled in FastAPI (main.py)
# 4. Make test fetch call
fetch('http://localhost:8000/aqi/latest?limit=5')
    .then(r => r.json())
    .then(d => console.log(d))
```

### Data Not Updating

```bash
# Check if data is being ingested
# 1. Query database directly
psql -U airflow -d airflow -c "SELECT * FROM aqi_data ORDER BY timestamp DESC LIMIT 5;"

# 2. Check Airflow DAGs are running
# Navigate to http://localhost:8080 (Airflow UI)

# 3. Check Kafka is receiving messages
# (Advanced: use Kafka CLI tools)
```

---

## Performance Tips

1. **Database Indexes**: Use indexes on frequently filtered columns (location, timestamp)
2. **Limit Results**: Always use `.limit()` to avoid fetching entire tables
3. **Connection Pooling**: Keep pool_size high enough for concurrent requests
4. **Caching**: Use Redis to cache `GET /correlations/latest` results
5. **Async**: FastAPI's async prevents blocking on I/O operations

---

## Security Notes

1. **CORS**: Change `allow_origins=["*"]` to specific domains in production
2. **Credentials**: Never commit `.env` file with real API keys
3. **SQL Injection**: SQLAlchemy ORM prevents this; don't use raw `text()` queries
4. **Rate Limiting**: Add rate limiting middleware for production
5. **Authentication**: Add OAuth2/JWT for API authentication

---

## Deployment

### Docker Compose

All services start together:
```bash
docker-compose up -d

# Verify all healthy
docker-compose ps
```

### Manual Startup

```bash
# Terminal 1: FastAPI
cd urban-air-quality-ai-agent
python -m uvicorn src.api.main:app --host 0.0.0.0 --port 8000

# Terminal 2: React Frontend
cd frontend
npm start

# Terminal 3: Airflow (if needed)
# Configure airflow + airflow scheduler, webserver, etc.
```

---

## Summary

- **Frontend** (React): Fetches data from API, displays AQI dashboard
- **Backend** (FastAPI): Provides 8 endpoint groups for different data types
- **Database** (PostgreSQL): Stores 5 tables of time-series data
- **Infrastructure** (Airflow, Kafka, Spark): Ingest, stream, and analyze data
- **All code is heavily commented** for easy understanding and modification

For questions about specific functions, files have inline comments explaining:
- **Purpose**: What the function/class does
- **Parameters**: What inputs it expects
- **Returns**: What it produces
- **Usage**: Real-world examples
- **Context**: Why it matters in the project

Happy coding! 🚀
