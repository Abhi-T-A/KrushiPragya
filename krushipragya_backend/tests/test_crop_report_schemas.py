"""Focused unit tests for Crop Report and Disease Report domain Pydantic schemas."""
from datetime import datetime, timezone
import uuid
import pytest
from pydantic import ValidationError

from app.schemas.crop_report import (
    CropReportCreate,
    CropReportDiagnosisResponse,
    CropReportImageResponse,
    CropReportResponse,
    CropReportUpdate,
    CropReportWithCropResponse,
    DiseasePredictionResult,
)
from app.schemas.farmer_crop import CropResponse


class MockCrop:
    """Mock representing an SQLAlchemy Crop ORM instance."""

    def __init__(
        self,
        id: uuid.UUID,
        code: str = "arecanut",
        name_en: str = "Arecanut",
        name_kn: str = "ಅಡಿಕೆ",
        is_active: bool = True,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.id = id
        self.code = code
        self.name_en = name_en
        self.name_kn = name_kn
        self.is_active = is_active
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)


class MockCropReport:
    """Mock representing an SQLAlchemy CropReport ORM instance."""

    def __init__(
        self,
        id: uuid.UUID,
        farmer_crop_id: uuid.UUID,
        notes: str | None = None,
        image_filename: str | None = None,
        image_storage_path: str | None = None,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        crop: MockCrop | None = None,
    ):
        self.id = id
        self.farmer_crop_id = farmer_crop_id
        self.notes = notes
        self.image_filename = image_filename
        self.image_storage_path = image_storage_path
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.crop = crop


# ==============================================================================
# 1. CropReportCreate Tests
# ==============================================================================

def test_crop_report_create_valid():
    """Test 1: CropReportCreate accepts valid input."""
    fc_id = uuid.uuid4()
    report = CropReportCreate(
        farmer_crop_id=fc_id,
        notes="Yellow spots on lower leaves",
        image_filename="leaf_observation.jpg",
    )
    assert report.farmer_crop_id == fc_id
    assert report.notes == "Yellow spots on lower leaves"
    assert report.image_filename == "leaf_observation.jpg"


def test_crop_report_create_requires_farmer_crop_id():
    """Test 2: CropReportCreate requires farmer_crop_id."""
    with pytest.raises(ValidationError) as exc_info:
        CropReportCreate(notes="Missing farmer crop id")
    assert "farmer_crop_id" in str(exc_info.value)


def test_crop_report_create_notes_accepts_valid_text():
    """Test 3: notes accepts valid text and optional None."""
    fc_id = uuid.uuid4()
    # With notes
    r1 = CropReportCreate(farmer_crop_id=fc_id, notes="Healthy leaves")
    assert r1.notes == "Healthy leaves"

    # With None
    r2 = CropReportCreate(farmer_crop_id=fc_id, notes=None)
    assert r2.notes is None

    # Default None
    r3 = CropReportCreate(farmer_crop_id=fc_id)
    assert r3.notes is None


def test_crop_report_create_notes_rejects_over_1000_chars():
    """Test 4: notes rejects >1000 characters."""
    fc_id = uuid.uuid4()
    # Exactly 1000 chars works
    valid_notes = "a" * 1000
    report = CropReportCreate(farmer_crop_id=fc_id, notes=valid_notes)
    assert len(report.notes) == 1000

    # 1001 chars fails
    invalid_notes = "a" * 1001
    with pytest.raises(ValidationError) as exc_info:
        CropReportCreate(farmer_crop_id=fc_id, notes=invalid_notes)
    assert "notes" in str(exc_info.value)


def test_crop_report_create_image_filename_accepts_valid_filename():
    """Test 5: image_filename accepts valid filename and optional None."""
    fc_id = uuid.uuid4()
    # With filename
    r1 = CropReportCreate(farmer_crop_id=fc_id, image_filename="photo_123.jpg")
    assert r1.image_filename == "photo_123.jpg"

    # With None
    r2 = CropReportCreate(farmer_crop_id=fc_id, image_filename=None)
    assert r2.image_filename is None


