"""Models for Agriculture Expert Verification and Community Corroboration."""
from datetime import datetime
from typing import Optional, TYPE_CHECKING
import uuid

from sqlalchemy import DateTime, Float, ForeignKey, Index, Numeric, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.crop_report import CropReport
    from app.models.user_profile import UserProfile
    from app.models.village import Village


class ExpertVerificationRequest(Base):
    """Relationship-based expert verification request for a farmer's crop report."""

    __tablename__ = "expert_verification_requests"

    __table_args__ = (
        Index("ix_expert_verifications_expert_status", "expert_id", "status"),
        Index("ix_expert_verifications_report_status", "crop_report_id", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        doc="Primary key identifier for the verification request",
    )
    crop_report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("crop_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to the crop report being verified",
    )
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to the farmer who owns the report",
    )
    expert_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Assigned Agriculture Expert user ID (null if in unassigned queue)",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="PENDING",
        server_default="PENDING",
        nullable=False,
        index=True,
        doc="Lifecycle status: PENDING, ASSIGNED, IN_REVIEW, VERIFIED, REJECTED, NEED_MORE_INFO",
    )
    action_type: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        doc="Expert decision action: CONFIRM, CORRECT, NEED_MORE_INFO",
    )
    finding: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Expert's confirmed or corrected disease / condition name",
    )
    expert_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Detailed expert clinical/field observations and diagnosis explanation",
    )
    recommended_action: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Expert recommendation, treatment advisory, or chemical/organic remedy instructions",
    )
    requested_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when verification was requested",
    )
    assigned_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when an expert was assigned or claimed this request",
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when expert finalized the verification",
    )
    payment_status: Mapped[Optional[str]] = mapped_column(
        String(50),
        default="SUCCESS",
        server_default="SUCCESS",
        nullable=True,
        doc="Payment status: SUCCESS, PENDING, FAILED",
    )
    payment_mode: Mapped[Optional[str]] = mapped_column(
        String(50),
        default="DEMO",
        server_default="DEMO",
        nullable=True,
        doc="Payment mode: DEMO",
    )
    payment_amount: Mapped[Optional[float]] = mapped_column(
        Numeric(10, 2),
        default=49.00,
        nullable=True,
        doc="Review fee in INR",
    )
    crop: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Crop name (e.g. Arecanut, Paddy)",
    )
    diagnosis: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Diagnosed condition / disease name",
    )
    ai_confidence: Mapped[Optional[float]] = mapped_column(
        Float,
        nullable=True,
        doc="AI confidence score between 0.0 and 1.0",
    )

    # Relationships
    crop_report: Mapped["CropReport"] = relationship(
        "CropReport",
    )
    farmer: Mapped["UserProfile"] = relationship(
        "UserProfile",
        foreign_keys=[farmer_id],
    )
    expert: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile",
        foreign_keys=[expert_id],
    )

    def __repr__(self) -> str:
        return f"<ExpertVerificationRequest(id={self.id}, report={self.crop_report_id}, expert={self.expert_id}, status='{self.status}')>"


class CommunityCorroboration(Base):
    """Community-contributed symptom and pest corroboration for a crop report."""

    __tablename__ = "community_corroborations"

    __table_args__ = (
        Index("ix_corroborations_report_member", "crop_report_id", "community_member_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        doc="Primary key unique identifier for corroboration",
    )
    crop_report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("crop_reports.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to the crop report being corroborated",
    )
    community_member_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key to the community member submitting observation",
    )
    observation_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Type of corroboration: SAME_SYMPTOMS, SEEN_NEARBY, NOT_MATCHING",
    )
    notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Community member observations or notes",
    )
    village_id: Mapped[Optional[str]] = mapped_column(
        String(50),
        ForeignKey("villages.id", ondelete="SET NULL"),
        nullable=True,
        doc="Optional village context of the observer",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of community corroboration",
    )

    # Relationships
    crop_report: Mapped["CropReport"] = relationship(
        "CropReport",
    )
    community_member: Mapped["UserProfile"] = relationship(
        "UserProfile",
        foreign_keys=[community_member_id],
    )
    village: Mapped[Optional["Village"]] = relationship(
        "Village",
    )

    def __repr__(self) -> str:
        return f"<CommunityCorroboration(id={self.id}, report={self.crop_report_id}, type='{self.observation_type}')>"
