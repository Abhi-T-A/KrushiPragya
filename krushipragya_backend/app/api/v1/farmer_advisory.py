"""API endpoints for comprehensive Farmer Advisory."""
import logging
from typing import Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.schemas.advisory import (
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
        "into an actionable localized farmer advisory using configured LLM provider (Groq/Ollama) with deterministic fallback."
    ),
    responses={
        200: {
            "description": "Farmer advisory generated successfully",
            "model": FarmerComprehensiveAdvisoryResponse,
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
    db: Session = Depends(get_db),
    service: FarmerAdvisoryService = Depends(get_farmer_advisory_service),
) -> FarmerComprehensiveAdvisoryResponse:
    """Generate comprehensive farmer advisory integrating weather, crop, and disease context."""
    crop_id = payload.crop_id if payload else None
    language = payload.language if payload else None

    try:
        return service.get_comprehensive_advisory(
            db=db,
            farmer_id=farmer_id,
            crop_id=crop_id,
            language=language,
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
