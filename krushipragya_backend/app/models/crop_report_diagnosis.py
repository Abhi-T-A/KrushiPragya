"""CropReportDiagnosis SQLAlchemy model for storing disease detection results."""
from datetime import datetime
from typing import TYPE_CHECKING
import uuid

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    JSON,
    String,
    func,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.crop_report import CropReport


class CropReportDiagnosis(Base):
    """Model representing a persistent disease diagnosis record for a crop report."""

    __tablename__ = "crop_report_diagnoses"

    __table_args__ = (
        Index(
            "ix_crop_report_diagnoses_crop_report_id_created_at",
            "crop_report_id",
            text("created_at DESC"),
        ),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        server_default=text("gen_random_uuid()"),
        doc="Primary key unique identifier for the diagnosis record",
    )
    crop_report_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("crop_reports.id", ondelete="CASCADE"),
        nullable=False,
        doc="Foreign key referencing crop_reports.id with cascading delete",
    )
    crop: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Normalized crop identifier used during disease inference",
    )
    predicted_class: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
        doc="Top-1 predicted condition label",
    )
    confidence: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        doc="Top-1 softmax confidence score between 0.0 and 1.0",
    )
    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Model checkpoint filename or identifier used for inference",
    )
    predictions: Mapped[list] = mapped_column(
        JSON().with_variant(JSONB, "postgresql"),
        nullable=False,
        doc="Full ranked list of class predictions and probabilities",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when diagnosis was generated and persisted",
    )

    # Relationships
    crop_report: Mapped["CropReport"] = relationship(
        "CropReport",
        back_populates="diagnoses",
    )

    def __repr__(self) -> str:
        return (
            f"<CropReportDiagnosis(id={self.id}, "
            f"crop_report_id={self.crop_report_id}, "
            f"crop='{self.crop}', "
            f"predicted_class='{self.predicted_class}', "
            f"confidence={self.confidence})>"
        )
