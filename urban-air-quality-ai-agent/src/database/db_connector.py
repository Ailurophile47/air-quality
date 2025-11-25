"""
Database Connection Management - Urban Air Quality AI Agent
===========================================================

This module handles all PostgreSQL database connectivity and session management.

KEY CONCEPTS:
1. Connection Pooling: Instead of creating a new connection for each request,
   maintain a pool of reusable connections for performance
2. Session Management: Each request gets a session (connection + transaction scope)
3. ORM Base: All database models inherit from Base to enable automatic table creation

CONNECTION FLOW:
  FastAPI Request → get_db() → SessionLocal() → PostgreSQL Pool → get free connection
                    ↓ (query executed) ↓
  Response sent ← db.close() ← connection returned to pool

ARCHITECTURE PATTERN:
This uses Dependency Injection (FastAPI's Depends) to provide sessions automatically
to each endpoint. FastAPI automatically calls get_db() and closes the session after.

PERFORMANCE TUNING:
- pool_size=10: Keep 10 idle connections ready
- max_overflow=20: Allow up to 20 extra connections if needed (total 30 max)
- pool_pre_ping=True: Verify each connection before using (prevents stale connections)
"""

import os
from contextlib import contextmanager
from typing import Generator

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import QueuePool

# Load environment variables from .env file
# This reads POSTGRES_HOST, POSTGRES_USER, POSTGRES_PASSWORD, POSTGRES_DB, POSTGRES_PORT
load_dotenv()

# ============================================================================
# BUILD DATABASE CONNECTION URL
# ============================================================================
# PostgreSQL connection string format: postgresql://user:password@host:port/database
# Example: postgresql://airflow:8520@localhost:5432/airflow

password = os.getenv('POSTGRES_PASSWORD', '')
# Only add password segment if password exists (handles no-auth scenarios)
password_part = f":{password}@" if password else "@"

DATABASE_URL = (
    f"postgresql://{os.getenv('POSTGRES_USER', 'airquality')}"  # User: read from .env or default
    f"{password_part}"  # Password segment: optional
    f"{os.getenv('POSTGRES_HOST', 'localhost')}:"  # Host: where PostgreSQL is running
    f"{os.getenv('POSTGRES_PORT', '5432')}/"  # Port: default 5432
    f"{os.getenv('POSTGRES_DB', 'urban_air_quality')}"  # Database name
)

print(f"🔌 Connecting to: postgresql://***@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'urban_air_quality')}")


# ============================================================================
# CREATE DATABASE ENGINE (Connection Pool)
# ============================================================================
# The engine is the core SQLAlchemy object that manages database connections
# QueuePool manages a queue of connections for reuse across requests

engine = create_engine(
    DATABASE_URL,
    poolclass=QueuePool,  # Use queue-based connection pooling
    pool_size=10,  # Number of idle connections to maintain (pre-allocated)
    max_overflow=20,  # Additional connections allowed when pool exhausted
    # Total possible connections = 10 + 20 = 30
    pool_pre_ping=True,  # IMPORTANT: Verify each connection before using
    # This prevents "server closed connection unexpectedly" errors
    echo=False  # Set to True to see all SQL queries printed to console (debug mode)
)


# ============================================================================
# CREATE SESSION FACTORY
# ============================================================================
# SessionLocal is a factory that creates new Session objects
# Sessions represent a single "conversation" with the database (one connection)

SessionLocal = sessionmaker(
    autocommit=False,  # Don't auto-commit; explicit commit() or rollback() needed
    autoflush=False,   # Don't flush automatically; only flush on commit()
    bind=engine  # Bind this session factory to our connection pool
)


# ============================================================================
# CREATE ORM BASE CLASS
# ============================================================================
# All database model classes (AQIData, WeatherData, etc.) inherit from Base
# Base keeps track of all models and enables automatic table creation

Base = declarative_base()


# ============================================================================
# DATABASE INITIALIZATION
# ============================================================================

