"""Unit tests for the CropReport SQLAlchemy model and its relationships."""
from datetime import datetime, timezone
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.inspection import inspect
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models.crop import Crop
from app.models.crop_report import CropReport
from app.models.farmer_crop import FarmerCrop
from app.models.user_profile import UserProfile
from app.schemas.crop_report import CropReportResponse


@pytest.fixture
def sqlite_session():
    """Create an isolated in-memory SQLite session for model persistence/cascade verification."""
    engine = create_engine("sqlite:///:memory:")
    # Create relevant tables in-memory
    Base.metadata.create_all(
        engine,
        tables=[
            UserProfile.__table__,
            Crop.__table__,
            FarmerCrop.__table__,
            CropReport.__table__,
        ],
    )
    with Session(engine) as session:
        yield session


# ==============================================================================
# Model Field & Instantiation Tests
# ==============================================================================

def test_crop_report_instantiation_with_valid_farmer_crop_id():
    """Test 1: CropReport model can be instantiated with a valid farmer_crop_id."""
    fc_id = uuid.uuid4()
    report = CropReport(
        id=uuid.uuid4(),
        farmer_crop_id=fc_id,
        notes="Yellow leaf observation",
        image_filename="leaf_01.jpg",
        image_storage_path="crop_reports/2026/09/uuid.jpg",
    )
    assert report.farmer_crop_id == fc_id
    assert report.notes == "Yellow leaf observation"
    assert report.image_filename == "leaf_01.jpg"
    assert report.image_storage_path == "crop_reports/2026/09/uuid.jpg"


def test_crop_report_notes_can_be_none():
    """Test 2: notes can be None."""
    report = CropReport(
        id=uuid.uuid4(),
        farmer_crop_id=uuid.uuid4(),
        notes=None,
    )
    assert report.notes is None


def test_crop_report_image_filename_can_be_none():
    """Test 3: image_filename can be None."""
    report = CropReport(
        id=uuid.uuid4(),
        farmer_crop_id=uuid.uuid4(),
        image_filename=None,
    )
    assert report.image_filename is None


def test_crop_report_image_storage_path_can_be_none():
    """Test 4: image_storage_path can be None."""
    report = CropReport(
        id=uuid.uuid4(),
        farmer_crop_id=uuid.uuid4(),
        image_storage_path=None,
    )
    assert report.image_storage_path is None


def test_multiple_reports_can_belong_to_same_farmer_crop():
    """Test 5: Multiple reports can belong to the same FarmerCrop."""
    fc_id = uuid.uuid4()
    r1 = CropReport(id=uuid.uuid4(), farmer_crop_id=fc_id, notes="First check")
    r2 = CropReport(id=uuid.uuid4(), farmer_crop_id=fc_id, notes="Followup check")
    assert r1.farmer_crop_id == r2.farmer_crop_id == fc_id
    assert r1.id != r2.id


# ==============================================================================
# Foreign Key and Relationship Tests
# ==============================================================================

def test_crop_report_has_expected_foreign_key_to_farmer_crop():
    """Test 6: CropReport has the expected FK to farmer_crops.id with ON DELETE CASCADE."""
    table = CropReport.__table__
    fks = list(table.foreign_keys)
    assert len(fks) == 1
    fk = fks[0]
    assert fk.parent.name == "farmer_crop_id"
    assert fk.target_fullname == "farmer_crops.id"
    assert fk.ondelete.upper() == "CASCADE"


def test_farmer_crop_crop_reports_relationship_exists():
    """Test 7: Relationship FarmerCrop.crop_reports exists with cascade all, delete-orphan."""
    mapper = inspect(FarmerCrop)
    assert "crop_reports" in mapper.relationships
    rel = mapper.relationships["crop_reports"]
    assert rel.target.name == "crop_reports"
    assert "delete" in rel.cascade
    assert "delete-orphan" in rel.cascade


def test_crop_report_farmer_crop_relationship_exists():
    """Test 8: Relationship CropReport.farmer_crop exists and references FarmerCrop."""
    mapper = inspect(CropReport)
    assert "farmer_crop" in mapper.relationships
    rel = mapper.relationships["farmer_crop"]
    assert rel.target.name == "farmer_crops"
    assert rel.back_populates == "crop_reports"


# ==============================================================================
# Schema Serialization Compatibility Tests
# ==============================================================================

def test_crop_report_serializes_through_pydantic_response():
    """Test 9: ORM object can serialize through CropReportResponse using from_attributes."""
    report_id = uuid.uuid4()
    fc_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    report = CropReport(
        id=report_id,
        farmer_crop_id=fc_id,
        notes="Arecanut yellowing spotted",
        image_filename="areca_01.jpg",
        image_storage_path="reports/areca_01.jpg",
        created_at=now,
        updated_at=now,
    )
    pydantic_obj = CropReportResponse.model_validate(report)
    assert pydantic_obj.id == report_id
    assert pydantic_obj.farmer_crop_id == fc_id
    assert pydantic_obj.notes == "Arecanut yellowing spotted"
    assert pydantic_obj.image_filename == "areca_01.jpg"
    assert pydantic_obj.image_storage_path == "reports/areca_01.jpg"
    assert pydantic_obj.created_at == now
    assert pydantic_obj.updated_at == now


# ==============================================================================
# Database Metadata, Indexing, and Schema Architecture Tests
# ==============================================================================

