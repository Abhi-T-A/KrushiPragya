"""GovernmentScheme and SchemeApplication models for KrushiPragya."""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import Boolean, DateTime, ForeignKey, Index, Integer, String, Text, UniqueConstraint, Uuid, func, text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

# Cross-platform UUID type (compiles to native UUID on PostgreSQL, CHAR(32) on SQLite)
UUID = Uuid

if TYPE_CHECKING:
    from app.models.user_profile import UserProfile


class GovernmentScheme(Base):
    """Agricultural scheme, subsidy, or insurance program from official portals or Government Officers."""

    __tablename__ = "government_schemes"

    __table_args__ = (
        Index("ix_government_schemes_status", "status"),
        Index("ix_government_schemes_category", "category"),
        Index("ix_government_schemes_state", "state"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        doc="Primary key unique identifier for the government scheme",
    )
    published_by: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
        doc="Foreign key to the Government Officer who published this scheme (null if ingested by crawler)",
    )
    title: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Official scheme title (e.g. PM-KISAN, Arecanut Yellow Leaf Disease Relief)",
    )
    title_kn: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Scheme title in Kannada",
    )
    department: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Issuing government department or ministry (e.g. Ministry of Agriculture, Karnataka Agri Dept)",
    )
    state: Mapped[Optional[str]] = mapped_column(
        String(100),
        default="Karnataka",
        server_default="Karnataka",
        nullable=True,
        doc="State or regional jurisdiction (e.g. Karnataka, Central / All India)",
    )
    description: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Detailed explanation of the scheme objective and coverage",
    )
    description_kn: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Detailed description in Kannada",
    )
    category: Mapped[str] = mapped_column(
        String(100),
        default="Subsidy",
        server_default="Subsidy",
        nullable=False,
        doc="Category: Subsidy, Insurance, Equipment, Financial Assistance, Irrigation, Advisory",
    )
    eligibility: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Eligibility criteria in English (land holding, crop type, farmer category)",
    )
    eligibility_kn: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Eligibility criteria in Kannada",
    )
    benefits: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Financial subsidy amount or non-financial benefits provided in English",
    )
    benefits_kn: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Benefits description in Kannada",
    )
    application_process: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Step-by-step application instructions in English",
    )
    application_process_kn: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Step-by-step application instructions in Kannada",
    )
    documents_required: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="List of mandatory documents in English (RTC / Pahani, Aadhaar, Bank passbook)",
    )
    documents_required_kn: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="List of mandatory documents in Kannada",
    )
    application_url: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        doc="Official portal URL for online application or form download",
    )
    source_url: Mapped[Optional[str]] = mapped_column(
        String(1000),
        nullable=True,
        doc="Canonical URL where this scheme was discovered or crawled",
    )
    source_name: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Human-readable source entity (e.g. myScheme, PM-KISAN, Raitha Mitra)",
    )
    source_type: Mapped[Optional[str]] = mapped_column(
        String(100),
        nullable=True,
        doc="Source type: MYSCHEME, CENTRAL_PORTAL, STATE_DEPT, OFFICER_MANUAL",
    )
    source_last_seen_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp when this scheme was last confirmed present on official source",
    )
    source_last_modified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Last-Modified header or timestamp reported by official source",
    )
    content_hash: Mapped[Optional[str]] = mapped_column(
        String(64),
        nullable=True,
        index=True,
        doc="SHA-256 hash of normalized scheme fields for change detection",
    )
    last_crawled_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of the most recent crawl run covering this scheme",
    )
    last_verified_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Timestamp of the most recent successful content verification",
    )
    crawler_status: Mapped[Optional[str]] = mapped_column(
        String(50),
        nullable=True,
        default="VERIFIED",
        server_default="VERIFIED",
        doc="Crawler status: VERIFIED, UPDATED, SOURCE_TEMPORARILY_UNAVAILABLE, PENDING_REVIEW",
    )
    valid_from: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Scheme commencement date",
    )
    valid_until: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="Application deadline date",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="ACTIVE",
        server_default="ACTIVE",
        nullable=False,
        doc="Status: DRAFT, ACTIVE, EXPIRED, ARCHIVED",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of publication or first ingestion",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp of last update or re-crawl",
    )

    # Relationships
    publisher: Mapped[Optional["UserProfile"]] = relationship(
        "UserProfile",
        foreign_keys=[published_by],
    )
    applications: Mapped[List["SchemeApplication"]] = relationship(
        "SchemeApplication",
        back_populates="scheme",
        cascade="all, delete-orphan",
        order_by="SchemeApplication.submitted_at.desc()",
    )

    def __repr__(self) -> str:
        return f"<GovernmentScheme(id={self.id}, title='{self.title}', status='{self.status}')>"


