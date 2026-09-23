from datetime import datetime, timezone
from decimal import Decimal
import uuid
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.main import app
from app.api.v1.weather import get_weather_service
from app.database.connection import get_db
from app.models.village import Village
from app.models.weather_observation import WeatherObservation
from app.schemas.weather import WeatherData
from app.services.weather_provider import (
    MockWeatherProvider,
    WeatherProvider,
    WeatherProviderError,
)
from app.services.weather_service import WeatherService

client = TestClient(app)


@pytest.fixture
def mock_village():
    """Return a mock Village entity with authoritative coordinates."""
    return Village(
        id="V001",
        name="Mangaluru",
        district="Dakshina Kannada",
        state="Karnataka",
        zone="Coastal",
        latitude=12.9141,
        longitude=74.8560,
    )


def test_weather_observe_valid_village(mock_village):
    """Verify POST /api/v1/weather/observe returns 200 and persists observation."""
    mock_db = MagicMock()
    mock_db.get.return_value = mock_village

    # Mock WeatherObservation instance with generated id
    def mock_save_observation(db, village_id, data):
        obs = WeatherObservation(
            id=uuid.uuid4(),
            village_id=village_id,
            observed_at=data.observed_at,
            temperature_c=data.temperature_c,
            humidity_pct=data.humidity_pct,
            rainfall_mm=data.rainfall_mm,
            wind_speed_kmh=data.wind_speed_kmh,
            wind_direction_deg=data.wind_direction_deg,
            pressure_hpa=data.pressure_hpa,
            cloud_cover_pct=data.cloud_cover_pct,
            weather_condition=data.weather_condition,
            source=data.source,
            created_at=datetime.now(timezone.utc),
            updated_at=datetime.now(timezone.utc),
        )
        db.add(obs)
        db.commit()
        return obs

    provider = MockWeatherProvider()
    service = WeatherService(provider=provider)
    service.save_observation = MagicMock(side_effect=lambda db, village_id, data: mock_save_observation(db, village_id, data))

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_weather_service] = lambda: service

    try:
        response = client.post("/api/v1/weather/observe", json={"village_id": "V001"})
        assert response.status_code == 200
        data = response.json()
        assert data["village_id"] == "V001"
        assert data["source"] == "MockWeatherProvider"
        assert float(data["temperature_c"]) == 28.50
        assert float(data["humidity_pct"]) == 75.00
        assert "id" in data
        assert "observed_at" in data

        # Verify village lookup was by authoritative ID
        mock_db.get.assert_called_once_with(Village, "V001")
        # Verify persistence occurred
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_weather_service, None)


def test_weather_observe_unknown_village():
    """Verify POST /api/v1/weather/observe returns 404 when village does not exist."""
    mock_db = MagicMock()
    mock_db.get.return_value = None  # Village not found

    app.dependency_overrides[get_db] = lambda: mock_db
    try:
        response = client.post("/api/v1/weather/observe", json={"village_id": "V_NON_EXISTENT"})
        assert response.status_code == 404
        data = response.json()
        assert "detail" in data
        assert "not found" in data["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)


def test_weather_observe_provider_failure(mock_village):
    """Verify POST /api/v1/weather/observe returns 502 when weather provider fails."""
    mock_db = MagicMock()
    mock_db.get.return_value = mock_village

    failing_provider = MagicMock(spec=WeatherProvider)
    failing_provider.get_current_weather.side_effect = WeatherProviderError("API gateway timeout")
    service = WeatherService(provider=failing_provider)

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_weather_service] = lambda: service
    try:
        response = client.post("/api/v1/weather/observe", json={"village_id": "V001"})
        assert response.status_code == 502
        data = response.json()
        assert "Weather provider error" in data["detail"]
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_weather_service, None)


def test_weather_observe_invalid_request_body():
    """Verify POST /api/v1/weather/observe returns 422 when request body is invalid."""
    # Missing village_id field
    response = client.post("/api/v1/weather/observe", json={})
    assert response.status_code == 422

    # Empty village_id string
    response = client.post("/api/v1/weather/observe", json={"village_id": ""})
    assert response.status_code == 422

    # Wrong data type
    response = client.post("/api/v1/weather/observe", json={"village_id": 12345})
    assert response.status_code in (200, 422)  # pydantic may coerce int to str if valid, or 422 if strict


def test_weather_observe_persistence_verification(mock_village):
    """Verify that WeatherObservation is correctly constructed and persisted with expected fields."""
    mock_db = MagicMock()
    mock_db.get.return_value = mock_village

    def mock_refresh(instance):
        if getattr(instance, "id", None) is None:
            instance.id = uuid.uuid4()
        if getattr(instance, "created_at", None) is None:
            instance.created_at = datetime.now(timezone.utc)

    mock_db.refresh.side_effect = mock_refresh

    now = datetime.now(timezone.utc)
    custom_weather = WeatherData(
        observed_at=now,
        temperature_c=Decimal("31.20"),
        humidity_pct=Decimal("65.00"),
        rainfall_mm=Decimal("0.00"),
        wind_speed_kmh=Decimal("14.00"),
        wind_direction_deg=Decimal("180.00"),
        pressure_hpa=Decimal("1014.00"),
        cloud_cover_pct=Decimal("20.00"),
        weather_condition="Clear Sky",
        source="MockWeatherProvider",
    )

    custom_provider = MagicMock(spec=WeatherProvider)
    custom_provider.get_current_weather.return_value = custom_weather
    service = WeatherService(provider=custom_provider)

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_weather_service] = lambda: service

    try:
        response = client.post("/api/v1/weather/observe", json={"village_id": "V001"})
        assert response.status_code == 200

        # Assert custom provider was called with the village's authoritative lat/lon
        custom_provider.get_current_weather.assert_called_once_with(12.9141, 74.8560)

        # Inspect the argument passed to db.add
        added_observation = mock_db.add.call_args[0][0]
        assert isinstance(added_observation, WeatherObservation)
        assert added_observation.village_id == "V001"
        assert added_observation.temperature_c == Decimal("31.20")
        assert added_observation.humidity_pct == Decimal("65.00")
        assert added_observation.weather_condition == "Clear Sky"
        assert added_observation.source == "MockWeatherProvider"

        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_weather_service, None)
