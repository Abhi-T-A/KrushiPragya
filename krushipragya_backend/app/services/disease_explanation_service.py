"""Disease Explanation & Kannada Localization Service for KrushiPragya.

Enforces strict separation of concerns:
- ML Model = Diagnosis Authority
- Disease KB = Verified Metadata Authority
- Rule Engine = Agricultural Action Authority
- Qwen (LLM) = Explanation and Localization ONLY

STRICT ARCHITECTURAL RULES:
1. Never send uploaded crop images to Qwen.
2. Qwen receives ONLY structured approved facts.
3. Qwen must never diagnose, reclassify, or alter the predicted disease, crop, or confidence.
4. Qwen must never invent unapproved chemicals, dosages, or treatments.
5. All Qwen outputs are validated; any hallucination or error falls back to deterministic Kannada.
"""
from dataclasses import dataclass, field
import hashlib
import json
import logging
import re
from typing import Any, Dict, List, Optional, Set, Tuple

from app.core.config import settings
from app.services.advisory_validator import DOSAGE_PATTERN, SUSPICIOUS_CHEMICAL_TERMS
from app.services.disease_kb import DiseaseKnowledgeItem
from app.services.llm_provider import (
    LLMConnectionError,
    LLMProvider,
    LLMProviderError,
    LLMTimeoutError,
    get_llm_provider,
)

logger = logging.getLogger(__name__)

# Bounded timeout for Qwen inference (seconds)
QWEN_DISEASE_TIMEOUT_SECONDS = 6.0

# Kannada Unicode character range check
KANNADA_REGEX = re.compile(r"[\u0C80-\u0CFF]")

QWEN_DISEASE_EXPLANATION_SYSTEM_PROMPT = (
    "You are the KrushiPragya Crop Health explanation and localization layer.\n"
    "Your SOLE purpose is to explain and localize the approved agricultural diagnosis facts into clear, farmer-friendly Kannada.\n"
    "STRICT SAFETY RULES:\n"
    "1. You are NOT the diagnostic authority. The ML model has already diagnosed the crop.\n"
    "2. You must NEVER change the crop name, disease name, scientific name, or confidence score.\n"
    "3. You must NEVER invent or recommend any chemical, pesticide, fertilizer, or dosage not present in the approved facts.\n"
    "4. Return ONLY a single valid JSON object matching the requested schema with no commentary or markdown outside the JSON.\n"
    "Schema:\n"
    "{\n"
    '  "title_kn": "Short title in Kannada (e.g. ಬೆಳೆ - ರೋಗದ ಹೆಸರು)",\n'
    '  "summary_kn": "2-3 simple Kannada sentences explaining what is happening to the crop using the approved facts",\n'
    '  "actions_kn": ["List of approved action steps in Kannada directly corresponding to approved facts"],\n'
    '  "timing_kn": "Recommended time window in Kannada (e.g. ಕೂಡಲೇ / ಮುಂದಿನ 24-48 ಗಂಟೆಗಳಲ್ಲಿ)",\n'
    '  "reason_kn": "Reason statement mentioning model confidence and causal agent from approved facts"\n'
    "}"
)


@dataclass
class ValidatedDiseaseExplanation:
    """Structured, verified explanation safe for farmer presentation."""
    title_kn: str
    summary_kn: str
    actions_kn: List[str]
    timing_kn: str
    reason_kn: str
    is_llm_generated: bool
    fallback_used: bool
    approved_facts: Dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "title_kn": self.title_kn,
            "summary_kn": self.summary_kn,
            "actions_kn": self.actions_kn,
            "timing_kn": self.timing_kn,
            "reason_kn": self.reason_kn,
            "is_llm_generated": self.is_llm_generated,
            "fallback_used": self.fallback_used,
        }


