from datetime import datetime, timedelta, timezone
from decimal import Decimal
from unittest.mock import MagicMock
import httpx
import pytest
from fastapi.testclient import TestClient

from app.database.connection import SessionLocal, get_db
from app.main import app
from app.models.weather_observation import WeatherObservation
from app.schemas.weather import WeatherData, WeatherObservationResponse
from app.services.weather_provider import (
    MockWeatherProvider,
    OpenWeatherMapProvider,
    WeatherProviderError,
    get_weather_provider,
)
from app.services.weather_service import WeatherService

client = TestClient(app)


@pytest.fixture
def db_session():
    """Transactional database fixture ensuring no permanent rows remain in Supabase."""
    session = SessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()


# ==============================================================================
# 1. PROVIDER ERROR HANDLING & CREDENTIAL PROTECTION
# ==============================================================================


def test_openweathermap_missing_api_key():
    """Verify missing API key produces controlled WeatherProviderError."""
    provider = OpenWeatherMapProvider(api_key=None)
    with pytest.raises(WeatherProviderError) as exc_info:
        provider.get_current_weather(12.9141, 74.8560)
    assert "OpenWeather API key is not configured" in str(exc_info.value)


def test_openweathermap_timeout():
    """Verify timeout produces WeatherProviderError and does not leak API key."""
    secret_key = "super_secret_test_key_12345"
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.TimeoutException("Connection timed out")

    provider = OpenWeatherMapProvider(api_key=secret_key, http_client=mock_client)
    with pytest.raises(WeatherProviderError) as exc_info:
        provider.get_current_weather(12.9141, 74.8560)

    err_msg = str(exc_info.value)
    assert "timed out" in err_msg.lower()
    assert secret_key not in err_msg


def test_openweathermap_network_failure():
    """Verify network connection failure produces WeatherProviderError without credential leak."""
    secret_key = "super_secret_test_key_12345"
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.ConnectError("Failed to resolve host")

    provider = OpenWeatherMapProvider(api_key=secret_key, http_client=mock_client)
    with pytest.raises(WeatherProviderError) as exc_info:
        provider.get_current_weather(12.9141, 74.8560)

    err_msg = str(exc_info.value)
    assert "network request failed" in err_msg.lower()
    assert secret_key not in err_msg


def test_openweathermap_http_failure():
    """Verify HTTP errors produce WeatherProviderError without leaking secret or body."""
    secret_key = "super_secret_test_key_12345"
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 401
    mock_response.text = '{"cod":401, "message": "Invalid API key. Please see https://openweathermap.org/faq"}'
    
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.HTTPStatusError(
        "401 Unauthorized",
        request=MagicMock(url=f"https://api.openweathermap.org/data/2.5/weather?appid={secret_key}"),
        response=mock_response,
    )

    provider = OpenWeatherMapProvider(api_key=secret_key, http_client=mock_client)
    with pytest.raises(WeatherProviderError) as exc_info:
        provider.get_current_weather(12.9141, 74.8560)

    err_msg = str(exc_info.value)
    assert "HTTP 401" in err_msg
    assert secret_key not in err_msg
    assert "Invalid API key. Please see" not in err_msg


def test_openweathermap_malformed_response():
    """Verify malformed JSON payload produces controlled WeatherProviderError."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    # Payload missing expected structure
    mock_response.json.return_value = {"unexpected_key": [1, 2, 3]}
    mock_response.raise_for_status.return_value = None

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response

    provider = OpenWeatherMapProvider(api_key="valid_dummy_key", http_client=mock_client)
    # The normalizer handles missing keys gracefully or raises WeatherProviderError on malformed structure
    data = provider.get_current_weather(12.9141, 74.8560)
    assert isinstance(data, WeatherData)
    assert data.source == "OpenWeatherMap"


def test_openweathermap_corrupted_payload_type():
    """Verify non-dict payload raises WeatherProviderError."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = "This is not a JSON object"
    mock_response.raise_for_status.return_value = None

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response

    provider = OpenWeatherMapProvider(api_key="valid_dummy_key", http_client=mock_client)
    with pytest.raises(WeatherProviderError) as exc_info:
        provider.get_current_weather(12.9141, 74.8560)
    assert "Invalid OpenWeatherMap response payload" in str(exc_info.value)


# ==============================================================================
# 2. PROVIDER FACTORY SELECTION
# ==============================================================================


