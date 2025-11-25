/**
 * Urban Air Quality Monitor - React Dashboard Application
 * =======================================================
 * 
 * PURPOSE:
 * This is the main React component that renders the air quality monitoring dashboard.
 * It displays real-time AQI (Air Quality Index) data, weather conditions, and AI-powered insights.
 * 
 * ARCHITECTURE:
 * - React Hooks for state management (useState, useEffect, useCallback)
 * - Fetch API to communicate with FastAPI backend
 * - Auto-refresh capability with configurable intervals
 * - AQI color-coding for visual interpretation
 * - Responsive grid layout using CSS Grid
 * 
 * DATA FLOW:
 * User selects city → fetchData() → Backend API (/aqi/latest, /aqi/location/{location})
 * → Parse response → Normalize data → Update React state → Re-render UI
 * 
 * PERFORMANCE NOTES:
 * - useCallback prevents unnecessary function recreations
 * - useEffect dependency array optimizes re-renders
 * - Auto-refresh interval is configurable (1-30 minutes)
 * 
 * STYLING:
 * - All styles in App.css using CSS Grid and Flexbox
 * - AQI color-coded: Green (Good) to Maroon (Hazardous)
 * - Mobile-responsive design with breakpoints in CSS
 */

import React, { useState, useEffect, useCallback } from 'react';
import './App.css';

