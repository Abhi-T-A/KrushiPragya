"""Unit and integration tests for Crop Report Disease Diagnosis API."""
from datetime import datetime, timezone
from unittest.mock import MagicMock
import uuid
import pytest
from fastapi.testclient import TestClient

from app.database.connection import get_db
from app.main import app
from app.models.crop_report_diagnosis import CropReportDiagnosis
from app.schemas.crop_report import CropReportDiagnosisRecordResponse
from app.services.crop_report_diagnosis_service import (
    CropReportImageNotFoundError,
    get_crop_report_diagnosis_service,
)
from app.services.crop_report_service import CropReportNotFoundError
from app.services.crop_report_storage_service import StorageServiceError
from app.services.disease_detection_service import (
    DiseaseDetectionError,
    UnsupportedCropError,
)
from app.services.farmer_crop_service import FarmerNotFoundError

client = TestClient(app)


def make_sample_diagnosis(
    farmer_id: uuid.UUID = None,
    report_id: uuid.UUID = None,
) -> CropReportDiagnosis:
    """Create a sample persisted CropReportDiagnosis domain object."""
    return CropReportDiagnosis(
        id=uuid.uuid4(),
        crop_report_id=report_id or uuid.uuid4(),
        crop="arecanut",
        predicted_class="yellow_leaf_disease",
        confidence=0.9421,
        model_name="krushisetu_efficientnet_b0_best.pth",
        predictions=[
            {"class_name": "yellow_leaf_disease", "confidence": 0.9421},
            {"class_name": "healthy", "confidence": 0.0350},
            {"class_name": "mahali_koleroga", "confidence": 0.0229},
        ],
        created_at=datetime.now(timezone.utc),
    )


@pytest.fixture
def mock_db():
    """Mock database session."""
    return MagicMock()


@pytest.fixture
def mock_service():
    """Mock diagnosis service."""
    return MagicMock()


@pytest.fixture(autouse=True)
def override_dependencies(mock_db, mock_service):
    """Override database and diagnosis service dependencies for isolated API testing."""
    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_crop_report_diagnosis_service] = lambda: mock_service
    yield
    app.dependency_overrides.pop(get_db, None)
    app.dependency_overrides.pop(get_crop_report_diagnosis_service, None)


# ==============================================================================
# A. Success Tests
# ==============================================================================

def test_diagnose_crop_report_success(mock_service):
    """Test 1: Successful diagnosis returns HTTP 200 with complete response schema."""
    farmer_id = uuid.uuid4()
    report_id = uuid.uuid4()
    diagnosis = make_sample_diagnosis(farmer_id=farmer_id, report_id=report_id)
    mock_service.diagnose_crop_report.return_value = diagnosis

    response = client.post(
        f"/api/v1/farmers/{farmer_id}/crop-reports/{report_id}/diagnose"
    )

    assert response.status_code == 200
    data = response.json()
    assert data["id"] == str(diagnosis.id)
    assert data["crop_report_id"] == str(report_id)
    assert data["crop"] == "arecanut"
    assert data["predicted_class"] == "yellow_leaf_disease"
    assert data["confidence"] == pytest.approx(0.9421)
    assert data["model_name"] == "krushisetu_efficientnet_b0_best.pth"
    assert isinstance(data["predictions"], list)
    assert len(data["predictions"]) == 3
    assert data["predictions"][0]["class_name"] == "yellow_leaf_disease"
    assert data["predictions"][0]["confidence"] == pytest.approx(0.9421)
    assert "created_at" in data
    # Ensure no storage secrets or raw bytes exposed
    assert "storage_path" not in data
    assert "image_bytes" not in data
    assert "service_role_key" not in data


# ==============================================================================
# B. Farmer / Report Validation Tests
# ==============================================================================

