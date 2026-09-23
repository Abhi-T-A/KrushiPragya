from datetime import datetime
from decimal import Decimal
from typing import Literal, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


class WeatherData(BaseModel):
    """Normalized weather data schema representing observations from any provider."""

    model_config = ConfigDict(from_attributes=True)

    observed_at: datetime = Field(
        description="Timestamp of observation in UTC with timezone"
    )
    temperature_c: Optional[Decimal] = Field(
        default=None,
        max_digits=5,
        decimal_places=2,
        description="Observed ambient temperature in Celsius",
    )
    humidity_pct: Optional[Decimal] = Field(
        default=None,
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2,
        description="Relative humidity percentage (0-100)",
    )
    rainfall_mm: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=8,
        decimal_places=2,
        description="Precipitation / rainfall accumulation in mm (>= 0)",
    )
    wind_speed_kmh: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=7,
        decimal_places=2,
        description="Wind speed in km/h (>= 0)",
    )
    wind_direction_deg: Optional[Decimal] = Field(
        default=None,
        ge=0,
        le=360,
        max_digits=6,
        decimal_places=2,
        description="Wind direction in degrees (0-360)",
    )
    pressure_hpa: Optional[Decimal] = Field(
        default=None,
        gt=0,
        max_digits=7,
        decimal_places=2,
        description="Barometric atmospheric pressure in hPa (> 0)",
    )
    cloud_cover_pct: Optional[Decimal] = Field(
        default=None,
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2,
        description="Cloud cover percentage (0-100)",
    )
    weather_condition: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Standardized descriptive weather condition",
    )
    source: str = Field(
        max_length=100,
        description="Identifier of weather data provider source",
    )


class ForecastData(BaseModel):
    """Normalized weather forecast data point for a forecast interval (typically 3 hours)."""

    model_config = ConfigDict(from_attributes=True)

    timestamp: datetime = Field(
        description="Forecast point-in-time timestamp in UTC with timezone"
    )
    temperature_c: Optional[Decimal] = Field(
        default=None,
        max_digits=5,
        decimal_places=2,
        description="Forecast ambient temperature in Celsius",
    )
    humidity_pct: Optional[Decimal] = Field(
        default=None,
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2,
        description="Forecast relative humidity percentage (0-100)",
    )
    rainfall_mm: Optional[Decimal] = Field(
        default=Decimal("0.0"),
        ge=0,
        max_digits=8,
        decimal_places=2,
        description="Forecast precipitation accumulation in mm (>= 0)",
    )
    wind_speed_kmh: Optional[Decimal] = Field(
        default=None,
        ge=0,
        max_digits=7,
        decimal_places=2,
        description="Forecast wind speed in km/h (>= 0)",
    )
    wind_direction_deg: Optional[Decimal] = Field(
        default=None,
        ge=0,
        le=360,
        max_digits=6,
        decimal_places=2,
        description="Forecast wind direction in degrees (0-360)",
    )
    pressure_hpa: Optional[Decimal] = Field(
        default=None,
        gt=0,
        max_digits=7,
        decimal_places=2,
        description="Forecast barometric atmospheric pressure in hPa (> 0)",
    )
    cloud_cover_pct: Optional[Decimal] = Field(
        default=None,
        ge=0,
        le=100,
        max_digits=5,
        decimal_places=2,
        description="Forecast cloud cover percentage (0-100)",
    )
    weather_condition: Optional[str] = Field(
        default=None,
        max_length=100,
        description="Forecast weather condition description",
    )


class WeatherObserveRequest(BaseModel):
    """Request payload to observe and record weather for a village."""

    village_id: str = Field(
        min_length=1,
        max_length=50,
        description="Canonical identifier of the village (e.g. V001)",
    )


