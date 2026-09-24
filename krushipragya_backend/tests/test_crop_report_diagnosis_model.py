"""Unit tests for the CropReportDiagnosis SQLAlchemy model and its relationships."""
from datetime import datetime, timezone
import uuid
import pytest
from sqlalchemy import create_engine, inspect
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models.village import Village
from app.models.crop import Crop
from app.models.crop_report import CropReport
from app.models.crop_report_diagnosis import CropReportDiagnosis
from app.models.farmer_crop import FarmerCrop
from app.models.user_profile import UserProfile


SAMPLE_PREDICTIONS = [
    {"class_name": "yellow_leaf_disease", "confidence": 0.9421},
    {"class_name": "healthy", "confidence": 0.0315},
    {"class_name": "mahali_koleroga", "confidence": 0.0152},
    {"class_name": "stem_bleeding", "confidence": 0.0071},
    {"class_name": "bud_rot", "confidence": 0.0028},
    {"class_name": "foot_rot", "confidence": 0.0013},
]


@pytest.fixture
def sqlite_session():
    """Create an isolated in-memory SQLite session for model persistence/cascade verification."""
    engine = create_engine("sqlite:///:memory:")
    # Enable foreign key enforcement in SQLite
    with engine.connect() as conn:
        conn.exec_driver_sql("PRAGMA foreign_keys = ON")

    Base.metadata.create_all(
        engine,
        tables=[
            Village.__table__,
            UserProfile.__table__,
            Crop.__table__,
            FarmerCrop.__table__,
            CropReport.__table__,
            CropReportDiagnosis.__table__,
        ],
    )
    with Session(engine) as session:
        yield session



# ==============================================================================
# 1. Model Instantiation & Field Tests
# ==============================================================================

def test_crop_report_diagnosis_instantiation():
    """Test 1: Model can be instantiated with valid attributes."""
    diag_id = uuid.uuid4()
    report_id = uuid.uuid4()
    diagnosis = CropReportDiagnosis(
        id=diag_id,
        crop_report_id=report_id,
        crop="arecanut",
        predicted_class="yellow_leaf_disease",
        confidence=0.9421,
        model_name="krushisetu_efficientnet_b0_best.pth",
        predictions=SAMPLE_PREDICTIONS,
    )
    assert diagnosis.id == diag_id
    assert diagnosis.crop_report_id == report_id
    assert diagnosis.crop == "arecanut"
    assert diagnosis.predicted_class == "yellow_leaf_disease"
    assert diagnosis.confidence == 0.9421
    assert diagnosis.model_name == "krushisetu_efficientnet_b0_best.pth"
    assert diagnosis.predictions == SAMPLE_PREDICTIONS
    assert len(diagnosis.predictions) == 6


def test_uuid_primary_key_exists():
    """Test 2: UUID primary key exists on crop_report_diagnoses."""
    table = CropReportDiagnosis.__table__
    pk_cols = [c.name for c in table.primary_key.columns]
    assert pk_cols == ["id"]
    assert table.c.id.primary_key is True


def test_required_columns_are_not_nullable():
    """Test 3: crop_report_id, crop, predicted_class, confidence, model_name, predictions are NOT NULL."""
    table = CropReportDiagnosis.__table__
    assert table.c.id.nullable is False
    assert table.c.crop_report_id.nullable is False
    assert table.c.crop.nullable is False
    assert table.c.predicted_class.nullable is False
    assert table.c.confidence.nullable is False
    assert table.c.model_name.nullable is False
    assert table.c.predictions.nullable is False
    assert table.c.created_at.nullable is False


def test_created_at_column_has_server_default():
    """Test 4: created_at column has server_default configured."""
    table = CropReportDiagnosis.__table__
    assert table.c.created_at.server_default is not None


def test_repr_string_formatting():
    """Test 5: __repr__ contains informative model attributes."""
    diag_id = uuid.uuid4()
    report_id = uuid.uuid4()
    diagnosis = CropReportDiagnosis(
        id=diag_id,
        crop_report_id=report_id,
        crop="arecanut",
        predicted_class="yellow_leaf_disease",
        confidence=0.9421,
        model_name="krushisetu_efficientnet_b0_best.pth",
        predictions=SAMPLE_PREDICTIONS,
    )
    repr_str = repr(diagnosis)
    assert str(diag_id) in repr_str
    assert "yellow_leaf_disease" in repr_str
    assert "arecanut" in repr_str
    assert "0.9421" in repr_str


