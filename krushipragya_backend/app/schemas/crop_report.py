"""Pydantic schemas for Crop Report and Disease Report domain."""
from datetime import datetime
from typing import List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.disease import ClassPrediction
from app.schemas.farmer_crop import CropResponse


class CropReportCreate(BaseModel):
    """Schema representing a farmer submitting a new crop-health observation."""

    farmer_crop_id: uuid.UUID = Field(
        ...,
        description="Foreign key referencing farmer_crops.id",
    )
    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Optional notes or observation text from the farmer (max 1000 chars)",
    )
    image_filename: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Optional original filename of the uploaded image (max 255 chars)",
    )


class CropReportUpdate(BaseModel):
    """Schema for partial update of farmer-entered report metadata (PATCH semantics)."""

    notes: Optional[str] = Field(
        default=None,
        max_length=1000,
        description="Updated notes or observation text from the farmer (max 1000 chars)",
    )
    image_filename: Optional[str] = Field(
        default=None,
        max_length=255,
        description="Updated original filename of the image (max 255 chars)",
    )


class CropReportResponse(BaseModel):
    """Schema representing a persisted crop-health report."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(
        ...,
        description="Primary key unique identifier for the crop report",
    )
    farmer_crop_id: uuid.UUID = Field(
        ...,
        description="Foreign key referencing farmer_crops.id",
    )
    notes: Optional[str] = Field(
        default=None,
        description="Notes or observation text from the farmer",
    )
    image_filename: Optional[str] = Field(
        default=None,
        description="Original filename of the uploaded image",
    )
    image_storage_path: Optional[str] = Field(
        default=None,
        description="Internal reference path to the stored image in storage bucket",
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when report was created",
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when report was last updated",
    )


class CropReportWithCropResponse(CropReportResponse):
    """Schema representing a crop report including canonical crop details."""

    crop: CropResponse = Field(
        ...,
        description="Canonical crop catalog details for client applications",
    )


class CropReportImageResponse(BaseModel):
    """Schema representing image information returned after a successful image upload."""

    report_id: uuid.UUID = Field(
        ...,
        description="Unique identifier of the crop report associated with this image",
    )
    image_filename: str = Field(
        ...,
        max_length=255,
        description="Filename of the uploaded image",
    )
    image_storage_path: str = Field(
        ...,
        description="Internal reference path to the stored image in storage bucket",
    )
    content_type: str = Field(
        ...,
        description="MIME type representing the image (e.g. image/jpeg, image/png)",
    )
    size_bytes: int = Field(
        ...,
        ge=0,
        description="File size in bytes (must be non-negative)",
    )

    @field_validator("content_type")
    @classmethod
    def validate_image_content_type(cls, v: str) -> str:
        """Ensure content_type represents an image MIME type within image/*."""
        if not v or not v.startswith("image/"):
            raise ValueError("content_type must represent an image MIME type starting with 'image/'")
        return v


class DiseasePredictionResult(BaseModel):
    """Response contract for disease detection model inference result."""

    crop: str = Field(
        ...,
        description="Normalized crop identifier (e.g. arecanut, paddy)",
    )
    predicted_class: str = Field(
        ...,
        description="Top-1 predicted disease condition or healthy status",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Prediction confidence score between 0.0 and 1.0",
    )


class CropReportDiagnosisResponse(BaseModel):
    """Combined response schema containing persisted crop report and disease prediction."""

    model_config = ConfigDict(from_attributes=True)

    report: CropReportResponse = Field(
        ...,
        description="Persisted crop report data",
    )
    prediction: DiseasePredictionResult = Field(
        ...,
        description="Disease diagnosis prediction result",
    )


class CropReportDiagnosisRecordResponse(BaseModel):
    """Schema representing a persisted crop report disease diagnosis record."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(
        ...,
        description="Primary key unique identifier for the diagnosis record",
    )
    crop_report_id: uuid.UUID = Field(
        ...,
        description="Foreign key referencing crop_reports.id",
    )
    crop: str = Field(
        ...,
        description="Normalized crop identifier used during disease inference",
    )
    predicted_class: str = Field(
        ...,
        description="Top-1 predicted condition label",
    )
    confidence: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="Top-1 prediction confidence score between 0.0 and 1.0",
    )
    model_name: str = Field(
        ...,
        description="Model checkpoint filename or identifier used for inference",
    )
    predictions: List[ClassPrediction] = Field(
        default_factory=list,
        description="Full ranked list of class predictions and probabilities",
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when diagnosis was generated and persisted",
    )
