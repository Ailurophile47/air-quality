"""
AI Insights API Routes
Provides endpoints for AI-powered insights using LangChain + OpenAI
"""

import os
import sys
import time
from datetime import datetime
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field
from sqlalchemy.orm import Session
from sqlalchemy import desc
from dotenv import load_dotenv

sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from database.db_connection import get_db
from database.models import AIAgentQuery, AQIData, TrafficData, CorrelationAnalysis
from ai_agent.agent import AirQualityAgent

# Load environment variables
load_dotenv()

# Create router
router = APIRouter()

# Initialize AI agent
try:
    agent = AirQualityAgent()
    print("✅ AI Agent initialized successfully")
except Exception as e:
    print(f"⚠️  AI Agent initialization warning: {e}")
    agent = None


# Request/Response models
class InsightRequest(BaseModel):
    """Request model for AI insights"""
    query: str = Field(..., min_length=5, max_length=500, description="User question about air quality")
    location: Optional[str] = Field(None, description="Specific location to analyze")
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Why is AQI high today in Koramangala?",
                "location": "Koramangala"
            }
        }


class InsightResponse(BaseModel):
    """Response model for AI insights"""
    query: str
    response: str
    location: Optional[str]
    timestamp: str
    response_time_ms: int
    sources_used: list
    
    class Config:
        schema_extra = {
            "example": {
                "query": "Why is AQI high today?",
                "response": "The AQI is elevated due to increased traffic congestion during peak hours...",
                "location": "Koramangala",
                "timestamp": "2024-01-15T10:30:00",
                "response_time_ms": 1250,
                "sources_used": ["aqi_data", "traffic_data", "correlation_analysis"]
            }
        }


@router.post("/insights-ai-agent", tags=["AI Insights"])
async def ask_ai_agent(
    request: InsightRequest,
    db: Session = Depends(get_db)
):
    """
    Ask AI agent a question about air quality
    
    Uses LangChain + OpenAI to provide intelligent insights based on:
    - Real-time AQI data
    - Weather conditions
    - Traffic patterns
    - Historical correlations
    
    **Example queries:**
    - "Why is AQI high today?"
    - "What is the trend of pollution this week in Indiranagar?"
    - "Is traffic causing pollution in Whitefield?"
    - "What time of day has the worst air quality?"
    """
    if agent is None:
        raise HTTPException(
            status_code=503,
            detail="AI Agent is not available. Please check OpenAI API key configuration."
        )
    
    start_time = time.time()
    
    try:
        # Get AI response
        response = agent.get_insight(
            query=request.query,
            location=request.location
        )
        
        # Calculate response time
        response_time_ms = int((time.time() - start_time) * 1000)
        
        # Store query in database
        try:
            query_record = AIAgentQuery(
                user_query=request.query,
                agent_response=response,
                location=request.location,
                response_time_ms=response_time_ms,
                tokens_used=None,  # Could be extracted from OpenAI response
                model_used="gpt-4"
            )
            db.add(query_record)
            db.commit()
        except Exception as db_error:
            print(f"⚠️  Failed to save query to database: {db_error}")
        
        return {
            "query": request.query,
            "response": response,
            "location": request.location,
            "timestamp": datetime.utcnow().isoformat(),
            "response_time_ms": response_time_ms,
            "sources_used": ["aqi_data", "weather_data", "traffic_data", "correlation_analysis"]
        }
        
    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Error generating insight: {str(e)}"
        )


@router.get("/insights/suggestions", tags=["AI Insights"])
async def get_query_suggestions():
    """
    Get suggested queries for users
    
    Returns a list of example questions users can ask the AI agent
    """
    return {
        "suggestions": [
            {
                "category": "Current Conditions",
                "queries": [
                    "Why is AQI high today?",
                    "What's the current air quality in Koramangala?",
                    "Is it safe to go for a run now?",
                    "Should I wear a mask outdoors today?"
                ]
            },
            {
                "category": "Trends & Patterns",
                "queries": [
                    "What is the pollution trend this week?",
                    "How has air quality changed in the last 24 hours?",
                    "Which day had the best air quality this week?",
                    "Show me the AQI pattern for Indiranagar"
                ]
            },
            {
                "category": "Correlations & Causes",
                "queries": [
                    "Is traffic causing pollution in Indiranagar?",
                    "How does weather affect air quality?",
                    "What time of day has the worst AQI?",
                    "Does rain help reduce pollution levels?"
                ]
            },
            {
                "category": "Predictions & Recommendations",
                "queries": [
                    "Will air quality improve tonight?",
                    "What's the best time to exercise outdoors?",
                    "Should I avoid going out during rush hour?",
                    "When is pollution expected to be lowest?"
                ]
            },
            {
                "category": "Location Comparisons",
                "queries": [
                    "Which area has better air quality: Whitefield or BTM Layout?",
                    "Compare pollution levels across all locations",
                    "Which location has the highest traffic congestion?",
                    "Where should I live for better air quality?"
                ]
            }
        ]
    }


