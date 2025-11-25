"""
SQLAlchemy ORM Models - Urban Air Quality AI Agent Database Schema
===================================================================

This module defines all database tables as Python classes using SQLAlchemy ORM.
Each class represents a table in PostgreSQL and maps Python objects to database rows.

WHY ORM?
- Write database queries in Python instead of raw SQL
- Automatic type validation and conversion
- Protection against SQL injection
- Easy schema migrations
- Model-driven development

TABLES:
1. aqi_data - Air Quality Index measurements
2. weather_data - Weather conditions (temperature, humidity, wind, etc.)
3. traffic_data - Traffic congestion levels and vehicle counts
4. correlation_analysis - Results from Spark jobs analyzing relationships between datasets
5. ai_agent_queries - History of user queries and AI-generated insights

DATA FLOW:
  Kafka → Spark Processing → Store in PostgreSQL → API Endpoints → Frontend Display
"""

from datetime import datetime
from sqlalchemy import (
    Column, Integer, Float, String, DateTime, 
    Text, Boolean, Index, ForeignKey
)
from sqlalchemy.orm import relationship

from .db_connector import Base


class AQIData(Base):
    """
    Air Quality Index (AQI) Measurements Table
    
    Stores real-time and historical air quality readings collected from AQICN API
    or other data sources. Data is ingested via Airflow DAG and streamed through Kafka.
    
    AQI Scale:
      0-50     : Good (Green)
      51-100   : Moderate (Yellow)
      101-150  : Unhealthy for Sensitive Groups (Orange)
      151-200  : Unhealthy (Red)
      201-300  : Very Unhealthy (Purple)
      301+     : Hazardous (Maroon)
    
    Used By: /aqi/* endpoints to serve air quality data to frontend
    """
    __tablename__ = "aqi_data"
    
    # Primary key: unique identifier for each record
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Location identification
    location = Column(String(100), nullable=False, index=True)  # City name (e.g., "bangalore")
    latitude = Column(Float, nullable=False)   # Geographic latitude
    longitude = Column(Float, nullable=False)  # Geographic longitude
    
    # AQI and Pollutant Measurements (all in various units as per standards)
    aqi = Column(Integer, nullable=False)  # Main AQI value (0-500+)
    pm25 = Column(Float)     # PM2.5 particulate matter (µg/m³)
    pm10 = Column(Float)     # PM10 particulate matter (µg/m³)
    no2 = Column(Float)      # Nitrogen dioxide (ppb)
    so2 = Column(Float)      # Sulfur dioxide (ppb)
    co = Column(Float)       # Carbon monoxide (ppm)
    o3 = Column(Float)       # Ozone (ppb)
    
    # Temporal and metadata fields
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    source = Column(String(50), default="AQICN")  # Data source identifier
    created_at = Column(DateTime, default=datetime.utcnow)  # Record creation timestamp
    
    # Database indexes for fast queries
    # Queries often filter by (location + timestamp), so compound index helps
    __table_args__ = (
        Index('idx_location_timestamp', 'location', 'timestamp'),
        Index('idx_timestamp', 'timestamp'),
    )
    
    def __repr__(self):
        """Human-readable representation for debugging"""
        return f"<AQIData(location='{self.location}', aqi={self.aqi}, timestamp='{self.timestamp}')>"


class WeatherData(Base):
    """
    Weather Measurements Table
    
    Stores weather conditions collected from OpenWeather API.
    Data is correlated with AQI to analyze weather-pollution relationships.
    
    Weather factors impact air quality:
    - High temp + low wind speed → pollution accumulation
    - Rain → temporarily improves air quality (washes out pollutants)
    - Low visibility → can indicate high pollution
    
    Used By: /weather/* endpoints; also used in correlation analysis
    """
    __tablename__ = "weather_data"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Location identification
    location = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Temperature and "feels like" (wind chill / heat index)
    temperature = Column(Float)  # Celsius
    feels_like = Column(Float)   # Apparent temperature adjusted for wind/humidity
    humidity = Column(Float)     # Percentage (0-100)
    pressure = Column(Float)     # Atmospheric pressure (hPa)
    
    # Wind measurements
    wind_speed = Column(Float)   # m/s
    wind_direction = Column(Float)  # Degrees (0-360)
    
    # Sky and visibility
    clouds = Column(Float)       # Cloud coverage percentage
    visibility = Column(Float)   # Visibility distance (meters)
    
    # Weather conditions
    weather_main = Column(String(50))  # Category: "Clear", "Clouds", "Rain", "Snow", etc.
    weather_description = Column(String(100))  # Detailed description
    
    # Temporal and metadata
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    source = Column(String(50), default="OpenWeather")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_weather_location_timestamp', 'location', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<WeatherData(location='{self.location}', temp={self.temperature}°C, timestamp='{self.timestamp}')>"


