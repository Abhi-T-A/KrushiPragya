"""ORM model for persisted production farmer advisories."""
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional
import uuid

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    JSON,
    String,
    Text,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class FarmerAdvisory(Base):
    """ORM mapping for persisted farmer advisories tracking evidence, validity, and status."""

    __tablename__ = "farmer_advisories"

    __table_args__ = (
        Index("ix_farmer_advisories_farmer_status", "farmer_id", "status"),
        Index("ix_farmer_advisories_crop_status", "crop_code", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        doc="Primary key unique identifier for farmer advisory",
    )
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key referencing user_profiles.id",
    )
    crop_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("farmer_crops.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Optional foreign key referencing farmer_crops.id",
    )
    crop_code: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Target crop code (e.g. arecanut)",
    )
    village_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        doc="Associated village identifier",
    )
    risk_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="INFO",
        doc="Overall risk severity: CRITICAL, HIGH, MODERATE, LOW, INFO",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="English title of the advisory",
    )
    title_kn: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Farmer-friendly Kannada title",
    )
    summary: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Advisory summary in English or synthesized text",
    )
    summary_kn: Mapped[Optional[Text]] = mapped_column(
        Text,
        nullable=True,
        doc="Farmer-friendly Kannada advisory summary",
    )
    reason: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Meteorological or crop diagnostic reasons triggering advisory",
    )
    recommended_actions: Mapped[List[str]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        doc="List of approved plain-text action strings",
    )
    structured_actions: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        doc="Structured actions with action_kn, priority, and time_window",
    )
    evidence: Mapped[List[Dict[str, Any]]] = mapped_column(
        JSON,
        nullable=False,
        default=list,
        doc="Audit trail of rule matches, weather observations, and disease diagnosis",
    )
    confidence_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="HIGH",
        doc="Confidence level: HIGH, MEDIUM, LOW, INSUFFICIENT_DATA",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="ACTIVE",
        index=True,
        doc="Lifecycle status: ACTIVE, EXPIRED, SUPERSEDED",
    )
    fingerprint: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        doc="SHA256 fingerprint for duplicate detection and caching",
    )
    is_llm_generated: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Whether the advisory summary was synthesized via LLM",
    )
    valid_from: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp from which the advisory is valid",
    )
    valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp until which the advisory remains valid",
    )
    weather_observed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of weather observation or forecast anchor",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Record creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Record update timestamp",
    )

    def __repr__(self) -> str:
        return (
            f"<FarmerAdvisory(id={self.id}, farmer_id={self.farmer_id}, "
            f"crop_code='{self.crop_code}', risk_level='{self.risk_level}', status='{self.status}')>"
        )
