"""Unit tests for CropReportService."""
from datetime import datetime, timedelta, timezone
from unittest.mock import MagicMock
import uuid
import pytest

from app.models.crop import Crop
from app.models.crop_report import CropReport
from app.models.farmer_crop import FarmerCrop
from app.models.user_profile import UserProfile
from app.schemas.crop_report import CropReportCreate, CropReportUpdate
from app.services.crop_report_service import (
    CropReportNotFoundError,
    CropReportService,
    FarmerCropNotFoundError,
    FarmerNotFoundError,
)


class InMemorySession:
    """In-memory transactional session simulator supporting CropReport, FarmerCrop, Crop, and UserProfile."""

    def __init__(self):
        self.crops: dict[uuid.UUID, Crop] = {}
        self.farmers: dict[uuid.UUID, UserProfile] = {}
        self.farmer_crops: dict[uuid.UUID, FarmerCrop] = {}
        self.crop_reports: dict[uuid.UUID, CropReport] = {}
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
        if model is CropReport:
            return self.crop_reports.get(entity_id)
        return None

    def query(self, model):
        if model is Crop:
            items = list(self.crops.values())
        elif model is FarmerCrop:
            items = list(self.farmer_crops.values())
        elif model is UserProfile:
            items = list(self.farmers.values())
        elif model is CropReport:
            items = list(self.crop_reports.values())
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
            elif isinstance(obj, CropReport):
                if getattr(obj, "farmer_crop", None) is None and obj.farmer_crop_id in self.farmer_crops:
                    obj.farmer_crop = self.farmer_crops[obj.farmer_crop_id]
                self.crop_reports[obj.id] = obj
        self.pending_adds.clear()
        self.committed = True

    def refresh(self, obj):
        if isinstance(obj, CropReport) and getattr(obj, "farmer_crop", None) is None:
            if obj.farmer_crop_id in self.farmer_crops:
                obj.farmer_crop = self.farmer_crops[obj.farmer_crop_id]

    def delete(self, obj):
        if isinstance(obj, CropReport) and obj.id in self.crop_reports:
            del self.crop_reports[obj.id]
        elif isinstance(obj, FarmerCrop) and obj.id in self.farmer_crops:
            del self.farmer_crops[obj.id]

    def rollback(self):
        self.pending_adds.clear()
        self.rolled_back = True


class FakeQuery:
    """Query object simulator for InMemorySession."""

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
        is_desc = False
        for arg in args:
            if str(arg).endswith("DESC") or "desc" in str(arg).lower():
                is_desc = True

        def sort_key(item):
            if hasattr(item, "created_at") and item.created_at is not None:
                return item.created_at
            return datetime.min.replace(tzinfo=timezone.utc)

        return FakeQuery(sorted(self.items, key=sort_key, reverse=is_desc))

    def all(self):
        return list(self.items)

    def first(self):
        return self.items[0] if self.items else None


# ==============================================================================
# Fixtures
# ==============================================================================

@pytest.fixture
def service():
    return CropReportService()


@pytest.fixture
def db():
    return InMemorySession()


@pytest.fixture
def farmer(db):
    f = UserProfile(id=uuid.uuid4(), full_name="Basavaraj Patil", language="kn")
    db.add(f)
    db.commit()
    return f


@pytest.fixture
def other_farmer(db):
    f = UserProfile(id=uuid.uuid4(), full_name="Manjunath Hegde", language="kn")
    db.add(f)
    db.commit()
    return f


@pytest.fixture
def crop(db):
    c = Crop(id=uuid.uuid4(), code="arecanut", name_en="Arecanut", name_kn="ಅಡಿಕೆ", is_active=True)
    db.add(c)
    db.commit()
    return c


@pytest.fixture
def farmer_crop(db, farmer, crop):
    fc = FarmerCrop(id=uuid.uuid4(), farmer_id=farmer.id, crop_id=crop.id, is_primary=True)
    fc.crop = crop
    fc.farmer = farmer
    db.add(fc)
    db.commit()
    return fc


@pytest.fixture
def other_farmer_crop(db, other_farmer, crop):
    fc = FarmerCrop(id=uuid.uuid4(), farmer_id=other_farmer.id, crop_id=crop.id, is_primary=True)
    fc.crop = crop
    fc.farmer = other_farmer
    db.add(fc)
    db.commit()
    return fc


# ==============================================================================
# 1. create_crop_report Tests
# ==============================================================================