@router.get("/insights/quick/{location}", tags=["AI Insights"])
async def get_quick_insights(
    location: str,
    db: Session = Depends(get_db)
):
    """
    Get quick pre-generated insights for a location
    
    Faster than AI agent, uses cached correlation data
    """
    try:
        # Get latest correlation analysis
        correlation = db.query(CorrelationAnalysis).filter(
            CorrelationAnalysis.location == location
        ).order_by(desc(CorrelationAnalysis.analysis_timestamp)).first()
        
        # Get current AQI
        latest_aqi = db.query(AQIData).filter(
            AQIData.location == location
        ).order_by(desc(AQIData.timestamp)).first()
        
        # Get current traffic
        latest_traffic = db.query(TrafficData).filter(
            TrafficData.location == location
        ).order_by(desc(TrafficData.timestamp)).first()
        
        if not latest_aqi:
            raise HTTPException(status_code=404, detail=f"No data found for location: {location}")
        
        # Generate quick insights
        insights = []
        
        # AQI level insight
        aqi = latest_aqi.aqi
        if aqi <= 50:
            insights.append({
                "type": "good",
                "level": "Good",
                "color": "green",
                "message": "Air quality is good. Great time for outdoor activities!",
                "recommendation": "Enjoy outdoor activities without restrictions."
            })
        elif aqi <= 100:
            insights.append({
                "type": "moderate",
                "level": "Moderate",
                "color": "yellow",
                "message": "Air quality is moderate. Acceptable for most people.",
                "recommendation": "Sensitive individuals should limit prolonged outdoor exertion."
            })
        elif aqi <= 150:
            insights.append({
                "type": "unhealthy_sensitive",
                "level": "Unhealthy for Sensitive Groups",
                "color": "orange",
                "message": "Members of sensitive groups may experience health effects.",
                "recommendation": "People with respiratory conditions should reduce outdoor activities."
            })
        elif aqi <= 200:
            insights.append({
                "type": "unhealthy",
                "level": "Unhealthy",
                "color": "red",
                "message": "Everyone may begin to experience health effects.",
                "recommendation": "Avoid prolonged outdoor exposure. Wear masks if necessary."
            })
        else:
            insights.append({
                "type": "very_unhealthy",
                "level": "Very Unhealthy",
                "color": "purple",
                "message": "Health alert: everyone may experience serious health effects.",
                "recommendation": "Stay indoors and use air purifiers. Avoid all outdoor activities."
            })
        
        # Traffic correlation insight
        if correlation and correlation.aqi_traffic_correlation is not None:
            if correlation.aqi_traffic_correlation > 0.5:
                insights.append({
                    "type": "correlation",
                    "message": f"Strong correlation between traffic and pollution detected (r={correlation.aqi_traffic_correlation:.2f})",
                    "recommendation": "Traffic congestion is a major contributor to air pollution in this area."
                })
            elif correlation.aqi_traffic_correlation > 0.3:
                insights.append({
                    "type": "correlation",
                    "message": f"Moderate correlation between traffic and pollution (r={correlation.aqi_traffic_correlation:.2f})",
                    "recommendation": "Traffic contributes to air pollution, especially during peak hours."
                })
        
        # Peak hours insight
        if correlation and correlation.peak_pollution_hour is not None:
            insights.append({
                "type": "peak_hours",
                "message": f"Pollution typically peaks around {correlation.peak_pollution_hour}:00 hours.",
                "recommendation": f"Avoid outdoor activities near {correlation.peak_pollution_hour}:00 for better health."
            })
        
        # Current traffic insight
        if latest_traffic:
            if latest_traffic.congestion_level in ["high", "severe"]:
                insights.append({
                    "type": "traffic",
                    "message": f"Current traffic congestion is {latest_traffic.congestion_level}.",
                    "recommendation": "High traffic is likely contributing to elevated pollution levels right now."
                })
        
        return {
            "location": location,
            "current_aqi": aqi,
            "current_pm25": latest_aqi.pm25,
            "current_traffic": latest_traffic.congestion_level if latest_traffic else "unknown",
            "insights": insights,
            "last_updated": latest_aqi.timestamp.isoformat(),
            "correlation_data": {
                "available": correlation is not None,
                "aqi_traffic_correlation": correlation.aqi_traffic_correlation if correlation else None,
                "peak_pollution_hour": correlation.peak_pollution_hour if correlation else None,
                "peak_traffic_hour": correlation.peak_traffic_hour if correlation else None
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating quick insights: {str(e)}")


@router.get("/insights/history", tags=["AI Insights"])
async def get_agent_history(
    limit: int = Query(10, ge=1, le=50),
    location: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    Get AI agent query history
    
    - **limit**: Number of records to return (1-50)
    - **location**: Filter by location (optional)
    """
    try:
        query = db.query(AIAgentQuery).order_by(desc(AIAgentQuery.query_timestamp))
        
        if location:
            query = query.filter(AIAgentQuery.location == location)
        
        results = query.limit(limit).all()
        
        return {
            "count": len(results),
            "data": [
                {
                    "id": r.id,
                    "query": r.user_query,
                    "response": r.agent_response,
                    "location": r.location,
                    "timestamp": r.query_timestamp.isoformat(),
                    "response_time_ms": r.response_time_ms,
                    "model_used": r.model_used
                }
                for r in results
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching history: {str(e)}")