"""Advisory validation, conflict resolution, and deterministic Kannada formatting."""
from dataclasses import dataclass
from datetime import datetime, timezone
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)

# Common chemical/pesticide and dosage patterns
DOSAGE_PATTERN = re.compile(
    r"\b(\d+(\.\d+)?\s*(g|gm|gram|grams|kg|ml|l|litre|litres|%|percent)\b|\b\d+(\.\d+)?\s*(g|gm|ml)/l(itre)?\b)",
    re.IGNORECASE,
)

SUSPICIOUS_CHEMICAL_TERMS = {
    "chlorpyrifos", "monocrotophos", "glyphosate", "imidacloprid",
    "cypermethrin", "endosulfan", "carbofuran", "phorate", "dimethoate",
    "quinalphos", "dichlorvos", "malathion", "methyl parathion",
}

SAFE_NO_DATA_MESSAGE_KN = "ಸಾಕಷ್ಟು ವಿಶ್ವಾಸಾರ್ಹ ಮಾಹಿತಿಯಿಲ್ಲ. ಸ್ಥಳೀಯ ಕೃಷಿ ಅಧಿಕಾರಿಯನ್ನು ಸಂಪರ್ಕಿಸಿ."
SAFE_NO_DATA_MESSAGE_EN = "Insufficient verified data. Please contact your local agricultural extension officer."


@dataclass
class ValidationResult:
    """Outcome of validating an advisory response."""

    is_valid: bool
    rejection_reasons: List[str]


