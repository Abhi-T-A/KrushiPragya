"""Unit and API tests for advisory explanation and provenance layer."""

from datetime import datetime, timezone
from decimal import Decimal
import pytest
from fastapi.testclient import TestClient

from app.api.v1.weather import get_farmer_advisory_service
from app.main import app
from app.models.crop import Crop
from app.models.village import Village
from app.schemas.weather import (
    AdvisoryExplanation,
    AdvisoryProvenance,
    FarmerAdvisoryResponse,
    ForecastAdvisoryContext,
    ForecastMetrics,
)
from app.services.farmer_advisory_service import FarmerAdvisoryService, build_explanations
from app.services.forecast_advisory_service import (
    ForecastAdvisoryResult,
    ForecastAdvisoryService,
    UnsupportedRule,
)
from app.services.weather_forecast_service import WeatherForecastService
from app.services.weather_provider import MockWeatherProvider
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
def sample_context():
    return ForecastAdvisoryContext(
        rainfall_mm_24h=Decimal("15.00"),
        rainfall_mm_48h=Decimal("112.40"),
        max_temperature_c_24h=Decimal("30.00"),
        max_temperature_c_48h=Decimal("29.40"),
        avg_humidity_pct_24h=Decimal("80.00"),
        avg_humidity_pct_48h=Decimal("86.50"),
        cloudy_hours_24h=Decimal("12.00"),
        cloudy_hours_48h=Decimal("24.00"),
    )


def _make_match(
    rule_id: int = 10,
    risk_name: str = "Test Risk",
    risk_level: str = "HIGH",
    condition_config: dict | None = None,
    source_name: str = "CPCRI",
    source_reference: str | None = "Package of Practices",
) -> AdvisoryMatch:
    return AdvisoryMatch(
        rule_id=rule_id,
        crop="Arecanut",
        risk_name=risk_name,
        risk_level=risk_level,
        condition_type="WEATHER_THRESHOLD",
        risk_context="Test",
        matched_factors=["factor1"],
        advisory_en="Test advisory guidance",
        advisory_kn="ಸಲಹೆ",
        source_name=source_name,
        source_reference=source_reference,
        condition_config=condition_config or {},
    )


# ==============================================================================
# 1. Rainfall minimum threshold explanation
# ==============================================================================
def test_rainfall_min_threshold_explanation(sample_context):
    """Test 1: min_rainfall_mm_48h generates correct operator '>=', unit 'mm', and threshold."""
    match = _make_match(condition_config={"min_rainfall_mm_48h": 100.0})
    explanations = build_explanations(match, sample_context)

    assert len(explanations) == 1
    exp = explanations[0]
    assert exp.metric_name == "rainfall_mm_48h"
    assert exp.threshold_operator == ">="
    assert exp.threshold_value == Decimal("100.0")
    assert exp.actual_value == Decimal("112.40")
    assert exp.unit == "mm"
    assert "Expected rainfall is 112.40 mm over 48 hours, meeting the advisory threshold of 100.0 mm." in exp.explanation_en


# ==============================================================================
# 2. Rainfall maximum threshold explanation
# ==============================================================================
def test_rainfall_max_threshold_explanation(sample_context):
    """Test 2: max_rainfall_mm_48h generates correct operator '<=', unit 'mm'."""
    match = _make_match(condition_config={"max_rainfall_mm_48h": 5.0})
    context = ForecastAdvisoryContext(rainfall_mm_48h=Decimal("3.20"))
    explanations = build_explanations(match, context)

    assert len(explanations) == 1
    exp = explanations[0]
    assert exp.metric_name == "rainfall_mm_48h"
    assert exp.threshold_operator == "<="
    assert exp.threshold_value == Decimal("5.0")
    assert exp.actual_value == Decimal("3.20")
    assert exp.unit == "mm"
    assert "Expected rainfall is 3.20 mm over 48 hours, which is within the advisory limit of 5.0 mm." in exp.explanation_en


# ==============================================================================
# 3. Humidity minimum threshold explanation
# ==============================================================================
def test_humidity_min_threshold_explanation(sample_context):
    """Test 3: min_humidity_pct generates correct operator '>=', unit '%'."""
    match = _make_match(condition_config={"min_humidity_pct": 80.0})
    explanations = build_explanations(match, sample_context)

    assert len(explanations) == 1
    exp = explanations[0]
    assert exp.metric_name == "avg_humidity_pct_48h"
    assert exp.threshold_operator == ">="
    assert exp.threshold_value == Decimal("80.0")
    assert exp.actual_value == Decimal("86.50")
    assert exp.unit == "%"
    assert "Expected average humidity is 86.50% over 48 hours, meeting the advisory threshold of 80.0%." in exp.explanation_en


