"""Unit tests for FarmerCropService."""
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
import uuid
import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.models.crop import Crop
from app.models.farmer_crop import FarmerCrop
from app.models.user_profile import UserProfile
from app.schemas.farmer_crop import FarmerCropCreate, FarmerCropUpdate
from app.services.farmer_crop_service import (
    CropNotFoundError,
    FarmerCropAlreadyExistsError,
    FarmerCropNotFoundError,
    FarmerCropService,
    FarmerNotFoundError,
    InactiveCropError,
)


class InMemorySession:
    """In-memory transactional session simulator supporting UserProfile, Crop, and FarmerCrop."""

    def __init__(self):
        self.crops: dict[uuid.UUID, Crop] = {}
        self.farmers: dict[uuid.UUID, UserProfile] = {}
        self.farmer_crops: dict[uuid.UUID, FarmerCrop] = {}
        self.pending_adds: list[object] = []
        self.committed = False
        self.rolled_back = False

    def get(self, model, entity_id):
        if model is Crop:
            return self.crops.get(entity_id)
        if model is UserProfile:
            return self.farmers.get(entity_id)
        if model is FarmerCrop:
            return self.farmer_crops.get(entity_id)
        return None

    def query(self, model):
        if model is Crop:
            items = list(self.crops.values())
        elif model is FarmerCrop:
            items = list(self.farmer_crops.values())
        elif model is UserProfile:
            items = list(self.farmers.values())
        else:
            items = []
        return FakeQuery(items)

    def add(self, obj):
        self.pending_adds.append(obj)

    def commit(self):
        for obj in self.pending_adds:
            if getattr(obj, "created_at", None) is None:
                obj.created_at = datetime.now(timezone.utc)
            if getattr(obj, "updated_at", None) is None:
                obj.updated_at = datetime.now(timezone.utc)

            if isinstance(obj, Crop):
                self.crops[obj.id] = obj
            elif isinstance(obj, UserProfile):
                self.farmers[obj.id] = obj
            elif isinstance(obj, FarmerCrop):
                self.farmer_crops[obj.id] = obj
        self.pending_adds.clear()
        self.committed = True

    def refresh(self, obj):
        pass

    def delete(self, obj):
        if isinstance(obj, FarmerCrop) and obj.id in self.farmer_crops:
            del self.farmer_crops[obj.id]

    def rollback(self):
        self.pending_adds.clear()
        self.rolled_back = True


class FakeQuery:
    """Query object simulator for FakeCropSession."""

    def __init__(self, items):
        self.items = list(items)

    def options(self, *args, **kwargs):
        return self

    def filter(self, *criteria):
        filtered = []
        for item in self.items:
            matches = True
            for c in criteria:
                col_name = getattr(c.left, "key", getattr(c.left, "name", None))
                target_val = getattr(c.right, "value", True)
                if getattr(item, col_name) != target_val:
                    matches = False
                    break
            if matches:
                filtered.append(item)
        return FakeQuery(filtered)

    def order_by(self, *args):
        def sort_key(item):
            if hasattr(item, "name_en"):
                return str(item.name_en)
            if hasattr(item, "created_at"):
                return item.created_at or datetime.min.replace(tzinfo=timezone.utc)
            return 0
        return FakeQuery(sorted(self.items, key=sort_key))

    def all(self):
        return list(self.items)

    def first(self):
        return self.items[0] if self.items else None


@pytest.fixture
def service():
    return FarmerCropService()


@pytest.fixture
def db():
    session = InMemorySession()
    return session


@pytest.fixture
def active_crop(db):
    crop = Crop(
        id=uuid.uuid4(),
        code="arecanut",
        name_en="Arecanut",
        name_kn="ಅಡಿಕೆ",
        is_active=True,
    )
    db.add(crop)
    db.commit()
    return crop


@pytest.fixture
def inactive_crop(db):
    crop = Crop(
        id=uuid.uuid4(),
        code="tobacco",
        name_en="Tobacco",
        name_kn="ತಂಬಾಕು",
        is_active=False,
    )
    db.add(crop)
    db.commit()
    return crop


@pytest.fixture
def registered_farmer(db):
    farmer = UserProfile(
        id=uuid.uuid4(),
        full_name="Basavaraj",
        language="kn",
    )
    db.add(farmer)
    db.commit()
    return farmer


# ==============================================================================
# 1. list_crops & get_crop Tests
# ==============================================================================

def test_list_crops_returns_active_crops(service, db, active_crop, inactive_crop):
    """Test 1: list_crops returns active crops."""
    crops = service.list_crops(db)
    assert len(crops) == 1
    assert crops[0].id == active_crop.id
    assert crops[0].is_active is True


