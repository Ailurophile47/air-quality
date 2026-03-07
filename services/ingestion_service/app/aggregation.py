"""
Phase 4: Aggregation and metric computation.
Computes hourly/daily AQI averages, rolling 7-day, correlation, and anomaly detection.
"""
import logging
from loader import get_connection

logger = logging.getLogger(__name__)
AQI_SPIKE_THRESHOLD = 300


def run_aggregation(location_id: int = 1) -> dict:
    """
    Compute hourly aggregates, daily aggregates, correlation metrics, and anomaly events.
    Returns summary of what was computed.
    """
    results = {"hourly": 0, "daily": 0, "correlation": False, "anomalies": 0}

    with get_connection() as conn:
        with conn.cursor() as cur:
            # 1. Hourly aggregates (from last 7 days)
            cur.execute("""
                INSERT INTO hourly_aggregates (location_id, hour_bucket, avg_aqi, avg_pm2_5, avg_temp, avg_humidity, avg_vehicle_count)
                SELECT
                    %s,
                    date_trunc('hour', a.recorded_at) AS hour_bucket,
                    AVG(a.aqi_value),
                    AVG(a.pm2_5),
                    AVG(w.temperature),
                    AVG(w.humidity),
                    AVG(t.vehicle_count)
                FROM aqi_measurements a
                LEFT JOIN weather_measurements w
                    ON a.location_id = w.location_id
                    AND date_trunc('hour', a.recorded_at) = date_trunc('hour', w.recorded_at)
                LEFT JOIN traffic_data t
                    ON a.location_id = t.location_id
                    AND date_trunc('hour', a.recorded_at) = date_trunc('hour', t.recorded_at)
                WHERE a.location_id = %s
                  AND a.recorded_at >= NOW() - INTERVAL '7 days'
                GROUP BY date_trunc('hour', a.recorded_at)
                ON CONFLICT (location_id, hour_bucket) DO UPDATE SET
                    avg_aqi = EXCLUDED.avg_aqi,
                    avg_pm2_5 = EXCLUDED.avg_pm2_5,
                    avg_temp = EXCLUDED.avg_temp,
                    avg_humidity = EXCLUDED.avg_humidity,
                    avg_vehicle_count = EXCLUDED.avg_vehicle_count
            """, (location_id, location_id))
            results["hourly"] = cur.rowcount
            conn.commit()

            # 2. Daily aggregates with rolling 7-day average
            cur.execute("""
                INSERT INTO daily_aggregates (location_id, date_bucket, avg_aqi, avg_pm2_5, max_aqi, min_aqi, rolling_7d_avg_aqi)
                SELECT
                    %s,
                    a.date_bucket,
                    a.avg_aqi,
                    a.avg_pm2_5,
                    a.max_aqi,
                    a.min_aqi,
                    AVG(a.avg_aqi) OVER (ORDER BY a.date_bucket ROWS BETWEEN 6 PRECEDING AND CURRENT ROW)
                FROM (
                    SELECT
                        date_trunc('day', recorded_at)::date AS date_bucket,
                        AVG(aqi_value) AS avg_aqi,
                        AVG(pm2_5) AS avg_pm2_5,
                        MAX(aqi_value) AS max_aqi,
                        MIN(aqi_value) AS min_aqi
                    FROM aqi_measurements
                    WHERE location_id = %s AND recorded_at >= NOW() - INTERVAL '7 days'
                    GROUP BY date_trunc('day', recorded_at)
                ) a
                ON CONFLICT (location_id, date_bucket) DO UPDATE SET
                    avg_aqi = EXCLUDED.avg_aqi,
                    avg_pm2_5 = EXCLUDED.avg_pm2_5,
                    max_aqi = EXCLUDED.max_aqi,
                    min_aqi = EXCLUDED.min_aqi,
                    rolling_7d_avg_aqi = EXCLUDED.rolling_7d_avg_aqi
            """, (location_id, location_id))
            results["daily"] = cur.rowcount
            conn.commit()

            # 3. Anomaly detection (AQI > 300)
            cur.execute("""
                INSERT INTO anomaly_events (location_id, recorded_at, aqi_value, event_type)
                SELECT location_id, recorded_at, aqi_value, 'spike'
                FROM aqi_measurements
                WHERE location_id = %s
                  AND aqi_value >= %s
                  AND recorded_at >= NOW() - INTERVAL '7 days'
                  AND NOT EXISTS (
                    SELECT 1 FROM anomaly_events ae
                    WHERE ae.location_id = aqi_measurements.location_id
                      AND ae.recorded_at = aqi_measurements.recorded_at
                  )
            """, (location_id, AQI_SPIKE_THRESHOLD))
            results["anomalies"] = cur.rowcount
            conn.commit()

            # 4. Correlation metrics (traffic vs AQI, weather vs AQI)
            cur.execute("""
                WITH aligned AS (
                    SELECT
                        a.aqi_value,
                        t.vehicle_count,
                        w.temperature,
                        w.humidity
                    FROM aqi_measurements a
                    JOIN traffic_data t ON a.location_id = t.location_id
                        AND a.recorded_at = t.recorded_at
                    JOIN weather_measurements w ON a.location_id = w.location_id
                        AND a.recorded_at = w.recorded_at
                    WHERE a.location_id = %s
                      AND a.recorded_at >= NOW() - INTERVAL '7 days'
                )
                INSERT INTO correlation_metrics (
                    location_id, traffic_aqi_correlation,
                    weather_aqi_correlation_temp, weather_aqi_correlation_humidity,
                    sample_count
                )
                SELECT
                    %s,
                    CORR(aqi_value, vehicle_count),
                    CORR(aqi_value, temperature),
                    CORR(aqi_value, humidity),
                    COUNT(*)
                FROM aligned
            """, (location_id, location_id))
            results["correlation"] = cur.rowcount > 0
            conn.commit()

    logger.info("Aggregation complete: %s", results)
    return results
