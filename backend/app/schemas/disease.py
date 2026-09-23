"""Pydantic schemas for Disease Detection module."""
from typing import List
from pydantic import BaseModel, ConfigDict, Field


class ClassPrediction(BaseModel):
    """Individual class prediction with confidence probability."""

    model_config = ConfigDict(extra="forbid")

    class_name: str = Field(..., description="Disease, pest, or healthy condition label")
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Softmax probability score between 0.0 and 1.0",
    )


class DiseasePredictionResponse(BaseModel):
    """Response schema for disease detection inference."""

    model_config = ConfigDict(extra="forbid")

    crop: str = Field(..., description="Normalized crop identifier (e.g. arecanut, paddy)")
    predicted_class: str = Field(
        ...,
        description="Top-1 predicted disease, condition, or healthy status",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Top-1 softmax prediction confidence between 0.0 and 1.0",
    )
    predictions: List[ClassPrediction] = Field(
        default_factory=list,
        description="Ranked list of all class predictions sorted by confidence descending",
    )
    model: str = Field(..., description="Name of the model checkpoint used for inference")
