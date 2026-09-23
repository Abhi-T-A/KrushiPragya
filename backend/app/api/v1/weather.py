from datetime import datetime, timezone
from decimal import Decimal
import logging
from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.database.connection import get_db
from app.models.village import Village
from app.schemas.weather import (
    AdvisoryMatchResponse,
    FarmerAdvisoryResponse,
    ForecastAdvisoryResponse,
    UnsupportedRuleResponse,
    WeatherAdvisoriesResponse,
    WeatherForecastResponse,
    WeatherMetricsResponse,
    WeatherObserveRequest,
    WeatherObservationResponse,
)
from app.services.farmer_advisory_service import FarmerAdvisoryService
from app.services.forecast_advisory_service import ForecastAdvisoryService
from app.services.weather_advisory_service import (
    CropNotFoundError,
    VillageNotFoundError,
    get_weather_advisory_bundle,
)
from app.services.weather_forecast_service import WeatherForecastService
from app.services.weather_provider import WeatherProviderError
from app.services.weather_service import WeatherService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/weather", tags=["Weather"])


def get_weather_service() -> WeatherService:
    """Dependency provider for WeatherService."""
    return WeatherService()


def get_weather_forecast_service() -> WeatherForecastService:
    """Dependency provider for WeatherForecastService."""
    return WeatherForecastService()


def get_forecast_advisory_service() -> ForecastAdvisoryService:
    """Dependency provider for ForecastAdvisoryService."""
    return ForecastAdvisoryService()


def get_farmer_advisory_service() -> FarmerAdvisoryService:
    """Dependency provider for FarmerAdvisoryService."""
    return FarmerAdvisoryService()


@router.post(
    "/observe",
    response_model=WeatherObservationResponse,
    status_code=status.HTTP_200_OK,
    summary="Record real-time weather observation for a village",
    description="Validates village, fetches real-time weather via configured provider using authoritative coordinates, persists observation, and returns normalized data.",
)
def observe_weather(
    payload: WeatherObserveRequest,
    db: Session = Depends(get_db),
    weather_service: WeatherService = Depends(get_weather_service),
) -> WeatherObservationResponse:
    """Fetch and persist current weather observation for a village."""
    # 1. Authoritative Village lookup
    village = db.get(Village, payload.village_id)
    if not village:
        logger.warning("Weather observe requested for non-existent village_id: %s", payload.village_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Village '{payload.village_id}' not found.",
        )

    # 2. Extract coordinates from authoritative village record
    latitude = village.latitude
    longitude = village.longitude

    # 3. Fetch from provider and persist via service
    try:
        _, observation = weather_service.get_and_record_weather(
            db=db,
            village_id=village.id,
            latitude=latitude,
            longitude=longitude,
            persist=True,
        )
    except WeatherProviderError as e:
        logger.error("Weather provider failed for village %s: %s", payload.village_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Weather provider error: {str(e)}",
        ) from e
    except Exception as e:
        logger.error("Unexpected error in weather observe endpoint: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the weather observation.",
        ) from e

    return observation


@router.get(
    "/advisories",
    response_model=WeatherAdvisoriesResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve agricultural weather advisories for a village and crop",
    description="Aggregates historical and current weather observations for a village, evaluates matching agricultural rules for the crop, and returns advisories.",
)
def get_advisories(
    village_id: str = Query(..., min_length=1, max_length=50, description="Village identifier (e.g. V001)"),
    crop: str = Query(..., min_length=1, max_length=50, description="Target crop code or name (e.g. arecanut)"),
    reference_time: Optional[datetime] = Query(default=None, description="Optional evaluation point-in-time timestamp"),
    db: Session = Depends(get_db),
) -> WeatherAdvisoriesResponse:
    """Evaluate and retrieve crop weather advisories based on trailing observation metrics."""
    try:
        result = get_weather_advisory_bundle(
            db=db,
            village_id=village_id,
            crop=crop,
            reference_time=reference_time,
        )
    except VillageNotFoundError as e:
        logger.warning("Advisory query failed: %s", str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except CropNotFoundError as e:
        logger.warning("Advisory query failed: %s", str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except Exception as e:
        logger.error("Unexpected error in weather advisories endpoint: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing weather advisories.",
        ) from e

    metrics_resp = WeatherMetricsResponse(
        temperature_c=result.metrics.temperature_c,
        temp_max_c=result.metrics.temp_max_c,
        humidity_pct=result.metrics.humidity_pct,
        rainfall_mm_48h=result.metrics.rainfall_mm_48h,
        cloudy_days_streak=result.metrics.cloudy_days_streak,
    )

    advisories_resp = [
        AdvisoryMatchResponse(
            rule_id=m.rule_id,
            crop=m.crop,
            risk_name=m.risk_name,
            risk_level=m.risk_level,
            condition_type=m.condition_type,
            risk_context=m.risk_context,
            matched_factors=m.matched_factors,
            advisory_en=m.advisory_en,
            advisory_kn=m.advisory_kn,
            source_name=m.source_name,
            source_reference=m.source_reference,
        )
        for m in result.advisories
    ]

    return WeatherAdvisoriesResponse(
        village_id=result.village.id,
        crop=result.crop.name_en,
        metrics=metrics_resp,
        advisories=advisories_resp,
    )


@router.get(
    "/forecast",
    response_model=WeatherForecastResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve 5-day / 3-hour weather forecast for a village",
    description="Resolves village coordinates and retrieves normalized 5-day / 3-hour weather forecast from configured provider.",
)
def get_village_forecast(
    village_id: str = Query(..., min_length=1, max_length=50, description="Village identifier (e.g. V001)"),
    db: Session = Depends(get_db),
    forecast_service: WeatherForecastService = Depends(get_weather_forecast_service),
) -> WeatherForecastResponse:
    """Retrieve weather forecast points for a village."""
    try:
        forecast_items = forecast_service.get_forecast(db=db, village_id=village_id)
    except VillageNotFoundError as e:
        logger.warning("Forecast query failed: %s", str(e))
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e),
        ) from e
    except WeatherProviderError as e:
        logger.error("Weather provider failed for village %s forecast: %s", village_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Weather provider error: {str(e)}",
        ) from e
    except Exception as e:
        logger.error("Unexpected error in weather forecast endpoint: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the weather forecast.",
        ) from e

    return WeatherForecastResponse(
        village_id=village_id.strip(),
        generated_at=datetime.now(timezone.utc),
        forecast=forecast_items,
    )


