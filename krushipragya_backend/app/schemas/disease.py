"""Pydantic schemas for Disease Detection module and Input Verification Layer."""
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field


class ClassPrediction(BaseModel):
    """Individual class prediction with confidence probability."""
    model_config = ConfigDict(extra="ignore")

    class_name: str = Field(..., description="Disease, pest, or healthy condition label")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Softmax probability score between 0.0 and 1.0",
    )


class DiseaseInfoResponse(BaseModel):
    """Curated ICAR Disease Knowledge Base information attached to positive AI diagnoses."""
    model_config = ConfigDict(extra="ignore")

    disease_name_en: str = Field(..., description="Disease name in English")
    disease_name_kn: str = Field(..., description="Disease name in Kannada")
    scientific_name: Optional[str] = Field(None, description="Scientific causal organism name")
    category: str = Field(..., description="Category: FUNGAL, BACTERIAL, VIRAL, PEST, ABIOTIC, HEALTHY")
    symptoms: str = Field(..., description="Clinical field symptoms")
    cultural_control: str = Field(..., description="Field agronomic management practices")
    remedy_en: str = Field(..., description="Recommended curative treatment in English")
    remedy_kn: str = Field(..., description="Recommended curative treatment in Kannada")
    source_institution: str = Field(..., description="Authoritative institution (e.g. ICAR-CPCRI, ICAR-DRR, ICAR-IISR)")


class DiseasePredictionResponse(BaseModel):
    """Response schema for disease detection inference and input verification."""
    model_config = ConfigDict(extra="ignore")

    crop: str = Field(..., description="Normalized crop identifier (e.g. arecanut, paddy)")
    status: str = Field(
        default="success",
        description="Verification/Inference status: 'success', 'uncertain', or 'rejected'",
    )
    predicted_class: Optional[str] = Field(
        default=None,
        description="Top-1 predicted disease condition or null if low confidence (< 50%) or rejected",
    )
    confidence: float = Field(
        default=0.0,
        ge=0.0,
        le=1.0,
        description="Top-1 softmax prediction confidence score between 0.0 and 1.0",
    )
    low_confidence: bool = Field(
        default=False,
        description="True if model confidence is below the application threshold (50%)",
    )
    input_verified: bool = Field(
        default=True,
        description="True if uploaded image passed input quality, exposure, and leaf relevance gates",
    )
    reason_code: Optional[str] = Field(
        default=None,
        description="Machine-readable code if rejected or uncertain (e.g. LOW_IMAGE_QUALITY, IRRELEVANT_IMAGE)",
    )
    message: Optional[str] = Field(
        default=None,
        description="Farmer-facing explanation and guidance message",
    )
    model_version: Optional[str] = Field(
        default=None,
        description="Standardized model version identifier (e.g. arecanut-v1)",
    )
    disease_info: Optional[DiseaseInfoResponse] = Field(
        default=None,
        description="Curated ICAR Disease KB treatment and symptoms info",
    )
    predictions: List[ClassPrediction] = Field(
        default_factory=list,
        description="Ranked list of all class predictions sorted by confidence descending",
    )
    top_predictions: Optional[List[ClassPrediction]] = Field(
        default=None,
        description="Top predictions for debugging, calibration, and monitoring",
    )
    model: str = Field(
        default="",
        description="Name of the model checkpoint used for inference",
    )


class DiseaseRejectionDetail(BaseModel):
    """Standardized rejection response for 400 Bad Request verification failures."""
    model_config = ConfigDict(extra="ignore")

    status: str = Field(default="rejected", description="Always 'rejected'")
    reason_code: str = Field(..., description="Reason code: INVALID_IMAGE, IMAGE_TOO_BLURRY, IMAGE_TOO_DARK, etc.")
    input_verified: bool = Field(default=False, description="Always False for rejected inputs")
    message: str = Field(..., description="Farmer-facing advisory explanation")
    metrics: Optional[Dict[str, Any]] = Field(default=None, description="Verification measurements")
