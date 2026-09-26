"""Unit and integration tests for Farmer Advisory API endpoint (Ollama-backed with fallback)."""
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from app.database.base import Base
from app.database.connection import get_db
from app.main import app
from app.models.crop import Crop
from app.models.crop_report import CropReport
from app.models.crop_report_diagnosis import CropReportDiagnosis
from app.models.farmer_advisory import FarmerAdvisory
from app.models.farmer_crop import FarmerCrop
from app.models.user_profile import UserProfile
from app.models.village import Village
from app.schemas.advisory import FarmerComprehensiveAdvisoryResponse
from app.schemas.weather import (
    ForecastMetrics,
)
from app.services.farmer_advisory_service import (
    FarmerAdvisoryService,
    OLLAMA_ADVISORY_SYSTEM_PROMPT,
    get_farmer_advisory_service,
)
from app.services.forecast_advisory_service import (
    ForecastAdvisoryResult,
    ForecastAdvisoryService,
)
from app.services.llm_provider import (
    LLMConnectionError,
    LLMProvider,
    LLMProviderError,
    LLMResponseError,
    LLMTimeoutError,
)
from app.services.weather_rule_engine import AdvisoryMatch

client = TestClient(app)


class MockLLMProvider(LLMProvider):
    """Mock LLMProvider recording calls and allowing injected responses or errors."""

    def __init__(self):
        self.call_count = 0
        self.last_prompt = None
        self.last_system_prompt = None
        self.next_response = "Synthesized advisory for farmer."
        self.raise_exception = None

    def generate(self, prompt: str, system_prompt: str = None) -> str:
        self.call_count += 1
        self.last_prompt = prompt
        self.last_system_prompt = system_prompt
        if self.raise_exception:
            raise self.raise_exception
        return self.next_response


from sqlalchemy.pool import StaticPool


@pytest.fixture
def sqlite_session():
    """Create isolated in-memory SQLite session with foreign keys enabled."""
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
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
            FarmerAdvisory.__table__,
        ],
    )
    with Session(engine) as session:
        yield session


@pytest.fixture
def mock_llm():
    return MockLLMProvider()


@pytest.fixture
def mock_forecast_service():
    service = MagicMock(spec=ForecastAdvisoryService)
    return service


@pytest.fixture
def test_data(sqlite_session):
    """Seed village, farmer, crop, farmer_crop, and diagnosis records."""
    village = Village(
        id="V001",
        name="Mangaluru",
        district="Dakshina Kannada",
        state="Karnataka",
        zone="Coastal",
        latitude=12.9141,
        longitude=74.8560,
    )
    farmer = UserProfile(
        id=uuid.uuid4(),
        full_name="Mahabaleshwar Bhat",
        phone="9876543210",
        village_id="V001",
        language="kn",
    )
    other_farmer = UserProfile(
        id=uuid.uuid4(),
        full_name="Ramesh Gowda",
        phone="9876543211",
        village_id="V001",
        language="kn",
    )
    crop = Crop(
        id=uuid.uuid4(),
        code="arecanut",
        name_en="Arecanut",
        name_kn="ಅಡಿಕೆ",
    )
    farmer_crop = FarmerCrop(
        id=uuid.uuid4(),
        farmer_id=farmer.id,
        crop_id=crop.id,
        is_primary=True,
    )
    other_farmer_crop = FarmerCrop(
        id=uuid.uuid4(),
        farmer_id=other_farmer.id,
        crop_id=crop.id,
        is_primary=True,
    )
    report = CropReport(
        id=uuid.uuid4(),
        farmer_crop_id=farmer_crop.id,
        notes="Yellow leaves observation",
        image_filename="leaf.jpg",
        image_storage_path="farmers/test/crop-reports/test/leaf.jpg",
    )
    diagnosis = CropReportDiagnosis(
        id=uuid.uuid4(),
        crop_report_id=report.id,
        crop="arecanut",
        predicted_class="yellow_leaf_disease",
        confidence=0.9250,
        model_name="krushisetu_efficientnet_b0_best.pth",
        predictions=[
            {"class_name": "yellow_leaf_disease", "confidence": 0.9250},
            {"class_name": "healthy", "confidence": 0.0500},
        ],
        created_at=datetime.now(timezone.utc),
    )

    sqlite_session.add_all([
        village,
        farmer,
        other_farmer,
        crop,
        farmer_crop,
        other_farmer_crop,
        report,
        diagnosis,
    ])
    sqlite_session.commit()

    return {
        "village": village,
        "farmer": farmer,
        "other_farmer": other_farmer,
        "crop": crop,
        "farmer_crop": farmer_crop,
        "other_farmer_crop": other_farmer_crop,
        "report": report,
        "diagnosis": diagnosis,
    }


