"""Dynamic Real-Time Evidence-Grounded Farmer Advisory Tests.

Validates Scenarios A through H ensuring:
- Dynamic context assembly driven by current application facts
- No hallucinated agricultural data, weather metrics, or diagnoses
- Strict source/provenance integrity (no fabricated institutions)
- Clean deterministic fallbacks on LLM errors
- Timestamps and freshness metadata
"""
from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
import uuid
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.database.base import Base
from app.database.connection import get_db
from app.main import app
from app.models.crop import Crop
from app.models.crop_report import CropReport
from app.models.crop_report_diagnosis import CropReportDiagnosis
from app.models.farmer_crop import FarmerCrop
from app.models.user_profile import UserProfile
from app.models.village import Village
from app.schemas.advisory import FarmerComprehensiveAdvisoryResponse
from app.schemas.weather import (
    ForecastMetrics,
)
from app.services.farmer_advisory_service import (
    FarmerAdvisoryService,
    STRICT_ADVISORY_SYSTEM_PROMPT,
    get_farmer_advisory_service,
)
from app.services.forecast_advisory_service import (
    ForecastAdvisoryResult,
    ForecastAdvisoryService,
)
from app.services.llm_provider import (
    LLMConnectionError,
    LLMProvider,
    LLMResponseError,
    LLMTimeoutError,
)
from app.services.weather_provider import WeatherProviderError
from app.services.weather_rule_engine import AdvisoryMatch

client = TestClient(app)


class MockLLMProvider(LLMProvider):
    """Deterministic mock LLMProvider recording prompt context and returning configurable output."""

    def __init__(self):
        self.call_count = 0
        self.last_prompt = None
        self.last_system_prompt = None
        self.prompt_history = []
        self.next_response = "Dynamic synthesized farmer advisory grounded in provided facts."
        self.raise_exception = None

    def generate(self, prompt: str, system_prompt: str = None) -> str:
        self.call_count += 1
        self.last_prompt = prompt
        self.last_system_prompt = system_prompt
        self.prompt_history.append(prompt)
        if self.raise_exception:
            raise self.raise_exception
        return self.next_response


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
        ],
    )
    with Session(engine) as session:
        yield session


@pytest.fixture
def mock_llm():
    return MockLLMProvider()


@pytest.fixture
def mock_forecast_service():
    return MagicMock(spec=ForecastAdvisoryService)


@pytest.fixture
def base_data(sqlite_session):
    """Seed test village, farmer, and primary arecanut crop."""
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
        area_acres=Decimal("2.50"),
        is_primary=True,
    )
    sqlite_session.add_all([village, farmer, crop, farmer_crop])
    sqlite_session.commit()

    return {
        "village": village,
        "farmer": farmer,
        "crop": crop,
        "farmer_crop": farmer_crop,
    }


def make_weather_result(village, crop, rainfall_48h=Decimal("2.00"), humidity_48h=Decimal("60.00"), advisories=None):
    """Helper creating customizable ForecastAdvisoryResult."""
    ref_time = datetime(2026, 9, 25, 6, 0, tzinfo=timezone.utc)
    metrics = ForecastMetrics(
        reference_time=ref_time,
        rainfall_mm_24h=rainfall_48h / Decimal("2"),
        rainfall_mm_48h=rainfall_48h,
        max_temperature_c_24h=Decimal("30.00"),
        max_temperature_c_48h=Decimal("31.50"),
        avg_humidity_pct_24h=humidity_48h,
        avg_humidity_pct_48h=humidity_48h,
        max_wind_speed_kmh_24h=Decimal("12.00"),
        max_wind_speed_kmh_48h=Decimal("15.00"),
        cloudy_hours_24h=Decimal("4.00"),
        cloudy_hours_48h=Decimal("8.00"),
    )
    return ForecastAdvisoryResult(
        village=village,
        crop=crop,
        forecast_reference_time=ref_time,
        metrics=metrics,
        advisories=advisories or [],
        unsupported_rules=[],
    )


# ==============================================================================
# SCENARIO A: Low rainfall + normal humidity + no disease
# ==============================================================================