def test_inactive_crops_excluded_from_default_listing(service, db, active_crop, inactive_crop):
    """Test 2: inactive crops are excluded from default crop listing."""
    default_crops = service.list_crops(db, active_only=True)
    assert inactive_crop not in default_crops

    all_crops = service.list_crops(db, active_only=False)
    assert len(all_crops) == 2


def test_get_crop_returns_existing_crop(service, db, active_crop):
    """Test 3: get_crop returns an existing crop."""
    crop = service.get_crop(db, active_crop.id)
    assert crop.id == active_crop.id
    assert crop.code == "arecanut"


def test_get_crop_raises_crop_not_found(service, db):
    """Test 4: get_crop raises CropNotFoundError for unknown crop."""
    random_id = uuid.uuid4()
    with pytest.raises(CropNotFoundError) as exc_info:
        service.get_crop(db, random_id)
    assert str(random_id) in str(exc_info.value)


# ==============================================================================
# 2. add_farmer_crop Tests
# ==============================================================================

def test_add_farmer_crop_successfully_creates_relationship(service, db, registered_farmer, active_crop):
    """Test 5: add_farmer_crop successfully creates a relationship."""
    payload = FarmerCropCreate(
        crop_id=active_crop.id,
        area_acres=Decimal("5.00"),
        is_primary=True,
    )
    fc = service.add_farmer_crop(db, registered_farmer.id, payload)

    assert fc is not None
    assert fc.farmer_id == registered_farmer.id
    assert fc.crop_id == active_crop.id
    assert fc.area_acres == Decimal("5.00")
    assert fc.is_primary is True
    assert fc.crop is active_crop


def test_add_farmer_crop_rejects_unknown_farmer(service, db, active_crop):
    """Test 6: add_farmer_crop rejects unknown farmer."""
    random_farmer_id = uuid.uuid4()
    payload = FarmerCropCreate(crop_id=active_crop.id)

    with pytest.raises(FarmerNotFoundError) as exc_info:
        service.add_farmer_crop(db, random_farmer_id, payload)
    assert str(random_farmer_id) in str(exc_info.value)


def test_add_farmer_crop_rejects_unknown_crop(service, db, registered_farmer):
    """Test 7: add_farmer_crop rejects unknown crop."""
    random_crop_id = uuid.uuid4()
    payload = FarmerCropCreate(crop_id=random_crop_id)

    with pytest.raises(CropNotFoundError) as exc_info:
        service.add_farmer_crop(db, registered_farmer.id, payload)
    assert str(random_crop_id) in str(exc_info.value)


def test_add_farmer_crop_rejects_inactive_crop(service, db, registered_farmer, inactive_crop):
    """Test 8: add_farmer_crop rejects inactive crop."""
    payload = FarmerCropCreate(crop_id=inactive_crop.id)

    with pytest.raises(InactiveCropError) as exc_info:
        service.add_farmer_crop(db, registered_farmer.id, payload)
    assert "inactive" in str(exc_info.value).lower()


def test_duplicate_farmer_crop_registration_rejected(service, db, registered_farmer, active_crop):
    """Test 9: duplicate farmer-crop registration is rejected."""
    payload = FarmerCropCreate(crop_id=active_crop.id)

    # First succeeds
    service.add_farmer_crop(db, registered_farmer.id, payload)

    # Second fails
    with pytest.raises(FarmerCropAlreadyExistsError):
        service.add_farmer_crop(db, registered_farmer.id, payload)


# ==============================================================================
# 3. list_farmer_crops & get_farmer_crop Tests
# ==============================================================================

def test_list_farmer_crops_returns_only_requested_farmers_crops(service, db, registered_farmer, active_crop):
    """Test 10: list_farmer_crops returns only the requested farmer's crops."""
    # Farmer 1
    service.add_farmer_crop(db, registered_farmer.id, FarmerCropCreate(crop_id=active_crop.id))

    # Farmer 2 with a different crop
    farmer2 = UserProfile(id=uuid.uuid4(), full_name="Farmer Two")
    crop2 = Crop(id=uuid.uuid4(), code="paddy", name_en="Paddy", name_kn="ಭತ್ತ", is_active=True)
    db.add(farmer2)
    db.add(crop2)
    db.commit()
    service.add_farmer_crop(db, farmer2.id, FarmerCropCreate(crop_id=crop2.id))

    farmer1_crops = service.list_farmer_crops(db, registered_farmer.id)
    assert len(farmer1_crops) == 1
    assert farmer1_crops[0].crop_id == active_crop.id

    farmer2_crops = service.list_farmer_crops(db, farmer2.id)
    assert len(farmer2_crops) == 1
    assert farmer2_crops[0].crop_id == crop2.id


def test_list_farmer_crops_rejects_unknown_farmer(service, db):
    """Test 11: list_farmer_crops rejects unknown farmer."""
    random_id = uuid.uuid4()
    with pytest.raises(FarmerNotFoundError):
        service.list_farmer_crops(db, random_id)


