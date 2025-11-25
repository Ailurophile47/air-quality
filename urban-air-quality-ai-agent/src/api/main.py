"""
FastAPI Main Application - Urban Air Quality AI Agent
======================================================

This module provides REST API endpoints for the Urban Air Quality AI Agent project.
It serves as the backend for fetching and analyzing air quality, weather, traffic data,
and AI-powered insights.

ARCHITECTURE:
- Framework: FastAPI (async, high-performance Python web framework)
- Database: PostgreSQL with SQLAlchemy ORM for data persistence
- Cache: Redis (optional, can be integrated for caching)
- Streaming: Kafka for real-time data ingestion
- Authentication: CORS middleware for cross-origin requests (frontend can call this API)

KEY ENDPOINTS:
- /health - Database connectivity check
- /aqi/* - Air Quality Index data endpoints
- /weather/* - Weather data endpoints
- /traffic/* - Traffic congestion data endpoints
- /correlations/* - Statistical correlation analysis
- /ai-agent/history - AI agent query history
"""

import os
from datetime import datetime, timedelta
from typing import List, Optional

from fastapi import FastAPI, Depends, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import func, desc, text
from dotenv import load_dotenv

import sys
sys.path.append(os.path.dirname(os.path.dirname(__file__)))

# Import database utilities and models
from database.db_connector import get_db, init_db, test_connection
from database.models import AQIData, WeatherData, TrafficData, CorrelationAnalysis, AIAgentQuery

# Load environment variables from .env file (API keys, DB credentials, etc.)
load_dotenv()

# Initialize FastAPI application
# - title: displayed in API docs (/docs)
# - description: explains API purpose
# - version: API semantic version
# - docs_url: generates interactive Swagger UI documentation
# - redoc_url: generates ReDoc alternative documentation
app = FastAPI(
    title="Urban Air Quality & Traffic Insight API",
    description="REST API for air quality, weather, traffic data and AI-powered insights",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS (Cross-Origin Resource Sharing) middleware
# This allows the React frontend (running on localhost:3000) to make API calls to this backend (localhost:8000)
# In production, replace allow_origins=["*"] with specific domain(s) like ["https://yourdomain.com"]
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow requests from any origin (development only)
    allow_credentials=True,  # Allow cookies/credentials in cross-origin requests
    allow_methods=["*"],  # Allow all HTTP methods (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Allow all headers in requests
)


# ============================================================================
# STARTUP & HEALTH CHECK ENDPOINTS
# ============================================================================

# Startup event handler - runs once when the API server starts
@app.on_event("startup")
async def startup_event():
    """
    Initialize database on startup.
    
    This function:
    1. Tests connection to PostgreSQL database
    2. If connected, initializes all tables (create tables if they don't exist)
    3. Logs success/failure messages for debugging
    
    Called automatically when the FastAPI server starts (e.g., via `uvicorn src.api.main:app`)
    """
    print("🚀 Starting Urban Air Quality API...")
    if test_connection():
        init_db()
        print("✅ Database initialized successfully")
    else:
        print("⚠️  Database connection failed. Some endpoints may not work.")


# Root endpoint - simple health check
@app.get("/", tags=["Health"])
async def root():
    """
    Root endpoint / basic health check.
    
    Returns: Basic API information without database checks
    Use this to verify the API server is running
    """
    return {
        "status": "healthy",
        "message": "Urban Air Quality & Traffic Insight API",
        "version": "1.0.0",
        "timestamp": datetime.utcnow().isoformat()
    }


# Detailed health check with database connectivity test
@app.get("/health", tags=["Health"])
async def health_check(db: Session = Depends(get_db)):
    """
    Detailed health check endpoint with database connectivity verification.
    
    Endpoint: GET /health
    Returns: 
        - status: "healthy" if DB is connected, "degraded" otherwise
        - database: "connected" or error message
        - timestamp: UTC timestamp of check
    
    Usage: Frontend can call this to verify API is ready before making data requests
    """
    try:
        # Execute a simple test query (SELECT 1) to verify DB connection
        db.execute(text("SELECT 1"))
        db_status = "connected"
    except Exception as e:
        db_status = f"error: {str(e)}"
    
    return {
        "status": "healthy" if db_status == "connected" else "degraded",
        "database": db_status,
        "timestamp": datetime.utcnow().isoformat()
    }


