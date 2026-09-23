from datetime import datetime, timezone
from decimal import Decimal
from unittest.mock import MagicMock
import httpx
import pytest

from app.schemas.weather import ForecastData
from app.services.weather_provider import (
    ForecastProvider,
    MockWeatherProvider,
    OpenWeatherMapProvider,
    WeatherProvider,
    WeatherProviderError,
    get_weather_provider,
)


@pytest.fixture
def mock_openweather_forecast_payload():
    """Return a standard OpenWeather 5-day / 3-hour forecast response payload with multiple intervals."""
    return {
        "cod": "200",
        "message": 0,
        "cnt": 3,
        "list": [
            {
                "dt": 1727136000,  # 2024-09-24 00:00:00 UTC
                "main": {
                    "temp": 28.45,
                    "feels_like": 31.20,
                    "temp_min": 28.00,
                    "temp_max": 28.50,
                    "pressure": 1010,
                    "humidity": 82,
                },
                "weather": [
                    {
                        "id": 500,
                        "main": "Rain",
                        "description": "light rain",
                        "icon": "10n",
                    }
                ],
                "clouds": {"all": 75},
                "wind": {"speed": 4.5, "deg": 230},
                "rain": {"3h": 3.85},
            },
            {
                "dt": 1727146800,  # 2024-09-24 03:00:00 UTC
                "main": {
                    "temp": 29.80,
                    "feels_like": 33.10,
                    "pressure": 1009,
                    "humidity": 78,
                },
                "weather": [
                    {
                        "id": 803,
                        "main": "Clouds",
                        "description": "broken clouds",
                        "icon": "04d",
                    }
                ],
                "clouds": {"all": 60},
                "wind": {"speed": 5.0, "deg": 240},
                # Notice: 'rain' key intentionally omitted for dry interval
            },
            {
                "dt": 1727157600,  # 2024-09-24 06:00:00 UTC
                "main": {
                    "temp": 31.00,
                    "pressure": 1008,
                    "humidity": 70,
                },
                "weather": [
                    {
                        "id": 801,
                        "main": "Clouds",
                        "description": "few clouds",
                        "icon": "02d",
                    }
                ],
                "clouds": {"all": 25},
                "wind": {"speed": 3.0, "deg": 210},
                "rain": {},  # Empty rain dict
            },
        ],
        "city": {
            "id": 1264527,
            "name": "Mangaluru",
            "coord": {"lat": 12.9141, "lon": 74.856},
            "country": "IN",
        },
    }


