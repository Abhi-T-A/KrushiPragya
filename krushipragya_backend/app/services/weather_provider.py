from abc import ABC, abstractmethod
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging
import os
from typing import Any, Dict, Optional

import httpx

from app.core.config import settings
from app.schemas.weather import ForecastData, WeatherData

logger = logging.getLogger(__name__)

# Suppress internal httpx/httpcore request line logging to avoid leaking query parameters or keys
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)

_DEFAULT_API_KEY = object()


class WeatherProviderError(Exception):
    """Base exception raised for weather provider failures."""
    pass


class ForecastProvider(ABC):
    """Abstract interface for weather forecast data providers."""

    @abstractmethod
    def get_forecast(self, latitude: float, longitude: float) -> list[ForecastData]:
        """Fetch and return normalized forecast points for the specified coordinates.

        Args:
            latitude: Latitude coordinate (-90.0 to 90.0)
            longitude: Longitude coordinate (-180.0 to 180.0)

        Returns:
            list[ForecastData]: List of normalized forecast points.

        Raises:
            WeatherProviderError: When provider fails to fetch or parse forecast data.
        """
        ...


class WeatherProvider(ForecastProvider, ABC):
    """Abstract interface for external weather data providers (current and forecast)."""

    @abstractmethod
    def get_current_weather(self, latitude: float, longitude: float) -> WeatherData:
        """Fetch and return normalized current weather for the specified coordinates.

        Args:
            latitude: Latitude coordinate (-90.0 to 90.0)
            longitude: Longitude coordinate (-180.0 to 180.0)

        Returns:
            WeatherData: Normalized weather data schema.

        Raises:
            WeatherProviderError: When the provider fails to fetch or parse weather data.
        """
        ...


