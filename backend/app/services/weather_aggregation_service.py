from collections import defaultdict
from datetime import datetime, timedelta, timezone
import logging
from typing import Optional

from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.weather_observation import WeatherObservation
from app.services.weather_rule_engine import WeatherMetrics

logger = logging.getLogger(__name__)

CLOUDY_CONDITIONS = {"cloudy", "overcast"}
CLOUDY_COVER_THRESHOLD = 75.0


def is_observation_cloudy(obs: WeatherObservation) -> bool:
    """Determine whether a single observation qualifies as cloudy."""
    if obs.cloud_cover_pct is not None and float(obs.cloud_cover_pct) >= CLOUDY_COVER_THRESHOLD:
        return True
    if obs.weather_condition and obs.weather_condition.strip().lower() in CLOUDY_CONDITIONS:
        return True
    return False


def get_weather_metrics(
    db: Session,
    village_id: str,
    reference_time: Optional[datetime] = None,
) -> WeatherMetrics:
    """Calculate aggregated and point-in-time WeatherMetrics for a village.

    Args:
        db: SQLAlchemy database session.
        village_id: Village identifier string.
        reference_time: Optional point-in-time anchor (defaults to current UTC).

    Returns:
        WeatherMetrics populated with calculated values (or None if data is missing).
    """
    # 1. Normalize reference time to timezone-aware UTC
    if reference_time is None:
        ref_time = datetime.now(timezone.utc)
    elif reference_time.tzinfo is None:
        ref_time = reference_time.replace(tzinfo=timezone.utc)
    else:
        ref_time = reference_time.astimezone(timezone.utc)

    # 2. Check if any observations exist for this village up to reference_time
    total_obs_count = (
        db.query(func.count(WeatherObservation.id))
        .filter(
            WeatherObservation.village_id == village_id,
            WeatherObservation.observed_at <= ref_time,
        )
        .scalar()
        or 0
    )

    if total_obs_count == 0:
        logger.info("No weather observations found for village %s at or before %s", village_id, ref_time)
        return WeatherMetrics(
            temperature_c=None,
            temp_max_c=None,
            humidity_pct=None,
            rainfall_mm_48h=None,
            cloudy_days_streak=None,
        )

    # 3. Trailing 48-Hour Rainfall Accumulation
    window_48h_start = ref_time - timedelta(hours=48)
    obs_48h = (
        db.query(
            func.count(WeatherObservation.id),
            func.count(WeatherObservation.rainfall_mm),
            func.sum(WeatherObservation.rainfall_mm),
        )
        .filter(
            WeatherObservation.village_id == village_id,
            WeatherObservation.observed_at >= window_48h_start,
            WeatherObservation.observed_at <= ref_time,
        )
        .first()
    )

    total_obs_48h, non_null_rainfall_count, sum_48h = obs_48h if obs_48h else (0, 0, None)
    if total_obs_48h == 0 or non_null_rainfall_count == 0:
        rainfall_mm_48h = None
    else:
        rainfall_mm_48h = float(sum_48h) if sum_48h is not None else 0.0

    # 4. Trailing 24-Hour Maximum Temperature
    window_24h_start = ref_time - timedelta(hours=24)
    max_temp_24h = (
        db.query(func.max(WeatherObservation.temperature_c))
        .filter(
            WeatherObservation.village_id == village_id,
            WeatherObservation.observed_at >= window_24h_start,
            WeatherObservation.observed_at <= ref_time,
            WeatherObservation.temperature_c.is_not(None),
        )
        .scalar()
    )
    temp_max_c = float(max_temp_24h) if max_temp_24h is not None else None

    # 5. Latest Point-in-Time Temperature & Humidity
    latest_obs = (
        db.query(WeatherObservation)
        .filter(
            WeatherObservation.village_id == village_id,
            WeatherObservation.observed_at <= ref_time,
        )
        .order_by(WeatherObservation.observed_at.desc())
        .first()
    )

    temperature_c = float(latest_obs.temperature_c) if latest_obs and latest_obs.temperature_c is not None else None
    humidity_pct = float(latest_obs.humidity_pct) if latest_obs and latest_obs.humidity_pct is not None else None

    # 6. Cloudy Day Streak Calculation
    # Look back up to 14 days to compute consecutive streak
    streak_lookback_start = ref_time - timedelta(days=14)
    recent_obs = (
        db.query(WeatherObservation)
        .filter(
            WeatherObservation.village_id == village_id,
            WeatherObservation.observed_at >= streak_lookback_start,
            WeatherObservation.observed_at <= ref_time,
        )
        .order_by(WeatherObservation.observed_at.desc())
        .all()
    )

    if not recent_obs:
        cloudy_days_streak = None
    else:
        # Group observations by UTC calendar date
        daily_observations = defaultdict(list)
        for obs in recent_obs:
            daily_observations[obs.observed_at.date()].append(obs)

        # Start evaluation from ref_date (or latest observed date if ref_time has no observations today)
        ref_date = ref_time.date()
        if ref_date not in daily_observations and recent_obs:
            # If reference day has no readings yet, anchor streak to latest observed date
            anchor_date = recent_obs[0].observed_at.date()
        else:
            anchor_date = ref_date

        streak = 0
        curr_date = anchor_date
        while True:
            if curr_date not in daily_observations:
                # Stop when there is no historical observation data for that day
                break

            day_obs = daily_observations[curr_date]
            has_cloudy = any(is_observation_cloudy(o) for o in day_obs)
            if has_cloudy:
                streak += 1
                curr_date -= timedelta(days=1)
            else:
                # Stop when a day has observations but none are cloudy
                break

        cloudy_days_streak = streak

    return WeatherMetrics(
        temperature_c=temperature_c,
        temp_max_c=temp_max_c,
        humidity_pct=humidity_pct,
        rainfall_mm_48h=rainfall_mm_48h,
        cloudy_days_streak=cloudy_days_streak,
    )
