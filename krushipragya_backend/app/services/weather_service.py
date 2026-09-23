import logging
from typing import Optional, Tuple
from sqlalchemy.orm import Session

from app.models.weather_observation import WeatherObservation
from app.schemas.weather import WeatherData
from app.services.weather_provider import (
    WeatherProvider,
    get_weather_provider,
)

logger = logging.getLogger(__name__)


class WeatherService:
    """Service layer managing weather data fetching, normalization, and persistence."""

    def __init__(self, provider: Optional[WeatherProvider] = None):
        self.provider = provider or get_weather_provider()

    def fetch_weather(self, latitude: float, longitude: float) -> WeatherData:
        """Fetch normalized weather data from the provider without database interaction.

        Args:
            latitude: Latitude of location
            longitude: Longitude of location

        Returns:
            WeatherData: Normalized weather schema
        """
        logger.info("Fetching weather for coordinates (lat=%s, lon=%s)", latitude, longitude)
        return self.provider.get_current_weather(latitude, longitude)

    def to_orm(self, village_id: str, data: WeatherData) -> WeatherObservation:
        """Convert normalized WeatherData schema into a WeatherObservation ORM model instance.

        Args:
            village_id: Village ID foreign key
            data: Normalized WeatherData

        Returns:
            WeatherObservation: Uncommitted ORM instance
        """
        return WeatherObservation(
            village_id=village_id,
            observed_at=data.observed_at,
            temperature_c=data.temperature_c,
            humidity_pct=data.humidity_pct,
            rainfall_mm=data.rainfall_mm,
            wind_speed_kmh=data.wind_speed_kmh,
            wind_direction_deg=data.wind_direction_deg,
            pressure_hpa=data.pressure_hpa,
            cloud_cover_pct=data.cloud_cover_pct,
            weather_condition=data.weather_condition,
            source=data.source,
        )

    def save_observation(
        self,
        db: Session,
        village_id: str,
        data: WeatherData,
    ) -> WeatherObservation:
        """Convert normalized weather data and persist to the database.

        Applies an application-level duplicate guard based on:
        village_id + observed_at + source.

        Args:
            db: SQLAlchemy session
            village_id: Village ID
            data: Normalized WeatherData

        Returns:
            WeatherObservation: Persisted ORM instance
        """
        # Application-level duplicate guard (safe without schema changes)
        existing = (
            db.query(WeatherObservation)
            .filter(
                WeatherObservation.village_id == village_id,
                WeatherObservation.observed_at == data.observed_at,
                WeatherObservation.source == data.source,
            )
            .first()
        )
        if isinstance(existing, WeatherObservation):
            logger.info(
                "Existing observation %s found for village %s at %s (source=%s). Returning existing record.",
                existing.id,
                village_id,
                data.observed_at,
                data.source,
            )
            return existing

        observation = self.to_orm(village_id=village_id, data=data)
        db.add(observation)
        db.commit()
        db.refresh(observation)
        logger.info(
            "Saved weather observation %s for village %s (source=%s)",
            observation.id,
            village_id,
            observation.source,
        )
        return observation

    def get_and_record_weather(
        self,
        db: Session,
        village_id: str,
        latitude: float,
        longitude: float,
        persist: bool = True,
    ) -> Tuple[WeatherData, Optional[WeatherObservation]]:
        """Fetch weather and optionally persist it to the database for the given village.

        Args:
            db: SQLAlchemy database session
            village_id: Identifier of the village
            latitude: Village latitude coordinate
            longitude: Village longitude coordinate
            persist: Whether to commit observation to database (default: True)

        Returns:
            Tuple of (WeatherData, Optional[WeatherObservation])
        """
        weather_data = self.fetch_weather(latitude, longitude)
        observation: Optional[WeatherObservation] = None

        if persist:
            observation = self.save_observation(db=db, village_id=village_id, data=weather_data)

        return weather_data, observation
