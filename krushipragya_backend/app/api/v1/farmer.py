"""API endpoints for Farmer Profile management."""
import logging
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, get_current_user, verify_farmer_access
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
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: FarmerProfileService = Depends(get_farmer_profile_service),
) -> FarmerProfileResponse:
    """Create a farmer profile enforcing authenticated identity."""
    # Never trust payload.id blindly - ensure the authenticated user owns this profile
    if payload.id != current_user.id and "ADMIN" not in current_user.roles:
        logger.warning(
            "User %s attempted to create profile for different ID %s",
            current_user.id,
            payload.id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot create a profile for another user ID",
        )
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
        403: {"description": "Access forbidden: insufficient role or cross-farmer access attempt"},
        404: {"description": "Farmer profile not found"},
        422: {"description": "Validation error (e.g., malformed UUID)"},
    },
)
def get_farmer_profile(
    farmer_id: uuid.UUID,
    auth_user: AuthenticatedUser = Depends(verify_farmer_access),
    db: Session = Depends(get_db),
    service: FarmerProfileService = Depends(get_farmer_profile_service),
) -> FarmerProfileResponse:
    """Retrieve a farmer profile by ID enforcing ownership and FARMER role."""
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
        403: {"description": "Access forbidden: insufficient role or cross-farmer access attempt"},
        404: {"description": "Farmer profile not found"},
        422: {"description": "Validation error"},
    },
)
def update_farmer_profile(
    farmer_id: uuid.UUID,
    payload: FarmerProfileUpdate,
    auth_user: AuthenticatedUser = Depends(verify_farmer_access),
    db: Session = Depends(get_db),
    service: FarmerProfileService = Depends(get_farmer_profile_service),
) -> FarmerProfileResponse:
    """Update a farmer profile by ID enforcing ownership and FARMER role."""
    try:
        return service.update_profile(db=db, farmer_id=farmer_id, payload=payload)
    except FarmerProfileNotFoundError as exc:
        logger.warning("Farmer profile not found for update ID: %s", farmer_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer profile not found",
        ) from exc
