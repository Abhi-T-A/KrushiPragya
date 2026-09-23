from datetime import datetime
from typing import List, TYPE_CHECKING
import uuid

from sqlalchemy import String, Boolean, DateTime, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.farmer_crop import FarmerCrop


class Crop(Base):
    """Canonical crop catalog model representing crops across KrushiPragya."""

    __tablename__ = "crops"

    __table_args__ = (
        UniqueConstraint("code", name="uq_crops_code"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        doc="Primary key unique identifier for the crop",
    )
    code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        unique=True,
        index=True,
        doc="Canonical machine-readable identifier (e.g. arecanut, paddy)",
    )
    name_en: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="English display name of the crop",
    )
    name_kn: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Kannada display name of the crop",
    )
    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        server_default=text("true"),
        doc="Flag indicating if crop is actively supported",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of crop record creation",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp of last update to crop record",
    )

    # Relationships
    farmer_crops: Mapped[List["FarmerCrop"]] = relationship(
        "FarmerCrop",
        back_populates="crop",
    )

    def __repr__(self) -> str:
        return f"<Crop(code='{self.code}', name_en='{self.name_en}', name_kn='{self.name_kn}')>"
