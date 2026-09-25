from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
import logging
from typing import Any, Dict, List, Literal, Optional
import uuid
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.crop_report import CropReport
from app.models.crop_report_diagnosis import CropReportDiagnosis
from app.models.farmer_crop import FarmerCrop
from app.models.user_profile import UserProfile
from app.models.village import Village
from app.schemas.advisory import (
    FarmerComprehensiveAdvisoryResponse,
    StructuredAdvisoryContext,
)
from app.schemas.weather import (
    AdvisoryExplanation,
    AdvisoryProvenance,
    FarmerAdvisoryItem,
    FarmerAdvisoryResponse,
    ForecastAdvisoryContext,
    UnsupportedRuleResponse,
)
from app.services.farmer_crop_service import (
    FarmerCropNotFoundError,
    FarmerNotFoundError,
)
from app.services.forecast_advisory_service import (
    ForecastAdvisoryResult,
    ForecastAdvisoryService,
)
from app.services.llm_provider import (
    LLMProvider,
    get_llm_provider,
)
from app.services.weather_advisory_service import (
    CropNotFoundError,
    VillageNotFoundError,
)
from app.services.weather_provider import WeatherProviderError
from app.services.weather_rule_engine import AdvisoryMatch

logger = logging.getLogger(__name__)

STRICT_ADVISORY_SYSTEM_PROMPT = (
    "You are the KrushiPragya agricultural advisory language layer.\n"
    "You are NOT the source of truth.\n"
    "Use ONLY the supplied structured facts.\n"
    "Do not invent facts.\n"
    "Never invent:\n"
    "- weather values\n"
    "- disease names\n"
    "- confidence values\n"
    "- crop conditions\n"
    "- market prices\n"
    "- government scheme information\n"
    "- sources\n"
    "- expert verification\n"
    "- chemical recommendations\n\n"
    "If information is missing, say that it is unavailable rather than guessing.\n"
    "Do not turn uncertainty into certainty.\n"
    "Do not claim a disease exists unless it is present in the supplied diagnosis.\n"
    "Do not claim that a treatment is required unless it is supported by the supplied verified advisory/rule context.\n"
    "Never prescribe chemical dosages or pesticide treatments unless explicitly provided in the verified recommendations. "
    "If evidence is insufficient, advise the farmer to consult an agricultural extension officer or certified expert.\n"
    "Produce a concise, actionable farmer advisory.\n"
    "Respect the requested language:\n"
    "- kn = Kannada\n"
    "- en = English\n\n"
    "Use farmer-friendly language."
)

