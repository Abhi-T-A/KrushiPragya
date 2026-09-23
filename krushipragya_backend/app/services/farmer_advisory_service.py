"""Presentation layer composing farmer-friendly agricultural guidance from forecast advisories."""

import logging
from decimal import Decimal
from typing import Any, Dict, List, Literal, Optional
from sqlalchemy.orm import Session

from app.schemas.weather import (
    AdvisoryExplanation,
    AdvisoryProvenance,
    FarmerAdvisoryItem,
    FarmerAdvisoryResponse,
    ForecastAdvisoryContext,
    UnsupportedRuleResponse,
)
from app.services.forecast_advisory_service import (
    ForecastAdvisoryResult,
    ForecastAdvisoryService,
)
from app.services.weather_rule_engine import AdvisoryMatch

logger = logging.getLogger(__name__)

SUPPORTED_LANGUAGES = {"en", "kn"}
NO_ADVISORY_MESSAGE_EN = "No forecast-based weather advisory is currently triggered."
NO_ADVISORY_MESSAGE_KN = "ಪ್ರಸ್ತುತ ಯಾವುದೇ ಮುನ್ಸೂಚನೆ ಆಧಾರಿತ ಹವಾಮಾನ ಸಲಹೆ ಸಕ್ರಿಯವಾಗಿಲ್ಲ."

# Condition evaluation metadata for deterministic explanation generation
CONDITION_EXPLANATION_SPECS = [
    (
        "min_rainfall_mm_48h",
        "rainfall_mm_48h",
        "Expected rainfall in 48 hours",
        ">=",
        "mm",
        lambda actual, thresh: f"Expected rainfall is {actual} mm over 48 hours, meeting the advisory threshold of {thresh} mm.",
    ),
    (
        "max_rainfall_mm_48h",
        "rainfall_mm_48h",
        "Expected rainfall in 48 hours",
        "<=",
        "mm",
        lambda actual, thresh: f"Expected rainfall is {actual} mm over 48 hours, which is within the advisory limit of {thresh} mm.",
    ),
    (
        "min_humidity_pct",
        "avg_humidity_pct_48h",
        "Average relative humidity in 48 hours",
        ">=",
        "%",
        lambda actual, thresh: f"Expected average humidity is {actual}% over 48 hours, meeting the advisory threshold of {thresh}%.",
    ),
    (
        "max_humidity_pct",
        "avg_humidity_pct_48h",
        "Average relative humidity in 48 hours",
        "<=",
        "%",
        lambda actual, thresh: f"Expected average humidity is {actual}% over 48 hours, which is within the advisory limit of {thresh}%.",
    ),
    (
        "min_temp_max_c",
        "max_temperature_c_48h",
        "Maximum temperature in 48 hours",
        ">=",
        "°C",
        lambda actual, thresh: f"Expected maximum temperature is {actual} °C over 48 hours, meeting the advisory threshold of {thresh} °C.",
    ),
]


def build_explanations(
    adv: AdvisoryMatch,
    context: ForecastAdvisoryContext,
) -> List[AdvisoryExplanation]:
    """Generate deterministic AdvisoryExplanation items for each matching condition in the rule."""
    config: Dict[str, Any] = getattr(adv, "condition_config", None) or {}
    explanations: List[AdvisoryExplanation] = []

    for key, metric_name, label_en, op, unit, template in CONDITION_EXPLANATION_SPECS:
        if key in config:
            raw_thresh = config[key]
            thresh_val = Decimal(str(raw_thresh)) if raw_thresh is not None else None
            actual_val = getattr(context, metric_name, None)

            explanation_en = template(actual_val, thresh_val)
            explanations.append(
                AdvisoryExplanation(
                    metric_name=metric_name,
                    metric_label_en=label_en,
                    metric_label_kn=None,  # Do not fabricate Kannada without authoritative catalog translation
                    actual_value=actual_val,
                    threshold_operator=op,
                    threshold_value=thresh_val,
                    unit=unit,
                    explanation_en=explanation_en,
                    explanation_kn=None,
                )
            )

    return explanations