def test_create_crop_report_successfully(service, db, farmer, farmer_crop):
    """Test 1: Create report successfully."""
    payload = CropReportCreate(
        farmer_crop_id=farmer_crop.id,
        notes="Yellowing foliage with brown margins",
        image_filename="leaf_observation.jpg",
    )
    report = service.create_crop_report(db=db, farmer_id=farmer.id, payload=payload)

    assert report is not None
    assert report.farmer_crop_id == farmer_crop.id
    assert report.notes == "Yellowing foliage with brown margins"
    assert report.image_filename == "leaf_observation.jpg"
    assert report.image_storage_path is None
    assert report.farmer_crop.id == farmer_crop.id
    assert db.committed is True


def test_create_crop_report_non_existent_farmer_fails(service, db, farmer_crop):
    """Test 2: Create report for non-existent farmer fails with FarmerNotFoundError."""
    unknown_farmer_id = uuid.uuid4()
    payload = CropReportCreate(
        farmer_crop_id=farmer_crop.id,
        notes="Notes for unknown farmer",
    )
    with pytest.raises(FarmerNotFoundError) as exc_info:
        service.create_crop_report(db=db, farmer_id=unknown_farmer_id, payload=payload)
    assert str(unknown_farmer_id) in str(exc_info.value)


def test_create_crop_report_non_existent_farmer_crop_fails(service, db, farmer):
    """Test 3: Create report for non-existent FarmerCrop fails with FarmerCropNotFoundError."""
    unknown_fc_id = uuid.uuid4()
    payload = CropReportCreate(
        farmer_crop_id=unknown_fc_id,
        notes="Notes for unknown crop relationship",
    )
    with pytest.raises(FarmerCropNotFoundError) as exc_info:
        service.create_crop_report(db=db, farmer_id=farmer.id, payload=payload)
    assert str(unknown_fc_id) in str(exc_info.value)


def test_create_crop_report_for_another_farmer_crop_fails(service, db, farmer, other_farmer_crop):
    """Test 4: Create report for another farmer's FarmerCrop fails with FarmerCropNotFoundError."""
    payload = CropReportCreate(
        farmer_crop_id=other_farmer_crop.id,
        notes="Attempting to report on another farmer's crop",
    )
    with pytest.raises(FarmerCropNotFoundError):
        service.create_crop_report(db=db, farmer_id=farmer.id, payload=payload)


# ==============================================================================
# 2. get_crop_report Tests
# ==============================================================================

def test_get_crop_report_successfully(service, db, farmer, farmer_crop):
    """Test 5: Get report successfully."""
    payload = CropReportCreate(
        farmer_crop_id=farmer_crop.id,
        notes="First inspection",
        image_filename="img1.jpg",
    )
    created = service.create_crop_report(db=db, farmer_id=farmer.id, payload=payload)

    fetched = service.get_crop_report(db=db, farmer_id=farmer.id, report_id=created.id)
    assert fetched.id == created.id
    assert fetched.notes == "First inspection"
    assert fetched.farmer_crop_id == farmer_crop.id


def test_get_non_existent_crop_report_fails(service, db, farmer):
    """Test 6: Get non-existent report fails with CropReportNotFoundError."""
    unknown_report_id = uuid.uuid4()
    with pytest.raises(CropReportNotFoundError):
        service.get_crop_report(db=db, farmer_id=farmer.id, report_id=unknown_report_id)


def test_get_another_farmer_report_blocked(service, db, farmer, other_farmer, other_farmer_crop):
    """Test 7: Get another farmer's report is blocked with CropReportNotFoundError."""
    payload = CropReportCreate(
        farmer_crop_id=other_farmer_crop.id,
        notes="Report by other farmer",
    )
    other_report = service.create_crop_report(
        db=db, farmer_id=other_farmer.id, payload=payload
    )

    # Farmer tries to access other_farmer's report
    with pytest.raises(CropReportNotFoundError):
        service.get_crop_report(db=db, farmer_id=farmer.id, report_id=other_report.id)


# ==============================================================================
# 3. list_crop_reports Tests
# ==============================================================================

def test_list_crop_reports_successfully(service, db, farmer, farmer_crop):
    """Test 8: List reports successfully."""
    r1 = service.create_crop_report(
        db=db,
        farmer_id=farmer.id,
        payload=CropReportCreate(farmer_crop_id=farmer_crop.id, notes="Report 1"),
    )
    r2 = service.create_crop_report(
        db=db,
        farmer_id=farmer.id,
        payload=CropReportCreate(farmer_crop_id=farmer_crop.id, notes="Report 2"),
    )

    reports = service.list_crop_reports(
        db=db, farmer_id=farmer.id, farmer_crop_id=farmer_crop.id
    )
    assert len(reports) == 2
    report_ids = [r.id for r in reports]
    assert r1.id in report_ids
    assert r2.id in report_ids


def test_list_crop_reports_empty_when_no_reports(service, db, farmer, farmer_crop):
    """Test 9: List reports returns empty list when no reports exist."""
    reports = service.list_crop_reports(
        db=db, farmer_id=farmer.id, farmer_crop_id=farmer_crop.id
    )
    assert reports == []


