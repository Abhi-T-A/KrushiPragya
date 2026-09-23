"""Unit tests for the pure ForecastAggregationService and ForecastMetrics schema."""

from datetime import datetime, timedelta, timezone
from decimal import Decimal
import pytest

from app.schemas.weather import ForecastData, ForecastMetrics
from app.services.forecast_aggregation_service import (
    ForecastAggregationService,
    is_forecast_item_cloudy,
)


def _make_forecast_item(
    dt: datetime,
    temp: float | None = 25.0,
    humidity: float | None = 70.0,
    rainfall: float | None = 0.0,
    wind: float | None = 10.0,
    cloud_cover: float | None = 20.0,
    condition: str | None = "Clear",
) -> ForecastData:
    """Helper to build a ForecastData point with specified parameters."""
    return ForecastData(
        timestamp=dt,
        temperature_c=Decimal(str(temp)) if temp is not None else None,
        humidity_pct=Decimal(str(humidity)) if humidity is not None else None,
        rainfall_mm=Decimal(str(rainfall)) if rainfall is not None else Decimal("0.0"),
        wind_speed_kmh=Decimal(str(wind)) if wind is not None else None,
        cloud_cover_pct=Decimal(str(cloud_cover)) if cloud_cover is not None else None,
        weather_condition=condition,
    )


# 1. Empty forecast
def test_empty_forecast():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    metrics = ForecastAggregationService.aggregate([], reference_time=ref)

    assert isinstance(metrics, ForecastMetrics)
    assert metrics.reference_time == ref
    assert metrics.rainfall_mm_24h is None
    assert metrics.rainfall_mm_48h is None
    assert metrics.max_temperature_c_24h is None
    assert metrics.max_temperature_c_48h is None
    assert metrics.min_temperature_c_24h is None
    assert metrics.min_temperature_c_48h is None
    assert metrics.avg_humidity_pct_24h is None
    assert metrics.avg_humidity_pct_48h is None
    assert metrics.max_wind_speed_kmh_24h is None
    assert metrics.max_wind_speed_kmh_48h is None
    assert metrics.cloudy_hours_24h is None
    assert metrics.cloudy_hours_48h is None


# 2. Single forecast item
def test_single_forecast_item():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    item = _make_forecast_item(
        ref + timedelta(hours=3),
        temp=28.5,
        humidity=75.0,
        rainfall=3.2,
        wind=16.0,
        cloud_cover=90.0,
        condition="cloudy",
    )
    metrics = ForecastAggregationService.aggregate([item], reference_time=ref)

    assert metrics.rainfall_mm_24h == Decimal("3.2")
    assert metrics.rainfall_mm_48h == Decimal("3.2")
    assert metrics.max_temperature_c_24h == Decimal("28.5")
    assert metrics.min_temperature_c_24h == Decimal("28.5")
    assert metrics.avg_humidity_pct_24h == Decimal("75.0")
    assert metrics.max_wind_speed_kmh_24h == Decimal("16.0")
    # Single item cannot establish an interval duration -> 0 hours
    assert metrics.cloudy_hours_24h == Decimal("0.0")
    assert metrics.cloudy_hours_48h == Decimal("0.0")


# 3. 24h rainfall sum
def test_24h_rainfall_sum():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    items = [
        _make_forecast_item(ref + timedelta(hours=3), rainfall=2.5),
        _make_forecast_item(ref + timedelta(hours=6), rainfall=3.5),
        _make_forecast_item(ref + timedelta(hours=24), rainfall=1.0),
        _make_forecast_item(ref + timedelta(hours=27), rainfall=10.0),  # outside 24h
    ]
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    assert metrics.rainfall_mm_24h == Decimal("7.0")


# 4. 48h rainfall sum
def test_48h_rainfall_sum():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    items = [
        _make_forecast_item(ref + timedelta(hours=3), rainfall=2.5),
        _make_forecast_item(ref + timedelta(hours=27), rainfall=4.5),
        _make_forecast_item(ref + timedelta(hours=48), rainfall=1.0),
        _make_forecast_item(ref + timedelta(hours=50), rainfall=20.0),  # outside 48h
    ]
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    assert metrics.rainfall_mm_48h == Decimal("8.0")


# 5. 24h max/min temperature
def test_24h_max_min_temperature():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    items = [
        _make_forecast_item(ref + timedelta(hours=3), temp=20.0),
        _make_forecast_item(ref + timedelta(hours=6), temp=32.5),
        _make_forecast_item(ref + timedelta(hours=9), temp=24.0),
        _make_forecast_item(ref + timedelta(hours=30), temp=45.0),  # outside 24h
    ]
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    assert metrics.max_temperature_c_24h == Decimal("32.5")
    assert metrics.min_temperature_c_24h == Decimal("20.0")