def make_forecast_result(village, crop):
    """Helper to create sample ForecastAdvisoryResult."""
    metrics = ForecastMetrics(
        reference_time=datetime(2026, 9, 25, 0, 0, tzinfo=timezone.utc),
        rainfall_mm_24h=Decimal("15.00"),
        rainfall_mm_48h=Decimal("45.00"),
        max_temperature_c_24h=Decimal("30.00"),
        max_temperature_c_48h=Decimal("31.00"),
        avg_humidity_pct_24h=Decimal("85.00"),
        avg_humidity_pct_48h=Decimal("88.00"),
        max_wind_speed_kmh_24h=Decimal("12.00"),
        max_wind_speed_kmh_48h=Decimal("14.00"),
        cloudy_hours_24h=Decimal("16.00"),
        cloudy_hours_48h=Decimal("30.00"),
    )
    match = AdvisoryMatch(
        rule_id=1,
        crop="Arecanut",
        risk_name="Koleroga Weather Risk Context",
        risk_level="HIGH",
        condition_type="WEATHER_THRESHOLD",
        risk_context="Koleroga",
        matched_factors=["rainfall_mm_48h >= 40.0 mm"],
        advisory_en="Apply 1% Bordeaux mixture on bunches to prevent fruit rot.",
        advisory_kn="ಕೊಳೆರೋಗ ತಡೆಗಟ್ಟಲು ಗೊನೆಗಳಿಗೆ ಶೇ 1 ರ ಬೋರ್ಡೋ ಮಿಶ್ರಣ ಸಿಂಪಡಿಸಿ.",
        source_name="CPCRI",
        source_reference="Package of Practices",
    )
    return ForecastAdvisoryResult(
        village=village,
        crop=crop,
        forecast_reference_time=metrics.reference_time,
        metrics=metrics,
        advisories=[match],
        unsupported_rules=[],
    )


# ==============================================================================
# A. Generation & Language Tests
# ==============================================================================

def test_generate_advisory_success_english(sqlite_session, mock_llm, mock_forecast_service, test_data):
    """Test 1: Successful English advisory generation using local LLM."""
    farmer = test_data["farmer"]
    village = test_data["village"]
    crop = test_data["crop"]

    mock_forecast_service.get_forecast_advisories.return_value = make_forecast_result(village, crop)
    mock_llm.next_response = "Heavy rains are expected. Apply Bordeaux mixture and inspect for yellow leaf symptoms."

    service = FarmerAdvisoryService(
        forecast_advisory_service=mock_forecast_service,
        llm_provider=mock_llm,
    )

    app.dependency_overrides[get_db] = lambda: sqlite_session
    app.dependency_overrides[get_farmer_advisory_service] = lambda: service

    try:
        response = client.post(
            f"/api/v1/farmers/{farmer.id}/advisory",
            json={"language": "en"},
        )

        assert response.status_code == 200
        data = response.json()

        # Schema & response verification
        assert data["title"] == "Agricultural Advisory for Mahabaleshwar Bhat - Arecanut"
        assert data["severity"] == "HIGH"
        assert data["language"] == "en"
        assert data["is_llm_generated"] is True
        assert data["summary"] == "Heavy rains are expected. Apply Bordeaux mixture and inspect for yellow leaf symptoms."
        assert "yellow leaf disease" in data["reason"].lower()
        assert len(data["recommended_actions"]) >= 1
        assert any("Bordeaux mixture" in act for act in data["recommended_actions"])
        assert "CPCRI" in data["sources"]
        assert any("Disease Detection AI" in src for src in data["sources"])

        # Strict LLM Prompt Verification
        assert mock_llm.call_count == 1
        assert mock_llm.last_system_prompt == OLLAMA_ADVISORY_SYSTEM_PROMPT
        assert "Do not invent facts." in mock_llm.last_system_prompt
        assert "Language: en" in mock_llm.last_prompt
        assert "Farmer: Mahabaleshwar Bhat" in mock_llm.last_prompt
        assert "Risk Severity: HIGH" in mock_llm.last_prompt

    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_farmer_advisory_service, None)