def test_forecast_parsing_success(mock_openweather_forecast_payload):
    """Test 1: Verify successful parsing of multi-interval OpenWeather forecast."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = mock_openweather_forecast_payload
    mock_response.raise_for_status.return_value = None

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response

    provider = OpenWeatherMapProvider(api_key="valid_dummy_key", http_client=mock_client)
    items = provider.get_forecast(12.9141, 74.8560)

    # 1. Total items
    assert len(items) == 3

    # 2. First interval verification (rain present)
    item0 = items[0]
    assert isinstance(item0, ForecastData)
    assert item0.timestamp == datetime.fromtimestamp(1727136000, tz=timezone.utc)
    assert item0.timestamp.tzinfo == timezone.utc
    assert item0.temperature_c == Decimal("28.45")
    assert item0.humidity_pct == Decimal("82")
    assert item0.pressure_hpa == Decimal("1010")
    assert item0.cloud_cover_pct == Decimal("75")
    # 4.5 m/s * 3.6 = 16.20 km/h
    assert item0.wind_speed_kmh == Decimal("16.20")
    assert item0.wind_direction_deg == Decimal("230")
    assert item0.rainfall_mm == Decimal("3.85")
    assert item0.weather_condition == "light rain"

    # 3. Second interval (rain key absent -> rainfall_mm = 0)
    item1 = items[1]
    assert item1.temperature_c == Decimal("29.80")
    assert item1.humidity_pct == Decimal("78")
    # 5.0 m/s * 3.6 = 18.00 km/h
    assert item1.wind_speed_kmh == Decimal("18.00")
    assert item1.rainfall_mm == Decimal("0.00")
    assert item1.weather_condition == "broken clouds"

    # 4. Third interval (empty rain dict -> rainfall_mm = 0)
    item2 = items[2]
    assert item2.rainfall_mm == Decimal("0.00")
    assert item2.weather_condition == "few clouds"


def test_forecast_missing_rain_field():
    """Test 2: When rain or rain.3h is absent, rainfall_mm defaults to 0.00 mm."""
    payload = {
        "list": [
            {
                "dt": 1727136000,
                "main": {"temp": 26.50, "humidity": 75},
                "wind": {"speed": 2.5},
                "weather": [{"description": "clear sky"}],
            }
        ]
    }
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.json.return_value = payload
    mock_response.raise_for_status.return_value = None

    mock_client = MagicMock()
    mock_client.get.return_value = mock_response

    provider = OpenWeatherMapProvider(api_key="valid_dummy_key", http_client=mock_client)
    items = provider.get_forecast(12.9141, 74.8560)
    assert len(items) == 1
    assert items[0].rainfall_mm == Decimal("0.00")


def test_forecast_http_401():
    """Test 3: HTTP 401 raises WeatherProviderError without credential leak."""
    secret_key = "super_secret_test_key_xyz"
    mock_response = MagicMock(spec=httpx.Response)
    mock_response.status_code = 401
    mock_response.text = '{"cod":401, "message": "Invalid API key"}'

    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.HTTPStatusError(
        "401 Unauthorized",
        request=MagicMock(url=f"https://api.openweathermap.org/data/2.5/forecast?appid={secret_key}"),
        response=mock_response,
    )

    provider = OpenWeatherMapProvider(api_key=secret_key, http_client=mock_client)
    with pytest.raises(WeatherProviderError) as exc_info:
        provider.get_forecast(12.9141, 74.8560)

    err_msg = str(exc_info.value)
    assert "HTTP 401" in err_msg
    assert secret_key not in err_msg


def test_forecast_timeout():
    """Test 4: Request timeout raises WeatherProviderError without credential leak."""
    secret_key = "super_secret_test_key_xyz"
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.TimeoutException("Timed out connecting")

    provider = OpenWeatherMapProvider(api_key=secret_key, http_client=mock_client)
    with pytest.raises(WeatherProviderError) as exc_info:
        provider.get_forecast(12.9141, 74.8560)

    err_msg = str(exc_info.value)
    assert "timed out" in err_msg.lower()
    assert secret_key not in err_msg


def test_forecast_network_failure():
    """Verify network connection errors raise WeatherProviderError."""
    mock_client = MagicMock()
    mock_client.get.side_effect = httpx.ConnectError("Failed DNS resolution")

    provider = OpenWeatherMapProvider(api_key="test_key", http_client=mock_client)
    with pytest.raises(WeatherProviderError) as exc_info:
        provider.get_forecast(12.9141, 74.8560)

    assert "network request failed" in str(exc_info.value).lower()


def test_forecast_malformed_responses():
    """Test 5: Malformed payloads raise WeatherProviderError."""
    mock_client = MagicMock()

    # Case A: Missing 'list'
    mock_resp1 = MagicMock()
    mock_resp1.status_code = 200
    mock_resp1.json.return_value = {"city": {"name": "Test"}}
    mock_resp1.raise_for_status.return_value = None
    mock_client.get.return_value = mock_resp1

    provider = OpenWeatherMapProvider(api_key="test_key", http_client=mock_client)
    with pytest.raises(WeatherProviderError) as exc1:
        provider.get_forecast(12.9141, 74.8560)
    assert "missing forecast list" in str(exc1.value).lower()

    # Case B: Non-dict payload
    mock_resp2 = MagicMock()
    mock_resp2.status_code = 200
    mock_resp2.json.return_value = ["not a dict"]
    mock_client.get.return_value = mock_resp2
    with pytest.raises(WeatherProviderError) as exc2:
        provider.get_forecast(12.9141, 74.8560)
    assert "expected json object" in str(exc2.value).lower()

    # Case C: Item missing required 'dt' timestamp
    mock_resp3 = MagicMock()
    mock_resp3.status_code = 200
    mock_resp3.json.return_value = {"list": [{"main": {"temp": 25.0, "humidity": 70}}]}
    mock_client.get.return_value = mock_resp3
    with pytest.raises(WeatherProviderError) as exc3:
        provider.get_forecast(12.9141, 74.8560)
    assert "malformed forecast item" in str(exc3.value).lower()

    # Case D: Item is not a dict
    mock_resp4 = MagicMock()
    mock_resp4.status_code = 200
    mock_resp4.json.return_value = {"list": ["corrupted_item"]}
    mock_client.get.return_value = mock_resp4
    with pytest.raises(WeatherProviderError) as exc4:
        provider.get_forecast(12.9141, 74.8560)
    assert "malformed forecast item at index 0" in str(exc4.value).lower()


def test_forecast_missing_api_key():
    """Test 6: Missing API key raises controlled WeatherProviderError."""
    provider = OpenWeatherMapProvider(api_key=None)
    with pytest.raises(WeatherProviderError) as exc_info:
        provider.get_forecast(12.9141, 74.8560)
    assert "OpenWeather API key is not configured" in str(exc_info.value)


def test_forecast_provider_abstraction_and_mock():
    """Test 7: Verify ForecastProvider abstraction and MockWeatherProvider behavior."""
    mock_provider = MockWeatherProvider()

    # 1. Type hierarchy verification
    assert isinstance(mock_provider, ForecastProvider)
    assert isinstance(mock_provider, WeatherProvider)

    ow_provider = OpenWeatherMapProvider(api_key="dummy_key")
    assert isinstance(ow_provider, ForecastProvider)
    assert isinstance(ow_provider, WeatherProvider)

    # 2. Mock forecast execution
    forecast_items = mock_provider.get_forecast(12.9141, 74.8560)
    assert len(forecast_items) == 40
    for item in forecast_items:
        assert isinstance(item, ForecastData)
        assert item.timestamp.tzinfo == timezone.utc
        assert item.temperature_c == Decimal("27.50")
        assert item.humidity_pct == Decimal("78.00")
        assert item.wind_speed_kmh == Decimal("14.00")
        assert item.weather_condition in ("light rain", "scattered clouds")

    # 3. Factory selection verification
    selected_mock = get_weather_provider("mock")
    assert isinstance(selected_mock, ForecastProvider)
    selected_ow = get_weather_provider("openweather")
    assert isinstance(selected_ow, ForecastProvider)
