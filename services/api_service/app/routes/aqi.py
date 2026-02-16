from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from ..database import AsyncSessionLocal
from sqlalchemy import text

router = APIRouter()

async def get_db():
    async with AsyncSessionLocal() as session:
        yield session

# -------- Latest AQI --------
@router.get("/aqi/latest")
async def get_latest(city: str, db: AsyncSession = Depends(get_db)):
    query = text("""
        SELECT a.*
        FROM aqi_measurements a
        JOIN locations l ON a.location_id = l.id
        WHERE l.city_name = :city
        ORDER BY recorded_at DESC
        LIMIT 1
    """)
    result = await db.execute(query, {"city": city})
    row = result.fetchone()

    if not row:
        return {"message": "No data found"}

    return dict(row._mapping)


@router.get("/aqi/history")
async def get_history(
    city: str,
    limit: int = 50,
    offset: int = 0,
    db: AsyncSession = Depends(get_db)
):
    limit = min(limit, 500)

    query = text("""
        SELECT a.*
        FROM aqi_measurements a
        JOIN locations l ON a.location_id = l.id
        WHERE l.city_name = :city
        ORDER BY recorded_at DESC
        LIMIT :limit OFFSET :offset
    """)

    result = await db.execute(query, {
        "city": city,
        "limit": limit,
        "offset": offset
    })

    rows = result.fetchall()
    return [dict(row._mapping) for row in rows]