"""SQLAlchemy database models for KrushiPragya."""
from app.models.village import Village
from app.models.user_profile import UserProfile
from app.models.crop import Crop
from app.models.farmer_crop import FarmerCrop
from app.models.weather_observation import WeatherObservation
from app.models.advisory_rule import AdvisoryRule

__all__ = [
    "Village",
    "UserProfile",
    "Crop",
    "FarmerCrop",
    "WeatherObservation",
    "AdvisoryRule",
]