def test_list_crop_reports_cannot_access_another_farmer_crop(
    service, db, farmer, other_farmer_crop
):
    """Test 10: List reports cannot access another farmer's FarmerCrop."""
    with pytest.raises(FarmerCropNotFoundError):
        service.list_crop_reports(
            db=db, farmer_id=farmer.id, farmer_crop_id=other_farmer_crop.id
        )


def test_multiple_reports_for_same_farmer_crop_work(service, db, farmer, farmer_crop):
    """Test 11: Multiple reports for the same FarmerCrop work."""
    for i in range(5):
        service.create_crop_report(
            db=db,
            farmer_id=farmer.id,
            payload=CropReportCreate(farmer_crop_id=farmer_crop.id, notes=f"Check {i}"),
        )
    reports = service.list_crop_reports(
        db=db, farmer_id=farmer.id, farmer_crop_id=farmer_crop.id
    )
    assert len(reports) == 5


def test_reports_ordered_newest_first(service, db, farmer, farmer_crop):
    """Test 12: Reports are ordered deterministically newest first (created_at descending)."""
    now = datetime.now(timezone.utc)
    old_report = CropReport(
        id=uuid.uuid4(),
        farmer_crop_id=farmer_crop.id,
        notes="Older report",
        created_at=now - timedelta(days=2),
    )
    new_report = CropReport(
        id=uuid.uuid4(),
        farmer_crop_id=farmer_crop.id,
        notes="Newer report",
        created_at=now,
    )
    db.add(old_report)
    db.add(new_report)
    db.commit()

    reports = service.list_crop_reports(
        db=db, farmer_id=farmer.id, farmer_crop_id=farmer_crop.id
    )
    assert len(reports) == 2
    assert reports[0].id == new_report.id
    assert reports[1].id == old_report.id
    assert reports[0].created_at > reports[1].created_at


# ==============================================================================
# 4. update_crop_report Tests
# ==============================================================================

def test_update_notes_successfully(service, db, farmer, farmer_crop):
    """Test 13: Update notes successfully."""
    report = service.create_crop_report(
        db=db,
        farmer_id=farmer.id,
        payload=CropReportCreate(
            farmer_crop_id=farmer_crop.id,
            notes="Initial notes",
            image_filename="original.jpg",
        ),
    )

    updated = service.update_crop_report(
        db=db,
        farmer_id=farmer.id,
        report_id=report.id,
        payload=CropReportUpdate(notes="Updated observation notes"),
    )
    assert updated.notes == "Updated observation notes"
    assert updated.image_filename == "original.jpg"  # Preserved


def test_update_image_filename_successfully(service, db, farmer, farmer_crop):
    """Test 14: Update image_filename successfully."""
    report = service.create_crop_report(
        db=db,
        farmer_id=farmer.id,
        payload=CropReportCreate(
            farmer_crop_id=farmer_crop.id,
            notes="Leaf damage",
            image_filename="old_name.jpg",
        ),
    )

    updated = service.update_crop_report(
        db=db,
        farmer_id=farmer.id,
        report_id=report.id,
        payload=CropReportUpdate(image_filename="renamed_leaf.jpg"),
    )
    assert updated.image_filename == "renamed_leaf.jpg"
    assert updated.notes == "Leaf damage"  # Preserved


def test_partial_update_preserves_omitted_fields(service, db, farmer, farmer_crop):
    """Test 15: Partial update preserves omitted fields."""
    report = service.create_crop_report(
        db=db,
        farmer_id=farmer.id,
        payload=CropReportCreate(
            farmer_crop_id=farmer_crop.id,
            notes="Keep these notes",
            image_filename="keep_image.jpg",
        ),
    )

    # Empty payload should keep everything intact
    updated = service.update_crop_report(
        db=db,
        farmer_id=farmer.id,
        report_id=report.id,
        payload=CropReportUpdate(),
    )
    assert updated.notes == "Keep these notes"
    assert updated.image_filename == "keep_image.jpg"


def test_update_cannot_change_farmer_crop_id(service, db, farmer, farmer_crop, other_farmer_crop):
    """Test 16 & 17: Update cannot change farmer_crop_id or move report to another FarmerCrop."""
    assert "farmer_crop_id" not in CropReportUpdate.model_fields

    report = service.create_crop_report(
        db=db,
        farmer_id=farmer.id,
        payload=CropReportCreate(farmer_crop_id=farmer_crop.id, notes="Original crop"),
    )
    original_fc_id = report.farmer_crop_id

    # Update notes
    updated = service.update_crop_report(
        db=db,
        farmer_id=farmer.id,
        report_id=report.id,
        payload=CropReportUpdate(notes="Updated notes without changing crop"),
    )
    assert updated.farmer_crop_id == original_fc_id
    assert updated.notes == "Updated notes without changing crop"


