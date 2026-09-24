"""Pydantic schemas for Farmer Profile management in KrushiPragya."""
from datetime import datetime
from decimal import Decimal
from typing import Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator


class FarmerProfileCreate(BaseModel):
    """Schema for creating a new farmer user profile."""

    id: uuid.UUID = Field(
        ...,
        description="User ID referencing Supabase auth.users(id)",
    )
    full_name: Optional[str] = Field(
        default=None,
        max_length=150,
        description="Full name of the farmer/user",
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Contact phone number",
    )
    village_id: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Village ID referencing public.villages",
    )
    language: str = Field(
        default="kn",
        description="Preferred language code ('kn' or 'en')",
    )
    land_holding_acres: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Total land holding area in acres (must be >= 0)",
    )

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        if not v:
            raise ValueError("Language must be either 'kn' or 'en'.")
        norm = v.strip().lower()
        if norm not in ("kn", "en"):
            raise ValueError("Language must be either 'kn' or 'en'.")
        return norm


class FarmerProfileUpdate(BaseModel):
    """Schema for partial update of a farmer profile. All fields optional."""

    full_name: Optional[str] = Field(
        default=None,
        max_length=150,
        description="Full name of the farmer/user",
    )
    phone: Optional[str] = Field(
        default=None,
        max_length=20,
        description="Contact phone number",
    )
    village_id: Optional[str] = Field(
        default=None,
        max_length=50,
        description="Village ID referencing public.villages",
    )
    language: Optional[str] = Field(
        default=None,
        description="Preferred language code ('kn' or 'en')",
    )
    land_holding_acres: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=10,
        decimal_places=2,
        description="Total land holding area in acres (must be >= 0)",
    )

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        norm = v.strip().lower()
        if norm not in ("kn", "en"):
            raise ValueError("Language must be either 'kn' or 'en'.")
        return norm


class FarmerProfileResponse(BaseModel):
    """Schema representing a persisted farmer profile."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(
        ...,
        description="User ID referencing Supabase auth.users(id)",
    )
    full_name: Optional[str] = Field(
        default=None,
        description="Full name of the farmer/user",
    )
    phone: Optional[str] = Field(
        default=None,
        description="Contact phone number",
    )
    village_id: Optional[str] = Field(
        default=None,
        description="Village ID referencing public.villages",
    )
    language: str = Field(
        default="kn",
        description="Preferred language code ('kn' or 'en')",
    )
    land_holding_acres: Optional[Decimal] = Field(
        default=None,
        description="Total land holding area in acres",
    )
    created_at: datetime = Field(
        ...,
        description="Timestamp of profile creation",
    )
    updated_at: datetime = Field(
        ...,
        description="Timestamp of last profile update",
    )
