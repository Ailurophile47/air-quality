from fastapi import APIRouter
from ..database import engine
from sqlalchemy import text

router = APIRouter()

@router.get("/health")
async def health():
    try:
        async with engine.connect() as conn:
            await conn.execute(text("SELECT 1"))
        return {"status": "healthy"}
    except Exception as e:
        return {"status": "unhealthy", "error": str(e)}
    