# 6. 48h max/min temperature
def test_48h_max_min_temperature():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    items = [
        _make_forecast_item(ref + timedelta(hours=3), temp=22.0),
        _make_forecast_item(ref + timedelta(hours=26), temp=35.0),
        _make_forecast_item(ref + timedelta(hours=40), temp=18.0),
        _make_forecast_item(ref + timedelta(hours=52), temp=50.0),  # outside 48h
    ]
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    assert metrics.max_temperature_c_48h == Decimal("35.0")
    assert metrics.min_temperature_c_48h == Decimal("18.0")


# 7. 24h average humidity
def test_24h_average_humidity():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    items = [
        _make_forecast_item(ref + timedelta(hours=3), humidity=60.0),
        _make_forecast_item(ref + timedelta(hours=6), humidity=80.0),
        _make_forecast_item(ref + timedelta(hours=9), humidity=70.0),
        _make_forecast_item(ref + timedelta(hours=30), humidity=10.0),  # outside 24h
    ]
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    assert metrics.avg_humidity_pct_24h == Decimal("70.0")


# 8. 48h average humidity
def test_48h_average_humidity():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    items = [
        _make_forecast_item(ref + timedelta(hours=3), humidity=50.0),
        _make_forecast_item(ref + timedelta(hours=30), humidity=90.0),
        _make_forecast_item(ref + timedelta(hours=50), humidity=20.0),  # outside 48h
    ]
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    assert metrics.avg_humidity_pct_48h == Decimal("70.0")


# 9. 24h maximum wind
def test_24h_maximum_wind():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    items = [
        _make_forecast_item(ref + timedelta(hours=3), wind=12.0),
        _make_forecast_item(ref + timedelta(hours=6), wind=28.5),
        _make_forecast_item(ref + timedelta(hours=9), wind=18.0),
        _make_forecast_item(ref + timedelta(hours=30), wind=55.0),  # outside 24h
    ]
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    assert metrics.max_wind_speed_kmh_24h == Decimal("28.5")


# 10. 48h maximum wind
def test_48h_maximum_wind():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    items = [
        _make_forecast_item(ref + timedelta(hours=3), wind=15.0),
        _make_forecast_item(ref + timedelta(hours=30), wind=38.0),
        _make_forecast_item(ref + timedelta(hours=55), wind=70.0),  # outside 48h
    ]
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    assert metrics.max_wind_speed_kmh_48h == Decimal("38.0")


# 11. Cloudy hours using cloud_cover_pct >= 75
def test_cloudy_hours_using_cloud_cover_pct():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    items = [
        _make_forecast_item(ref + timedelta(hours=0), cloud_cover=75.0, condition="Clear"),
        _make_forecast_item(ref + timedelta(hours=3), cloud_cover=85.0, condition="Sunny"),
        _make_forecast_item(ref + timedelta(hours=6), cloud_cover=50.0, condition="Clear"),
    ]
    # Interval 0: [0h, 3h) -> cloudy (3h)
    # Interval 1: [3h, 6h) -> cloudy (3h)
    # Interval 2: [6h, ...] -> final record (0h)
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    assert metrics.cloudy_hours_24h == Decimal("6.0")


# 12. Cloudy hours using 'cloudy' condition
def test_cloudy_hours_using_cloudy_condition():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    items = [
        _make_forecast_item(ref + timedelta(hours=0), cloud_cover=40.0, condition="Cloudy"),
        _make_forecast_item(ref + timedelta(hours=3), cloud_cover=50.0, condition="cloudy"),
        _make_forecast_item(ref + timedelta(hours=6), cloud_cover=20.0, condition="clear"),
    ]
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    assert metrics.cloudy_hours_24h == Decimal("6.0")


# 13. Cloudy hours using 'overcast' condition
def test_cloudy_hours_using_overcast_condition():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    items = [
        _make_forecast_item(ref + timedelta(hours=0), cloud_cover=0.0, condition="Overcast"),
        _make_forecast_item(ref + timedelta(hours=3), cloud_cover=0.0, condition="overcast"),
        _make_forecast_item(ref + timedelta(hours=6), cloud_cover=0.0, condition="sunny"),
    ]
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    assert metrics.cloudy_hours_24h == Decimal("6.0")


