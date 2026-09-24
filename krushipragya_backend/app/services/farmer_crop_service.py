"""Farmer Crop Service for KrushiPragya.

Manages canonical crop catalog querying, farmer crop registrations,
updates, and deletions with ownership validation and transaction safety.
"""
import logging
from typing import List, Optional
import uuid

from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.models.crop import Crop
from app.models.farmer_crop import FarmerCrop
from app.models.user_profile import UserProfile
from app.schemas.farmer_crop import FarmerCropCreate, FarmerCropUpdate

logger = logging.getLogger(__name__)


# ==============================================================================
# Domain Exceptions
# ==============================================================================

class FarmerCropError(Exception):
    """Base exception for farmer crop operations."""
    pass


class FarmerNotFoundError(FarmerCropError):
    """Raised when a farmer profile does not exist."""
    pass


class CropNotFoundError(FarmerCropError):
    """Raised when a canonical crop catalog entry is not found."""
    pass


class InactiveCropError(FarmerCropError):
    """Raised when attempting to associate an inactive crop."""
    pass


class FarmerCropAlreadyExistsError(FarmerCropError):
    """Raised when a farmer-crop relationship already exists."""
    pass


class FarmerCropNotFoundError(FarmerCropError):
    """Raised when a farmer-crop relationship does not exist or does not belong to the farmer."""
    pass


# ==============================================================================
# Service Implementation
# ==============================================================================