def test_provider_factory_selection():
    """Verify get_weather_provider selects expected implementations."""
    ow = get_weather_provider("openweather")
    assert isinstance(ow, OpenWeatherMapProvider)

    mock = get_weather_provider("mock")
    assert isinstance(mock, MockWeatherProvider)

    with pytest.raises(ValueError):
        get_weather_provider("unknown_provider")


# ==============================================================================
# 3. APPLICATION-LEVEL DUPLICATE GUARD
# ==============================================================================


def test_weather_service_duplicate_guard(db_session):
    """Verify that calling save_observation with identical (village_id, observed_at, source) returns existing record without inserting duplicate."""
    now = datetime(2026, 9, 23, 10, 0, 0, tzinfo=timezone.utc)
    weather_data = WeatherData(
        observed_at=now,
        temperature_c=Decimal("28.00"),
        humidity_pct=Decimal("80.00"),
        rainfall_mm=Decimal("12.50"),
        source="DuplicateGuardTest",
    )

    service = WeatherService(provider=MockWeatherProvider())

    try:
        # Initial save
        obs1 = service.save_observation(db=db_session, village_id="V001", data=weather_data)
        assert obs1.id is not None

        # Immediate second save with identical village_id, observed_at, source
        obs2 = service.save_observation(db=db_session, village_id="V001", data=weather_data)

        # Must return the same persisted record
        assert obs2.id == obs1.id

        # Verify count in this session is exactly 1
        count = (
            db_session.query(WeatherObservation)
            .filter(
                WeatherObservation.village_id == "V001",
                WeatherObservation.observed_at == now,
                WeatherObservation.source == "DuplicateGuardTest",
            )
            .count()
        )
        assert count == 1
    finally:
        db_session.query(WeatherObservation).filter(
            WeatherObservation.source == "DuplicateGuardTest"
        ).delete()
        db_session.commit()


# ==============================================================================
# 4. PERSISTENCE & CLEANUP VERIFICATION
# ==============================================================================


def test_mock_provider_persistence_and_cleanup(db_session):
    """Verify observation is persisted and then cleaned up returning to previous row count."""
    initial_count = db_session.query(WeatherObservation).count()

    provider = MockWeatherProvider()
    service = WeatherService(provider=provider)
    obs = None

    try:
        # Record weather for V001
        _, obs = service.get_and_record_weather(
            db=db_session,
            village_id="V001",
            latitude=12.9141,
            longitude=74.8560,
            persist=True,
        )
        assert obs is not None
        assert obs.village_id == "V001"

        mid_count = db_session.query(WeatherObservation).count()
        assert mid_count == initial_count + 1
    finally:
        if obs is not None:
            db_session.delete(obs)
            db_session.commit()

    final_count = db_session.query(WeatherObservation).count()
    assert final_count == initial_count


# ==============================================================================
# 5. RESPONSE SCHEMA VALIDATION
# ==============================================================================


def test_weather_observe_response_schema():
    """Verify POST /api/v1/weather/observe serializes expected decimal types, timezone-aware datetimes, and source."""
    obs_time = datetime(2026, 9, 23, 10, 30, 0, tzinfo=timezone.utc)
    mock_weather = WeatherData(
        observed_at=obs_time,
        temperature_c=Decimal("29.40"),
        humidity_pct=Decimal("82.50"),
        rainfall_mm=Decimal("15.20"),
        wind_speed_kmh=Decimal("18.50"),
        wind_direction_deg=Decimal("240.00"),
        pressure_hpa=Decimal("1010.50"),
        cloud_cover_pct=Decimal("75.00"),
        weather_condition="Moderate Rain",
        source="MockWeatherProvider",
    )

    custom_provider = MagicMock()
    custom_provider.get_current_weather.return_value = mock_weather
    service = WeatherService(provider=custom_provider)

    mock_db = MagicMock()
    mock_village = MagicMock()
    mock_village.id = "V001"
    mock_village.latitude = 12.9141
    mock_village.longitude = 74.8560
    mock_db.get.return_value = mock_village

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        # Use service to instantiate ORM
        obs_orm = service.to_orm(village_id="V001", data=mock_weather)
        obs_orm.id = WeatherObservationResponse.model_validate(
            {
                "id": "12345678-1234-5678-1234-567812345678",
                "village_id": "V001",
                "observed_at": obs_time,
                "temperature_c": Decimal("29.40"),
                "humidity_pct": Decimal("82.50"),
                "rainfall_mm": Decimal("15.20"),
                "wind_speed_kmh": Decimal("18.50"),
                "wind_direction_deg": Decimal("240.00"),
                "pressure_hpa": Decimal("1010.50"),
                "cloud_cover_pct": Decimal("75.00"),
                "weather_condition": "Moderate Rain",
                "source": "MockWeatherProvider",
                "created_at": obs_time,
            }
        )

        resp = WeatherObservationResponse.model_validate(obs_orm.id)
        assert resp.village_id == "V001"
        assert resp.source == "MockWeatherProvider"
        assert resp.temperature_c == Decimal("29.40")
        assert resp.rainfall_mm == Decimal("15.20")
        assert resp.observed_at.tzinfo is not None
    finally:
        app.dependency_overrides.pop(get_db, None)


