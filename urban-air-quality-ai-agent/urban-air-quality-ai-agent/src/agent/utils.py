"""
Utility functions for AI Agent
Helper functions for data formatting and processing
"""

from typing import Dict, Any, Optional
from datetime import datetime


def format_aqi_data(record: Any) -> Dict[str, Any]:
    """
    Format AQI database record for LLM context
    
    Args:
        record: AQIData SQLAlchemy object
        
    Returns:
        Formatted dictionary
    """
    return {
        "location": record.location,
        "aqi": record.aqi,
        "pm25": round(record.pm25, 2) if record.pm25 else None,
        "pm10": round(record.pm10, 2) if record.pm10 else None,
        "no2": round(record.no2, 2) if record.no2 else None,
        "so2": round(record.so2, 2) if record.so2 else None,
        "co": round(record.co, 2) if record.co else None,
        "o3": round(record.o3, 2) if record.o3 else None,
        "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M"),
        "source": record.source
    }


def format_weather_data(record: Any) -> Dict[str, Any]:
    """
    Format weather database record for LLM context
    
    Args:
        record: WeatherData SQLAlchemy object
        
    Returns:
        Formatted dictionary
    """
    return {
        "location": record.location,
        "temperature": round(record.temperature, 1) if record.temperature else None,
        "feels_like": round(record.feels_like, 1) if record.feels_like else None,
        "humidity": round(record.humidity, 1) if record.humidity else None,
        "pressure": round(record.pressure, 1) if record.pressure else None,
        "wind_speed": round(record.wind_speed, 1) if record.wind_speed else None,
        "wind_direction": record.wind_direction,
        "clouds": record.clouds,
        "visibility": record.visibility,
        "weather_main": record.weather_main,
        "weather_description": record.weather_description,
        "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M")
    }


def format_traffic_data(record: Any) -> Dict[str, Any]:
    """
    Format traffic database record for LLM context
    
    Args:
        record: TrafficData SQLAlchemy object
        
    Returns:
        Formatted dictionary
    """
    return {
        "location": record.location,
        "congestion_level": record.congestion_level,
        "congestion_score": round(record.congestion_score, 1) if record.congestion_score else None,
        "average_speed": round(record.average_speed, 1) if record.average_speed else None,
        "vehicle_count": record.vehicle_count,
        "timestamp": record.timestamp.strftime("%Y-%m-%d %H:%M")
    }


def format_correlation_data(record: Any) -> Dict[str, Any]:
    """
    Format correlation analysis record for LLM context
    
    Args:
        record: CorrelationAnalysis SQLAlchemy object
        
    Returns:
        Formatted dictionary
    """
    return {
        "location": record.location,
        "aqi_traffic_correlation": round(record.aqi_traffic_correlation, 3) if record.aqi_traffic_correlation else None,
        "aqi_temperature_correlation": round(record.aqi_temperature_correlation, 3) if record.aqi_temperature_correlation else None,
        "aqi_humidity_correlation": round(record.aqi_humidity_correlation, 3) if record.aqi_humidity_correlation else None,
        "aqi_wind_correlation": round(record.aqi_wind_correlation, 3) if record.aqi_wind_correlation else None,
        "avg_aqi": round(record.avg_aqi, 1) if record.avg_aqi else None,
        "max_aqi": record.max_aqi,
        "min_aqi": record.min_aqi,
        "avg_traffic_score": round(record.avg_traffic_score, 1) if record.avg_traffic_score else None,
        "peak_pollution_hour": record.peak_pollution_hour,
        "peak_traffic_hour": record.peak_traffic_hour,
        "insight_summary": record.insight_summary,
        "analysis_timestamp": record.analysis_timestamp.strftime("%Y-%m-%d %H:%M")
    }


def get_aqi_health_category(aqi: int) -> str:
    """
    Get health category for AQI value
    
    Args:
        aqi: AQI value
        
    Returns:
        Health category string
    """
    if aqi <= 50:
        return "Good"
    elif aqi <= 100:
        return "Moderate"
    elif aqi <= 150:
        return "Unhealthy for Sensitive Groups"
    elif aqi <= 200:
        return "Unhealthy"
    elif aqi <= 300:
        return "Very Unhealthy"
    else:
        return "Hazardous"


def get_aqi_color(aqi: int) -> str:
    """
    Get color code for AQI value
    
    Args:
        aqi: AQI value
        
    Returns:
        Color name or hex code
    """
    if aqi <= 50:
        return "green"
    elif aqi <= 100:
        return "yellow"
    elif aqi <= 150:
        return "orange"
    elif aqi <= 200:
        return "red"
    elif aqi <= 300:
        return "purple"
    else:
        return "maroon"


