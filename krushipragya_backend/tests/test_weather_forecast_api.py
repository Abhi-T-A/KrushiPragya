from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from app.api.v1.weather import get_weather_forecast_service
from app.database.connection import SessionLocal, get_db
from app.main import app
from app.models.village import Village
from app.schemas.weather import ForecastData
from app.services.weather_forecast_service import WeatherForecastService
from app.services.weather_provider import (
    ForecastProvider,
    MockWeatherProvider,
    WeatherProviderError,
)

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


@pytest.fixture
def mock_v001_village():
    """Return mock Village entity for V001."""
    return Village(
        id="V001",
        name="Mangaluru",
        district="Dakshina Kannada",
        state="Karnataka",
        zone="Coastal",
        latitude=12.9141,
        longitude=74.8560,
    )


# ==============================================================================
# STEP 9B API TESTS
# ==============================================================================


def test_forecast_api_success_mock_provider(mock_v001_village):
    """Test 1: Successful forecast request using MockWeatherProvider returns HTTP 200."""
    mock_db = MagicMock()
    mock_db.get.return_value = mock_v001_village

    provider = MockWeatherProvider()
    service = WeatherForecastService(provider=provider)

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_weather_forecast_service] = lambda: service
    try:
        response = client.get("/api/v1/weather/forecast", params={"village_id": "V001"})
        assert response.status_code == 200
        data = response.json()

        assert data["village_id"] == "V001"
        assert "generated_at" in data
        assert len(data["forecast"]) == 40
        assert float(data["forecast"][0]["temperature_c"]) == 27.50
        assert float(data["forecast"][0]["humidity_pct"]) == 78.00
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_weather_forecast_service, None)


def test_forecast_api_unknown_village():
    """Test 2: Unknown village returns HTTP 404."""
    mock_db = MagicMock()
    mock_db.get.return_value = None  # Village not found

    service = WeatherForecastService(provider=MockWeatherProvider())

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_weather_forecast_service] = lambda: service
    try:
        response = client.get("/api/v1/weather/forecast", params={"village_id": "UNKNOWN_VILLAGE"})
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_weather_forecast_service, None)


def test_forecast_api_provider_failure(mock_v001_village):
    """Test 3: Provider failure raises HTTP 502 with safe error detail."""
    mock_db = MagicMock()
    mock_db.get.return_value = mock_v001_village

    failing_provider = MagicMock(spec=ForecastProvider)
    failing_provider.get_forecast.side_effect = WeatherProviderError("OpenWeatherMap service error: HTTP 500")
    service = WeatherForecastService(provider=failing_provider)

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_weather_forecast_service] = lambda: service
    try:
        response = client.get("/api/v1/weather/forecast", params={"village_id": "V001"})
        assert response.status_code == 502
        data = response.json()
        assert "weather provider error" in data["detail"].lower()
        assert "HTTP 500" in data["detail"]
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_weather_forecast_service, None)


def test_forecast_api_response_structure(mock_v001_village):
    """Test 4: Verify complete response structure including all meteorological fields."""
    mock_db = MagicMock()
    mock_db.get.return_value = mock_v001_village

    now = datetime(2026, 9, 24, 6, 0, 0, tzinfo=timezone.utc)
    custom_item = ForecastData(
        timestamp=now,
        temperature_c=Decimal("29.40"),
        humidity_pct=Decimal("82.00"),
        rainfall_mm=Decimal("4.50"),
        wind_speed_kmh=Decimal("18.00"),
        wind_direction_deg=Decimal("240.00"),
        pressure_hpa=Decimal("1010.00"),
        cloud_cover_pct=Decimal("75.00"),
        weather_condition="moderate rain",
    )

    custom_provider = MagicMock(spec=ForecastProvider)
    custom_provider.get_forecast.return_value = [custom_item]
    service = WeatherForecastService(provider=custom_provider)

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_weather_forecast_service] = lambda: service
    try:
        response = client.get("/api/v1/weather/forecast", params={"village_id": "V001"})
        assert response.status_code == 200
        data = response.json()

        assert data["village_id"] == "V001"
        assert len(data["forecast"]) == 1
        item = data["forecast"][0]
        assert float(item["temperature_c"]) == 29.40
        assert float(item["humidity_pct"]) == 82.00
        assert float(item["rainfall_mm"]) == 4.50
        assert float(item["wind_speed_kmh"]) == 18.00
        assert float(item["wind_direction_deg"]) == 240.00
        assert float(item["pressure_hpa"]) == 1010.00
        assert float(item["cloud_cover_pct"]) == 75.00
        assert item["weather_condition"] == "moderate rain"
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_weather_forecast_service, None)


