"""
Streamlit Dashboard for Urban Air Quality & Traffic Insights
Interactive visualization dashboard with AI-powered chatbot
"""

import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Any

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from dotenv import load_dotenv
import requests

# Add project root to sys.path so 'src' package can be imported when running as a script
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Add parent directory to path for imports
parent_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if parent_dir not in sys.path:
    sys.path.insert(0, parent_dir)

from src.database.db_connection import get_db_session
from src.database.models import AQIData, WeatherData, TrafficData, CorrelationAnalysis
from src.ai_agent.utils import get_aqi_health_category, get_aqi_color

# Load environment variables
load_dotenv()

# Page configuration
st.set_page_config(
    page_title="Urban Air Quality Dashboard",
    page_icon="🌍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# API endpoint configuration
API_BASE_URL = os.getenv("FASTAPI_HOST", "http://localhost:8000")

# Custom CSS
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 10px;
        border-radius: 5px;
    }
    .good-aqi {
        background-color: #00e400;
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .moderate-aqi {
        background-color: #ffff00;
        color: black;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .unhealthy-sensitive-aqi {
        background-color: #ff7e00;
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .unhealthy-aqi {
        background-color: #ff0000;
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .very-unhealthy-aqi {
        background-color: #8f3f97;
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    .hazardous-aqi {
        background-color: #7e0023;
        color: white;
        padding: 10px;
        border-radius: 5px;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)


# Helper Functions
@st.cache_data(ttl=300)  # Cache for 5 minutes
def fetch_locations() -> List[str]:
    """Fetch available locations from database"""
    try:
        with get_db_session() as session:
            locations = session.query(AQIData.location).distinct().all()
            return [loc[0] for loc in locations]
    except Exception as e:
        st.error(f"Error fetching locations: {e}")
        return ["Koramangala", "Indiranagar", "Whitefield", "BTM Layout", "Electronic City"]


@st.cache_data(ttl=300)
def fetch_latest_aqi_data(location: str = None):
    """Fetch latest AQI data"""
    try:
        with get_db_session() as session:
            query = session.query(AQIData).order_by(AQIData.timestamp.desc())
            if location:
                query = query.filter(AQIData.location == location)
            results = query.limit(50).all()
            
            data = []
            for r in results:
                data.append({
                    "location": r.location,
                    "aqi": r.aqi,
                    "pm25": r.pm25,
                    "pm10": r.pm10,
                    "timestamp": r.timestamp,
                    "latitude": r.latitude,
                    "longitude": r.longitude
                })
            return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error fetching AQI data: {e}")
        return pd.DataFrame()


@st.cache_data(ttl=300)
def fetch_time_series_data(location: str, hours: int = 24):
    """Fetch time series data for a location"""
    try:
        with get_db_session() as session:
            time_filter = datetime.utcnow() - timedelta(hours=hours)
            
            # AQI data
            aqi_data = session.query(AQIData).filter(
                AQIData.location == location,
                AQIData.timestamp >= time_filter
            ).order_by(AQIData.timestamp).all()
            
            # Weather data
            weather_data = session.query(WeatherData).filter(
                WeatherData.location == location,
                WeatherData.timestamp >= time_filter
            ).order_by(WeatherData.timestamp).all()
            
            # Traffic data
            traffic_data = session.query(TrafficData).filter(
                TrafficData.location == location,
                TrafficData.timestamp >= time_filter
            ).order_by(TrafficData.timestamp).all()
            
            return {
                "aqi": pd.DataFrame([{
                    "timestamp": r.timestamp,
                    "aqi": r.aqi,
                    "pm25": r.pm25,
                    "pm10": r.pm10
                } for r in aqi_data]),
                "weather": pd.DataFrame([{
                    "timestamp": r.timestamp,
                    "temperature": r.temperature,
                    "humidity": r.humidity,
                    "wind_speed": r.wind_speed
                } for r in weather_data]),
                "traffic": pd.DataFrame([{
                    "timestamp": r.timestamp,
                    "congestion_score": r.congestion_score,
                    "average_speed": r.average_speed
                } for r in traffic_data])
            }
    except Exception as e:
        st.error(f"Error fetching time series data: {e}")
        return {"aqi": pd.DataFrame(), "weather": pd.DataFrame(), "traffic": pd.DataFrame()}


@st.cache_data(ttl=300)
def fetch_correlation_data(location: str = None):
    """Fetch correlation analysis data"""
    try:
        with get_db_session() as session:
            query = session.query(CorrelationAnalysis).order_by(
                CorrelationAnalysis.analysis_timestamp.desc()
            )
            if location:
                query = query.filter(CorrelationAnalysis.location == location)
            
            results = query.limit(10).all()
            
            data = []
            for r in results:
                data.append({
                    "location": r.location,
                    "aqi_traffic_correlation": r.aqi_traffic_correlation,
                    "aqi_temperature_correlation": r.aqi_temperature_correlation,
                    "avg_aqi": r.avg_aqi,
                    "max_aqi": r.max_aqi,
                    "peak_pollution_hour": r.peak_pollution_hour,
                    "peak_traffic_hour": r.peak_traffic_hour,
                    "insight_summary": r.insight_summary,
                    "analysis_timestamp": r.analysis_timestamp
                })
            return pd.DataFrame(data)
    except Exception as e:
        st.error(f"Error fetching correlation data: {e}")
        return pd.DataFrame()


def get_aqi_color_hex(aqi: int) -> str:
    """Get hex color for AQI value"""
    if aqi <= 50:
        return "#00e400"
    elif aqi <= 100:
        return "#ffff00"
    elif aqi <= 150:
        return "#ff7e00"
    elif aqi <= 200:
        return "#ff0000"
    elif aqi <= 300:
        return "#8f3f97"
    else:
        return "#7e0023"


def create_aqi_gauge(aqi: int, location: str):
    """Create AQI gauge chart"""
    fig = go.Figure(go.Indicator(
        mode="gauge+number+delta",
        value=aqi,
        domain={'x': [0, 1], 'y': [0, 1]},
        title={'text': f"AQI - {location}", 'font': {'size': 20}},
        delta={'reference': 100},
        gauge={
            'axis': {'range': [None, 300], 'tickwidth': 1, 'tickcolor': "darkblue"},
            'bar': {'color': get_aqi_color_hex(aqi)},
            'bgcolor': "white",
            'borderwidth': 2,
            'bordercolor': "gray",
            'steps': [
                {'range': [0, 50], 'color': '#d4edda'},
                {'range': [50, 100], 'color': '#fff3cd'},
                {'range': [100, 150], 'color': '#ffd7b5'},
                {'range': [150, 200], 'color': '#f8d7da'},
                {'range': [200, 300], 'color': '#d6c5d8'}
            ],
            'threshold': {
                'line': {'color': "red", 'width': 4},
                'thickness': 0.75,
                'value': 150
            }
        }
    ))
    
    fig.update_layout(height=300, margin=dict(l=20, r=20, t=50, b=20))
    return fig


def create_time_series_chart(df: pd.DataFrame, y_column: str, title: str, color: str):
    """Create time series line chart"""
    fig = px.line(
        df,
        x="timestamp",
        y=y_column,
        title=title,
        labels={"timestamp": "Time", y_column: title}
    )
    fig.update_traces(line_color=color, line_width=2)
    fig.update_layout(
        height=300,
        margin=dict(l=20, r=20, t=40, b=20),
        hovermode='x unified'
    )
    return fig


def create_correlation_heatmap(df: pd.DataFrame):
    """Create correlation heatmap"""
    if df.empty:
        return None
    
    # Prepare data for heatmap
    locations = df['location'].unique()
    correlations = []
    
    for loc in locations:
        loc_data = df[df['location'] == loc].iloc[0]
        correlations.append({
            'Location': loc,
            'Traffic': loc_data.get('aqi_traffic_correlation', 0),
            'Temperature': loc_data.get('aqi_temperature_correlation', 0)
        })
    
    corr_df = pd.DataFrame(correlations).set_index('Location')
    
    fig = px.imshow(
        corr_df,
        labels=dict(x="Factor", y="Location", color="Correlation"),
        x=corr_df.columns,
        y=corr_df.index,
        color_continuous_scale="RdYlGn",
        aspect="auto",
        title="AQI Correlations by Location"
    )
    fig.update_layout(height=400, margin=dict(l=20, r=20, t=40, b=20))
    return fig


def create_map(df: pd.DataFrame):
    """Create interactive map with AQI markers"""
    if df.empty:
        return None
    
    # Get latest data for each location
    latest_df = df.groupby('location').first().reset_index()
    
    fig = px.scatter_mapbox(
        latest_df,
        lat="latitude",
        lon="longitude",
        color="aqi",
        size="aqi",
        hover_name="location",
        hover_data={"aqi": True, "pm25": True, "latitude": False, "longitude": False},
        color_continuous_scale=[
            [0, "#00e400"],
            [0.2, "#ffff00"],
            [0.4, "#ff7e00"],
            [0.6, "#ff0000"],
            [0.8, "#8f3f97"],
            [1, "#7e0023"]
        ],
        zoom=11,
        height=500,
        title="Real-time AQI Map"
    )
    
    fig.update_layout(
        mapbox_style="open-street-map",
        margin=dict(l=0, r=0, t=40, b=0)
    )
    
    return fig


# Main Dashboard
def main():
    # Header
    st.title("🌍 Urban Air Quality & Traffic Insight Dashboard")
    st.markdown("Real-time air quality monitoring with AI-powered insights for Bangalore")
    
    # Sidebar
    st.sidebar.header("⚙️ Settings")
    
    # Location selector
    locations = fetch_locations()
    selected_location = st.sidebar.selectbox(
        "📍 Select Location",
        options=["All Locations"] + locations
    )
    
    # Time range selector
    time_range = st.sidebar.selectbox(
        "🕐 Time Range",
        options=["Last 6 Hours", "Last 12 Hours", "Last 24 Hours", "Last 3 Days", "Last Week"],
        index=2
    )
    
    hours_map = {
        "Last 6 Hours": 6,
        "Last 12 Hours": 12,
        "Last 24 Hours": 24,
        "Last 3 Days": 72,
        "Last Week": 168
    }
    hours = hours_map[time_range]
    
    # Refresh button
    if st.sidebar.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    # Auto-refresh toggle
    auto_refresh = st.sidebar.checkbox("🔁 Auto-refresh (5 min)", value=False)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 📊 Data Sources")
    st.sidebar.markdown("- **AQI**: AQICN / Mock")
    st.sidebar.markdown("- **Weather**: OpenWeather / Mock")
    st.sidebar.markdown("- **Traffic**: Mock Data")
    
    # Main content
    tabs = st.tabs(["📊 Overview", "📈 Time Series", "🔗 Correlations", "🗺️ Map View", "🤖 AI Assistant"])
    
    # Tab 1: Overview
    with tabs[0]:
        st.header("Current Air Quality Overview")
        
        # Fetch latest data
        location_filter = None if selected_location == "All Locations" else selected_location
        aqi_df = fetch_latest_aqi_data(location_filter)
        
        if not aqi_df.empty:
            # Display metrics
            if selected_location == "All Locations":
                # Show all locations
                cols = st.columns(len(locations))
                for idx, loc in enumerate(locations):
                    loc_data = aqi_df[aqi_df['location'] == loc]
                    if not loc_data.empty:
                        latest = loc_data.iloc[0]
                        with cols[idx]:
                            aqi_val = int(latest['aqi'])
                            category = get_aqi_health_category(aqi_val)
                            st.metric(
                                label=loc,
                                value=f"AQI {aqi_val}",
                                delta=category
                            )
                            st.markdown(f"PM2.5: {latest['pm25']:.1f} µg/m³")
            else:
                # Show selected location details
                latest = aqi_df.iloc[0]
                aqi_val = int(latest['aqi'])
                category = get_aqi_health_category(aqi_val)
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    st.metric("Current AQI", aqi_val)
                with col2:
                    st.metric("Health Category", category)
                with col3:
                    st.metric("PM2.5", f"{latest['pm25']:.1f} µg/m³")
                with col4:
                    st.metric("PM10", f"{latest['pm10']:.1f} µg/m³")
                
                # AQI Gauge
                st.plotly_chart(
                    create_aqi_gauge(aqi_val, selected_location),
                    use_container_width=True
                )
                
                # Health recommendations
                st.subheader("🏥 Health Recommendations")
                if aqi_val <= 50:
                    st.success("✅ Air quality is excellent. Perfect for all outdoor activities!")
                elif aqi_val <= 100:
                    st.info("ℹ️ Air quality is acceptable. Sensitive individuals should take precautions.")
                elif aqi_val <= 150:
                    st.warning("⚠️ Unhealthy for sensitive groups. Reduce prolonged outdoor exertion.")
                elif aqi_val <= 200:
                    st.error("❌ Unhealthy air quality. Everyone should avoid prolonged outdoor activities.")
                else:
                    st.error("🚨 Very unhealthy or hazardous. Stay indoors and use air purifiers.")
        else:
            st.warning("No data available for the selected location.")
    
    # Tab 2: Time Series
    with tabs[1]:
        st.header("📈 Time Series Analysis")
        
        if selected_location != "All Locations":
            time_data = fetch_time_series_data(selected_location, hours)
            
            if not time_data["aqi"].empty:
                # AQI over time
                st.plotly_chart(
                    create_time_series_chart(
                        time_data["aqi"],
                        "aqi",
                        f"AQI Trend - {selected_location}",
                        "#ff6b6b"
                    ),
                    use_container_width=True
                )
                
                col1, col2 = st.columns(2)
                
                with col1:
                    # PM2.5 over time
                    st.plotly_chart(
                        create_time_series_chart(
                            time_data["aqi"],
                            "pm25",
                            "PM2.5 Levels",
                            "#4ecdc4"
                        ),
                        use_container_width=True
                    )
                
                with col2:
                    # PM10 over time
                    st.plotly_chart(
                        create_time_series_chart(
                            time_data["aqi"],
                            "pm10",
                            "PM10 Levels",
                            "#95e1d3"
                        ),
                        use_container_width=True
                    )
                
                # Weather correlation
                if not time_data["weather"].empty:
                    st.subheader("🌤️ Weather Factors")
                    
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.plotly_chart(
                            create_time_series_chart(
                                time_data["weather"],
                                "temperature",
                                "Temperature (°C)",
                                "#ffa726"
                            ),
                            use_container_width=True
                        )
                    
                    with col2:
                        st.plotly_chart(
                            create_time_series_chart(
                                time_data["weather"],
                                "wind_speed",
                                "Wind Speed (m/s)",
                                "#42a5f5"
                            ),
                            use_container_width=True
                        )
                
                # Traffic data
                if not time_data["traffic"].empty:
                    st.subheader("🚗 Traffic Congestion")
                    st.plotly_chart(
                        create_time_series_chart(
                            time_data["traffic"],
                            "congestion_score",
                            "Traffic Congestion Score",
                            "#ef5350"
                        ),
                        use_container_width=True
                    )
            else:
                st.warning(f"No time series data available for {selected_location}")
        else:
            st.info("Please select a specific location to view time series data")
    
    # Tab 3: Correlations
    with tabs[2]:
        st.header("🔗 Correlation Analysis")
        
        location_filter = None if selected_location == "All Locations" else selected_location
        corr_df = fetch_correlation_data(location_filter)
        
        if not corr_df.empty:
            # Correlation heatmap
            heatmap = create_correlation_heatmap(corr_df)
            if heatmap:
                st.plotly_chart(heatmap, use_container_width=True)
            
            # Insights table
            st.subheader("💡 Key Insights")
            for _, row in corr_df.iterrows():
                with st.expander(f"📍 {row['location']} - Analysis from {row['analysis_timestamp'].strftime('%Y-%m-%d %H:%M')}"):
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("AQI-Traffic Correlation", f"{row['aqi_traffic_correlation']:.3f}")
                        st.metric("Avg AQI", f"{row['avg_aqi']:.1f}")
                    
                    with col2:
                        st.metric("AQI-Temperature Correlation", f"{row['aqi_temperature_correlation']:.3f}")
                        st.metric("Max AQI", f"{row['max_aqi']}")
                    
                    with col3:
                        st.metric("Peak Pollution Hour", f"{row['peak_pollution_hour']}:00")
                        st.metric("Peak Traffic Hour", f"{row['peak_traffic_hour']}:00")
                    
                    st.markdown("**Insight Summary:**")
                    st.info(row['insight_summary'])
        else:
            st.warning("No correlation analysis data available yet. Spark jobs may not have run.")
    
    # Tab 4: Map View
    with tabs[3]:
        st.header("🗺️ Interactive AQI Map")
        
        aqi_df = fetch_latest_aqi_data(None)  # Get all locations
        
        if not aqi_df.empty:
            map_fig = create_map(aqi_df)
            if map_fig:
                st.plotly_chart(map_fig, use_container_width=True)
            
            # Location comparison table
            st.subheader("📋 Location Comparison")
            comparison_df = aqi_df.groupby('location').first()[['aqi', 'pm25', 'pm10']].reset_index()
            comparison_df['Health Category'] = comparison_df['aqi'].apply(get_aqi_health_category)
            comparison_df = comparison_df.sort_values('aqi', ascending=False)
            
            st.dataframe(
                comparison_df.style.background_gradient(subset=['aqi'], cmap='RdYlGn_r'),
                use_container_width=True
            )
        else:
            st.warning("No location data available for mapping.")
    
    # Tab 5: AI Assistant
    with tabs[4]:
        st.header("🤖 AI-Powered Insights Assistant")
        st.markdown("Ask questions about air quality, pollution patterns, and health recommendations.")
        
        # Sample questions
        with st.expander("💡 Sample Questions"):
            st.markdown("""
            - Why is AQI high today in Koramangala?
            - What is the pollution trend this week?
            - Is traffic causing pollution in Indiranagar?
            - What time of day has the worst air quality?
            - Should I go for a run right now?
            - Compare air quality across all locations
            """)
        
        # Chat interface
        user_query = st.text_input(
            "Ask a question:",
            placeholder="e.g., Why is AQI high today in Koramangala?"
        )
        
        if st.button("🔍 Get AI Insight"):
            if user_query:
                with st.spinner("🤔 AI is analyzing data..."):
                    try:
                        # Call AI agent API
                        response = requests.post(
                            f"{API_BASE_URL}/insights-ai-agent",
                            json={
                                "query": user_query,
                                "location": selected_location if selected_location != "All Locations" else None
                            },
                            timeout=30
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            st.success("✅ AI Response:")
                            st.markdown(result["response"])
                            st.caption(f"Response time: {result['response_time_ms']}ms")
                        else:
                            st.error(f"Error: {response.status_code} - {response.text}")
                    
                    except requests.exceptions.ConnectionError:
                        st.error("❌ Cannot connect to AI Agent API. Please ensure FastAPI server is running.")
                    except Exception as e:
                        st.error(f"❌ Error: {str(e)}")
            else:
                st.warning("Please enter a question")
        
        # Query history
        st.subheader("📜 Recent Queries")
        try:
            history_response = requests.get(
                f"{API_BASE_URL}/insights/history",
                params={"limit": 5},
                timeout=10
            )
            
            if history_response.status_code == 200:
                history = history_response.json()
                for item in history.get("data", []):
                    with st.expander(f"❓ {item['query'][:80]}..."):
                        st.markdown(f"**Response:** {item['response']}")
                        st.caption(f"📍 {item['location'] or 'All locations'} | ⏱️ {item['timestamp']}")
        except:
            st.info("Query history unavailable")
    
    # Footer
    st.markdown("---")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("🌍 **Urban Air Quality Dashboard**")
    with col2:
        st.markdown(f"🕐 Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    with col3:
        st.markdown("💚 Built with Streamlit")
    
    # Auto-refresh functionality
    if auto_refresh:
        import time
        time.sleep(300)  # 5 minutes
        st.rerun()


if __name__ == "__main__":
    main()