def test_crop_report_create_image_filename_rejects_over_255_chars():
    """Test 6: image_filename rejects >255 characters."""
    fc_id = uuid.uuid4()
    # Exactly 255 chars works
    valid_name = "a" * 251 + ".jpg"
    report = CropReportCreate(farmer_crop_id=fc_id, image_filename=valid_name)
    assert len(report.image_filename) == 255

    # 256 chars fails
    invalid_name = "a" * 252 + ".jpg"
    with pytest.raises(ValidationError) as exc_info:
        CropReportCreate(farmer_crop_id=fc_id, image_filename=invalid_name)
    assert "image_filename" in str(exc_info.value)


def test_crop_report_create_does_not_contain_farmer_id():
    """Test 7: CropReportCreate does not contain farmer_id field."""
    assert "farmer_id" not in CropReportCreate.model_fields


def test_crop_report_create_does_not_contain_crop_id():
    """Test 8: CropReportCreate does not contain crop_id or internal fields."""
    assert "crop_id" not in CropReportCreate.model_fields
    assert "id" not in CropReportCreate.model_fields
    assert "created_at" not in CropReportCreate.model_fields
    assert "updated_at" not in CropReportCreate.model_fields
    assert "image_storage_path" not in CropReportCreate.model_fields
    assert "storage_path" not in CropReportCreate.model_fields
    assert "image_url" not in CropReportCreate.model_fields
    assert "diagnosis" not in CropReportCreate.model_fields
    assert "confidence" not in CropReportCreate.model_fields


# ==============================================================================
# 2. CropReportUpdate Tests
# ==============================================================================

def test_crop_report_update_allows_partial_updates():
    """Test 9: CropReportUpdate allows partial updates (PATCH semantics)."""
    # Empty update
    u1 = CropReportUpdate()
    assert u1.model_dump(exclude_unset=True) == {}

    # Update only notes
    u2 = CropReportUpdate(notes="Updated observation notes")
    dumped2 = u2.model_dump(exclude_unset=True)
    assert dumped2 == {"notes": "Updated observation notes"}

    # Update only image_filename
    u3 = CropReportUpdate(image_filename="new_leaf.png")
    dumped3 = u3.model_dump(exclude_unset=True)
    assert dumped3 == {"image_filename": "new_leaf.png"}

    # Update both
    u4 = CropReportUpdate(notes="Both updated", image_filename="both.png")
    assert u4.notes == "Both updated"
    assert u4.image_filename == "both.png"


def test_crop_report_update_does_not_contain_farmer_crop_id():
    """Test 10: CropReportUpdate does not contain farmer_crop_id or immutable fields."""
    assert "farmer_crop_id" not in CropReportUpdate.model_fields
    assert "farmer_id" not in CropReportUpdate.model_fields
    assert "crop_id" not in CropReportUpdate.model_fields
    assert "id" not in CropReportUpdate.model_fields
    assert "diagnosis" not in CropReportUpdate.model_fields
    assert "confidence" not in CropReportUpdate.model_fields
    assert "image_storage_path" not in CropReportUpdate.model_fields
    assert "image_url" not in CropReportUpdate.model_fields


# ==============================================================================
# 3. CropReportResponse Tests
# ==============================================================================

def test_crop_report_response_serializes_orm_data():
    """Test 11: CropReportResponse serializes ORM-style data."""
    report_id = uuid.uuid4()
    fc_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock = MockCropReport(
        id=report_id,
        farmer_crop_id=fc_id,
        notes="Yellowing foliage detected",
        image_filename="observation_001.jpg",
        image_storage_path="crop_reports/2026/09/uuid.jpg",
        created_at=now,
        updated_at=now,
    )

    resp = CropReportResponse.model_validate(mock)
    assert resp.id == report_id
    assert resp.farmer_crop_id == fc_id
    assert resp.notes == "Yellowing foliage detected"
    assert resp.image_filename == "observation_001.jpg"
    assert resp.image_storage_path == "crop_reports/2026/09/uuid.jpg"
    assert resp.created_at == now
    assert resp.updated_at == now
    assert isinstance(resp.id, uuid.UUID)
    assert isinstance(resp.farmer_crop_id, uuid.UUID)
    assert isinstance(resp.created_at, datetime)
    assert isinstance(resp.updated_at, datetime)


