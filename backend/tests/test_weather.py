from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
import pytest
from pydantic import ValidationError

from app.schemas.weather import WeatherData
from app.services.weather_provider import (
    MockWeatherProvider,
    OpenWeatherMapProvider,
    WeatherProviderError,
)
from app.services.weather_service import WeatherService


def test_valid_weather_data():
    """Verify WeatherData schema validates valid meteorological fields."""
    now = datetime.now(timezone.utc)
    data = WeatherData(
        observed_at=now,
        temperature_c=Decimal("29.40"),
        humidity_pct=Decimal("82.50"),
        rainfall_mm=Decimal("14.20"),
        wind_speed_kmh=Decimal("18.50"),
        wind_direction_deg=Decimal("240.00"),
        pressure_hpa=Decimal("1010.50"),
        cloud_cover_pct=Decimal("75.00"),
        weather_condition="Moderate Rain",
        source="TestProvider",
    )
    assert data.temperature_c == Decimal("29.40")
    assert data.humidity_pct == Decimal("82.50")
    assert data.rainfall_mm == Decimal("14.20")
    assert data.wind_speed_kmh == Decimal("18.50")
    assert data.wind_direction_deg == Decimal("240.00")
    assert data.pressure_hpa == Decimal("1010.50")
    assert data.cloud_cover_pct == Decimal("75.00")
    assert data.weather_condition == "Moderate Rain"
    assert data.source == "TestProvider"


def test_invalid_humidity():
    """Verify validation fails when humidity is negative or exceeds 100%."""
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        WeatherData(observed_at=now, humidity_pct=Decimal("-5.00"), source="Test")

    with pytest.raises(ValidationError):
        WeatherData(observed_at=now, humidity_pct=Decimal("100.01"), source="Test")


def test_invalid_rainfall():
    """Verify validation fails when rainfall is negative."""
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        WeatherData(observed_at=now, rainfall_mm=Decimal("-0.01"), source="Test")


def test_invalid_wind_direction():
    """Verify validation fails when wind direction is outside 0-360 degrees."""
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        WeatherData(observed_at=now, wind_direction_deg=Decimal("-1.00"), source="Test")

    with pytest.raises(ValidationError):
        WeatherData(observed_at=now, wind_direction_deg=Decimal("360.50"), source="Test")


def test_invalid_pressure():
    """Verify validation fails when atmospheric pressure is non-positive."""
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        WeatherData(observed_at=now, pressure_hpa=Decimal("0.00"), source="Test")

    with pytest.raises(ValidationError):
        WeatherData(observed_at=now, pressure_hpa=Decimal("-10.00"), source="Test")


def test_invalid_cloud_cover():
    """Verify validation fails when cloud cover is outside 0-100%."""
    now = datetime.now(timezone.utc)
    with pytest.raises(ValidationError):
        WeatherData(observed_at=now, cloud_cover_pct=Decimal("-1.00"), source="Test")

    with pytest.raises(ValidationError):
        WeatherData(observed_at=now, cloud_cover_pct=Decimal("105.00"), source="Test")


def test_mock_weather_provider():
    """Verify MockWeatherProvider returns valid deterministic normalized WeatherData."""
    provider = MockWeatherProvider()
    data = provider.get_current_weather(12.9141, 74.8560)
    assert isinstance(data, WeatherData)
    assert data.source == "MockWeatherProvider"
    assert data.temperature_c == Decimal("28.50")
    assert data.humidity_pct == Decimal("75.00")
    assert data.rainfall_mm == Decimal("2.40")
    assert data.pressure_hpa == Decimal("1012.00")


def test_openweathermap_provider_missing_key():
    """Verify OpenWeatherMapProvider raises WeatherProviderError when API key is missing."""
    provider = OpenWeatherMapProvider(api_key=None)
    with pytest.raises(WeatherProviderError) as exc_info:
        provider.get_current_weather(12.9141, 74.8560)
    assert "OpenWeather API key is not configured" in str(exc_info.value)


def test_openweathermap_provider_mocked_http():
    """Verify OpenWeatherMapProvider correctly normalizes external JSON response using mocked HTTP client."""
    mock_payload = {
        "coord": {"lon": 74.856, "lat": 12.9141},
        "weather": [{"id": 500, "main": "Rain", "description": "light rain"}],
        "main": {
            "temp": 27.85,
            "pressure": 1008,
            "humidity": 88,
        },
        "wind": {"speed": 4.5, "deg": 190},
        "clouds": {"all": 80},
        "rain": {"1h": 3.2},
        "dt": 1695484800,
    }

    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_payload
    mock_response.raise_for_status.return_value = None

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response

    provider = OpenWeatherMapProvider(api_key="test_dummy_key", http_client=mock_client)
    data = provider.get_current_weather(12.9141, 74.8560)

    assert data.source == "OpenWeatherMap"
    assert data.temperature_c == Decimal("27.85")
    assert data.humidity_pct == Decimal("88")
    assert data.pressure_hpa == Decimal("1008")
    # 4.5 m/s * 3.6 = 16.20 km/h
    assert data.wind_speed_kmh == Decimal("16.20")
    assert data.wind_direction_deg == Decimal("190")
    assert data.cloud_cover_pct == Decimal("80")
    assert data.rainfall_mm == Decimal("3.20")
    assert data.weather_condition == "Rain"


def test_weather_service_fetch_and_to_orm():
    """Verify WeatherService fetches normalized data and converts to ORM without persisting."""
    provider = MockWeatherProvider()
    service = WeatherService(provider=provider)

    data = service.fetch_weather(12.9141, 74.8560)
    assert isinstance(data, WeatherData)

    orm_obj = service.to_orm(village_id="V001", data=data)
    assert orm_obj.village_id == "V001"
    assert orm_obj.temperature_c == data.temperature_c
    assert orm_obj.humidity_pct == data.humidity_pct
    assert orm_obj.rainfall_mm == data.rainfall_mm
    assert orm_obj.source == "MockWeatherProvider"


def test_weather_service_save_observation_mocked():
    """Verify WeatherService persists observation to database session when requested."""
    provider = MockWeatherProvider()
    service = WeatherService(provider=provider)

    mock_db = MagicMock()
    data, orm_obj = service.get_and_record_weather(
        db=mock_db,
        village_id="V001",
        latitude=12.9141,
        longitude=74.8560,
        persist=True,
    )

    assert orm_obj is not None
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()


def test_weather_service_no_persist():
    """Verify WeatherService does not touch database session when persist=False."""
    provider = MockWeatherProvider()
    service = WeatherService(provider=provider)

    mock_db = MagicMock()
    data, orm_obj = service.get_and_record_weather(
        db=mock_db,
        village_id="V001",
        latitude=12.9141,
        longitude=74.8560,
        persist=False,
    )

    assert orm_obj is None
    mock_db.add.assert_not_called()
    mock_db.commit.assert_not_called()
