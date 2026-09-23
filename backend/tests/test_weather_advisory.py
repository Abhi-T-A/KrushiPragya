from datetime import datetime, timedelta, timezone
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient

from app.api.v1.weather import get_weather_service
from app.database.connection import SessionLocal, get_db
from app.main import app
from app.models.village import Village
from app.models.weather_observation import WeatherObservation
from app.services.weather_advisory_service import (
    CropNotFoundError,
    VillageNotFoundError,
    get_weather_advisories,
    get_weather_advisory_bundle,
)
from app.services.weather_aggregation_service import (
    get_weather_metrics,
    is_observation_cloudy,
)
from app.services.weather_rule_engine import WeatherMetrics

client = TestClient(app)


@pytest.fixture
def db_session():
    """Provide a real transactional database session that always rolls back.

    Guarantees no persistent test weather observations are left in Supabase.
    """
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


def create_observation(
    db,
    village_id: str,
    observed_at: datetime,
    temperature_c: float = 25.0,
    humidity_pct: float = 70.0,
    rainfall_mm: float = 0.0,
    cloud_cover_pct: float = 20.0,
    weather_condition: str = "Clear",
    source: str = "TestFixture",
) -> WeatherObservation:
    """Helper to instantiate and flush a test WeatherObservation."""
    obs = WeatherObservation(
        id=uuid.uuid4(),
        village_id=village_id,
        observed_at=observed_at,
        temperature_c=Decimal(str(temperature_c)) if temperature_c is not None else None,
        humidity_pct=Decimal(str(humidity_pct)) if humidity_pct is not None else None,
        rainfall_mm=Decimal(str(rainfall_mm)) if rainfall_mm is not None else None,
        wind_speed_kmh=Decimal("10.0"),
        wind_direction_deg=Decimal("180.0"),
        pressure_hpa=Decimal("1012.0"),
        cloud_cover_pct=Decimal(str(cloud_cover_pct)) if cloud_cover_pct is not None else None,
        weather_condition=weather_condition,
        source=source,
    )
    db.add(obs)
    db.flush()
    return obs


# ==============================================================================
# TASK 10 — AGGREGATION TESTS
# ==============================================================================


def test_48_hour_rainfall_sum(db_session):
    """Test 1: Trailing 48-hour rainfall sum (30mm + 20mm + 25mm = 75mm)."""
    ref_time = datetime(2026, 9, 23, 12, 0, 0, tzinfo=timezone.utc)
    village_id = "V001"

    # Inside 48h window
    create_observation(db_session, village_id, ref_time - timedelta(hours=40), rainfall_mm=30.0)
    create_observation(db_session, village_id, ref_time - timedelta(hours=20), rainfall_mm=20.0)
    create_observation(db_session, village_id, ref_time - timedelta(hours=5), rainfall_mm=25.0)

    metrics = get_weather_metrics(db_session, village_id, reference_time=ref_time)
    assert metrics.rainfall_mm_48h == 75.0


def test_observation_outside_48h_window_excluded(db_session):
    """Test 2: Observations older than 48 hours are strictly excluded from sum."""
    ref_time = datetime(2026, 9, 23, 12, 0, 0, tzinfo=timezone.utc)
    village_id = "V001"

    # Inside window
    create_observation(db_session, village_id, ref_time - timedelta(hours=24), rainfall_mm=30.0)
    # Outside window (> 48h)
    create_observation(db_session, village_id, ref_time - timedelta(hours=49), rainfall_mm=100.0)
    # In future (> ref_time)
    create_observation(db_session, village_id, ref_time + timedelta(hours=1), rainfall_mm=50.0)

    metrics = get_weather_metrics(db_session, village_id, reference_time=ref_time)
    assert metrics.rainfall_mm_48h == 30.0


def test_null_rainfall_does_not_crash(db_session):
    """Test 3: NULL rainfall values are ignored and do not crash calculation."""
    ref_time = datetime(2026, 9, 23, 12, 0, 0, tzinfo=timezone.utc)
    village_id = "V001"

    create_observation(db_session, village_id, ref_time - timedelta(hours=10), rainfall_mm=None)
    create_observation(db_session, village_id, ref_time - timedelta(hours=5), rainfall_mm=45.0)

    metrics = get_weather_metrics(db_session, village_id, reference_time=ref_time)
    assert metrics.rainfall_mm_48h == 45.0


