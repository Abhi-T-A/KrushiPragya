"""Unit tests for FarmerProfileService."""
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.user_profile import UserProfile
from app.schemas.farmer import FarmerProfileCreate, FarmerProfileUpdate
from app.services.farmer_profile_service import (
    FarmerProfileAlreadyExistsError,
    FarmerProfileNotFoundError,
    FarmerProfileService,
)


class InMemorySession:
    """In-memory transactional session simulator for deterministic unit testing."""

    def __init__(self):
        self.store: dict[uuid.UUID, UserProfile] = {}
        self.pending_adds: list[UserProfile] = []
        self.committed = False
        self.rolled_back = False

    def get(self, model, entity_id):
        return self.store.get(entity_id)

    def add(self, obj: UserProfile):
        self.pending_adds.append(obj)

    def commit(self):
        for obj in self.pending_adds:
            if getattr(obj, "created_at", None) is None:
                obj.created_at = datetime.now(timezone.utc)
            if getattr(obj, "updated_at", None) is None:
                obj.updated_at = datetime.now(timezone.utc)
            self.store[obj.id] = obj
        self.pending_adds.clear()
        self.committed = True

    def refresh(self, obj: UserProfile):
        if obj.id in self.store:
            stored = self.store[obj.id]
            obj.created_at = stored.created_at
            obj.updated_at = stored.updated_at

    def rollback(self):
        self.pending_adds.clear()
        self.rolled_back = True


@pytest.fixture
def service():
    return FarmerProfileService()


@pytest.fixture
def db():
    return InMemorySession()


# ==============================================================================
# 1. create_profile Tests
# ==============================================================================

def test_create_profile_success(service, db):
    """Test 1: create_profile successfully creates and returns a profile."""
    farmer_id = uuid.uuid4()
    payload = FarmerProfileCreate(
        id=farmer_id,
        full_name="Mahadevappa",
        phone="9845012345",
        village_id="V001",
        language="kn",
        land_holding_acres=Decimal("6.50"),
    )

    profile = service.create_profile(db, payload)

    assert profile is not None
    assert profile.id == farmer_id
    assert db.committed is True
    assert db.get(UserProfile, farmer_id) is profile


def test_create_profile_persists_all_supplied_fields(service, db):
    """Test 2: create_profile persists all supplied fields accurately."""
    farmer_id = uuid.uuid4()
    payload = FarmerProfileCreate(
        id=farmer_id,
        full_name="Anand Rao",
        phone="+919876543210",
        village_id="V042",
        language="en",
        land_holding_acres=Decimal("15.75"),
    )

    profile = service.create_profile(db, payload)

    assert profile.id == farmer_id
    assert profile.full_name == "Anand Rao"
    assert profile.phone == "+919876543210"
    assert profile.village_id == "V042"
    assert profile.language == "en"
    assert profile.land_holding_acres == Decimal("15.75")
    assert profile.created_at is not None
    assert profile.updated_at is not None


def test_create_profile_duplicate_id_rejected(service, db):
    """Test 3: duplicate profile creation is rejected with FarmerProfileAlreadyExistsError."""
    farmer_id = uuid.uuid4()
    payload = FarmerProfileCreate(
        id=farmer_id,
        full_name="Farmer One",
        language="kn",
    )

    # First creation succeeds
    service.create_profile(db, payload)

    # Second creation with identical ID must raise error
    with pytest.raises(FarmerProfileAlreadyExistsError) as exc_info:
        service.create_profile(db, payload)

    assert str(farmer_id) in str(exc_info.value)


def test_create_profile_integrity_error_handled(service):
    """Test 3b: IntegrityError during commit triggers rollback and raises FarmerProfileAlreadyExistsError."""
    farmer_id = uuid.uuid4()
    payload = FarmerProfileCreate(
        id=farmer_id,
        full_name="Test Integrity",
    )

    mock_db = MagicMock(spec=Session)
    mock_db.get.return_value = None
    mock_db.commit.side_effect = IntegrityError("duplicate key", params=None, orig=Exception("unique constraint"))

    with pytest.raises(FarmerProfileAlreadyExistsError):
        service.create_profile(mock_db, payload)

    mock_db.rollback.assert_called_once()


# ==============================================================================
# 2. get_profile Tests
# ==============================================================================

def test_get_profile_returns_existing_profile(service, db):
    """Test 4: get_profile returns the existing profile ORM object."""
    farmer_id = uuid.uuid4()
    payload = FarmerProfileCreate(
        id=farmer_id,
        full_name="Ramesh Gowda",
        village_id="V010",
    )
    created = service.create_profile(db, payload)

    fetched = service.get_profile(db, farmer_id)

    assert fetched is created
    assert fetched.id == farmer_id
    assert fetched.full_name == "Ramesh Gowda"


def test_get_profile_not_found_raises_error(service, db):
    """Test 5: get_profile raises FarmerProfileNotFoundError for non-existent ID."""
    unknown_id = uuid.uuid4()

    with pytest.raises(FarmerProfileNotFoundError) as exc_info:
        service.get_profile(db, unknown_id)

    assert str(unknown_id) in str(exc_info.value)


# ==============================================================================
# 3. update_profile Tests
# ==============================================================================