def test_update_another_farmer_report_blocked(
    service, db, farmer, other_farmer, other_farmer_crop
):
    """Test 18: Update another farmer's report is blocked with CropReportNotFoundError."""
    other_report = service.create_crop_report(
        db=db,
        farmer_id=other_farmer.id,
        payload=CropReportCreate(farmer_crop_id=other_farmer_crop.id, notes="Original"),
    )

    with pytest.raises(CropReportNotFoundError):
        service.update_crop_report(
            db=db,
            farmer_id=farmer.id,
            report_id=other_report.id,
            payload=CropReportUpdate(notes="Hijacked notes"),
        )
    # Confirm unmodified
    assert other_report.notes == "Original"


# ==============================================================================
# 5. delete_crop_report Tests
# ==============================================================================

def test_delete_crop_report_successfully(service, db, farmer, farmer_crop):
    """Test 19: Delete report successfully."""
    report = service.create_crop_report(
        db=db,
        farmer_id=farmer.id,
        payload=CropReportCreate(farmer_crop_id=farmer_crop.id, notes="To be deleted"),
    )
    report_id = report.id

    service.delete_crop_report(db=db, farmer_id=farmer.id, report_id=report_id)

    # Verification: report is deleted
    assert db.get(CropReport, report_id) is None
    # Subsequent get raises CropReportNotFoundError
    with pytest.raises(CropReportNotFoundError):
        service.get_crop_report(db=db, farmer_id=farmer.id, report_id=report_id)


def test_delete_non_existent_crop_report_fails(service, db, farmer):
    """Test 20: Delete non-existent report fails with CropReportNotFoundError."""
    unknown_report_id = uuid.uuid4()
    with pytest.raises(CropReportNotFoundError):
        service.delete_crop_report(
            db=db, farmer_id=farmer.id, report_id=unknown_report_id
        )


def test_delete_another_farmer_report_blocked(
    service, db, farmer, other_farmer, other_farmer_crop
):
    """Test 21: Delete another farmer's report is blocked with CropReportNotFoundError."""
    other_report = service.create_crop_report(
        db=db,
        farmer_id=other_farmer.id,
        payload=CropReportCreate(farmer_crop_id=other_farmer_crop.id, notes="Do not delete"),
    )

    with pytest.raises(CropReportNotFoundError):
        service.delete_crop_report(
            db=db, farmer_id=farmer.id, report_id=other_report.id
        )
    # Confirm report still exists
    assert db.get(CropReport, other_report.id) is not None


# ==============================================================================
# 6. Transaction Safety & Isolation
# ==============================================================================

def test_database_rollback_on_mutating_failure(service, farmer, farmer_crop):
    """Test 22: Database rollback occurs on mutating failure."""
    failing_db = MagicMock()
    failing_db.get.return_value = farmer
    failing_db.query.return_value.filter.return_value.first.return_value = farmer_crop
    failing_db.commit.side_effect = RuntimeError("Database connection failed")

    payload = CropReportCreate(
        farmer_crop_id=farmer_crop.id,
        notes="Rollback test",
    )
    with pytest.raises(RuntimeError):
        service.create_crop_report(db=failing_db, farmer_id=farmer.id, payload=payload)

    failing_db.rollback.assert_called_once()


def test_service_does_not_modify_farmer_crop_or_crop(service, db, farmer, farmer_crop, crop):
    """Test 23: Verify no CropReport service method modifies FarmerCrop or Crop."""
    initial_crop_code = crop.code
    initial_primary = farmer_crop.is_primary

    # Create
    report = service.create_crop_report(
        db=db,
        farmer_id=farmer.id,
        payload=CropReportCreate(farmer_crop_id=farmer_crop.id, notes="Integrity check"),
    )
    # Update
    service.update_crop_report(
        db=db,
        farmer_id=farmer.id,
        report_id=report.id,
        payload=CropReportUpdate(notes="Updated notes"),
    )
    # List
    service.list_crop_reports(db=db, farmer_id=farmer.id, farmer_crop_id=farmer_crop.id)
    # Get
    service.get_crop_report(db=db, farmer_id=farmer.id, report_id=report.id)
    # Delete
    service.delete_crop_report(db=db, farmer_id=farmer.id, report_id=report.id)

    # Parent entities remain completely unchanged
    assert crop.code == initial_crop_code
    assert farmer_crop.is_primary == initial_primary
    assert db.get(FarmerCrop, farmer_crop.id) is not None
    assert db.get(Crop, crop.id) is not None
