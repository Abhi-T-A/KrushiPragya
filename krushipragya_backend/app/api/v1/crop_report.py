"""API endpoints for Crop Report management."""
import logging
from typing import List
import uuid

from fastapi import APIRouter, Depends, File, HTTPException, Query, Response, UploadFile, status
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, verify_farmer_access
from app.database.connection import get_db
from app.schemas.crop_report import (
    CropReportCreate,
    CropReportResponse,
    CropReportUpdate,
)
from app.services.crop_report_service import (
    CropReportNotFoundError,
    CropReportService,
    FarmerCropNotFoundError,
    FarmerNotFoundError,
)
from app.services.crop_report_storage_service import (
    ImageSizeLimitExceededError,
    InvalidImageError,
    StorageServiceError,
    UnsupportedImageTypeError,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Crop Reports"])


def get_crop_report_service() -> CropReportService:
    """Dependency provider for CropReportService."""
    return CropReportService()


@router.post(
    "/farmers/{farmer_id}/crop-reports",
    response_model=CropReportResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new crop health report",
    description="Submits a new crop health observation report for a registered farmer crop.",
    responses={
        201: {"description": "Crop report created successfully"},
        404: {"description": "Farmer or farmer crop not found"},
        422: {"description": "Validation error"},
    },
)
def create_crop_report(
    farmer_id: uuid.UUID,
    payload: CropReportCreate,
    auth_user: AuthenticatedUser = Depends(verify_farmer_access),
    db: Session = Depends(get_db),
    service: CropReportService = Depends(get_crop_report_service),
) -> CropReportResponse:
    """Create a new crop report enforcing ownership and FARMER role."""
    try:
        return service.create_crop_report(db=db, farmer_id=farmer_id, payload=payload)
    except FarmerNotFoundError as exc:
        logger.warning("Farmer not found for crop report: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer not found",
        ) from exc
    except FarmerCropNotFoundError as exc:
        logger.warning("Farmer crop not found for crop report: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer crop not found",
        ) from exc


@router.get(
    "/farmers/{farmer_id}/crop-reports",
    response_model=List[CropReportResponse],
    status_code=status.HTTP_200_OK,
    summary="List crop reports for a farmer crop",
    description="Retrieves all crop reports for a specific farmer crop relationship ordered newest first.",
    responses={
        200: {"description": "List of crop reports retrieved successfully"},
        403: {"description": "Access forbidden: insufficient role or cross-farmer access attempt"},
        404: {"description": "Farmer or farmer crop not found"},
        422: {"description": "Validation error"},
    },
)
def list_crop_reports(
    farmer_id: uuid.UUID,
    farmer_crop_id: uuid.UUID = Query(
        ...,
        description="UUID of the farmer crop relationship to list reports for",
    ),
    auth_user: AuthenticatedUser = Depends(verify_farmer_access),
    db: Session = Depends(get_db),
    service: CropReportService = Depends(get_crop_report_service),
) -> List[CropReportResponse]:
    """List crop reports for a farmer crop enforcing ownership."""
    try:
        return service.list_crop_reports(
            db=db, farmer_id=farmer_id, farmer_crop_id=farmer_crop_id
        )
    except FarmerNotFoundError as exc:
        logger.warning("Farmer not found for listing crop reports: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer not found",
        ) from exc
    except FarmerCropNotFoundError as exc:
        logger.warning("Farmer crop not found for listing crop reports: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer crop not found",
        ) from exc


@router.get(
    "/farmers/{farmer_id}/crop-reports/{report_id}",
    response_model=CropReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve a single crop report",
    description="Retrieves a specific crop report by ID, strictly enforcing farmer ownership.",
    responses={
        200: {"description": "Crop report retrieved successfully"},
        403: {"description": "Access forbidden: insufficient role or cross-farmer access attempt"},
        404: {"description": "Farmer or crop report not found"},
        422: {"description": "Validation error"},
    },
)
def get_crop_report(
    farmer_id: uuid.UUID,
    report_id: uuid.UUID,
    auth_user: AuthenticatedUser = Depends(verify_farmer_access),
    db: Session = Depends(get_db),
    service: CropReportService = Depends(get_crop_report_service),
) -> CropReportResponse:
    """Retrieve an individual crop report enforcing ownership."""
    try:
        return service.get_crop_report(
            db=db, farmer_id=farmer_id, report_id=report_id
        )
    except FarmerNotFoundError as exc:
        logger.warning("Farmer not found for crop report retrieval: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer not found",
        ) from exc
    except CropReportNotFoundError as exc:
        logger.warning("Crop report not found: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop report not found",
        ) from exc


@router.patch(
    "/farmers/{farmer_id}/crop-reports/{report_id}",
    response_model=CropReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update a crop report",
    description="Updates editable metadata (notes, image_filename) on an existing crop report.",
    responses={
        200: {"description": "Crop report updated successfully"},
        403: {"description": "Access forbidden: insufficient role or cross-farmer access attempt"},
        404: {"description": "Farmer or crop report not found"},
        422: {"description": "Validation error"},
    },
)
def update_crop_report(
    farmer_id: uuid.UUID,
    report_id: uuid.UUID,
    payload: CropReportUpdate,
    auth_user: AuthenticatedUser = Depends(verify_farmer_access),
    db: Session = Depends(get_db),
    service: CropReportService = Depends(get_crop_report_service),
) -> CropReportResponse:
    """Partially update a crop report enforcing ownership."""
    try:
        return service.update_crop_report(
            db=db, farmer_id=farmer_id, report_id=report_id, payload=payload
        )
    except FarmerNotFoundError as exc:
        logger.warning("Farmer not found for crop report update: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer not found",
        ) from exc
    except CropReportNotFoundError as exc:
        logger.warning("Crop report not found for update: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop report not found",
        ) from exc


@router.delete(
    "/farmers/{farmer_id}/crop-reports/{report_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a crop report",
    description="Deletes a crop report record strictly enforcing farmer ownership.",
    responses={
        204: {"description": "Crop report deleted successfully"},
        403: {"description": "Access forbidden: insufficient role or cross-farmer access attempt"},
        404: {"description": "Farmer or crop report not found"},
        422: {"description": "Validation error"},
    },
)
def delete_crop_report(
    farmer_id: uuid.UUID,
    report_id: uuid.UUID,
    auth_user: AuthenticatedUser = Depends(verify_farmer_access),
    db: Session = Depends(get_db),
    service: CropReportService = Depends(get_crop_report_service),
) -> Response:
    """Delete a crop report enforcing ownership."""
    try:
        service.delete_crop_report(
            db=db, farmer_id=farmer_id, report_id=report_id
        )
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except FarmerNotFoundError as exc:
        logger.warning("Farmer not found for crop report delete: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer not found",
        ) from exc
    except CropReportNotFoundError as exc:
        logger.warning("Crop report not found for delete: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop report not found",
        ) from exc


@router.put(
    "/farmers/{farmer_id}/crop-reports/{report_id}/image",
    response_model=CropReportResponse,
    status_code=status.HTTP_200_OK,
    summary="Upload or replace crop report image",
    description="Uploads an image (JPEG, PNG, WebP up to 10 MB) for a crop report and updates its storage path.",
    responses={
        200: {"description": "Image uploaded successfully"},
        400: {"description": "Unsupported image type or invalid image"},
        403: {"description": "Access forbidden: insufficient role or cross-farmer access attempt"},
        404: {"description": "Farmer or crop report not found"},
        413: {"description": "File exceeds maximum size of 10 MB"},
        422: {"description": "Validation error"},
        500: {"description": "Storage service failure"},
    },
)
def upload_crop_report_image(
    farmer_id: uuid.UUID,
    report_id: uuid.UUID,
    file: UploadFile = File(...),
    auth_user: AuthenticatedUser = Depends(verify_farmer_access),
    db: Session = Depends(get_db),
    service: CropReportService = Depends(get_crop_report_service),
) -> CropReportResponse:
    """Upload or replace crop report image."""
    max_size = 10 * 1024 * 1024
    content = file.file.read(max_size + 1)
    if len(content) > max_size:
        logger.warning("Upload rejected: file size exceeds 10 MB limit")
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail="File exceeds maximum size of 10 MB",
        )
    if len(content) == 0:
        logger.warning("Upload rejected: empty file")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Image file is empty",
        )

    content_type = file.content_type or ""
    original_filename = file.filename or "image.jpg"

    try:
        return service.update_crop_report_image(
            db=db,
            farmer_id=farmer_id,
            report_id=report_id,
            file_content=content,
            original_filename=original_filename,
            content_type=content_type,
        )
    except FarmerNotFoundError as exc:
        logger.warning("Farmer not found for image upload: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer not found",
        ) from exc
    except CropReportNotFoundError as exc:
        logger.warning("Crop report not found for image upload: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop report not found",
        ) from exc
    except UnsupportedImageTypeError as exc:
        logger.warning("Unsupported image type for image upload: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except InvalidImageError as exc:
        logger.warning("Invalid image file for image upload: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except ImageSizeLimitExceededError as exc:
        logger.warning("Image size limit exceeded: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=str(exc),
        ) from exc
    except StorageServiceError as exc:
        logger.error("Storage infrastructure failure: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Storage service failure",
        ) from exc