def get_health_recommendation(aqi: int) -> Dict[str, str]:
    """
    Get detailed health recommendation for AQI level
    
    Args:
        aqi: AQI value
        
    Returns:
        Dictionary with recommendation details
    """
    if aqi <= 50:
        return {
            "category": "Good",
            "message": "Air quality is good. Perfect for outdoor activities.",
            "sensitive_groups": "No precautions needed.",
            "general_population": "Enjoy outdoor activities.",
            "color": "green"
        }
    elif aqi <= 100:
        return {
            "category": "Moderate",
            "message": "Air quality is acceptable for most people.",
            "sensitive_groups": "Unusually sensitive people should limit prolonged outdoor exertion.",
            "general_population": "Can enjoy normal outdoor activities.",
            "color": "yellow"
        }
    elif aqi <= 150:
        return {
            "category": "Unhealthy for Sensitive Groups",
            "message": "Sensitive groups may experience health effects.",
            "sensitive_groups": "Reduce prolonged or heavy outdoor exertion. Consider indoor activities.",
            "general_population": "Can continue normal outdoor activities.",
            "color": "orange"
        }
    elif aqi <= 200:
        return {
            "category": "Unhealthy",
            "message": "Everyone may experience health effects.",
            "sensitive_groups": "Avoid prolonged outdoor activities completely.",
            "general_population": "Reduce prolonged outdoor exertion. Wear masks if going outside.",
            "color": "red"
        }
    elif aqi <= 300:
        return {
            "category": "Very Unhealthy",
            "message": "Health alert: serious health effects for everyone.",
            "sensitive_groups": "Remain indoors and keep activity levels low.",
            "general_population": "Avoid all outdoor activities. Stay indoors with air purifiers.",
            "color": "purple"
        }
    else:
        return {
            "category": "Hazardous",
            "message": "Health emergency: everyone is at risk.",
            "sensitive_groups": "Stay indoors. Avoid all physical activity.",
            "general_population": "Remain indoors. Avoid all outdoor exposure. Use air purifiers.",
            "color": "maroon"
        }


def calculate_trend(values: list) -> str:
    """
    Calculate trend direction from list of values
    
    Args:
        values: List of numeric values (chronological order)
        
    Returns:
        Trend description: "increasing", "decreasing", or "stable"
    """
    if len(values) < 2:
        return "insufficient_data"
    
    # Simple linear trend
    increases = 0
    decreases = 0
    
    for i in range(1, len(values)):
        if values[i] > values[i-1]:
            increases += 1
        elif values[i] < values[i-1]:
            decreases += 1
    
    if increases > decreases * 1.5:
        return "increasing"
    elif decreases > increases * 1.5:
        return "decreasing"
    else:
        return "stable"


def format_time_period(hours: int) -> str:
    """
    Format hours into human-readable time period
    
    Args:
        hours: Number of hours
        
    Returns:
        Formatted string
    """
    if hours < 24:
        return f"past {hours} hours"
    elif hours == 24:
        return "past 24 hours"
    elif hours < 168:
        days = hours // 24
        return f"past {days} days"
    else:
        weeks = hours // 168
        return f"past {weeks} weeks"


def interpret_correlation(correlation: float) -> str:
    """
    Interpret correlation coefficient strength
    
    Args:
        correlation: Correlation coefficient (-1 to 1)
        
    Returns:
        Interpretation string
    """
    abs_corr = abs(correlation)
    direction = "positive" if correlation > 0 else "negative"
    
    if abs_corr >= 0.7:
        strength = "strong"
    elif abs_corr >= 0.4:
        strength = "moderate"
    elif abs_corr >= 0.2:
        strength = "weak"
    else:
        strength = "negligible"
    
    return f"{strength} {direction}"


# Test utilities
if __name__ == "__main__":
    print("Testing utility functions...")
    
    # Test AQI categories
    test_aqis = [25, 75, 125, 175, 250, 350]
    for aqi in test_aqis:
        category = get_aqi_health_category(aqi)
        color = get_aqi_color(aqi)
        recommendation = get_health_recommendation(aqi)
        print(f"\nAQI {aqi}: {category} ({color})")
        print(f"  Message: {recommendation['message']}")
    
    # Test trend calculation
    increasing = [10, 15, 20, 25, 30]
    decreasing = [30, 25, 20, 15, 10]
    stable = [20, 22, 19, 21, 20]
    
    print(f"\nTrend tests:")
    print(f"  {increasing} -> {calculate_trend(increasing)}")
    print(f"  {decreasing} -> {calculate_trend(decreasing)}")
    print(f"  {stable} -> {calculate_trend(stable)}")
    
    # Test correlation interpretation
    print(f"\nCorrelation tests:")
    print(f"  0.85 -> {interpret_correlation(0.85)}")
    print(f"  -0.60 -> {interpret_correlation(-0.60)}")
    print(f"  0.25 -> {interpret_correlation(0.25)}")
    
    print("\n✅ Utility tests complete!")