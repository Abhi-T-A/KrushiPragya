"""MarketPriceRecord model storing factual official mandi prices."""
from datetime import date, datetime
from decimal import Decimal
from typing import Optional, TYPE_CHECKING
import uuid

from sqlalchemy import Date, DateTime, ForeignKey, Index, Numeric, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.market.models.market import Market
    from app.market.models.market_source import MarketDataSource
    from app.models.crop import Crop


class MarketPriceRecord(Base):
    """Factual market price record reported by APMC Mandis via official government portals.

    Stores minimum, maximum, and modal price plus arrivals.
    Never mixed with farmer expected prices or buyer offers.
    """

    __tablename__ = "market_price_records"

    __table_args__ = (
        UniqueConstraint(
            "market_id",
            "crop_id",
            "arrival_date",
            "variety",
            "grade",
            name="uq_market_price_unique_arrival",
        ),
        Index("ix_market_prices_crop_date", "crop_id", "arrival_date"),
        Index("ix_market_prices_market_date", "market_id", "arrival_date"),
        Index("ix_market_prices_arrival_date", "arrival_date"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    market_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("markets.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to the APMC Mandi",
    )
    crop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("crops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to canonical KrushiPragya crop",
    )
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("market_data_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Reference to the provenance data source",
    )
    source_record_id: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        doc="Upstream unique record ID if supplied by API",
    )
    arrival_date: Mapped[date] = mapped_column(
        Date,
        nullable=False,
        doc="Official date of market arrivals and price quotation",
    )
    commodity_raw: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Original commodity name reported by mandi",
    )
    variety: Mapped[str] = mapped_column(
        String(100),
        default="Standard",
        server_default="Standard",
        nullable=False,
        doc="Reported variety (e.g. Bette, Rasi, Chali)",
    )
    grade: Mapped[str] = mapped_column(
        String(50),
        default="FAQ",
        server_default="FAQ",
        nullable=False,
        doc="Reported quality grade (e.g. FAQ, Medium, Grade A)",
    )
    min_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        doc="Reported minimum price in INR (₹) per unit",
    )
    max_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        doc="Reported maximum price in INR (₹) per unit",
    )
    modal_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        doc="Reported modal (most frequent) price in INR (₹) per unit",
    )
    arrival_quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        default=0.0,
        server_default="0.0",
        nullable=False,
        doc="Arrival volume / quantity reported",
    )
    unit: Mapped[str] = mapped_column(
        String(20),
        default="Quintal",
        server_default="Quintal",
        nullable=False,
        doc="Pricing unit (typically Quintal = 100 kg, or Thousand for Coconut)",
    )
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when record was ingested from source",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    market: Mapped["Market"] = relationship("Market", back_populates="price_records")
    crop: Mapped["Crop"] = relationship("Crop")
    source: Mapped[Optional["MarketDataSource"]] = relationship("MarketDataSource", back_populates="price_records")

    def __repr__(self) -> str:
        return f"<MarketPriceRecord(market='{self.market_id}', crop='{self.crop_id}', modal={self.modal_price}, date={self.arrival_date})>"
