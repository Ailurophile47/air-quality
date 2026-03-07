"""
Phase 4: 7-day rolling retention.
Deletes data older than 7 days from all measurement tables.
"""
import logging
from datetime import datetime, timedelta

from loader import get_connection

logger = logging.getLogger(__name__)
RETENTION_DAYS = 7


def run_retention() -> dict:
    """
    Delete records older than 7 days from all tables.
    Returns counts of deleted rows per table.
    """
    cutoff = datetime.utcnow() - timedelta(days=RETENTION_DAYS)
    results = {}

    with get_connection() as conn:
        with conn.cursor() as cur:
            tables = [
                ("aqi_measurements", "recorded_at"),
                ("weather_measurements", "recorded_at"),
                ("traffic_data", "recorded_at"),
                ("raw_aqi_data", "ingestion_time"),
                ("raw_weather_data", "ingestion_time"),
            ]
            for table, ts_col in tables:
                cur.execute(
                    f"DELETE FROM {table} WHERE {ts_col} < %s",
                    (cutoff,),
                )
                deleted = cur.rowcount
                results[table] = deleted
                conn.commit()
                if deleted:
                    logger.info("Deleted %d rows from %s (older than %s)", deleted, table, cutoff)

    return results
