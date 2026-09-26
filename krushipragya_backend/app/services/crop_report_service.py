"""Crop Report Service for KrushiPragya.

Manages crop health observations/reports lifecycle with strict ownership validation,
relationship traversal, and transactional safety.
"""
import logging
from pathlib import Path
from typing import List, Optional
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.crop_report import CropReport
from app.models.farmer_crop import FarmerCrop
from app.models.user_profile import UserProfile
from app.schemas.crop_report import CropReportCreate, CropReportUpdate
from app.services.farmer_crop_service import (
    FarmerCropNotFoundError,
    FarmerNotFoundError,
)
from app.services.crop_report_storage_service import (
    CropReportStorageService,
    get_crop_report_storage_service,
)

logger = logging.getLogger(__name__)


# ==============================================================================
# Domain Exceptions
# ==============================================================================

class CropReportError(Exception):
    """Base exception for crop report operations."""
    pass


class CropReportNotFoundError(CropReportError):
    """Raised when a crop report does not exist or does not belong to the farmer."""
    pass


# ==============================================================================
# Service Implementation
# ==============================================================================

class CropReportService:
    """Service layer managing crop health observation reports."""

    def __init__(self, storage_service: Optional[CropReportStorageService] = None):
        self._storage_service = storage_service

    @property
    def storage_service(self) -> CropReportStorageService:
        """Return initialized CropReportStorageService instance."""
        if self._storage_service is None:
            self._storage_service = get_crop_report_storage_service()
        return self._storage_service

    def create_crop_report(
        self,
        db: Session,
        farmer_id: uuid.UUID,
        payload: CropReportCreate,
    ) -> CropReport:
        """Create a new CropReport for a validated farmer and farmer crop association.

        Args:
            db: SQLAlchemy session
            farmer_id: UUID of the farmer submitting the report
            payload: Validated report creation payload

        Returns:
            CropReport: The persisted and refreshed CropReport ORM instance

        Raises:
            FarmerNotFoundError: If the farmer does not exist
            FarmerCropNotFoundError: If the farmer crop does not exist or does not belong to the farmer
        """
        # 1. Verify farmer exists
        farmer = db.get(UserProfile, farmer_id)
        if farmer is None:
            logger.warning("Farmer not found for ID: %s", farmer_id)
            raise FarmerNotFoundError(f"Farmer with ID '{farmer_id}' not found.")

        # 2 & 3. Verify farmer crop exists and belongs to farmer_id
        farmer_crop = (
            db.query(FarmerCrop)
            .filter(
                FarmerCrop.id == payload.farmer_crop_id,
                FarmerCrop.farmer_id == farmer_id,
            )
            .first()
        )
        if farmer_crop is None:
            logger.warning(
                "FarmerCrop %s not found or does not belong to farmer %s",
                payload.farmer_crop_id,
                farmer_id,
            )
            raise FarmerCropNotFoundError(
                f"Farmer crop with ID '{payload.farmer_crop_id}' not found for farmer '{farmer_id}'."
            )

        # 4. Instantiate CropReport
        report = CropReport(
            id=uuid.uuid4(),
            farmer_crop_id=payload.farmer_crop_id,
            notes=payload.notes,
            image_filename=payload.image_filename,
            image_storage_path=None,
        )
        report.farmer_crop = farmer_crop

        # 5 & 6. Transactional persistence
        try:
            db.add(report)
            db.commit()
            db.refresh(report)
            logger.info(
                "Successfully created CropReport %s for farmer_crop %s (farmer %s)",
                report.id,
                payload.farmer_crop_id,
                farmer_id,
            )
            return report
        except Exception:
            db.rollback()
            raise

    def get_crop_report(
        self,
        db: Session,
        farmer_id: uuid.UUID,
        report_id: uuid.UUID,
    ) -> CropReport:
        """Retrieve a specific crop report strictly enforcing ownership through FarmerCrop.

        Args:
            db: SQLAlchemy session
            farmer_id: UUID of the requesting farmer
            report_id: UUID of the crop report

        Returns:
            CropReport: Persisted CropReport ORM instance

        Raises:
            FarmerNotFoundError: If the farmer does not exist
            CropReportNotFoundError: If the report does not exist or belongs to another farmer
        """
        # 1. Verify farmer exists
        farmer = db.get(UserProfile, farmer_id)
        if farmer is None:
            logger.warning("Farmer not found for ID: %s", farmer_id)
            raise FarmerNotFoundError(f"Farmer with ID '{farmer_id}' not found.")

        # 2 & 3. Load report with relations
        report = (
            db.query(CropReport)
            .options(
                selectinload(CropReport.farmer_crop).selectinload(FarmerCrop.crop)
            )
            .filter(CropReport.id == report_id)
            .first()
        )
        if report is None:
            logger.warning("CropReport %s not found", report_id)
            raise CropReportNotFoundError(
                f"Crop report with ID '{report_id}' not found."
            )

        # 4. Verify ownership via FarmerCrop
        farmer_crop = getattr(report, "farmer_crop", None)
        if farmer_crop is None:
            farmer_crop = db.get(FarmerCrop, report.farmer_crop_id)

        if farmer_crop is None or farmer_crop.farmer_id != farmer_id:
            logger.warning(
                "CropReport %s does not belong to farmer %s",
                report_id,
                farmer_id,
            )
            raise CropReportNotFoundError(
                f"Crop report with ID '{report_id}' not found for farmer '{farmer_id}'."
            )

        return report

    def list_crop_reports(
        self,
        db: Session,
        farmer_id: uuid.UUID,
        farmer_crop_id: Optional[uuid.UUID] = None,
    ) -> List[CropReport]:
        """List all crop reports for a given farmer crop or all farmer crops in newest-first order.

        Args:
            db: SQLAlchemy session
            farmer_id: UUID of the requesting farmer
            farmer_crop_id: Optional UUID of the farmer-crop relationship

        Returns:
            List[CropReport]: List of CropReport instances ordered by created_at descending

        Raises:
            FarmerNotFoundError: If the farmer does not exist
            FarmerCropNotFoundError: If the farmer crop does not exist or belongs to another farmer
        """
        # 1. Verify farmer exists
        farmer = db.get(UserProfile, farmer_id)
        if farmer is None:
            logger.warning("Farmer not found for ID: %s", farmer_id)
            raise FarmerNotFoundError(f"Farmer with ID '{farmer_id}' not found.")

        # 2. If farmer_crop_id is provided, verify farmer crop exists and belongs to farmer
        if farmer_crop_id is not None:
            farmer_crop = (
                db.query(FarmerCrop)
                .filter(
                    FarmerCrop.id == farmer_crop_id,
                    FarmerCrop.farmer_id == farmer_id,
                )
                .first()
            )
            if farmer_crop is None:
                logger.warning(
                    "FarmerCrop %s not found or does not belong to farmer %s",
                    farmer_crop_id,
                    farmer_id,
                )
                raise FarmerCropNotFoundError(
                    f"Farmer crop with ID '{farmer_crop_id}' not found for farmer '{farmer_id}'."
                )

        # 3. Return crop reports ordered newest first
        query = (
            db.query(CropReport)
            .options(
                selectinload(CropReport.farmer_crop).selectinload(FarmerCrop.crop)
            )
        )
        if farmer_crop_id is not None:
            query = query.filter(CropReport.farmer_crop_id == farmer_crop_id)
        else:
            query = query.join(FarmerCrop, CropReport.farmer_crop_id == FarmerCrop.id).filter(
                FarmerCrop.farmer_id == farmer_id
            )

        return query.order_by(CropReport.created_at.desc()).all()

    def update_crop_report(
        self,
        db: Session,
        farmer_id: uuid.UUID,
        report_id: uuid.UUID,
        payload: CropReportUpdate,
    ) -> CropReport:
        """Partially update farmer-entered metadata (notes, image_filename) on a report.

        Args:
            db: SQLAlchemy session
            farmer_id: UUID of the requesting farmer
            report_id: UUID of the crop report
            payload: Validated partial update schema

        Returns:
            CropReport: Updated and refreshed CropReport ORM instance

        Raises:
            FarmerNotFoundError: If the farmer does not exist
            CropReportNotFoundError: If the report does not exist or belongs to another farmer
        """
        # 1, 2 & 3. Verify farmer exists, find report, and enforce ownership
        report = self.get_crop_report(db=db, farmer_id=farmer_id, report_id=report_id)

        # 4 & 5. Extract only explicitly set fields
        update_data = payload.model_dump(exclude_unset=True)

        # 6 & 7. Disallow mutating immutable identity, relational, and timestamp fields
        update_data.pop("id", None)
        update_data.pop("farmer_crop_id", None)
        update_data.pop("farmer_id", None)
        update_data.pop("crop_id", None)
        update_data.pop("diagnosis", None)
        update_data.pop("confidence", None)
        update_data.pop("image_storage_path", None)
        update_data.pop("image_url", None)
        update_data.pop("created_at", None)
        update_data.pop("updated_at", None)

        for field_name, value in update_data.items():
            if hasattr(report, field_name):
                setattr(report, field_name, value)

        # 8 & 9. Commit and refresh
        try:
            db.commit()
            db.refresh(report)
            logger.info(
                "Successfully updated CropReport %s for farmer %s (fields: %s)",
                report_id,
                farmer_id,
                list(update_data.keys()),
            )
            return report
        except Exception:
            db.rollback()
            raise

    def update_crop_report_image(
        self,
        db: Session,
        farmer_id: uuid.UUID,
        report_id: uuid.UUID,
        file_content: bytes,
        original_filename: str,
        content_type: str,
    ) -> CropReport:
        """Upload or replace crop report image with safe path and transactional rollback.

        Args:
            db: SQLAlchemy session
            farmer_id: UUID of the requesting farmer
            report_id: UUID of the crop report
            file_content: Raw bytes of the uploaded image
            original_filename: Original client filename
            content_type: Declared content type

        Returns:
            CropReport: Updated CropReport instance with new image_storage_path and image_filename

        Raises:
            FarmerNotFoundError: If the farmer does not exist
            CropReportNotFoundError: If the report does not exist or belongs to another farmer
            UnsupportedImageTypeError: If image MIME type is not allowed
            ImageSizeLimitExceededError: If file exceeds 10 MB
            InvalidImageError: If image cannot be decoded
            StorageServiceError: If storage infrastructure upload fails
        """
        # 1 & 2. Verify ownership
        report = self.get_crop_report(db=db, farmer_id=farmer_id, report_id=report_id)

        # 3, 4 & 5. Validate image format, integrity, and size
        normalized_mime = self.storage_service.validate_image(file_content, content_type)

        # 6. Generate safe internal storage path
        new_storage_path = self.storage_service.generate_storage_path(
            farmer_id=farmer_id,
            report_id=report_id,
            content_type=normalized_mime,
        )
        safe_filename = Path(original_filename).name[:255] if original_filename else "image.jpg"
        old_storage_path = report.image_storage_path

        # 7. Upload to Supabase Storage
        self.storage_service.upload_image(
            storage_path=new_storage_path,
            content=file_content,
            content_type=normalized_mime,
        )

        # 8, 9 & 10. Update CropReport and commit
        try:
            report.image_storage_path = new_storage_path
            report.image_filename = safe_filename
            db.commit()
            db.refresh(report)
            logger.info(
                "Successfully updated image for CropReport %s (path: %s)",
                report_id,
                new_storage_path,
            )
        except Exception:
            db.rollback()
            # Case B cleanup: Delete newly uploaded storage object if database commit failed
            try:
                self.storage_service.delete_image(new_storage_path)
            except Exception as cleanup_exc:
                logger.error(
                    "Failed to delete orphaned storage object %s after DB error: %s",
                    new_storage_path,
                    cleanup_exc,
                )
            raise

        # 7. (Replacement cleanup): Delete old storage object only after new state is safely committed
        if old_storage_path and old_storage_path != new_storage_path:
            try:
                self.storage_service.delete_image(old_storage_path)
            except Exception as cleanup_exc:
                logger.warning(
                    "Failed to delete superseded storage object %s: %s",
                    old_storage_path,
                    cleanup_exc,
                )

        return report

    def delete_crop_report(
        self,
        db: Session,
        farmer_id: uuid.UUID,
        report_id: uuid.UUID,
    ) -> None:
        """Delete a crop report strictly enforcing ownership and cleaning up storage.

        Args:
            db: SQLAlchemy session
            farmer_id: UUID of the requesting farmer
            report_id: UUID of the crop report

        Raises:
            FarmerNotFoundError: If the farmer does not exist
            CropReportNotFoundError: If the report does not exist or belongs to another farmer
        """
        # 1, 2 & 3. Verify farmer exists, find report, enforce ownership
        report = self.get_crop_report(db=db, farmer_id=farmer_id, report_id=report_id)
        storage_path_to_delete = report.image_storage_path

        # 4 & 5. Delete and commit database record
        try:
            db.delete(report)
            db.commit()
            logger.info(
                "Successfully deleted CropReport %s for farmer %s",
                report_id,
                farmer_id,
            )
        except Exception:
            db.rollback()
            raise

        # 6. Delete associated storage object after successful DB commit
        if storage_path_to_delete:
            try:
                self.storage_service.delete_image(storage_path_to_delete)
            except Exception as exc:
                logger.error(
                    "Failed to delete storage object %s after DB record deletion: %s",
                    storage_path_to_delete,
                    exc,
                )
