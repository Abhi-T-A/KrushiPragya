"""API endpoints for Crop Disease Detection."""
from functools import lru_cache
import logging
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status

from app.schemas.disease import DiseasePredictionResponse
from app.services.disease_detection_service import (
    DiseaseDetectionService,
    EmptyImageError,
    InvalidCheckpointError,
    InvalidImageError,
    ModelNotFoundError,
    UnsupportedCropError,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/disease", tags=["Disease Detection"])


@lru_cache
def get_disease_detection_service() -> DiseaseDetectionService:
    """Dependency provider returning singleton DiseaseDetectionService."""
    return DiseaseDetectionService()


@router.post(
    "/predict",
    response_model=DiseasePredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict crop disease from leaf image",
    description=(
        "Analyzes an uploaded leaf image and returns the predicted disease or condition "
        "along with confidence score and ranked alternatives using trained EfficientNet-B0 models."
    ),
    responses={
        200: {"description": "Inference successfully completed"},
        400: {"description": "Empty image or unreadable/corrupt image file"},
        422: {"description": "Unsupported crop identifier"},
        500: {"description": "Model checkpoint missing or corrupted on server"},
    },
)
async def predict_disease(
    crop: str = Form(..., description="Crop name (e.g., arecanut, paddy, coconut, black_pepper, cardamom, turmeric, ginger)"),
    file: UploadFile = File(..., description="Leaf image file upload (JPEG, PNG, etc.)"),
    service: DiseaseDetectionService = Depends(get_disease_detection_service),
) -> DiseasePredictionResponse:
    """Predict disease for a given crop using an uploaded image."""
    try:
        image_bytes = await file.read()
        return service.predict(raw_crop=crop, image_bytes=image_bytes)
    except UnsupportedCropError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc
    except (EmptyImageError, InvalidImageError) as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc
    except (ModelNotFoundError, InvalidCheckpointError) as exc:
        logger.error("Model error during prediction for crop '%s': %s", crop, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Disease detection model error: {exc}",
        ) from exc