def test_scenario_a_low_weather_risk_no_disease(sqlite_session, mock_llm, mock_forecast_service, base_data):
    """Scenario A: Low rainfall (2mm), normal humidity (60%), no disease diagnosis -> Low/no weather risk."""
    farmer = base_data["farmer"]
    village = base_data["village"]
    crop = base_data["crop"]

    mock_forecast_service.get_forecast_advisories.return_value = make_weather_result(
        village, crop, rainfall_48h=Decimal("2.00"), humidity_48h=Decimal("60.00"), advisories=[]
    )
    mock_llm.next_response = "Weather conditions are stable with minimal rainfall expected. Continue routine farm operations."

    service = FarmerAdvisoryService(
        forecast_advisory_service=mock_forecast_service,
        llm_provider=mock_llm,
    )
    app.dependency_overrides[get_db] = lambda: sqlite_session
    app.dependency_overrides[get_farmer_advisory_service] = lambda: service

    try:
        response = client.post(f"/api/v1/farmers/{farmer.id}/advisory", json={"language": "en"})
        assert response.status_code == 200
        data = response.json()

        # Strict evidence checks
        assert data["severity"] in ["INFO", "LOW"]
        assert data["provenance"] == []
        assert data["is_llm_generated"] is True
        assert data["weather_observed_at"] is not None
        assert data["forecast_valid_until"] is not None

        # Validate prompt facts passed to LLM
        prompt = mock_llm.last_prompt
        assert "Expected Rainfall (48h): 2.0 mm" in prompt
        assert "Average Humidity (48h): 60.0%" in prompt
        assert "Crop Disease Diagnosis: No recent crop disease diagnosis recorded." in prompt
        assert "Active Weather Risks & Rules: No active meteorological risk conditions triggered." in prompt
        assert "Farmer: Mahabaleshwar Bhat" in prompt
        assert "Arecanut" in prompt

        # Sources should only contain the weather provider (no fake university/IMD)
        assert "University of Agricultural Sciences, Dharwad" not in data["sources"]
        assert "India Meteorological Department (IMD)" not in data["sources"]
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_farmer_advisory_service, None)


# ==============================================================================
# SCENARIO B: High rainfall + high humidity + no disease
# ==============================================================================

def test_scenario_b_high_weather_risk_no_disease(sqlite_session, mock_llm, mock_forecast_service, base_data):
    """Scenario B: High rainfall (75mm), high humidity (92%), no disease -> High weather risk triggered."""
    farmer = base_data["farmer"]
    village = base_data["village"]
    crop = base_data["crop"]

    high_rain_rule = AdvisoryMatch(
        rule_id=101,
        crop="Arecanut",
        risk_name="Excess Rainfall and Waterlogging Context",
        risk_level="HIGH",
        condition_type="WEATHER_THRESHOLD",
        risk_context="Waterlogging",
        matched_factors=["rainfall_mm_48h >= 50.0 mm"],
        advisory_en="Ensure drainage channels are clear to prevent water stagnation in the root zone.",
        advisory_kn="ಬೇರು ವಲಯದಲ್ಲಿ ನೀರು ನಿಲ್ಲದಂತೆ ಒಳಚರಂಡಿ ಚರಂಡಿಗಳನ್ನು ಸ್ವಚ್ಛಗೊಳಿಸಿ.",
        source_name="ICAR-CPCRI",
        source_reference="Water Management Manual 2024",
    )

    mock_forecast_service.get_forecast_advisories.return_value = make_weather_result(
        village, crop, rainfall_48h=Decimal("75.00"), humidity_48h=Decimal("92.00"), advisories=[high_rain_rule]
    )

    service = FarmerAdvisoryService(
        forecast_advisory_service=mock_forecast_service,
        llm_provider=mock_llm,
    )
    app.dependency_overrides[get_db] = lambda: sqlite_session
    app.dependency_overrides[get_farmer_advisory_service] = lambda: service

    try:
        response = client.post(f"/api/v1/farmers/{farmer.id}/advisory", json={"language": "en"})
        assert response.status_code == 200
        data = response.json()

        assert data["severity"] == "HIGH"
        assert len(data["provenance"]) == 1
        assert data["provenance"][0]["rule_id"] == 101
        assert data["provenance"][0]["risk_name"] == "Excess Rainfall and Waterlogging Context"
        assert "ICAR-CPCRI" in data["sources"]
        assert not any("Disease Detection AI" in s for s in data["sources"])
        assert any("drainage" in act.lower() for act in data["recommended_actions"])

        # Validate prompt facts passed to LLM
        prompt = mock_llm.last_prompt
        assert "Expected Rainfall (48h): 75.0 mm" in prompt
        assert "Average Humidity (48h): 92.0%" in prompt
        assert "Excess Rainfall and Waterlogging Context" in prompt
        assert "Crop Disease Diagnosis: No recent crop disease diagnosis recorded." in prompt
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_farmer_advisory_service, None)


