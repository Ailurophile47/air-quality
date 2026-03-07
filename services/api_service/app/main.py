from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from .routes import health, aqi, dashboard

app = FastAPI(title="Urban Air Quality API")

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins (dev environment)
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(health.router)
app.include_router(aqi.router)
app.include_router(dashboard.router)