class SchemeSource(Base):
    """Configurable registry of allowlisted official government sources."""

    __tablename__ = "scheme_sources"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    name: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        doc="Human-readable name of the source (e.g. myScheme, PM-KISAN Portal)",
    )
    base_url: Mapped[str] = mapped_column(
        String(1000),
        nullable=False,
        doc="Root URL for the scheme portal",
    )
    domain_allowlist: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="JSON serialized list of approved domain patterns",
    )
    source_type: Mapped[str] = mapped_column(
        String(100),
        default="CENTRAL_PORTAL",
        nullable=False,
        doc="Source type: MYSCHEME, CENTRAL_PORTAL, STATE_DEPT",
    )
    enabled: Mapped[bool] = mapped_column(
        Boolean,
        default=True,
        server_default=text("true"),
        nullable=False,
        doc="Whether this source is actively crawled",
    )
    crawl_priority: Mapped[int] = mapped_column(
        Integer,
        default=1,
        server_default="1",
        nullable=False,
        doc="Crawl priority order (1=highest, 10=lowest)",
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


class SchemeCrawlRun(Base):
    """Audit log of automated 5-hour scheme crawl executions."""

    __tablename__ = "scheme_crawl_runs"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scheme_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    completed_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="RUNNING",
        nullable=False,
        doc="Status: RUNNING, SUCCESS, FAILED, PARTIAL",
    )
    pages_discovered: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    pages_crawled: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    schemes_found: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    schemes_created: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    schemes_updated: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    schemes_unchanged: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    schemes_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[Optional[str]] = mapped_column(Text, nullable=True)

    source: Mapped[Optional["SchemeSource"]] = relationship("SchemeSource")


class SchemeSourceDocument(Base):
    """Raw extracted document provenance preserving audit trail without storing heavy raw HTML."""

    __tablename__ = "scheme_source_documents"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    scheme_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("government_schemes.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_id: Mapped[Optional[uuid.UUID]] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("scheme_sources.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )
    source_url: Mapped[str] = mapped_column(String(1000), nullable=False)
    content_hash: Mapped[str] = mapped_column(String(64), nullable=False, index=True)
    raw_title: Mapped[Optional[str]] = mapped_column(String(500), nullable=True)
    extracted_content: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="JSON serialized structured extracted sections",
    )
    http_status: Mapped[int] = mapped_column(Integer, default=200, nullable=False)
    fetched_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    parser_version: Mapped[str] = mapped_column(String(50), default="1.0.0", nullable=False)


class SchemeUserState(Base):
    """User-specific scheme state tracking read/unread and bookmarked/saved schemes."""

    __tablename__ = "scheme_user_state"

    __table_args__ = (
        UniqueConstraint("user_id", "scheme_id", name="uq_scheme_user_state"),
        Index("ix_scheme_user_state_user", "user_id"),
        Index("ix_scheme_user_state_scheme", "scheme_id"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
    )
    scheme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("government_schemes.id", ondelete="CASCADE"),
        nullable=False,
    )
    is_read: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False,
    )
    read_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    is_saved: Mapped[bool] = mapped_column(
        Boolean,
        default=False,
        server_default=text("false"),
        nullable=False,
    )
    saved_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    user: Mapped["UserProfile"] = relationship("UserProfile", foreign_keys=[user_id])
    scheme: Mapped["GovernmentScheme"] = relationship("GovernmentScheme", foreign_keys=[scheme_id])


class SchemeApplication(Base):
    """Farmer's application submission for an official government scheme."""

    __tablename__ = "scheme_applications"

    __table_args__ = (
        Index("ix_scheme_applications_scheme_farmer", "scheme_id", "farmer_id"),
        Index("ix_scheme_applications_status", "status"),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        doc="Primary key unique identifier for scheme application",
    )
    scheme_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("government_schemes.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key referencing government_schemes.id",
    )
    farmer_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key referencing user_profiles.id (the applicant farmer)",
    )
    status: Mapped[str] = mapped_column(
        String(50),
        default="SUBMITTED",
        server_default="SUBMITTED",
        nullable=False,
        doc="Application status: SUBMITTED, UNDER_REVIEW, APPROVED, REJECTED",
    )
    application_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Farmer's application remarks or uploaded document references",
    )
    review_notes: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Official review notes from reviewing Government Officer",
    )
    submitted_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of submission",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Timestamp of last status update",
    )

    # Relationships
    scheme: Mapped["GovernmentScheme"] = relationship(
        "GovernmentScheme",
        back_populates="applications",
    )
    farmer: Mapped["UserProfile"] = relationship(
        "UserProfile",
        foreign_keys=[farmer_id],
    )

    def __repr__(self) -> str:
        return f"<SchemeApplication(id={self.id}, scheme_id={self.scheme_id}, farmer_id={self.farmer_id}, status='{self.status}')>"
