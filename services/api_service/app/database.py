from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
import os

DATABASE_URL = (
    f"postgresql+psycopg://"
    f"{os.getenv('POSTGRES_USER')}:"
    f"{os.getenv('POSTGRES_PASSWORD')}@"
    f"{os.getenv('POSTGRES_HOST')}:"
    f"{os.getenv('POSTGRES_PORT')}/"
    f"{os.getenv('POSTGRES_DB')}"
)

engine = create_async_engine(DATABASE_URL)
AsyncSessionLocal = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)