class OpenWeatherMapProvider(WeatherProvider):
    """OpenWeatherMap API implementation of WeatherProvider."""

    def __init__(
        self,
        api_key: Any = _DEFAULT_API_KEY,
        base_url: Optional[str] = None,
        http_client: Optional[httpx.Client] = None,
    ):
        if api_key is _DEFAULT_API_KEY:
            raw_key = os.getenv("OPENWEATHER_API_KEY") or settings.OPENWEATHER_API_KEY
            self.api_key = raw_key
        else:
            self.api_key = api_key
        if self.api_key and isinstance(self.api_key, str):
            self.api_key = self.api_key.strip().strip("'\"")
        self.base_url = (base_url or os.getenv("OPENWEATHER_BASE_URL") or settings.OPENWEATHER_BASE_URL).rstrip("/")
        self._client = http_client

    def _get_client(self) -> httpx.Client:
        if self._client is not None:
            return self._client
        return httpx.Client(timeout=10.0)

    def get_current_weather(self, latitude: float, longitude: float) -> WeatherData:
        if not self.api_key:
            raise WeatherProviderError(
                "OpenWeather API key is not configured. Set OPENWEATHER_API_KEY in environment or .env."
            )

        endpoint = f"{self.base_url}/weather"
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": "metric",
        }

        try:
            client = self._get_client()
            response = client.get(endpoint, params=params)
            response.raise_for_status()
            raw_data = response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            logger.error("OpenWeatherMap HTTP error received with status code %s", status_code)
            raise WeatherProviderError(f"OpenWeatherMap service error: HTTP {status_code}") from None
        except httpx.TimeoutException:
            logger.error("OpenWeatherMap request timed out")
            raise WeatherProviderError("OpenWeatherMap request timed out") from None
        except httpx.RequestError as e:
            logger.error("OpenWeatherMap network request failed: %s", type(e).__name__)
            raise WeatherProviderError(f"OpenWeatherMap network request failed: {type(e).__name__}") from None
        except WeatherProviderError:
            raise
        except Exception as e:
            logger.error("Unexpected error fetching from OpenWeatherMap: %s", type(e).__name__)
            raise WeatherProviderError(f"Failed to fetch weather: {type(e).__name__}") from None

        return self._normalize(raw_data)

    def _normalize(self, data: Dict[str, Any]) -> WeatherData:
        """Parse raw OpenWeatherMap response JSON into normalized WeatherData schema."""
        try:
            dt = data.get("dt")
            observed_at = (
                datetime.fromtimestamp(dt, tz=timezone.utc)
                if dt
                else datetime.now(timezone.utc)
            )

            main = data.get("main", {})
            temp = main.get("temp")
            temperature_c = Decimal(str(round(temp, 2))) if temp is not None else None

            humidity = main.get("humidity")
            humidity_pct = Decimal(str(round(humidity, 2))) if humidity is not None else None

            pressure = main.get("pressure")
            pressure_hpa = Decimal(str(round(pressure, 2))) if pressure is not None and pressure > 0 else None

            wind = data.get("wind", {})
            speed_ms = wind.get("speed")
            wind_speed_kmh = (
                Decimal(str(round(speed_ms * 3.6, 2)))
                if speed_ms is not None
                else None
            )

            deg = wind.get("deg")
            wind_direction_deg = Decimal(str(round(deg, 2))) if deg is not None else None

            clouds = data.get("clouds", {})
            cloud_all = clouds.get("all")
            cloud_cover_pct = Decimal(str(round(cloud_all, 2))) if cloud_all is not None else None

            # Rainfall accumulation (check 'rain' dict: '1h' or '3h')
            rain = data.get("rain", {})
            rain_mm = rain.get("1h", rain.get("3h", 0.0))
            rainfall_mm = Decimal(str(round(rain_mm, 2))) if rain_mm is not None and rain_mm >= 0 else Decimal("0.00")

            # Weather condition string
            weather_list = data.get("weather", [])
            condition = weather_list[0].get("main") if weather_list else None

            return WeatherData(
                observed_at=observed_at,
                temperature_c=temperature_c,
                humidity_pct=humidity_pct,
                rainfall_mm=rainfall_mm,
                wind_speed_kmh=wind_speed_kmh,
                wind_direction_deg=wind_direction_deg,
                pressure_hpa=pressure_hpa,
                cloud_cover_pct=cloud_cover_pct,
                weather_condition=condition,
                source="OpenWeatherMap",
            )
        except Exception as e:
            logger.error("Failed to parse OpenWeatherMap payload: %s", type(e).__name__)
            raise WeatherProviderError(f"Invalid OpenWeatherMap response payload: {type(e).__name__}") from None

    def get_forecast(self, latitude: float, longitude: float) -> list[ForecastData]:
        """Fetch and return normalized 5-day / 3-hour forecast for coordinates.

        Args:
            latitude: Latitude coordinate (-90.0 to 90.0)
            longitude: Longitude coordinate (-180.0 to 180.0)

        Returns:
            list[ForecastData]: Chronological sequence of 3-hour forecast items.

        Raises:
            WeatherProviderError: On missing configuration, HTTP failures, timeouts, or invalid payloads.
        """
        if not self.api_key:
            raise WeatherProviderError(
                "OpenWeather API key is not configured. Set OPENWEATHER_API_KEY in environment or .env."
            )

        endpoint = f"{self.base_url}/forecast"
        params = {
            "lat": latitude,
            "lon": longitude,
            "appid": self.api_key,
            "units": "metric",
        }

        try:
            client = self._get_client()
            response = client.get(endpoint, params=params)
            response.raise_for_status()
            raw_data = response.json()
        except httpx.HTTPStatusError as e:
            status_code = e.response.status_code
            logger.error("OpenWeatherMap forecast HTTP error received with status code %s", status_code)
            raise WeatherProviderError(f"OpenWeatherMap service error: HTTP {status_code}") from None
        except httpx.TimeoutException:
            logger.error("OpenWeatherMap forecast request timed out")
            raise WeatherProviderError("OpenWeatherMap request timed out") from None
        except httpx.RequestError as e:
            logger.error("OpenWeatherMap forecast network request failed: %s", type(e).__name__)
            raise WeatherProviderError(f"OpenWeatherMap network request failed: {type(e).__name__}") from None
        except WeatherProviderError:
            raise
        except Exception as e:
            logger.error("Unexpected error fetching forecast from OpenWeatherMap: %s", type(e).__name__)
            raise WeatherProviderError(f"Failed to fetch forecast: {type(e).__name__}") from None

        return self._normalize_forecast(raw_data)

    def _normalize_forecast(self, data: Dict[str, Any]) -> list[ForecastData]:
        """Parse raw OpenWeatherMap 5-day / 3-hour forecast response JSON into ForecastData items."""
        if not isinstance(data, dict):
            raise WeatherProviderError("Invalid OpenWeatherMap response payload: expected JSON object")

        raw_list = data.get("list")
        if raw_list is None or not isinstance(raw_list, list):
            logger.error("OpenWeatherMap forecast response is missing 'list' array")
            raise WeatherProviderError("Invalid OpenWeatherMap response payload: missing forecast list")

        results: list[ForecastData] = []
        for idx, item in enumerate(raw_list):
            if not isinstance(item, dict):
                logger.error("Malformed forecast item at index %s: expected dict", idx)
                raise WeatherProviderError(f"Malformed forecast item at index {idx}")

            try:
                dt = item.get("dt")
                if not dt:
                    raise ValueError("Missing 'dt' timestamp")
                timestamp = datetime.fromtimestamp(dt, tz=timezone.utc)

                main = item.get("main", {})
                temp = main.get("temp")
                if temp is None:
                    raise ValueError("Missing 'main.temp'")
                temperature_c = Decimal(str(round(float(temp), 2)))

                humidity = main.get("humidity")
                if humidity is None:
                    raise ValueError("Missing 'main.humidity'")
                humidity_pct = Decimal(str(round(float(humidity), 2)))

                pressure = main.get("pressure")
                pressure_hpa = (
                    Decimal(str(round(float(pressure), 2)))
                    if pressure is not None and float(pressure) > 0
                    else None
                )

                wind = item.get("wind", {})
                speed_ms = wind.get("speed")
                wind_speed_kmh = (
                    Decimal(str(round(float(speed_ms) * 3.6, 2)))
                    if speed_ms is not None
                    else Decimal("0.00")
                )

                deg = wind.get("deg")
                wind_direction_deg = (
                    Decimal(str(round(float(deg), 2)))
                    if deg is not None
                    else None
                )

                clouds = item.get("clouds", {})
                cloud_all = clouds.get("all")
                cloud_cover_pct = (
                    Decimal(str(round(float(cloud_all), 2)))
                    if cloud_all is not None
                    else None
                )

                # Rainfall 3h accumulation (absent means 0.00 mm for forecast intervals)
                rain = item.get("rain") or {}
                rain_3h = rain.get("3h", 0.0) if isinstance(rain, dict) else 0.0
                rainfall_mm = (
                    Decimal(str(round(float(rain_3h), 2)))
                    if rain_3h is not None and float(rain_3h) >= 0
                    else Decimal("0.00")
                )

                weather_list = item.get("weather", [])
                condition = None
                if weather_list and isinstance(weather_list, list) and isinstance(weather_list[0], dict):
                    condition = weather_list[0].get("description") or weather_list[0].get("main")

                results.append(
                    ForecastData(
                        timestamp=timestamp,
                        temperature_c=temperature_c,
                        humidity_pct=humidity_pct,
                        rainfall_mm=rainfall_mm,
                        wind_speed_kmh=wind_speed_kmh,
                        wind_direction_deg=wind_direction_deg,
                        pressure_hpa=pressure_hpa,
                        cloud_cover_pct=cloud_cover_pct,
                        weather_condition=condition,
                    )
                )
            except Exception as e:
                logger.error("Failed to parse forecast item at index %s: %s", idx, type(e).__name__)
                raise WeatherProviderError(f"Malformed forecast item at index {idx}: {type(e).__name__}") from None

        return results