def test_generate_advisory_success_kannada(sqlite_session, mock_llm, mock_forecast_service, test_data):
    """Test 2: Successful Kannada advisory generation using local LLM."""
    farmer = test_data["farmer"]
    village = test_data["village"]
    crop = test_data["crop"]

    mock_forecast_service.get_forecast_advisories.return_value = make_forecast_result(village, crop)
    kannada_summary = "ಮುಂದಿನ ದಿನಗಳಲ್ಲಿ ಮಳೆ ನಿರೀಕ್ಷೆಯಿದೆ. ಅಡಿಕೆ ಗೊನೆಗಳಿಗೆ ಬೋರ್ಡೋ ಸಿಂಪಡಿಸಿ."
    mock_llm.next_response = kannada_summary

    service = FarmerAdvisoryService(
        forecast_advisory_service=mock_forecast_service,
        llm_provider=mock_llm,
    )

    app.dependency_overrides[get_db] = lambda: sqlite_session
    app.dependency_overrides[get_farmer_advisory_service] = lambda: service

    try:
        response = client.post(
            f"/api/v1/farmers/{farmer.id}/advisory",
            json={"language": "kn"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["language"] == "kn"
        assert data["is_llm_generated"] is True
        assert data["summary"] == kannada_summary
        assert "ಅಡಿಕೆ" in data["title"]
        assert any("ಬೋರ್ಡೋ" in act for act in data["recommended_actions"])

        assert mock_llm.call_count == 1
        assert mock_llm.last_system_prompt == OLLAMA_ADVISORY_SYSTEM_PROMPT
        assert "Language: kn" in mock_llm.last_prompt
        assert "simple Kannada" in mock_llm.last_prompt

    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_farmer_advisory_service, None)


# ==============================================================================
# B. Ollama Unavailable & Deterministic Fallback Tests
# ==============================================================================

def test_generate_advisory_ollama_connection_error_fallback(sqlite_session, mock_llm, mock_forecast_service, test_data):
    """Test 3: LLM connection failure falls back cleanly to deterministic guidance without crashing."""
    farmer = test_data["farmer"]
    village = test_data["village"]
    crop = test_data["crop"]

    mock_forecast_service.get_forecast_advisories.return_value = make_forecast_result(village, crop)
    mock_llm.raise_exception = LLMConnectionError("Ollama daemon is not running on localhost:11434")

    service = FarmerAdvisoryService(
        forecast_advisory_service=mock_forecast_service,
        llm_provider=mock_llm,
    )

    app.dependency_overrides[get_db] = lambda: sqlite_session
    app.dependency_overrides[get_farmer_advisory_service] = lambda: service

    try:
        response = client.post(
            f"/api/v1/farmers/{farmer.id}/advisory",
            json={"language": "en"},
        )

        assert response.status_code == 200
        data = response.json()

        # Ensures clean fallback
        assert data["is_llm_generated"] is False
        assert data["language"] == "en"
        assert len(data["summary"]) > 0
        assert "Bordeaux mixture" in data["summary"]
        assert data["severity"] == "HIGH"

    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_farmer_advisory_service, None)