class TrafficData(Base):
    """
    Traffic Measurements Table
    
    Stores traffic congestion levels and vehicle counts from Google Maps / similar APIs.
    Heavy traffic correlates with higher pollution from vehicle emissions.
    
    Used By: /traffic/* endpoints; also used in correlation analysis with AQI
    """
    __tablename__ = "traffic_data"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Location identification
    location = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Congestion measurements
    congestion_level = Column(String(20))  # Qualitative: "low", "moderate", "high", "severe"
    congestion_score = Column(Float)  # Quantitative: 0-100 scale
    average_speed = Column(Float)     # km/h (lower speed = more congestion)
    vehicle_count = Column(Integer)   # Number of vehicles detected
    
    # Temporal and metadata
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    source = Column(String(50), default="GoogleMaps")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_traffic_location_timestamp', 'location', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<TrafficData(location='{self.location}', congestion='{self.congestion_level}', timestamp='{self.timestamp}')>"


class CorrelationAnalysis(Base):
    """
    Correlation Analysis Results Table
    
    Stores insights generated by Spark jobs analyzing relationships between:
    - Air Quality (AQI, pollutants)
    - Traffic (congestion, vehicle count)
    - Weather (temperature, wind, humidity)
    
    This table is populated by Spark processing jobs running in Airflow.
    Helps answer questions like:
    - "How much does traffic increase pollution?"
    - "What time of day has worst air quality?"
    - "Does humidity worsen air quality?"
    
    Used By: /correlations/* endpoints; frontend displays insights
    """
    __tablename__ = "correlation_analysis"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Location
    location = Column(String(100), nullable=False, index=True)
    
    # Analysis time period
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    
    # Correlation coefficients (-1 to +1)
    # Positive = both variables increase together
    # Negative = one increases while other decreases
    # 0 = no relationship
    aqi_traffic_correlation = Column(Float)       # How much traffic affects pollution
    aqi_temperature_correlation = Column(Float)   # Temperature's effect on AQI
    aqi_humidity_correlation = Column(Float)      # Humidity's effect on AQI
    aqi_wind_correlation = Column(Float)          # Wind's effect on AQI
    
    # Statistical summaries
    avg_aqi = Column(Float)
    max_aqi = Column(Float)
    min_aqi = Column(Float)
    avg_traffic_score = Column(Float)
    
    # Time-based insights
    peak_pollution_hour = Column(Integer)  # Hour of day (0-23) with worst pollution
    peak_traffic_hour = Column(Integer)    # Hour with highest traffic
    
    # AI-generated insight summary
    insight_summary = Column(Text)  # Human-readable summary of findings
    
    # Metadata
    analysis_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    job_id = Column(String(100))  # Spark job ID for tracking
    
    __table_args__ = (
        Index('idx_correlation_location_time', 'location', 'analysis_timestamp'),
    )
    
    def __repr__(self):
        return f"<CorrelationAnalysis(location='{self.location}', aqi_traffic_corr={self.aqi_traffic_correlation:.2f})>"


class AIAgentQuery(Base):
    """
    AI Agent Query History Table
    
    Stores all questions asked by users to the AI agent and its responses.
    Used for:
    - Auditing: track what users asked
    - Analytics: understand user interests
    - Training: improve the AI agent over time
    - Performance monitoring: track response times
    
    Example User Query: "Why is pollution high in Bangalore today?"
    Example AI Response: "High traffic on MG Road + low wind speed = pollution accumulation"
    
    Used By: /ai-agent/history endpoint
    """
    __tablename__ = "ai_agent_queries"
    
    # Primary key
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Query and response
    user_query = Column(Text, nullable=False)  # User's question
    agent_response = Column(Text, nullable=False)  # AI's answer
    
    # Context
    location = Column(String(100))  # City/location the query is about
    query_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Performance and cost metrics
    response_time_ms = Column(Integer)  # Time taken to generate response (milliseconds)
    tokens_used = Column(Integer)       # LLM tokens consumed (for cost tracking)
    model_used = Column(String(50))     # Which LLM model (e.g., "gpt-3.5-turbo")
    
    def __repr__(self):
        """Human-readable format (truncate long query)"""
        query_preview = self.user_query[:50] + "..." if len(self.user_query) > 50 else self.user_query
        return f"<AIAgentQuery(id={self.id}, query='{query_preview}')>"


# Database initialization script (run this file directly to create tables)
if __name__ == "__main__":
    from .db_connector import init_db, test_connection
    
    print("🔧 Initializing database schema...")
    
    if test_connection():
        init_db()
        print("✅ All tables created successfully!")
        print("\nTables created:")
        print("  1. aqi_data - Air quality measurements")
        print("  2. weather_data - Weather conditions")
        print("  3. traffic_data - Traffic congestion data")
        print("  4. correlation_analysis - Statistical insights")
        print("  5. ai_agent_queries - AI conversation history")
    else:
        print("❌ Failed to connect to database. Check PostgreSQL is running and credentials in .env are correct.")