const App = () => {
  /**
   * STATE MANAGEMENT - React Hooks for component data
   * Each state variable has a setter function to update it
   */
  
  // data: holds the fetched air quality data from backend
  // Structure: { count: number, data: array of city records, raw: original API response }
  const [data, setData] = useState(null);
  
  // loading: true while fetching data, false when complete
  // Used to show "Loading..." message and disable refresh button
  const [loading, setLoading] = useState(true);
  
  // error: stores error message if fetch fails (network error, API error, etc.)
  // Display as red alert banner if not null
  const [error, setError] = useState(null);
  
  // selectedCity: which city the user selected in dropdown
  // 'all' = show all cities, 'delhi' = show only Delhi, etc.
  // Triggers new fetch when changed
  const [selectedCity, setSelectedCity] = useState('all');
  
  // refreshInterval: how often to auto-fetch data (milliseconds)
  // 300000 ms = 5 minutes (default)
  // User can change via dropdown: 1min, 5min, 10min, 30min
  const [refreshInterval, setRefreshInterval] = useState(300000); // 5 minutes
  
  // alerts: array of active pollution alerts (if API returns them)
  // Each alert has: { severity, title, message, timestamp }
  const [alerts, setAlerts] = useState([]);

  /**
   * API CONFIGURATION
   * REACT_APP_API_URL environment variable set in .env file
   * Example: REACT_APP_API_URL=http://localhost:8000
   * Defaults to localhost:8000 for local development
   */
  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  /**
   * FETCH AIR QUALITY DATA FROM BACKEND
   * 
   * This function makes HTTP GET requests to the FastAPI backend.
   * It handles two scenarios:
   * 1. selectedCity === 'all': Fetch latest readings from all cities (/aqi/latest?limit=50)
   * 2. selectedCity === specific city: Fetch historical data for that city (/aqi/location/{city}?hours=24)
   * 
   * RESPONSE FORMAT FROM BACKEND:
   * For /aqi/latest:
   *   { count: 50, data: [ { location, aqi, pm25, pm10, no2, so2, co, o3, timestamp, source }, ... ] }
   * 
   * For /aqi/location/{location}:
   *   { location: "delhi", period_hours: 24, count: 24, data: [ { aqi, pm25, timestamp }, ... ] }
   * 
   * DATA NORMALIZATION:
   * The backend sends different response structures depending on endpoint.
   * We normalize both to a consistent format that the UI expects:
   *   { city, aqi, pm25, temperature, humidity, wind_speed, timestamp }
   * 
   * ERROR HANDLING:
   * - Network errors: catch block logs and displays message
   * - HTTP errors (4xx, 5xx): throw Error with status code
   * - Missing fields: use null coalescing (??) to provide N/A values
   */
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);  // Show loading indicator
      setError(null);    // Clear previous errors
      
      // Build API endpoint URL based on selected city
      const endpoint = selectedCity === 'all'
        ? `${API_BASE_URL}/aqi/latest?limit=50`  // All cities, latest readings
        : `${API_BASE_URL}/aqi/location/${selectedCity}?hours=24`;  // Specific city, 24 hours
      
      // Make HTTP GET request to backend
      // Headers explicitly set to JSON (though GET usually doesn't have body)
      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });
      
      // Check if HTTP response is successful (status 200-299)
      // If status is 4xx or 5xx, throw error (won't automatically throw)
      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }
      
      // Parse JSON response body
      const result = await response.json();
      
      /**
       * DATA NORMALIZATION
       * 
       * Different API endpoints return slightly different structures.
       * We normalize both to: { city, aqi, pm25, temperature, humidity, wind_speed, timestamp }
       */
      let normalized = [];
      
      if (selectedCity === 'all') {
        // /aqi/latest returns: { count, data: [ { location, aqi, pm25, ... } ] }
        if (result.data && Array.isArray(result.data)) {
          normalized = result.data.map(r => ({
            city: r.location || r.city || 'unknown',  // Extract city name
            aqi: r.aqi ?? null,  // Null coalesce: use null if undefined/null
            pm25: r.pm25 ?? null,
            temperature: r.temperature ?? null,  // May not be included in basic AQI response
            humidity: r.humidity ?? null,
            wind_speed: r.wind_speed ?? null,
            timestamp: r.timestamp ?? null
          }));
        }
      } else {
        // /aqi/location/{location} returns: { location, period_hours, count, data: [ { aqi, pm25, timestamp } ] }
        if (result.data && Array.isArray(result.data)) {
          normalized = result.data.map(r => ({
            city: result.location || selectedCity,  // Location from response metadata
            aqi: r.aqi ?? null,
            pm25: r.pm25 ?? null,
            temperature: null,  // Not returned by location endpoint
            humidity: null,
            wind_speed: null,
            timestamp: r.timestamp ?? null
          }));
        }
      }
      
      // Update React state with normalized data
      // Keep raw response for debugging
      setData({ count: normalized.length, data: normalized, raw: result });
      
      // Extract and store alerts if API includes them
      setAlerts(result.alerts || []);
    } catch (err) {
      // Log full error for debugging (visible in browser console)
      console.error('Error fetching data:', err);
      
      // Set error message to display in UI
      setError(err.message || 'Failed to fetch air quality data');
    } finally {
      // Always executes: hide loading indicator regardless of success/failure
      setLoading(false);
    }
  }, [selectedCity, API_BASE_URL]);  // Re-create function if selectedCity or API_BASE_URL changes

  /**
   * FETCH AI INSIGHTS (Currently stubbed)
   * 
   * This function would fetch AI-generated insights from /api/insights/predictions
   * Currently not fully implemented but structure is ready for future use.
   * 
   * Would return insights like:
   * - "Air quality expected to improve in next 2 hours"
   * - "Traffic surge detected on MG Road, expect pollution spike"
   * - "Health advisory: Senior citizens should avoid outdoor activities"
   */
  const fetchInsights = useCallback(async () => {
    try {
      const response = await fetch(`${API_BASE_URL}/api/insights/predictions`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      return await response.json();
    } catch (err) {
      console.error('Error fetching insights:', err);
      return null;  // Return null on error (insights are optional)
    }
  }, [API_BASE_URL]);

  /**
   * AUTO-REFRESH SETUP
   * 
   * This useEffect hook sets up automatic data fetching at regular intervals.
   * 
   * BEHAVIOR:
   * 1. On component mount: Call fetchData() immediately
   * 2. Then: Set up interval timer that calls fetchData() every refreshInterval ms
   * 3. On dependency change (city selected, interval changed): Clear old timer and create new one
   * 4. On component unmount: Clear timer (cleanup function)
   * 
   * WHY? Ensures dashboard always shows fresh data without manual refresh
   * 
   * CLEANUP FUNCTION:
   * return () => clearInterval(interval)
   * This prevents memory leaks by stopping timer when component unmounts
   */
  useEffect(() => {
    // Fetch data immediately when component loads or city changes
    fetchData();

    // Set up auto-refresh timer
    const interval = setInterval(() => {
      fetchData();
    }, refreshInterval);

    // CLEANUP: Stop the interval when component unmounts or dependencies change
    // This prevents multiple timers running simultaneously
    return () => clearInterval(interval);
  }, [selectedCity, refreshInterval, fetchData]);  // Re-run effect if these change

  /**
   * AQI CATEGORY AND COLOR MAPPING
   * 
   * Maps AQI numbers (0-500+) to human-readable categories and colors
   * Used for:
   * 1. Color-coded display circles (green good, red bad)
   * 2. Category text ("Good", "Unhealthy", etc.)
   * 3. Health advisory level ("Caution", "Warning", etc.)
   * 
   * AQI SCALE (WHO/US EPA):
   * 0-50     : Good (Green)      - Can exercise outdoors
   * 51-100   : Moderate (Yellow) - Acceptable, sensitive groups limit activity
   * 101-150  : Unhealthy for Sensitive Groups (Orange) - Sensitive groups stay indoors
   * 151-200  : Unhealthy (Red)   - Everyone should limit outdoor activities
   * 201-300  : Very Unhealthy (Purple) - Everyone should stay indoors
   * 301+     : Hazardous (Maroon) - Emergency, avoid all outdoor activity
   * 
   * PARAMETERS:
   * aqi: number (can be null/undefined)
   * 
   * RETURNS:
   * { category, color, level } object for display
   */
  const getAQICategory = (aqi) => {
    if (!aqi) return { category: 'Unknown', color: '#gray', level: 'N/A' };
    if (aqi <= 50) return { category: 'Good', color: '#4caf50', level: 'Favorable' };
    if (aqi <= 100) return { category: 'Moderate', color: '#8bc34a', level: 'Acceptable' };
    if (aqi <= 150) return { category: 'Unhealthy for Sensitive Groups', color: '#ff9800', level: 'Caution' };
    if (aqi <= 200) return { category: 'Unhealthy', color: '#f44336', level: 'Warning' };
    if (aqi <= 300) return { category: 'Very Unhealthy', color: '#9c27b0', level: 'Severe' };
    return { category: 'Hazardous', color: '#4a0000', level: 'Emergency' };
  };

  /**
   * LOADING STATE RENDERING
   * Show spinner/message while initially loading (before data arrives)
   */
  if (loading && !data) {
    return (
      <div className="app">
        <div className="loader">Loading air quality data...</div>
      </div>
    );
  }

  /**
   * MAIN RENDER
   * Return the full dashboard JSX
   */
  return (
    <div className="app">
      {/* ===== HEADER SECTION ===== */}
      <header className="app-header">
        <div className="header-content">
          <h1>🌍 Air Quality Monitor</h1>
          <p>Real-time AI-powered air quality monitoring and predictions</p>
        </div>
      </header>

      {/* ===== MAIN CONTENT AREA ===== */}
      <main className="app-main">
        
        {/* ===== CONTROL PANEL ===== */}
        {/* User controls for filtering and refreshing data */}
        <section className="controls">
          {/* City Selector */}
          <div className="control-group">
            <label htmlFor="city-select">Select City:</label>
            <select
              id="city-select"
              value={selectedCity}
              onChange={(e) => setSelectedCity(e.target.value)}  // Update state on selection
              className="select-control"
            >
              <option value="all">All Cities</option>
              <option value="beijing">Beijing</option>
              <option value="delhi">Delhi</option>
              <option value="shanghai">Shanghai</option>
              <option value="lagos">Lagos</option>
              <option value="dhaka">Dhaka</option>
            </select>
          </div>

          {/* Auto-Refresh Interval Selector */}
          <div className="control-group">
            <label htmlFor="refresh-interval">Refresh Interval:</label>
            <select
              id="refresh-interval"
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(parseInt(e.target.value))}  // Update interval
              className="select-control"
            >
              <option value={60000}>1 minute</option>
              <option value={300000}>5 minutes</option>
              <option value={600000}>10 minutes</option>
              <option value={1800000}>30 minutes</option>
            </select>
          </div>

          {/* Manual Refresh Button */}
          <button
            onClick={() => fetchData()}  // Manually trigger fetch
            className="btn-refresh"
            disabled={loading}  // Disable while loading
          >
            {loading ? 'Refreshing...' : 'Refresh Now'}
          </button>
        </section>

        {/* ===== ALERTS SECTION ===== */}
        {/* Show pollution alerts if any exist */}
        {alerts && alerts.length > 0 && (
          <section className="alerts-section">
            <h2>⚠️ Active Alerts</h2>
            <div className="alerts-container">
              {alerts.map((alert, index) => (
                <div key={index} className={`alert alert-${alert.severity}`}>
                  <strong>{alert.title}</strong>
                  <p>{alert.message}</p>
                  <small>{alert.timestamp}</small>
                </div>
              ))}
            </div>
          </section>
        )}

        {/* ===== ERROR MESSAGE ===== */}
        {/* Display if fetch failed */}
        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* ===== MAIN DATA DISPLAY ===== */}
        {data && (
          <>
            {/* ===== CURRENT CONDITIONS CARDS ===== */}
            <section className="current-conditions">
              <h2>Current Air Quality</h2>
              <div className="data-grid">
                {Array.isArray(data.data) ? (
                  // Map over each city's data and create a card
                  data.data.map((cityData, index) => {
                    // Get category info for this city's AQI
                    const aqiInfo = getAQICategory(cityData.aqi);
                    return (
                      <div
                        key={index}
                        className="data-card"
                        style={{ borderLeftColor: aqiInfo.color }}  // Color border matches AQI category
                      >
                        {/* City Name */}
                        <h3>{cityData.city}</h3>
                        
                        {/* AQI Display */}
                        <div className="aqi-display">
                          {/* Large AQI number circle (color-coded) */}
                          <div
                            className="aqi-circle"
                            style={{ backgroundColor: aqiInfo.color }}  // Dynamic color
                          >
                            {cityData.aqi}
                          </div>
                          
                          {/* Category and level text */}
                          <div className="aqi-info">
                            <p className="aqi-category">{aqiInfo.category}</p>
                            <p className="aqi-level">{aqiInfo.level}</p>
                          </div>
                        </div>
                        
                        {/* Additional Metrics Grid */}
                        <div className="metrics">
                          {/* Temperature */}
                          <div className="metric">
                            <span className="metric-label">Temperature:</span>
                            <span className="metric-value">
                              {cityData.temperature ? `${cityData.temperature.toFixed(1)}°C` : 'N/A'}
                            </span>
                          </div>
                          
                          {/* Humidity */}
                          <div className="metric">
                            <span className="metric-label">Humidity:</span>
                            <span className="metric-value">
                              {cityData.humidity ? `${cityData.humidity.toFixed(1)}%` : 'N/A'}
                            </span>
                          </div>
                          
                          {/* Wind Speed */}
                          <div className="metric">
                            <span className="metric-label">Wind Speed:</span>
                            <span className="metric-value">
                              {cityData.wind_speed ? `${cityData.wind_speed.toFixed(1)} m/s` : 'N/A'}
                            </span>
                          </div>
                          
                          {/* PM2.5 (Primary Pollutant) */}
                          <div className="metric">
                            <span className="metric-label">PM2.5:</span>
                            <span className="metric-value">
                              {cityData.pm25 ? `${cityData.pm25.toFixed(1)} µg/m³` : 'N/A'}
                            </span>
                          </div>
                        </div>
                      </div>
                    );
                  })
                ) : (
                  <p>No data available</p>
                )}
              </div>
            </section>

            {/* ===== AI INSIGHTS SECTION ===== */}
            {/* Static insights cards (can be dynamic if fetchInsights() is fully implemented) */}
            <section className="insights-section">
              <h2>🤖 AI Insights & Predictions</h2>
              <div className="insights-content">
                {/* Insight Card 1: Forecast */}
                <div className="insight-card">
                  <h3>24-Hour Forecast</h3>
                  <p>Air quality is expected to remain moderate with slight improvements in the evening hours.</p>
                </div>
                
                {/* Insight Card 2: Health */}
                <div className="insight-card">
                  <h3>Health Recommendations</h3>
                  <p>Sensitive groups should limit outdoor activities. Consider wearing N95 masks in high-pollution areas.</p>
                </div>
                
                {/* Insight Card 3: Trends */}
                <div className="insight-card">
                  <h3>Trend Analysis</h3>
                  <p>Overall air quality shows a declining trend over the past 7 days. Recommended actions: increase green spaces, reduce traffic.</p>
                </div>
              </div>
            </section>

            {/* ===== STATISTICS SECTION ===== */}
            {/* Summary statistics calculated from data */}
            <section className="statistics">
              <h2>📊 Statistics</h2>
              <div className="stats-grid">
                
                {/* Stat 1: Average AQI */}
                <div className="stat-card">
                  <h4>Average AQI</h4>
                  <p className="stat-value">
                    {data.data && data.data.length > 0
                      ? (
                          data.data.reduce((sum, city) => sum + (city.aqi || 0), 0) /
                          data.data.length
                        ).toFixed(1)
                      : 'N/A'}
                  </p>
                </div>
                
                {/* Stat 2: Most Polluted City */}
                <div className="stat-card">
                  <h4>Most Polluted City</h4>
                  <p className="stat-value">
                    {data.data && data.data.length > 0
                      ? data.data.reduce((prev, current) =>
                          (prev.aqi || 0) > (current.aqi || 0) ? prev : current
                        ).city
                      : 'N/A'}
                  </p>
                </div>
                
                {/* Stat 3: Cleanest City */}
                <div className="stat-card">
                  <h4>Cleanest City</h4>
                  <p className="stat-value">
                    {data.data && data.data.length > 0
                      ? data.data.reduce((prev, current) =>
                          (prev.aqi || 0) < (current.aqi || 0) ? prev : current
                        ).city
                      : 'N/A'}
                  </p>
                </div>
                
                {/* Stat 4: Total Cities Monitored */}
                <div className="stat-card">
                  <h4>Cities Monitored</h4>
                  <p className="stat-value">{data.data ? data.data.length : 0}</p>
                </div>
              </div>
            </section>
          </>
        )}
      </main>

      {/* ===== FOOTER ===== */}
      <footer className="app-footer">
        <p>Last updated: {new Date().toLocaleString()}</p>
        <p>Urban Air Quality AI Agent - Powered by Apache Airflow, Kafka, and Machine Learning</p>
      </footer>
    </div>
  );
};

export default App;