def test_diagnose_crop_report_farmer_not_found(mock_service):
    """Test 2: Nonexistent farmer returns HTTP 404 with 'Farmer not found'."""
    farmer_id = uuid.uuid4()
    report_id = uuid.uuid4()
    mock_service.diagnose_crop_report.side_effect = FarmerNotFoundError(
        f"Farmer with ID '{farmer_id}' not found."
    )

    response = client.post(
        f"/api/v1/farmers/{farmer_id}/crop-reports/{report_id}/diagnose"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Farmer not found"}


def test_diagnose_crop_report_report_not_found(mock_service):
    """Test 3: Nonexistent report returns HTTP 404 with 'Crop report not found'."""
    farmer_id = uuid.uuid4()
    report_id = uuid.uuid4()
    mock_service.diagnose_crop_report.side_effect = CropReportNotFoundError(
        f"Crop report with ID '{report_id}' not found."
    )

    response = client.post(
        f"/api/v1/farmers/{farmer_id}/crop-reports/{report_id}/diagnose"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Crop report not found"}


def test_diagnose_crop_report_cross_farmer_report(mock_service):
    """Test 4: Cross-farmer report returns HTTP 404 with 'Crop report not found'."""
    farmer_id = uuid.uuid4()
    report_id = uuid.uuid4()
    mock_service.diagnose_crop_report.side_effect = CropReportNotFoundError(
        f"Crop report with ID '{report_id}' not found for farmer '{farmer_id}'."
    )

    response = client.post(
        f"/api/v1/farmers/{farmer_id}/crop-reports/{report_id}/diagnose"
    )

    assert response.status_code == 404
    assert response.json() == {"detail": "Crop report not found"}


# ==============================================================================
# C. Image State Tests
# ==============================================================================

def test_diagnose_crop_report_no_image_conflict(mock_service):
    """Test 5: Report without uploaded image returns HTTP 409 with 'Crop report has no image'."""
    farmer_id = uuid.uuid4()
    report_id = uuid.uuid4()
    mock_service.diagnose_crop_report.side_effect = CropReportImageNotFoundError(
        f"Crop report '{report_id}' has no uploaded image to diagnose."
    )

    response = client.post(
        f"/api/v1/farmers/{farmer_id}/crop-reports/{report_id}/diagnose"
    )

    assert response.status_code == 409
    assert response.json() == {"detail": "Crop report has no image"}


# ==============================================================================
# D. Disease Errors
# ==============================================================================

def test_diagnose_crop_report_unsupported_crop(mock_service):
    """Test 6: Unsupported crop returns HTTP 422 with 'Crop is not supported for disease detection'."""
    farmer_id = uuid.uuid4()
    report_id = uuid.uuid4()
    mock_service.diagnose_crop_report.side_effect = UnsupportedCropError(
        "wheat", ["arecanut", "paddy", "coconut"]
    )

    response = client.post(
        f"/api/v1/farmers/{farmer_id}/crop-reports/{report_id}/diagnose"
    )

    assert response.status_code == 422
    assert response.json() == {"detail": "Crop is not supported for disease detection"}


def test_diagnose_crop_report_inference_failure(mock_service):
    """Test 7: Disease inference failure returns HTTP 500 with 'Disease analysis failed'."""
    farmer_id = uuid.uuid4()
    report_id = uuid.uuid4()
    mock_service.diagnose_crop_report.side_effect = DiseaseDetectionError(
        "Model execution failed with CUDA out of memory"
    )

    response = client.post(
        f"/api/v1/farmers/{farmer_id}/crop-reports/{report_id}/diagnose"
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Disease analysis failed"}


# ==============================================================================
# E. Storage Errors
# ==============================================================================

def test_diagnose_crop_report_storage_download_failure(mock_service):
    """Test 8: Storage download failure returns HTTP 502 with 'Unable to retrieve crop report image'."""
    farmer_id = uuid.uuid4()
    report_id = uuid.uuid4()
    mock_service.diagnose_crop_report.side_effect = StorageServiceError(
        "HTTP network failure during storage download: Connection reset"
    )

    response = client.post(
        f"/api/v1/farmers/{farmer_id}/crop-reports/{report_id}/diagnose"
    )

    assert response.status_code == 502
    assert response.json() == {"detail": "Unable to retrieve crop report image"}


# ==============================================================================
# F. Database / Unexpected Service Failure
# ==============================================================================

def test_diagnose_crop_report_unexpected_failure(mock_service):
    """Test 9: Unexpected service failure returns HTTP 500 with 'Unable to diagnose crop report'."""
    farmer_id = uuid.uuid4()
    report_id = uuid.uuid4()
    mock_service.diagnose_crop_report.side_effect = RuntimeError(
        "Database pool connection exhausted"
    )

    response = client.post(
        f"/api/v1/farmers/{farmer_id}/crop-reports/{report_id}/diagnose"
    )

    assert response.status_code == 500
    assert response.json() == {"detail": "Unable to diagnose crop report"}


# ==============================================================================
# G. API Contract & OpenAPI Tests
# ==============================================================================

def test_diagnose_crop_report_no_request_body_required(mock_service):
    """Test 10: Endpoint succeeds without any request body."""
    farmer_id = uuid.uuid4()
    report_id = uuid.uuid4()
    mock_service.diagnose_crop_report.return_value = make_sample_diagnosis(
        farmer_id=farmer_id, report_id=report_id
    )

    # Calling post without content/json/data
    response = client.post(
        f"/api/v1/farmers/{farmer_id}/crop-reports/{report_id}/diagnose"
    )
    assert response.status_code == 200

    # Calling post with empty json {} also succeeds
    response2 = client.post(
        f"/api/v1/farmers/{farmer_id}/crop-reports/{report_id}/diagnose",
        json={},
    )
    assert response2.status_code == 200


def test_diagnose_crop_report_invalid_farmer_uuid():
    """Test 11: Invalid farmer_id UUID format returns HTTP 422."""
    report_id = uuid.uuid4()
    response = client.post(
        f"/api/v1/farmers/not-a-valid-uuid/crop-reports/{report_id}/diagnose"
    )
    assert response.status_code == 422


def test_diagnose_crop_report_invalid_report_uuid():
    """Test 12: Invalid report_id UUID format returns HTTP 422."""
    farmer_id = uuid.uuid4()
    response = client.post(
        f"/api/v1/farmers/{farmer_id}/crop-reports/not-a-valid-uuid/diagnose"
    )
    assert response.status_code == 422


def test_openapi_contains_endpoint_and_contract():
    """Test 13: OpenAPI schema registers endpoint with path parameters and no request body."""
    schema = app.openapi()
    path = "/api/v1/farmers/{farmer_id}/crop-reports/{report_id}/diagnose"
    assert path in schema["paths"]

    op = schema["paths"][path]["post"]
    assert "requestBody" not in op

    param_names = [p["name"] for p in op["parameters"]]
    assert "farmer_id" in param_names
    assert "report_id" in param_names

    # Verify UUID format on parameters
    for p in op["parameters"]:
        assert p["in"] == "path"
        assert p["required"] is True
        assert p["schema"]["type"] == "string"
        assert p["schema"]["format"] == "uuid"


def test_openapi_response_schema_registered_and_no_secrets():
    """Test 14: Response schema is registered in OpenAPI components and leaks no secrets."""
    schema = app.openapi()
    schemas = schema["components"]["schemas"]
    assert "CropReportDiagnosisRecordResponse" in schemas

    response_schema = schemas["CropReportDiagnosisRecordResponse"]
    props = response_schema["properties"]

    expected_fields = [
        "id",
        "crop_report_id",
        "crop",
        "predicted_class",
        "confidence",
        "model_name",
        "predictions",
        "created_at",
    ]
    for field in expected_fields:
        assert field in props, f"Field '{field}' missing from OpenAPI schema"

    # Confirm sensitive/internal fields are absent
    forbidden = ["secret", "token", "password", "service_role_key", "signed_url", "image_bytes"]
    for key in forbidden:
        assert key not in props, f"Forbidden key '{key}' found in schema properties"
