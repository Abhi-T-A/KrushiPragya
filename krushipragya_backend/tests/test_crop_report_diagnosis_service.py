"""Unit tests for CropReportDiagnosisService."""
from datetime import datetime, timezone
from unittest.mock import MagicMock
import uuid
import pytest
from sqlalchemy import create_engine
from sqlalchemy.exc import OperationalError
from sqlalchemy.orm import Session

from app.database.base import Base
from app.models.crop import Crop
from app.models.crop_report import CropReport
from app.models.crop_report_diagnosis import CropReportDiagnosis
from app.models.farmer_crop import FarmerCrop
from app.models.user_profile import UserProfile
from app.models.village import Village
from app.schemas.disease import ClassPrediction, DiseasePredictionResponse
from app.services.crop_report_diagnosis_service import (
    CropReportDiagnosisService,
    CropReportImageNotFoundError,
)
from app.services.crop_report_service import CropReportNotFoundError
from app.services.crop_report_storage_service import StorageServiceError
from app.services.disease_detection_service import (
    DiseaseDetectionError,
    UnsupportedCropError,
)
from app.services.farmer_crop_service import FarmerNotFoundError


class MockDiseaseDetectionService:
    """Mock for DiseaseDetectionService to isolate from PyTorch model execution."""

    def __init__(self):
        self.call_count = 0
        self.last_crop = None
        self.last_image_bytes = None
        self.fail_inference = False
        self.raise_unsupported = False
        self.mock_response = DiseasePredictionResponse(
            crop="arecanut",
            predicted_class="yellow_leaf_disease",
            confidence=0.9421,
            predictions=[
                ClassPrediction(class_name="yellow_leaf_disease", confidence=0.9421),
                ClassPrediction(class_name="healthy", confidence=0.0315),
                ClassPrediction(class_name="mahali_koleroga", confidence=0.0152),
            ],
            model="krushisetu_efficientnet_b0_best.pth",
        )

    def predict(self, raw_crop: str, image_bytes: bytes) -> DiseasePredictionResponse:
        self.call_count += 1
        self.last_crop = raw_crop
        self.last_image_bytes = image_bytes
        if self.raise_unsupported:
            raise UnsupportedCropError(raw_crop, ["arecanut", "paddy", "coconut"])
        if self.fail_inference:
            raise DiseaseDetectionError("Inference failed")
        return self.mock_response


class MockStorageService:
    """Mock for CropReportStorageService."""

    def __init__(self):
        self.downloaded_paths = []
        self.fail_download = False
        self.image_bytes = b"\xff\xd8\xff\xe0mock_stored_image_bytes"

    def download_image(self, storage_path: str) -> bytes:
        self.downloaded_paths.append(storage_path)
        if self.fail_download:
            raise StorageServiceError("Failed to download image: HTTP 500")
        return self.image_bytes


@pytest.fixture
def sqlite_session():
    """Create isolated in-memory SQLite session with foreign keys enabled."""
    engine = create_engine("sqlite:///:memory:")
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


@pytest.fixture
def mock_storage():
    return MockStorageService()


@pytest.fixture
def mock_disease():
    return MockDiseaseDetectionService()


@pytest.fixture
def diagnosis_service(mock_storage, mock_disease):
    return CropReportDiagnosisService(
        storage_service=mock_storage,
        disease_service=mock_disease,
    )


@pytest.fixture
def test_setup(sqlite_session):
    """Seed farmer, crop, farmer_crop, and report with image."""
    farmer = UserProfile(id=uuid.uuid4(), full_name="Basavaraj Patil", language="kn")
    other_farmer = UserProfile(id=uuid.uuid4(), full_name="Manjunath Hegde", language="kn")
    crop = Crop(id=uuid.uuid4(), code="arecanut", name_en="Arecanut", name_kn="ಅಡಿಕೆ")
    farmer_crop = FarmerCrop(id=uuid.uuid4(), farmer=farmer, crop=crop, is_primary=True)
    report = CropReport(
        id=uuid.uuid4(),
        farmer_crop=farmer_crop,
        notes="Yellow leaves observation",
        image_filename="leaf.jpg",
        image_storage_path="farmers/test/crop-reports/test/leaf.jpg",
    )
    sqlite_session.add_all([farmer, other_farmer, crop, farmer_crop, report])
    sqlite_session.commit()
    return {
        "farmer": farmer,
        "other_farmer": other_farmer,
        "crop": crop,
        "farmer_crop": farmer_crop,
        "report": report,
    }


# ==============================================================================
# A. Successful Diagnosis Tests
# ==============================================================================

