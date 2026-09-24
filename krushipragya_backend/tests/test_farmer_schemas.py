"""Focused unit tests for Farmer Profile Pydantic schemas."""
from datetime import datetime, timezone
from decimal import Decimal
import uuid
import pytest
from pydantic import ValidationError

from app.schemas.farmer import (
    FarmerProfileCreate,
    FarmerProfileResponse,
    FarmerProfileUpdate,
)


class MockUserProfile:
    """Mock representing an SQLAlchemy UserProfile ORM instance."""

    def __init__(
        self,
        id: uuid.UUID,
        full_name: str | None = None,
        phone: str | None = None,
        village_id: str | None = None,
        language: str = "kn",
        land_holding_acres: Decimal | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.id = id
        self.full_name = full_name
        self.phone = phone
        self.village_id = village_id
        self.language = language
        self.land_holding_acres = land_holding_acres
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)


# ==============================================================================
# 1. Valid Creation & Language Handling
# ==============================================================================

def test_valid_creation_with_default_language():
    """Verify that creating a profile without language defaults to 'kn'."""
    user_id = uuid.uuid4()
    profile = FarmerProfileCreate(id=user_id)

    assert profile.id == user_id
    assert profile.language == "kn"
    assert profile.full_name is None
    assert profile.phone is None
    assert profile.village_id is None
    assert profile.land_holding_acres is None


def test_valid_kannada_profile():
    """Verify explicit Kannada profile creation."""
    user_id = uuid.uuid4()
    profile = FarmerProfileCreate(
        id=user_id,
        full_name="ಬಸವರಾಜ್",
        phone="9876543210",
        village_id="V001",
        language="kn",
        land_holding_acres=Decimal("4.50"),
    )

    assert profile.id == user_id
    assert profile.language == "kn"
    assert profile.full_name == "ಬಸವರಾಜ್"
    assert profile.land_holding_acres == Decimal("4.50")


def test_valid_english_profile():
    """Verify explicit English profile creation."""
    user_id = uuid.uuid4()
    profile = FarmerProfileCreate(
        id=user_id,
        full_name="Basavaraj Patil",
        phone="+919876543210",
        village_id="V002",
        language="en",
        land_holding_acres=Decimal("12.00"),
    )

    assert profile.id == user_id
    assert profile.language == "en"
    assert profile.full_name == "Basavaraj Patil"
    assert profile.land_holding_acres == Decimal("12.00")


def test_language_normalization_case_and_whitespace():
    """Verify uppercase or spaced language codes are normalized."""
    user_id = uuid.uuid4()
    profile_kn = FarmerProfileCreate(id=user_id, language="  KN ")
    assert profile_kn.language == "kn"

    profile_en = FarmerProfileCreate(id=user_id, language="En ")
    assert profile_en.language == "en"


def test_invalid_language_create_rejected():
    """Verify invalid language codes are rejected during creation."""
    user_id = uuid.uuid4()
    for bad_lang in ["hi", "te", "ta", "es", "french", ""]:
        with pytest.raises(ValidationError) as exc_info:
            FarmerProfileCreate(id=user_id, language=bad_lang)
        assert "language" in str(exc_info.value).lower()


def test_invalid_language_update_rejected():
    """Verify invalid language codes are rejected during update."""
    for bad_lang in ["hi", "kannada", "english", "123"]:
        with pytest.raises(ValidationError) as exc_info:
            FarmerProfileUpdate(language=bad_lang)
        assert "language" in str(exc_info.value).lower()


# ==============================================================================
# 2. Land Holding Validation
# ==============================================================================

def test_negative_land_holding_acres_rejected():
    """Verify negative land_holding_acres is rejected in create and update."""
    user_id = uuid.uuid4()

    # Create schema negative rejected
    with pytest.raises(ValidationError) as exc_info:
        FarmerProfileCreate(id=user_id, land_holding_acres=Decimal("-0.01"))
    assert "land_holding_acres" in str(exc_info.value)

    # Update schema negative rejected
    with pytest.raises(ValidationError) as exc_info:
        FarmerProfileUpdate(land_holding_acres=Decimal("-5.0"))
    assert "land_holding_acres" in str(exc_info.value)


