"""Dashboard API: predictions, aggregates, anomalies, correlation."""
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import text

from ..database import AsyncSessionLocal

router = APIRouter(prefix="/dashboard", tags=["dashboard"])


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session


@router.get("/predictions")
async def get_predictions(
    city: str = "Bangalore",
    limit: int = 24,
    db: AsyncSession = Depends(get_db),
):
    """Latest AQI predictions for the city."""
    limit = min(limit, 100)
    q = text("""
        SELECT p.id, p.location_id, p.predicted_at, p.predicted_aqi, p.model_version, p.created_at
        FROM aqi_predictions p
        JOIN locations l ON p.location_id = l.id
        WHERE l.city_name = :city
        ORDER BY p.predicted_at DESC
        LIMIT :limit
    """)
    result = await db.execute(q, {"city": city, "limit": limit})
    rows = result.fetchall()
    return [dict(row._mapping) for row in rows]


@router.get("/hourly")
async def get_hourly_aggregates(
    city: str = "Bangalore",
    limit: int = 168,
    db: AsyncSession = Depends(get_db),
):
    """Hourly aggregates (AQI, weather, traffic) for charts."""
    limit = min(limit, 500)
    q = text("""
        SELECT h.hour_bucket, h.avg_aqi, h.avg_pm2_5, h.avg_temp, h.avg_humidity, h.avg_vehicle_count
        FROM hourly_aggregates h
        JOIN locations l ON h.location_id = l.id
        WHERE l.city_name = :city
        ORDER BY h.hour_bucket DESC
        LIMIT :limit
    """)
    result = await db.execute(q, {"city": city, "limit": limit})
    rows = result.fetchall()
    return [dict(row._mapping) for row in rows]


@router.get("/daily")
async def get_daily_aggregates(
    city: str = "Bangalore",
    limit: int = 30,
    db: AsyncSession = Depends(get_db),
):
    """Daily aggregates including rolling 7-day AQI."""
    limit = min(limit, 90)
    q = text("""
        SELECT d.date_bucket, d.avg_aqi, d.avg_pm2_5, d.max_aqi, d.min_aqi, d.rolling_7d_avg_aqi
        FROM daily_aggregates d
        JOIN locations l ON d.location_id = l.id
        WHERE l.city_name = :city
        ORDER BY d.date_bucket DESC
        LIMIT :limit
    """)
    result = await db.execute(q, {"city": city, "limit": limit})
    rows = result.fetchall()
    return [dict(row._mapping) for row in rows]


@router.get("/anomalies")
async def get_anomalies(
    city: str = "Bangalore",
    limit: int = 50,
    db: AsyncSession = Depends(get_db),
):
    """AQI spike events (e.g. AQI >= 300)."""
    limit = min(limit, 200)
    q = text("""
        SELECT a.recorded_at, a.aqi_value, a.event_type, a.created_at
        FROM anomaly_events a
        JOIN locations l ON a.location_id = l.id
        WHERE l.city_name = :city
        ORDER BY a.recorded_at DESC
        LIMIT :limit
    """)
    result = await db.execute(q, {"city": city, "limit": limit})
    rows = result.fetchall()
    return [dict(row._mapping) for row in rows]


@router.get("/correlation")
async def get_correlation(city: str = "Bangalore", db: AsyncSession = Depends(get_db)):
    """Latest correlation metrics (traffic vs AQI, weather vs AQI)."""
    q = text("""
        SELECT c.computed_at, c.traffic_aqi_correlation,
               c.weather_aqi_correlation_temp, c.weather_aqi_correlation_humidity,
               c.sample_count
        FROM correlation_metrics c
        JOIN locations l ON c.location_id = l.id
        WHERE l.city_name = :city
        ORDER BY c.computed_at DESC
        LIMIT 1
    """)
    result = await db.execute(q, {"city": city})
    row = result.fetchone()
    if not row:
        return {"message": "No correlation data yet"}
    return dict(row._mapping)
