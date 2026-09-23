from dataclasses import dataclass, field
import logging
from typing import Any, Dict, List, Optional
from sqlalchemy import func, or_
from sqlalchemy.orm import Session

from app.models.advisory_rule import AdvisoryRule
from app.models.crop import Crop

logger = logging.getLogger(__name__)

# Known metadata keys in condition_config that are not evaluation thresholds
KNOWN_METADATA_KEYS = {"risk_context", "risk_factors"}

# Known supported condition threshold keys
SUPPORTED_THRESHOLD_KEYS = {
    "min_rainfall_mm_48h",
    "max_rainfall_mm_48h",
    "min_humidity_pct",
    "max_humidity_pct",
    "min_cloudy_days_streak",
    "min_temp_max_c",
}


@dataclass(frozen=True)
class WeatherMetrics:
    """Container for current and trailing-window weather metrics used in rule evaluation."""

    temperature_c: Optional[float] = None
    temp_max_c: Optional[float] = None
    humidity_pct: Optional[float] = None
    rainfall_mm_48h: Optional[float] = None
    cloudy_days_streak: Optional[int] = None


@dataclass(frozen=True)
class AdvisoryMatch:
    """Representation of an advisory rule that matched the evaluated weather metrics."""

    rule_id: int
    crop: str
    risk_name: str
    risk_level: str
    condition_type: str
    risk_context: Optional[str]
    matched_factors: List[str]
    advisory_en: str
    advisory_kn: str
    source_name: str
    source_reference: Optional[str]
    condition_config: Optional[Dict[str, Any]] = None


def evaluate_rule(
    rule: AdvisoryRule,
    metrics: WeatherMetrics,
) -> Optional[AdvisoryMatch]:
    """Evaluate a single AdvisoryRule against WeatherMetrics using conjunctive (AND) logic.

    Args:
        rule: AdvisoryRule database model instance.
        metrics: WeatherMetrics instance containing observed/aggregated data.

    Returns:
        AdvisoryMatch if all defined threshold conditions are met and required metrics are present;
        None otherwise.
    """
    config: Dict[str, Any] = rule.condition_config or {}

    # Check for unknown condition keys
    for key in config:
        if key not in SUPPORTED_THRESHOLD_KEYS and key not in KNOWN_METADATA_KEYS:
            logger.warning(
                "Rule %s (%s) contains unsupported condition key '%s'. Disqualifying rule match.",
                rule.id,
                rule.risk_name,
                key,
            )
            return None

    # 1. min_rainfall_mm_48h: actual >= threshold
    if "min_rainfall_mm_48h" in config:
        if metrics.rainfall_mm_48h is None:
            return None
        if metrics.rainfall_mm_48h < float(config["min_rainfall_mm_48h"]):
            return None

    # 2. max_rainfall_mm_48h: actual <= threshold
    if "max_rainfall_mm_48h" in config:
        if metrics.rainfall_mm_48h is None:
            return None
        if metrics.rainfall_mm_48h > float(config["max_rainfall_mm_48h"]):
            return None

    # 3. min_humidity_pct: actual >= threshold
    if "min_humidity_pct" in config:
        if metrics.humidity_pct is None:
            return None
        if metrics.humidity_pct < float(config["min_humidity_pct"]):
            return None

    # 4. max_humidity_pct: actual <= threshold
    if "max_humidity_pct" in config:
        if metrics.humidity_pct is None:
            return None
        if metrics.humidity_pct > float(config["max_humidity_pct"]):
            return None

    # 5. min_cloudy_days_streak: actual >= threshold
    if "min_cloudy_days_streak" in config:
        if metrics.cloudy_days_streak is None:
            return None
        if metrics.cloudy_days_streak < int(config["min_cloudy_days_streak"]):
            return None

    # 6. min_temp_max_c: actual >= threshold
    if "min_temp_max_c" in config:
        if metrics.temp_max_c is None:
            return None
        if metrics.temp_max_c < float(config["min_temp_max_c"]):
            return None

    # Extract metadata safely
    risk_context = config.get("risk_context")
    raw_factors = config.get("risk_factors")
    matched_factors = list(raw_factors) if isinstance(raw_factors, list) else []

    return AdvisoryMatch(
        rule_id=rule.id,
        crop=rule.crop,
        risk_name=rule.risk_name,
        risk_level=rule.risk_level,
        condition_type=rule.condition_type,
        risk_context=risk_context,
        matched_factors=matched_factors,
        advisory_en=rule.advisory_en,
        advisory_kn=rule.advisory_kn,
        source_name=rule.source_name,
        source_reference=rule.source_reference,
        condition_config=config,
    )


def normalize_crop_name(db: Session, crop_input: str) -> str:
    """Normalize crop input (code or name in any case) into canonical crop name.

    Examples:
        'arecanut' -> 'Arecanut'
        'Arecanut' -> 'Arecanut'
        'ARECANUT' -> 'Arecanut'
    """
    cleaned = crop_input.strip()
    # Check canonical crops table for exact code or name_en match (case-insensitive)
    crop_record = (
        db.query(Crop)
        .filter(or_(Crop.code.ilike(cleaned), Crop.name_en.ilike(cleaned)))
        .first()
    )
    if crop_record:
        return crop_record.name_en

    # Fallback to Title Case formatting if not found in catalog
    return cleaned.title()


def evaluate_rules_for_crop(
    db: Session,
    crop: str,
    metrics: WeatherMetrics,
    active_only: bool = True,
) -> List[AdvisoryMatch]:
    """Retrieve rules matching crop from database and evaluate each against WeatherMetrics.

    Args:
        db: SQLAlchemy database session.
        crop: Target crop identifier (e.g. 'arecanut', 'Arecanut', 'ARECANUT').
        metrics: WeatherMetrics instance.
        active_only: Whether to filter by active=True (default True).

    Returns:
        List of AdvisoryMatch instances preserving database order.
    """
    normalized_crop = normalize_crop_name(db, crop)

    query = (
        db.query(AdvisoryRule)
        .filter(or_(
            AdvisoryRule.crop.ilike(normalized_crop),
            AdvisoryRule.crop.ilike(crop.strip()),
        ))
    )

    if active_only:
        query = query.filter(AdvisoryRule.active.is_(True))

    rules = query.order_by(AdvisoryRule.id.asc()).all()

    matches: List[AdvisoryMatch] = []
    for rule in rules:
        match = evaluate_rule(rule, metrics)
        if match is not None:
            matches.append(match)

    return matches