def test_zero_and_positive_land_holding_acres_accepted():
    """Verify zero and positive values are valid land holdings."""
    user_id = uuid.uuid4()

    # Zero acres
    profile_zero = FarmerProfileCreate(id=user_id, land_holding_acres=Decimal("0.00"))
    assert profile_zero.land_holding_acres == Decimal("0.00")

    # Positive acres
    update_pos = FarmerProfileUpdate(land_holding_acres=Decimal("25.75"))
    assert update_pos.land_holding_acres == Decimal("25.75")


# ==============================================================================
# 3. String Length Validation
# ==============================================================================

def test_string_length_validation_create():
    """Verify max length constraints on full_name (150), phone (20), village_id (50)."""
    user_id = uuid.uuid4()

    # Valid boundary lengths
    valid_create = FarmerProfileCreate(
        id=user_id,
        full_name="A" * 150,
        phone="1" * 20,
        village_id="V" * 50,
    )
    assert len(valid_create.full_name) == 150
    assert len(valid_create.phone) == 20
    assert len(valid_create.village_id) == 50

    # Exceeding full_name > 150
    with pytest.raises(ValidationError) as exc_info:
        FarmerProfileCreate(id=user_id, full_name="A" * 151)
    assert "full_name" in str(exc_info.value)

    # Exceeding phone > 20
    with pytest.raises(ValidationError) as exc_info:
        FarmerProfileCreate(id=user_id, phone="1" * 21)
    assert "phone" in str(exc_info.value)

    # Exceeding village_id > 50
    with pytest.raises(ValidationError) as exc_info:
        FarmerProfileCreate(id=user_id, village_id="V" * 51)
    assert "village_id" in str(exc_info.value)


def test_string_length_validation_update():
    """Verify max length constraints on FarmerProfileUpdate."""
    # Exceeding full_name > 150
    with pytest.raises(ValidationError) as exc_info:
        FarmerProfileUpdate(full_name="B" * 151)
    assert "full_name" in str(exc_info.value)

    # Exceeding phone > 20
    with pytest.raises(ValidationError) as exc_info:
        FarmerProfileUpdate(phone="9" * 21)
    assert "phone" in str(exc_info.value)

    # Exceeding village_id > 50
    with pytest.raises(ValidationError) as exc_info:
        FarmerProfileUpdate(village_id="V" * 51)
    assert "village_id" in str(exc_info.value)


# ==============================================================================
# 4. Update Schema Partial / Optional Fields
# ==============================================================================

def test_update_schema_does_not_require_all_fields():
    """Verify FarmerProfileUpdate allows empty instantiation and partial updates."""
    # Completely empty update
    empty_update = FarmerProfileUpdate()
    assert empty_update.full_name is None
    assert empty_update.phone is None
    assert empty_update.village_id is None
    assert empty_update.language is None
    assert empty_update.land_holding_acres is None

    # Partial update with only one field
    name_update = FarmerProfileUpdate(full_name="Shankar Gowda")
    assert name_update.full_name == "Shankar Gowda"
    assert name_update.phone is None
    assert name_update.village_id is None

    # Exclude unset fields when dumping for PATCH
    dumped = name_update.model_dump(exclude_unset=True)
    assert dumped == {"full_name": "Shankar Gowda"}


def test_update_schema_does_not_have_id_field():
    """Verify id is not an accepted field in FarmerProfileUpdate."""
    assert "id" not in FarmerProfileUpdate.model_fields


# ==============================================================================
# 5. Response Schema ORM Serialization
# ==============================================================================

def test_response_schema_can_serialize_orm_style_data():
    """Verify FarmerProfileResponse can serialize an ORM-style object."""
    user_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_orm = MockUserProfile(
        id=user_id,
        full_name="Mahadevappa",
        phone="+919845012345",
        village_id="V042",
        language="kn",
        land_holding_acres=Decimal("7.25"),
        created_at=now,
        updated_at=now,
    )

    response = FarmerProfileResponse.model_validate(mock_orm)

    assert response.id == user_id
    assert response.full_name == "Mahadevappa"
    assert response.phone == "+919845012345"
    assert response.village_id == "V042"
    assert response.language == "kn"
    assert response.land_holding_acres == Decimal("7.25")
    assert response.created_at == now
    assert response.updated_at == now

    # Also check JSON serialization roundtrip
    json_data = response.model_dump(mode="json")
    assert json_data["id"] == str(user_id)
    assert json_data["language"] == "kn"
    assert json_data["land_holding_acres"] == "7.25"