def test_update_profile_updates_only_supplied_fields(service, db):
    """Test 6: update_profile updates only the fields supplied in FarmerProfileUpdate."""
    farmer_id = uuid.uuid4()
    initial_payload = FarmerProfileCreate(
        id=farmer_id,
        full_name="Original Name",
        phone="1111111111",
        village_id="V001",
        language="kn",
        land_holding_acres=Decimal("5.00"),
    )
    service.create_profile(db, initial_payload)

    # Update only phone and language
    update_payload = FarmerProfileUpdate(
        phone="9999999999",
        language="en",
    )
    updated = service.update_profile(db, farmer_id, update_payload)

    assert updated.phone == "9999999999"
    assert updated.language == "en"


def test_update_profile_preserves_unspecified_fields(service, db):
    """Test 7: update_profile preserves unspecified fields without overwriting."""
    farmer_id = uuid.uuid4()
    initial_payload = FarmerProfileCreate(
        id=farmer_id,
        full_name="Original Name",
        phone="1111111111",
        village_id="V001",
        language="kn",
        land_holding_acres=Decimal("5.00"),
    )
    service.create_profile(db, initial_payload)

    # Update only land_holding_acres
    update_payload = FarmerProfileUpdate(
        land_holding_acres=Decimal("8.25"),
    )
    updated = service.update_profile(db, farmer_id, update_payload)

    assert updated.land_holding_acres == Decimal("8.25")
    # All other fields must be unchanged
    assert updated.full_name == "Original Name"
    assert updated.phone == "1111111111"
    assert updated.village_id == "V001"
    assert updated.language == "kn"


def test_update_profile_cannot_change_id(service, db):
    """Test 8: update_profile ensures id cannot be modified."""
    farmer_id = uuid.uuid4()
    initial_payload = FarmerProfileCreate(
        id=farmer_id,
        full_name="Locked ID Farmer",
    )
    service.create_profile(db, initial_payload)

    # FarmerProfileUpdate schema does not accept id
    assert "id" not in FarmerProfileUpdate.model_fields

    update_payload = FarmerProfileUpdate(full_name="New Name")
    updated = service.update_profile(db, farmer_id, update_payload)

    assert updated.id == farmer_id


def test_update_profile_not_found_raises_error(service, db):
    """Test 9: update_profile raises FarmerProfileNotFoundError for non-existent ID."""
    unknown_id = uuid.uuid4()
    update_payload = FarmerProfileUpdate(full_name="Nobody")

    with pytest.raises(FarmerProfileNotFoundError) as exc_info:
        service.update_profile(db, unknown_id, update_payload)

    assert str(unknown_id) in str(exc_info.value)


def test_update_profile_explicitly_supplied_nullable_values(service, db):
    """Test 10: explicitly supplied None values are updated while unset fields are preserved."""
    farmer_id = uuid.uuid4()
    initial_payload = FarmerProfileCreate(
        id=farmer_id,
        full_name="Farmer to Clear",
        phone="9845012345",
        village_id="V050",
        land_holding_acres=Decimal("10.00"),
        language="kn",
    )
    service.create_profile(db, initial_payload)

    # Explicitly clear phone and village_id to None, leaving full_name, language, and acres unset
    patch_payload = FarmerProfileUpdate(
        phone=None,
        village_id=None,
    )
    # Verify model_dump(exclude_unset=True) includes explicit None
    dumped = patch_payload.model_dump(exclude_unset=True)
    assert "phone" in dumped and dumped["phone"] is None
    assert "village_id" in dumped and dumped["village_id"] is None
    assert "full_name" not in dumped
    assert "land_holding_acres" not in dumped

    updated = service.update_profile(db, farmer_id, patch_payload)

    # Cleared fields become None
    assert updated.phone is None
    assert updated.village_id is None
    # Unset fields are preserved
    assert updated.full_name == "Farmer to Clear"
    assert updated.land_holding_acres == Decimal("10.00")
    assert updated.language == "kn"


# ==============================================================================
# 4. Transaction & Failure Handling Tests
# ==============================================================================

def test_database_failure_rolls_back_on_create(service):
    """Test 11a: Database failure on create rolls back and re-raises exception."""
    mock_db = MagicMock(spec=Session)
    mock_db.get.return_value = None
    mock_db.commit.side_effect = RuntimeError("Fatal DB Connection Lost")

    payload = FarmerProfileCreate(id=uuid.uuid4(), full_name="Fail Test")

    with pytest.raises(RuntimeError) as exc_info:
        service.create_profile(mock_db, payload)

    assert "Fatal DB Connection Lost" in str(exc_info.value)
    mock_db.rollback.assert_called_once()


def test_database_failure_rolls_back_on_update(service):
    """Test 11b: Database failure on update rolls back and re-raises exception."""
    farmer_id = uuid.uuid4()
    existing_profile = UserProfile(id=farmer_id, full_name="Original")

    mock_db = MagicMock(spec=Session)
    mock_db.get.return_value = existing_profile
    mock_db.commit.side_effect = RuntimeError("Disk full error")

    payload = FarmerProfileUpdate(full_name="New Name")

    with pytest.raises(RuntimeError) as exc_info:
        service.update_profile(mock_db, farmer_id, payload)

    assert "Disk full error" in str(exc_info.value)
    mock_db.rollback.assert_called_once()
