"""Crop Report Diagnosis Service.

Coordinates disease detection inference on crop report images, enforces ownership,
retrieves images from Supabase Storage, passes image bytes to DiseaseDetectionService,
and persists diagnoses to crop_report_diagnoses.
"""
import logging
from typing import Optional
import uuid

from sqlalchemy.orm import Session, selectinload

from app.models.crop_report import CropReport
from app.models.crop_report_diagnosis import CropReportDiagnosis
from app.models.farmer_crop import FarmerCrop
from app.models.user_profile import UserProfile
from app.services.crop_report_service import (
    CropReportNotFoundError,
    CropReportService,
)
from app.services.crop_report_storage_service import (
    CropReportStorageService,
    StorageServiceError,
    get_crop_report_storage_service,
)
from app.services.disease_detection_service import (
    DiseaseDetectionError,
    DiseaseDetectionService,
    UnsupportedCropError,
)
from app.services.farmer_crop_service import FarmerNotFoundError

logger = logging.getLogger(__name__)


# ==============================================================================
# Domain Exceptions
# ==============================================================================

class CropReportDiagnosisServiceError(Exception):
    """Base exception for crop report diagnosis operations."""
    pass


class CropReportImageNotFoundError(CropReportDiagnosisServiceError):
    """Raised when a crop report has no uploaded image to diagnose."""
    pass


# ==============================================================================
# Service Implementation
# ==============================================================================

class CropReportDiagnosisService:
    """Service orchestrating disease diagnosis workflow for Crop Reports."""

    def __init__(
        self,
        crop_report_service: Optional[CropReportService] = None,
        storage_service: Optional[CropReportStorageService] = None,
        disease_service: Optional[DiseaseDetectionService] = None,
    ):
        self._crop_report_service = crop_report_service
        self._storage_service = storage_service
        self._disease_service = disease_service

    @property
    def crop_report_service(self) -> CropReportService:
        """Return initialized CropReportService instance."""
        if self._crop_report_service is None:
            self._crop_report_service = CropReportService()
        return self._crop_report_service

    @property
    def storage_service(self) -> CropReportStorageService:
        """Return initialized CropReportStorageService instance."""
        if self._storage_service is None:
            self._storage_service = get_crop_report_storage_service()
        return self._storage_service

    @property
    def disease_service(self) -> DiseaseDetectionService:
        """Return initialized DiseaseDetectionService instance."""
        if self._disease_service is None:
            self._disease_service = DiseaseDetectionService()
        return self._disease_service

    def diagnose_crop_report(
        self,
        db: Session,
        farmer_id: uuid.UUID,
        report_id: uuid.UUID,
    ) -> CropReportDiagnosis:
        """Diagnose a crop report by retrieving its image, running inference, and persisting diagnosis.

        Args:
            db: SQLAlchemy session
            farmer_id: UUID of the requesting farmer
            report_id: UUID of the crop report to diagnose

        Returns:
            CropReportDiagnosis: Persisted diagnosis record

        Raises:
            FarmerNotFoundError: If farmer does not exist
            CropReportNotFoundError: If report does not exist or does not belong to farmer
            CropReportImageNotFoundError: If report has no image
            StorageServiceError: If image download from Supabase fails
            UnsupportedCropError: If crop is not supported by disease detection model
            DiseaseDetectionError: If ML inference fails
        """
        # 1. Verify farmer exists
        farmer = db.get(UserProfile, farmer_id)
        if farmer is None:
            logger.warning("Farmer %s not found for diagnosis", farmer_id)
            raise FarmerNotFoundError(f"Farmer with ID '{farmer_id}' not found.")

        # 2. Retrieve report with relationships and enforce ownership
        report = (
            db.query(CropReport)
            .options(
                selectinload(CropReport.farmer_crop).selectinload(FarmerCrop.crop)
            )
            .filter(CropReport.id == report_id)
            .first()
        )
        if report is None:
            logger.warning("Crop report %s not found for diagnosis", report_id)
            raise CropReportNotFoundError(f"Crop report with ID '{report_id}' not found.")

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

        # 3. Verify that the CropReport has an image
        if not report.image_storage_path:
            logger.warning("CropReport %s has no image uploaded for diagnosis", report_id)
            raise CropReportImageNotFoundError(
                f"Crop report '{report_id}' has no uploaded image to diagnose."
            )

        # 4. Download stored image bytes from Supabase Storage
        logger.info(
            "Downloading image from storage path '%s' for report %s",
            report.image_storage_path,
            report_id,
        )
        image_bytes = self.storage_service.download_image(report.image_storage_path)

        # 5. Determine crop code
        if not farmer_crop.crop or not farmer_crop.crop.code:
            raise UnsupportedCropError(
                "",
                list(getattr(self.disease_service, "SUPPORTED_CROPS", {}).keys()),
            )

        crop_code = farmer_crop.crop.code

        # 6. Execute ML inference via DiseaseDetectionService
        logger.info(
            "Executing disease detection inference for crop '%s' on report %s",
            crop_code,
            report_id,
        )
        prediction = self.disease_service.predict(raw_crop=crop_code, image_bytes=image_bytes)

        # 7. Create CropReportDiagnosis record
        diagnosis = CropReportDiagnosis(
            id=uuid.uuid4(),
            crop_report_id=report.id,
            crop=prediction.crop,
            predicted_class=prediction.predicted_class,
            confidence=prediction.confidence,
            model_name=prediction.model,
            predictions=[
                {
                    "class_name": item.class_name,
                    "confidence": item.confidence,
                }
                for item in prediction.predictions
            ],
        )

        # 8, 9 & 10. Persist, commit, and return
        try:
            db.add(diagnosis)
            db.commit()
            db.refresh(diagnosis)
            logger.info(
                "Successfully persisted diagnosis %s for report %s: %s (confidence: %.4f)",
                diagnosis.id,
                report_id,
                diagnosis.predicted_class,
                diagnosis.confidence,
            )
            return diagnosis
        except Exception:
            db.rollback()
            raise


def get_crop_report_diagnosis_service() -> CropReportDiagnosisService:
    """Dependency provider / singleton factory for CropReportDiagnosisService."""
    return CropReportDiagnosisService()