# ==============================================================================
# 4. Humidity maximum threshold explanation
# ==============================================================================
def test_humidity_max_threshold_explanation(sample_context):
    """Test 4: max_humidity_pct generates correct operator '<=', unit '%'."""
    match = _make_match(condition_config={"max_humidity_pct": 72.0})
    context = ForecastAdvisoryContext(avg_humidity_pct_48h=Decimal("68.50"))
    explanations = build_explanations(match, context)

    assert len(explanations) == 1
    exp = explanations[0]
    assert exp.metric_name == "avg_humidity_pct_48h"
    assert exp.threshold_operator == "<="
    assert exp.threshold_value == Decimal("72.0")
    assert exp.actual_value == Decimal("68.50")
    assert exp.unit == "%"
    assert "within the advisory limit of 72.0%" in exp.explanation_en


# ==============================================================================
# 5. Temperature minimum threshold explanation
# ==============================================================================
def test_temperature_min_threshold_explanation(sample_context):
    """Test 5: min_temp_max_c generates correct operator '>=', unit '°C'."""
    match = _make_match(condition_config={"min_temp_max_c": 28.0})
    explanations = build_explanations(match, sample_context)

    assert len(explanations) == 1
    exp = explanations[0]
    assert exp.metric_name == "max_temperature_c_48h"
    assert exp.threshold_operator == ">="
    assert exp.threshold_value == Decimal("28.0")
    assert exp.actual_value == Decimal("29.40")
    assert exp.unit == "°C"
    assert "Expected maximum temperature is 29.40 °C over 48 hours, meeting the advisory threshold of 28.0 °C." in exp.explanation_en


# ==============================================================================
# 6. Multiple-condition rule produces multiple explanations
# ==============================================================================
def test_multiple_conditions_produce_multiple_explanations():
    """Test 6: Rule 4 (Dry Window) with 3 conditions produces exactly 3 distinct explanations."""
    config = {
        "max_rainfall_mm_48h": 5.0,
        "max_humidity_pct": 72.0,
        "min_temp_max_c": 28.0,
    }
    match = _make_match(condition_config=config)
    context = ForecastAdvisoryContext(
        rainfall_mm_48h=Decimal("2.50"),
        avg_humidity_pct_48h=Decimal("65.00"),
        max_temperature_c_48h=Decimal("30.20"),
    )
    explanations = build_explanations(match, context)

    assert len(explanations) == 3
    metric_names = [e.metric_name for e in explanations]
    assert "rainfall_mm_48h" in metric_names
    assert "avg_humidity_pct_48h" in metric_names
    assert "max_temperature_c_48h" in metric_names


# ==============================================================================
# 7. Actual forecast value is preserved
# ==============================================================================
def test_actual_forecast_value_preserved(sample_context):
    """Test 7: Actual value in explanation exactly matches context value."""
    match = _make_match(condition_config={"min_rainfall_mm_48h": 50.0})
    explanations = build_explanations(match, sample_context)
    assert explanations[0].actual_value == sample_context.rainfall_mm_48h


# ==============================================================================
# 8. Actual threshold comes from condition_config
# ==============================================================================
def test_threshold_value_comes_from_config(sample_context):
    """Test 8: Threshold value is dynamically read from rule config, never hard-coded."""
    for thresh in [25.0, 75.5, 120.0]:
        match = _make_match(condition_config={"min_rainfall_mm_48h": thresh})
        explanations = build_explanations(match, sample_context)
        assert explanations[0].threshold_value == Decimal(str(thresh))


# ==============================================================================
# 9. Correct comparison operator is used
# ==============================================================================
def test_correct_comparison_operators(sample_context):
    """Test 9: 'min_' generates '>=' while 'max_' generates '<='."""
    m_min = _make_match(condition_config={"min_rainfall_mm_48h": 10.0})
    m_max = _make_match(condition_config={"max_rainfall_mm_48h": 10.0})

    assert build_explanations(m_min, sample_context)[0].threshold_operator == ">="
    assert build_explanations(m_max, sample_context)[0].threshold_operator == "<="


# ==============================================================================
# 10. Unit is correct
# ==============================================================================
def test_correct_units(sample_context):
    """Test 10: Units are correctly mapped ('mm', '%', '°C')."""
    m_rain = _make_match(condition_config={"min_rainfall_mm_48h": 10.0})
    m_hum = _make_match(condition_config={"min_humidity_pct": 80.0})
    m_temp = _make_match(condition_config={"min_temp_max_c": 28.0})

    assert build_explanations(m_rain, sample_context)[0].unit == "mm"
    assert build_explanations(m_hum, sample_context)[0].unit == "%"
    assert build_explanations(m_temp, sample_context)[0].unit == "°C"