# ==============================================================================
# 2. Foreign Key & Relationships
# ==============================================================================

def test_crop_report_diagnosis_has_foreign_key_to_crop_report():
    """Test 6: Foreign key references crop_reports.id with ON DELETE CASCADE."""
    table = CropReportDiagnosis.__table__
    fks = list(table.foreign_keys)
    assert len(fks) == 1
    fk = fks[0]
    assert fk.parent.name == "crop_report_id"
    assert fk.target_fullname == "crop_reports.id"
    assert fk.ondelete.upper() == "CASCADE"


def test_crop_report_diagnoses_relationship_exists():
    """Test 7: Relationship CropReport.diagnoses exists with cascade all, delete-orphan and order_by."""
    mapper = inspect(CropReport)
    assert "diagnoses" in mapper.relationships
    rel = mapper.relationships["diagnoses"]
    assert rel.target.name == "crop_report_diagnoses"
    assert "delete" in rel.cascade
    assert "delete-orphan" in rel.cascade
    assert rel.back_populates == "crop_report"


def test_crop_report_diagnosis_crop_report_relationship_exists():
    """Test 8: Relationship CropReportDiagnosis.crop_report exists and references CropReport."""
    mapper = inspect(CropReportDiagnosis)
    assert "crop_report" in mapper.relationships
    rel = mapper.relationships["crop_report"]
    assert rel.target.name == "crop_reports"
    assert rel.back_populates == "diagnoses"


# ==============================================================================
# 3. Index Architecture Tests
# ==============================================================================

def test_compound_index_exists_on_crop_report_id_and_created_at():
    """Test 9: Composite index (crop_report_id, created_at DESC) exists."""
    table = CropReportDiagnosis.__table__
    index_names = [idx.name for idx in table.indexes]
    assert "ix_crop_report_diagnoses_crop_report_id_created_at" in index_names

    comp_idx = next(
        idx for idx in table.indexes if idx.name == "ix_crop_report_diagnoses_crop_report_id_created_at"
    )
    col_names = [getattr(col, "name", str(col)) for col in comp_idx.columns]
    assert col_names[0] == "crop_report_id"


def test_predicted_class_is_indexed():
    """Test 10: predicted_class column has an index."""
    table = CropReportDiagnosis.__table__
    assert table.c.predicted_class.index is True or any(
        "predicted_class" in [c.name for c in idx.columns] for idx in table.indexes
    )


def test_crop_is_indexed():
    """Test 11: crop column has an index."""
    table = CropReportDiagnosis.__table__
    assert table.c.crop.index is True or any(
        "crop" in [c.name for c in idx.columns] for idx in table.indexes
    )


def test_no_separate_standalone_crop_report_id_index():
    """Test 12: No separate standalone single-column index on crop_report_id exists."""
    table = CropReportDiagnosis.__table__
    # Verify crop_report_id is not individually indexed
    assert table.c.crop_report_id.index is not True

    # Check that no standalone single-column index on crop_report_id exists
    single_col_indexes = [
        idx
        for idx in table.indexes
        if len(idx.expressions) == 1
        and getattr(list(idx.expressions)[0], "name", None) == "crop_report_id"
    ]
    assert len(single_col_indexes) == 0


# ==============================================================================
# 4. Database Persistence & Cascade Tests
# ==============================================================================

def test_persist_diagnosis_with_complete_predictions_json(sqlite_session):
    """Test 13: Persist diagnosis and retrieve full ranked predictions JSON."""
    farmer = UserProfile(id=uuid.uuid4(), full_name="Ramesh Gowda")
    crop = Crop(id=uuid.uuid4(), code="arecanut", name_en="Arecanut", name_kn="ಅಡಿಕೆ")
    farmer_crop = FarmerCrop(id=uuid.uuid4(), farmer=farmer, crop=crop)
    report = CropReport(id=uuid.uuid4(), farmer_crop=farmer_crop, notes="Leaf spots")
    diagnosis = CropReportDiagnosis(
        id=uuid.uuid4(),
        crop_report=report,
        crop="arecanut",
        predicted_class="yellow_leaf_disease",
        confidence=0.9421,
        model_name="krushisetu_efficientnet_b0_best.pth",
        predictions=SAMPLE_PREDICTIONS,
    )

    sqlite_session.add_all([farmer, crop, farmer_crop, report, diagnosis])
    sqlite_session.commit()

    saved_diag = sqlite_session.get(CropReportDiagnosis, diagnosis.id)
    assert saved_diag is not None
    assert saved_diag.crop == "arecanut"
    assert saved_diag.predicted_class == "yellow_leaf_disease"
    assert saved_diag.confidence == 0.9421
    assert saved_diag.predictions == SAMPLE_PREDICTIONS
    assert len(saved_diag.predictions) == 6
    assert saved_diag.predictions[0]["class_name"] == "yellow_leaf_disease"


