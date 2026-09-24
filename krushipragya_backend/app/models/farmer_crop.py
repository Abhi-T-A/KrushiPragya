from datetime import datetime
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import (
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Numeric,
    UniqueConstraint,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user_profile import UserProfile
    from app.models.crop import Crop
    from app.models.crop_report import CropReport


class FarmerCrop(Base):
    """Model representing crops cultivated by a farmer."""

    __tablename__ = "farmer_crops"

    __table_args__ = (
        UniqueConstraint("farmer_id", "crop_id", name="uq_farmer_crops_farmer_crop"),
        CheckConstraint("area_acres >= 0", name="ck_farmer_crops_area_acres_non_negative"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        doc="Primary key unique identifier for farmer-crop relationship",
    )
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key referencing user_profiles.id with cascading delete",
    )
    crop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("crops.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Foreign key referencing crops.id with restricted delete",
    )
    area_acres: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        doc="Cultivated area in acres (non-negative)",
    )
    is_primary: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        server_default=text("false"),
        doc="Flag indicating if this is the farmer's primary cultivated crop",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when relationship was created",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when relationship was last updated",
    )

    # Relationships
    farmer: Mapped["UserProfile"] = relationship(
        "UserProfile",
        back_populates="farmer_crops",
    )
    crop: Mapped["Crop"] = relationship(
        "Crop",
        back_populates="farmer_crops",
    )
    crop_reports: Mapped[List["CropReport"]] = relationship(
        "CropReport",
        back_populates="farmer_crop",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<FarmerCrop(farmer_id={self.farmer_id}, crop_id={self.crop_id}, is_primary={self.is_primary})>"