def test_model_metadata_contains_crop_reports_table():
    """Test 10: Model metadata contains crop_reports table."""
    assert "crop_reports" in Base.metadata.tables


def test_farmer_crop_id_is_indexed():
    """Test 11: farmer_crop_id is indexed according to project convention."""
    table = CropReport.__table__
    col = table.c.farmer_crop_id
    is_indexed = col.index is True or any(
        "farmer_crop_id" in [c.name for c in idx.columns] for idx in table.indexes
    )
    assert is_indexed is True


def test_no_farmer_id_column_on_crop_report():
    """Test 12: No farmer_id column exists on CropReport."""
    assert "farmer_id" not in CropReport.__table__.c


def test_no_crop_id_column_on_crop_report():
    """Test 13: No crop_id column exists on CropReport."""
    assert "crop_id" not in CropReport.__table__.c


def test_image_storage_path_not_signed_url_or_token_field():
    """Test 14: image_storage_path does not represent a signed URL field or token field."""
    columns = [c.name for c in CropReport.__table__.columns]
    assert "signed_url" not in columns
    assert "token" not in columns
    assert "access_token" not in columns
    assert "image_base64" not in columns
    assert "image_bytes" not in columns


# ==============================================================================
# Database Integration / Cascade Tests
# ==============================================================================

def test_crop_report_can_be_persisted(sqlite_session):
    """Test 15: CropReport can be persisted to the database."""
    farmer = UserProfile(id=uuid.uuid4(), full_name="Ramesh Gowda", language="kn")
    crop = Crop(id=uuid.uuid4(), code="arecanut", name_en="Arecanut", name_kn="ಅಡಿಕೆ")
    sqlite_session.add_all([farmer, crop])
    sqlite_session.commit()

    farmer_crop = FarmerCrop(id=uuid.uuid4(), farmer_id=farmer.id, crop_id=crop.id)
    sqlite_session.add(farmer_crop)
    sqlite_session.commit()

    report_id = uuid.uuid4()
    report = CropReport(
        id=report_id,
        farmer_crop_id=farmer_crop.id,
        notes="Initial symptoms",
        image_filename="symptom.jpg",
        image_storage_path="reports/symptom.jpg",
    )
    sqlite_session.add(report)
    sqlite_session.commit()

    persisted = sqlite_session.get(CropReport, report_id)
    assert persisted is not None
    assert persisted.farmer_crop_id == farmer_crop.id
    assert persisted.notes == "Initial symptoms"
    assert persisted.farmer_crop.id == farmer_crop.id


def test_multiple_reports_persisted_for_one_farmer_crop(sqlite_session):
    """Test 16: Multiple reports can be persisted for one FarmerCrop."""
    farmer = UserProfile(id=uuid.uuid4(), full_name="Suresh Kumar", language="kn")
    crop = Crop(id=uuid.uuid4(), code="cotton", name_en="Cotton", name_kn="ಹತ್ತಿ")
    sqlite_session.add_all([farmer, crop])
    sqlite_session.commit()

    farmer_crop = FarmerCrop(id=uuid.uuid4(), farmer_id=farmer.id, crop_id=crop.id)
    sqlite_session.add(farmer_crop)
    sqlite_session.commit()

    r1 = CropReport(id=uuid.uuid4(), farmer_crop_id=farmer_crop.id, notes="Week 1 observation")
    r2 = CropReport(id=uuid.uuid4(), farmer_crop_id=farmer_crop.id, notes="Week 2 observation")
    r3 = CropReport(id=uuid.uuid4(), farmer_crop_id=farmer_crop.id, notes="Week 3 observation")
    sqlite_session.add_all([r1, r2, r3])
    sqlite_session.commit()

    reports = (
        sqlite_session.query(CropReport)
        .filter(CropReport.farmer_crop_id == farmer_crop.id)
        .all()
    )
    assert len(reports) == 3
    assert len(farmer_crop.crop_reports) == 3


def test_deleting_farmer_crop_cascades_to_crop_reports(sqlite_session):
    """Test 17: Deleting FarmerCrop cascades to CropReport at database/ORM level."""
    farmer = UserProfile(id=uuid.uuid4(), full_name="Anand Patil", language="kn")
    crop = Crop(id=uuid.uuid4(), code="paddy", name_en="Paddy", name_kn="ಭತ್ತ")
    sqlite_session.add_all([farmer, crop])
    sqlite_session.commit()

    farmer_crop = FarmerCrop(id=uuid.uuid4(), farmer_id=farmer.id, crop_id=crop.id)
    sqlite_session.add(farmer_crop)
    sqlite_session.commit()

    r1 = CropReport(id=uuid.uuid4(), farmer_crop_id=farmer_crop.id, notes="Observation 1")
    r2 = CropReport(id=uuid.uuid4(), farmer_crop_id=farmer_crop.id, notes="Observation 2")
    sqlite_session.add_all([r1, r2])
    sqlite_session.commit()

    assert sqlite_session.query(CropReport).count() == 2

    # Delete FarmerCrop
    sqlite_session.delete(farmer_crop)
    sqlite_session.commit()

    # Verify CropReport entries were cascade deleted
    assert sqlite_session.query(CropReport).count() == 0
    # Verify UserProfile and Crop remain intact
    assert sqlite_session.get(UserProfile, farmer.id) is not None
    assert sqlite_session.get(Crop, crop.id) is not None
