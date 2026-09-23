"""Unit and API tests for forecast-based agricultural advisory integration."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.api.v1.weather import get_forecast_advisory_service, get_weather_forecast_service
from app.database.connection import SessionLocal, get_db
from app.main import app
from app.models.advisory_rule import AdvisoryRule
from app.models.crop import Crop
from app.models.village import Village
from app.schemas.weather import ForecastData
from app.services.forecast_advisory_service import (
    ForecastAdvisoryService,
    UnsupportedRule,
)
from app.services.forecast_aggregation_service import ForecastAggregationService
from app.services.weather_forecast_service import WeatherForecastService
from app.services.weather_provider import (
    ForecastProvider,
    MockWeatherProvider,
    WeatherProviderError,
)
from app.services.weather_rule_engine import WeatherMetrics, evaluate_rule

client = TestClient(app)


@pytest.fixture
def db_session():
    """Transactional DB session that rolls back automatically."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def _build_forecast_points(
    ref_time: datetime,
    rainfall_per_item: float = 0.0,
    temp: float = 25.0,
    humidity: float = 70.0,
    cloud_cover: float = 0.0,
    condition: str = "Clear",
    num_items: int = 16,  # 16 * 3h = 48 hours
) -> list[ForecastData]:
    """Helper to generate a sequence of 3-hourly ForecastData points."""
    points = []
    for i in range(num_items):
        points.append(
            ForecastData(
                timestamp=ref_time + timedelta(hours=i * 3),
                temperature_c=Decimal(str(temp)),
                humidity_pct=Decimal(str(humidity)),
                rainfall_mm=Decimal(str(rainfall_per_item)),
                wind_speed_kmh=Decimal("12.0"),
                cloud_cover_pct=Decimal(str(cloud_cover)),
                weather_condition=condition,
            )
        )
    return points


# ==============================================================================
# 1. Forecast advisory success
# ==============================================================================
def test_forecast_advisory_success():
    """Test 1: Valid forecast advisory request returns HTTP 200 with complete structure."""
    mock_provider = MockWeatherProvider()
    forecast_service = WeatherForecastService(provider=mock_provider)
    advisory_service = ForecastAdvisoryService(forecast_service=forecast_service)

    app.dependency_overrides[get_forecast_advisory_service] = lambda: advisory_service

    try:
        response = client.get("/api/v1/weather/forecast-advisories?village_id=V001&crop=arecanut")
        assert response.status_code == 200
        data = response.json()

        assert data["village_id"] == "V001"
        assert data["crop"] == "Arecanut"
        assert "generated_at" in data
        assert "forecast_reference_time" in data
        assert "metrics" in data
        assert "advisories" in data
        assert "unsupported_rules" in data

        # Koleroga & Bud Rot require cloudy_days_streak, must be in unsupported_rules
        unsupported_ids = [r["rule_id"] for r in data["unsupported_rules"]]
        assert 1 in unsupported_ids
        assert 2 in unsupported_ids
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 2. Unknown village -> 404
# ==============================================================================
def test_unknown_village_404():
    """Test 2: Unknown village returns HTTP 404."""
    response = client.get("/api/v1/weather/forecast-advisories?village_id=UNKNOWN_VILLAGE&crop=arecanut")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ==============================================================================
# 3. Unknown crop -> 404
# ==============================================================================
def test_unknown_crop_404():
    """Test 3: Unknown crop returns HTTP 404."""
    response = client.get("/api/v1/weather/forecast-advisories?village_id=V001&crop=unsupported_crop_xyz")
    assert response.status_code == 404
    assert "not found" in response.json()["detail"].lower()