def init_db() -> None:
    """
    Initialize database schema by creating all tables
    
    What it does:
    1. Reads all model classes that inherit from Base (in models.py)
    2. For each model, creates a corresponding PostgreSQL table
    3. Creates indexes and constraints as defined in each model
    4. Idempotent: if table exists, it's skipped (no error)
    
    When to call:
    - Application startup (in FastAPI startup event)
    - First time deploying the application
    - After adding new models (migrations for new tables)
    
    Return: None (prints success/failure message)
    """
    try:
        # Create all tables defined in Base.metadata
        # This maps Python classes to SQL CREATE TABLE statements
        Base.metadata.create_all(bind=engine)
        print("✅ Database tables created successfully")
    except Exception as e:
        print(f"❌ Error creating database tables: {e}")
        raise


# ============================================================================
# SESSION DEPENDENCY FOR FASTAPI
# ============================================================================

def get_db() -> Generator[Session, None, None]:
    """
    FastAPI Dependency: Provides a database session to endpoints
    
    This is the "magic function" that FastAPI calls automatically for every
    endpoint that declares: db: Session = Depends(get_db)
    
    FLOW:
    1. FastAPI receives a request for an endpoint using get_db dependency
    2. FastAPI calls get_db() to get a session
    3. get_db() creates a SessionLocal() instance (gets connection from pool)
    4. Session passed to the endpoint handler
    5. Endpoint queries database using: db.query(Model).filter(...).all()
    6. Response sent back
    7. finally block executes: db.close() (returns connection to pool)
    
    EXAMPLE USAGE in API endpoint:
    ```python
    @app.get("/aqi/latest")
    def get_aqi_latest(limit: int = 5, db: Session = Depends(get_db)):
        # db is automatically provided by FastAPI
        records = db.query(AQIData).limit(limit).all()
        return records
    ```
    
    Return: Generator that yields a Session, then cleans up
    """
    db = SessionLocal()  # Get a new session from the pool
    try:
        yield db  # Provide session to the endpoint
    finally:
        db.close()  # Always close (even if endpoint had exception)


# ============================================================================
# CONTEXT MANAGER FOR MANUAL SESSION MANAGEMENT
# ============================================================================

@contextmanager
def get_db_session() -> Generator[Session, None, None]:
    """
    Context manager for database sessions (manual approach)
    
    Use this when you need fine control over commit/rollback outside FastAPI.
    Automatically handles transaction management.
    
    EXAMPLE USAGE:
    ```python
    # In a Kafka consumer or background job
    with get_db_session() as session:
        new_aqi = AQIData(location="delhi", aqi=150, timestamp=datetime.now())
        session.add(new_aqi)
        # Auto-commits here on exit
    ```
    
    BEHAVIOR:
    - On success: Auto-commits all changes
    - On exception: Auto-rollbacks (discards changes)
    - Always: Closes connection and returns to pool
    
    Return: Generator that yields a Session with transaction management
    """
    session = SessionLocal()
    try:
        yield session
        session.commit()  # Commit all changes if no exception
    except Exception:
        session.rollback()  # Undo changes if exception occurred
        raise  # Re-raise the exception
    finally:
        session.close()  # Always close connection


# ============================================================================
# CONNECTION TESTING
# ============================================================================

def test_connection() -> bool:
    """
    Test database connectivity
    
    What it does:
    1. Attempts to get a connection from the pool
    2. Executes simple query: SELECT 1 (returns 1 if working)
    3. Returns True if successful, False if fails
    
    When to call:
    - Application startup to verify configuration
    - Health check endpoints
    - Troubleshooting database issues
    
    Example Output:
    ✅ Database connection successful
    OR
    ❌ Database connection failed: connection refused
    
    Return: True if successful, False if failed
    """
    try:
        with engine.connect() as conn:
            # text() allows raw SQL strings
            result = conn.execute(text("SELECT 1"))
            result.fetchone()  # Actually fetch the result
        print("✅ Database connection successful")
        return True
    except Exception as e:
        print(f"❌ Database connection failed: {e}")
        return False


# ============================================================================
# MAIN: STANDALONE TESTING
# ============================================================================

if __name__ == "__main__":
    """
    This block runs when db_connector.py is executed directly (not imported)
    
    Usage: python -m src.database.db_connector
    
    Tests the database connection without starting the FastAPI server
    Useful for debugging connectivity issues
    """
    print(f"🔧 Testing connection to: postgresql://***@{os.getenv('POSTGRES_HOST', 'localhost')}:{os.getenv('POSTGRES_PORT', '5432')}/{os.getenv('POSTGRES_DB', 'urban_air_quality')}")
    test_connection()