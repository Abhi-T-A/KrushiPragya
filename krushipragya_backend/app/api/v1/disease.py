"""API endpoints for Crop Disease Detection and Input Verification Layer."""
from functools import lru_cache
import logging
from typing import Optional
from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile, status
from fastapi.responses import JSONResponse

from app.schemas.disease import DiseasePredictionResponse
from app.services.disease_detection_service import (
    DiseaseDetectionService,
    EmptyImageError,
    InvalidCheckpointError,
    InvalidImageError,
    ModelNotFoundError,
    ModelUnavailableError,
    UnsupportedCropError,
    VerificationRejectionError,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["Disease Detection"])


@lru_cache
def get_disease_detection_service() -> DiseaseDetectionService:
    """Dependency provider returning singleton DiseaseDetectionService."""
    return DiseaseDetectionService()


@router.post(
    "/disease/predict",
    response_model=DiseasePredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="Predict crop disease from leaf image with defensive input verification",
    description=(
        "Analyzes an uploaded crop photo through an Input Verification Layer "
        "(checking resolution, blur, lighting, exposure, and leaf relevance), "
        "executes crop-specific EfficientNet-B0 inference, applies a 50% confidence gate, "
        "and attaches curated ICAR disease intelligence."
    ),
    responses={
        200: {"description": "Inference successfully completed (status 'success' or 'uncertain')"},
        400: {"description": "Input rejected (empty, corrupt, blurry, dark, overexposed, or irrelevant non-leaf image)"},
        422: {"description": "Unsupported crop identifier"},
        503: {"description": "Model checkpoint unavailable for requested crop"},
    },
)
@router.post(
    "/ai/predict",
    response_model=DiseasePredictionResponse,
    status_code=status.HTTP_200_OK,
    summary="AI predict crop disease endpoint (alias)",
    include_in_schema=False,
)
async def predict_disease(
    crop: str = Form(..., description="Crop name (e.g., arecanut, paddy, coconut, black_pepper, cardamom, turmeric, ginger)"),
    file: Optional[UploadFile] = File(None, description="Leaf image file upload (JPEG, PNG, WEBP)"),
    image: Optional[UploadFile] = File(None, description="Leaf image file upload (alias for 'file')"),
    service: DiseaseDetectionService = Depends(get_disease_detection_service),
):
    """Predict disease for a given crop using an uploaded image through the defensive verification layer."""
    upload_file = file or image
    if upload_file is None:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded image file is empty.",
        )

    try:
        image_bytes = await upload_file.read()
        return service.predict(raw_crop=crop, image_bytes=image_bytes, verify_input=True, enforce_confidence_gate=True)

    except UnsupportedCropError as exc:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=str(exc),
        ) from exc

    except VerificationRejectionError as exc:
        # Structured defensive input verification rejection
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status": "rejected",
                "reason_code": exc.reason_code,
                "input_verified": False,
                "message": exc.message,
                "detail": exc.message,
                "metrics": exc.metrics,
            },
        )

    except EmptyImageError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status": "rejected",
                "reason_code": "INVALID_IMAGE",
                "input_verified": False,
                "message": "Uploaded image file is empty.",
                "detail": "Uploaded image file is empty.",
            },
        )

    except InvalidImageError as exc:
        return JSONResponse(
            status_code=status.HTTP_400_BAD_REQUEST,
            content={
                "status": "rejected",
                "reason_code": "INVALID_IMAGE",
                "input_verified": False,
                "message": str(exc),
                "detail": str(exc),
            },
        )

    except (ModelNotFoundError, ModelUnavailableError) as exc:
        logger.error("Model unavailable for crop '%s': %s", crop, exc, exc_info=True)
        return JSONResponse(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            content={
                "status": "rejected",
                "reason_code": "MODEL_UNAVAILABLE",
                "input_verified": False,
                "message": f"AI analysis is temporarily unavailable for crop '{crop}'.",
                "detail": f"AI analysis is temporarily unavailable for crop '{crop}'.",
            },
        )

    except InvalidCheckpointError as exc:
        logger.error("Model checkpoint corruption for crop '%s': %s", crop, exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Disease detection model error: {exc}",
        ) from exc
