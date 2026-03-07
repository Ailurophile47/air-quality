"""
Urban Air Quality Intelligence Platform — Phase 5 Dashboard.
Shows AQI trends, weather/traffic, predictions, anomalies, and correlations.
"""
import os
import requests
import streamlit as st
import pandas as pd

API_BASE = os.getenv("API_BASE", "http://localhost:8000")
CITY = os.getenv("CITY", "Bangalore")

st.set_page_config(
    page_title="Urban Air Quality Intelligence",
    page_icon="🌫️",
    layout="wide",
)

st.title("🌫️ Urban Air Quality Intelligence — Bengaluru")
st.caption(f"Data for {CITY} | API: {API_BASE}")


def fetch(path: str, params: dict | None = None):
    url = f"{API_BASE}{path}"
    try:
        r = requests.get(url, params=params or {}, timeout=10)
        r.raise_for_status()
        return r.json()
    except Exception as e:
        st.error(f"API error: {e}")
        return None


# Sidebar
st.sidebar.header("Filters")
city = st.sidebar.text_input("City", value=CITY)
limit_hourly = st.sidebar.slider("Hourly points", 24, 168, 72)
limit_daily = st.sidebar.slider("Daily points", 7, 30, 14)

# --- Latest AQI & Predictions ---
st.header("Current AQI & Predictions")
col1, col2, col3 = st.columns(3)

latest = fetch("/aqi/latest", {"city": city})
if latest:
    col1.metric("Latest AQI", latest.get("aqi_value", "—"), help="Most recent measurement")
    col2.metric("PM2.5", latest.get("pm2_5") or "—", help="µg/m³")
    col3.metric("Dominant", latest.get("dominant_pollutant") or "—", help="Dominant pollutant")

preds = fetch("/dashboard/predictions", {"city": city, "limit": 6})
if preds and isinstance(preds, list) and len(preds) > 0:
    next_p = preds[0]
    st.success(f"**Next 3h predicted AQI:** {next_p.get('predicted_aqi', '—')} (at {next_p.get('predicted_at', '')})")
else:
    st.info("No predictions yet. Run the pipeline (ingestion → aggregation → ML train → predict).")

# --- AQI trend (hourly) ---
st.header("AQI Trend (Hourly)")
hourly = fetch("/dashboard/hourly", {"city": city, "limit": limit_hourly})
if hourly and isinstance(hourly, list) and len(hourly) > 0:
    df_h = pd.DataFrame(hourly)
    df_h["hour_bucket"] = pd.to_datetime(df_h["hour_bucket"])
    df_h = df_h.sort_values("hour_bucket")
    st.line_chart(df_h.set_index("hour_bucket")[["avg_aqi"]])
else:
    st.warning("No hourly data. Ensure aggregation has run.")

# --- Daily & 7-day rolling ---
st.header("Daily AQI & 7-Day Rolling Average")
daily = fetch("/dashboard/daily", {"city": city, "limit": limit_daily})
if daily and isinstance(daily, list) and len(daily) > 0:
    df_d = pd.DataFrame(daily)
    df_d["date_bucket"] = pd.to_datetime(df_d["date_bucket"])
    df_d = df_d.sort_values("date_bucket")
    st.line_chart(
        df_d.set_index("date_bucket")[["avg_aqi", "rolling_7d_avg_aqi"]].rename(
            columns={"avg_aqi": "Daily avg AQI", "rolling_7d_avg_aqi": "7-day rolling"}
        )
    )
else:
    st.warning("No daily aggregates yet.")

# --- Anomalies ---
st.header("Anomaly Events (AQI ≥ 300)")
anomalies = fetch("/dashboard/anomalies", {"city": city, "limit": 20})
if anomalies and isinstance(anomalies, list) and len(anomalies) > 0:
    df_a = pd.DataFrame(anomalies)
    df_a["recorded_at"] = pd.to_datetime(df_a["recorded_at"])
    st.dataframe(df_a[["recorded_at", "aqi_value", "event_type"]], use_container_width=True)
else:
    st.info("No anomaly events in the current window.")

# --- Correlation ---
st.header("Correlation Metrics")
corr = fetch("/dashboard/correlation", {"city": city})
if corr and isinstance(corr, dict) and "traffic_aqi_correlation" in corr:
    c1, c2, c3 = st.columns(3)
    c1.metric("Traffic vs AQI", f"{corr.get('traffic_aqi_correlation') or 0:.3f}", help="Pearson correlation")
    c2.metric("Temp vs AQI", f"{corr.get('weather_aqi_correlation_temp') or 0:.3f}", help="Pearson correlation")
    c3.metric("Humidity vs AQI", f"{corr.get('weather_aqi_correlation_humidity') or 0:.3f}", help="Pearson correlation")
    if corr.get("sample_count"):
        st.caption(f"Based on {corr['sample_count']} aligned samples.")
else:
    st.info("Correlation not computed yet (need aligned AQI + weather + traffic).")

st.sidebar.markdown("---")
st.sidebar.markdown("**Phase 5** — ML predictions & dashboard")