class MockWeatherProvider(WeatherProvider):
    """Deterministic mock weather provider for testing and local development."""

    def __init__(self, default_data: Optional[Dict[str, Any]] = None):
        self.default_data = default_data or {}

    def get_current_weather(self, latitude: float, longitude: float) -> WeatherData:
        now = datetime.now(timezone.utc)
        return WeatherData(
            observed_at=self.default_data.get("observed_at", now),
            temperature_c=self.default_data.get("temperature_c", Decimal("28.50")),
            humidity_pct=self.default_data.get("humidity_pct", Decimal("75.00")),
            rainfall_mm=self.default_data.get("rainfall_mm", Decimal("2.40")),
            wind_speed_kmh=self.default_data.get("wind_speed_kmh", Decimal("12.50")),
            wind_direction_deg=self.default_data.get("wind_direction_deg", Decimal("210.00")),
            pressure_hpa=self.default_data.get("pressure_hpa", Decimal("1012.00")),
            cloud_cover_pct=self.default_data.get("cloud_cover_pct", Decimal("40.00")),
            weather_condition=self.default_data.get("weather_condition", "Partly Cloudy"),
            source="MockWeatherProvider",
        )

    def get_forecast(self, latitude: float, longitude: float) -> list[ForecastData]:
        """Generate deterministic mock forecast points at 3-hour intervals."""
        if "forecast" in self.default_data:
            return self.default_data["forecast"]

        now = datetime.now(timezone.utc)
        items: list[ForecastData] = []
        for i in range(40):
            fc_time = now + timedelta(hours=3 * (i + 1))
            items.append(
                ForecastData(
                    timestamp=fc_time,
                    temperature_c=Decimal("27.50"),
                    humidity_pct=Decimal("78.00"),
                    rainfall_mm=Decimal("1.20") if i % 2 == 0 else Decimal("0.00"),
                    wind_speed_kmh=Decimal("14.00"),
                    wind_direction_deg=Decimal("220.00"),
                    pressure_hpa=Decimal("1011.00"),
                    cloud_cover_pct=Decimal("60.00"),
                    weather_condition="light rain" if i % 2 == 0 else "scattered clouds",
                )
            )
        return items


def get_weather_provider(provider_name: Optional[str] = None) -> WeatherProvider:
    """Factory creating weather provider instance based on settings."""
    chosen = (provider_name or os.getenv("WEATHER_PROVIDER") or settings.WEATHER_PROVIDER).lower()
    if chosen == "openweather":
        return OpenWeatherMapProvider()
    if chosen == "mock":
        return MockWeatherProvider()
    raise ValueError(f"Unknown weather provider: {chosen}")
