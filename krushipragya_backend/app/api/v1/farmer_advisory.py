"""API endpoints for comprehensive Farmer Advisory (ಸಲಹೆ)."""
import logging
from typing import Literal, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, get_current_user, verify_farmer_access
from app.database.connection import get_db
from app.schemas.advisory import (
    FarmerAdvisoriesListResponse,
    FarmerAdvisoryRequest,
    FarmerComprehensiveAdvisoryResponse,
)
from app.services.farmer_advisory_service import (
    FarmerAdvisoryService,
    get_farmer_advisory_service,
)
from app.services.farmer_crop_service import (
    FarmerCropNotFoundError,
    FarmerNotFoundError,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Farmer Advisory"])


@router.post(
    "/farmers/{farmer_id}/advisory",
    response_model=FarmerComprehensiveAdvisoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Generate comprehensive farmer advisory",
    description=(
        "Synthesizes forward weather forecasts, recent disease observations, and crop context "
        "into an actionable localized farmer advisory using configured LLM provider with deterministic fallback."
    ),
    responses={
        200: {
            "description": "Farmer advisory generated successfully",
            "model": FarmerComprehensiveAdvisoryResponse,
        },
        403: {
            "description": "Access forbidden: insufficient role or cross-farmer access attempt",
        },
        404: {
            "description": "Farmer or specified crop relationship not found",
        },
        422: {
            "description": "Invalid parameter or UUID format",
        },
        500: {
            "description": "Internal server error",
        },
    },
)
def generate_farmer_advisory(
    farmer_id: uuid.UUID,
    payload: Optional[FarmerAdvisoryRequest] = None,
    auth_user: AuthenticatedUser = Depends(verify_farmer_access),
    db: Session = Depends(get_db),
    service: FarmerAdvisoryService = Depends(get_farmer_advisory_service),
) -> FarmerComprehensiveAdvisoryResponse:
    """Generate or refresh comprehensive farmer advisory integrating weather, crop, and disease context."""
    crop_id = payload.crop_id if payload else None
    language = payload.language if payload else None
    force_refresh = payload.force_refresh if payload else True

    try:
        return service.get_comprehensive_advisory(
            db=db,
            farmer_id=farmer_id,
            crop_id=crop_id,
            language=language,
            force_refresh=force_refresh,
        )
    except FarmerNotFoundError as exc:
        logger.warning("Farmer not found for advisory: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer not found",
        ) from exc
    except FarmerCropNotFoundError as exc:
        logger.warning("Farmer crop not found for advisory: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Farmer crop not found",
        ) from exc
    except ValueError as exc:
        logger.warning("Invalid advisory parameters: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error generating farmer advisory: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Unable to generate farmer advisory",
        ) from exc


@router.get(
    "/farmers/{farmer_id}/advisory",
    response_model=FarmerComprehensiveAdvisoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get active farmer advisory (with caching)",
    description="Retrieves the current active advisory for the farmer, serving from cache if fresh or generating on demand.",
)
def get_active_farmer_advisory(
    farmer_id: uuid.UUID,
    crop_id: Optional[uuid.UUID] = Query(default=None, description="Optional crop relationship UUID"),
    language: Optional[Literal["en", "kn"]] = Query(default=None, description="Language preference ('en' or 'kn')"),
    auth_user: AuthenticatedUser = Depends(verify_farmer_access),
    db: Session = Depends(get_db),
    service: FarmerAdvisoryService = Depends(get_farmer_advisory_service),
) -> FarmerComprehensiveAdvisoryResponse:
    """Fetch current active advisory for authenticated farmer."""
    try:
        return service.get_active_advisory(
            db=db,
            farmer_id=farmer_id,
            crop_id=crop_id,
            language=language,
        )
    except FarmerNotFoundError as exc:
        logger.warning("Farmer not found for advisory: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found") from exc
    except FarmerCropNotFoundError as exc:
        logger.warning("Farmer crop not found for advisory: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer crop not found") from exc
    except Exception as exc:
        logger.error("Error fetching active advisory: %s", exc, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to retrieve advisory") from exc


@router.get(
    "/farmers/{farmer_id}/advisories",
    response_model=FarmerAdvisoriesListResponse,
    status_code=status.HTTP_200_OK,
    summary="Get advisory history for a farmer",
    description="Retrieves historical generated advisories for the authenticated farmer.",
)
def get_farmer_advisories_history(
    farmer_id: uuid.UUID,
    limit: int = Query(default=10, ge=1, le=50, description="Max number of records to return"),
    auth_user: AuthenticatedUser = Depends(verify_farmer_access),
    db: Session = Depends(get_db),
    service: FarmerAdvisoryService = Depends(get_farmer_advisory_service),
) -> FarmerAdvisoriesListResponse:
    """Fetch historical advisories for the farmer."""
    try:
        return service.get_advisories_history(db=db, farmer_id=farmer_id, limit=limit)
    except FarmerNotFoundError as exc:
        logger.warning("Farmer not found for advisory history: %s", exc)
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Farmer not found") from exc
    except Exception as exc:
        logger.error("Error fetching advisory history: %s", exc, exc_info=True)
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Unable to retrieve advisory history") from exc


@router.get(
    "/advisories/{advisory_id}",
    response_model=FarmerComprehensiveAdvisoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Get specific advisory by ID",
    description="Retrieves a specific advisory by primary key UUID. Enforces farmer ownership or expert/admin privilege.",
)
def get_advisory_by_id(
    advisory_id: uuid.UUID,
    auth_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    service: FarmerAdvisoryService = Depends(get_farmer_advisory_service),
) -> FarmerComprehensiveAdvisoryResponse:
    """Retrieve advisory record by ID with RBAC and ownership verification."""
    advisory = service.get_advisory_by_id(db=db, advisory_id=advisory_id)
    if advisory is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Advisory not found")

    # Verify farmer ownership unless expert or admin
    is_privileged = any(r in ("ADMIN", "AGRICULTURE_EXPERT", "GOVERNMENT_OFFICER") for r in auth_user.roles)
    if not is_privileged:
        # Check if authenticated user owns the advisory
        from app.models.farmer_advisory import FarmerAdvisory
        rec = db.get(FarmerAdvisory, advisory_id)
        if rec and rec.farmer_id != auth_user.id:
            logger.warning("Blocked cross-farmer access to advisory %s by user %s", advisory_id, auth_user.id)
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Access forbidden: You do not have permission to view this advisory",
            )

    return advisory