def test_generate_advisory_ollama_timeout_fallback(sqlite_session, mock_llm, mock_forecast_service, test_data):
    """Test 4: LLM timeout falls back cleanly to deterministic advisory."""
    farmer = test_data["farmer"]
    village = test_data["village"]
    crop = test_data["crop"]

    mock_forecast_service.get_forecast_advisories.return_value = make_forecast_result(village, crop)
    mock_llm.raise_exception = LLMTimeoutError("Ollama timed out after 60s")

    service = FarmerAdvisoryService(
        forecast_advisory_service=mock_forecast_service,
        llm_provider=mock_llm,
    )

    app.dependency_overrides[get_db] = lambda: sqlite_session
    app.dependency_overrides[get_farmer_advisory_service] = lambda: service

    try:
        response = client.post(
            f"/api/v1/farmers/{farmer.id}/advisory",
            json={"language": "kn"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["is_llm_generated"] is False
        assert data["language"] == "kn"
        assert len(data["summary"]) > 0
        assert "ಬೋರ್ಡೋ" in data["summary"]

    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_farmer_advisory_service, None)


def test_generate_advisory_groq_api_error_fallback(sqlite_session, mock_llm, mock_forecast_service, test_data):
    """Test 5a: Groq API response error (401/429/5xx) falls back to deterministic advisory."""
    farmer = test_data["farmer"]
    village = test_data["village"]
    crop = test_data["crop"]

    mock_forecast_service.get_forecast_advisories.return_value = make_forecast_result(village, crop)
    mock_llm.raise_exception = LLMResponseError("Groq API rate limit exceeded.")

    service = FarmerAdvisoryService(
        forecast_advisory_service=mock_forecast_service,
        llm_provider=mock_llm,
    )

    app.dependency_overrides[get_db] = lambda: sqlite_session
    app.dependency_overrides[get_farmer_advisory_service] = lambda: service

    try:
        response = client.post(
            f"/api/v1/farmers/{farmer.id}/advisory",
            json={"language": "kn"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["is_llm_generated"] is False
        assert data["language"] == "kn"
        assert len(data["summary"]) > 0
        assert "ಬೋರ್ಡೋ" in data["summary"]

    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_farmer_advisory_service, None)


def test_generate_advisory_groq_provider_error_fallback(sqlite_session, mock_llm, mock_forecast_service, test_data):
    """Test 5b: Groq malformed response / provider error falls back cleanly without crashing."""
    farmer = test_data["farmer"]
    village = test_data["village"]
    crop = test_data["crop"]

    mock_forecast_service.get_forecast_advisories.return_value = make_forecast_result(village, crop)
    mock_llm.raise_exception = LLMProviderError("No response choices returned by Groq service.")

    service = FarmerAdvisoryService(
        forecast_advisory_service=mock_forecast_service,
        llm_provider=mock_llm,
    )

    app.dependency_overrides[get_db] = lambda: sqlite_session
    app.dependency_overrides[get_farmer_advisory_service] = lambda: service

    try:
        response = client.post(
            f"/api/v1/farmers/{farmer.id}/advisory",
            json={"language": "en"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["is_llm_generated"] is False
        assert data["language"] == "en"
        assert len(data["summary"]) > 0
        assert "Bordeaux mixture" in data["summary"]
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_farmer_advisory_service, None)


def test_generate_advisory_empty_response_fallback(sqlite_session, mock_llm, mock_forecast_service, test_data):
    """Test 5c: Empty LLM response triggers deterministic fallback."""
    farmer = test_data["farmer"]
    village = test_data["village"]
    crop = test_data["crop"]

    mock_forecast_service.get_forecast_advisories.return_value = make_forecast_result(village, crop)
    mock_llm.next_response = "   "

    service = FarmerAdvisoryService(
        forecast_advisory_service=mock_forecast_service,
        llm_provider=mock_llm,
    )

    app.dependency_overrides[get_db] = lambda: sqlite_session
    app.dependency_overrides[get_farmer_advisory_service] = lambda: service

    try:
        response = client.post(
            f"/api/v1/farmers/{farmer.id}/advisory",
            json={"language": "en"},
        )

        assert response.status_code == 200
        data = response.json()

        assert data["is_llm_generated"] is False
        assert len(data["summary"]) > 0

    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_farmer_advisory_service, None)


# ==============================================================================
# C. Farmer Ownership & Validation Tests
# ==============================================================================

def test_generate_advisory_farmer_not_found(sqlite_session):
    """Test 6: Nonexistent farmer returns HTTP 404."""
    non_existent_id = uuid.uuid4()
    app.dependency_overrides[get_db] = lambda: sqlite_session

    try:
        response = client.post(f"/api/v1/farmers/{non_existent_id}/advisory")
        assert response.status_code == 404
        assert response.json()["detail"] == "Farmer not found"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_generate_advisory_crop_ownership_violation(sqlite_session, test_data):
    """Test 7: Cross-farmer crop relationship returns HTTP 404."""
    farmer = test_data["farmer"]
    other_crop = test_data["other_farmer_crop"]

    app.dependency_overrides[get_db] = lambda: sqlite_session

    try:
        response = client.post(
            f"/api/v1/farmers/{farmer.id}/advisory",
            json={"crop_id": str(other_crop.id)},
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Farmer crop not found"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_generate_advisory_invalid_uuid():
    """Test 8: Invalid farmer UUID in URL path returns HTTP 422."""
    response = client.post("/api/v1/farmers/invalid-uuid-string/advisory")
    assert response.status_code == 422


def test_generate_advisory_invalid_language(sqlite_session, test_data):
    """Test 9: Invalid language code in payload returns HTTP 422."""
    farmer = test_data["farmer"]
    app.dependency_overrides[get_db] = lambda: sqlite_session

    try:
        response = client.post(
            f"/api/v1/farmers/{farmer.id}/advisory",
            json={"language": "es"},
        )
        assert response.status_code == 422
    finally:
        app.dependency_overrides.pop(get_db, None)


# ==============================================================================
# D. Schema & OpenAPI Contract Tests
# ==============================================================================

def test_generate_advisory_schema_structure(sqlite_session, mock_llm, test_data):
    """Test 10: Complete response adheres to FarmerComprehensiveAdvisoryResponse schema."""
    farmer = test_data["farmer"]
    service = FarmerAdvisoryService(llm_provider=mock_llm)
    app.dependency_overrides[get_db] = lambda: sqlite_session
    app.dependency_overrides[get_farmer_advisory_service] = lambda: service

    try:
        response = client.post(f"/api/v1/farmers/{farmer.id}/advisory")
        assert response.status_code == 200

        data = response.json()
        validated = FarmerComprehensiveAdvisoryResponse.model_validate(data)
        assert validated.title
        assert validated.severity in ["LOW", "MODERATE", "HIGH", "INFO"]
        assert validated.summary
        assert validated.reason
        assert isinstance(validated.recommended_actions, list)
        assert validated.language in ["en", "kn"]
        assert isinstance(validated.sources, list)
        assert isinstance(validated.provenance, list)
        assert isinstance(validated.is_llm_generated, bool)
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_farmer_advisory_service, None)


def test_openapi_schema_contains_advisory_endpoint():
    """Test 11: OpenAPI definition contains the farmer advisory endpoint with expected contract."""
    schema = app.openapi()
    path = "/api/v1/farmers/{farmer_id}/advisory"
    assert path in schema["paths"]

    op = schema["paths"][path]["post"]
    assert op["summary"] == "Generate comprehensive farmer advisory"
    assert "200" in op["responses"]
    assert "404" in op["responses"]
    assert "422" in op["responses"]

    param_names = [p["name"] for p in op.get("parameters", [])]
    assert "farmer_id" in param_names
