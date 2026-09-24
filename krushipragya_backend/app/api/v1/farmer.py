"""API endpoints for Farmer Profile management."""
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.farmer import (
    FarmerProfileCreate,
    FarmerProfileResponse,
    FarmerProfileUpdate,
)
from app.services.farmer_profile_service import (
    FarmerProfileAlreadyExistsError,
    FarmerProfileNotFoundError,
    FarmerProfileService,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/farmers", tags=["Farmers"])


def get_farmer_profile_service() -> FarmerProfileService:
    """Dependency provider for FarmerProfileService."""
    return FarmerProfileService()


@router.post(
    "/profile",
    response_model=FarmerProfileResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create farmer profile",
    description="Creates a new farmer profile record linked to Supabase auth.users UUID.",
    responses={
        201: {"description": "Farmer profile created successfully"},
        409: {"description": "Farmer profile already exists"},
        422: {"description": "Validation error"},
    },
)
def create_farmer_profile(
    payload: FarmerProfileCreate,
    db: Session = Depends(get_db),
    service: FarmerProfileService = Depends(get_farmer_profile_service),
) -> FarmerProfileResponse:
    """Create a farmer profile."""
    try:
        return service.create_profile(db=db, payload=payload)
    except FarmerProfileAlreadyExistsError as exc:
        logger.warning("Conflict creating farmer profile: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Farmer profile already exists",
        ) from exc


@router.get(
    "/profile/{farmer_id}",
    response_model=FarmerProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve farmer profile",
    description="Retrieves a farmer profile by user UUID.",
    responses={
        200: {"description": "Farmer profile retrieved successfully"},
        404: {"description": "Farmer profile not found"},
        422: {"description": "Validation error (e.g., malformed UUID)"},
    },
)
def get_farmer_profile(
    farmer_id: uuid.UUID,
    db: Session = Depends(get_db),
    service: FarmerProfileService = Depends(get_farmer_profile_service),
) -> FarmerProfileResponse:
    """Retrieve a farmer profile by ID."""
    try:
        return service.get_profile(db=db, farmer_id=farmer_id)
    except FarmerProfileNotFoundError as exc:
        logger.warning("Farmer profile not found for ID: %s", farmer_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer profile not found",
        ) from exc


@router.patch(
    "/profile/{farmer_id}",
    response_model=FarmerProfileResponse,
    status_code=status.HTTP_200_OK,
    summary="Partially update farmer profile",
    description="Updates only the supplied fields of a farmer profile. Unsupplied fields remain untouched.",
    responses={
        200: {"description": "Farmer profile updated successfully"},
        404: {"description": "Farmer profile not found"},
        422: {"description": "Validation error"},
    },
)
def update_farmer_profile(
    farmer_id: uuid.UUID,
    payload: FarmerProfileUpdate,
    db: Session = Depends(get_db),
    service: FarmerProfileService = Depends(get_farmer_profile_service),
) -> FarmerProfileResponse:
    """Update a farmer profile by ID."""
    try:
        return service.update_profile(db=db, farmer_id=farmer_id, payload=payload)
    except FarmerProfileNotFoundError as exc:
        logger.warning("Farmer profile not found for update ID: %s", farmer_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer profile not found",
        ) from exc
