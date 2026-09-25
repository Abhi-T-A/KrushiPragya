"""Market (APMC Mandi) model for KrushiPragya Market Discovery."""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, DateTime, Float, Index, String, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.market.models.market_follow import FarmerMarketFollow
    from app.market.models.market_price import MarketPriceRecord


class Market(Base):
    """Regulated market yard / APMC Mandi where agricultural commodities are traded."""

    __tablename__ = "markets"

    __table_args__ = (
        Index("ix_markets_state_district", "state", "district"),
        Index("ix_markets_coordinates", "latitude", "longitude"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        doc="Primary key unique identifier for market/mandi",
    )
    code: Mapped[str] = mapped_column(
        String(100),
        unique=True,
        nullable=False,
        index=True,
        doc="Canonical unique identifier code (e.g. KA_DK_MANGALORE)",
    )
    name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        index=True,
        doc="Official Mandi / Market Yard Name",
    )
    state: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="State name (e.g. Karnataka)",
    )
    district: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="District name (e.g. Dakshina Kannada, Uttara Kannada)",
    )
    taluk: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Taluk / sub-district location",
    )
    latitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Geographic latitude coordinate of the market yard",
    )
    longitude: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Geographic longitude coordinate of the market yard",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
        doc="Whether this market is active and reporting prices",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    price_records: Mapped[List["MarketPriceRecord"]] = relationship(
        "MarketPriceRecord",
        back_populates="market",
        cascade="all, delete-orphan",
    )
    follows: Mapped[List["FarmerMarketFollow"]] = relationship(
        "FarmerMarketFollow",
        back_populates="market",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Market(code='{self.code}', name='{self.name}', district='{self.district}')>"
