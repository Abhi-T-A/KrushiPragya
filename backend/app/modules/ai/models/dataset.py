from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.database.connection import Base


class Dataset(Base):
    __tablename__ = "datasets"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    name: Mapped[str] = mapped_column(String(150), nullable=False)
    crop: Mapped[str] = mapped_column(String(50), nullable=False)

    source: Mapped[str] = mapped_column(String(200), nullable=False)
    license: Mapped[str | None] = mapped_column(String(100), nullable=True)
    version: Mapped[str | None] = mapped_column(String(50), nullable=True)

    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    total_images: Mapped[int] = mapped_column(Integer, nullable=False, default=0)

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    images: Mapped[list["DatasetImage"]] = relationship(
        back_populates="dataset",
        cascade="all, delete-orphan",
    )


class DatasetImage(Base):
    __tablename__ = "dataset_images"

    id: Mapped[int] = mapped_column(Integer, primary_key=True, autoincrement=True)

    dataset_id: Mapped[int] = mapped_column(
        ForeignKey("datasets.id", ondelete="CASCADE"),
        nullable=False,
    )

    crop: Mapped[str] = mapped_column(String(50), nullable=False)
    class_name: Mapped[str] = mapped_column(String(150), nullable=False)
    split: Mapped[str] = mapped_column(String(20), nullable=False)

    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    storage_path: Mapped[str] = mapped_column(String(500), nullable=False)

    sha256: Mapped[str] = mapped_column(String(64), nullable=False)

    width: Mapped[int | None] = mapped_column(Integer, nullable=True)
    height: Mapped[int | None] = mapped_column(Integer, nullable=True)
    file_size: Mapped[int | None] = mapped_column(Integer, nullable=True)

    source_url: Mapped[str | None] = mapped_column(String(500), nullable=True)

    imported_at: Mapped[datetime] = mapped_column(
        DateTime,
        nullable=False,
        default=datetime.utcnow,
    )

    dataset: Mapped["Dataset"] = relationship(
        back_populates="images",
    )

    __table_args__ = (
        UniqueConstraint(
            "dataset_id",
            "sha256",
            name="uq_dataset_image_hash",
        ),
    )