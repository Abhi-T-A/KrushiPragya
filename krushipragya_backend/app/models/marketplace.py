"""ProduceListing and BuyerOffer models for the KrushiPragya Marketplace."""
from datetime import datetime
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, Index, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.crop import Crop
    from app.models.user_profile import UserProfile


class ProduceListing(Base):
    """Farmer-created produce listing offering harvest produce to buyers."""

    __tablename__ = "produce_listings"

    __table_args__ = (
        Index("ix_produce_listings_farmer_status", "farmer_id", "status"),
        Index("ix_produce_listings_crop_status", "crop_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        doc="Primary key identifier for the produce listing",
    )
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to the farmer who owns this listing",
    )
    crop_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("crops.id", ondelete="RESTRICT"),
        nullable=False,
        index=True,
        doc="Foreign key to the crop commodity",
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        doc="Available quantity for sale",
    )
    unit: Mapped[str] = mapped_column(
        String(20),
        default="kg",
        server_default="kg",
        nullable=False,
        doc="Unit of quantity measurement (kg, quintal, bag, tonne)",
    )
    quality_grade: Mapped[str] = mapped_column(
        String(20),
        default="A",
        server_default="A",
        nullable=False,
        doc="Quality grade designation (e.g. A, B, Premium, Grade 1)",
    )
    expected_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        doc="Expected asking price per unit in INR (₹)",
    )
    location: Mapped[str] = mapped_column(
        String(200),
        nullable=False,
        doc="Pickup location / village name",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="LISTED",
        server_default="LISTED",
        nullable=False,
        index=True,
        doc="Listing status: LISTED, OFFER_RECEIVED, NEGOTIATING, SOLD, DELISTED",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of listing creation",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp of last listing update",
    )

    # Relationships
    farmer: Mapped["UserProfile"] = relationship(
        "UserProfile",
        foreign_keys=[farmer_id],
    )
    crop: Mapped["Crop"] = relationship(
        "Crop",
    )
    offers: Mapped[List["BuyerOffer"]] = relationship(
        "BuyerOffer",
        back_populates="listing",
        cascade="all, delete-orphan",
        order_by="BuyerOffer.created_at.desc()",
    )

    def __repr__(self) -> str:
        return f"<ProduceListing(id={self.id}, farmer_id={self.farmer_id}, crop_id={self.crop_id}, status='{self.status}')>"


class BuyerOffer(Base):
    """Purchase offer submitted by a buyer/trader on a farmer's produce listing."""

    __tablename__ = "buyer_offers"

    __table_args__ = (
        Index("ix_buyer_offers_listing_buyer", "listing_id", "buyer_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        doc="Primary key unique identifier for buyer offer",
    )
    listing_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("produce_listings.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to the targeted produce listing",
    )
    buyer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to the buyer/trader making the offer",
    )
    offered_price: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        doc="Offered price per unit in INR (₹)",
    )
    quantity: Mapped[Decimal] = mapped_column(
        Numeric(12, 2),
        nullable=False,
        doc="Offered purchase quantity",
    )
    message: Mapped[Optional[str]] = mapped_column(
        String(500),
        nullable=True,
        doc="Optional note or negotiation message from buyer",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING",
        server_default="PENDING",
        nullable=False,
        index=True,
        doc="Status of offer: PENDING, NEGOTIATING, ACCEPTED, REJECTED, COMPLETED",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when offer was submitted",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp when offer was last updated",
    )

    # Relationships
    listing: Mapped["ProduceListing"] = relationship(
        "ProduceListing",
        back_populates="offers",
    )
    buyer: Mapped["UserProfile"] = relationship(
        "UserProfile",
        foreign_keys=[buyer_id],
    )

    def __repr__(self) -> str:
        return f"<BuyerOffer(id={self.id}, listing_id={self.listing_id}, buyer_id={self.buyer_id}, status='{self.status}')>"
