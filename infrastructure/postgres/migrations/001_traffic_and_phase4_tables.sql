-- Migration 001: Create traffic_data and Phase 4 tables on existing databases
-- Run this when Postgres was initialized before these tables were added (e.g. "Skipping initialization").
-- Usage: docker exec -i air_postgres psql -U airuser -d airquality < infrastructure/postgres/migrations/001_traffic_and_phase4_tables.sql

-- 1. traffic_data (required for batch ingestion and retention)
CREATE TABLE IF NOT EXISTS traffic_data (
    id SERIAL PRIMARY KEY,
    location_id INT REFERENCES locations(id),
    city VARCHAR(50),
    recorded_at TIMESTAMP NOT NULL,
    vehicle_count INT,
    congestion_index FLOAT,
    avg_speed FLOAT
);

CREATE INDEX IF NOT EXISTS idx_traffic_recorded_at ON traffic_data(recorded_at);
CREATE INDEX IF NOT EXISTS idx_traffic_location_time ON traffic_data(location_id, recorded_at);

-- Add location_id to traffic_data if table existed without it
DO $$
BEGIN
    IF EXISTS (SELECT 1 FROM information_schema.tables WHERE table_name = 'traffic_data')
       AND NOT EXISTS (SELECT 1 FROM information_schema.columns WHERE table_name = 'traffic_data' AND column_name = 'location_id') THEN
        ALTER TABLE traffic_data ADD COLUMN location_id INT REFERENCES locations(id);
    END IF;
END $$;

-- 2. Phase 4 aggregation tables
CREATE TABLE IF NOT EXISTS hourly_aggregates (
    id SERIAL PRIMARY KEY,
    location_id INT REFERENCES locations(id),
    hour_bucket TIMESTAMP NOT NULL,
    avg_aqi DOUBLE PRECISION,
    avg_pm2_5 DOUBLE PRECISION,
    avg_temp DOUBLE PRECISION,
    avg_humidity DOUBLE PRECISION,
    avg_vehicle_count DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (location_id, hour_bucket)
);

CREATE TABLE IF NOT EXISTS daily_aggregates (
    id SERIAL PRIMARY KEY,
    location_id INT REFERENCES locations(id),
    date_bucket DATE NOT NULL,
    avg_aqi DOUBLE PRECISION,
    avg_pm2_5 DOUBLE PRECISION,
    max_aqi INT,
    min_aqi INT,
    rolling_7d_avg_aqi DOUBLE PRECISION,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (location_id, date_bucket)
);

CREATE TABLE IF NOT EXISTS correlation_metrics (
    id SERIAL PRIMARY KEY,
    location_id INT REFERENCES locations(id),
    computed_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    traffic_aqi_correlation DOUBLE PRECISION,
    weather_aqi_correlation_temp DOUBLE PRECISION,
    weather_aqi_correlation_humidity DOUBLE PRECISION,
    sample_count INT
);

CREATE TABLE IF NOT EXISTS anomaly_events (
    id SERIAL PRIMARY KEY,
    location_id INT REFERENCES locations(id),
    recorded_at TIMESTAMP NOT NULL,
    aqi_value INT NOT NULL,
    event_type VARCHAR(50) DEFAULT 'spike',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX IF NOT EXISTS idx_anomaly_recorded_at ON anomaly_events(recorded_at);

-- Phase 5: AQI predictions
CREATE TABLE IF NOT EXISTS aqi_predictions (
    id SERIAL PRIMARY KEY,
    location_id INT REFERENCES locations(id),
    predicted_at TIMESTAMP NOT NULL,
    predicted_aqi DOUBLE PRECISION NOT NULL,
    model_version VARCHAR(50),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE (location_id, predicted_at)
);

CREATE INDEX IF NOT EXISTS idx_aqi_predictions_predicted_at ON aqi_predictions(predicted_at);
