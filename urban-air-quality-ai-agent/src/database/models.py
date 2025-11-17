"""
SQLAlchemy ORM models for Urban Air Quality AI Agent
Defines database schema for AQI, weather, traffic, and correlation data
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
    Air Quality Index measurements
    Stores real-time and historical AQI readings
    """
    __tablename__ = "aqi_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    location = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # AQI metrics
    aqi = Column(Integer, nullable=False)
    pm25 = Column(Float)  # PM2.5 particulate matter
    pm10 = Column(Float)  # PM10 particulate matter
    no2 = Column(Float)   # Nitrogen dioxide
    so2 = Column(Float)   # Sulfur dioxide
    co = Column(Float)    # Carbon monoxide
    o3 = Column(Float)    # Ozone
    
    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    source = Column(String(50), default="AQICN")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Indexes for efficient querying
    __table_args__ = (
        Index('idx_location_timestamp', 'location', 'timestamp'),
        Index('idx_timestamp', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<AQIData(location='{self.location}', aqi={self.aqi}, timestamp='{self.timestamp}')>"


class WeatherData(Base):
    """
    Weather measurements
    Stores temperature, humidity, wind, and other weather conditions
    """
    __tablename__ = "weather_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    location = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Weather metrics
    temperature = Column(Float)  # Celsius
    feels_like = Column(Float)   # Apparent temperature
    humidity = Column(Float)     # Percentage
    pressure = Column(Float)     # hPa
    wind_speed = Column(Float)   # m/s
    wind_direction = Column(Float)  # Degrees
    clouds = Column(Float)       # Cloud coverage percentage
    visibility = Column(Float)   # Meters
    
    # Conditions
    weather_main = Column(String(50))  # Clear, Clouds, Rain, etc.
    weather_description = Column(String(100))
    
    # Metadata
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    source = Column(String(50), default="OpenWeather")
    created_at = Column(DateTime, default=datetime.utcnow)
    
    __table_args__ = (
        Index('idx_weather_location_timestamp', 'location', 'timestamp'),
    )
    
    def __repr__(self):
        return f"<WeatherData(location='{self.location}', temp={self.temperature}, timestamp='{self.timestamp}')>"


class TrafficData(Base):
    """
    Traffic measurements
    Stores traffic congestion levels and vehicle counts
    """
    __tablename__ = "traffic_data"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    location = Column(String(100), nullable=False, index=True)
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)
    
    # Traffic metrics
    congestion_level = Column(String(20))  # low, moderate, high, severe
    congestion_score = Column(Float)  # 0-100 scale
    average_speed = Column(Float)     # km/h
    vehicle_count = Column(Integer)
    
    # Metadata
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
    Correlation analysis results from Spark jobs
    Stores insights about relationships between AQI, traffic, and weather
    """
    __tablename__ = "correlation_analysis"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    location = Column(String(100), nullable=False, index=True)
    
    # Analysis period
    start_time = Column(DateTime, nullable=False)
    end_time = Column(DateTime, nullable=False)
    
    # Correlation coefficients
    aqi_traffic_correlation = Column(Float)
    aqi_temperature_correlation = Column(Float)
    aqi_humidity_correlation = Column(Float)
    aqi_wind_correlation = Column(Float)
    
    # Statistical metrics
    avg_aqi = Column(Float)
    max_aqi = Column(Float)
    min_aqi = Column(Float)
    avg_traffic_score = Column(Float)
    
    # Insights
    peak_pollution_hour = Column(Integer)  # Hour of day (0-23)
    peak_traffic_hour = Column(Integer)
    insight_summary = Column(Text)
    
    # Metadata
    analysis_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    job_id = Column(String(100))
    
    __table_args__ = (
        Index('idx_correlation_location_time', 'location', 'analysis_timestamp'),
    )
    
    def __repr__(self):
        return f"<CorrelationAnalysis(location='{self.location}', aqi_traffic_corr={self.aqi_traffic_correlation})>"


class AIAgentQuery(Base):
    """
    AI Agent query history
    Stores user questions and AI-generated insights
    """
    __tablename__ = "ai_agent_queries"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    
    # Query details
    user_query = Column(Text, nullable=False)
    agent_response = Column(Text, nullable=False)
    
    # Context
    location = Column(String(100))
    query_timestamp = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    
    # Metadata
    response_time_ms = Column(Integer)  # Response generation time
    tokens_used = Column(Integer)
    model_used = Column(String(50))
    
    def __repr__(self):
        return f"<AIAgentQuery(id={self.id}, query='{self.user_query[:50]}...')>"


# Database initialization script
if __name__ == "__main__":
    from .db_connection import init_db, test_connection
    
    print("🔧 Initializing database schema...")
    
    if test_connection():
        init_db()
        print("✅ All tables created successfully!")
        print("\nTables created:")
        print("  - aqi_data")
        print("  - weather_data")
        print("  - traffic_data")
        print("  - correlation_analysis")
        print("  - ai_agent_queries")
    else:
        print("❌ Failed to connect to database. Please check your configuration.")