# ==============================================================================
# 4. Provider failure -> 502
# ==============================================================================
def test_provider_failure_502():
    """Test 4: Provider error returns HTTP 502 Bad Gateway."""
    failing_provider = MagicMock(spec=ForecastProvider)
    failing_provider.get_forecast.side_effect = WeatherProviderError("Upstream API unavailable")

    forecast_service = WeatherForecastService(provider=failing_provider)
    advisory_service = ForecastAdvisoryService(forecast_service=forecast_service)

    app.dependency_overrides[get_forecast_advisory_service] = lambda: advisory_service

    try:
        response = client.get("/api/v1/weather/forecast-advisories?village_id=V001&crop=arecanut")
        assert response.status_code == 502
        assert "Weather provider error" in response.json()["detail"]
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 5. Missing forecast data -> 200 with empty advisories
# ==============================================================================
def test_missing_forecast_data_returns_200():
    """Test 5: Empty forecast returns HTTP 200 with null metrics and empty advisories."""
    empty_provider = MagicMock(spec=ForecastProvider)
    empty_provider.get_forecast.return_value = []

    forecast_service = WeatherForecastService(provider=empty_provider)
    advisory_service = ForecastAdvisoryService(forecast_service=forecast_service)

    app.dependency_overrides[get_forecast_advisory_service] = lambda: advisory_service

    try:
        response = client.get("/api/v1/weather/forecast-advisories?village_id=V001&crop=arecanut")
        assert response.status_code == 200
        data = response.json()
        assert data["advisories"] == []
        assert data["metrics"]["rainfall_mm_24h"] is None
        assert data["metrics"]["rainfall_mm_48h"] is None
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 6. Rainfall threshold match (Rule 3: Waterlogging >= 100mm)
# ==============================================================================
def test_rainfall_threshold_match():
    """Test 6: Rule requiring min_rainfall_mm_48h = 100 matches when forecast >= 100mm."""
    ref_time = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    # 16 items * 7mm = 112mm > 100mm threshold
    items = _build_forecast_points(ref_time, rainfall_per_item=7.0, temp=26.0, humidity=85.0)

    mock_provider = MagicMock(spec=ForecastProvider)
    mock_provider.get_forecast.return_value = items

    forecast_service = WeatherForecastService(provider=mock_provider)
    advisory_service = ForecastAdvisoryService(forecast_service=forecast_service)

    app.dependency_overrides[get_forecast_advisory_service] = lambda: advisory_service

    try:
        response = client.get(
            "/api/v1/weather/forecast-advisories",
            params={"village_id": "V001", "crop": "arecanut", "reference_time": ref_time.isoformat()},
        )
        assert response.status_code == 200
        data = response.json()

        matched_rules = [a["rule_id"] for a in data["advisories"]]
        # Rule 3 is 'Heavy Rainfall Waterlogging Risk Context' (min_rainfall_mm_48h = 100)
        assert 3 in matched_rules
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 7. Maximum rainfall threshold match (Rule 4: Dry Window <= 5mm)
# ==============================================================================
def test_maximum_rainfall_threshold_match():
    """Test 7: Rule requiring max_rainfall_mm_48h = 5 matches when rainfall <= 5."""
    ref_time = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    # 16 items * 0.1mm = 1.6mm <= 5mm, humidity = 65% <= 72%, temp = 30C >= 28C
    items = _build_forecast_points(ref_time, rainfall_per_item=0.1, temp=30.0, humidity=65.0)

    mock_provider = MagicMock(spec=ForecastProvider)
    mock_provider.get_forecast.return_value = items

    forecast_service = WeatherForecastService(provider=mock_provider)
    advisory_service = ForecastAdvisoryService(forecast_service=forecast_service)

    app.dependency_overrides[get_forecast_advisory_service] = lambda: advisory_service

    try:
        response = client.get(
            "/api/v1/weather/forecast-advisories",
            params={"village_id": "V001", "crop": "arecanut", "reference_time": ref_time.isoformat()},
        )
        assert response.status_code == 200
        data = response.json()

        matched_rules = [a["rule_id"] for a in data["advisories"]]
        # Rule 4 is 'Post-Monsoon Dry Operational Window'
        assert 4 in matched_rules
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 8. Humidity threshold match & fail behavior
# ==============================================================================
def test_humidity_threshold_match_and_fail():
    """Test 8: Rule 4 max_humidity_pct = 72 fails when forecast average humidity is high."""
    ref_time = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    # Rainfall = 1.6mm (passes <= 5), Temp = 30C (passes >= 28), Humidity = 85% (> 72% fails)
    items = _build_forecast_points(ref_time, rainfall_per_item=0.1, temp=30.0, humidity=85.0)

    mock_provider = MagicMock(spec=ForecastProvider)
    mock_provider.get_forecast.return_value = items

    forecast_service = WeatherForecastService(provider=mock_provider)
    advisory_service = ForecastAdvisoryService(forecast_service=forecast_service)

    app.dependency_overrides[get_forecast_advisory_service] = lambda: advisory_service

    try:
        response = client.get(
            "/api/v1/weather/forecast-advisories",
            params={"village_id": "V001", "crop": "arecanut", "reference_time": ref_time.isoformat()},
        )
        assert response.status_code == 200
        data = response.json()

        matched_rules = [a["rule_id"] for a in data["advisories"]]
        # Rule 4 fails because humidity (85%) > threshold (72%)
        assert 4 not in matched_rules
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 9. Temperature threshold match & fail behavior
# ==============================================================================
def test_temperature_threshold_match_and_fail():
    """Test 9: Rule 4 min_temp_max_c = 28 fails when forecast max temp < 28."""
    ref_time = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    # Rainfall = 1.6mm (passes <= 5), Humidity = 65% (passes <= 72), Temp = 24C (< 28C fails)
    items = _build_forecast_points(ref_time, rainfall_per_item=0.1, temp=24.0, humidity=65.0)

    mock_provider = MagicMock(spec=ForecastProvider)
    mock_provider.get_forecast.return_value = items

    forecast_service = WeatherForecastService(provider=mock_provider)
    advisory_service = ForecastAdvisoryService(forecast_service=forecast_service)

    app.dependency_overrides[get_forecast_advisory_service] = lambda: advisory_service

    try:
        response = client.get(
            "/api/v1/weather/forecast-advisories",
            params={"village_id": "V001", "crop": "arecanut", "reference_time": ref_time.isoformat()},
        )
        assert response.status_code == 200
        data = response.json()

        matched_rules = [a["rule_id"] for a in data["advisories"]]
        # Rule 4 fails because max temp (24C) < threshold (28C)
        assert 4 not in matched_rules
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 10. MANDATORY SAFETY TEST: Cloudy-days rule is NOT falsely matched
# ==============================================================================
def test_cloudy_days_rule_not_falsely_matched():
    """Test 10: Rule requiring min_cloudy_days_streak must NEVER match from forecast cloudy_hours.

    Even if forecast is 100% overcast/cloudy for 48 hours and rainfall/humidity thresholds
    are completely satisfied, Koleroga (Rule 1) and Bud Rot (Rule 2) must NOT match.
    They must be placed into unsupported_rules.
    """
    ref_time = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    # 48 hours of 100% overcast, rainfall = 80mm (>70mm Koleroga), humidity = 90% (>85%)
    items = _build_forecast_points(
        ref_time,
        rainfall_per_item=5.0,  # 16 * 5 = 80mm
        temp=28.0,
        humidity=90.0,
        cloud_cover=100.0,
        condition="overcast",
    )

    mock_provider = MagicMock(spec=ForecastProvider)
    mock_provider.get_forecast.return_value = items

    forecast_service = WeatherForecastService(provider=mock_provider)
    advisory_service = ForecastAdvisoryService(forecast_service=forecast_service)

    app.dependency_overrides[get_forecast_advisory_service] = lambda: advisory_service

    try:
        response = client.get(
            "/api/v1/weather/forecast-advisories",
            params={"village_id": "V001", "crop": "arecanut", "reference_time": ref_time.isoformat()},
        )
        assert response.status_code == 200
        data = response.json()

        # Verify cloudy_hours_48h is indeed high
        assert float(data["metrics"]["cloudy_hours_48h"]) >= 45.0

        matched_rules = [a["rule_id"] for a in data["advisories"]]
        # Rule 1 (Koleroga) and Rule 2 (Bud Rot) require min_cloudy_days_streak = 3
        # Neither must match!
        assert 1 not in matched_rules
        assert 2 not in matched_rules

        # Both must appear in unsupported_rules
        unsupported = {u["rule_id"]: u["reason"] for u in data["unsupported_rules"]}
        assert 1 in unsupported
        assert 2 in unsupported
        assert "cloudy_days_streak" in unsupported[1]
        assert "cloudy_days_streak" in unsupported[2]
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 11. Multiple compatible rules evaluation logic
# ==============================================================================
def test_rule_metric_mapping_unit_evaluation():
    """Test 11: Direct evaluation of compatible rules via WeatherMetrics adapter."""
    # Synthetic rule requiring min_rainfall_mm_48h = 30 and min_humidity_pct = 80
    rule = AdvisoryRule(
        id=99,
        crop="Arecanut",
        risk_name="Synthetic Risk",
        risk_level="HIGH",
        condition_type="WEATHER_THRESHOLD",
        condition_config={
            "min_rainfall_mm_48h": 30.0,
            "min_humidity_pct": 80.0,
            "min_temp_max_c": 28.0,
        },
        advisory_en="Test advisory",
        advisory_kn="Test advisory kn",
        source_name="Test",
        active=True,
    )

    # 1. Matching metrics
    matching_metrics = WeatherMetrics(
        rainfall_mm_48h=35.0,
        humidity_pct=82.0,
        temp_max_c=29.0,
        cloudy_days_streak=None,
    )
    match = evaluate_rule(rule, matching_metrics)
    assert match is not None
    assert match.rule_id == 99

    # 2. Failing on rainfall
    failing_rain = WeatherMetrics(
        rainfall_mm_48h=20.0,
        humidity_pct=82.0,
        temp_max_c=29.0,
    )
    assert evaluate_rule(rule, failing_rain) is None


