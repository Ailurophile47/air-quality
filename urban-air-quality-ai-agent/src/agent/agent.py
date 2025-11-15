"""
AI Agent for Urban Air Quality Insights
Uses LangChain + OpenAI to provide intelligent analysis of air quality data
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List

from dotenv import load_dotenv
from langchain.chat_models import ChatOpenAI
from langchain.prompts import ChatPromptTemplate
from langchain.schema import SystemMessage, HumanMessage

sys.path.append(os.path.dirname(os.path.dirname(__file__)))

from database.db_connection import get_db_session
from database.models import AQIData, WeatherData, TrafficData, CorrelationAnalysis
from ai_agent.utils import (
    format_aqi_data,
    format_weather_data,
    format_traffic_data,
    format_correlation_data,
    get_aqi_health_category
)

# Load environment variables
load_dotenv()


class AirQualityAgent:
    """
    AI Agent for analyzing air quality data and providing insights
    """
    
    def __init__(self):
        """Initialize the AI agent with OpenAI and database connection"""
        self.openai_api_key = os.getenv('OPENAI_API_KEY')
        
        if not self.openai_api_key or self.openai_api_key == 'your_openai_api_key_here':
            raise ValueError(
                "OpenAI API key not configured. Please set OPENAI_API_KEY in .env file"
            )
        
        # Initialize OpenAI chat model
        self.llm = ChatOpenAI(
            model="gpt-4",
            temperature=0.7,
            openai_api_key=self.openai_api_key
        )
        
        # Load system prompt
        self.system_prompt = self._load_system_prompt()
        
        print("✅ AI Agent initialized with GPT-4")
    
    def _load_system_prompt(self) -> str:
        """Load system prompt from template file"""
        prompt_file = os.path.join(
            os.path.dirname(__file__),
            'prompt_template.txt'
        )
        
        try:
            with open(prompt_file, 'r') as f:
                return f.read()
        except FileNotFoundError:
            # Fallback prompt if file doesn't exist
            return """You are an expert air quality analyst AI assistant specializing in urban environmental data.

Your role is to:
- Analyze air quality (AQI), weather, and traffic data
- Identify patterns and correlations
- Provide health recommendations based on pollution levels
- Explain complex environmental data in simple terms
- Offer actionable insights for citizens