# 14. Non-cloudy forecast
def test_non_cloudy_forecast():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    items = [
        _make_forecast_item(ref + timedelta(hours=0), cloud_cover=30.0, condition="sunny"),
        _make_forecast_item(ref + timedelta(hours=3), cloud_cover=50.0, condition="partly cloudy"),
        _make_forecast_item(ref + timedelta(hours=6), cloud_cover=10.0, condition="clear"),
    ]
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    assert metrics.cloudy_hours_24h == Decimal("0.0")
    assert metrics.cloudy_hours_48h == Decimal("0.0")


# 15. Mixed cloudy/non-cloudy intervals
def test_mixed_cloudy_non_cloudy_intervals():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    items = [
        _make_forecast_item(ref + timedelta(hours=0), cloud_cover=80.0),   # cloudy: 3h
        _make_forecast_item(ref + timedelta(hours=3), cloud_cover=20.0),   # clear: 0h
        _make_forecast_item(ref + timedelta(hours=6), condition="cloudy"),  # cloudy: 3h
        _make_forecast_item(ref + timedelta(hours=9), cloud_cover=10.0),   # final record: 0h
    ]
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    assert metrics.cloudy_hours_24h == Decimal("6.0")


# 16. Exact 24-hour boundary
def test_exact_24_hour_boundary():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    items = [
        _make_forecast_item(ref + timedelta(hours=0), rainfall=1.0, temp=20.0, cloud_cover=80.0),
        _make_forecast_item(ref + timedelta(hours=24), rainfall=2.0, temp=25.0, cloud_cover=80.0),
        _make_forecast_item(ref + timedelta(hours=27), rainfall=4.0, temp=30.0, cloud_cover=10.0),
    ]
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    # The record at exact 24h is included in 24h metrics (<= 24h)
    assert metrics.rainfall_mm_24h == Decimal("3.0")
    assert metrics.max_temperature_c_24h == Decimal("25.0")
    # For cloudy hours:
    # Interval 0 [0h, 24h): overlap with [0, 24h] is 24h.
    # Interval 1 [24h, 27h): overlap with [0, 24h] is 0h!
    # Overlap with [0, 48h] is 24h + 3h = 27h.
    assert metrics.cloudy_hours_24h == Decimal("24.0")
    assert metrics.cloudy_hours_48h == Decimal("27.0")


# 17. Exact 48-hour boundary
def test_exact_48_hour_boundary():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    items = [
        _make_forecast_item(ref + timedelta(hours=0), rainfall=1.0),
        _make_forecast_item(ref + timedelta(hours=48), rainfall=5.0),
        _make_forecast_item(ref + timedelta(hours=51), rainfall=10.0),
    ]
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    # Record at 48h is included in 48h metrics (<= 48h)
    assert metrics.rainfall_mm_48h == Decimal("6.0")


# 18. Forecast records before reference_time are ignored
def test_forecast_records_before_reference_time_ignored():
    ref = datetime(2026, 9, 24, 12, 0, tzinfo=timezone.utc)
    items = [
        _make_forecast_item(ref - timedelta(hours=6), rainfall=100.0, temp=60.0, cloud_cover=100.0),
        _make_forecast_item(ref - timedelta(hours=1), rainfall=50.0, temp=55.0, cloud_cover=100.0),
        _make_forecast_item(ref + timedelta(hours=3), rainfall=2.0, temp=25.0, cloud_cover=0.0),
        _make_forecast_item(ref + timedelta(hours=6), rainfall=3.0, temp=28.0, cloud_cover=0.0),
    ]
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    assert metrics.rainfall_mm_24h == Decimal("5.0")
    assert metrics.max_temperature_c_24h == Decimal("28.0")
    assert metrics.cloudy_hours_24h == Decimal("0.0")


# 19. Missing humidity/temperature/wind values ignored
def test_missing_humidity_temperature_wind_values():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    items = [
        _make_forecast_item(ref + timedelta(hours=3), temp=None, humidity=None, wind=None, rainfall=2.0),
        _make_forecast_item(ref + timedelta(hours=6), temp=28.0, humidity=75.0, wind=15.0, rainfall=3.0),
        _make_forecast_item(ref + timedelta(hours=9), temp=None, humidity=None, wind=None, rainfall=0.0),
    ]
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    assert metrics.rainfall_mm_24h == Decimal("5.0")
    assert metrics.max_temperature_c_24h == Decimal("28.0")
    assert metrics.min_temperature_c_24h == Decimal("28.0")
    assert metrics.avg_humidity_pct_24h == Decimal("75.0")
    assert metrics.max_wind_speed_kmh_24h == Decimal("15.0")