def test_diagnose_crop_report_success(sqlite_session, diagnosis_service, mock_storage, mock_disease, test_setup):
    """Test 1: Successful diagnosis persists diagnosis and matches DB record."""
    farmer = test_setup["farmer"]
    report = test_setup["report"]

    diagnosis = diagnosis_service.diagnose_crop_report(
        db=sqlite_session,
        farmer_id=farmer.id,
        report_id=report.id,
    )

    assert diagnosis is not None
    assert diagnosis.crop_report_id == report.id
    assert diagnosis.crop == "arecanut"
    assert diagnosis.predicted_class == "yellow_leaf_disease"
    assert diagnosis.confidence == 0.9421
    assert diagnosis.model_name == "krushisetu_efficientnet_b0_best.pth"
    assert len(diagnosis.predictions) == 3
    assert diagnosis.created_at is not None

    # Check mock interactions
    assert mock_storage.downloaded_paths == [report.image_storage_path]
    assert mock_disease.call_count == 1
    assert mock_disease.last_crop == "arecanut"
    assert mock_disease.last_image_bytes == mock_storage.image_bytes

    # Verify persisted in database
    saved = sqlite_session.get(CropReportDiagnosis, diagnosis.id)
    assert saved is not None
    assert saved.predicted_class == "yellow_leaf_disease"
    assert saved.confidence == 0.9421


# ==============================================================================
# B. Ownership & Access Control Tests
# ==============================================================================

def test_diagnose_crop_report_unknown_farmer_raises_not_found(sqlite_session, diagnosis_service, test_setup):
    """Test 2: Unknown farmer raises FarmerNotFoundError."""
    report = test_setup["report"]
    fake_farmer_id = uuid.uuid4()

    with pytest.raises(FarmerNotFoundError) as exc_info:
        diagnosis_service.diagnose_crop_report(
            db=sqlite_session,
            farmer_id=fake_farmer_id,
            report_id=report.id,
        )
    assert str(fake_farmer_id) in str(exc_info.value)


def test_diagnose_crop_report_other_farmer_raises_crop_report_not_found(sqlite_session, diagnosis_service, test_setup):
    """Test 3: Report belonging to another farmer raises CropReportNotFoundError."""
    other_farmer = test_setup["other_farmer"]
    report = test_setup["report"]

    with pytest.raises(CropReportNotFoundError):
        diagnosis_service.diagnose_crop_report(
            db=sqlite_session,
            farmer_id=other_farmer.id,
            report_id=report.id,
        )


def test_diagnose_crop_report_missing_report_raises_not_found(sqlite_session, diagnosis_service, test_setup):
    """Test 4: Missing report raises CropReportNotFoundError."""
    farmer = test_setup["farmer"]
    fake_report_id = uuid.uuid4()

    with pytest.raises(CropReportNotFoundError):
        diagnosis_service.diagnose_crop_report(
            db=sqlite_session,
            farmer_id=farmer.id,
            report_id=fake_report_id,
        )


# ==============================================================================
# C. Image State Tests
# ==============================================================================

def test_diagnose_crop_report_without_image_raises_image_not_found(sqlite_session, diagnosis_service, test_setup):
    """Test 5: Report without image raises CropReportImageNotFoundError."""
    farmer = test_setup["farmer"]
    farmer_crop = test_setup["farmer_crop"]

    report_no_img = CropReport(
        id=uuid.uuid4(),
        farmer_crop=farmer_crop,
        notes="No photo taken yet",
        image_storage_path=None,
    )
    sqlite_session.add(report_no_img)
    sqlite_session.commit()

    with pytest.raises(CropReportImageNotFoundError) as exc_info:
        diagnosis_service.diagnose_crop_report(
            db=sqlite_session,
            farmer_id=farmer.id,
            report_id=report_no_img.id,
        )
    assert "no uploaded image" in str(exc_info.value)


def test_diagnose_crop_report_storage_download_failure_raises_storage_error(
    sqlite_session, diagnosis_service, mock_storage, test_setup
):
    """Test 6: Storage download failure raises StorageServiceError."""
    farmer = test_setup["farmer"]
    report = test_setup["report"]
    mock_storage.fail_download = True

    with pytest.raises(StorageServiceError):
        diagnosis_service.diagnose_crop_report(
            db=sqlite_session,
            farmer_id=farmer.id,
            report_id=report.id,
        )


# ==============================================================================
# D. Disease Detection Inference Tests
# ==============================================================================

def test_diagnose_crop_report_unsupported_crop_propagates_error(
    sqlite_session, diagnosis_service, mock_disease, test_setup
):
    """Test 7: Unsupported crop error from DiseaseDetectionService propagates."""
    farmer = test_setup["farmer"]
    report = test_setup["report"]
    mock_disease.raise_unsupported = True

    with pytest.raises(UnsupportedCropError) as exc_info:
        diagnosis_service.diagnose_crop_report(
            db=sqlite_session,
            farmer_id=farmer.id,
            report_id=report.id,
        )
    assert "arecanut" in str(exc_info.value)


def test_diagnose_crop_report_inference_failure_raises_error(
    sqlite_session, diagnosis_service, mock_disease, test_setup
):
    """Test 8: ML inference failure raises DiseaseDetectionError."""
    farmer = test_setup["farmer"]
    report = test_setup["report"]
    mock_disease.fail_inference = True

    with pytest.raises(DiseaseDetectionError):
        diagnosis_service.diagnose_crop_report(
            db=sqlite_session,
            farmer_id=farmer.id,
            report_id=report.id,
        )


