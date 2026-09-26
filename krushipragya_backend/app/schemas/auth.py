"""Authentication schemas for KrushiPragya Supabase Auth integration."""
from decimal import Decimal
from typing import List, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field, field_validator

from app.schemas.farmer import FarmerProfileResponse


class RegisterRequest(BaseModel):
    """Schema for new farmer user registration."""

    email: str = Field(..., max_length=255, description="Farmer email address for Supabase Auth")
    password: str = Field(..., min_length=6, description="Password (at least 6 characters)")
    full_name: str = Field(..., min_length=1, max_length=150, description="Farmer full name")
    phone: Optional[str] = Field(default=None, max_length=20, description="Contact phone number")
    village_id: Optional[str] = Field(default=None, max_length=50, description="Canonical village ID (e.g. V001)")
    language: str = Field(default="kn", description="Preferred language ('kn' or 'en')")
    land_holding_acres: Optional[Decimal] = Field(
        default=None, ge=0, max_digits=10, decimal_places=2, description="Land holding in acres"
    )

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if "@" not in cleaned or "." not in cleaned.split("@")[-1] or len(cleaned) < 5:
            raise ValueError("Invalid email address format.")
        return cleaned

    @field_validator("language")
    @classmethod
    def validate_language(cls, v: str) -> str:
        norm = v.strip().lower()
        if norm not in ("kn", "en"):
            raise ValueError("Language must be either 'kn' or 'en'.")
        return norm


class LoginRequest(BaseModel):
    """Schema for farmer user login."""

    email: str = Field(..., description="Registered email address")
    password: str = Field(..., description="Account password")

    @field_validator("email")
    @classmethod
    def validate_email(cls, v: str) -> str:
        cleaned = v.strip().lower()
        if "@" not in cleaned or "." not in cleaned.split("@")[-1]:
            raise ValueError("Invalid email address format.")
        return cleaned


class RefreshTokenRequest(BaseModel):
    """Schema for refreshing Supabase access token."""

    refresh_token: str = Field(..., description="Supabase refresh token")


class AuthResponse(BaseModel):
    """Schema returned after successful authentication."""

    model_config = ConfigDict(from_attributes=True)

    access_token: str = Field(..., description="Supabase JWT access token")
    refresh_token: str = Field(..., description="Supabase refresh token")
    token_type: str = Field(default="bearer", description="Token type")
    expires_in: int = Field(default=3600, description="Access token expiry window in seconds")
    user_id: uuid.UUID = Field(..., description="Supabase user UUID")
    email: str = Field(..., description="User email address")
    roles: List[str] = Field(default_factory=list, description="Assigned active role codes")
    profile: Optional[FarmerProfileResponse] = Field(default=None, description="Persisted farmer profile")
