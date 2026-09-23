from datetime import datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
import uuid

from sqlalchemy import (
    CheckConstraint,
    DateTime,
    ForeignKey,
    Index,
    Numeric,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.village import Village


class WeatherObservation(Base):
    """Normalized weather observations for a village."""

    __tablename__ = "weather_observations"

    __table_args__ = (
        CheckConstraint(
            "humidity_pct >= 0 AND humidity_pct <= 100",
            name="ck_weather_observations_humidity_pct",
        ),
        CheckConstraint(
            "rainfall_mm >= 0",
            name="ck_weather_observations_rainfall_mm",
        ),
        CheckConstraint(
            "wind_speed_kmh >= 0",
            name="ck_weather_observations_wind_speed_kmh",
        ),
        CheckConstraint(
            "wind_direction_deg >= 0 AND wind_direction_deg <= 360",
            name="ck_weather_observations_wind_direction_deg",
        ),
        CheckConstraint(
            "pressure_hpa > 0",
            name="ck_weather_observations_pressure_hpa",
        ),
        CheckConstraint(
            "cloud_cover_pct >= 0 AND cloud_cover_pct <= 100",
            name="ck_weather_observations_cloud_cover_pct",
        ),
        Index(
            "ix_weather_observations_village_id_observed_at",
            "village_id",
            "observed_at",
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        doc="Primary key unique identifier for observation",
    )
    village_id: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("villages.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key referencing public.villages(id)",
    )
    observed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        nullable=False,
        index=True,
        doc="Timestamp of weather observation with timezone",
    )
    temperature_c: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Observed ambient temperature in Celsius",
    )
    humidity_pct: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Relative humidity percentage (0-100)",
    )
    rainfall_mm: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(8, 2),
        nullable=True,
        doc="Observed rainfall accumulation in mm (>= 0)",
    )
    wind_speed_kmh: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(7, 2),
        nullable=True,
        doc="Wind speed in km/h (>= 0)",
    )
    wind_direction_deg: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(6, 2),
        nullable=True,
        doc="Wind direction in degrees (0-360)",
    )
    pressure_hpa: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(7, 2),
        nullable=True,
        doc="Barometric atmospheric pressure in hPa (> 0)",
    )
    cloud_cover_pct: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(5, 2),
        nullable=True,
        doc="Cloud cover percentage (0-100)",
    )
    weather_condition: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Descriptive weather condition string (e.g. Sunny, Heavy Rain)",
    )
    source: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Data source provider name",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of observation record creation",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp of observation record last update",
    )

    # Relationships
    village: Mapped["Village"] = relationship(
        "Village",
        back_populates="weather_observations",
    )

    def __repr__(self) -> str:
        return f"<WeatherObservation(id={self.id}, village_id='{self.village_id}', observed_at={self.observed_at}, condition='{self.weather_condition}')>"