def test_get_farmer_crop_returns_correct_relationship(service, db, registered_farmer, active_crop):
    """Test 12: get_farmer_crop returns the correct relationship for the correct farmer."""
    fc = service.add_farmer_crop(
        db,
        registered_farmer.id,
        FarmerCropCreate(crop_id=active_crop.id, area_acres=Decimal("2.50")),
    )
    retrieved = service.get_farmer_crop(db, registered_farmer.id, fc.id)

    assert retrieved.id == fc.id
    assert retrieved.farmer_id == registered_farmer.id
    assert retrieved.crop_id == active_crop.id


def test_get_farmer_crop_cannot_access_another_farmers_crop(service, db, registered_farmer, active_crop):
    """Test 13: get_farmer_crop cannot access another farmer's crop relationship."""
    fc = service.add_farmer_crop(db, registered_farmer.id, FarmerCropCreate(crop_id=active_crop.id))

    other_farmer = UserProfile(id=uuid.uuid4(), full_name="Intruder")
    db.add(other_farmer)
    db.commit()

    with pytest.raises(FarmerCropNotFoundError):
        service.get_farmer_crop(db, other_farmer.id, fc.id)


def test_get_farmer_crop_raises_not_found_when_relationship_missing(service, db, registered_farmer):
    """Test 14: get_farmer_crop raises not-found when relationship does not exist."""
    random_fc_id = uuid.uuid4()
    with pytest.raises(FarmerCropNotFoundError):
        service.get_farmer_crop(db, registered_farmer.id, random_fc_id)


# ==============================================================================
# 4. update_farmer_crop Tests
# ==============================================================================

def test_update_farmer_crop_updates_area_acres_only(service, db, registered_farmer, active_crop):
    """Test 15: update_farmer_crop updates area_acres only."""
    fc = service.add_farmer_crop(
        db,
        registered_farmer.id,
        FarmerCropCreate(crop_id=active_crop.id, area_acres=Decimal("3.00"), is_primary=False),
    )
    updated = service.update_farmer_crop(
        db,
        registered_farmer.id,
        fc.id,
        FarmerCropUpdate(area_acres=Decimal("7.50")),
    )
    assert updated.area_acres == Decimal("7.50")
    assert updated.is_primary is False


def test_update_farmer_crop_updates_is_primary_only(service, db, registered_farmer, active_crop):
    """Test 16: update_farmer_crop updates is_primary only."""
    fc = service.add_farmer_crop(
        db,
        registered_farmer.id,
        FarmerCropCreate(crop_id=active_crop.id, area_acres=Decimal("3.00"), is_primary=False),
    )
    updated = service.update_farmer_crop(
        db,
        registered_farmer.id,
        fc.id,
        FarmerCropUpdate(is_primary=True),
    )
    assert updated.is_primary is True
    assert updated.area_acres == Decimal("3.00")


def test_update_farmer_crop_preserves_unspecified_fields(service, db, registered_farmer, active_crop):
    """Test 17: update_farmer_crop preserves unspecified fields."""
    fc = service.add_farmer_crop(
        db,
        registered_farmer.id,
        FarmerCropCreate(crop_id=active_crop.id, area_acres=Decimal("4.00"), is_primary=True),
    )
    updated = service.update_farmer_crop(
        db,
        registered_farmer.id,
        fc.id,
        FarmerCropUpdate(),
    )
    assert updated.area_acres == Decimal("4.00")
    assert updated.is_primary is True


def test_update_farmer_crop_supports_explicit_null_acreage(service, db, registered_farmer, active_crop):
    """Test 18: update_farmer_crop supports explicit area_acres=None."""
    fc = service.add_farmer_crop(
        db,
        registered_farmer.id,
        FarmerCropCreate(crop_id=active_crop.id, area_acres=Decimal("4.00")),
    )
    updated = service.update_farmer_crop(
        db,
        registered_farmer.id,
        fc.id,
        FarmerCropUpdate(area_acres=None),
    )
    assert updated.area_acres is None


def test_update_farmer_crop_cannot_change_crop_id(service, db, registered_farmer, active_crop):
    """Test 19: update_farmer_crop cannot change crop_id."""
    fc = service.add_farmer_crop(db, registered_farmer.id, FarmerCropCreate(crop_id=active_crop.id))
    assert "crop_id" not in FarmerCropUpdate.model_fields

    updated = service.update_farmer_crop(db, registered_farmer.id, fc.id, FarmerCropUpdate(is_primary=True))
    assert updated.crop_id == active_crop.id