# ==============================================================================
# 12. Response clearly represents forecast-derived metrics
# ==============================================================================
def test_response_structure_forecast_derived_metrics():
    """Test 12: Verify response metrics contain all 24h and 48h forecast dimensions."""
    mock_provider = MockWeatherProvider()
    forecast_service = WeatherForecastService(provider=mock_provider)
    advisory_service = ForecastAdvisoryService(forecast_service=forecast_service)

    app.dependency_overrides[get_forecast_advisory_service] = lambda: advisory_service

    try:
        response = client.get("/api/v1/weather/forecast-advisories?village_id=V001&crop=arecanut")
        assert response.status_code == 200
        metrics = response.json()["metrics"]

        expected_fields = [
            "rainfall_mm_24h",
            "rainfall_mm_48h",
            "max_temperature_c_24h",
            "max_temperature_c_48h",
            "min_temperature_c_24h",
            "min_temperature_c_48h",
            "avg_humidity_pct_24h",
            "avg_humidity_pct_48h",
            "max_wind_speed_kmh_24h",
            "max_wind_speed_kmh_48h",
            "cloudy_hours_24h",
            "cloudy_hours_48h",
        ]
        for field in expected_fields:
            assert field in metrics
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 13. Reference time is handled correctly
# ==============================================================================
def test_reference_time_handled_correctly():
    """Test 13: Query reference_time anchors forecast evaluation window."""
    ref_time = datetime(2026, 9, 24, 18, 0, 0, tzinfo=timezone.utc)
    mock_provider = MockWeatherProvider()
    forecast_service = WeatherForecastService(provider=mock_provider)
    advisory_service = ForecastAdvisoryService(forecast_service=forecast_service)

    app.dependency_overrides[get_forecast_advisory_service] = lambda: advisory_service

    try:
        response = client.get(
            "/api/v1/weather/forecast-advisories",
            params={"village_id": "V001", "crop": "arecanut", "reference_time": ref_time.isoformat()},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["forecast_reference_time"] == "2026-09-24T18:00:00Z"
    finally:
        app.dependency_overrides.clear()


# ==============================================================================
# 14. Existing historical advisory behavior remains unchanged
# ==============================================================================
def test_existing_historical_advisory_behavior_unchanged():
    """Test 14: Existing GET /api/v1/weather/advisories continues to operate identically."""
    response = client.get("/api/v1/weather/advisories?village_id=V001&crop=arecanut")
    assert response.status_code == 200
    data = response.json()
    assert data["village_id"] == "V001"
    assert data["crop"] == "Arecanut"
    assert "metrics" in data
    assert "cloudy_days_streak" in data["metrics"]
    assert "advisories" in data
    # Ensure forecast fields are NOT present in the historical endpoint
    assert "forecast_reference_time" not in data
    assert "unsupported_rules" not in data