class FarmerCropService:
    """Service layer managing canonical crops and farmer crop associations."""

    def list_crops(self, db: Session, active_only: bool = True) -> List[Crop]:
        """Return canonical crops from the catalog in deterministic order.

        Args:
            db: SQLAlchemy session
            active_only: If True, filters only active crops. Defaults to True.

        Returns:
            List[Crop]: List of Crop ORM objects ordered alphabetically by English name.
        """
        query = db.query(Crop)
        if active_only:
            query = query.filter(Crop.is_active.is_(True))
        return query.order_by(Crop.name_en.asc()).all()

    def get_crop(self, db: Session, crop_id: uuid.UUID) -> Crop:
        """Retrieve a single canonical crop by ID.

        Args:
            db: SQLAlchemy session
            crop_id: UUID of the crop

        Returns:
            Crop: The Crop ORM instance

        Raises:
            CropNotFoundError: If the crop does not exist
        """
        crop = db.get(Crop, crop_id)
        if crop is None:
            logger.warning("Crop not found with ID: %s", crop_id)
            raise CropNotFoundError(f"Crop with ID '{crop_id}' not found.")
        return crop

    def add_farmer_crop(
        self,
        db: Session,
        farmer_id: uuid.UUID,
        payload: FarmerCropCreate,
    ) -> FarmerCrop:
        """Register a crop for a farmer after validating existence, status, and uniqueness.

        Args:
            db: SQLAlchemy session
            farmer_id: UUID of the farmer
            payload: Validated crop creation payload

        Returns:
            FarmerCrop: Persisted and refreshed FarmerCrop ORM instance

        Raises:
            FarmerNotFoundError: If the farmer does not exist
            CropNotFoundError: If the crop does not exist
            InactiveCropError: If the crop exists but is marked inactive
            FarmerCropAlreadyExistsError: If the farmer already cultivates this crop
        """
        # 1. Verify farmer exists
        farmer = db.get(UserProfile, farmer_id)
        if farmer is None:
            logger.warning("Farmer not found for ID: %s", farmer_id)
            raise FarmerNotFoundError(f"Farmer with ID '{farmer_id}' not found.")

        # 2. Verify crop exists
        crop = db.get(Crop, payload.crop_id)
        if crop is None:
            logger.warning("Crop not found for ID: %s", payload.crop_id)
            raise CropNotFoundError(f"Crop with ID '{payload.crop_id}' not found.")

        # 3. Verify crop is active
        if not crop.is_active:
            logger.warning("Crop '%s' (%s) is inactive", crop.name_en, crop.id)
            raise InactiveCropError(
                f"Crop '{crop.name_en}' is inactive and cannot be registered."
            )

        # 4. Check for duplicate farmer-crop relationship
        existing = (
            db.query(FarmerCrop)
            .filter(
                FarmerCrop.farmer_id == farmer_id,
                FarmerCrop.crop_id == payload.crop_id,
            )
            .first()
        )
        if existing is not None:
            logger.warning(
                "Farmer %s already has crop %s registered",
                farmer_id,
                payload.crop_id,
            )
            raise FarmerCropAlreadyExistsError(
                f"Farmer already has crop '{crop.name_en}' registered."
            )

        farmer_crop = FarmerCrop(
            id=uuid.uuid4(),
            farmer_id=farmer_id,
            crop_id=payload.crop_id,
            area_acres=payload.area_acres,
            is_primary=payload.is_primary,
        )
        # Attach crop relation in-memory for immediate access
        farmer_crop.crop = crop

        try:
            db.add(farmer_crop)
            db.commit()
            db.refresh(farmer_crop)
            logger.info(
                "Successfully added crop '%s' for farmer %s (primary=%s)",
                crop.name_en,
                farmer_id,
                payload.is_primary,
            )
            return farmer_crop
        except IntegrityError as exc:
            db.rollback()
            logger.warning(
                "IntegrityError adding crop %s for farmer %s: %s",
                payload.crop_id,
                farmer_id,
                exc,
            )
            raise FarmerCropAlreadyExistsError(
                f"Farmer already has crop '{crop.name_en}' registered."
            ) from exc
        except Exception:
            db.rollback()
            raise

    def list_farmer_crops(self, db: Session, farmer_id: uuid.UUID) -> List[FarmerCrop]:
        """Return all crop relationships belonging to the specified farmer.

        Args:
            db: SQLAlchemy session
            farmer_id: UUID of the farmer

        Returns:
            List[FarmerCrop]: List of FarmerCrop ORM instances with loaded Crop relation

        Raises:
            FarmerNotFoundError: If the farmer does not exist
        """
        farmer = db.get(UserProfile, farmer_id)
        if farmer is None:
            logger.warning("Farmer not found for ID: %s", farmer_id)
            raise FarmerNotFoundError(f"Farmer with ID '{farmer_id}' not found.")

        return (
            db.query(FarmerCrop)
            .options(selectinload(FarmerCrop.crop))
            .filter(FarmerCrop.farmer_id == farmer_id)
            .order_by(FarmerCrop.created_at.asc())
            .all()
        )

    def get_farmer_crop(
        self,
        db: Session,
        farmer_id: uuid.UUID,
        farmer_crop_id: uuid.UUID,
    ) -> FarmerCrop:
        """Retrieve a specific farmer crop relationship strictly enforcing ownership.

        Args:
            db: SQLAlchemy session
            farmer_id: UUID of the farmer
            farmer_crop_id: UUID of the farmer-crop relationship

        Returns:
            FarmerCrop: Persisted FarmerCrop ORM instance

        Raises:
            FarmerNotFoundError: If the farmer does not exist
            FarmerCropNotFoundError: If the relationship does not exist or does not belong to the farmer
        """
        farmer = db.get(UserProfile, farmer_id)
        if farmer is None:
            logger.warning("Farmer not found for ID: %s", farmer_id)
            raise FarmerNotFoundError(f"Farmer with ID '{farmer_id}' not found.")

        farmer_crop = (
            db.query(FarmerCrop)
            .options(selectinload(FarmerCrop.crop))
            .filter(
                FarmerCrop.id == farmer_crop_id,
                FarmerCrop.farmer_id == farmer_id,
            )
            .first()
        )
        if farmer_crop is None:
            logger.warning(
                "FarmerCrop %s not found for farmer %s",
                farmer_crop_id,
                farmer_id,
            )
            raise FarmerCropNotFoundError(
                f"Farmer crop with ID '{farmer_crop_id}' not found for farmer '{farmer_id}'."
            )
        return farmer_crop

    def update_farmer_crop(
        self,
        db: Session,
        farmer_id: uuid.UUID,
        farmer_crop_id: uuid.UUID,
        payload: FarmerCropUpdate,
    ) -> FarmerCrop:
        """Partially update mutable fields (area_acres, is_primary) of a farmer crop relationship.

        Args:
            db: SQLAlchemy session
            farmer_id: UUID of the farmer
            farmer_crop_id: UUID of the farmer-crop relationship
            payload: Validated partial update schema

        Returns:
            FarmerCrop: Updated and refreshed FarmerCrop ORM instance

        Raises:
            FarmerNotFoundError: If the farmer does not exist
            FarmerCropNotFoundError: If the relationship does not exist or does not belong to the farmer
        """
        farmer_crop = self.get_farmer_crop(
            db=db,
            farmer_id=farmer_id,
            farmer_crop_id=farmer_crop_id,
        )

        update_data = payload.model_dump(exclude_unset=True)
        # Disallow mutating immutable identity and foreign keys
        update_data.pop("id", None)
        update_data.pop("farmer_id", None)
        update_data.pop("crop_id", None)

        for field_name, value in update_data.items():
            if hasattr(farmer_crop, field_name):
                setattr(farmer_crop, field_name, value)

        try:
            db.commit()
            db.refresh(farmer_crop)
            logger.info(
                "Updated FarmerCrop %s for farmer %s (fields: %s)",
                farmer_crop_id,
                farmer_id,
                list(update_data.keys()),
            )
            return farmer_crop
        except Exception:
            db.rollback()
            raise

    def delete_farmer_crop(
        self,
        db: Session,
        farmer_id: uuid.UUID,
        farmer_crop_id: uuid.UUID,
    ) -> FarmerCrop:
        """Delete a farmer crop relationship strictly enforcing ownership.

        Does not delete the underlying Crop catalog entry or UserProfile.

        Args:
            db: SQLAlchemy session
            farmer_id: UUID of the farmer
            farmer_crop_id: UUID of the farmer-crop relationship

        Returns:
            FarmerCrop: The deleted FarmerCrop instance

        Raises:
            FarmerNotFoundError: If the farmer does not exist
            FarmerCropNotFoundError: If the relationship does not exist or does not belong to the farmer
        """
        farmer_crop = self.get_farmer_crop(
            db=db,
            farmer_id=farmer_id,
            farmer_crop_id=farmer_crop_id,
        )

        try:
            db.delete(farmer_crop)
            db.commit()
            logger.info(
                "Successfully deleted FarmerCrop %s for farmer %s",
                farmer_crop_id,
                farmer_id,
            )
            return farmer_crop
        except Exception:
            db.rollback()
            raise
