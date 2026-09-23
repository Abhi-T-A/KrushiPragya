from datetime import datetime, timezone
import logging
from typing import Optional
from sqlalchemy.orm import Session

from app.models.village import Village
from app.schemas.weather import ForecastData
from app.services.weather_advisory_service import VillageNotFoundError
from app.services.weather_provider import (
    ForecastProvider,
    WeatherProviderError,
    get_weather_provider,
)

logger = logging.getLogger(__name__)


class WeatherForecastService:
    """Service layer managing weather forecast retrieval for villages."""

    def __init__(self, provider: Optional[ForecastProvider] = None):
        self.provider = provider or get_weather_provider()

    def get_forecast(
        self,
        db: Session,
        village_id: str,
    ) -> list[ForecastData]:
        """Retrieve normalized 5-day / 3-hour weather forecast points for a village.

        Workflow:
            1. Validate village existence via authoritative database lookup.
            2. Extract authoritative village latitude and longitude.
            3. Call configured ForecastProvider with village coordinates.
            4. Return sequence of normalized ForecastData objects.

        Args:
            db: SQLAlchemy session.
            village_id: Canonical village identifier (e.g. V001).

        Returns:
            list[ForecastData]: Chronological sequence of forecast items.

        Raises:
            VillageNotFoundError: When village_id is not found in villages table.
            WeatherProviderError: When external weather provider fails or returns malformed payload.
        """
        clean_id = village_id.strip()
        village = db.get(Village, clean_id)
        if not village:
            logger.warning("Forecast lookup failed: Village '%s' not found.", clean_id)
            raise VillageNotFoundError(f"Village '{clean_id}' not found.")

        latitude = float(village.latitude)
        longitude = float(village.longitude)

        logger.info(
            "Fetching forecast for village %s at coordinates (lat=%s, lon=%s)",
            clean_id,
            latitude,
            longitude,
        )
        return self.provider.get_forecast(latitude, longitude)
