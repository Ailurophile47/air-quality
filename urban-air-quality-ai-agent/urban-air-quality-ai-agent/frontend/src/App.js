import React, { useState, useEffect, useCallback } from 'react';
import './App.css';

const App = () => {
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState(null);
  const [selectedCity, setSelectedCity] = useState('all');
  const [refreshInterval, setRefreshInterval] = useState(300000); // 5 minutes
  const [alerts, setAlerts] = useState([]);
  const [chartData, setChartData] = useState([]);

  const API_BASE_URL = process.env.REACT_APP_API_URL || 'http://localhost:8000';

  // Fetch air quality data
  const fetchData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);

      const endpoint = selectedCity === 'all' 
        ? `${API_BASE_URL}/api/aqi/current` 
        : `${API_BASE_URL}/api/aqi/city/${selectedCity}`;

      const response = await fetch(endpoint, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        },
      });

      if (!response.ok) {
        throw new Error(`HTTP error! status: ${response.status}`);
      }

      const result = await response.json();
      setData(result);
      
      // Update chart data
      if (result.data && Array.isArray(result.data)) {
        setChartData(result.data);
      }

      // Check for alerts
      if (result.alerts) {
        setAlerts(result.alerts);
      }
    } catch (err) {
      console.error('Error fetching data:', err);
      setError(err.message || 'Failed to fetch air quality data');
    } finally {
      setLoading(false);
    }
  }, [selectedCity]);

  // Fetch AI insights
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
      return null;
    }
  }, []);

  // Set up auto-refresh
  useEffect(() => {
    fetchData();

    const interval = setInterval(() => {
      fetchData();
    }, refreshInterval);

    return () => clearInterval(interval);
  }, [selectedCity, refreshInterval, fetchData]);

  // Get AQI category and color
  const getAQICategory = (aqi) => {
    if (!aqi) return { category: 'Unknown', color: '#gray', level: 'N/A' };
    if (aqi <= 50) return { category: 'Good', color: '#4caf50', level: 'Favorable' };
    if (aqi <= 100) return { category: 'Moderate', color: '#8bc34a', level: 'Acceptable' };
    if (aqi <= 150) return { category: 'Unhealthy for Sensitive Groups', color: '#ff9800', level: 'Caution' };
    if (aqi <= 200) return { category: 'Unhealthy', color: '#f44336', level: 'Warning' };
    if (aqi <= 300) return { category: 'Very Unhealthy', color: '#9c27b0', level: 'Severe' };
    return { category: 'Hazardous', color: '#4a0000', level: 'Emergency' };
  };

  if (loading && !data) {
    return (
      <div className="app">
        <div className="loader">Loading air quality data...</div>
      </div>
    );
  }

  return (
    <div className="app">
      {/* Header */}
      <header className="app-header">
        <div className="header-content">
          <h1>🌍 Air Quality Monitor</h1>
          <p>Real-time AI-powered air quality monitoring and predictions</p>
        </div>
      </header>

      {/* Main Content */}
      <main className="app-main">
        {/* Controls */}
        <section className="controls">
          <div className="control-group">
            <label htmlFor="city-select">Select City:</label>
            <select
              id="city-select"
              value={selectedCity}
              onChange={(e) => setSelectedCity(e.target.value)}
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

          <div className="control-group">
            <label htmlFor="refresh-interval">Refresh Interval:</label>
            <select
              id="refresh-interval"
              value={refreshInterval}
              onChange={(e) => setRefreshInterval(parseInt(e.target.value))}
              className="select-control"
            >
              <option value={60000}>1 minute</option>
              <option value={300000}>5 minutes</option>
              <option value={600000}>10 minutes</option>
              <option value={1800000}>30 minutes</option>
            </select>
          </div>

          <button
            onClick={() => fetchData()}
            className="btn-refresh"
            disabled={loading}
          >
            {loading ? 'Refreshing...' : 'Refresh Now'}
          </button>
        </section>

        {/* Alerts */}
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

        {/* Error Message */}
        {error && (
          <div className="error-message">
            <strong>Error:</strong> {error}
          </div>
        )}

        {/* Data Display */}
        {data && (
          <>
            {/* Current Conditions */}
            <section className="current-conditions">
              <h2>Current Air Quality</h2>
              <div className="data-grid">
                {Array.isArray(data.data) ? (
                  data.data.map((cityData, index) => {
                    const aqiInfo = getAQICategory(cityData.aqi);
                    return (
                      <div
                        key={index}
                        className="data-card"
                        style={{ borderLeftColor: aqiInfo.color }}
                      >
                        <h3>{cityData.city}</h3>
                        <div className="aqi-display">
                          <div
                            className="aqi-circle"
                            style={{ backgroundColor: aqiInfo.color }}
                          >
                            {cityData.aqi}
                          </div>
                          <div className="aqi-info">
                            <p className="aqi-category">{aqiInfo.category}</p>
                            <p className="aqi-level">{aqiInfo.level}</p>
                          </div>
                        </div>
                        <div className="metrics">
                          <div className="metric">
                            <span className="metric-label">Temperature:</span>
                            <span className="metric-value">
                              {cityData.temperature ? `${cityData.temperature.toFixed(1)}°C` : 'N/A'}
                            </span>
                          </div>
                          <div className="metric">
                            <span className="metric-label">Humidity:</span>
                            <span className="metric-value">
                              {cityData.humidity ? `${cityData.humidity.toFixed(1)}%` : 'N/A'}
                            </span>
                          </div>
                          <div className="metric">
                            <span className="metric-label">Wind Speed:</span>
                            <span className="metric-value">
                              {cityData.wind_speed ? `${cityData.wind_speed.toFixed(1)} m/s` : 'N/A'}
                            </span>
                          </div>
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

            {/* AI Insights */}
            <section className="insights-section">
              <h2>🤖 AI Insights & Predictions</h2>
              <div className="insights-content">
                <div className="insight-card">
                  <h3>24-Hour Forecast</h3>
                  <p>Air quality is expected to remain moderate with slight improvements in the evening hours.</p>
                </div>
                <div className="insight-card">
                  <h3>Health Recommendations</h3>
                  <p>Sensitive groups should limit outdoor activities. Consider wearing N95 masks in high-pollution areas.</p>
                </div>
                <div className="insight-card">
                  <h3>Trend Analysis</h3>
                  <p>Overall air quality shows a declining trend over the past 7 days. Recommended actions: increase green spaces, reduce traffic.</p>
                </div>
              </div>
            </section>

            {/* Statistics */}
            <section className="statistics">
              <h2>📊 Statistics</h2>
              <div className="stats-grid">
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
                <div className="stat-card">
                  <h4>Cities Monitored</h4>
                  <p className="stat-value">{data.data ? data.data.length : 0}</p>
                </div>
              </div>
            </section>
          </>
        )}
      </main>

      {/* Footer */}
      <footer className="app-footer">
        <p>Last updated: {new Date().toLocaleString()}</p>
        <p>Urban Air Quality AI Agent - Powered by Apache Airflow, Kafka, and Machine Learning</p>
      </footer>
    </div>
  );
};

export default App;