# ==============================================================================
# SCENARIO C: High rainfall + high humidity + Koleroga diagnosis
# ==============================================================================

def test_scenario_c_high_weather_risk_with_disease_diagnosis(sqlite_session, mock_llm, mock_forecast_service, base_data):
    """Scenario C: High rainfall + high humidity + persistent Koleroga diagnosis -> Context includes diagnosis & confidence."""
    farmer = base_data["farmer"]
    village = base_data["village"]
    crop = base_data["crop"]
    farmer_crop = base_data["farmer_crop"]

    # Seed crop report and diagnosis
    report = CropReport(
        id=uuid.uuid4(),
        farmer_crop_id=farmer_crop.id,
        notes="Fallen rotting nuts with water soaked lesions",
        image_filename="koleroga.jpg",
        image_storage_path="farmers/test/crop-reports/koleroga.jpg",
    )
    diagnosis = CropReportDiagnosis(
        id=uuid.uuid4(),
        crop_report_id=report.id,
        crop="arecanut",
        predicted_class="koleroga",
        confidence=0.9420,
        model_name="krushisetu_efficientnet_b0_v2.pth",
        predictions=[{"class_name": "koleroga", "confidence": 0.9420}],
        created_at=datetime(2026, 9, 25, 5, 30, tzinfo=timezone.utc),
    )
    sqlite_session.add_all([report, diagnosis])
    sqlite_session.commit()

    weather_rule = AdvisoryMatch(
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

    mock_forecast_service.get_forecast_advisories.return_value = make_weather_result(
        village, crop, rainfall_48h=Decimal("65.00"), humidity_48h=Decimal("94.00"), advisories=[weather_rule]
    )

    service = FarmerAdvisoryService(
        forecast_advisory_service=mock_forecast_service,
        llm_provider=mock_llm,
    )
    app.dependency_overrides[get_db] = lambda: sqlite_session
    app.dependency_overrides[get_farmer_advisory_service] = lambda: service

    try:
        response = client.post(f"/api/v1/farmers/{farmer.id}/advisory", json={"language": "en"})
        assert response.status_code == 200
        data = response.json()

        assert data["severity"] == "HIGH"
        assert "koleroga" in data["reason"].lower()
        assert "94.2%" in data["reason"]
        assert any("Bordeaux mixture" in act for act in data["recommended_actions"])
        assert any("koleroga" in act.lower() for act in data["recommended_actions"])
        assert "CPCRI" in data["sources"]
        assert "Disease Detection AI (krushisetu_efficientnet_b0_v2.pth)" in data["sources"]

        # Validate prompt facts passed to LLM
        prompt = mock_llm.last_prompt
        assert "koleroga" in prompt
        assert "Confidence: 94.2%" in prompt
        assert "krushisetu_efficientnet_b0_v2.pth" in prompt
        assert "Expected Rainfall (48h): 65.0 mm" in prompt
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_farmer_advisory_service, None)


# ==============================================================================
# SCENARIO D: Same farmer/crop but changed weather context
# ==============================================================================

def test_scenario_d_weather_context_change_updates_advisory(sqlite_session, mock_llm, mock_forecast_service, base_data):
    """Scenario D: Same farmer & crop called twice with differing weather metrics produces dynamic context change."""
    farmer = base_data["farmer"]
    village = base_data["village"]
    crop = base_data["crop"]

    service = FarmerAdvisoryService(
        forecast_advisory_service=mock_forecast_service,
        llm_provider=mock_llm,
    )
    app.dependency_overrides[get_db] = lambda: sqlite_session
    app.dependency_overrides[get_farmer_advisory_service] = lambda: service

    try:
        # Call 1: Dry conditions
        mock_forecast_service.get_forecast_advisories.return_value = make_weather_result(
            village, crop, rainfall_48h=Decimal("1.50"), humidity_48h=Decimal("55.00"), advisories=[]
        )
        resp1 = client.post(f"/api/v1/farmers/{farmer.id}/advisory", json={"language": "en"})
        assert resp1.status_code == 200
        prompt1 = mock_llm.last_prompt

        # Call 2: Monsoon surge
        heavy_rain_rule = AdvisoryMatch(
            rule_id=202,
            crop="Arecanut",
            risk_name="Heavy Rain Warning",
            risk_level="HIGH",
            condition_type="WEATHER_THRESHOLD",
            risk_context="Flooding",
            matched_factors=["rainfall_mm_48h >= 90.0 mm"],
            advisory_en="Postpone fertilizer application and clear channels.",
            advisory_kn="ಗೊಬ್ಬರ ಹಾಕುವುದನ್ನು ಮುಂದೂಡಿ.",
            source_name="UAS Bangalore",
            source_reference="Agromet Advisory",
        )
        mock_forecast_service.get_forecast_advisories.return_value = make_weather_result(
            village, crop, rainfall_48h=Decimal("95.00"), humidity_48h=Decimal("96.00"), advisories=[heavy_rain_rule]
        )
        resp2 = client.post(f"/api/v1/farmers/{farmer.id}/advisory", json={"language": "en"})
        assert resp2.status_code == 200
        prompt2 = mock_llm.last_prompt

        # The factual context passed to the LLM must have changed dynamically
        assert prompt1 != prompt2
        assert "1.5 mm" in prompt1
        assert "95.0 mm" in prompt2
        assert resp1.json()["severity"] != resp2.json()["severity"]
        assert resp2.json()["severity"] == "HIGH"
        assert len(resp2.json()["provenance"]) == 1
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_farmer_advisory_service, None)


