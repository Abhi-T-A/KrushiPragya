from datetime import datetime
from typing import List, TYPE_CHECKING

from sqlalchemy import String, Float, DateTime, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user_profile import UserProfile
    from app.models.weather_observation import WeatherObservation


class Village(Base):
    """Canonical village master model mapped to existing public.villages table."""

    __tablename__ = "villages"

    id: Mapped[str] = mapped_column(
        String(50),
        primary_key=True,
        doc="Unique identifier code for the village (e.g. V001)",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Village name",
    )
    district: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="District name",
    )
    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="State name",
    )
    zone: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Agro-climatic zone name",
    )
    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Geographic latitude coordinate",
    )
    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Geographic longitude coordinate",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Record creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Record last update timestamp",
    )

    # Relationships
    user_profiles: Mapped[List["UserProfile"]] = relationship(
        "UserProfile",
        back_populates="village",
    )
    weather_observations: Mapped[List["WeatherObservation"]] = relationship(
        "WeatherObservation",
        back_populates="village",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Village(id='{self.id}', name='{self.name}', district='{self.district}', zone='{self.zone}')>"
