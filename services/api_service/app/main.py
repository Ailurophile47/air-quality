from fastapi import FastAPI
from .routes import health, aqi

app = FastAPI(title="Urban Air Quality API")

app.include_router(health.router)
app.include_router(aqi.router)