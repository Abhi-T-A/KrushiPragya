from datetime import datetime
from typing import Optional, TYPE_CHECKING
import uuid

from sqlalchemy import (
    DateTime,
    ForeignKey,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.farmer_crop import FarmerCrop


class CropReport(Base):
    """Model representing crop health observations and reports submitted by farmers."""

    __tablename__ = "crop_reports"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        doc="Primary key unique identifier for the crop report",
    )
    farmer_crop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("farmer_crops.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key referencing farmer_crops.id with cascading delete",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        doc="Optional notes or observation text from the farmer (max 1000 chars)",
    )
    image_filename: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Optional original filename of the uploaded image (max 255 chars)",
    )
    image_storage_path: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="Internal reference path to the stored image in storage bucket",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when report was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when report was last updated",
    )

    # Relationships
    farmer_crop: Mapped["FarmerCrop"] = relationship(
        "FarmerCrop",
        back_populates="crop_reports",
    )

    def __repr__(self) -> str:
        return f"<CropReport(id={self.id}, farmer_crop_id={self.farmer_crop_id})>"