# 20. Missing data results in None rather than zero
def test_missing_data_results_in_none_rather_than_zero():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    items = [
        _make_forecast_item(ref + timedelta(hours=3), temp=None, humidity=None, wind=None, rainfall=0.0),
        _make_forecast_item(ref + timedelta(hours=6), temp=None, humidity=None, wind=None, rainfall=0.0),
    ]
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    assert metrics.max_temperature_c_24h is None
    assert metrics.min_temperature_c_24h is None
    assert metrics.avg_humidity_pct_24h is None
    assert metrics.max_wind_speed_kmh_24h is None
    assert metrics.rainfall_mm_24h == Decimal("0.0")


# 21. Timezone-aware reference time
def test_timezone_aware_reference_time():
    ref = datetime(2026, 9, 24, 15, 30, tzinfo=timezone.utc)
    items = [_make_forecast_item(ref + timedelta(hours=3), temp=25.0)]
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    assert metrics.reference_time == ref
    assert metrics.reference_time.tzinfo == timezone.utc


# 22. Naive reference time normalized consistently
def test_naive_reference_time_normalized():
    ref_naive = datetime(2026, 9, 24, 15, 30)
    expected_aware = datetime(2026, 9, 24, 15, 30, tzinfo=timezone.utc)
    items = [_make_forecast_item(expected_aware + timedelta(hours=3), temp=25.0)]
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref_naive)
    assert metrics.reference_time == expected_aware
    assert metrics.reference_time.tzinfo == timezone.utc
    assert metrics.max_temperature_c_24h == Decimal("25.0")


# 23. Final forecast record does not receive an invented interval
def test_final_forecast_record_no_invented_interval():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    items = [
        _make_forecast_item(ref + timedelta(hours=0), cloud_cover=100.0),
        _make_forecast_item(ref + timedelta(hours=3), cloud_cover=100.0),
        _make_forecast_item(ref + timedelta(hours=6), cloud_cover=100.0),  # final record
    ]
    # Interval 1: [0h, 3h) = 3h
    # Interval 2: [3h, 6h) = 3h
    # Item at 6h has no next timestamp -> 0h
    # Total cloudy hours = 6.0 (NOT 9.0)
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    assert metrics.cloudy_hours_24h == Decimal("6.0")


# 24. Partial interval overlap at the 24h/48h boundary
def test_partial_interval_overlap_at_boundaries():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    items = [
        # Starts at +22h, next at +26h (duration 4h). Overlap with [0, 24h] is 2h, with [0, 48h] is 4h.
        _make_forecast_item(ref + timedelta(hours=22), cloud_cover=80.0),
        # Starts at +26h, next at +46h (duration 20h). Overlap with [0, 24h] is 0h, with [0, 48h] is 20h.
        _make_forecast_item(ref + timedelta(hours=26), cloud_cover=80.0),
        # Starts at +46h, next at +50h (duration 4h). Overlap with [0, 24h] is 0h, with [0, 48h] is 2h (from 46h to 48h).
        _make_forecast_item(ref + timedelta(hours=46), cloud_cover=80.0),
        # Final record at +50h
        _make_forecast_item(ref + timedelta(hours=50), cloud_cover=10.0),
    ]
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    assert metrics.cloudy_hours_24h == Decimal("2.0")
    # 48h cloudy: 4h (from first interval) + 20h (second interval) + 2h (third interval overlap up to 48h) = 26h
    assert metrics.cloudy_hours_48h == Decimal("26.0")


# 25. Window without data produces None for that window
def test_no_data_in_24h_window_produces_none():
    ref = datetime(2026, 9, 24, 0, 0, tzinfo=timezone.utc)
    items = [
        _make_forecast_item(ref + timedelta(hours=30), temp=26.0, rainfall=5.0, cloud_cover=80.0),
        _make_forecast_item(ref + timedelta(hours=33), temp=28.0, rainfall=2.0, cloud_cover=10.0),
    ]
    metrics = ForecastAggregationService.aggregate(items, reference_time=ref)
    # 24h window has no data
    assert metrics.rainfall_mm_24h is None
    assert metrics.max_temperature_c_24h is None
    assert metrics.min_temperature_c_24h is None
    assert metrics.avg_humidity_pct_24h is None
    assert metrics.max_wind_speed_kmh_24h is None
    assert metrics.cloudy_hours_24h is None

    # 48h window has data
    assert metrics.rainfall_mm_48h == Decimal("7.0")
    assert metrics.max_temperature_c_48h == Decimal("28.0")
    assert metrics.min_temperature_c_48h == Decimal("26.0")
    assert metrics.cloudy_hours_48h == Decimal("3.0")
