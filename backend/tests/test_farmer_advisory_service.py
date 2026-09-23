"""Unit and API tests for FarmerAdvisoryService and farmer presentation endpoints."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.api.v1.weather import get_farmer_advisory_service, get_forecast_advisory_service
from app.main import app
from app.models.crop import Crop
from app.models.village import Village
from app.schemas.weather import (
    FarmerAdvisoryItem,
    FarmerAdvisoryResponse,
    ForecastData,
    ForecastMetrics,
)
from app.services.farmer_advisory_service import FarmerAdvisoryService
from app.services.forecast_advisory_service import (
    ForecastAdvisoryResult,
    ForecastAdvisoryService,
    UnsupportedRule,
)
from app.services.weather_forecast_service import WeatherForecastService
from app.services.weather_provider import ForecastProvider, MockWeatherProvider
from app.services.weather_rule_engine import AdvisoryMatch

client = TestClient(app)


@pytest.fixture
def sample_village():
    return Village(
        id="V001",
        name="Mangaluru",
        district="Dakshina Kannada",
        state="Karnataka",
        zone="Coastal",
        latitude=12.9141,
        longitude=74.8560,
    )


@pytest.fixture
def sample_crop():
    return Crop(
        id=1,
        code="arecanut",
        name_en="Arecanut",
        name_kn="ಅಡಿಕೆ",
    )


@pytest.fixture
def sample_forecast_metrics():
    return ForecastMetrics(
        reference_time=datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc),
        rainfall_mm_24h=Decimal("12.50"),
        rainfall_mm_48h=Decimal("35.00"),
        max_temperature_c_24h=Decimal("30.00"),
        max_temperature_c_48h=Decimal("31.50"),
        avg_humidity_pct_24h=Decimal("82.00"),
        avg_humidity_pct_48h=Decimal("84.50"),
        max_wind_speed_kmh_24h=Decimal("15.00"),
        max_wind_speed_kmh_48h=Decimal("18.00"),
        cloudy_hours_24h=Decimal("14.00"),
        cloudy_hours_48h=Decimal("28.00"),
    )


# ==============================================================================
# 1. No active advisory
# ==============================================================================
def test_no_active_advisory(sample_village, sample_crop, sample_forecast_metrics):
    """Test 1: When no rules match, status is 'no_active_advisory' with verified text."""
    result = ForecastAdvisoryResult(
        village=sample_village,
        crop=sample_crop,
        forecast_reference_time=sample_forecast_metrics.reference_time,
        metrics=sample_forecast_metrics,
        advisories=[],
        unsupported_rules=[
            UnsupportedRule(
                rule_id=1,
                risk_name="Koleroga Weather Risk Context",
                reason="Requires cloudy_days_streak, which is not available from forecast metrics.",
            )
        ],
    )

    service = FarmerAdvisoryService()
    resp = service.format_result(result, language="en")

    assert resp.status == "no_active_advisory"
    assert resp.message_en == "No forecast-based weather advisory is currently triggered."
    assert resp.message_kn == "ಪ್ರಸ್ತುತ ಯಾವುದೇ ಮುನ್ಸೂಚನೆ ಆಧಾರಿತ ಹವಾಮಾನ ಸಲಹೆ ಸಕ್ರಿಯವಾಗಿಲ್ಲ."
    assert resp.advisories == []
    assert len(resp.unsupported_rules) == 1


# ==============================================================================
# 2. One active forecast advisory
# ==============================================================================
def test_one_active_forecast_advisory(sample_village, sample_crop, sample_forecast_metrics):
    """Test 2: A single active rule produces status 'advisory_active' with one item."""
    match = AdvisoryMatch(
        rule_id=3,
        crop="Arecanut",
        risk_name="Heavy Rainfall Waterlogging Risk Context",
        risk_level="HIGH",
        condition_type="WEATHER_THRESHOLD",
        risk_context="Waterlogging",
        matched_factors=["extreme rainfall accumulation (>100 mm/48h)"],
        advisory_en="Provide proper drainage channels in the plantation.",
        advisory_kn="ತೋಟದಲ್ಲಿ ಸೂಕ್ತ ನೀರುಗಾಲುವೆಗಳನ್ನು ನಿರ್ಮಿಸಿ ನೀರು ನಿಲ್ಲದಂತೆ ನೋಡಿಕೊಳ್ಳಿ.",
        source_name="CPCRI",
        source_reference="Package of Practices",
    )

    result = ForecastAdvisoryResult(
        village=sample_village,
        crop=sample_crop,
        forecast_reference_time=sample_forecast_metrics.reference_time,
        metrics=sample_forecast_metrics,
        advisories=[match],
        unsupported_rules=[],
    )

    service = FarmerAdvisoryService()
    resp = service.format_result(result, language="en")

    assert resp.status == "advisory_active"
    assert len(resp.advisories) == 1
    item = resp.advisories[0]
    assert item.risk_name == "Heavy Rainfall Waterlogging Risk Context"
    assert item.risk_level == "HIGH"
    assert item.title_en == "Heavy Rainfall Waterlogging Risk Context"
    assert item.message_en == "Provide proper drainage channels in the plantation."
    assert item.message_kn == "ತೋಟದಲ್ಲಿ ಸೂಕ್ತ ನೀರುಗಾಲುವೆಗಳನ್ನು ನಿರ್ಮಿಸಿ ನೀರು ನಿಲ್ಲದಂತೆ ನೋಡಿಕೊಳ್ಳಿ."


# ==============================================================================
# 3. Multiple active advisories
# ==============================================================================
def test_multiple_active_advisories(sample_village, sample_crop, sample_forecast_metrics):
    """Test 3: Multiple active rules are all preserved and formatted."""
    match1 = AdvisoryMatch(
        rule_id=3,
        crop="Arecanut",
        risk_name="Heavy Rainfall Waterlogging Risk Context",
        risk_level="HIGH",
        condition_type="WEATHER_THRESHOLD",
        risk_context="Waterlogging",
        matched_factors=["extreme rainfall accumulation (>100 mm/48h)"],
        advisory_en="Drain excess water.",
        advisory_kn="ಹೆಚ್ಚುವರಿ ನೀರನ್ನು ಹೊರಹಾಕಿ.",
        source_name="CPCRI",
        source_reference="Ref 1",
    )
    match2 = AdvisoryMatch(
        rule_id=4,
        crop="Arecanut",
        risk_name="Post-Monsoon Dry Operational Window",
        risk_level="LOW",
        condition_type="WEATHER_THRESHOLD",
        risk_context="Dry Window",
        matched_factors=["negligible rainfall (<5 mm/48h)"],
        advisory_en="Favorable window for fertilizer application.",
        advisory_kn="ಗೊಬ್ಬರ ಹಾಕಲು ಸೂಕ್ತ ಸಮಯ.",
        source_name="CPCRI",
        source_reference="Ref 2",
    )

    result = ForecastAdvisoryResult(
        village=sample_village,
        crop=sample_crop,
        forecast_reference_time=sample_forecast_metrics.reference_time,
        metrics=sample_forecast_metrics,
        advisories=[match1, match2],
        unsupported_rules=[],
    )

    service = FarmerAdvisoryService()
    resp = service.format_result(result, language="en")

    assert resp.status == "advisory_active"
    assert len(resp.advisories) == 2
    assert resp.advisories[0].risk_name == "Heavy Rainfall Waterlogging Risk Context"
    assert resp.advisories[1].risk_name == "Post-Monsoon Dry Operational Window"


# ==============================================================================
# 4. English language selection
# ==============================================================================
def test_english_language_selection():
    """Test 4: Requesting language=en via API returns language='en'."""
    response = client.get(
        "/api/v1/weather/farmer-advisory",
        params={"village_id": "V001", "crop": "arecanut", "language": "en"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "en"


# ==============================================================================
# 5. Kannada language selection
# ==============================================================================
def test_kannada_language_selection():
    """Test 5: Requesting language=kn via API returns language='kn'."""
    response = client.get(
        "/api/v1/weather/farmer-advisory",
        params={"village_id": "V001", "crop": "arecanut", "language": "kn"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["language"] == "kn"


# ==============================================================================
# 6. Unsupported language -> 422
# ==============================================================================
def test_unsupported_language_422():
    """Test 6: Requesting unsupported language returns HTTP 422 Unprocessable Entity."""
    response = client.get(
        "/api/v1/weather/farmer-advisory",
        params={"village_id": "V001", "crop": "arecanut", "language": "fr"},
    )
    assert response.status_code == 422


# ==============================================================================
# 7. Existing advisory text is preserved exactly
# ==============================================================================
def test_advisory_text_preserved_exactly(sample_village, sample_crop, sample_forecast_metrics):
    """Test 7: English and Kannada text strings are preserved verbatim without AI alteration."""
    raw_en = "Exact text: Apply 1% Bordeaux mixture on bunches before monsoon."
    raw_kn = "ನಿಖರ ಪಠ್ಯ: ಮುಂಗಾರು ಪೂರ್ವದಲ್ಲಿ ಶೇ 1ರ ಬೋರ್ಡೋ ಮಿಶ್ರಣ ಸಿಂಪಡಿಸಿ."

    match = AdvisoryMatch(
        rule_id=1,
        crop="Arecanut",
        risk_name="Koleroga Context",
        risk_level="HIGH",
        condition_type="WEATHER_THRESHOLD",
        risk_context="Koleroga",
        matched_factors=["factor1"],
        advisory_en=raw_en,
        advisory_kn=raw_kn,
        source_name="CPCRI",
        source_reference="Ref A",
    )

    result = ForecastAdvisoryResult(
        village=sample_village,
        crop=sample_crop,
        forecast_reference_time=sample_forecast_metrics.reference_time,
        metrics=sample_forecast_metrics,
        advisories=[match],
        unsupported_rules=[],
    )

    service = FarmerAdvisoryService()
    resp = service.format_result(result, language="en")

    assert resp.advisories[0].message_en == raw_en
    assert resp.advisories[0].message_kn == raw_kn


# ==============================================================================
# 8. Risk level is preserved exactly
# ==============================================================================
def test_risk_level_preserved_exactly(sample_village, sample_crop, sample_forecast_metrics):
    """Test 8: Risk levels ('LOW', 'MODERATE', 'HIGH') are passed through unchanged."""
    for level in ["LOW", "MODERATE", "HIGH"]:
        match = AdvisoryMatch(
            rule_id=10,
            crop="Arecanut",
            risk_name="Test Risk",
            risk_level=level,
            condition_type="WEATHER_THRESHOLD",
            risk_context=None,
            matched_factors=[],
            advisory_en="Advice",
            advisory_kn="ಸಲಹೆ",
            source_name="Source",
            source_reference=None,
        )
        result = ForecastAdvisoryResult(
            village=sample_village,
            crop=sample_crop,
            forecast_reference_time=sample_forecast_metrics.reference_time,
            metrics=sample_forecast_metrics,
            advisories=[match],
            unsupported_rules=[],
        )
        resp = FarmerAdvisoryService().format_result(result)
        assert resp.advisories[0].risk_level == level


# ==============================================================================
# 9. Matched factors are preserved
# ==============================================================================
def test_matched_factors_preserved(sample_village, sample_crop, sample_forecast_metrics):
    """Test 9: Specific rule condition factors are forwarded directly."""
    factors = ["rainfall_mm_48h >= 100.0", "temp_max_c >= 28.0"]
    match = AdvisoryMatch(
        rule_id=10,
        crop="Arecanut",
        risk_name="Waterlogging",
        risk_level="HIGH",
        condition_type="WEATHER_THRESHOLD",
        risk_context=None,
        matched_factors=factors,
        advisory_en="Advice",
        advisory_kn="ಸಲಹೆ",
        source_name="Source",
        source_reference=None,
    )
    result = ForecastAdvisoryResult(
        village=sample_village,
        crop=sample_crop,
        forecast_reference_time=sample_forecast_metrics.reference_time,
        metrics=sample_forecast_metrics,
        advisories=[match],
        unsupported_rules=[],
    )
    resp = FarmerAdvisoryService().format_result(result)
    assert resp.advisories[0].matched_factors == factors


# ==============================================================================
# 10. Unsupported rules remain separate
# ==============================================================================
def test_unsupported_rules_remain_separate(sample_village, sample_crop, sample_forecast_metrics):
    """Test 10: Unsupported rules appear exclusively in unsupported_rules list."""
    unsupported = [
        UnsupportedRule(
            rule_id=1,
            risk_name="Koleroga Weather Risk Context",
            reason="Requires cloudy_days_streak, which is not available from forecast metrics.",
        )
    ]
    result = ForecastAdvisoryResult(
        village=sample_village,
        crop=sample_crop,
        forecast_reference_time=sample_forecast_metrics.reference_time,
        metrics=sample_forecast_metrics,
        advisories=[],
        unsupported_rules=unsupported,
    )
    resp = FarmerAdvisoryService().format_result(result)
    assert len(resp.advisories) == 0
    assert len(resp.unsupported_rules) == 1
    assert resp.unsupported_rules[0].rule_id == 1
    assert "cloudy_days_streak" in resp.unsupported_rules[0].reason


# ==============================================================================
# 11. Forecast advisory type is 'forecast'
# ==============================================================================
def test_advisory_type_is_forecast(sample_village, sample_crop, sample_forecast_metrics):
    """Test 11: Each advisory item explicitly declares advisory_type='forecast'."""
    match = AdvisoryMatch(
        rule_id=1,
        crop="Arecanut",
        risk_name="Risk",
        risk_level="LOW",
        condition_type="WEATHER_THRESHOLD",
        risk_context=None,
        matched_factors=[],
        advisory_en="Advice",
        advisory_kn="ಸಲಹೆ",
        source_name="Source",
        source_reference=None,
    )
    result = ForecastAdvisoryResult(
        village=sample_village,
        crop=sample_crop,
        forecast_reference_time=sample_forecast_metrics.reference_time,
        metrics=sample_forecast_metrics,
        advisories=[match],
        unsupported_rules=[],
    )
    resp = FarmerAdvisoryService().format_result(result)
    assert resp.advisories[0].advisory_type == "forecast"


# ==============================================================================
# 12. Missing Kannada text is not fabricated
# ==============================================================================
def test_missing_kannada_text_not_fabricated(sample_village, sample_crop, sample_forecast_metrics):
    """Test 12: If advisory_kn is None in the database, title_kn/message_kn remains None."""
    match = AdvisoryMatch(
        rule_id=1,
        crop="Arecanut",
        risk_name="Risk",
        risk_level="LOW",
        condition_type="WEATHER_THRESHOLD",
        risk_context=None,
        matched_factors=[],
        advisory_en="Advice only in English",
        advisory_kn=None,
        source_name="Source",
        source_reference=None,
    )
    result = ForecastAdvisoryResult(
        village=sample_village,
        crop=sample_crop,
        forecast_reference_time=sample_forecast_metrics.reference_time,
        metrics=sample_forecast_metrics,
        advisories=[match],
        unsupported_rules=[],
    )
    resp = FarmerAdvisoryService().format_result(result, language="kn")
    assert resp.advisories[0].message_kn is None
    assert resp.advisories[0].title_kn is None


# ==============================================================================
# 13. Forecast context is preserved
# ==============================================================================
def test_forecast_context_preserved(sample_village, sample_crop, sample_forecast_metrics):
    """Test 13: Numerical forecast context values are cleanly attached."""
    result = ForecastAdvisoryResult(
        village=sample_village,
        crop=sample_crop,
        forecast_reference_time=sample_forecast_metrics.reference_time,
        metrics=sample_forecast_metrics,
        advisories=[],
        unsupported_rules=[],
    )
    resp = FarmerAdvisoryService().format_result(result)
    assert resp.context.rainfall_mm_24h == Decimal("12.50")
    assert resp.context.rainfall_mm_48h == Decimal("35.00")
    assert resp.context.max_temperature_c_24h == Decimal("30.00")
    assert resp.context.max_temperature_c_48h == Decimal("31.50")
    assert resp.context.avg_humidity_pct_24h == Decimal("82.00")
    assert resp.context.avg_humidity_pct_48h == Decimal("84.50")
    assert resp.context.cloudy_hours_24h == Decimal("14.00")
    assert resp.context.cloudy_hours_48h == Decimal("28.00")


# ==============================================================================
# 14. Existing historical advisory behavior remains unchanged
# ==============================================================================
def test_historical_advisory_behavior_unchanged():
    """Test 14: Historical observation advisory endpoint GET /api/v1/weather/advisories continues unaffected."""
    response = client.get("/api/v1/weather/advisories?village_id=V001&crop=arecanut")
    assert response.status_code == 200
    data = response.json()
    assert data["village_id"] == "V001"
    assert data["crop"] == "Arecanut"
    assert "metrics" in data
    assert "cloudy_days_streak" in data["metrics"]
    assert "advisories" in data
    assert "context" not in data