def test_all_null_rainfall_returns_none(db_session):
    """Verify that if all observations in window have NULL rainfall, result is None (not 0)."""
    ref_time = datetime(2026, 9, 23, 12, 0, 0, tzinfo=timezone.utc)
    village_id = "V001"

    create_observation(db_session, village_id, ref_time - timedelta(hours=10), rainfall_mm=None)
    create_observation(db_session, village_id, ref_time - timedelta(hours=5), rainfall_mm=None)

    metrics = get_weather_metrics(db_session, village_id, reference_time=ref_time)
    assert metrics.rainfall_mm_48h is None


def test_daily_maximum_temperature(db_session):
    """Test 4: Trailing 24-hour maximum temperature (25C, 29C, 27C -> 29C)."""
    ref_time = datetime(2026, 9, 23, 15, 0, 0, tzinfo=timezone.utc)
    village_id = "V001"

    create_observation(db_session, village_id, ref_time - timedelta(hours=20), temperature_c=25.0)
    create_observation(db_session, village_id, ref_time - timedelta(hours=12), temperature_c=29.0)
    create_observation(db_session, village_id, ref_time - timedelta(hours=2), temperature_c=27.0)
    # Outside 24h window
    create_observation(db_session, village_id, ref_time - timedelta(hours=26), temperature_c=38.0)

    metrics = get_weather_metrics(db_session, village_id, reference_time=ref_time)
    assert metrics.temp_max_c == 29.0


def test_cloudy_day_streak(db_session):
    """Test 5: Cloudy-day streak backwards from reference date.

    today = cloudy
    yesterday = cloudy
    2 days ago = cloudy
    3 days ago = clear
    Expected streak: 3
    """
    ref_time = datetime(2026, 9, 23, 14, 0, 0, tzinfo=timezone.utc)
    village_id = "V001"

    # Today (Sep 23): cloudy by cloud_cover_pct >= 75
    create_observation(
        db_session,
        village_id,
        datetime(2026, 9, 23, 10, 0, 0, tzinfo=timezone.utc),
        cloud_cover_pct=80.0,
        weather_condition="Scattered Clouds",
    )
    # Yesterday (Sep 22): cloudy by condition 'Cloudy'
    create_observation(
        db_session,
        village_id,
        datetime(2026, 9, 22, 11, 0, 0, tzinfo=timezone.utc),
        cloud_cover_pct=50.0,
        weather_condition="Cloudy",
    )
    # 2 days ago (Sep 21): cloudy by condition 'Overcast'
    create_observation(
        db_session,
        village_id,
        datetime(2026, 9, 21, 9, 0, 0, tzinfo=timezone.utc),
        cloud_cover_pct=70.0,
        weather_condition="overcast",
    )
    # 3 days ago (Sep 20): clear day (cloud_cover < 75, condition Sunny)
    create_observation(
        db_session,
        village_id,
        datetime(2026, 9, 20, 12, 0, 0, tzinfo=timezone.utc),
        cloud_cover_pct=20.0,
        weather_condition="Sunny",
    )

    metrics = get_weather_metrics(db_session, village_id, reference_time=ref_time)
    assert metrics.cloudy_days_streak == 3


def test_missing_weather_history(db_session):
    """Test 6: Missing weather history returns safe null metrics and empty advisories."""
    ref_time = datetime(2026, 9, 23, 12, 0, 0, tzinfo=timezone.utc)
    # V006 (Madikeri) has 0 observations
    metrics = get_weather_metrics(db_session, "V006", reference_time=ref_time)

    assert metrics.temperature_c is None
    assert metrics.temp_max_c is None
    assert metrics.humidity_pct is None
    assert metrics.rainfall_mm_48h is None
    assert metrics.cloudy_days_streak is None

    # Advisory evaluation with null metrics must return empty list
    advisories = get_weather_advisories(db_session, "V006", "Arecanut", reference_time=ref_time)
    assert advisories == []


def test_village_isolation(db_session):
    """Test 7: Observations from another village do not bleed into requested village."""
    ref_time = datetime(2026, 9, 23, 12, 0, 0, tzinfo=timezone.utc)
    v1 = "V001"
    v2 = "V002"

    create_observation(db_session, v1, ref_time - timedelta(hours=10), rainfall_mm=10.0, temperature_c=22.0)
    create_observation(db_session, v2, ref_time - timedelta(hours=10), rainfall_mm=95.0, temperature_c=34.0)

    m1 = get_weather_metrics(db_session, v1, reference_time=ref_time)
    m2 = get_weather_metrics(db_session, v2, reference_time=ref_time)

    assert m1.rainfall_mm_48h == 10.0
    assert m1.temp_max_c == 22.0

    assert m2.rainfall_mm_48h == 95.0
    assert m2.temp_max_c == 34.0


# ==============================================================================
# TASK 11 — API & SERVICE INTEGRATION TESTS
# ==============================================================================