@router.get(
    "/forecast-advisories",
    response_model=ForecastAdvisoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve agricultural weather advisories based on forward-looking forecast",
    description="Fetches 5-day / 3-hour forecast for a village, aggregates 24h and 48h forward metrics, and evaluates forecast-compatible agricultural advisory rules for the crop.",
)
def get_forecast_advisories(
    village_id: str = Query(..., min_length=1, max_length=50, description="Village identifier (e.g. V001)"),
    crop: str = Query(..., min_length=1, max_length=50, description="Target crop code or name (e.g. arecanut)"),
    reference_time: Optional[datetime] = Query(default=None, description="Optional evaluation point-in-time timestamp"),
    db: Session = Depends(get_db),
    service: ForecastAdvisoryService = Depends(get_forecast_advisory_service),
) -> ForecastAdvisoryResponse:
    """Evaluate and retrieve crop weather advisories based on forward-looking forecast metrics."""
    try:
        result = service.get_forecast_advisories(
            db=db,
            village_id=village_id,
            crop=crop,
            reference_time=reference_time,
        )
    except VillageNotFoundError as e:
        logger.warning("Forecast advisory query failed: %s", str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except CropNotFoundError as e:
        logger.warning("Forecast advisory query failed: %s", str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except WeatherProviderError as e:
        logger.error("Weather provider failed for village %s forecast: %s", village_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Weather provider error: {str(e)}",
        ) from e
    except Exception as e:
        logger.error("Unexpected error in forecast advisories endpoint: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing forecast advisories.",
        ) from e

    advisories_resp = [
        AdvisoryMatchResponse(
            rule_id=m.rule_id,
            crop=m.crop,
            risk_name=m.risk_name,
            risk_level=m.risk_level,
            condition_type=m.condition_type,
            risk_context=m.risk_context,
            matched_factors=m.matched_factors,
            advisory_en=m.advisory_en,
            advisory_kn=m.advisory_kn,
            source_name=m.source_name,
            source_reference=m.source_reference,
        )
        for m in result.advisories
    ]

    unsupported_resp = [
        UnsupportedRuleResponse(
            rule_id=u.rule_id,
            risk_name=u.risk_name,
            reason=u.reason,
        )
        for u in result.unsupported_rules
    ]

    return ForecastAdvisoryResponse(
        village_id=result.village.id,
        crop=result.crop.name_en,
        generated_at=datetime.now(timezone.utc),
        forecast_reference_time=result.forecast_reference_time,
        metrics=result.metrics,
        advisories=advisories_resp,
        unsupported_rules=unsupported_resp,
    )


@router.get(
    "/farmer-advisory",
    response_model=FarmerAdvisoryResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve farmer-friendly forecast agricultural advisory guidance",
    description="Translates forecast-based advisory evaluation into simplified, actionable farmer guidance in English or Kannada.",
)
def get_farmer_advisory(
    village_id: str = Query(..., min_length=1, max_length=50, description="Village identifier (e.g. V001)"),
    crop: str = Query(..., min_length=1, max_length=50, description="Target crop code or name (e.g. arecanut)"),
    reference_time: Optional[datetime] = Query(default=None, description="Optional evaluation point-in-time timestamp"),
    language: Literal["en", "kn"] = Query(default="en", description="Presentation language ('en' or 'kn')"),
    db: Session = Depends(get_db),
    service: FarmerAdvisoryService = Depends(get_farmer_advisory_service),
) -> FarmerAdvisoryResponse:
    """Provide simplified farmer-facing agricultural advisory based on forward weather forecast."""
    try:
        return service.get_farmer_advisories(
            db=db,
            village_id=village_id,
            crop=crop,
            reference_time=reference_time,
            language=language,
        )
    except VillageNotFoundError as e:
        logger.warning("Farmer advisory query failed: %s", str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except CropNotFoundError as e:
        logger.warning("Farmer advisory query failed: %s", str(e))
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e)) from e
    except WeatherProviderError as e:
        logger.error("Weather provider failed during farmer advisory generation for %s: %s", village_id, str(e))
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Weather provider error: {str(e)}",
        ) from e
    except ValueError as e:
        logger.warning("Farmer advisory parameter error: %s", str(e))
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(e)) from e
    except Exception as e:
        logger.error("Unexpected error in farmer advisory endpoint: %s", str(e), exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="An unexpected error occurred while processing the farmer advisory.",
        ) from e




