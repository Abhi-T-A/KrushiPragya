"""Pure forecast aggregation service calculating 24h and 48h meteorological metrics."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import logging
from typing import Optional, Sequence

from app.schemas.weather import ForecastData, ForecastMetrics

logger = logging.getLogger(__name__)

CLOUDY_CONDITIONS = {"cloudy", "overcast"}
CLOUDY_COVER_THRESHOLD = Decimal("75.0")


def is_forecast_item_cloudy(item: ForecastData) -> bool:
    """Determine whether a single forecast point qualifies as cloudy or overcast."""
    cloud_cover = getattr(item, "cloud_cover_pct", None)
    if cloud_cover is not None:
        try:
            if Decimal(str(cloud_cover)) >= CLOUDY_COVER_THRESHOLD:
                return True
        except (ValueError, TypeError):
            pass

    condition = getattr(item, "weather_condition", None)
    if condition and str(condition).strip().lower() in CLOUDY_CONDITIONS:
        return True

    return False


def _ensure_utc(dt: datetime) -> datetime:
    """Normalize datetime to timezone-aware UTC."""
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class ForecastAggregationService:
    """Pure aggregation service that computes 24h and 48h ForecastMetrics from ForecastData."""

    @staticmethod
    def aggregate(
        forecast: Sequence[ForecastData],
        reference_time: Optional[datetime] = None,
    ) -> ForecastMetrics:
        """Aggregate forecast records into 24-hour and 48-hour meteorological metrics.

        Rules:
            1. Normalize reference_time to timezone-aware UTC (defaults to current UTC).
            2. Only forecast records in the future (timestamp >= reference_time) are evaluated.
            3. 24h window: reference_time <= timestamp <= reference_time + 24 hours.
            4. 48h window: reference_time <= timestamp <= reference_time + 48 hours.
            5. If no records exist in a window, all metrics for that window are None.
            6. Missing temperature, humidity, or wind values are ignored, never substituted by zero.
            7. Rainfall is summed across all records whose timestamp falls in the window.
            8. Cloudy hours use interval duration derived from consecutive records and
               calculate the exact overlap with the window. The final record contributes 0 hours.

        Args:
            forecast: Sequence of normalized ForecastData points.
            reference_time: Optional point-in-time anchor (defaults to current UTC).

        Returns:
            ForecastMetrics with calculated 24h and 48h aggregations.
        """
        # 1. Normalize reference_time
        if reference_time is None:
            ref_time = datetime.now(timezone.utc)
        else:
            ref_time = _ensure_utc(reference_time)

        # 2. Handle empty forecast
        if not forecast:
            return ForecastMetrics(
                reference_time=ref_time,
                rainfall_mm_24h=None,
                rainfall_mm_48h=None,
                max_temperature_c_24h=None,
                max_temperature_c_48h=None,
                min_temperature_c_24h=None,
                min_temperature_c_48h=None,
                avg_humidity_pct_24h=None,
                avg_humidity_pct_48h=None,
                max_wind_speed_kmh_24h=None,
                max_wind_speed_kmh_48h=None,
                cloudy_hours_24h=None,
                cloudy_hours_48h=None,
            )

        # Sort chronologically
        sorted_forecast = sorted(forecast, key=lambda f: _ensure_utc(f.timestamp))

        # Filter strictly to future records (timestamp >= reference_time)
        future_forecast = [f for f in sorted_forecast if _ensure_utc(f.timestamp) >= ref_time]

        window_24h_end = ref_time + timedelta(hours=24)
        window_48h_end = ref_time + timedelta(hours=48)

        items_24h = [f for f in future_forecast if _ensure_utc(f.timestamp) <= window_24h_end]
        items_48h = [f for f in future_forecast if _ensure_utc(f.timestamp) <= window_48h_end]

        # Calculate metrics for 24h window
        if not items_24h:
            rainfall_mm_24h = None
            max_temperature_c_24h = None
            min_temperature_c_24h = None
            avg_humidity_pct_24h = None
            max_wind_speed_kmh_24h = None
            cloudy_hours_24h = None
        else:
            # Rainfall: sum of valid values (missing normalized to 0)
            rain_vals = [getattr(f, "rainfall_mm", None) for f in items_24h]
            rainfall_mm_24h = sum(
                (Decimal(str(r)) if r is not None else Decimal("0.0") for r in rain_vals),
                Decimal("0.0"),
            )

            # Temperature: max and min (ignore nulls)
            temp_vals = [getattr(f, "temperature_c", None) for f in items_24h]
            valid_temps = [Decimal(str(t)) for t in temp_vals if t is not None]
            max_temperature_c_24h = max(valid_temps) if valid_temps else None
            min_temperature_c_24h = min(valid_temps) if valid_temps else None

            # Humidity: average (ignore nulls)
            hum_vals = [getattr(f, "humidity_pct", None) for f in items_24h]
            valid_hums = [Decimal(str(h)) for h in hum_vals if h is not None]
            avg_humidity_pct_24h = (
                round(sum(valid_hums) / Decimal(len(valid_hums)), 2) if valid_hums else None
            )

            # Wind speed: max (ignore nulls)
            wind_vals = [getattr(f, "wind_speed_kmh", None) for f in items_24h]
            valid_winds = [Decimal(str(w)) for w in wind_vals if w is not None]
            max_wind_speed_kmh_24h = max(valid_winds) if valid_winds else None

            # Cloudy hours: sum of overlap between consecutive cloudy intervals and window
            cloudy_seconds_24h = 0.0
            for i in range(len(future_forecast) - 1):
                f_curr = future_forecast[i]
                f_next = future_forecast[i + 1]
                t_start = _ensure_utc(f_curr.timestamp)
                t_end = _ensure_utc(f_next.timestamp)
                if t_end <= t_start:
                    continue

                if is_forecast_item_cloudy(f_curr):
                    overlap_start = max(t_start, ref_time)
                    overlap_end = min(t_end, window_24h_end)
                    if overlap_end > overlap_start:
                        cloudy_seconds_24h += (overlap_end - overlap_start).total_seconds()

            hours_24h = cloudy_seconds_24h / 3600.0
            cloudy_hours_24h = Decimal(str(round(hours_24h, 2)))

        # Calculate metrics for 48h window
        if not items_48h:
            rainfall_mm_48h = None
            max_temperature_c_48h = None
            min_temperature_c_48h = None
            avg_humidity_pct_48h = None
            max_wind_speed_kmh_48h = None
            cloudy_hours_48h = None
        else:
            # Rainfall: sum of valid values (missing normalized to 0)
            rain_vals_48 = [getattr(f, "rainfall_mm", None) for f in items_48h]
            rainfall_mm_48h = sum(
                (Decimal(str(r)) if r is not None else Decimal("0.0") for r in rain_vals_48),
                Decimal("0.0"),
            )

            # Temperature: max and min (ignore nulls)
            temp_vals_48 = [getattr(f, "temperature_c", None) for f in items_48h]
            valid_temps_48 = [Decimal(str(t)) for t in temp_vals_48 if t is not None]
            max_temperature_c_48h = max(valid_temps_48) if valid_temps_48 else None
            min_temperature_c_48h = min(valid_temps_48) if valid_temps_48 else None

            # Humidity: average (ignore nulls)
            hum_vals_48 = [getattr(f, "humidity_pct", None) for f in items_48h]
            valid_hums_48 = [Decimal(str(h)) for h in hum_vals_48 if h is not None]
            avg_humidity_pct_48h = (
                round(sum(valid_hums_48) / Decimal(len(valid_hums_48)), 2) if valid_hums_48 else None
            )

            # Wind speed: max (ignore nulls)
            wind_vals_48 = [getattr(f, "wind_speed_kmh", None) for f in items_48h]
            valid_winds_48 = [Decimal(str(w)) for w in wind_vals_48 if w is not None]
            max_wind_speed_kmh_48h = max(valid_winds_48) if valid_winds_48 else None

            # Cloudy hours: sum of overlap between consecutive cloudy intervals and window
            cloudy_seconds_48h = 0.0
            for i in range(len(future_forecast) - 1):
                f_curr = future_forecast[i]
                f_next = future_forecast[i + 1]
                t_start = _ensure_utc(f_curr.timestamp)
                t_end = _ensure_utc(f_next.timestamp)
                if t_end <= t_start:
                    continue

                if is_forecast_item_cloudy(f_curr):
                    overlap_start = max(t_start, ref_time)
                    overlap_end = min(t_end, window_48h_end)
                    if overlap_end > overlap_start:
                        cloudy_seconds_48h += (overlap_end - overlap_start).total_seconds()

            hours_48h = cloudy_seconds_48h / 3600.0
            cloudy_hours_48h = Decimal(str(round(hours_48h, 2)))

        return ForecastMetrics(
            reference_time=ref_time,
            rainfall_mm_24h=rainfall_mm_24h,
            rainfall_mm_48h=rainfall_mm_48h,
            max_temperature_c_24h=max_temperature_c_24h,
            max_temperature_c_48h=max_temperature_c_48h,
            min_temperature_c_24h=min_temperature_c_24h,
            min_temperature_c_48h=min_temperature_c_48h,
            avg_humidity_pct_24h=avg_humidity_pct_24h,
            avg_humidity_pct_48h=avg_humidity_pct_48h,
            max_wind_speed_kmh_24h=max_wind_speed_kmh_24h,
            max_wind_speed_kmh_48h=max_wind_speed_kmh_48h,
            cloudy_hours_24h=cloudy_hours_24h,
            cloudy_hours_48h=cloudy_hours_48h,
        )
