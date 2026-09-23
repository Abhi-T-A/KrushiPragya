"""Pydantic data schemas for KrushiPragya API."""
from app.schemas.health import HealthResponse
from app.schemas.weather import (
    WeatherData,
    ForecastData,
    WeatherObserveRequest,
    WeatherObservationResponse,
    WeatherMetricsResponse,
    AdvisoryMatchResponse,
    WeatherAdvisoriesResponse,
    WeatherForecastResponse,
    ForecastMetrics,
    UnsupportedRuleResponse,
    ForecastAdvisoryResponse,
    ForecastAdvisoryContext,
    FarmerAdvisoryItem,
    FarmerAdvisoryResponse,
    AdvisoryProvenance,
    AdvisoryExplanation,
)
from app.schemas.disease import (
    ClassPrediction,
    DiseasePredictionResponse,
)

__all__ = [
    "HealthResponse",
    "WeatherData",
    "ForecastData",
    "WeatherObserveRequest",
    "WeatherObservationResponse",
    "WeatherMetricsResponse",
    "AdvisoryMatchResponse",
    "WeatherAdvisoriesResponse",
    "WeatherForecastResponse",
    "ForecastMetrics",
    "UnsupportedRuleResponse",
    "ForecastAdvisoryResponse",
    "ForecastAdvisoryContext",
    "FarmerAdvisoryItem",
    "FarmerAdvisoryResponse",
    "AdvisoryProvenance",
    "AdvisoryExplanation",
    "ClassPrediction",
    "DiseasePredictionResponse",
]