# ==============================================================================
# E. Persistence & Multiple Diagnoses
# ==============================================================================

def test_diagnose_crop_report_multiple_diagnoses_allowed(
    sqlite_session, diagnosis_service, mock_disease, test_setup
):
    """Test 9: Multiple diagnoses on same report are allowed and stored."""
    farmer = test_setup["farmer"]
    report = test_setup["report"]

    # First diagnosis
    mock_disease.mock_response = DiseasePredictionResponse(
        crop="arecanut",
        predicted_class="yellow_leaf_disease",
        confidence=0.88,
        predictions=[ClassPrediction(class_name="yellow_leaf_disease", confidence=0.88)],
        model="v1.pth",
    )
    diag1 = diagnosis_service.diagnose_crop_report(
        db=sqlite_session,
        farmer_id=farmer.id,
        report_id=report.id,
    )

    # Second diagnosis (re-run)
    mock_disease.mock_response = DiseasePredictionResponse(
        crop="arecanut",
        predicted_class="healthy",
        confidence=0.95,
        predictions=[ClassPrediction(class_name="healthy", confidence=0.95)],
        model="v2.pth",
    )
    diag2 = diagnosis_service.diagnose_crop_report(
        db=sqlite_session,
        farmer_id=farmer.id,
        report_id=report.id,
    )

    assert diag1.id != diag2.id
    sqlite_session.refresh(report)
    assert len(report.diagnoses) == 2
    diag_ids = {d.id for d in report.diagnoses}
    assert diag1.id in diag_ids
    assert diag2.id in diag_ids



# ==============================================================================
# F. Transaction Safety & Non-Destructive Integrity
# ==============================================================================

def test_inference_failure_creates_no_diagnosis_record(
    sqlite_session, diagnosis_service, mock_disease, test_setup
):
    """Test 10: Inference failure does not leave partial diagnosis in DB."""
    farmer = test_setup["farmer"]
    report = test_setup["report"]
    mock_disease.fail_inference = True

    with pytest.raises(DiseaseDetectionError):
        diagnosis_service.diagnose_crop_report(
            db=sqlite_session,
            farmer_id=farmer.id,
            report_id=report.id,
        )

    # Diagnosis table remains empty
    count = sqlite_session.query(CropReportDiagnosis).count()
    assert count == 0
    # Report remains intact
    assert sqlite_session.get(CropReport, report.id) is not None
    assert sqlite_session.get(CropReport, report.id).image_storage_path is not None


def test_diagnosis_does_not_modify_or_delete_stored_image(
    sqlite_session, diagnosis_service, mock_storage, test_setup
):
    """Test 11: Stored image is never deleted or mutated during diagnosis."""
    farmer = test_setup["farmer"]
    report = test_setup["report"]
    original_path = report.image_storage_path

    diagnosis_service.diagnose_crop_report(
        db=sqlite_session,
        farmer_id=farmer.id,
        report_id=report.id,
    )

    sqlite_session.refresh(report)
    assert report.image_storage_path == original_path


def test_database_commit_failure_triggers_rollback(
    sqlite_session, diagnosis_service, mock_storage, mock_disease, test_setup, monkeypatch
):
    """Test 12: Database commit failure triggers rollback and leaves no persisted diagnosis."""
    farmer = test_setup["farmer"]
    report = test_setup["report"]

    # 1. Valid farmer, 2. Farmer crop, 3. Crop report with image_storage_path
    assert report.image_storage_path is not None

    # 4. Mock CropReportStorageService.download_image() returns valid image bytes
    mock_storage.fail_download = False
    assert len(mock_storage.image_bytes) > 0

    # 5. Mock DiseaseDetectionService.predict() returns a valid DiseasePredictionResponse
    mock_disease.fail_inference = False
    assert mock_disease.mock_response is not None

    # 6. Make the database session commit operation raise an appropriate database exception
    mock_rollback = MagicMock(wraps=sqlite_session.rollback)
    monkeypatch.setattr(sqlite_session, "rollback", mock_rollback)

    def failing_commit():
        raise OperationalError(
            statement="COMMIT",
            params={},
            orig=Exception("database is locked"),
        )

    monkeypatch.setattr(sqlite_session, "commit", failing_commit)

    # 7. Call diagnose_crop_report() & 8. Assert that the expected exception propagates
    with pytest.raises(OperationalError) as exc_info:
        diagnosis_service.diagnose_crop_report(
            db=sqlite_session,
            farmer_id=farmer.id,
            report_id=report.id,
        )

    assert "database is locked" in str(exc_info.value)

    # 9. Verify rollback was executed
    mock_rollback.assert_called_once()

    # 10. Verify that no CropReportDiagnosis row remains persisted
    assert sqlite_session.query(CropReportDiagnosis).count() == 0
    sqlite_session.refresh(report)
    assert len(report.diagnoses) == 0