def test_multiple_diagnoses_belong_to_one_crop_report(sqlite_session):
    """Test 14: Multiple diagnoses can belong to a single CropReport."""
    farmer = UserProfile(id=uuid.uuid4(), full_name="Suresh Bhat")
    crop = Crop(id=uuid.uuid4(), code="arecanut", name_en="Arecanut", name_kn="ಅಡಿಕೆ")
    farmer_crop = FarmerCrop(id=uuid.uuid4(), farmer=farmer, crop=crop)
    report = CropReport(id=uuid.uuid4(), farmer_crop=farmer_crop)

    diag1 = CropReportDiagnosis(
        id=uuid.uuid4(),
        crop_report=report,
        crop="arecanut",
        predicted_class="healthy",
        confidence=0.85,
        model_name="v1_model.pth",
        predictions=[{"class_name": "healthy", "confidence": 0.85}],
        created_at=datetime(2026, 9, 20, 10, 0, tzinfo=timezone.utc),
    )
    diag2 = CropReportDiagnosis(
        id=uuid.uuid4(),
        crop_report=report,
        crop="arecanut",
        predicted_class="yellow_leaf_disease",
        confidence=0.92,
        model_name="v2_model.pth",
        predictions=[{"class_name": "yellow_leaf_disease", "confidence": 0.92}],
        created_at=datetime(2026, 9, 24, 10, 0, tzinfo=timezone.utc),
    )

    sqlite_session.add_all([farmer, crop, farmer_crop, report, diag1, diag2])
    sqlite_session.commit()

    sqlite_session.refresh(report)
    assert len(report.diagnoses) == 2
    # Verify newest first ordering
    assert report.diagnoses[0].predicted_class == "yellow_leaf_disease"
    assert report.diagnoses[1].predicted_class == "healthy"


def test_deleting_crop_report_cascades_diagnoses(sqlite_session):
    """Test 15: Deleting a CropReport cascades deletion to its CropReportDiagnosis records."""
    farmer = UserProfile(id=uuid.uuid4(), full_name="Anand Rao")
    crop = Crop(id=uuid.uuid4(), code="paddy", name_en="Paddy", name_kn="ಭತ್ತ")
    farmer_crop = FarmerCrop(id=uuid.uuid4(), farmer=farmer, crop=crop)
    report = CropReport(id=uuid.uuid4(), farmer_crop=farmer_crop)


    diag1 = CropReportDiagnosis(
        id=uuid.uuid4(),
        crop_report=report,
        crop="paddy",
        predicted_class="blast",
        confidence=0.91,
        model_name="paddy_model.pth",
        predictions=[{"class_name": "blast", "confidence": 0.91}],
    )
    diag2 = CropReportDiagnosis(
        id=uuid.uuid4(),
        crop_report=report,
        crop="paddy",
        predicted_class="brown_spot",
        confidence=0.88,
        model_name="paddy_model.pth",
        predictions=[{"class_name": "brown_spot", "confidence": 0.88}],
    )

    sqlite_session.add_all([farmer, crop, farmer_crop, report, diag1, diag2])
    sqlite_session.commit()

    diag1_id = diag1.id
    diag2_id = diag2.id

    # Verify rows exist
    assert sqlite_session.get(CropReportDiagnosis, diag1_id) is not None
    assert sqlite_session.get(CropReportDiagnosis, diag2_id) is not None

    # Delete CropReport
    sqlite_session.delete(report)
    sqlite_session.commit()

    # Diagnoses must be cascaded and deleted
    assert sqlite_session.get(CropReportDiagnosis, diag1_id) is None
    assert sqlite_session.get(CropReportDiagnosis, diag2_id) is None
