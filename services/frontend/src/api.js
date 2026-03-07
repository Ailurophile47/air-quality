import axios from 'axios'

// Always use localhost from browser - the API is exposed on port 8000
const API_BASE = 'http://localhost:8000'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 10000,
})

export const fetchLatestAQI = async (city = 'Bangalore') => {
  try {
    const res = await api.get('/aqi/latest', { params: { city } })
    return res.data
  } catch (error) {
    console.error('Error fetching latest AQI:', error)
    return null
  }
}

export const fetchPredictions = async (city = 'Bangalore', limit = 6) => {
  try {
    const res = await api.get('/dashboard/predictions', { params: { city, limit } })
    return res.data || []
  } catch (error) {
    console.error('Error fetching predictions:', error)
    return []
  }
}

export const fetchHourlyData = async (city = 'Bangalore', limit = 72) => {
  try {
    const res = await api.get('/dashboard/hourly', { params: { city, limit } })
    return res.data || []
  } catch (error) {
    console.error('Error fetching hourly data:', error)
    return []
  }
}

export const fetchDailyData = async (city = 'Bangalore', limit = 14) => {
  try {
    const res = await api.get('/dashboard/daily', { params: { city, limit } })
    return res.data || []
  } catch (error) {
    console.error('Error fetching daily data:', error)
    return []
  }
}

export const fetchAnomalies = async (city = 'Bangalore', limit = 20) => {
  try {
    const res = await api.get('/dashboard/anomalies', { params: { city, limit } })
    return res.data || []
  } catch (error) {
    console.error('Error fetching anomalies:', error)
    return []
  }
}

export const fetchCorrelation = async (city = 'Bangalore') => {
  try {
    const res = await api.get('/dashboard/correlation', { params: { city } })
    return res.data || {}
  } catch (error) {
    console.error('Error fetching correlation:', error)
    return {}
  }
}