def test_api_valid_request_with_matching_rules(db_session):
    """Test 8: Valid request triggers advisory matches (HTTP 200)."""
    ref_time = datetime(2026, 9, 23, 12, 0, 0, tzinfo=timezone.utc)
    village_id = "V001"

    # Create conditions to trigger Rule 1 (Koleroga: rainfall >= 70, humidity >= 85, cloudy streak >= 3)
    # Day 0
    create_observation(
        db_session,
        village_id,
        ref_time - timedelta(hours=2),
        temperature_c=26.0,
        humidity_pct=88.0,
        rainfall_mm=40.0,
        cloud_cover_pct=90.0,
    )
    # Day 0 earlier
    create_observation(
        db_session,
        village_id,
        ref_time - timedelta(hours=20),
        temperature_c=25.0,
        humidity_pct=86.0,
        rainfall_mm=40.0,
        cloud_cover_pct=85.0,
    )
    # Day -1
    create_observation(
        db_session,
        village_id,
        ref_time - timedelta(days=1),
        cloud_cover_pct=80.0,
        weather_condition="Overcast",
    )
    # Day -2
    create_observation(
        db_session,
        village_id,
        ref_time - timedelta(days=2),
        cloud_cover_pct=80.0,
        weather_condition="Cloudy",
    )

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        response = client.get(
            "/api/v1/weather/advisories",
            params={
                "village_id": "V001",
                "crop": "arecanut",
                "reference_time": ref_time.isoformat(),
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert data["village_id"] == "V001"
        assert data["crop"] == "Arecanut"
        assert data["metrics"]["rainfall_mm_48h"] == 80.0
        assert data["metrics"]["humidity_pct"] == 88.0
        assert data["metrics"]["cloudy_days_streak"] >= 3

        # Should match at least Rule 1 (Koleroga) and Rule 2 (Bud Rot)
        rule_ids = [a["rule_id"] for a in data["advisories"]]
        assert 1 in rule_ids
        assert 2 in rule_ids
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_api_valid_request_no_matching_rules(db_session):
    """Test 9: Valid request with moderate weather returns HTTP 200 and empty advisories.

    Rainfall 15mm (> 5mm dry window, < 30mm bud rot/koleroga), humidity 70% (> 65%, < 80%),
    temp 25C (< 28C min for dry window). None of the 4 Arecanut rules trigger.
    """
    ref_time = datetime(2026, 9, 23, 12, 0, 0, tzinfo=timezone.utc)
    village_id = "V001"

    create_observation(
        db_session,
        village_id,
        ref_time - timedelta(hours=2),
        temperature_c=25.0,
        humidity_pct=70.0,
        rainfall_mm=15.0,
        cloud_cover_pct=30.0,
        weather_condition="Scattered Clouds",
    )

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        response = client.get(
            "/api/v1/weather/advisories",
            params={
                "village_id": "V001",
                "crop": "arecanut",
                "reference_time": ref_time.isoformat(),
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert data["village_id"] == "V001"
        assert data["crop"] == "Arecanut"
        assert data["metrics"]["rainfall_mm_48h"] == 15.0
        assert data["advisories"] == []
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_api_unknown_village(db_session):
    """Test 10: Unknown village returns HTTP 404."""
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        response = client.get("/api/v1/weather/advisories?village_id=UNKNOWN_XYZ&crop=arecanut")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_api_unknown_crop(db_session):
    """Test 11: Unknown/unsupported crop returns HTTP 404."""
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        response = client.get("/api/v1/weather/advisories?village_id=V001&crop=pineapple_unknown")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower() or "unsupported" in data["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


@pytest.mark.parametrize("crop_input", ["arecanut", "Arecanut", "ARECANUT"])
def test_api_crop_case_normalization(crop_input, db_session):
    """Test 12: Crop code/name normalization works case-insensitively."""
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        response = client.get(f"/api/v1/weather/advisories?village_id=V001&crop={crop_input}")
        assert response.status_code == 200
        data = response.json()
        assert data["crop"] == "Arecanut"
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_api_missing_weather_history(db_session):
    """Test 13: Missing weather history returns HTTP 200 with null metrics and empty advisories."""
    app.dependency_overrides[get_db] = lambda: db_session
    try:
        # V006 has 0 observations
        response = client.get("/api/v1/weather/advisories?village_id=V006&crop=arecanut")
        assert response.status_code == 200
        data = response.json()

        assert data["village_id"] == "V006"
        assert data["crop"] == "Arecanut"
        assert data["metrics"]["rainfall_mm_48h"] is None
        assert data["metrics"]["temperature_c"] is None
        assert data["advisories"] == []
    finally:
        app.dependency_overrides.pop(get_db, None)