class WeatherObservationResponse(BaseModel):
    """API response payload representing a persisted weather observation."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID = Field(description="Unique observation record UUID")
    village_id: str = Field(description="Village identifier")
    observed_at: datetime = Field(description="Observation timestamp with timezone")
    temperature_c: Optional[Decimal] = Field(default=None, description="Temperature in Celsius")
    humidity_pct: Optional[Decimal] = Field(default=None, description="Humidity percentage")
    rainfall_mm: Optional[Decimal] = Field(default=None, description="Rainfall accumulation in mm")
    wind_speed_kmh: Optional[Decimal] = Field(default=None, description="Wind speed in km/h")
    wind_direction_deg: Optional[Decimal] = Field(default=None, description="Wind direction in degrees")
    pressure_hpa: Optional[Decimal] = Field(default=None, description="Atmospheric pressure in hPa")
    cloud_cover_pct: Optional[Decimal] = Field(default=None, description="Cloud cover percentage")
    weather_condition: Optional[str] = Field(default=None, description="Weather condition description")
    source: str = Field(description="Data source provider")
    created_at: datetime = Field(description="Observation creation timestamp")


class WeatherMetricsResponse(BaseModel):
    """Calculated weather metrics used in advisory evaluation."""

    temperature_c: Optional[float] = Field(default=None, description="Current ambient temperature in Celsius")
    temp_max_c: Optional[float] = Field(default=None, description="Trailing 24-hour maximum temperature in Celsius")
    humidity_pct: Optional[float] = Field(default=None, description="Current relative humidity percentage")
    rainfall_mm_48h: Optional[float] = Field(default=None, description="Trailing 48-hour cumulative rainfall in mm")
    cloudy_days_streak: Optional[int] = Field(default=None, description="Consecutive days with persistent cloudy/overcast conditions")


class AdvisoryMatchResponse(BaseModel):
    """Advisory rule match details."""

    rule_id: int = Field(description="Rule identifier")
    crop: str = Field(description="Crop name")
    risk_name: str = Field(description="Agricultural risk category name")
    risk_level: str = Field(description="Risk severity level (HIGH, MODERATE, LOW)")
    condition_type: str = Field(description="Evaluation condition type")
    risk_context: Optional[str] = Field(default=None, description="Specific risk context")
    matched_factors: list[str] = Field(default_factory=list, description="Specific meteorological factors triggering match")
    advisory_en: str = Field(description="English advisory guidance")
    advisory_kn: str = Field(description="Kannada advisory guidance")
    source_name: str = Field(description="Source institution or agency")
    source_reference: Optional[str] = Field(default=None, description="Bibliographic or operational reference")


class WeatherAdvisoriesResponse(BaseModel):
    """Consolidated weather advisory response payload."""

    village_id: str = Field(description="Village identifier")
    crop: str = Field(description="Target crop canonical name")
    metrics: WeatherMetricsResponse = Field(description="Calculated weather metrics used for evaluation")
    advisories: list[AdvisoryMatchResponse] = Field(default_factory=list, description="List of triggered advisory matches")


class WeatherForecastResponse(BaseModel):
    """API response payload representing 5-day / 3-hour weather forecast for a village."""

    village_id: str = Field(description="Canonical village identifier")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Forecast generation timestamp in UTC with timezone",
    )
    forecast: list[ForecastData] = Field(
        default_factory=list,
        description="Chronological list of 3-hour forecast intervals",
    )


class ForecastMetrics(BaseModel):
    """Calculated meteorological metrics aggregated over 24h and 48h forecast windows."""

    model_config = ConfigDict(from_attributes=True)

    reference_time: datetime = Field(
        description="Forecast aggregation reference timestamp in UTC with timezone"
    )
    rainfall_mm_24h: Optional[Decimal] = Field(
        default=None,
        description="24-hour forecast rainfall accumulation in mm",
    )
    rainfall_mm_48h: Optional[Decimal] = Field(
        default=None,
        description="48-hour forecast rainfall accumulation in mm",
    )
    max_temperature_c_24h: Optional[Decimal] = Field(
        default=None,
        description="24-hour maximum forecast temperature in Celsius",
    )
    max_temperature_c_48h: Optional[Decimal] = Field(
        default=None,
        description="48-hour maximum forecast temperature in Celsius",
    )
    min_temperature_c_24h: Optional[Decimal] = Field(
        default=None,
        description="24-hour minimum forecast temperature in Celsius",
    )
    min_temperature_c_48h: Optional[Decimal] = Field(
        default=None,
        description="48-hour minimum forecast temperature in Celsius",
    )
    avg_humidity_pct_24h: Optional[Decimal] = Field(
        default=None,
        description="24-hour average forecast relative humidity percentage",
    )
    avg_humidity_pct_48h: Optional[Decimal] = Field(
        default=None,
        description="48-hour average forecast relative humidity percentage",
    )
    max_wind_speed_kmh_24h: Optional[Decimal] = Field(
        default=None,
        description="24-hour maximum forecast wind speed in km/h",
    )
    max_wind_speed_kmh_48h: Optional[Decimal] = Field(
        default=None,
        description="48-hour maximum forecast wind speed in km/h",
    )
    cloudy_hours_24h: Optional[Decimal] = Field(
        default=None,
        description="24-hour cumulative forecast cloudy hours",
    )
    cloudy_hours_48h: Optional[Decimal] = Field(
        default=None,
        description="48-hour cumulative forecast cloudy hours",
    )


class UnsupportedRuleResponse(BaseModel):
    """Advisory rule requiring metrics unsupported by forecast evaluation."""

    rule_id: int = Field(description="Advisory rule identifier")
    risk_name: str = Field(description="Risk name from rule definition")
    reason: str = Field(description="Reason why rule is unsupported by forecast evaluation")


class ForecastAdvisoryResponse(BaseModel):
    """Consolidated forecast-based agricultural advisory response."""

    village_id: str = Field(description="Canonical village identifier")
    crop: str = Field(description="Target crop canonical name")
    generated_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        description="Response generation timestamp in UTC with timezone",
    )
    forecast_reference_time: datetime = Field(
        description="Forecast aggregation reference timestamp in UTC with timezone",
    )
    metrics: ForecastMetrics = Field(
        description="Calculated 24h and 48h forecast metrics",
    )
    advisories: list[AdvisoryMatchResponse] = Field(
        default_factory=list,
        description="List of forecast-compatible triggered advisory rules",
    )
    unsupported_rules: list[UnsupportedRuleResponse] = Field(
        default_factory=list,
        description="List of crop advisory rules requiring metrics unsupported by forecast (e.g. cloudy_days_streak)",
    )


class ForecastAdvisoryContext(BaseModel):
    """Contextual meteorological indicators derived from forecast aggregation."""

    model_config = ConfigDict(from_attributes=True)

    rainfall_mm_24h: Optional[Decimal] = Field(default=None, description="24-hour forecast rainfall in mm")
    rainfall_mm_48h: Optional[Decimal] = Field(default=None, description="48-hour forecast rainfall in mm")
    max_temperature_c_24h: Optional[Decimal] = Field(default=None, description="24-hour forecast maximum temperature in Celsius")
    max_temperature_c_48h: Optional[Decimal] = Field(default=None, description="48-hour forecast maximum temperature in Celsius")
    avg_humidity_pct_24h: Optional[Decimal] = Field(default=None, description="24-hour forecast average relative humidity percentage")
    avg_humidity_pct_48h: Optional[Decimal] = Field(default=None, description="48-hour forecast average relative humidity percentage")
    cloudy_hours_24h: Optional[Decimal] = Field(default=None, description="24-hour forecast cloudy hours duration")
    cloudy_hours_48h: Optional[Decimal] = Field(default=None, description="48-hour forecast cloudy hours duration")


class AdvisoryProvenance(BaseModel):
    """Provenance metadata identifying the origin and authoritative source of an advisory."""

    model_config = ConfigDict(from_attributes=True)

    rule_id: int = Field(description="Authoritative advisory rule ID")
    risk_name: str = Field(description="Name of the agricultural risk category")
    risk_level: str = Field(description="Severity level: LOW, MODERATE, or HIGH")
    source_name: str = Field(description="Authoritative institution or issuing agency")
    source_reference: Optional[str] = Field(default=None, description="Bibliographic or protocol reference")
    condition_type: str = Field(description="Condition evaluation type, e.g. WEATHER_THRESHOLD")


class AdvisoryExplanation(BaseModel):
    """Detailed deterministic explanation of why a specific forecast metric triggered a rule."""

    model_config = ConfigDict(from_attributes=True)

    metric_name: str = Field(description="Internal metric key name")
    metric_label_en: str = Field(description="Human-readable English label for the metric")
    metric_label_kn: Optional[str] = Field(default=None, description="Kannada metric label if verified, otherwise None")
    actual_value: Optional[Decimal] = Field(default=None, description="Forecast observed value for this metric")
    threshold_operator: str = Field(description="Comparison operator: '>=', '<=', '>', '<', '=='")
    threshold_value: Optional[Decimal] = Field(default=None, description="Rule threshold limit")
    unit: str = Field(description="Measurement unit, e.g. mm, %, °C, km/h")
    explanation_en: str = Field(description="Deterministic English explanation sentence")
    explanation_kn: Optional[str] = Field(default=None, description="Verified Kannada explanation if available, otherwise None")


class FarmerAdvisoryItem(BaseModel):
    """Farmer-friendly representation of an active agricultural advisory rule."""

    risk_name: str = Field(description="Name of the agricultural risk")
    risk_level: str = Field(description="Severity level: LOW, MODERATE, or HIGH")
    title_en: str = Field(description="English advisory title, derived from risk name")
    title_kn: Optional[str] = Field(default=None, description="Kannada advisory title if available, never fabricated")
    message_en: Optional[str] = Field(default=None, description="English guidance text from advisory rule")
    message_kn: Optional[str] = Field(default=None, description="Kannada guidance text from advisory rule if available, never fabricated")
    matched_factors: list[str] = Field(default_factory=list, description="Specific threshold conditions triggering the advisory")
    source_name: str = Field(description="Authoritative source or institution")
    source_reference: Optional[str] = Field(default=None, description="Bibliographic or protocol reference")
    advisory_type: Literal["forecast"] = Field(default="forecast", description="Classification of advisory source")
    explanations: list[AdvisoryExplanation] = Field(
        default_factory=list,
        description="Deterministic explanations for each condition contributing to the advisory match",
    )
    provenance: Optional[AdvisoryProvenance] = Field(
        default=None,
        description="Provenance and source metadata for the advisory rule",
    )


class FarmerAdvisoryResponse(BaseModel):
    """Farmer-facing presentation of forecast-based agricultural advisories."""

    village_id: str = Field(description="Canonical village identifier")
    crop: str = Field(description="Target crop canonical name")
    status: Literal["advisory_active", "no_active_advisory"] = Field(
        description="Overall advisory status for the farmer"
    )
    language: Literal["en", "kn"] = Field(default="en", description="Requested presentation language")
    message_en: Optional[str] = Field(
        default=None,
        description="General English advisory status message when no specific rules trigger",
    )
    message_kn: Optional[str] = Field(
        default=None,
        description="General Kannada advisory status message when no specific rules trigger",
    )
    context: ForecastAdvisoryContext = Field(
        description="Contextual forecast weather indicators for the farm"
    )
    advisories: list[FarmerAdvisoryItem] = Field(
        default_factory=list,
        description="Active farmer-friendly advisory recommendations",
    )
    unsupported_rules: list[UnsupportedRuleResponse] = Field(
        default_factory=list,
        description="Rules unsupported by forecast metrics, preserved separately for diagnostics",
    )