class AdvisoryValidator:
    """Validates generated advisory content against authoritative evidence and rules."""

    @staticmethod
    def extract_approved_terms(approved_actions: List[str], rules_text: List[str]) -> Set[str]:
        """Extract allowed vocabulary of words and numbers from approved texts."""
        corpus = " ".join(approved_actions + rules_text).lower()
        # Extract alphanumeric words
        words = set(re.findall(r"\b[a-z0-9_]{3,}\b", corpus))
        return words

    @classmethod
    def validate_llm_text(
        cls,
        llm_text: str,
        approved_actions: List[str],
        rule_texts: List[str],
    ) -> ValidationResult:
        """Verify that LLM generated text does not introduce hallucinated chemicals or unapproved dosages.

        Args:
            llm_text: Generated summary text from LLM.
            approved_actions: Approved action strings from deterministic rules.
            rule_texts: Raw rule texts (en and kn) from database.

        Returns:
            ValidationResult indicating validity and any violations detected.
        """
        rejection_reasons: List[str] = []
        if not llm_text or not llm_text.strip():
            return ValidationResult(is_valid=False, rejection_reasons=["LLM output is empty"])

        cleaned = llm_text.strip().lower()
        combined_approved = " ".join(approved_actions + rule_texts).lower()

        # 1. Check for banned/unapproved harsh chemicals
        for chemical in SUSPICIOUS_CHEMICAL_TERMS:
            if chemical in cleaned and chemical not in combined_approved:
                rejection_reasons.append(f"Detected unapproved chemical recommendation: '{chemical}'")

        # 2. Check for invented chemical dosages not present in approved rule text
        found_dosages = DOSAGE_PATTERN.findall(cleaned)
        if found_dosages:
            approved_dosages = DOSAGE_PATTERN.findall(combined_approved)
            approved_dosage_strings = {d[0].replace(" ", "").lower() for d in approved_dosages}
            for dosage_tuple in found_dosages:
                d_str = dosage_tuple[0].replace(" ", "").lower()
                if d_str not in approved_dosage_strings:
                    rejection_reasons.append(f"Detected invented dosage '{dosage_tuple[0]}' not present in verified rules")

        is_valid = len(rejection_reasons) == 0
        if not is_valid:
            logger.warning("Advisory validation failed: %s", "; ".join(rejection_reasons))

        return ValidationResult(is_valid=is_valid, rejection_reasons=rejection_reasons)

    @staticmethod
    def resolve_conflicts(
        weather_risks: List[Dict[str, Any]],
        recommended_actions: List[str],
        rainfall_48h_mm: Optional[float] = None,
        language: str = "kn",
    ) -> List[str]:
        """Deterministically resolve conflicting actions (e.g. spraying vs imminent rainfall).

        Safety Rule:
        If heavy rainfall or waterlogging is expected, ensure drainage and rain precautions
        are prioritized without deleting approved prophylactic rule actions.
        """
        is_heavy_rain = False
        if rainfall_48h_mm is not None and rainfall_48h_mm >= 50.0:
            is_heavy_rain = True

        for r in weather_risks:
            r_name = str(r.get("risk_name", "")).lower()
            r_level = str(r.get("risk_level", "")).upper()
            if ("waterlogging" in r_name or "flood" in r_name or "extreme" in r_name) and r_level in ("HIGH", "CRITICAL"):
                is_heavy_rain = True
                break

        resolved: List[str] = []
        # Include heavy rain precaution if conditions indicate severe downpours
        if is_heavy_rain:
            precaution_kn = "ಭಾರೀ ಮಳೆ ಅಥವಾ ನೀರು ನಿಲ್ಲುವ ಸಮಯದಲ್ಲಿ ಅನಗತ್ಯ ಸಿಂಪಡಣೆ ಮಾಡಬೇಡಿ; ಬಸಿಗಾಲುವೆಗಳನ್ನು ಸರಿಪಡಿಸಿ."
            precaution_en = "Avoid spraying during active heavy downpours; ensure field drainage channels are clear."
            p_msg = precaution_kn if language == "kn" else precaution_en
            resolved.append(p_msg)

        for act in recommended_actions:
            if act not in resolved:
                resolved.append(act)

        return resolved

    @staticmethod
    def calculate_confidence(
        has_weather_data: bool,
        has_rules_matched: bool,
        diagnosis_confidence: Optional[float] = None,
    ) -> Tuple[str, str]:
        """Derive confidence deterministically from actual evidence presence.

        Returns:
            Tuple of (confidence_level, confidence_level_kn)
            Levels: HIGH, MEDIUM, LOW, INSUFFICIENT_DATA
        """
        if not has_weather_data and not has_rules_matched and diagnosis_confidence is None:
            return "INSUFFICIENT_DATA", "ಸಾಕಷ್ಟು ಮಾಹಿತಿಯಿಲ್ಲ"

        if has_weather_data and has_rules_matched:
            return "HIGH", "ಹೆಚ್ಚು"

        if diagnosis_confidence is not None:
            if diagnosis_confidence >= 0.80:
                return "HIGH", "ಹೆಚ್ಚು"
            elif diagnosis_confidence >= 0.50:
                return "MEDIUM", "ಮಧ್ಯಮ"
            else:
                return "LOW", "ಕಡಿಮೆ"

        if has_weather_data:
            return "MEDIUM", "ಮಧ್ಯಮ"

        return "LOW", "ಕಡಿಮೆ"

    @classmethod
    def generate_deterministic_kannada_summary(
        cls,
        crop_name_kn: str,
        risk_name: str,
        risk_level: str,
        reasons: List[str],
        actions: List[str],
        time_window: str = "ಮುಂದಿನ 24-48 ಗಂಟೆಗಳು",
        confidence_kn: str = "ಹೆಚ್ಚು",
    ) -> str:
        """Compose the standard 5-part farmer-friendly Kannada advisory format.

        Structure:
        🌾 ಸಲಹೆ
        ಬೆಳೆ: <Crop>
        ⚠️ ಅಪಾಯ / ಸ್ಥಿತಿ: <Status>
        👉 ಏನು ಮಾಡಬೇಕು:
        • <Action 1>
        • <Action 2>
        ⏰ ಯಾವಾಗ: <Time Window>
        📊 ವಿಶ್ವಾಸ: <Confidence>
        """
        lines = [
            "🌾 ಸಲಹೆ",
            f"ಬೆಳೆ: {crop_name_kn}",
        ]

        if risk_level in ("HIGH", "CRITICAL"):
            risk_label = "ಹೆಚ್ಚಿನ ಅಪಾಯ"
            icon = "⚠️"
        elif risk_level in ("MODERATE", "MEDIUM"):
            risk_label = "ಮಧ್ಯಮ ಅಪಾಯ"
            icon = "⚡"
        elif risk_level == "LOW":
            risk_label = "ಕಡಿಮೆ ಅಪಾಯ / ಅನುಕೂಲಕರ ವಾತಾವರಣ"
            icon = "ℹ️"
        else:
            risk_label = "ಸಾಮಾನ್ಯ ಮಾಹಿತಿ"
            icon = "ℹ️"

        reason_text = " ".join(reasons) if reasons else "ಹವಾಮಾನ ಸ್ಥಿತಿ ಸಾಮಾನ್ಯವಾಗಿದೆ."
        lines.append(f"{icon} ಸ್ಥಿತಿ ({risk_label}): {reason_text}")

        lines.append("👉 ಏನು ಮಾಡಬೇಕು:")
        if actions:
            for act in actions:
                # Clean bullet if already exists
                clean_act = act.lstrip("•-* \t")
                lines.append(f"• {clean_act}")
        else:
            lines.append("• ತೋಟದ ನಿಯಮಿತ ಪರಿಶೀಲನೆಯನ್ನು ಮುಂದುವರಿಸಿ.")

        lines.append(f"⏰ ಯಾವಾಗ: {time_window}")
        lines.append(f"📊 ವಿಶ್ವಾಸ ಮಟ್ಟ: {confidence_kn}")

        return "\n".join(lines)
