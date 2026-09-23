from datetime import datetime
from decimal import Decimal
from typing import List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import String, Numeric, DateTime, ForeignKey, Table, Column, func
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

# External Supabase auth.users table representation for foreign key resolution
if "auth.users" not in Base.metadata.tables:
    Table("users", Base.metadata, Column("id", UUID(as_uuid=True), primary_key=True), schema="auth")

if TYPE_CHECKING:
    from app.models.village import Village
    from app.models.farmer_crop import FarmerCrop


class UserProfile(Base):
    """User profile model storing farmer profile metadata linked to Supabase auth.users."""

    __tablename__ = "user_profiles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("auth.users.id", ondelete="CASCADE"),
        primary_key=True,
        doc="User ID referencing Supabase auth.users(id)",
    )
    full_name: Mapped[Optional[str]] = mapped_column(
        String(150),
        nullable=True,
        doc="Full name of the farmer/user",
    )
    phone: Mapped[Optional[str]] = mapped_column(
        String(20),
        nullable=True,
        doc="Contact phone number",
    )
    village_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("villages.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Foreign key referencing public.villages(id)",
    )
    language: Mapped[str] = mapped_column(
        String(5),
        nullable=False,
        default="kn",
        server_default="kn",
        doc="Preferred language code ('kn' or 'en')",
    )
    land_holding_acres: Mapped[Optional[Decimal]] = mapped_column(
        Numeric(10, 2),
        nullable=True,
        doc="Total land holding area in acres",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of profile creation",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp of last profile update",
    )

    # Relationships
    village: Mapped[Optional["Village"]] = relationship(
        "Village",
        back_populates="user_profiles",
    )
    farmer_crops: Mapped[List["FarmerCrop"]] = relationship(
        "FarmerCrop",
        back_populates="farmer",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<UserProfile(id={self.id}, full_name='{self.full_name}', language='{self.language}')>"