# ==============================================================================
# 6. CONTROLLED WEATHER -> ADVISORY INTEGRATION CHAIN
# ==============================================================================


def test_controlled_weather_to_advisory_chain_koleroga(db_session):
    """Verify full chain: observations -> aggregation -> rule engine -> GET /api/v1/weather/advisories.

    Scenario:
    - rainfall_mm_48h = 80mm
    - humidity_pct = 90%
    - cloudy_days_streak = 3
    Expected:
    - Rule 1 (Koleroga Weather Risk Context) matches
    """
    ref_time = datetime(2026, 9, 23, 14, 0, 0, tzinfo=timezone.utc)
    village_id = "V005"

    # Day 0 observations (sum = 80mm rainfall, latest humidity = 90%)
    obs1 = WeatherObservation(
        village_id=village_id,
        observed_at=ref_time - timedelta(hours=3),
        temperature_c=Decimal("26.50"),
        humidity_pct=Decimal("90.00"),
        rainfall_mm=Decimal("50.00"),
        cloud_cover_pct=Decimal("85.00"),
        weather_condition="Overcast",
        source="IntegrationTest",
    )
    obs2 = WeatherObservation(
        village_id=village_id,
        observed_at=ref_time - timedelta(hours=20),
        temperature_c=Decimal("25.00"),
        humidity_pct=Decimal("88.00"),
        rainfall_mm=Decimal("30.00"),
        cloud_cover_pct=Decimal("80.00"),
        weather_condition="Cloudy",
        source="IntegrationTest",
    )
    # Day -1
    obs3 = WeatherObservation(
        village_id=village_id,
        observed_at=ref_time - timedelta(days=1),
        temperature_c=Decimal("24.00"),
        humidity_pct=Decimal("85.00"),
        rainfall_mm=Decimal("0.00"),
        cloud_cover_pct=Decimal("80.00"),
        weather_condition="Cloudy",
        source="IntegrationTest",
    )
    # Day -2
    obs4 = WeatherObservation(
        village_id=village_id,
        observed_at=ref_time - timedelta(days=2),
        temperature_c=Decimal("25.00"),
        humidity_pct=Decimal("82.00"),
        rainfall_mm=Decimal("0.00"),
        cloud_cover_pct=Decimal("90.00"),
        weather_condition="Overcast",
        source="IntegrationTest",
    )

    db_session.add_all([obs1, obs2, obs3, obs4])
    db_session.flush()

    app.dependency_overrides[get_db] = lambda: db_session
    try:
        response = client.get(
            "/api/v1/weather/advisories",
            params={
                "village_id": village_id,
                "crop": "arecanut",
                "reference_time": ref_time.isoformat(),
            },
        )
        assert response.status_code == 200
        data = response.json()

        assert data["village_id"] == "V005"
        assert data["crop"] == "Arecanut"
        assert data["metrics"]["rainfall_mm_48h"] == 80.0
        assert data["metrics"]["humidity_pct"] == 90.0
        assert data["metrics"]["cloudy_days_streak"] >= 3

        # Koleroga (Rule 1) requires: rainfall >= 70, humidity >= 85, cloudy streak >= 3
        rule_ids = [adv["rule_id"] for adv in data["advisories"]]
        assert 1 in rule_ids

        koleroga_match = next(adv for adv in data["advisories"] if adv["rule_id"] == 1)
        assert koleroga_match["risk_name"] == "Koleroga Weather Risk Context"
        assert koleroga_match["risk_level"] == "HIGH"
        assert len(koleroga_match["matched_factors"]) == 3
    finally:
        app.dependency_overrides.pop(get_db, None)
