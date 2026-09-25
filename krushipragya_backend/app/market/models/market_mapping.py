"""MarketCropMapping model for controlled commodity normalization."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, String, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.crop import Crop


class MarketCropMapping(Base):
    """Controlled mapping between official upstream commodity names and canonical KrushiPragya crops.

    Prevents blind merging of different varieties (e.g. Tender Coconut vs Copra vs Coconut with Husk).
    """

    __tablename__ = "market_crop_mappings"

    __table_args__ = (
        UniqueConstraint("raw_commodity_name", "variety", name="uq_market_crop_mapping_raw_variety"),
        Index("ix_market_crop_mappings_crop_id", "crop_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    crop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("crops.id", ondelete="CASCADE"),
        nullable=False,
        doc="Reference to canonical KrushiPragya crop",
    )
    canonical_crop_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Canonical machine-readable crop code (e.g. arecanut, paddy, coconut)",
    )
    raw_commodity_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Raw commodity string in OGD/AGMARKNET records",
    )
    variety: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        default=None,
        doc="Specific variety or grade string (or None/empty for all compatible varieties)",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
    )
    notes: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Classification guidelines and documentation",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    crop: Mapped["Crop"] = relationship("Crop")

    def __repr__(self) -> str:
        return f"<MarketCropMapping({self.raw_commodity_name} -> {self.canonical_crop_code})>"
