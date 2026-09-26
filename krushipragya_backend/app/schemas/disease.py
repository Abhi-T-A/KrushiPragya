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

    crop: Any = Field(..., description="Normalized crop identifier or crop details dict")
    status: str = Field(
        default="success",
        description="Verification/Inference status: 'success', 'uncertain', or 'rejected'",
    )
    state: str = Field(
        default="VALID_IMAGE",
        description="Verification state: VALID_IMAGE, IRRELEVANT_IMAGE, CROP_MISMATCH, UNCERTAIN_IMAGE, LOW_QUALITY",
    )
    predicted_class: Optional[str] = Field(
        default=None,
        description="Top-1 predicted disease condition or null if low confidence (< 50%) or rejected",
    )
    diagnosis: Optional[str] = Field(
        default=None,
        description="Disease diagnosis result (null if low confidence or irrelevant)",
    )
    confidence: Optional[float] = Field(
        default=0.0,
        description="Top-1 softmax prediction confidence score between 0.0 and 1.0 (null if irrelevant)",
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
    disease: Optional[str] = Field(
        default=None,
        description="Authoritative disease name from verified Disease Knowledge Base",
    )
    disease_name_kn: Optional[str] = Field(
        default=None,
        description="Verified disease name in Kannada",
    )
    knowledge_base_reference: Optional[str] = Field(
        default=None,
        description="Authoritative institutional reference (e.g. ICAR-CPCRI Kasaragod)",
    )
    explanation_kn: Optional[str] = Field(
        default=None,
        description="Farmer-facing Kannada summary and explanation (Qwen or deterministic fallback)",
    )
    approved_actions: List[str] = Field(
        default_factory=list,
        description="List of verified agricultural actions and treatments",
    )
    verification_state: str = Field(
        default="AI_ANALYSED",
        description="Canonical verification state (e.g. AI_ANALYSED, UNCERTAIN_IMAGE, CROP_MISMATCH)",
    )
    generated_at: Optional[str] = Field(
        default=None,
        description="UTC ISO timestamp of the diagnosis",
    )
    is_llm_generated: bool = Field(
        default=False,
        description="True if explanation was generated by Qwen, False if deterministic fallback",
    )
    fallback_used: bool = Field(
        default=False,
        description="True if deterministic fallback was used instead of Qwen",
    )


class DiseaseRejectionDetail(BaseModel):
    """Standardized rejection response for 400 Bad Request verification failures."""
    model_config = ConfigDict(extra="ignore")

    status: str = Field(default="rejected", description="Always 'rejected'")
    reason_code: str = Field(..., description="Reason code: INVALID_IMAGE, IMAGE_TOO_BLURRY, IMAGE_TOO_DARK, etc.")
    input_verified: bool = Field(default=False, description="Always False for rejected inputs")
    message: str = Field(..., description="Farmer-facing advisory explanation")
    metrics: Optional[Dict[str, Any]] = Field(default=None, description="Verification measurements")
