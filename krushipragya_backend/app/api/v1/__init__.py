"""API v1 routers."""
from app.api.v1.health import router as health_router
from app.api.v1.weather import router as weather_router

__all__ = ["health_router", "weather_router"]