# ============================================================================
# AQI (AIR QUALITY INDEX) ENDPOINTS
# ============================================================================
# These endpoints serve air quality data from the AQIData table in PostgreSQL
# AQI values range: 0 (best) to 500+ (hazardous)

@app.get("/aqi/latest", tags=["AQI"])
async def get_latest_aqi(
    location: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Fetch the latest AQI (Air Quality Index) records from the database.
    
    Endpoint: GET /aqi/latest?location=<city>&limit=<count>
    
    Query Parameters:
        - location (optional): Filter by city/location name (e.g., "bangalore")
        - limit (optional): Max number of records to return (default 10, max 100)
    
    Returns:
        {
            "count": <number of records>,
            "data": [
                {
                    "id": <record_id>,
                    "location": "<city>",
                    "latitude": <float>,
                    "longitude": <float>,
                    "aqi": <int (0-500+)>,
                    "pm25": <float (µg/m³)>,
                    "pm10": <float (µg/m³)>,
                    "no2": <float (ppb)>,
                    "so2": <float (ppb)>,
                    "co": <float (ppm)>,
                    "o3": <float (ppb)>,
                    "timestamp": "<ISO8601 datetime>",
                    "source": "<data source (e.g., WAQI API)>"
                },
                ...
            ]
        }
    
    Frontend Usage:
        fetch('http://localhost:8000/aqi/latest?limit=50')
            .then(res => res.json())
            .then(data => {
                // Display data.data array of AQI records
                // Color-code by AQI value (green=good, red=hazardous)
            })
    """
    try:
        # Build query: fetch AQI records, ordered by newest first
        query = db.query(AQIData).order_by(desc(AQIData.timestamp))
        
        # If location filter provided, apply it
        if location:
            query = query.filter(AQIData.location == location)
        
        # Fetch records limited to the requested amount
        results = query.limit(limit).all()
        
        # Return structured JSON response
        return {
            "count": len(results),
            "data": [
                {
                    "id": r.id,
                    "location": r.location,
                    "latitude": r.latitude,
                    "longitude": r.longitude,
                    "aqi": r.aqi,
                    "pm25": r.pm25,
                    "pm10": r.pm10,
                    "no2": r.no2,
                    "so2": r.so2,
                    "co": r.co,
                    "o3": r.o3,
                    "timestamp": r.timestamp.isoformat(),
                    "source": r.source
                }
                for r in results
            ]
        }
    except Exception as e:
        # Return HTTP 500 error if database query fails
        raise HTTPException(status_code=500, detail=f"Error fetching AQI data: {str(e)}")


@app.get("/aqi/location/{location}", tags=["AQI"])
async def get_aqi_by_location(
    location: str,
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """
    Get AQI history for a specific location
    
    - **location**: Location name
    - **hours**: Number of hours of historical data (1-168)
    """
    try:
        time_filter = datetime.utcnow() - timedelta(hours=hours)
        
        results = db.query(AQIData).filter(
            AQIData.location == location,
            AQIData.timestamp >= time_filter
        ).order_by(desc(AQIData.timestamp)).all()
        
        if not results:
            raise HTTPException(status_code=404, detail=f"No data found for location: {location}")
        
        return {
            "location": location,
            "period_hours": hours,
            "count": len(results),
            "data": [
                {
                    "aqi": r.aqi,
                    "pm25": r.pm25,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in results
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")


@app.get("/aqi/statistics/{location}", tags=["AQI"])
async def get_aqi_statistics(
    location: str,
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """
    Get statistical analysis of AQI over a time period.
    
    Endpoint: GET /aqi/statistics/{location}?hours=<number>
    
    Purpose: Provide aggregated statistics for understanding AQI trends
    
    Path Parameters:
        - location: City name (e.g., "beijing", "delhi")
    
    Query Parameters:
        - hours: Time period to analyze (1-168 hours = 1 week)
    
    Returns:
        {
            "location": "<city>",
            "period_hours": <hours>,
            "statistics": {
                "average_aqi": <float>,          # Mean AQI over period
                "maximum_aqi": <int>,             # Worst AQI reading
                "minimum_aqi": <int>,             # Best AQI reading
                "average_pm25": <float>,          # Mean PM2.5 concentration
                "record_count": <int>             # Number of data points
            }
        }
    
    Usage: Analyze pollution trends for a location
    Example: GET /aqi/statistics/delhi?hours=24
             Returns average, min, max AQI for last 24 hours in Delhi
    """
    try:
        # Calculate timestamp for filtering (e.g., 24 hours ago)
        time_filter = datetime.utcnow() - timedelta(hours=hours)
        
        # Query database for aggregate statistics using SQL aggregation functions
        # func.avg() = average, func.max() = maximum, func.min() = minimum, func.count() = count
        stats = db.query(
            func.avg(AQIData.aqi).label('avg_aqi'),
            func.max(AQIData.aqi).label('max_aqi'),
            func.min(AQIData.aqi).label('min_aqi'),
            func.avg(AQIData.pm25).label('avg_pm25'),
            func.count(AQIData.id).label('record_count')
        ).filter(
            AQIData.location == location,
            AQIData.timestamp >= time_filter
        ).first()
        
        # Check if we found any records
        if stats.record_count == 0:
            raise HTTPException(status_code=404, detail=f"No data found for location: {location}")
        
        # Return structured response with statistics
        return {
            "location": location,
            "period_hours": hours,
            "statistics": {
                "average_aqi": round(float(stats.avg_aqi), 2) if stats.avg_aqi else None,
                "maximum_aqi": int(stats.max_aqi) if stats.max_aqi else None,
                "minimum_aqi": int(stats.min_aqi) if stats.min_aqi else None,
                "average_pm25": round(float(stats.avg_pm25), 2) if stats.avg_pm25 else None,
                "record_count": stats.record_count
            }
        }
    except HTTPException:
        raise  # Re-raise 404 errors
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating statistics: {str(e)}")


# ============================================================================
# WEATHER DATA ENDPOINTS
# ============================================================================

@app.get("/weather/latest", tags=["Weather"])
async def get_latest_weather(
    location: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get latest weather measurements from all locations or filtered by location.
    
    Endpoint: GET /weather/latest?location=<city>&limit=<count>
    
    Purpose: Fetch current weather conditions (temperature, humidity, wind)
    
    Query Parameters:
        - location: Filter by city (optional)
        - limit: Max records to return (default 10, max 100)
    
    Returns:
        {
            "count": <number>,
            "data": [
                {
                    "id": <int>,
                    "location": "<city>",
                    "temperature": <float>,       # Celsius
                    "feels_like": <float>,        # Apparent temperature
                    "humidity": <float>,          # Percentage
                    "pressure": <float>,          # hPa
                    "wind_speed": <float>,        # m/s
                    "weather_main": "<type>",     # "Clear", "Rain", "Cloud", etc.
                    "weather_description": "<desc>",
                    "timestamp": "<ISO8601>"
                },
                ...
            ]
        }
    
    Use Case: Display weather widget on dashboard, correlate weather with pollution
    """
    try:
        # Build query ordered by newest readings first
        query = db.query(WeatherData).order_by(desc(WeatherData.timestamp))
        
        # Apply location filter if provided
        if location:
            query = query.filter(WeatherData.location == location)
        
        # Fetch and limit results
        results = query.limit(limit).all()
        
        # Format response
        return {
            "count": len(results),
            "data": [
                {
                    "id": r.id,
                    "location": r.location,
                    "temperature": r.temperature,
                    "feels_like": r.feels_like,
                    "humidity": r.humidity,
                    "pressure": r.pressure,
                    "wind_speed": r.wind_speed,
                    "weather_main": r.weather_main,
                    "weather_description": r.weather_description,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weather data: {str(e)}")


# ============================================================================
# TRAFFIC DATA ENDPOINTS
# ============================================================================

@app.get("/traffic/latest", tags=["Traffic"])
async def get_latest_traffic(
    location: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get latest traffic congestion data from all locations or filtered by location.
    
    Endpoint: GET /traffic/latest?location=<city>&limit=<count>
    
    Purpose: Show current traffic conditions (congestion levels, vehicle counts)
    
    Query Parameters:
        - location: Filter by city (optional)
        - limit: Max records to return (default 10, max 100)
    
    Returns:
        {
            "count": <number>,
            "data": [
                {
                    "id": <int>,
                    "location": "<city>",
                    "congestion_level": "<low|moderate|high|severe>",
                    "congestion_score": <0-100>,     # Quantitative measure
                    "average_speed": <float>,         # km/h
                    "vehicle_count": <int>,           # Number of vehicles
                    "timestamp": "<ISO8601>"
                },
                ...
            ]
        }
    
    INSIGHT: High traffic correlates with vehicle emissions and higher AQI
    Use Case: Analyze traffic-pollution relationship, predict pollution spikes
    """
    try:
        # Build query ordered by newest readings first
        query = db.query(TrafficData).order_by(desc(TrafficData.timestamp))
        
        # Apply location filter if provided
        if location:
            query = query.filter(TrafficData.location == location)
        
        # Fetch and limit results
        results = query.limit(limit).all()
        
        # Format response
        return {
            "count": len(results),
            "data": [
                {
                    "id": r.id,
                    "location": r.location,
                    "congestion_level": r.congestion_level,
                    "congestion_score": r.congestion_score,
                    "average_speed": r.average_speed,
                    "vehicle_count": r.vehicle_count,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching traffic data: {str(e)}")


# ============================================================================
# CORRELATION ANALYSIS ENDPOINTS
# ============================================================================

@app.get("/correlations/latest", tags=["Correlations"])
async def get_latest_correlations(
    location: Optional[str] = None,
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get latest correlation analysis results from Spark jobs.
    
    Endpoint: GET /correlations/latest?location=<city>&limit=<count>
    
    Purpose: Retrieve AI-generated insights about relationships between:
             - AQI (air pollution) vs Traffic (vehicle emissions)
             - AQI vs Weather (temperature, wind, humidity)
             
    These correlations are calculated by Spark jobs running in Airflow pipeline.
    
    Query Parameters:
        - location: Filter by city (optional)
        - limit: Max records to return (default 5, max 50)
    
    Returns:
        {
            "count": <number>,
            "data": [
                {
                    "id": <int>,
                    "location": "<city>",
                    "aqi_traffic_correlation": <-1.0 to 1.0>,     # How much traffic affects AQI
                    "aqi_temperature_correlation": <float>,        # Temperature effect
                    "aqi_humidity_correlation": <float>,           # Humidity effect
                    "aqi_wind_correlation": <float>,               # Wind effect
                    "avg_aqi": <float>,                            # Average during period
                    "max_aqi": <float>,                            # Peak pollution
                    "peak_pollution_hour": <0-23>,                 # Hour with worst pollution
                    "peak_traffic_hour": <0-23>,                   # Hour with most traffic
                    "insight_summary": "<human-readable insight>", # AI-generated explanation
                    "analysis_timestamp": "<ISO8601>"
                },
                ...
            ]
        }
    
    CORRELATION INTERPRETATION:
    - Correlation = 0.7 to 1.0: Strong positive (both increase together)
    - Correlation = 0.3 to 0.7: Moderate positive
    - Correlation = -0.7 to -1.0: Strong negative (one increases, other decreases)
    - Correlation = 0: No relationship
    
    Example: aqi_traffic_correlation = 0.85 means:
             → Higher traffic strongly correlates with higher pollution
             → Vehicle emissions are a major pollution driver
    
    Use Case: Answer "Why is pollution high?" questions, forecast pollution
    """
    try:
        # Query correlation analysis table, ordered by newest analysis first
        query = db.query(CorrelationAnalysis).order_by(desc(CorrelationAnalysis.analysis_timestamp))
        
        # Apply location filter if provided
        if location:
            query = query.filter(CorrelationAnalysis.location == location)
        
        # Fetch and limit results
        results = query.limit(limit).all()
        
        # Format response
        return {
            "count": len(results),
            "data": [
                {
                    "id": r.id,
                    "location": r.location,
                    "aqi_traffic_correlation": r.aqi_traffic_correlation,
                    "aqi_temperature_correlation": r.aqi_temperature_correlation,
                    "aqi_humidity_correlation": r.aqi_humidity_correlation,
                    "aqi_wind_correlation": r.aqi_wind_correlation,
                    "avg_aqi": r.avg_aqi,
                    "max_aqi": r.max_aqi,
                    "peak_pollution_hour": r.peak_pollution_hour,
                    "peak_traffic_hour": r.peak_traffic_hour,
                    "insight_summary": r.insight_summary,
                    "analysis_timestamp": r.analysis_timestamp.isoformat()
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching correlations: {str(e)}")


# ============================================================================
# LOCATION ENDPOINTS
# ============================================================================

@app.get("/locations", tags=["Locations"])
async def get_locations(db: Session = Depends(get_db)):
    """
    Get list of all monitored locations with latest data summary.
    
    Endpoint: GET /locations
    
    Purpose: Discover available cities and their current status
    
    Returns:
        {
            "count": <number of cities>,
            "locations": [
                {
                    "location": "<city>",
                    "latitude": <float>,
                    "longitude": <float>,
                    "latest_aqi": <int>,              # Most recent AQI reading
                    "last_updated": "<ISO8601>"       # When this data was recorded
                },
                ...
            ]
        }
    
    Use Case: Populate city dropdown in frontend, show which cities have data
    """
    try:
        # Get all unique location names from AQI data table
        locations = db.query(AQIData.location).distinct().all()
        
        location_data = []
        for loc in locations:
            location_name = loc[0]
            
            # For each location, get the most recent AQI record
            latest_aqi = db.query(AQIData).filter(
                AQIData.location == location_name
            ).order_by(desc(AQIData.timestamp)).first()
            
            # If we found a record, add it to response
            if latest_aqi:
                location_data.append({
                    "location": location_name,
                    "latitude": latest_aqi.latitude,
                    "longitude": latest_aqi.longitude,
                    "latest_aqi": latest_aqi.aqi,
                    "last_updated": latest_aqi.timestamp.isoformat()
                })
        
        return {
            "count": len(location_data),
            "locations": location_data
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching locations: {str(e)}")


# ============================================================================
# AI AGENT ENDPOINTS
# ============================================================================

@app.get("/ai-agent/history", tags=["AI Agent"])
async def get_agent_history(
    limit: int = Query(10, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get AI agent query history - all questions users asked and responses.
    
    Endpoint: GET /ai-agent/history?limit=<count>
    
    Purpose: Show past interactions with AI for:
             - User learning (see example queries/responses)
             - AI performance tracking (response time, accuracy)
             - Auditing (what users asked)
    
    Query Parameters:
        - limit: Number of records to return (1-50, default 10)
    
    Returns:
        {
            "count": <number>,
            "data": [
                {
                    "id": <int>,
                    "query": "<user question>",       # e.g., "Why is pollution high today?"
                    "response": "<AI answer>",        # e.g., "High traffic + low wind"
                    "location": "<city>",             # If location-specific
                    "timestamp": "<ISO8601>",         # When query was made
                    "response_time_ms": <int>         # How long AI took to respond
                },
                ...
            ]
        }
    
    Example Query: "What causes pollution in Beijing?"
    Example Response: "Top factors: Vehicle emissions (70%), Industrial sources (20%), 
                       Dust storms (10%). Current wind is low, trapping pollutants."
    
    Use Case: View past conversations, understand pollution causes, improve AI
    """
    try:
        # Query AI history table, ordered by most recent first
        results = db.query(AIAgentQuery).order_by(
            desc(AIAgentQuery.query_timestamp)
        ).limit(limit).all()
        
        # Format response
        return {
            "count": len(results),
            "data": [
                {
                    "id": r.id,
                    "query": r.user_query,
                    "response": r.agent_response,
                    "location": r.location,
                    "timestamp": r.query_timestamp.isoformat(),
                    "response_time_ms": r.response_time_ms
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    
    host = os.getenv("FASTAPI_HOST", "0.0.0.0")
    port = int(os.getenv("FASTAPI_PORT", 8000))
    
    print(f"🚀 Starting FastAPI server on {host}:{port}")
    uvicorn.run(app, host=host, port=port, reload=True)