# ==============================================================================
# 4. CropReportWithCropResponse Tests
# ==============================================================================

def test_crop_report_with_crop_response_serializes_nested_crop():
    """Test 12: CropReportWithCropResponse serializes nested CropResponse."""
    crop_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_crop = MockCrop(
        id=crop_id,
        code="arecanut",
        name_en="Arecanut",
        name_kn="ಅಡಿಕೆ",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    report_id = uuid.uuid4()
    fc_id = uuid.uuid4()
    mock_report = MockCropReport(
        id=report_id,
        farmer_crop_id=fc_id,
        notes="Arecanut leaf rot symptoms",
        image_filename="areca_rot.jpg",
        image_storage_path="reports/areca_rot.jpg",
        created_at=now,
        updated_at=now,
        crop=mock_crop,
    )

    resp = CropReportWithCropResponse.model_validate(mock_report)
    assert resp.id == report_id
    assert resp.farmer_crop_id == fc_id
    assert resp.crop.id == crop_id
    assert resp.crop.code == "arecanut"
    assert resp.crop.name_en == "Arecanut"
    assert resp.crop.name_kn == "ಅಡಿಕೆ"
    assert resp.crop.is_active is True
    assert isinstance(resp.crop, CropResponse)


# ==============================================================================
# 5. CropReportImageResponse Tests
# ==============================================================================

def test_crop_report_image_response_accepts_valid_image_metadata():
    """Test 13: CropReportImageResponse accepts valid image metadata."""
    report_id = uuid.uuid4()
    img_resp = CropReportImageResponse(
        report_id=report_id,
        image_filename="leaf_rot.jpeg",
        image_storage_path="reports/f0c4/leaf_rot.jpeg",
        content_type="image/jpeg",
        size_bytes=204800,
    )
    assert img_resp.report_id == report_id
    assert img_resp.image_filename == "leaf_rot.jpeg"
    assert img_resp.image_storage_path == "reports/f0c4/leaf_rot.jpeg"
    assert img_resp.content_type == "image/jpeg"
    assert img_resp.size_bytes == 204800

    # Test rejection of non-image MIME types
    with pytest.raises(ValidationError) as exc_info:
        CropReportImageResponse(
            report_id=report_id,
            image_filename="document.pdf",
            image_storage_path="reports/f0c4/document.pdf",
            content_type="application/pdf",
            size_bytes=1024,
        )
    assert "content_type" in str(exc_info.value)


def test_crop_report_image_response_rejects_negative_size_bytes():
    """Test 14: CropReportImageResponse rejects negative size_bytes."""
    report_id = uuid.uuid4()
    with pytest.raises(ValidationError) as exc_info:
        CropReportImageResponse(
            report_id=report_id,
            image_filename="leaf.png",
            image_storage_path="reports/leaf.png",
            content_type="image/png",
            size_bytes=-1,
        )
    assert "size_bytes" in str(exc_info.value)

    # 0 bytes is valid
    zero_size = CropReportImageResponse(
        report_id=report_id,
        image_filename="leaf.png",
        image_storage_path="reports/leaf.png",
        content_type="image/png",
        size_bytes=0,
    )
    assert zero_size.size_bytes == 0


# ==============================================================================
# 6. DiseasePredictionResult Tests
# ==============================================================================

def test_disease_prediction_result_accepts_confidence_between_0_and_1():
    """Test 15: DiseasePredictionResult accepts confidence between 0 and 1."""
    # Boundary 0.0
    r0 = DiseasePredictionResult(crop="arecanut", predicted_class="healthy", confidence=0.0)
    assert r0.confidence == 0.0

    # Mid 0.85
    r_mid = DiseasePredictionResult(
        crop="arecanut", predicted_class="kole_roga", confidence=0.85
    )
    assert r_mid.confidence == 0.85

    # Boundary 1.0
    r1 = DiseasePredictionResult(crop="arecanut", predicted_class="yellow_leaf", confidence=1.0)
    assert r1.confidence == 1.0


def test_disease_prediction_result_rejects_confidence_less_than_0():
    """Test 16: DiseasePredictionResult rejects confidence <0."""
    with pytest.raises(ValidationError) as exc_info:
        DiseasePredictionResult(crop="arecanut", predicted_class="kole_roga", confidence=-0.01)
    assert "confidence" in str(exc_info.value)


def test_disease_prediction_result_rejects_confidence_greater_than_1():
    """Test 17: DiseasePredictionResult rejects confidence >1."""
    with pytest.raises(ValidationError) as exc_info:
        DiseasePredictionResult(crop="arecanut", predicted_class="kole_roga", confidence=1.01)
    assert "confidence" in str(exc_info.value)


# ==============================================================================
# 7. CropReportDiagnosisResponse Tests
# ==============================================================================

def test_crop_report_diagnosis_response_serializes_nested():
    """Test 18: CropReportDiagnosisResponse serializes nested report + prediction."""
    report_id = uuid.uuid4()
    fc_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock = MockCropReport(
        id=report_id,
        farmer_crop_id=fc_id,
        notes="Infected fruit stalks",
        image_filename="fruit_rot.jpg",
        image_storage_path="reports/2026/fruit_rot.jpg",
        created_at=now,
        updated_at=now,
    )
    report_response = CropReportResponse.model_validate(mock)
    prediction_result = DiseasePredictionResult(
        crop="arecanut",
        predicted_class="kole_roga",
        confidence=0.942,
    )

    combined = CropReportDiagnosisResponse(
        report=report_response,
        prediction=prediction_result,
    )
    assert combined.report.id == report_id
    assert combined.report.farmer_crop_id == fc_id
    assert combined.prediction.crop == "arecanut"
    assert combined.prediction.predicted_class == "kole_roga"
    assert combined.prediction.confidence == 0.942


# ==============================================================================
# 8. Type Safety and Storage Security Verification
# ==============================================================================

def test_type_safety_and_storage_security_verification():
    """Test 19: Verify types remain UUID/datetime, no binary data, no signed URLs."""
    report_id = uuid.uuid4()
    fc_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    report = CropReportResponse(
        id=report_id,
        farmer_crop_id=fc_id,
        notes="Field notes",
        image_filename="leaf.jpg",
        image_storage_path="crop_reports/uuid_path.jpg",
        created_at=now,
        updated_at=now,
    )

    # UUID fields are UUID objects
    assert isinstance(report.id, uuid.UUID)
    assert isinstance(report.farmer_crop_id, uuid.UUID)

    # Timestamps are datetime objects
    assert isinstance(report.created_at, datetime)
    assert isinstance(report.updated_at, datetime)

    # Verify no binary or base64 fields are present in any of the schemas
    schemas = [
        CropReportCreate,
        CropReportUpdate,
        CropReportResponse,
        CropReportWithCropResponse,
        CropReportImageResponse,
        DiseasePredictionResult,
        CropReportDiagnosisResponse,
    ]
    for schema in schemas:
        field_names = list(schema.model_fields.keys())
        assert "image_base64" not in field_names
        assert "image_bytes" not in field_names
        assert "base64" not in field_names
        assert "signed_url" not in field_names
        assert "access_token" not in field_names

    # Verify storage path is an internal reference path, not a signed URL
    assert not report.image_storage_path.startswith("http://")
    assert not report.image_storage_path.startswith("https://")
    assert "token=" not in report.image_storage_path
    assert "signature=" not in report.image_storage_path