Guidelines:
- Be concise and clear
- Use data to support your insights
- Provide specific health recommendations
- Explain causation when correlations are strong
- Mention time periods and locations explicitly
- Use metric units (°C, km/h, etc.)
"""
    
    def _fetch_context_data(self, location: Optional[str] = None, hours: int = 24) -> Dict[str, Any]:
        """
        Fetch relevant data from database for context
        
        Args:
            location: Specific location to filter (optional)
            hours: Hours of historical data to fetch
            
        Returns:
            Dictionary with formatted data
        """
        context = {
            "aqi_data": [],
            "weather_data": [],
            "traffic_data": [],
            "correlation_data": [],
            "locations": []
        }
        
        try:
            with get_db_session() as session:
                # Calculate time filter
                time_filter = datetime.utcnow() - timedelta(hours=hours)
                
                # Fetch AQI data
                aqi_query = session.query(AQIData).filter(
                    AQIData.timestamp >= time_filter
                ).order_by(AQIData.timestamp.desc())
                
                if location:
                    aqi_query = aqi_query.filter(AQIData.location == location)
                
                aqi_records = aqi_query.limit(50).all()
                context["aqi_data"] = [format_aqi_data(r) for r in aqi_records]
                
                # Fetch weather data
                weather_query = session.query(WeatherData).filter(
                    WeatherData.timestamp >= time_filter
                ).order_by(WeatherData.timestamp.desc())
                
                if location:
                    weather_query = weather_query.filter(WeatherData.location == location)
                
                weather_records = weather_query.limit(50).all()
                context["weather_data"] = [format_weather_data(r) for r in weather_records]
                
                # Fetch traffic data
                traffic_query = session.query(TrafficData).filter(
                    TrafficData.timestamp >= time_filter
                ).order_by(TrafficData.timestamp.desc())
                
                if location:
                    traffic_query = traffic_query.filter(TrafficData.location == location)
                
                traffic_records = traffic_query.limit(50).all()
                context["traffic_data"] = [format_traffic_data(r) for r in traffic_records]
                
                # Fetch correlation analysis
                corr_query = session.query(CorrelationAnalysis).order_by(
                    CorrelationAnalysis.analysis_timestamp.desc()
                )
                
                if location:
                    corr_query = corr_query.filter(CorrelationAnalysis.location == location)
                
                correlation_records = corr_query.limit(10).all()
                context["correlation_data"] = [format_correlation_data(r) for r in correlation_records]
                
                # Get unique locations
                if not location:
                    locations = session.query(AQIData.location).distinct().all()
                    context["locations"] = [loc[0] for loc in locations]
                else:
                    context["locations"] = [location]
                
        except Exception as e:
            print(f"⚠️  Error fetching context data: {e}")
        
        return context
    
    def _prepare_context_summary(self, context: Dict[str, Any]) -> str:
        """
        Prepare a summary of context data for the LLM
        
        Args:
            context: Context data dictionary
            
        Returns:
            Formatted context string
        """
        summary_parts = []
        
        # Current timestamp
        summary_parts.append(f"Current Time: {datetime.utcnow().strftime('%Y-%m-%d %H:%M UTC')}")
        summary_parts.append(f"Locations Available: {', '.join(context['locations'])}\n")
        
        # Latest AQI data
        if context["aqi_data"]:
            summary_parts.append("=== LATEST AIR QUALITY DATA ===")
            for data in context["aqi_data"][:5]:  # Top 5 most recent
                health_category = get_aqi_health_category(data["aqi"])
                summary_parts.append(
                    f"Location: {data['location']}, "
                    f"AQI: {data['aqi']} ({health_category}), "
                    f"PM2.5: {data['pm25']}, "
                    f"Time: {data['timestamp']}"
                )
            summary_parts.append("")
        
        # Latest weather data
        if context["weather_data"]:
            summary_parts.append("=== LATEST WEATHER DATA ===")
            for data in context["weather_data"][:5]:
                summary_parts.append(
                    f"Location: {data['location']}, "
                    f"Temp: {data['temperature']}°C, "
                    f"Humidity: {data['humidity']}%, "
                    f"Wind: {data['wind_speed']} m/s, "
                    f"Conditions: {data['weather_description']}"
                )
            summary_parts.append("")
        
        # Latest traffic data
        if context["traffic_data"]:
            summary_parts.append("=== LATEST TRAFFIC DATA ===")
            for data in context["traffic_data"][:5]:
                summary_parts.append(
                    f"Location: {data['location']}, "
                    f"Congestion: {data['congestion_level']} ({data['congestion_score']}/100), "
                    f"Avg Speed: {data['average_speed']} km/h"
                )
            summary_parts.append("")
        
        # Correlation analysis
        if context["correlation_data"]:
            summary_parts.append("=== CORRELATION ANALYSIS ===")
            for data in context["correlation_data"][:3]:
                summary_parts.append(
                    f"Location: {data['location']}\n"
                    f"  AQI-Traffic Correlation: {data['aqi_traffic_correlation']:.3f}\n"
                    f"  Average AQI: {data['avg_aqi']:.1f}\n"
                    f"  Peak Pollution Hour: {data['peak_pollution_hour']}:00\n"
                    f"  Insight: {data['insight_summary']}"
                )
            summary_parts.append("")
        
        return "\n".join(summary_parts)
    
    def get_insight(self, query: str, location: Optional[str] = None) -> str:
        """
        Get AI-powered insight for a user query
        
        Args:
            query: User's question about air quality
            location: Specific location (optional)
            
        Returns:
            AI-generated insight response
        """
        try:
            # Fetch context data
            print(f"🔍 Fetching data for query: {query}")
            context = self._fetch_context_data(location=location, hours=24)
            
            # Prepare context summary
            context_summary = self._prepare_context_summary(context)
            
            # Create messages for the LLM
            messages = [
                SystemMessage(content=self.system_prompt),
                HumanMessage(content=f"""
Context Data:
{context_summary}

User Query: {query}

Please provide a detailed, data-driven response to the user's query. Include:
1. Direct answer to their question
2. Supporting data points
3. Health recommendations if relevant
4. Actionable insights
5. Time periods and locations mentioned explicitly

Keep your response concise but informative (3-5 paragraphs maximum).
""")
            ]
            
            # Get response from LLM
            print("🤖 Generating AI response...")
            response = self.llm(messages)
            
            return response.content
            
        except Exception as e:
            error_msg = f"Error generating insight: {str(e)}"
            print(f"❌ {error_msg}")
            return f"I apologize, but I encountered an error while analyzing the data: {str(e)}. Please try again or rephrase your question."
    
    def get_summary(self, location: str, hours: int = 24) -> str:
        """
        Get automated summary for a location
        
        Args:
            location: Location name
            hours: Hours of data to summarize
            
        Returns:
            Summary text
        """
        query = f"Provide a comprehensive summary of air quality conditions in {location} over the last {hours} hours. Include trends, correlations with traffic/weather, and recommendations."
        return self.get_insight(query, location=location)


# Test the agent
if __name__ == "__main__":
    try:
        agent = AirQualityAgent()
        
        # Test queries
        test_queries = [
            "What is the current air quality in Koramangala?",
            "Is traffic causing pollution in Indiranagar?",
            "What time of day has the worst air quality?",
        ]
        
        print("\n🧪 Testing AI Agent with sample queries...\n")
        
        for query in test_queries:
            print(f"❓ Query: {query}")
            response = agent.get_insight(query)
            print(f"🤖 Response: {response}\n")
            print("-" * 80 + "\n")
            
    except Exception as e:
        print(f"❌ Error testing agent: {e}")