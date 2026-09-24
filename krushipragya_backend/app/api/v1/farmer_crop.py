"""API endpoints for Farmer Crop Management and Crop catalog."""
import logging
from typing import List
import uuid
from fastapi import APIRouter, Depends, HTTPException, Response, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.farmer_crop import (
    CropResponse,
    FarmerCropCreate,
    FarmerCropUpdate,
    FarmerCropWithDetailsResponse,
)
from app.services.farmer_crop_service import (
    CropNotFoundError,
    FarmerCropAlreadyExistsError,
    FarmerCropNotFoundError,
    FarmerCropService,
    FarmerNotFoundError,
    InactiveCropError,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Farmer Crops"])


def get_farmer_crop_service() -> FarmerCropService:
    """Dependency provider for FarmerCropService."""
    return FarmerCropService()


@router.get(
    "/crops",
    response_model=List[CropResponse],
    status_code=status.HTTP_200_OK,
    summary="Retrieve active canonical crop catalog",
    description="Returns all active crops from the canonical catalog in alphabetical order.",
    responses={
        200: {"description": "Active crop catalog retrieved successfully"},
    },
)
def list_crops(
    db: Session = Depends(get_db),
    service: FarmerCropService = Depends(get_farmer_crop_service),
) -> List[CropResponse]:
    """Return all active crops in the catalog."""
    return service.list_crops(db=db, active_only=True)


@router.post(
    "/farmers/{farmer_id}/crops",
    response_model=FarmerCropWithDetailsResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register a crop for a farmer",
    description="Associates a canonical crop from catalog with a farmer.",
    responses={
        201: {"description": "Farmer crop created successfully"},
        404: {"description": "Farmer or crop not found"},
        409: {"description": "Crop is inactive or already registered by farmer"},
        422: {"description": "Validation error"},
    },
)
def add_farmer_crop(
    farmer_id: uuid.UUID,
    payload: FarmerCropCreate,
    db: Session = Depends(get_db),
    service: FarmerCropService = Depends(get_farmer_crop_service),
) -> FarmerCropWithDetailsResponse:
    """Register a new crop for the farmer."""
    try:
        return service.add_farmer_crop(db=db, farmer_id=farmer_id, payload=payload)
    except FarmerNotFoundError as exc:
        logger.warning("Farmer not found for crop registration: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer not found",
        ) from exc
    except CropNotFoundError as exc:
        logger.warning("Crop not found for registration: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Crop not found",
        ) from exc
    except InactiveCropError as exc:
        logger.warning("Attempt to register inactive crop: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Crop is inactive",
        ) from exc
    except FarmerCropAlreadyExistsError as exc:
        logger.warning("Duplicate crop registration: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Farmer already has this crop",
        ) from exc


@router.get(
    "/farmers/{farmer_id}/crops",
    response_model=List[FarmerCropWithDetailsResponse],
    status_code=status.HTTP_200_OK,
    summary="List crops registered by a farmer",
    description="Retrieves all crop relationships belonging to the specified farmer.",
    responses={
        200: {"description": "Farmer crops retrieved successfully"},
        404: {"description": "Farmer not found"},
        422: {"description": "Validation error (e.g. malformed UUID)"},
    },
)
def list_farmer_crops(
    farmer_id: uuid.UUID,
    db: Session = Depends(get_db),
    service: FarmerCropService = Depends(get_farmer_crop_service),
) -> List[FarmerCropWithDetailsResponse]:
    """Retrieve all crops registered for a given farmer."""
    try:
        return service.list_farmer_crops(db=db, farmer_id=farmer_id)
    except FarmerNotFoundError as exc:
        logger.warning("Farmer not found: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer not found",
        ) from exc


@router.get(
    "/farmers/{farmer_id}/crops/{crop_id}",
    response_model=FarmerCropWithDetailsResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve one farmer-crop relationship",
    description="Retrieves a specific farmer-crop relationship by relationship ID, enforcing ownership.",
    responses={
        200: {"description": "Farmer crop relationship retrieved successfully"},
        404: {"description": "Farmer or farmer crop not found"},
        422: {"description": "Validation error (e.g. malformed UUID)"},
    },
)
def get_farmer_crop(
    farmer_id: uuid.UUID,
    crop_id: uuid.UUID,
    db: Session = Depends(get_db),
    service: FarmerCropService = Depends(get_farmer_crop_service),
) -> FarmerCropWithDetailsResponse:
    """Retrieve one farmer crop relationship by ID (crop_id parameter represents the FarmerCrop ID)."""
    try:
        return service.get_farmer_crop(db=db, farmer_id=farmer_id, farmer_crop_id=crop_id)
    except FarmerNotFoundError as exc:
        logger.warning("Farmer not found: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer not found",
        ) from exc
    except FarmerCropNotFoundError as exc:
        logger.warning("Farmer crop relationship not found: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer crop not found",
        ) from exc


@router.patch(
    "/farmers/{farmer_id}/crops/{crop_id}",
    response_model=FarmerCropWithDetailsResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update a farmer-crop relationship",
    description="Updates mutable fields (area_acres, is_primary) of a farmer crop relationship.",
    responses={
        200: {"description": "Farmer crop updated successfully"},
        404: {"description": "Farmer or farmer crop not found"},
        422: {"description": "Validation error"},
    },
)
def update_farmer_crop(
    farmer_id: uuid.UUID,
    crop_id: uuid.UUID,
    payload: FarmerCropUpdate,
    db: Session = Depends(get_db),
    service: FarmerCropService = Depends(get_farmer_crop_service),
) -> FarmerCropWithDetailsResponse:
    """Update fields of an existing farmer crop relationship."""
    try:
        return service.update_farmer_crop(
            db=db,
            farmer_id=farmer_id,
            farmer_crop_id=crop_id,
            payload=payload,
        )
    except FarmerNotFoundError as exc:
        logger.warning("Farmer not found for update: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer not found",
        ) from exc
    except FarmerCropNotFoundError as exc:
        logger.warning("Farmer crop not found for update: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer crop not found",
        ) from exc


@router.delete(
    "/farmers/{farmer_id}/crops/{crop_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Delete a farmer-crop relationship",
    description="Removes a farmer crop relationship without deleting the catalog crop.",
    responses={
        204: {"description": "Farmer crop relationship deleted successfully"},
        404: {"description": "Farmer or farmer crop not found"},
        422: {"description": "Validation error (e.g. malformed UUID)"},
    },
)
def delete_farmer_crop(
    farmer_id: uuid.UUID,
    crop_id: uuid.UUID,
    db: Session = Depends(get_db),
    service: FarmerCropService = Depends(get_farmer_crop_service),
) -> Response:
    """Delete a farmer crop relationship."""
    try:
        service.delete_farmer_crop(db=db, farmer_id=farmer_id, farmer_crop_id=crop_id)
        return Response(status_code=status.HTTP_204_NO_CONTENT)
    except FarmerNotFoundError as exc:
        logger.warning("Farmer not found for delete: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer not found",
        ) from exc
    except FarmerCropNotFoundError as exc:
        logger.warning("Farmer crop not found for delete: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer crop not found",
        ) from exc
