"""FarmerMarketFollow model for farmer-followed APMC Mandis."""
from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import DateTime, ForeignKey, Index, UniqueConstraint, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.market.models.market import Market
    from app.models.user_profile import UserProfile


class FarmerMarketFollow(Base):
    """Bookmark / follow relationship between a farmer and an APMC Mandi."""

    __tablename__ = "farmer_market_follows"

    __table_args__ = (
        UniqueConstraint("farmer_id", "market_id", name="uq_farmer_market_follow"),
        Index("ix_farmer_market_follows_farmer", "farmer_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        doc="Reference to the farmer who followed this mandi",
    )
    market_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("markets.id", ondelete="CASCADE"),
        nullable=False,
        doc="Reference to the followed APMC Mandi",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    farmer: Mapped["UserProfile"] = relationship("UserProfile")
    market: Mapped["Market"] = relationship("Market", back_populates="follows")

    def __repr__(self) -> str:
        return f"<FarmerMarketFollow(farmer='{self.farmer_id}', market='{self.market_id}')>"
