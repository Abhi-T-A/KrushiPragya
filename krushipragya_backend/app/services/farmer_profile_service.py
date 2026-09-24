"""Farmer Profile Service for KrushiPragya.

Manages farmer profile creation, retrieval, and partial updates (PATCH)
linked to Supabase auth.users UUIDs.
"""
import logging
from typing import Optional
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user_profile import UserProfile
from app.schemas.farmer import FarmerProfileCreate, FarmerProfileUpdate

logger = logging.getLogger(__name__)


# ==============================================================================
# Domain Exceptions
# ==============================================================================

class FarmerProfileError(Exception):
    """Base exception for farmer profile operations."""
    pass


class FarmerProfileNotFoundError(FarmerProfileError):
    """Raised when a farmer profile with the requested ID is not found."""
    pass


class FarmerProfileAlreadyExistsError(FarmerProfileError):
    """Raised when attempting to create a profile that already exists."""
    pass


# ==============================================================================
# Service Implementation
# ==============================================================================

class FarmerProfileService:
    """Service layer managing farmer user profile lifecycle."""

    def create_profile(
        self,
        db: Session,
        payload: FarmerProfileCreate,
    ) -> UserProfile:
        """Create a new UserProfile linked to Supabase auth.users UUID.

        Args:
            db: SQLAlchemy session
            payload: Validated farmer profile creation schema

        Returns:
            UserProfile: The persisted and refreshed ORM instance

        Raises:
            FarmerProfileAlreadyExistsError: If a profile with the ID already exists
        """
        # Pre-check for duplicate profile id
        existing = db.get(UserProfile, payload.id)
        if existing is not None:
            logger.warning("Farmer profile already exists for ID: %s", payload.id)
            raise FarmerProfileAlreadyExistsError(
                f"Farmer profile with ID '{payload.id}' already exists."
            )

        profile = UserProfile(
            id=payload.id,
            full_name=payload.full_name,
            phone=payload.phone,
            village_id=payload.village_id,
            language=payload.language,
            land_holding_acres=payload.land_holding_acres,
        )

        try:
            db.add(profile)
            db.commit()
            db.refresh(profile)
            logger.info("Successfully created farmer profile for ID: %s", payload.id)
            return profile
        except IntegrityError as exc:
            db.rollback()
            logger.warning("IntegrityError creating profile for ID %s: %s", payload.id, exc)
            raise FarmerProfileAlreadyExistsError(
                f"Farmer profile with ID '{payload.id}' already exists."
            ) from exc
        except Exception:
            db.rollback()
            raise

    def get_profile(
        self,
        db: Session,
        farmer_id: uuid.UUID,
    ) -> UserProfile:
        """Retrieve an existing farmer profile by user UUID.

        Args:
            db: SQLAlchemy session
            farmer_id: UUID of the farmer

        Returns:
            UserProfile: Persisted profile ORM instance

        Raises:
            FarmerProfileNotFoundError: If the profile is not found
        """
        profile = db.get(UserProfile, farmer_id)
        if profile is None:
            logger.warning("Farmer profile not found for ID: %s", farmer_id)
            raise FarmerProfileNotFoundError(
                f"Farmer profile with ID '{farmer_id}' not found."
            )
        return profile

    def update_profile(
        self,
        db: Session,
        farmer_id: uuid.UUID,
        payload: FarmerProfileUpdate,
    ) -> UserProfile:
        """Update an existing farmer profile using partial (PATCH) semantics.

        Updates only fields explicitly supplied in the request. Never overwrites
        unspecified fields, and never allows modifying the profile ID.

        Args:
            db: SQLAlchemy session
            farmer_id: UUID of the farmer to update
            payload: Validated partial update schema

        Returns:
            UserProfile: Updated and refreshed ORM instance

        Raises:
            FarmerProfileNotFoundError: If the profile is not found
        """
        profile = self.get_profile(db, farmer_id)

        update_data = payload.model_dump(exclude_unset=True)
        # Prevent any modification of the primary key
        update_data.pop("id", None)

        for field_name, value in update_data.items():
            if hasattr(profile, field_name):
                setattr(profile, field_name, value)

        try:
            db.commit()
            db.refresh(profile)
            logger.info(
                "Successfully updated farmer profile for ID: %s (fields: %s)",
                farmer_id,
                list(update_data.keys()),
            )
            return profile
        except Exception:
            db.rollback()
            raise
