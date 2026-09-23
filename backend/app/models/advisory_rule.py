from datetime import datetime
from typing import Any, Dict, Optional

from sqlalchemy import (
    Boolean,
    DateTime,
    Integer,
    JSON,
    String,
    Text,
    func,
)
from sqlalchemy.orm import Mapped, mapped_column

from app.database.base import Base


class AdvisoryRule(Base):
    """ORM mapping for the pre-existing public.advisory_rules database table."""

    __tablename__ = "advisory_rules"

    id: Mapped[int] = mapped_column(
        Integer,
        primary_key=True,
        autoincrement=True,
        doc="Primary key unique identifier for advisory rule",
    )
    crop: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Target crop name (e.g. Arecanut)",
    )
    risk_name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Name of the agricultural risk context",
    )
    risk_level: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Risk severity level (e.g. HIGH, MODERATE, LOW)",
    )
    condition_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        doc="Condition evaluation type (e.g. WEATHER_THRESHOLD)",
    )
    condition_config: Mapped[Dict[str, Any]] = mapped_column(
        JSON,
        nullable=False,
        doc="JSON configuration specifying threshold criteria and risk factors",
    )
    advisory_en: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="English agricultural advisory text",
    )
    advisory_kn: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Kannada agricultural advisory text",
    )
    source_name: Mapped[str] = mapped_column(
        String(150),
        nullable=False,
        doc="Authoritative institution or expert source",
    )
    source_reference: Mapped[Optional[str]] = mapped_column(
        Text,
        nullable=True,
        doc="Bibliographic or publication reference details",
    )
    is_demo_rule: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=False,
        doc="Flag indicating if this is demo seed rule",
    )
    active: Mapped[bool] = mapped_column(
        Boolean,
        nullable=False,
        default=True,
        doc="Flag indicating if this rule is currently active for evaluation",
    )
    version: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
        default=1,
        doc="Rule version number",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Rule record creation timestamp",
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        doc="Rule record last updated timestamp",
    )

    def __repr__(self) -> str:
        return f"<AdvisoryRule(id={self.id}, crop='{self.crop}', risk_name='{self.risk_name}', risk_level='{self.risk_level}', active={self.active})>"
