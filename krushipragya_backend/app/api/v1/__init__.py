"""API v1 routers."""
from app.api.v1.health import router as health_router
from app.api.v1.weather import router as weather_router
from app.api.v1.disease import router as disease_router
from app.api.v1.farmer import router as farmer_router
from app.api.v1.farmer_crop import router as farmer_crop_router
from app.api.v1.crop_report import router as crop_report_router

__all__ = [
    "health_router",
    "weather_router",
    "disease_router",
    "farmer_router",
    "farmer_crop_router",
    "crop_report_router",
]