class FarmerAdvisoryService:
    """Presentation service translating ForecastAdvisoryResult into farmer-friendly guidance."""

    def __init__(
        self,
        forecast_advisory_service: Optional[ForecastAdvisoryService] = None,
    ) -> None:
        self.forecast_advisory_service = forecast_advisory_service or ForecastAdvisoryService()

    def format_result(
        self,
        result: ForecastAdvisoryResult,
        language: Literal["en", "kn"] = "en",
    ) -> FarmerAdvisoryResponse:
        """Compose a FarmerAdvisoryResponse from an evaluated ForecastAdvisoryResult.

        Rules:
            1. Validates supported language ('en', 'kn').
            2. Preserves database-backed advisory content without AI modification or fabricated claims.
            3. Derives title_en from existing risk_name; title_kn left None if no verified text exists.
            4. If no advisories match, sets status='no_active_advisory' with empty explanations.
            5. If advisories match, sets status='advisory_active' and populates FarmerAdvisoryItem list with
               deterministic explanations and provenance metadata.
            6. Preserves unsupported diagnostic rules separately without explanations.
            7. Embeds contextual forecast weather metrics.

        Args:
            result: Evaluated ForecastAdvisoryResult.
            language: Requested language ('en' or 'kn').

        Returns:
            FarmerAdvisoryResponse tailored for farmers.

        Raises:
            ValueError: When language is not in {'en', 'kn'}.
        """
        if language not in SUPPORTED_LANGUAGES:
            logger.warning("Unsupported language requested: %s", language)
            raise ValueError(f"Unsupported language '{language}'. Supported languages: 'en', 'kn'.")

        context = ForecastAdvisoryContext(
            rainfall_mm_24h=result.metrics.rainfall_mm_24h,
            rainfall_mm_48h=result.metrics.rainfall_mm_48h,
            max_temperature_c_24h=result.metrics.max_temperature_c_24h,
            max_temperature_c_48h=result.metrics.max_temperature_c_48h,
            avg_humidity_pct_24h=result.metrics.avg_humidity_pct_24h,
            avg_humidity_pct_48h=result.metrics.avg_humidity_pct_48h,
            cloudy_hours_24h=result.metrics.cloudy_hours_24h,
            cloudy_hours_48h=result.metrics.cloudy_hours_48h,
        )

        unsupported_resp = [
            UnsupportedRuleResponse(
                rule_id=u.rule_id,
                risk_name=u.risk_name,
                reason=u.reason,
            )
            for u in result.unsupported_rules
        ]

        if not result.advisories:
            return FarmerAdvisoryResponse(
                village_id=result.village.id,
                crop=result.crop.name_en,
                status="no_active_advisory",
                language=language,
                message_en=NO_ADVISORY_MESSAGE_EN,
                message_kn=NO_ADVISORY_MESSAGE_KN,
                context=context,
                advisories=[],
                unsupported_rules=unsupported_resp,
            )

        items = []
        for adv in result.advisories:
            explanations = build_explanations(adv, context)
            provenance = AdvisoryProvenance(
                rule_id=adv.rule_id,
                risk_name=adv.risk_name,
                risk_level=adv.risk_level,
                source_name=adv.source_name,
                source_reference=adv.source_reference,
                condition_type=adv.condition_type,
            )

            item = FarmerAdvisoryItem(
                risk_name=adv.risk_name,
                risk_level=adv.risk_level,
                title_en=adv.risk_name,
                title_kn=None,  # Do not fabricate Kannada titles without authoritative catalog translation
                message_en=adv.advisory_en,
                message_kn=adv.advisory_kn,  # Exact text from database, preserved as-is
                matched_factors=list(adv.matched_factors) if adv.matched_factors else [],
                source_name=adv.source_name,
                source_reference=adv.source_reference,
                advisory_type="forecast",
                explanations=explanations,
                provenance=provenance,
            )
            items.append(item)

        return FarmerAdvisoryResponse(
            village_id=result.village.id,
            crop=result.crop.name_en,
            status="advisory_active",
            language=language,
            message_en=None,
            message_kn=None,
            context=context,
            advisories=items,
            unsupported_rules=unsupported_resp,
        )

    def get_farmer_advisories(
        self,
        db: Session,
        village_id: str,
        crop: str,
        reference_time: Optional[object] = None,
        language: Literal["en", "kn"] = "en",
    ) -> FarmerAdvisoryResponse:
        """Fetch forecast advisories and format them into farmer-friendly guidance."""
        result = self.forecast_advisory_service.get_forecast_advisories(
            db=db,
            village_id=village_id,
            crop=crop,
            reference_time=reference_time,
        )
        return self.format_result(result, language=language)
