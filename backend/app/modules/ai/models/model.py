from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    JSON,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class MLModel(Base):
    __tablename__ = "models"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    crop: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    model_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    architecture: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    version: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )

    model_path: Mapped[str] = mapped_column(
        String(500),
        nullable=False,
    )

    status: Mapped[str] = mapped_column(
        String(30),
        nullable=False,
        default="pending_validation",
    )

    class_mapping: Mapped[dict] = mapped_column(
        JSON,
        nullable=False,
    )

    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    is_active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    __table_args__ = (
        Index("ix_models_crop", "crop"),
    )

    metrics: Mapped[list["ModelMetric"]] = relationship(
        back_populates="model",
        cascade="all, delete-orphan",
    )


class ModelMetric(Base):
    __tablename__ = "model_metrics"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
    )

    model_id: Mapped[int] = mapped_column(
        ForeignKey("models.id", ondelete="CASCADE"),
        nullable=False,
    )

    test_accuracy: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    macro_f1: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    weighted_f1: Mapped[float] = mapped_column(
        Float,
        nullable=False,
    )

    test_samples: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )

    evaluation_notes: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    evaluated_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    model: Mapped["MLModel"] = relationship(
        back_populates="metrics",
    )