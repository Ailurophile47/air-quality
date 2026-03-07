import React, { useState, useEffect } from 'react'
import {
  Wind,
  Droplets,
  AlertTriangle,
  TrendingUp,
  Activity,
  Gauge,
  CloudDrizzle,
  Eye,
} from 'lucide-react'
import {
  LineChart,
  Line,
  AreaChart,
  Area,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  Legend,
  ResponsiveContainer,
  ComposedChart,
  ScatterChart,
  Scatter,
} from 'recharts'
import {
  fetchLatestAQI,
  fetchPredictions,
  fetchHourlyData,
  fetchDailyData,
  fetchAnomalies,
  fetchCorrelation,
} from './api'
import MetricCard from './components/MetricCard'
import ChartContainer from './components/ChartContainer'
import Header from './components/Header'

function App() {
  const [city] = useState('Bangalore')
  const [latestAQI, setLatestAQI] = useState(null)
  const [predictions, setPredictions] = useState([])
  const [hourlyData, setHourlyData] = useState([])
  const [dailyData, setDailyData] = useState([])
  const [anomalies, setAnomalies] = useState([])
  const [correlation, setCorrelation] = useState({})
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    const loadData = async () => {
      setLoading(true)
      const [aqi, preds, hourly, daily, anom, corr] = await Promise.all([
        fetchLatestAQI(city),
        fetchPredictions(city),
        fetchHourlyData(city, 72),
        fetchDailyData(city, 14),
        fetchAnomalies(city),
        fetchCorrelation(city),
      ])

      setLatestAQI(aqi)
      setPredictions(preds)
      setHourlyData(hourly)
      setDailyData(daily)
      setAnomalies(anom)
      setCorrelation(corr)
      setLoading(false)
    }

    loadData()
    const interval = setInterval(loadData, 30000) // Refresh every 30 seconds
    return () => clearInterval(interval)
  }, [city])

  const getAQIColor = (aqi) => {
    if (aqi <= 50) return { text: 'text-green-400', bg: 'from-green-900 to-green-800', label: 'Good' }
    if (aqi <= 100) return { text: 'text-yellow-400', bg: 'from-yellow-900 to-yellow-800', label: 'Moderate' }
    if (aqi <= 150) return { text: 'text-orange-400', bg: 'from-orange-900 to-orange-800', label: 'Unhealthy for Sensitive Groups' }
    if (aqi <= 200) return { text: 'text-orange-500', bg: 'from-orange-900 to-red-900', label: 'Unhealthy' }
    if (aqi <= 300) return { text: 'text-red-500', bg: 'from-red-900 to-purple-900', label: 'Very Unhealthy' }
    return { text: 'text-red-600', bg: 'from-purple-900 to-red-900', label: 'Hazardous' }
  }

  const aqiColor = getAQIColor(latestAQI?.aqi_value || 0)
  const nextPred = predictions?.[0]

  return (
    <div className="min-h-screen bg-gradient-to-br from-gray-950 via-slate-900 to-gray-950">
      <Header city={city} />

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 py-8">
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block animate-spin rounded-full h-8 w-8 border-b-2 border-cyan-400 mb-4"></div>
            <p className="text-slate-400">Loading dashboard...</p>
          </div>
        )}

        {!loading && (
          <>
            {/* Primary Metrics Row */}
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4 mb-8">
              <MetricCard
                title="Current AQI"
                value={latestAQI?.aqi_value || '—'}
                subtitle={aqiColor.label}
                icon={<Gauge className="w-6 h-6" />}
                colorClass={aqiColor.text}
                bgGradient={aqiColor.bg}
              />
              <MetricCard
                title="PM2.5"
                value={`${latestAQI?.pm2_5 || '—'} µg/m³`}
                subtitle="Particulate Matter"
                icon={<CloudDrizzle className="w-6 h-6" />}
                colorClass="text-cyan-400"
              />
              <MetricCard
                title="Next 3h Prediction"
                value={nextPred?.predicted_aqi ? Math.round(nextPred.predicted_aqi) : '—'}
                subtitle={nextPred ? new Date(nextPred.predicted_at).toLocaleTimeString() : 'No prediction'}
                icon={<TrendingUp className="w-6 h-6" />}
                colorClass="text-purple-400"
              />
              <MetricCard
                title="Dominant Pollutant"
                value={latestAQI?.dominant_pollutant?.toUpperCase() || '—'}
                subtitle="Primary concern"
                icon={<AlertTriangle className="w-6 h-6" />}
                colorClass="text-orange-400"
              />
            </div>

            {/* Charts Row 1 */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 mb-8">
              {/* Hourly Trend */}
              <ChartContainer title="AQI Trend (72h)" subtitle="Hourly measurements">
                <ResponsiveContainer width="100%" height={300}>
                  <AreaChart data={hourlyData}>
                    <defs>
                      <linearGradient id="colorAqi" x1="0" y1="0" x2="0" y2="1">
                        <stop offset="5%" stopColor="#06b6d4" stopOpacity={0.8} />
                        <stop offset="95%" stopColor="#06b6d4" stopOpacity={0.1} />
                      </linearGradient>
                    </defs>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="hour_bucket" stroke="#94a3b8" tick={{ fontSize: 12 }} />
                    <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                      formatter={(value) => Math.round(value)}
                    />
                    <Area
                      type="monotone"
                      dataKey="avg_aqi"
                      stroke="#06b6d4"
                      fillOpacity={1}
                      fill="url(#colorAqi)"
                      isAnimationActive
                    />
                  </AreaChart>
                </ResponsiveContainer>
              </ChartContainer>

              {/* Daily Trend with Rolling Average */}
              <ChartContainer title="Daily AQI & 7-Day Rolling Average" subtitle="Daily statistics">
                <ResponsiveContainer width="100%" height={300}>
                  <ComposedChart data={dailyData}>
                    <CartesianGrid strokeDasharray="3 3" stroke="#334155" />
                    <XAxis dataKey="date_bucket" stroke="#94a3b8" tick={{ fontSize: 12 }} />
                    <YAxis stroke="#94a3b8" tick={{ fontSize: 12 }} />
                    <Tooltip
                      contentStyle={{ backgroundColor: '#1e293b', border: '1px solid #475569' }}
                      formatter={(value) => Math.round(value)}
                    />
                    <Legend />
                    <Bar dataKey="avg_aqi" fill="#06b6d4" opacity={0.6} name="Daily Average" />
                    <Line
                      type="monotone"
                      dataKey="rolling_7d_avg_aqi"
                      stroke="#a855f7"
                      strokeWidth={2}
                      name="7-Day Rolling"
                      isAnimationActive
                    />
                  </ComposedChart>
                </ResponsiveContainer>
              </ChartContainer>
            </div>

            {/* Statistics Row */}
            <div className="grid grid-cols-1 md:grid-cols-3 gap-4 mb-8">
              {/* Correlation Metrics */}
              <ChartContainer title="Correlation Analysis" subtitle="Statistical relationships">
                <div className="space-y-4">
                  <div className="p-4 bg-slate-700/50 rounded-lg border border-slate-600">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400 text-sm">Traffic ↔ AQI</span>
                      <span className="text-lg font-bold text-cyan-400">
                        {(correlation?.traffic_aqi_correlation || 0).toFixed(3)}
                      </span>
                    </div>
                    <div className="w-full bg-slate-600 rounded h-1 mt-2">
                      <div
                        className="bg-gradient-to-r from-cyan-500 to-cyan-400 h-1 rounded"
                        style={{ width: `${Math.abs(correlation?.traffic_aqi_correlation || 0) * 100}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="p-4 bg-slate-700/50 rounded-lg border border-slate-600">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400 text-sm">Temperature ↔ AQI</span>
                      <span className="text-lg font-bold text-purple-400">
                        {(correlation?.weather_aqi_correlation_temp || 0).toFixed(3)}
                      </span>
                    </div>
                    <div className="w-full bg-slate-600 rounded h-1 mt-2">
                      <div
                        className="bg-gradient-to-r from-purple-500 to-purple-400 h-1 rounded"
                        style={{ width: `${Math.abs(correlation?.weather_aqi_correlation_temp || 0) * 100}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="p-4 bg-slate-700/50 rounded-lg border border-slate-600">
                    <div className="flex items-center justify-between">
                      <span className="text-slate-400 text-sm">Humidity ↔ AQI</span>
                      <span className="text-lg font-bold text-blue-400">
                        {(correlation?.weather_aqi_correlation_humidity || 0).toFixed(3)}
                      </span>
                    </div>
                    <div className="w-full bg-slate-600 rounded h-1 mt-2">
                      <div
                        className="bg-gradient-to-r from-blue-500 to-blue-400 h-1 rounded"
                        style={{ width: `${Math.abs(correlation?.weather_aqi_correlation_humidity || 0) * 100}%` }}
                      ></div>
                    </div>
                  </div>

                  <div className="pt-2 border-t border-slate-600 mt-4">
                    <p className="text-xs text-slate-500">
                      Based on {correlation?.sample_count || 0} aligned samples
                    </p>
                  </div>
                </div>
              </ChartContainer>

              {/* Anomalies */}
              <ChartContainer title="Anomaly Events" subtitle="AQI ≥ 300 spikes">
                <div className="space-y-2 max-h-80 overflow-y-auto">
                  {anomalies && anomalies.length > 0 ? (
                    anomalies.map((anomaly, idx) => (
                      <div key={idx} className="p-3 bg-red-900/30 rounded-lg border border-red-700/50">
                        <div className="flex items-center gap-2 mb-1">
                          <AlertTriangle className="w-4 h-4 text-red-400" />
                          <span className="text-sm font-bold text-red-400">{Math.round(anomaly.aqi_value)}</span>
                        </div>
                        <p className="text-xs text-slate-400">
                          {new Date(anomaly.recorded_at).toLocaleString()}
                        </p>
                      </div>
                    ))
                  ) : (
                    <p className="text-slate-500 text-sm text-center py-8">No anomalies detected</p>
                  )}
                </div>
              </ChartContainer>

              {/* Summary Stats */}
              <ChartContainer title="Summary Statistics" subtitle="Current window stats">
                <div className="space-y-3">
                  <div className="stat-item p-3 bg-slate-700/50 rounded-lg">
                    <p className="text-slate-400 text-sm mb-1">Max AQI (7d)</p>
                    <p className="text-2xl font-bold text-orange-400">
                      {dailyData?.length > 0
                        ? Math.max(...dailyData.map((d) => d.max_aqi || 0))
                        : '—'}
                    </p>
                  </div>
                  <div className="stat-item p-3 bg-slate-700/50 rounded-lg">
                    <p className="text-slate-400 text-sm mb-1">Min AQI (7d)</p>
                    <p className="text-2xl font-bold text-green-400">
                      {dailyData?.length > 0
                        ? Math.min(...dailyData.map((d) => d.min_aqi || 999))
                        : '—'}
                    </p>
                  </div>
                  <div className="stat-item p-3 bg-slate-700/50 rounded-lg">
                    <p className="text-slate-400 text-sm mb-1">7-Day Average</p>
                    <p className="text-2xl font-bold text-cyan-400">
                      {dailyData?.length > 0
                        ? Math.round(dailyData[dailyData.length - 1]?.rolling_7d_avg_aqi || 0)
                        : '—'}
                    </p>
                  </div>
                </div>
              </ChartContainer>
            </div>

            {/* Footer */}
            <div className="text-center py-8 border-t border-slate-700 mt-12">
              <p className="text-slate-500 text-sm">
                🌫️ Urban Air Quality Intelligence • Last updated: {new Date().toLocaleTimeString()}
              </p>
              <p className="text-slate-600 text-xs mt-2">
                Data auto-refreshes every 30 seconds | Phase 5 ML Predictions Enabled
              </p>
            </div>
          </>
        )}
      </div>
    </div>
  )
}

export default App
