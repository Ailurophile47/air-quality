CREATE TABLE locations (
    id SERIAL PRIMARY KEY,
    city_name VARCHAR(100) NOT NULL,
    latitude DOUBLE PRECISION NOT NULL,
    longitude DOUBLE PRECISION NOT NULL,
    country VARCHAR(100),
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE UNIQUE INDEX idx_location_unique 
ON locations(city_name);

CREATE TABLE raw_aqi_data (
    id SERIAL PRIMARY KEY,
    location_id INT REFERENCES locations(id),
    raw_payload JSONB NOT NULL,
    ingestion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE raw_weather_data (
    id SERIAL PRIMARY KEY,
    location_id INT REFERENCES locations(id),
    raw_payload JSONB NOT NULL,
    ingestion_time TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE aqi_measurements (
    id SERIAL PRIMARY KEY,
    location_id INT REFERENCES locations(id),
    aqi_value INT CHECK (aqi_value >= 0),
    pm2_5 DOUBLE PRECISION,
    pm10 DOUBLE PRECISION,
    no2 DOUBLE PRECISION,
    o3 DOUBLE PRECISION,
    co DOUBLE PRECISION,
    dominant_pollutant VARCHAR(50),
    recorded_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_aqi_recorded_at ON aqi_measurements(recorded_at);
CREATE INDEX idx_aqi_loc_time ON aqi_measurements(location_id, recorded_at);

CREATE TABLE weather_measurements (
    id SERIAL PRIMARY KEY,
    location_id INT REFERENCES locations(id),
    temperature DOUBLE PRECISION,
    humidity DOUBLE PRECISION,
    wind_speed DOUBLE PRECISION,
    pressure DOUBLE PRECISION,
    visibility DOUBLE PRECISION,
    recorded_at TIMESTAMP NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE INDEX idx_weather_recorded_at 
ON weather_measurements(recorded_at);
ALTER TABLE aqi_measurements
ADD CONSTRAINT unique_aqi_record
UNIQUE (location_id, recorded_at);

ALTER TABLE weather_measurements
ADD CONSTRAINT unique_weather_record
UNIQUE (location_id, recorded_at);