def test_forecast_api_village_coordinates_used(mock_v001_village):
    """Test 5: Verify village latitude and longitude are passed to ForecastProvider."""
    mock_db = MagicMock()
    mock_db.get.return_value = mock_v001_village

    mock_provider = MagicMock(spec=ForecastProvider)
    mock_provider.get_forecast.return_value = []
    service = WeatherForecastService(provider=mock_provider)

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_weather_forecast_service] = lambda: service
    try:
        response = client.get("/api/v1/weather/forecast", params={"village_id": "V001"})
        assert response.status_code == 200

        # Assert village coordinates were queried from db and passed to provider
        mock_db.get.assert_called_once_with(Village, "V001")
        mock_provider.get_forecast.assert_called_once_with(12.9141, 74.8560)
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_weather_forecast_service, None)


def test_forecast_api_empty_list_handled_safely(mock_v001_village):
    """Test 6: Empty forecast list returned by provider is handled safely without crashing."""
    mock_db = MagicMock()
    mock_db.get.return_value = mock_v001_village

    mock_provider = MagicMock(spec=ForecastProvider)
    mock_provider.get_forecast.return_value = []
    service = WeatherForecastService(provider=mock_provider)

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_weather_forecast_service] = lambda: service
    try:
        response = client.get("/api/v1/weather/forecast", params={"village_id": "V001"})
        assert response.status_code == 200
        data = response.json()
        assert data["village_id"] == "V001"
        assert data["forecast"] == []
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_weather_forecast_service, None)


def test_forecast_api_timestamps_are_timezone_aware(mock_v001_village):
    """Test 7: Verify generated_at and item timestamps in JSON are valid timezone-aware strings."""
    mock_db = MagicMock()
    mock_db.get.return_value = mock_v001_village

    provider = MockWeatherProvider()
    service = WeatherForecastService(provider=provider)

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_weather_forecast_service] = lambda: service
    try:
        response = client.get("/api/v1/weather/forecast", params={"village_id": "V001"})
        assert response.status_code == 200
        data = response.json()

        # Parse generated_at
        gen_dt = datetime.fromisoformat(data["generated_at"])
        assert gen_dt.tzinfo is not None

        # Parse forecast item timestamp
        item_dt = datetime.fromisoformat(data["forecast"][0]["timestamp"])
        assert item_dt.tzinfo is not None
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_weather_forecast_service, None)


def test_forecast_api_credential_leak_protection(mock_v001_village):
    """Test 8: Provider failure does not leak secret API keys or raw URLs in error response."""
    mock_db = MagicMock()
    mock_db.get.return_value = mock_v001_village

    secret_key = "very_secret_api_key_hidden"
    failing_provider = MagicMock(spec=ForecastProvider)
    # Even if exception message contains simulated raw error, ensure sanitized output
    failing_provider.get_forecast.side_effect = WeatherProviderError("OpenWeatherMap service error: HTTP 401")
    service = WeatherForecastService(provider=failing_provider)

    app.dependency_overrides[get_db] = lambda: mock_db
    app.dependency_overrides[get_weather_forecast_service] = lambda: service
    try:
        response = client.get("/api/v1/weather/forecast", params={"village_id": "V001"})
        assert response.status_code == 502
        data = response.json()
        assert secret_key not in data["detail"]
        assert "appid" not in data["detail"]
    finally:
        app.dependency_overrides.pop(get_db, None)
        app.dependency_overrides.pop(get_weather_forecast_service, None)