# ==============================================================================
# 11. Unsupported cloudy_days_streak gets no explanation
# ==============================================================================
def test_unsupported_cloudy_days_streak_no_explanation(sample_context):
    """Test 11: min_cloudy_days_streak is never converted to an explanation."""
    match = _make_match(condition_config={"min_cloudy_days_streak": 3})
    explanations = build_explanations(match, sample_context)
    assert len(explanations) == 0


# ==============================================================================
# 12. Provenance preserves rule ID
# ==============================================================================
def test_provenance_preserves_rule_id(sample_village, sample_crop, sample_context):
    """Test 12: AdvisoryProvenance carries the authoritative rule_id."""
    match = _make_match(rule_id=42)
    metrics = ForecastMetrics(
        reference_time=datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc),
        rainfall_mm_48h=Decimal("112.40"),
    )
    result = ForecastAdvisoryResult(
        village=sample_village,
        crop=sample_crop,
        forecast_reference_time=metrics.reference_time,
        metrics=metrics,
        advisories=[match],
        unsupported_rules=[],
    )

    resp = FarmerAdvisoryService().format_result(result)
    assert resp.advisories[0].provenance is not None
    assert resp.advisories[0].provenance.rule_id == 42


# ==============================================================================
# 13. Provenance preserves source name
# ==============================================================================
def test_provenance_preserves_source_name(sample_village, sample_crop):
    """Test 13: Source institution name is preserved in provenance."""
    match = _make_match(source_name="ICAR-CPCRI Kasaragod")
    metrics = ForecastMetrics(reference_time=datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc))
    result = ForecastAdvisoryResult(
        village=sample_village,
        crop=sample_crop,
        forecast_reference_time=metrics.reference_time,
        metrics=metrics,
        advisories=[match],
        unsupported_rules=[],
    )
    resp = FarmerAdvisoryService().format_result(result)
    assert resp.advisories[0].provenance.source_name == "ICAR-CPCRI Kasaragod"


# ==============================================================================
# 14. Provenance preserves source reference
# ==============================================================================
def test_provenance_preserves_source_reference(sample_village, sample_crop):
    """Test 14: Source reference document is preserved in provenance."""
    match = _make_match(source_reference="Arecanut Disease Protocol 2024")
    metrics = ForecastMetrics(reference_time=datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc))
    result = ForecastAdvisoryResult(
        village=sample_village,
        crop=sample_crop,
        forecast_reference_time=metrics.reference_time,
        metrics=metrics,
        advisories=[match],
        unsupported_rules=[],
    )
    resp = FarmerAdvisoryService().format_result(result)
    assert resp.advisories[0].provenance.source_reference == "Arecanut Disease Protocol 2024"


# ==============================================================================
# 15. No active advisory produces empty explanations
# ==============================================================================
def test_no_active_advisory_empty_explanations(sample_village, sample_crop):
    """Test 15: When status is no_active_advisory, advisories and explanations are empty."""
    metrics = ForecastMetrics(reference_time=datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc))
    result = ForecastAdvisoryResult(
        village=sample_village,
        crop=sample_crop,
        forecast_reference_time=metrics.reference_time,
        metrics=metrics,
        advisories=[],
        unsupported_rules=[],
    )
    resp = FarmerAdvisoryService().format_result(result)
    assert resp.status == "no_active_advisory"
    assert resp.advisories == []


# ==============================================================================
# 16. Kannada explanation is not fabricated
# ==============================================================================
def test_kannada_explanation_not_fabricated(sample_context):
    """Test 16: explanation_kn remains None rather than using machine translation."""
    match = _make_match(condition_config={"min_rainfall_mm_48h": 100.0})
    explanations = build_explanations(match, sample_context)
    assert explanations[0].explanation_kn is None
    assert explanations[0].metric_label_kn is None


# ==============================================================================
# 17. Existing farmer advisory response remains valid with explanations
# ==============================================================================
def test_farmer_advisory_response_schema_with_explanations():
    """Test 17: GET /api/v1/weather/farmer-advisory returns valid explanations and provenance."""
    response = client.get(
        "/api/v1/weather/farmer-advisory",
        params={"village_id": "V001", "crop": "arecanut", "language": "en"},
    )
    assert response.status_code == 200
    data = response.json()
    assert "status" in data
    assert "context" in data
    assert "advisories" in data
    assert "unsupported_rules" in data


# ==============================================================================
# 18. Existing historical advisory behavior remains unchanged
# ==============================================================================
def test_historical_advisory_behavior_unchanged():
    """Test 18: Historical advisory endpoint GET /api/v1/weather/advisories continues unaffected."""
    response = client.get("/api/v1/weather/advisories?village_id=V001&crop=arecanut")
    assert response.status_code == 200
    data = response.json()
    assert data["village_id"] == "V001"
    assert data["crop"] == "Arecanut"
    assert "metrics" in data
    assert "cloudy_days_streak" in data["metrics"]
    assert "advisories" in data
    assert "context" not in data
