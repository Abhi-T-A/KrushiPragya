"""Pydantic schemas and dataclasses for Farmer Advisory domain."""
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Literal, Optional
import uuid

from pydantic import BaseModel, ConfigDict, Field

from app.schemas.weather import AdvisoryProvenance


@dataclass
class StructuredAdvisoryContext:
    """Internal evidence-grounded factual context compiled dynamically for advisory generation."""

    generated_at: str
    farmer: Dict[str, Any]
    crop: Dict[str, Any]
    weather: Optional[Dict[str, Any]] = None
    weather_risks: List[Dict[str, Any]] = field(default_factory=list)
    disease: Optional[Dict[str, Any]] = None
    verified_sources: List[str] = field(default_factory=list)
    provenance: List[Dict[str, Any]] = field(default_factory=list)
    severity: str = "INFO"
    recommended_actions: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Return canonical dictionary representation of structured facts."""
        return {
            "generated_at": self.generated_at,
            "farmer": self.farmer,
            "crop": self.crop,
            "weather": self.weather,
            "weather_risks": self.weather_risks,
            "disease": self.disease,
            "verified_sources": self.verified_sources,
            "provenance": self.provenance,
            "severity": self.severity,
            "recommended_actions": self.recommended_actions,
        }

    def to_llm_prompt_text(self, target_lang: str = "kn") -> str:
        """Compose strict, structured facts representation for LLM synthesis."""
        facts = [
            f"Advisory Generation Time (UTC): {self.generated_at}",
            f"Language: {target_lang}",
            f"Farmer: {self.farmer.get('name', 'Farmer')}",
            f"Risk Severity: {self.severity}",
            f"Location: {self.farmer.get('village', 'Unknown Village')}, {self.farmer.get('district', '')}, {self.farmer.get('state', '')}",
            f"Crop: {self.crop.get('crop_name', 'General Farm')} (Code: {self.crop.get('crop_code', 'general')}, Primary: {self.crop.get('is_primary', False)})",
        ]

        if self.weather:
            w_facts = []
            if self.weather.get("rainfall_48h_mm") is not None:
                w_facts.append(f"Expected Rainfall (48h): {self.weather.get('rainfall_48h_mm')} mm")
            if self.weather.get("humidity_avg_pct") is not None:
                w_facts.append(f"Average Humidity (48h): {self.weather.get('humidity_avg_pct')}%")
            if self.weather.get("temperature_max_c") is not None:
                w_facts.append(f"Max Temperature (48h): {self.weather.get('temperature_max_c')} °C")
            if self.weather.get("observed_at"):
                w_facts.append(f"Observation Reference Time: {self.weather.get('observed_at')}")
            if self.weather.get("forecast_valid_until"):
                w_facts.append(f"Forecast Valid Until: {self.weather.get('forecast_valid_until')}")
            if w_facts:
                facts.append("Weather Forecast Context: " + "; ".join(w_facts))
            else:
                facts.append("Weather Forecast Context: Limited meteorological indicators available.")
        else:
            facts.append("Weather Forecast Context: Weather forecast data currently unavailable for this location.")

        if self.weather_risks:
            risk_descriptions = []
            for r in self.weather_risks:
                risk_descriptions.append(
                    f"{r.get('risk_name')} (Level: {r.get('risk_level')}, Trigger: {r.get('reason')}, Recommended Action: {r.get('action')})"
                )
            facts.append("Active Weather Risks & Rules: " + " | ".join(risk_descriptions))
        else:
            facts.append("Active Weather Risks & Rules: No active meteorological risk conditions triggered.")

        if self.disease and self.disease.get("diagnosis_available"):
            d = self.disease
            facts.append(
                f"Crop Disease Diagnosis: {d.get('predicted_class')} "
                f"(Confidence: {d.get('confidence_pct')}%, Model: {d.get('model_name')}, Diagnosed: {d.get('diagnosed_at')})"
            )
        else:
            facts.append("Crop Disease Diagnosis: No recent crop disease diagnosis recorded.")

        if self.recommended_actions:
            facts.append(f"Deterministic Recommendations: {'; '.join(self.recommended_actions)}")

        if self.verified_sources:
            facts.append("Verified Sources: " + ", ".join(self.verified_sources))
        else:
            facts.append("Verified Sources: None")

        lang_instruction = "simple Kannada" if target_lang == "kn" else "simple English"
        facts.append(
            f"Task: Generate a concise, practical 2-3 sentence farmer advisory summary in {lang_instruction} "
            f"using strictly the verified evidence above. "
            f"Do not invent numbers, chemical doses, unverified diseases, or external sources."
        )

        return "\n".join(facts)


class AdvisoryActionItem(BaseModel):
    """Structured actionable farming step with deterministic priority and timing."""

    action_kn: str = Field(..., description="Actionable recommendation in farmer-friendly Kannada")
    action_en: Optional[str] = Field(default=None, description="Actionable recommendation in English")
    priority: int = Field(default=1, description="Deterministic priority (1=Critical/Safety, 2=High, 3=Medium, 4=Routine)")
    time_window: str = Field(default="ಮುಂದಿನ 24-48 ಗಂಟೆಗಳು", description="Time window for action (e.g. Next 24-48 hours)")
    category: Optional[str] = Field(default="ACTIVITY", description="Action category: SAFETY, WEATHER, PROTECTION, ACTIVITY, GENERAL")


class AdvisoryCropContext(BaseModel):
    """Crop context information associated with an advisory."""

    id: Optional[str] = Field(default=None, description="Farmer crop ID if available")
    code: str = Field(..., description="Crop code (e.g. arecanut, paddy)")
    name_en: str = Field(..., description="Crop name in English")
    name_kn: str = Field(..., description="Crop name in Kannada")
    area_acres: Optional[float] = Field(default=None, description="Cultivated land area in acres")


class AdvisoryLocationContext(BaseModel):
    """Geographic location context for an advisory."""

    village_id: Optional[str] = Field(default=None, description="Village identifier")
    name: str = Field(..., description="Village or location name in English")
    name_kn: Optional[str] = Field(default=None, description="Village or location name in Kannada")
    district: Optional[str] = Field(default=None, description="District name")
    state: Optional[str] = Field(default=None, description="State name")


class FarmerAdvisoryRequest(BaseModel):
    """Optional request payload for generating comprehensive farmer advisory."""

    crop_id: Optional[uuid.UUID] = Field(
        default=None,
        description="Optional farmer crop relationship ID to focus the advisory on",
    )
    language: Optional[Literal["en", "kn"]] = Field(
        default=None,
        description="Optional presentation language ('en' or 'kn'). Defaults to farmer's preference.",
    )
    force_refresh: bool = Field(
        default=False,
        description="If True, bypasses cache and forces re-evaluation of advisory",
    )


class FarmerComprehensiveAdvisoryResponse(BaseModel):
    """Unified farmer advisory integrating forecast weather, crop status, and disease diagnoses."""

    model_config = ConfigDict(from_attributes=True)

    title: str = Field(
        ...,
        description="Advisory title tailored to the farmer and target crop",
    )
    severity: str = Field(
        ...,
        description="Overall risk severity: CRITICAL, HIGH, MODERATE, LOW, or INFO",
    )
    summary: str = Field(
        ...,
        description="Farmer-friendly synthesized summary in the requested language",
    )
    reason: str = Field(
        ...,
        description="Specific meteorological and crop-health reasons that triggered this advisory",
    )
    recommended_actions: List[str] = Field(
        default_factory=list,
        description="Actionable farming practices, treatment steps, and preventive measures",
    )
    language: Literal["en", "kn"] = Field(
        default="kn",
        description="Language of the generated advisory text ('en' or 'kn')",
    )
    sources: List[str] = Field(
        default_factory=list,
        description="Authoritative sources, institutions, and models providing the facts",
    )
    provenance: List[AdvisoryProvenance] = Field(
        default_factory=list,
        description="Detailed provenance records for deterministic rules contributing to advisory",
    )
    is_llm_generated: bool = Field(
        default=False,
        description="True if summary was synthesized by LLM, False if generated via deterministic fallback",
    )
    generated_at: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp when this advisory was generated",
    )
    weather_observed_at: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp of the weather observation or forecast reference",
    )
    forecast_valid_until: Optional[datetime] = Field(
        default=None,
        description="UTC timestamp until which the forecast metrics are valid",
    )

    # Production extensions (with defaults for backwards compatibility)
    advisory_id: Optional[str] = Field(
        default=None,
        description="Unique UUID identifier for this advisory record",
    )
    crop: Optional[AdvisoryCropContext] = Field(
        default=None,
        description="Target crop context information",
    )
    location: Optional[AdvisoryLocationContext] = Field(
        default=None,
        description="Geographic location context",
    )
    risk_level: Optional[str] = Field(
        default=None,
        description="Authoritative risk severity: CRITICAL, HIGH, MODERATE, LOW, INFO",
    )
    title_kn: Optional[str] = Field(
        default=None,
        description="Farmer-friendly Kannada title (e.g. ಸಲಹೆ - ಅಡಿಕೆ)",
    )
    summary_kn: Optional[str] = Field(
        default=None,
        description="Kannada summary answering the 5 farmer questions",
    )
    actions: List[AdvisoryActionItem] = Field(
        default_factory=list,
        description="Structured list of approved action items with priorities and time windows",
    )
    valid_from: Optional[datetime] = Field(
        default=None,
        description="Timestamp from which the advisory is active",
    )
    valid_until: Optional[datetime] = Field(
        default=None,
        description="Timestamp until which the advisory is active",
    )
    confidence_level: str = Field(
        default="HIGH",
        description="Authoritative evidence confidence: HIGH, MEDIUM, LOW, INSUFFICIENT_DATA",
    )
    confidence_level_kn: str = Field(
        default="ಹೆಚ್ಚು",
        description="Kannada confidence representation: ಹೆಚ್ಚು, ಮಧ್ಯಮ, ಕಡಿಮೆ, ಸಾಕಷ್ಟು ಮಾಹಿತಿಯಿಲ್ಲ",
    )
    status: str = Field(
        default="ACTIVE",
        description="Lifecycle status: ACTIVE, EXPIRED, SUPERSEDED",
    )
    evidence: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="Traceable provenance audit trail of rules, weather, and diagnoses",
    )


class FarmerAdvisoriesListResponse(BaseModel):
    """List response for farmer active advisories or history."""

    farmer_id: uuid.UUID = Field(..., description="Farmer identifier")
    advisories: List[FarmerComprehensiveAdvisoryResponse] = Field(
        default_factory=list,
        description="List of farmer advisories",
    )
    total: int = Field(default=0, description="Total count of advisories returned")
