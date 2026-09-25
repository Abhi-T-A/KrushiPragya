"""Role and UserRole SQLAlchemy models for KrushiPragya RBAC."""
from datetime import datetime
from typing import List, Optional, TYPE_CHECKING
import uuid

from sqlalchemy import DateTime, ForeignKey, Index, String, Text, func, text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.base import Base

if TYPE_CHECKING:
    from app.models.user_profile import UserProfile


class Role(Base):
    """System roles defining user actor types in KrushiPragya."""

    __tablename__ = "roles"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        doc="Primary key unique identifier for role",
    )
    code: Mapped[str] = mapped_column(
        String(50),
        unique=True,
        nullable=False,
        index=True,
        doc="Unique role code (e.g. FARMER, AGRICULTURE_EXPERT, GOVERNMENT_OFFICER, BUYER, COMMUNITY_MEMBER, ADMIN)",
    )
    name: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        doc="Human-readable role name",
    )
    description: Mapped[Optional[str]] = mapped_column(
        String(255),
        nullable=True,
        doc="Brief description of responsibilities and permissions",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp of role creation",
    )

    # Relationships
    user_roles: Mapped[List["UserRole"]] = relationship(
        "UserRole",
        back_populates="role",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        return f"<Role(code='{self.code}', name='{self.name}')>"


class UserRole(Base):
    """Mapping between users and their assigned roles with lifecycle status."""

    __tablename__ = "user_roles"

    __table_args__ = (
        Index("ix_user_roles_user_id_role_code", "user_id", "role_code", unique=True),
    )

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
        server_default=text("gen_random_uuid()"),
        doc="Primary key unique identifier for user-role assignment",
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("user_profiles.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Foreign key referencing user_profiles.id",
    )
    role_code: Mapped[str] = mapped_column(
        String(50),
        ForeignKey("roles.code", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Role code referencing roles.code",
    )
    status: Mapped[str] = mapped_column(
        String(20),
        default="ACTIVE",
        server_default="ACTIVE",
        nullable=False,
        doc="Assignment status: ACTIVE, SUSPENDED, REVOKED",
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="Timestamp when role was assigned",
    )

    # Relationships
    role: Mapped["Role"] = relationship(
        "Role",
        back_populates="user_roles",
    )
    user: Mapped["UserProfile"] = relationship(
        "UserProfile",
        back_populates="user_roles",
    )

    def __repr__(self) -> str:
        return f"<UserRole(user_id={self.user_id}, role_code='{self.role_code}', status='{self.status}')>"