OLLAMA_ADVISORY_SYSTEM_PROMPT = STRICT_ADVISORY_SYSTEM_PROMPT

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
        llm_provider: Optional[LLMProvider] = None,
    ) -> None:
        self.forecast_advisory_service = forecast_advisory_service or ForecastAdvisoryService()
        self._llm_provider = llm_provider

    @property
    def llm_provider(self) -> LLMProvider:
        """Return initialized LLMProvider instance."""
        if self._llm_provider is None:
            self._llm_provider = get_llm_provider()
        return self._llm_provider

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

    def get_comprehensive_advisory(
        self,
        db: Session,
        farmer_id: uuid.UUID,
        crop_id: Optional[uuid.UUID] = None,
        language: Optional[Literal["en", "kn"]] = None,
    ) -> FarmerComprehensiveAdvisoryResponse:
        """Compose a unified advisory synthesizing weather forecasts, disease diagnoses, and crop context.

        Args:
            db: SQLAlchemy database session
            farmer_id: UUID of the requesting farmer
            crop_id: Optional UUID of specific farmer_crop to focus on (validates ownership)
            language: Optional presentation language ('en' or 'kn'). Defaults to farmer's preference.

        Returns:
            FarmerComprehensiveAdvisoryResponse: Structured farmer advisory

        Raises:
            FarmerNotFoundError: If farmer profile does not exist
            FarmerCropNotFoundError: If crop_id is specified but does not belong to farmer
        """
        # 1. Verify farmer exists
        farmer = db.get(UserProfile, farmer_id)
        if farmer is None:
            logger.warning("Farmer %s not found for advisory", farmer_id)
            raise FarmerNotFoundError(f"Farmer with ID '{farmer_id}' not found.")

        # 2. Determine target language
        target_lang: Literal["en", "kn"] = (
            language if language in ("en", "kn")
            else (farmer.language if farmer.language in ("en", "kn") else "kn")
        )

        # 3. Determine target farmer crop & enforce ownership
        farmer_crop: Optional[FarmerCrop] = None
        if crop_id is not None:
            farmer_crop = db.get(FarmerCrop, crop_id)
            if farmer_crop is None or farmer_crop.farmer_id != farmer_id:
                logger.warning("Crop %s does not belong to farmer %s", crop_id, farmer_id)
                raise FarmerCropNotFoundError(
                    f"Farmer crop with ID '{crop_id}' not found for farmer '{farmer_id}'."
                )
        else:
            # Select primary crop or first available crop
            farmer_crop = (
                db.query(FarmerCrop)
                .filter(FarmerCrop.farmer_id == farmer_id, FarmerCrop.is_primary == True)
                .first()
            )
            if farmer_crop is None:
                farmer_crop = (
                    db.query(FarmerCrop)
                    .filter(FarmerCrop.farmer_id == farmer_id)
                    .first()
                )

        crop_name_en = farmer_crop.crop.name_en if (farmer_crop and farmer_crop.crop) else "General Farm"
        crop_name_kn = farmer_crop.crop.name_kn if (farmer_crop and farmer_crop.crop) else "ಸಾಮಾನ್ಯ ಕೃಷಿ"
        crop_code = farmer_crop.crop.code if (farmer_crop and farmer_crop.crop) else "general"

        # 4. Retrieve fresh weather/forecast advisory context
        weather_advisories: List[FarmerAdvisoryItem] = []
        weather_reasons: List[str] = []
        weather_metrics: Optional[ForecastAdvisoryContext] = None
        weather_observed_at: Optional[datetime] = None
        forecast_valid_until: Optional[datetime] = None
        sources: List[str] = []
        provenance: List[AdvisoryProvenance] = []

        if farmer.village_id and crop_code != "general":
            try:
                forecast_result = self.forecast_advisory_service.get_forecast_advisories(
                    db=db,
                    village_id=farmer.village_id,
                    crop=crop_code,
                )
                if forecast_result:
                    weather_observed_at = forecast_result.forecast_reference_time
                    if weather_observed_at:
                        forecast_valid_until = weather_observed_at + timedelta(hours=48)
                    weather_resp = self.format_result(forecast_result, language=target_lang)
                    if weather_resp:
                        if weather_resp.advisories:
                            weather_advisories = weather_resp.advisories
                            for adv in weather_advisories:
                                if adv.source_name and adv.source_name not in sources:
                                    sources.append(adv.source_name)
                                if adv.provenance:
                                    provenance.append(adv.provenance)
                                for exp in adv.explanations:
                                    exp_text = (
                                        exp.explanation_kn
                                        if target_lang == "kn" and exp.explanation_kn
                                        else exp.explanation_en
                                    )
                                    if exp_text:
                                        weather_reasons.append(exp_text)
                        if weather_resp.context:
                            weather_metrics = weather_resp.context
                            prov_name = "OpenWeatherMap" if settings.WEATHER_PROVIDER == "openweather" else "MockWeatherProvider"
                            if prov_name not in sources:
                                sources.append(prov_name)
            except (VillageNotFoundError, CropNotFoundError, WeatherProviderError, Exception) as exc:
                logger.info("Forecast advisory lookup skipped or unavailable for %s/%s: %s", farmer.village_id, crop_code, exc)

        # 5. Retrieve latest persistent disease diagnosis
        diag_query = (
            db.query(CropReportDiagnosis)
            .join(CropReport, CropReportDiagnosis.crop_report_id == CropReport.id)
            .join(FarmerCrop, CropReport.farmer_crop_id == FarmerCrop.id)
            .filter(FarmerCrop.farmer_id == farmer_id)
        )
        if farmer_crop is not None:
            diag_query = diag_query.filter(CropReport.farmer_crop_id == farmer_crop.id)
        latest_diagnosis = diag_query.order_by(CropReportDiagnosis.created_at.desc()).first()

        if latest_diagnosis and latest_diagnosis.model_name:
            source_tag = f"Disease Detection AI ({latest_diagnosis.model_name})"
            if source_tag not in sources:
                sources.append(source_tag)

        # 6. Determine overall severity deterministically
        severity = "INFO"
        if any(a.risk_level == "HIGH" for a in weather_advisories):
            severity = "HIGH"
        elif any(a.risk_level == "MODERATE" for a in weather_advisories):
            severity = "MODERATE"
        elif latest_diagnosis and latest_diagnosis.predicted_class != "healthy" and latest_diagnosis.confidence >= 0.70:
            severity = "HIGH" if latest_diagnosis.confidence >= 0.90 else "MODERATE"
        elif weather_advisories:
            severity = "LOW"

        # 7. Collect recommended actions deterministically
        recommended_actions: List[str] = []
        for adv in weather_advisories:
            act = adv.message_kn if target_lang == "kn" and adv.message_kn else adv.message_en
            if act and act not in recommended_actions:
                recommended_actions.append(act)

        if latest_diagnosis and latest_diagnosis.predicted_class != "healthy":
            diag_label = latest_diagnosis.predicted_class.replace("_", " ").title()
            if target_lang == "kn":
                disease_action = f"{latest_diagnosis.predicted_class} ಲಕ್ಷಣಗಳನ್ನು ಪರಿಶೀಲಿಸಿ ಮತ್ತು ಶಿಫಾರಸು ಮಾಡಿದ ಸಸ್ಯ ಸಂರಕ್ಷಣಾ ಕ್ರಮಗಳನ್ನು ಅನುಸರಿಸಿ."
            else:
                disease_action = f"Inspect field for signs of {diag_label} and follow standard plant protection measures."
            if disease_action not in recommended_actions:
                recommended_actions.append(disease_action)

        if not recommended_actions:
            if target_lang == "kn":
                recommended_actions = [
                    "ನಿಯಮಿತ ಕೃಷಿ ಮೇಲ್ವಿಚಾರಣೆಯನ್ನು ಮುಂದುವರಿಸಿ.",
                    "ತೋಟದಲ್ಲಿ ನೀರು ಸರಾಗವಾಗಿ ಹರಿದುಹೋಗುವಂತೆ ಒಳಚರಂಡಿ ವ್ಯವಸ್ಥೆಯನ್ನು ಕಾಪಾಡಿಕೊಳ್ಳಿ.",
                ]
            else:
                recommended_actions = [
                    "Continue routine plot monitoring and crop surveillance.",
                    "Ensure adequate field drainage and clean cultivation practices.",
                ]

        # 8. Compose deterministic reason string
        reasons_list: List[str] = []
        if weather_reasons:
            reasons_list.extend(weather_reasons)
        elif weather_metrics:
            if weather_metrics.rainfall_mm_48h is not None and weather_metrics.rainfall_mm_48h > 0:
                reasons_list.append(
                    f"ಮುಂದಿನ 48 ಗಂಟೆಗಳಲ್ಲಿ {weather_metrics.rainfall_mm_48h} ಮಿ.ಮೀ ಮಳೆ ನಿರೀಕ್ಷಿಸಲಾಗಿದೆ."
                    if target_lang == "kn"
                    else f"Expected rainfall of {weather_metrics.rainfall_mm_48h} mm in the next 48 hours."
                )
            if weather_metrics.avg_humidity_pct_48h is not None:
                reasons_list.append(
                    f"ಸರಾಸರಿ ಆರ್ದ್ರತೆ: {weather_metrics.avg_humidity_pct_48h}%."
                    if target_lang == "kn"
                    else f"Average relative humidity is {weather_metrics.avg_humidity_pct_48h}%."
                )

        if latest_diagnosis:
            if target_lang == "kn":
                reasons_list.append(
                    f"ಬೆಳೆ ವರದಿಯಲ್ಲಿ {latest_diagnosis.predicted_class} (ವಿಶ್ವಾಸಾರ್ಹತೆ: {latest_diagnosis.confidence * 100:.1f}%) ಪತ್ತೆಯಾಗಿದೆ."
                )
            else:
                reasons_list.append(
                    f"Recent report diagnosed {latest_diagnosis.predicted_class.replace('_', ' ')} with {latest_diagnosis.confidence * 100:.1f}% confidence."
                )

        if not reasons_list:
            if not weather_metrics:
                reason_str = (
                    "ಹವಾಮಾನ ಮುನ್ಸೂಚನೆ ದತ್ತಾಂಶ ಪ್ರಸ್ತುತ ಲಭ್ಯವಿಲ್ಲ. ಯಾವುದೇ ರೋಗದ ದಾಖಲೆ ಇಲ್ಲ."
                    if target_lang == "kn"
                    else "Weather forecast data currently unavailable. No acute disease conditions detected."
                )
            else:
                reason_str = (
                    "ಪ್ರಸ್ತುತ ಯಾವುದೇ ಪ್ರತಿಕೂಲ ಹವಾಮಾನ ಅಥವಾ ರೋಗದ ಗಂಭೀರ ಅಪಾಯಗಳು ಕಂಡುಬಂದಿಲ್ಲ."
                    if target_lang == "kn"
                    else "No acute weather risks or severe disease conditions currently detected."
                )
        else:
            reason_str = " | ".join(reasons_list)

        # 9. Deterministic title
        farmer_name = farmer.full_name or "Farmer"
        if target_lang == "kn":
            title = f"{farmer_name} ಅವರಿಗೆ ಕೃಷಿ ಸಲಹೆ - {crop_name_kn}"
        else:
            title = f"Agricultural Advisory for {farmer_name} - {crop_name_en}"

        # 10. Compile fresh StructuredAdvisoryContext
        now_utc = datetime.now(timezone.utc)
        village_obj = farmer.village or (db.get(Village, farmer.village_id) if farmer.village_id else None)
        farmer_dict = {
            "name": farmer_name,
            "language": target_lang,
            "village": village_obj.name if village_obj else (farmer.village_id or "Unknown Village"),
            "district": village_obj.district if village_obj else "",
            "state": village_obj.state if village_obj else "",
        }
        crop_dict = {
            "crop_id": str(farmer_crop.id) if farmer_crop else None,
            "crop_code": crop_code,
            "crop_name": crop_name_en,
            "area_acres": float(farmer_crop.area_acres) if (farmer_crop and farmer_crop.area_acres is not None) else None,
            "is_primary": farmer_crop.is_primary if farmer_crop else False,
        }
        weather_dict: Optional[Dict[str, Any]] = None
        if weather_metrics:
            weather_dict = {
                "observed_at": weather_observed_at.isoformat() if weather_observed_at else None,
                "forecast_generated_at": weather_observed_at.isoformat() if weather_observed_at else None,
                "forecast_valid_until": forecast_valid_until.isoformat() if forecast_valid_until else None,
                "rainfall_48h_mm": float(weather_metrics.rainfall_mm_48h) if weather_metrics.rainfall_mm_48h is not None else None,
                "humidity_avg_pct": float(weather_metrics.avg_humidity_pct_48h) if weather_metrics.avg_humidity_pct_48h is not None else None,
                "temperature_min_c": None,
                "temperature_max_c": float(weather_metrics.max_temperature_c_48h) if weather_metrics.max_temperature_c_48h is not None else None,
                "other_available_metrics": {
                    "rainfall_24h_mm": float(weather_metrics.rainfall_mm_24h) if weather_metrics.rainfall_mm_24h is not None else None,
                    "humidity_avg_24h_pct": float(weather_metrics.avg_humidity_pct_24h) if weather_metrics.avg_humidity_pct_24h is not None else None,
                    "max_temperature_24h_c": float(weather_metrics.max_temperature_c_24h) if weather_metrics.max_temperature_c_24h is not None else None,
                    "cloudy_hours_48h": float(weather_metrics.cloudy_hours_48h) if weather_metrics.cloudy_hours_48h is not None else None,
                },
            }

        weather_risks_dict = []
        for adv in weather_advisories:
            weather_risks_dict.append({
                "rule_id": adv.provenance.rule_id if adv.provenance else None,
                "risk_name": adv.risk_name,
                "risk_level": adv.risk_level,
                "reason": " | ".join(exp.explanation_en for exp in adv.explanations) if adv.explanations else (adv.matched_factors[0] if adv.matched_factors else ""),
                "action": adv.message_kn if target_lang == "kn" and adv.message_kn else adv.message_en,
            })

        disease_dict = {
            "diagnosis_available": bool(latest_diagnosis is not None),
            "crop": latest_diagnosis.crop if latest_diagnosis else None,
            "predicted_class": latest_diagnosis.predicted_class if latest_diagnosis else None,
            "confidence": float(latest_diagnosis.confidence) if latest_diagnosis and latest_diagnosis.confidence is not None else None,
            "confidence_pct": round(float(latest_diagnosis.confidence) * 100, 1) if latest_diagnosis and latest_diagnosis.confidence is not None else None,
            "model_name": latest_diagnosis.model_name if latest_diagnosis else None,
            "diagnosed_at": latest_diagnosis.created_at.isoformat() if latest_diagnosis and latest_diagnosis.created_at else None,
        }

        provenance_dict = [p.model_dump() if hasattr(p, "model_dump") else p.dict() for p in provenance]

        structured_context = StructuredAdvisoryContext(
            generated_at=now_utc.isoformat(),
            farmer=farmer_dict,
            crop=crop_dict,
            weather=weather_dict,
            weather_risks=weather_risks_dict,
            disease=disease_dict,
            verified_sources=list(sources),
            provenance=provenance_dict,
            severity=severity,
            recommended_actions=list(recommended_actions),
        )

        user_prompt = structured_context.to_llm_prompt_text(target_lang=target_lang)

        # 11. Synthesize summary with configured LLMProvider (Groq/Ollama), with robust fallback
        summary = ""
        is_llm_generated = False

        try:
            llm_text = self.llm_provider.generate(
                prompt=user_prompt,
                system_prompt=STRICT_ADVISORY_SYSTEM_PROMPT,
            )
            if llm_text and llm_text.strip():
                cleaned = llm_text.strip()
                # If response was returned as JSON, parse safely to extract summary
                if cleaned.startswith("{") and cleaned.endswith("}"):
                    try:
                        parsed = json.loads(cleaned)
                        if isinstance(parsed, dict) and "summary" in parsed:
                            cleaned = str(parsed["summary"]).strip()
                    except Exception:
                        pass

                # Never allow LLM hallucinated sources to leak into output
                if "\nSource:" in cleaned:
                    cleaned = cleaned.split("\nSource:")[0].strip()
                if "\nSources:" in cleaned:
                    cleaned = cleaned.split("\nSources:")[0].strip()

                if cleaned:
                    summary = cleaned
                    is_llm_generated = True
        except Exception as exc:
            logger.warning(
                "LLM generation unavailable or failed (%s). Falling back to deterministic advisory.",
                exc,
            )

        # Deterministic fallback if LLM is unavailable or empty
        if not summary:
            is_llm_generated = False
            if target_lang == "kn":
                if weather_advisories:
                    adv_msgs = [a.message_kn or a.message_en for a in weather_advisories if a.message_kn or a.message_en]
                    summary = f"{crop_name_kn} ಬೆಳೆಗೆ ಮುನ್ಸೂಚನೆ ಆಧಾರಿತ ಸಲಹೆ: " + " ".join(adv_msgs)
                elif latest_diagnosis and latest_diagnosis.predicted_class != "healthy":
                    summary = f"{crop_name_kn} ಬೆಳೆಯಲ್ಲಿ {latest_diagnosis.predicted_class} ಪತ್ತೆಯಾಗಿದೆ. ದಯವಿಟ್ಟು ಶಿಫಾರಸು ಮಾಡಿದ ರೋಗ ನಿಯಂತ್ರಣ ಕ್ರಮಗಳನ್ನು ಅನುಸರಿಸಿ."
                elif not weather_metrics:
                    summary = f"{crop_name_kn} ಬೆಳೆಗೆ ಪ್ರಸ್ತುತ ಹವಾಮಾನ ಮುನ್ಸೂಚನೆ ಲಭ್ಯವಿಲ್ಲ. ದಯವಿಟ್ಟು ನಿಯಮಿತ ಕೃಷಿ ಮೇಲ್ವಿಚಾರಣೆಯನ್ನು ಮುಂದುವರಿಸಿ."
                else:
                    summary = f"{crop_name_kn} ಬೆಳೆಗೆ ಪ್ರಸ್ತುತ ಯಾವುದೇ ಹವಾಮಾನ ಅಥವಾ ರೋಗದ ಗಂಭೀರ ಅಪಾಯವಿಲ್ಲ. ಸಾಮಾನ್ಯ ಕೃಷಿ ಕಾರ್ಯಗಳನ್ನು ಮುಂದುವರಿಸಿ."
            else:
                if weather_advisories:
                    adv_msgs = [a.message_en for a in weather_advisories if a.message_en]
                    summary = f"Forecast advisory for {crop_name_en}: " + " ".join(adv_msgs)
                elif latest_diagnosis and latest_diagnosis.predicted_class != "healthy":
                    summary = f"{crop_name_en} crop observation diagnosed {latest_diagnosis.predicted_class.replace('_', ' ')}. Please follow recommended actions."
                elif not weather_metrics:
                    summary = f"Weather forecast is currently unavailable for {crop_name_en}. Continue routine farm monitoring."
                else:
                    summary = f"No adverse weather or acute disease risks currently detected for {crop_name_en}. Continue routine farm operations."

        return FarmerComprehensiveAdvisoryResponse(
            title=title,
            severity=severity,
            summary=summary,
            reason=reason_str,
            recommended_actions=recommended_actions,
            language=target_lang,
            sources=sources,
            provenance=provenance,
            is_llm_generated=is_llm_generated,
            generated_at=now_utc,
            weather_observed_at=weather_observed_at,
            forecast_valid_until=forecast_valid_until,
        )


def get_farmer_advisory_service() -> FarmerAdvisoryService:
    """Dependency provider / singleton factory for FarmerAdvisoryService."""
    return FarmerAdvisoryService()
