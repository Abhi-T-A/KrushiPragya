from dataclasses import dataclass
from datetime import datetime
import logging
from typing import List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.crop import Crop
from app.models.village import Village
from app.services.weather_aggregation_service import get_weather_metrics
from app.services.weather_rule_engine import (
    AdvisoryMatch,
    WeatherMetrics,
    evaluate_rules_for_crop,
)

logger = logging.getLogger(__name__)


class VillageNotFoundError(Exception):
    """Raised when requested village does not exist."""
    pass


class CropNotFoundError(Exception):
    """Raised when requested crop is not found in canonical catalog."""
    pass


@dataclass(frozen=True)
class WeatherAdvisoryResult:
    """Consolidated result containing village, crop, computed metrics, and matched advisories."""

    village: Village
    crop: Crop
    metrics: WeatherMetrics
    advisories: List[AdvisoryMatch]


def get_weather_advisory_bundle(
    db: Session,
    village_id: str,
    crop: str,
    reference_time: Optional[datetime] = None,
) -> WeatherAdvisoryResult:
    """Retrieve weather advisories and calculated metrics bundle for a specific village and crop.

    Workflow:
        1. Look up authoritative village.
        2. Look up authoritative canonical crop.
        3. Aggregate historical/current weather metrics from weather_observations.
        4. Evaluate active advisory rules via WeatherRuleEngine.
        5. Return consolidated result with metrics and all matching advisories.

    Args:
        db: SQLAlchemy session.
        village_id: Target village identifier.
        crop: Target crop code or name (case-insensitive).
        reference_time: Optional evaluation reference timestamp (defaults to current UTC).

    Returns:
        WeatherAdvisoryResult containing village, crop, metrics, and list of AdvisoryMatch.

    Raises:
        VillageNotFoundError: When village_id is not found in villages table.
        CropNotFoundError: When crop is not found in crops table.
    """
    # 1. Authoritative Village lookup
    village = db.get(Village, village_id.strip())
    if not village:
        logger.warning("Advisory lookup failed: Village '%s' not found.", village_id)
        raise VillageNotFoundError(f"Village '{village_id}' not found.")

    # 2. Authoritative Canonical Crop lookup (by code or name_en)
    cleaned_crop = crop.strip()
    crop_obj = (
        db.query(Crop)
        .filter(or_(
            Crop.code.ilike(cleaned_crop),
            Crop.name_en.ilike(cleaned_crop),
        ))
        .first()
    )
    if not crop_obj:
        logger.warning("Advisory lookup failed: Crop '%s' not found or unsupported.", crop)
        raise CropNotFoundError(f"Crop '{crop}' not found or unsupported.")

    # 3. Calculate aggregated WeatherMetrics from observations
    metrics = get_weather_metrics(db=db, village_id=village.id, reference_time=reference_time)

    # 4. Evaluate rules through the existing WeatherRuleEngine
    advisories = evaluate_rules_for_crop(
        db=db,
        crop=crop_obj.name_en,
        metrics=metrics,
        active_only=True,
    )

    return WeatherAdvisoryResult(
        village=village,
        crop=crop_obj,
        metrics=metrics,
        advisories=advisories,
    )


def get_weather_advisories(
    db: Session,
    village_id: str,
    crop: str,
    reference_time: Optional[datetime] = None,
) -> list[AdvisoryMatch]:
    """Retrieve matching weather advisories for a village and crop.

    Implements Step 8C Task 6 interface:
    1. Validates village.
    2. Calculates WeatherMetrics using aggregation service.
    3. Evaluates active rules using WeatherRuleEngine.
    4. Returns list of AdvisoryMatch objects without ranking or suppression.

    Args:
        db: SQLAlchemy session.
        village_id: Village identifier string.
        crop: Crop code or name.
        reference_time: Optional point-in-time timestamp.

    Returns:
        List of matching AdvisoryMatch objects.
    """
    bundle = get_weather_advisory_bundle(
        db=db,
        village_id=village_id,
        crop=crop,
        reference_time=reference_time,
    )
    return bundle.advisories