def test_update_farmer_crop_cannot_change_farmer_ownership(service, db, registered_farmer, active_crop):
    """Test 20: update_farmer_crop cannot change farmer ownership."""
    fc = service.add_farmer_crop(db, registered_farmer.id, FarmerCropCreate(crop_id=active_crop.id))
    assert "farmer_id" not in FarmerCropUpdate.model_fields

    updated = service.update_farmer_crop(db, registered_farmer.id, fc.id, FarmerCropUpdate(is_primary=True))
    assert updated.farmer_id == registered_farmer.id


def test_update_farmer_crop_rejects_unknown_farmer(service, db):
    """Test 21: update_farmer_crop rejects unknown farmer."""
    random_farmer_id = uuid.uuid4()
    with pytest.raises(FarmerNotFoundError):
        service.update_farmer_crop(db, random_farmer_id, uuid.uuid4(), FarmerCropUpdate(is_primary=True))


def test_update_farmer_crop_rejects_unknown_relationship(service, db, registered_farmer):
    """Test 22: update_farmer_crop rejects unknown farmer-crop relationship."""
    random_fc_id = uuid.uuid4()
    with pytest.raises(FarmerCropNotFoundError):
        service.update_farmer_crop(db, registered_farmer.id, random_fc_id, FarmerCropUpdate(is_primary=True))


# ==============================================================================
# 5. delete_farmer_crop Tests
# ==============================================================================

def test_delete_farmer_crop_deletes_relationship_only(service, db, registered_farmer, active_crop):
    """Test 23: delete_farmer_crop deletes only the requested relationship."""
    fc = service.add_farmer_crop(db, registered_farmer.id, FarmerCropCreate(crop_id=active_crop.id))
    deleted = service.delete_farmer_crop(db, registered_farmer.id, fc.id)

    assert deleted.id == fc.id
    assert db.get(FarmerCrop, fc.id) is None


def test_delete_farmer_crop_does_not_delete_crop_entry(service, db, registered_farmer, active_crop):
    """Test 24: delete_farmer_crop does not delete the Crop catalog entry."""
    fc = service.add_farmer_crop(db, registered_farmer.id, FarmerCropCreate(crop_id=active_crop.id))
    service.delete_farmer_crop(db, registered_farmer.id, fc.id)

    # Crop still exists in catalog
    assert db.get(Crop, active_crop.id) is not None


def test_delete_farmer_crop_cannot_delete_another_farmers_relationship(service, db, registered_farmer, active_crop):
    """Test 25: delete_farmer_crop cannot delete another farmer's relationship."""
    fc = service.add_farmer_crop(db, registered_farmer.id, FarmerCropCreate(crop_id=active_crop.id))

    other_farmer = UserProfile(id=uuid.uuid4(), full_name="Intruder")
    db.add(other_farmer)
    db.commit()

    with pytest.raises(FarmerCropNotFoundError):
        service.delete_farmer_crop(db, other_farmer.id, fc.id)

    # Relationship still intact for rightful owner
    assert db.get(FarmerCrop, fc.id) is not None


# ==============================================================================
# 6. Database Failure & Rollback Tests
# ==============================================================================

def test_database_failure_triggers_rollback(service, registered_farmer, active_crop):
    """Test 26: database failure triggers rollback on add, update, delete."""
    # Failure on add
    mock_db = MagicMock(spec=Session)
    mock_db.get.side_effect = lambda model, ident: registered_farmer if model is UserProfile else active_crop
    mock_db.query.return_value.filter.return_value.first.return_value = None
    mock_db.commit.side_effect = RuntimeError("Commit failed")

    with pytest.raises(RuntimeError):
        service.add_farmer_crop(mock_db, registered_farmer.id, FarmerCropCreate(crop_id=active_crop.id))
    mock_db.rollback.assert_called_once()

    # Failure on update
    mock_fc = FarmerCrop(id=uuid.uuid4(), farmer_id=registered_farmer.id, crop_id=active_crop.id)
    mock_db_update = MagicMock(spec=Session)
    mock_db_update.get.return_value = registered_farmer
    mock_db_update.query.return_value.options.return_value.filter.return_value.first.return_value = mock_fc
    mock_db_update.commit.side_effect = RuntimeError("Update failed")

    with pytest.raises(RuntimeError):
        service.update_farmer_crop(mock_db_update, registered_farmer.id, mock_fc.id, FarmerCropUpdate(is_primary=True))
    mock_db_update.rollback.assert_called_once()

    # Failure on delete
    mock_db_delete = MagicMock(spec=Session)
    mock_db_delete.get.return_value = registered_farmer
    mock_db_delete.query.return_value.options.return_value.filter.return_value.first.return_value = mock_fc
    mock_db_delete.commit.side_effect = RuntimeError("Delete failed")

    with pytest.raises(RuntimeError):
        service.delete_farmer_crop(mock_db_delete, registered_farmer.id, mock_fc.id)
    mock_db_delete.rollback.assert_called_once()