# ==============================================================================
# SCENARIO E: Same weather but newly created disease diagnosis
# ==============================================================================

def test_scenario_e_new_disease_diagnosis_updates_advisory(sqlite_session, mock_llm, mock_forecast_service, base_data):
    """Scenario E: Same weather, but adding a new disease diagnosis dynamically updates the advisory context."""
    farmer = base_data["farmer"]
    village = base_data["village"]
    crop = base_data["crop"]
    farmer_crop = base_data["farmer_crop"]

    mock_forecast_service.get_forecast_advisories.return_value = make_weather_result(
        village, crop, rainfall_48h=Decimal("10.00"), humidity_48h=Decimal("70.00"), advisories=[]
    )

    service = FarmerAdvisoryService(
        forecast_advisory_service=mock_forecast_service,
        llm_provider=mock_llm,
    )
    app.dependency_overrides[get_db] = lambda: sqlite_session
    app.dependency_overrides[get_farmer_advisory_service] = lambda: service

    try:
        # Call 1: Without disease diagnosis
        resp1 = client.post(f"/api/v1/farmers/{farmer.id}/advisory", json={"language": "en"})
        assert resp1.status_code == 200
        assert "No recent crop disease diagnosis recorded." in mock_llm.last_prompt

        # Add new disease diagnosis in DB
        report = CropReport(
            id=uuid.uuid4(),
            farmer_crop_id=farmer_crop.id,
            notes="Observed bleeding patches on stem",
            image_filename="stem_bleeding.jpg",
            image_storage_path="farmers/test/stem.jpg",
        )
        diagnosis = CropReportDiagnosis(
            id=uuid.uuid4(),
            crop_report_id=report.id,
            crop="arecanut",
            predicted_class="anabe_disease",
            confidence=0.8900,
            model_name="krushisetu_efficientnet_b0_v2.pth",
            predictions=[{"class_name": "anabe_disease", "confidence": 0.8900}],
            created_at=datetime.now(timezone.utc),
        )
        sqlite_session.add_all([report, diagnosis])
        sqlite_session.commit()

        # Call 2: Context dynamically reflects newly saved diagnosis
        resp2 = client.post(f"/api/v1/farmers/{farmer.id}/advisory", json={"language": "en"})
        assert resp2.status_code == 200
        data2 = resp2.json()

        assert "anabe_disease" in mock_llm.last_prompt
        assert "Confidence: 89.0%" in mock_llm.last_prompt
        assert "anabe disease" in data2["reason"].lower()
        assert "Disease Detection AI (krushisetu_efficientnet_b0_v2.pth)" in data2["sources"]
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_farmer_advisory_service, None)


# ==============================================================================
# SCENARIO F: No current weather data available
# ==============================================================================

def test_scenario_f_weather_data_unavailable_no_fabrication(sqlite_session, mock_llm, mock_forecast_service, base_data):
    """Scenario F: Weather provider unavailable -> does not invent fake metrics, returns uncertainty guidance."""
    farmer = base_data["farmer"]
    crop = base_data["crop"]

    mock_forecast_service.get_forecast_advisories.side_effect = WeatherProviderError("Weather provider API down.")

    service = FarmerAdvisoryService(
        forecast_advisory_service=mock_forecast_service,
        llm_provider=mock_llm,
    )
    app.dependency_overrides[get_db] = lambda: sqlite_session
    app.dependency_overrides[get_farmer_advisory_service] = lambda: service

    try:
        response = client.post(f"/api/v1/farmers/{farmer.id}/advisory", json={"language": "en"})
        assert response.status_code == 200
        data = response.json()

        # Must not fabricate fake weather
        assert data["weather_observed_at"] is None
        assert data["forecast_valid_until"] is None
        assert "8.04 mm" not in mock_llm.last_prompt
        assert "Weather forecast data currently unavailable for this location." in mock_llm.last_prompt
        assert "Weather forecast data currently unavailable" in data["reason"]
        assert data["provenance"] == []
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_farmer_advisory_service, None)


