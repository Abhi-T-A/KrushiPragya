"""API endpoints for Crop Report Disease Diagnosis."""
import logging
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, verify_farmer_access
from app.database.connection import get_db
from app.schemas.crop_report import CropReportDiagnosisRecordResponse
from app.services.crop_report_diagnosis_service import (
    CropReportDiagnosisService,
    CropReportImageNotFoundError,
    get_crop_report_diagnosis_service,
)
from app.services.crop_report_service import (
    CropReportNotFoundError,
)
from app.services.crop_report_storage_service import (
    StorageServiceError,
)
from app.services.disease_detection_service import (
    DiseaseDetectionError,
    UnsupportedCropError,
)
from app.services.farmer_crop_service import (
    FarmerNotFoundError,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Crop Report Diagnosis"])


@router.post(
    "/farmers/{farmer_id}/crop-reports/{report_id}/diagnose",
    response_model=CropReportDiagnosisRecordResponse,
    status_code=status.HTTP_200_OK,
    summary="Diagnose crop report disease",
    description=(
        "Executes disease detection inference on an uploaded crop report image "
        "and persists the resulting diagnosis record."
    ),
    responses={
        200: {
            "description": "Crop report diagnosis executed and persisted successfully",
            "model": CropReportDiagnosisRecordResponse,
        },
        404: {
            "description": "Farmer or crop report not found",
        },
        409: {
            "description": "Crop report has no uploaded image",
        },
        422: {
            "description": "Crop is not supported for disease detection or invalid UUID format",
        },
        500: {
            "description": "Disease analysis failed or internal service error",
        },
        502: {
            "description": "Unable to retrieve crop report image from storage",
        },
    },
)
def diagnose_crop_report(
    farmer_id: uuid.UUID,
    report_id: uuid.UUID,
    auth_user: AuthenticatedUser = Depends(verify_farmer_access),
    db: Session = Depends(get_db),
    service: CropReportDiagnosisService = Depends(get_crop_report_diagnosis_service),
) -> CropReportDiagnosisRecordResponse:
    """Diagnose an existing crop report from its uploaded image."""
    try:
        diagnosis = service.diagnose_crop_report(
            db=db,
            farmer_id=farmer_id,
            report_id=report_id,
        )
        return CropReportDiagnosisRecordResponse.model_validate(diagnosis)
    except FarmerNotFoundError as exc:
        logger.warning("Farmer not found for diagnosis: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer not found",
        ) from exc
    except CropReportNotFoundError as exc:
        logger.warning("Crop report not found for diagnosis: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop report not found",
        ) from exc
    except CropReportImageNotFoundError as exc:
        logger.warning("Crop report has no image for diagnosis: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Crop report has no image",
        ) from exc
    except StorageServiceError as exc:
        logger.error("Storage download failure during diagnosis: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="Unable to retrieve crop report image",
        ) from exc
    except UnsupportedCropError as exc:
        logger.warning("Unsupported crop for diagnosis: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail="Crop is not supported for disease detection",
        ) from exc
    except DiseaseDetectionError as exc:
        logger.error("Disease detection inference failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Disease analysis failed",
        ) from exc
    except Exception as exc:
        logger.error("Unexpected failure during crop report diagnosis: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to diagnose crop report",
        ) from exc
