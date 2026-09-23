"""Service layer managing forecast-based agricultural advisory evaluation."""

from dataclasses import dataclass
from datetime import datetime, timezone
import logging
from typing import List, Optional
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.models.advisory_rule import AdvisoryRule
from app.models.crop import Crop
from app.models.village import Village
from app.schemas.weather import ForecastMetrics
from app.services.forecast_aggregation_service import ForecastAggregationService
from app.services.weather_advisory_service import (
    CropNotFoundError,
    VillageNotFoundError,
)
from app.services.weather_forecast_service import WeatherForecastService
from app.services.weather_rule_engine import (
    AdvisoryMatch,
    WeatherMetrics,
    evaluate_rule,
)

logger = logging.getLogger(__name__)


@dataclass(frozen=True)
class UnsupportedRule:
    """Representation of an advisory rule requiring metrics not supported by forecast evaluation."""

    rule_id: int
    risk_name: str
    reason: str


@dataclass(frozen=True)
class ForecastAdvisoryResult:
    """Consolidated result containing village, crop, computed forecast metrics, and matching advisories."""

    village: Village
    crop: Crop
    forecast_reference_time: datetime
    metrics: ForecastMetrics
    advisories: List[AdvisoryMatch]
    unsupported_rules: List[UnsupportedRule]


class ForecastAdvisoryService:
    """Coordinates forecast retrieval, metrics aggregation, and forecast-compatible rule evaluation."""

    def __init__(
        self,
        forecast_service: Optional[WeatherForecastService] = None,
        aggregation_service: Optional[ForecastAggregationService] = None,
    ) -> None:
        self.forecast_service = forecast_service or WeatherForecastService()
        self.aggregation_service = aggregation_service or ForecastAggregationService()

    def get_forecast_advisories(
        self,
        db: Session,
        village_id: str,
        crop: str,
        reference_time: Optional[datetime] = None,
    ) -> ForecastAdvisoryResult:
        """Evaluate and retrieve crop weather advisories based on forward-looking forecast metrics.

        Workflow:
            1. Authoritative Village lookup.
            2. Authoritative Canonical Crop lookup.
            3. Retrieve forecast points via WeatherForecastService.
            4. Aggregate forecast metrics via ForecastAggregationService.
            5. Map compatible forecast metrics to WeatherRuleEngine.
            6. Segregate unsupported historical rules (e.g. cloudy_days_streak).
            7. Return consolidated ForecastAdvisoryResult.

        Args:
            db: SQLAlchemy session.
            village_id: Target village identifier.
            crop: Target crop code or name (case-insensitive).
            reference_time: Optional point-in-time anchor (defaults to current UTC).

        Returns:
            ForecastAdvisoryResult with village, crop, metrics, matched advisories, and unsupported rules.

        Raises:
            VillageNotFoundError: When village_id is not found in villages table.
            CropNotFoundError: When crop is not found in crops table.
            WeatherProviderError: When external forecast provider fails.
        """
        # 1. Authoritative Village lookup
        clean_village_id = village_id.strip()
        village = db.get(Village, clean_village_id)
        if not village:
            logger.warning("Forecast advisory failed: Village '%s' not found.", clean_village_id)
            raise VillageNotFoundError(f"Village '{clean_village_id}' not found.")

        # 2. Authoritative Canonical Crop lookup
        clean_crop = crop.strip()
        crop_obj = (
            db.query(Crop)
            .filter(or_(
                Crop.code.ilike(clean_crop),
                Crop.name_en.ilike(clean_crop),
            ))
            .first()
        )
        if not crop_obj:
            logger.warning("Forecast advisory failed: Crop '%s' not found or unsupported.", clean_crop)
            raise CropNotFoundError(f"Crop '{crop}' not found or unsupported.")

        # 3. Retrieve forecast points
        forecast_items = self.forecast_service.get_forecast(db=db, village_id=clean_village_id)

        # 4. Aggregate forecast metrics
        forecast_metrics = self.aggregation_service.aggregate(
            forecast=forecast_items,
            reference_time=reference_time,
        )

        # 5. Retrieve active advisory rules for the canonical crop
        rules = (
            db.query(AdvisoryRule)
            .filter(or_(
                AdvisoryRule.crop.ilike(crop_obj.name_en),
                AdvisoryRule.crop.ilike(clean_crop),
            ))
            .filter(AdvisoryRule.active.is_(True))
            .order_by(AdvisoryRule.id.asc())
            .all()
        )

        # 6. Evaluate forecast-compatible rules
        # Map compatible values:
        #   min_rainfall_mm_48h / max_rainfall_mm_48h -> rainfall_mm_48h
        #   min_humidity_pct / max_humidity_pct       -> avg_humidity_pct_48h
        #   min_temp_max_c                            -> max_temperature_c_48h
        # Explicitly do NOT map min_cloudy_days_streak -> cloudy_hours_48h
        rule_metrics = WeatherMetrics(
            temperature_c=None,
            temp_max_c=float(forecast_metrics.max_temperature_c_48h) if forecast_metrics.max_temperature_c_48h is not None else None,
            humidity_pct=float(forecast_metrics.avg_humidity_pct_48h) if forecast_metrics.avg_humidity_pct_48h is not None else None,
            rainfall_mm_48h=float(forecast_metrics.rainfall_mm_48h) if forecast_metrics.rainfall_mm_48h is not None else None,
            cloudy_days_streak=None,
        )

        matched_advisories: List[AdvisoryMatch] = []
        unsupported_rules: List[UnsupportedRule] = []

        for rule in rules:
            config = rule.condition_config or {}
            # Separate rules that require historical cloudy_days_streak
            if "min_cloudy_days_streak" in config:
                unsupported_rules.append(
                    UnsupportedRule(
                        rule_id=rule.id,
                        risk_name=rule.risk_name,
                        reason="Requires cloudy_days_streak, which is not available from forecast metrics.",
                    )
                )
                continue

            match = evaluate_rule(rule, rule_metrics)
            if match is not None:
                matched_advisories.append(match)

        return ForecastAdvisoryResult(
            village=village,
            crop=crop_obj,
            forecast_reference_time=forecast_metrics.reference_time,
            metrics=forecast_metrics,
            advisories=matched_advisories,
            unsupported_rules=unsupported_rules,
        )
