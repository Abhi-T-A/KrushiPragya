"""MarketDataSource model representing official market price provenance."""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, DateTime, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.market.models.market_price import MarketPriceRecord


class MarketDataSource(Base):
    """Catalog of official data sources providing market and price provenance."""

    __tablename__ = "market_data_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        doc="Primary key unique identifier for data source",
    )
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique machine code for source (e.g. OGD_INDIA, AGMARKNET, ENAM)",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Human-readable name of the authority/platform",
    )
    source_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="GOVERNMENT_OGD",
        server_default="GOVERNMENT_OGD",
        doc="Type category: GOVERNMENT_OGD, AGMARKNET_PORTAL, ENAM_PORTAL",
    )
    base_url: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Upstream API endpoint or portal URL",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
        doc="Whether this data source is actively polled",
    )
    is_demo: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False,
        doc="Whether this data source provides benchmark demo seeded data rather than live feeds",
    )
    data_mode: Mapped[str] = mapped_column(
        String(20),
        default="LIVE",
        server_default="LIVE",
        nullable=False,
        doc="Data mode: LIVE or DEMO_SEEDED",
    )
    last_success_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of last successful data ingestion",
    )
    last_failure_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of last ingestion failure",
    )
    last_sync_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when ingestion was last executed",
    )
    sync_status: Mapped[str] = mapped_column(
        String(50),
        default="IDLE",
        server_default="IDLE",
        nullable=False,
        doc="Current status: IDLE, SYNCING, SUCCESS, FAILED, STALE",
    )
    last_error: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Error message from last failed ingestion run",
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
        back_populates="source",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<MarketDataSource(code='{self.code}', sync_status='{self.sync_status}')>"