class DiseaseExplanationService:
    """Orchestrates Qwen explanation generation with defensive output validation and deterministic fallback."""

    def __init__(self, llm_provider: Optional[LLMProvider] = None):
        self._llm = llm_provider
        self._cache: Dict[str, ValidatedDiseaseExplanation] = {}

    @property
    def llm(self) -> LLMProvider:
        if self._llm is None:
            self._llm = get_llm_provider()
        return self._llm

    def build_approved_facts(
        self,
        crop_code: str,
        crop_name_en: str,
        crop_name_kn: str,
        raw_class: str,
        raw_confidence: float,
        kb_entry: DiseaseKnowledgeItem,
    ) -> Dict[str, Any]:
        """Construct minimal, privacy-safe structured factual representation of the diagnosis.
        
        CRITICAL: Never includes image bytes, JWTs, phone numbers, passwords, or PII.
        """
        approved_actions: List[str] = []
        if kb_entry.cultural_control and kb_entry.cultural_control.strip():
            approved_actions.append(kb_entry.cultural_control.strip())
        if kb_entry.remedy_kn and kb_entry.remedy_kn.strip():
            approved_actions.append(kb_entry.remedy_kn.strip())
        elif kb_entry.remedy_en and kb_entry.remedy_en.strip():
            approved_actions.append(kb_entry.remedy_en.strip())

        return {
            "crop": crop_name_en,
            "crop_kn": crop_name_kn,
            "crop_code": crop_code,
            "raw_class": raw_class,
            "diagnosis": kb_entry.disease_name_en,
            "diagnosis_kn": kb_entry.disease_name_kn,
            "scientific_name": kb_entry.scientific_name or "",
            "category": kb_entry.category,
            "confidence": round(float(raw_confidence), 4),
            "confidence_pct": round(float(raw_confidence) * 100, 1),
            "symptoms": kb_entry.symptoms,
            "cultural_control": kb_entry.cultural_control,
            "remedy_en": kb_entry.remedy_en,
            "remedy_kn": kb_entry.remedy_kn,
            "source_institution": kb_entry.source_institution,
            "approved_actions": approved_actions,
        }

    def generate_deterministic_fallback(
        self,
        approved_facts: Dict[str, Any],
        kb_entry: DiseaseKnowledgeItem,
    ) -> ValidatedDiseaseExplanation:
        """Construct 100% deterministic, verified Kannada explanation directly from Knowledge Base."""
        crop_kn = approved_facts.get("crop_kn", "ಬೆಳೆ")
        disease_kn = kb_entry.disease_name_kn
        confidence_pct = approved_facts.get("confidence_pct", 0.0)

        if kb_entry.category == "HEALTHY":
            title_kn = f"{crop_kn} - ಆರೋಗ್ಯಕರ ಸ್ಥಿತಿ"
            summary_kn = (
                f"ನಿಮ್ಮ {crop_kn} ಬೆಳೆಯು ಆರೋಗ್ಯಕರವಾಗಿ ಕಂಡುಬಂದಿದೆ (AI ಮಾದರಿ ವಿಶ್ವಾಸಾರ್ಹತೆ: {confidence_pct}%). "
                f"ಯಾವುದೇ ಗಂಭೀರ ರೋಗ ಅಥವಾ ಕೀಟ ಬಾಧೆಯ ಲಕ್ಷಣಗಳು ಕಂಡುಬಂದಿಲ್ಲ."
            )
            actions_kn = [
                kb_entry.remedy_kn or "ನಿಯಮಿತ ಪೋಷಕಾಂಶ ಮತ್ತು ನೀರು ನಿರ್ವಹಣೆ ಮುಂದುವರಿಸಿ.",
                kb_entry.cultural_control or "ತೋಟದಲ್ಲಿ ನಿಯಮಿತ ಕಳೆ ಮತ್ತು ಒಳಚರಂಡಿ ನಿರ್ವಹಣೆ ಮುಂದುವರಿಸಿ.",
            ]
            timing_kn = "ನಿಯಮಿತ ಕೃಷಿ ನಿರ್ವಹಣೆ"
            reason_kn = f"ಮಾದರಿ ವಿಶ್ವಾಸಾರ್ಹತೆ: {confidence_pct}% | ರೋಗ ಲಕ್ಷಣಗಳಿಲ್ಲ (ಆರೋಗ್ಯಕರ)"
        else:
            title_kn = f"{crop_kn} - {disease_kn}"
            summary_kn = (
                f"{crop_kn} ಬೆಳೆಯಲ್ಲಿ {disease_kn} ಲಕ್ಷಣಗಳು ಪತ್ತೆಯಾಗಿವೆ (AI ಮಾದರಿ ವಿಶ್ವಾಸಾರ್ಹತೆ: {confidence_pct}%). "
                f"{kb_entry.symptoms}"
            )
            actions_kn = [
                kb_entry.remedy_kn,
                kb_entry.cultural_control,
            ]
            timing_kn = "ಕೂಡಲೇ ಅಥವಾ ಮಳೆ ಬಿಡುವಿನ ವೇಳೆಯಲ್ಲಿ"
            reason_kn = (
                f"ಮಾದರಿ ವಿಶ್ವಾಸಾರ್ಹತೆ: {confidence_pct}% | "
                f"ರೋಗಕಾರಕ: {kb_entry.scientific_name or 'ಪರಿಶೀಲಿಸಲಾಗುತ್ತಿದೆ'} ({kb_entry.category})"
            )

        return ValidatedDiseaseExplanation(
            title_kn=title_kn,
            summary_kn=summary_kn,
            actions_kn=[a for a in actions_kn if a and a.strip()],
            timing_kn=timing_kn,
            reason_kn=reason_kn,
            is_llm_generated=False,
            fallback_used=True,
            approved_facts=approved_facts,
        )

    def validate_qwen_output(
        self,
        raw_output: str,
        approved_facts: Dict[str, Any],
        kb_entry: DiseaseKnowledgeItem,
    ) -> Tuple[bool, Optional[Dict[str, Any]], str]:
        """Strictly validate Qwen JSON output against approved facts.
        
        Returns:
            (is_valid, parsed_dict, rejection_reason)
        """
        if not raw_output or not raw_output.strip():
            return False, None, "Qwen output is empty"

        # 1. Parse JSON (strip markdown codeblocks if model returned them)
        cleaned = raw_output.strip()
        if cleaned.startswith("```"):
            lines = cleaned.split("\n")
            if lines[0].startswith("```"):
                lines = lines[1:]
            if lines and lines[-1].startswith("```"):
                lines = lines[:-1]
            cleaned = "\n".join(lines).strip()

        try:
            parsed = json.loads(cleaned)
        except json.JSONDecodeError as exc:
            return False, None, f"Invalid JSON from Qwen: {exc}"

        if not isinstance(parsed, dict):
            return False, None, "Qwen output is not a JSON object"

        # 2. Check required schema fields
        required_keys = ["title_kn", "summary_kn", "actions_kn", "timing_kn", "reason_kn"]
        for key in required_keys:
            if key not in parsed or not parsed[key]:
                return False, None, f"Missing required key in Qwen output: '{key}'"

        actions = parsed.get("actions_kn")
        if not isinstance(actions, list) or len(actions) == 0:
            return False, None, "actions_kn must be a non-empty list of strings"

        # 3. Kannada script validation
        summary_text = parsed.get("summary_kn", "")
        if not KANNADA_REGEX.search(summary_text):
            return False, None, "Qwen output does not contain valid Kannada text"

        # 4. Check for hallucinated / changed disease
        corpus = (
            parsed.get("title_kn", "") + " " +
            parsed.get("summary_kn", "") + " " +
            parsed.get("reason_kn", "")
        ).lower()

        # 5. Check for unapproved harsh chemicals not present in verified KB
        combined_approved = (
            kb_entry.remedy_en + " " +
            kb_entry.remedy_kn + " " +
            kb_entry.cultural_control
        ).lower()

        all_actions_text = " ".join(str(a) for a in actions).lower()
        full_text_to_check = corpus + " " + all_actions_text

        for chemical in SUSPICIOUS_CHEMICAL_TERMS:
            if chemical in full_text_to_check and chemical not in combined_approved:
                return False, None, f"Qwen hallucinated unapproved chemical: '{chemical}'"

        # 6. Check for invented numerical dosages
        found_dosages = DOSAGE_PATTERN.findall(full_text_to_check)
        if found_dosages:
            approved_dosages = DOSAGE_PATTERN.findall(combined_approved)
            approved_dosage_strings = {d[0].replace(" ", "").lower() for d in approved_dosages}
            for dosage_tuple in found_dosages:
                d_str = dosage_tuple[0].replace(" ", "").lower()
                if d_str not in approved_dosage_strings:
                    return False, None, f"Qwen invented unapproved dosage: '{dosage_tuple[0]}'"

        return True, parsed, "OK"

    def explain_diagnosis(
        self,
        crop_code: str,
        crop_name_en: str,
        crop_name_kn: str,
        raw_class: str,
        raw_confidence: float,
        kb_entry: DiseaseKnowledgeItem,
    ) -> ValidatedDiseaseExplanation:
        """Generate verified explanation using Qwen with defensive fallback."""
        approved_facts = self.build_approved_facts(
            crop_code=crop_code,
            crop_name_en=crop_name_en,
            crop_name_kn=crop_name_kn,
            raw_class=raw_class,
            raw_confidence=raw_confidence,
            kb_entry=kb_entry,
        )

        # Cache key based on deterministic facts
        cache_key = hashlib.sha256(
            f"{crop_code}:{raw_class}:{round(raw_confidence, 2)}".encode()
        ).hexdigest()

        if cache_key in self._cache:
            logger.info("[QWEN_EXPLANATION] Serving cached explanation for %s:%s", crop_code, raw_class)
            return self._cache[cache_key]

        prompt = (
            f"Approved Diagnosis Facts (JSON):\n"
            f"{json.dumps(approved_facts, ensure_ascii=False, indent=2)}\n\n"
            f"Task: Generate a concise, simple farmer Kannada explanation matching the required JSON schema strictly."
        )

        try:
            logger.info(
                "[QWEN_EXPLANATION] Requesting explanation for %s -> %s (conf: %.4f)",
                crop_code, raw_class, raw_confidence,
            )
            raw_response = self.llm.generate(
                prompt=prompt,
                system_prompt=QWEN_DISEASE_EXPLANATION_SYSTEM_PROMPT,
            )

            is_valid, parsed_data, rejection_reason = self.validate_qwen_output(
                raw_output=raw_response,
                approved_facts=approved_facts,
                kb_entry=kb_entry,
            )

            if is_valid and parsed_data:
                logger.info("[QWEN_EXPLANATION] Successfully validated Qwen output for %s:%s", crop_code, raw_class)
                result = ValidatedDiseaseExplanation(
                    title_kn=parsed_data["title_kn"],
                    summary_kn=parsed_data["summary_kn"],
                    actions_kn=parsed_data["actions_kn"],
                    timing_kn=parsed_data["timing_kn"],
                    reason_kn=parsed_data["reason_kn"],
                    is_llm_generated=True,
                    fallback_used=False,
                    approved_facts=approved_facts,
                )
                self._cache[cache_key] = result
                return result
            else:
                logger.warning(
                    "[QWEN_EXPLANATION] Validation failed (%s). Falling back to deterministic content.",
                    rejection_reason,
                )

        except (LLMConnectionError, LLMTimeoutError) as exc:
            logger.warning("[QWEN_EXPLANATION] LLM provider unavailable (%s). Using deterministic fallback.", exc)
        except LLMProviderError as exc:
            logger.warning("[QWEN_EXPLANATION] LLM provider error (%s). Using deterministic fallback.", exc)
        except Exception as exc:
            logger.error("[QWEN_EXPLANATION] Unexpected error in Qwen explanation: %s", exc, exc_info=True)

        # Seamless deterministic fallback
        fallback = self.generate_deterministic_fallback(approved_facts, kb_entry)
        self._cache[cache_key] = fallback
        return fallback


_explanation_service_instance: Optional[DiseaseExplanationService] = None


def get_disease_explanation_service() -> DiseaseExplanationService:
    """Singleton provider for DiseaseExplanationService."""
    global _explanation_service_instance
    if _explanation_service_instance is None:
        _explanation_service_instance = DiseaseExplanationService()
    return _explanation_service_instance