# ==============================================================================
# SCENARIO G: Groq / LLM unavailable
# ==============================================================================

@pytest.mark.parametrize(
    "error_instance",
    [
        LLMConnectionError("Cannot connect to Groq endpoint"),
        LLMTimeoutError("Groq call timed out after 300s"),
        LLMResponseError("429 Too Many Requests"),
        LLMResponseError("503 Service Unavailable"),
    ],
)
def test_scenario_g_groq_failures_fallback_cleanly(sqlite_session, mock_llm, mock_forecast_service, base_data, error_instance):
    """Scenario G: Network or API failure to Groq gracefully returns deterministic fallback advisory."""
    farmer = base_data["farmer"]
    village = base_data["village"]
    crop = base_data["crop"]

    mock_forecast_service.get_forecast_advisories.return_value = make_weather_result(
        village, crop, rainfall_48h=Decimal("45.00"), humidity_48h=Decimal("85.00"), advisories=[]
    )
    mock_llm.raise_exception = error_instance

    service = FarmerAdvisoryService(
        forecast_advisory_service=mock_forecast_service,
        llm_provider=mock_llm,
    )
    app.dependency_overrides[get_db] = lambda: sqlite_session
    app.dependency_overrides[get_farmer_advisory_service] = lambda: service

    try:
        response = client.post(f"/api/v1/farmers/{farmer.id}/advisory", json={"language": "en"})
        assert response.status_code == 200
        data = response.json()

        assert data["is_llm_generated"] is False
        assert len(data["summary"]) > 0
        assert data["language"] == "en"
        assert data["severity"] in ["INFO", "LOW"]
        assert len(data["recommended_actions"]) >= 1
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_farmer_advisory_service, None)


# ==============================================================================
# SCENARIO H: LLM returns fabricated source names
# ==============================================================================

def test_scenario_h_llm_fabricated_sources_rejected(sqlite_session, mock_llm, mock_forecast_service, base_data):
    """Scenario H: When LLM outputs hallucinated sources, application does not trust or return them."""
    farmer = base_data["farmer"]
    village = base_data["village"]
    crop = base_data["crop"]

    match_rule = AdvisoryMatch(
        rule_id=5,
        crop="Arecanut",
        risk_name="High Humidity Alert",
        risk_level="MODERATE",
        condition_type="WEATHER_THRESHOLD",
        risk_context="Humidity",
        matched_factors=["humidity >= 80%"],
        advisory_en="Monitor palms for fungus.",
        advisory_kn="ಶಿಲೀಂಧ್ರ ಬಾಧೆಯನ್ನು ಗಮನಿಸಿ.",
        source_name="CPCRI",
        source_reference="Advisory Sheet",
    )
    mock_forecast_service.get_forecast_advisories.return_value = make_weather_result(
        village, crop, rainfall_48h=Decimal("15.00"), humidity_48h=Decimal("85.00"), advisories=[match_rule]
    )

    # LLM hallucinates fake institutions in its text output
    mock_llm.next_response = (
        "High humidity conditions detected. Monitor palms closely for fungal growth.\n"
        "Sources: University of California, Mars Meteorological Institute, Global Agritech Corp"
    )

    service = FarmerAdvisoryService(
        forecast_advisory_service=mock_forecast_service,
        llm_provider=mock_llm,
    )
    app.dependency_overrides[get_db] = lambda: sqlite_session
    app.dependency_overrides[get_farmer_advisory_service] = lambda: service

    try:
        response = client.post(f"/api/v1/farmers/{farmer.id}/advisory", json={"language": "en"})
        assert response.status_code == 200
        data = response.json()

        # The application must NOT adopt the LLM's fabricated sources
        assert "University of California" not in data["sources"]
        assert "Mars Meteorological Institute" not in data["sources"]
        assert "Global Agritech Corp" not in data["sources"]

        # Only legitimate evidence-based sources are returned
        assert "CPCRI" in data["sources"]
        assert "Sources:" not in data["summary"]
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_farmer_advisory_service, None)
