"""
AQI API Routes
Provides endpoints for AQI, weather, and traffic data
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database.db_connection import get_db
from database.models import AQIData, WeatherData, TrafficData, CorrelationAnalysis

# Create router
router = APIRouter()


# AQI Endpoints
@router.get("/aqi/latest", tags=["AQI"])
async def get_latest_aqi(
    location: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get latest AQI data
    
    - **location**: Filter by location name (optional)
    - **limit**: Number of records to return (1-100)
    """
    try:
        query = db.query(AQIData).order_by(desc(AQIData.timestamp))
        
        if location:
            query = query.filter(AQIData.location == location)
        
        results = query.limit(limit).all()
        
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
        raise HTTPException(status_code=500, detail=f"Error fetching AQI data: {str(e)}")


@router.get("/aqi/location/{location}", tags=["AQI"])
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
                    "pm10": r.pm10,
                    "timestamp": r.timestamp.isoformat()
                }
                for r in results
            ]
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching data: {str(e)}")


@router.get("/aqi/statistics/{location}", tags=["AQI"])
async def get_aqi_statistics(
    location: str,
    hours: int = Query(24, ge=1, le=168),
    db: Session = Depends(get_db)
):
    """
    Get AQI statistics for a location
    
    - **location**: Location name
    - **hours**: Time period for statistics (1-168 hours)
    """
    try:
        time_filter = datetime.utcnow() - timedelta(hours=hours)
        
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
        
        if stats.record_count == 0:
            raise HTTPException(status_code=404, detail=f"No data found for location: {location}")
        
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
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error calculating statistics: {str(e)}")


# Weather Endpoints
@router.get("/weather/latest", tags=["Weather"])
async def get_latest_weather(
    location: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get latest weather data
    
    - **location**: Filter by location name (optional)
    - **limit**: Number of records to return (1-100)
    """
    try:
        query = db.query(WeatherData).order_by(desc(WeatherData.timestamp))
        
        if location:
            query = query.filter(WeatherData.location == location)
        
        results = query.limit(limit).all()
        
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
                    "wind_direction": r.wind_direction,
                    "clouds": r.clouds,
                    "visibility": r.visibility,
                    "weather_main": r.weather_main,
                    "weather_description": r.weather_description,
                    "timestamp": r.timestamp.isoformat(),
                    "source": r.source
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching weather data: {str(e)}")


# Traffic Endpoints
@router.get("/traffic/latest", tags=["Traffic"])
async def get_latest_traffic(
    location: Optional[str] = None,
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db)
):
    """
    Get latest traffic data
    
    - **location**: Filter by location name (optional)
    - **limit**: Number of records to return (1-100)
    """
    try:
        query = db.query(TrafficData).order_by(desc(TrafficData.timestamp))
        
        if location:
            query = query.filter(TrafficData.location == location)
        
        results = query.limit(limit).all()
        
        return {
            "count": len(results),
            "data": [
                {
                    "id": r.id,
                    "location": r.location,
                    "latitude": r.latitude,
                    "longitude": r.longitude,
                    "congestion_level": r.congestion_level,
                    "congestion_score": r.congestion_score,
                    "average_speed": r.average_speed,
                    "vehicle_count": r.vehicle_count,
                    "timestamp": r.timestamp.isoformat(),
                    "source": r.source
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching traffic data: {str(e)}")


# Correlation Endpoints
@router.get("/correlations/latest", tags=["Correlations"])
async def get_latest_correlations(
    location: Optional[str] = None,
    limit: int = Query(5, ge=1, le=50),
    db: Session = Depends(get_db)
):
    """
    Get latest correlation analysis results
    
    - **location**: Filter by location name (optional)
    - **limit**: Number of records to return (1-50)
    """
    try:
        query = db.query(CorrelationAnalysis).order_by(desc(CorrelationAnalysis.analysis_timestamp))
        
        if location:
            query = query.filter(CorrelationAnalysis.location == location)
        
        results = query.limit(limit).all()
        
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
                    "min_aqi": r.min_aqi,
                    "avg_traffic_score": r.avg_traffic_score,
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


# Locations Endpoint
@router.get("/locations", tags=["Locations"])
async def get_locations(db: Session = Depends(get_db)):
    """Get all available locations with latest data summary"""
    try:
        # Get unique locations from AQI data
        locations = db.query(AQIData.location).distinct().all()
        
        location_data = []
        for loc in locations:
            location_name = loc[0]
            
            # Get latest AQI for this location
            latest_aqi = db.query(AQIData).filter(
                AQIData.location == location_name
            ).order_by(desc(AQIData.timestamp)).first()
            
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