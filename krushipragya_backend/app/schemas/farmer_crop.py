"""Pydantic schemas for Farmer Crop Management and Crop catalog."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field


class CropResponse(BaseModel):
    """Schema representing a canonical crop from the crops catalog."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(
        ...,
        description="Primary key unique identifier for the crop",
    )
    code: str = Field(
        ...,
        max_length=50,
        description="Canonical machine-readable identifier (e.g. arecanut, paddy)",
    )
    name_en: str = Field(
        ...,
        max_length=100,
        description="English display name of the crop",
    )
    name_kn: str = Field(
        ...,
        max_length=100,
        description="Kannada display name of the crop",
    )
    is_active: bool = Field(
        ...,
        description="Flag indicating if crop is actively supported",
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp of crop record creation",
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp of last update to crop record",
    )


class FarmerCropCreate(BaseModel):
    """Schema for registering a crop cultivated by a farmer."""

    crop_id: uuid.UUID = Field(
        ...,
        description="Foreign key referencing canonical crop catalog ID",
    )
    area_acres: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Cultivated area in acres (>= 0)",
    )
    is_primary: bool = Field(
        default=False,
        description="Flag indicating if this is the farmer's primary cultivated crop",
    )


class FarmerCropUpdate(BaseModel):
    """Schema for partial update of a farmer crop association (PATCH)."""

    area_acres: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Cultivated area in acres (>= 0)",
    )
    is_primary: Optional[bool] = Field(
        default=None,
        description="Flag indicating if this is the farmer's primary cultivated crop",
    )


class FarmerCropResponse(BaseModel):
    """Schema representing a persisted farmer-crop relationship."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(
        ...,
        description="Primary key unique identifier for farmer-crop relationship",
    )
    farmer_id: uuid.UUID = Field(
        ...,
        description="Foreign key referencing user_profiles.id",
    )
    crop_id: uuid.UUID = Field(
        ...,
        description="Foreign key referencing crops.id",
    )
    area_acres: Optional[Decimal] = Field(
        default=None,
        description="Cultivated area in acres",
    )
    is_primary: bool = Field(
        ...,
        description="Flag indicating if this is the farmer's primary cultivated crop",
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp when relationship was created",
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp when relationship was last updated",
    )


class FarmerCropWithDetailsResponse(FarmerCropResponse):
    """Schema representing a farmer-crop relationship including canonical crop details."""

    crop: CropResponse = Field(
        ...,
        description="Canonical crop catalog details",
    )
