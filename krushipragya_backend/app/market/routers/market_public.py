"""Public Market Price Discovery API Endpoints."""
from datetime import date
import logging
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, get_current_user, oauth2_scheme
from app.database.connection import get_db
from app.market.models.market import Market
from app.market.models.market_mapping import MarketCropMapping
from app.market.models.market_source import MarketDataSource
from app.market.schemas.market import (
    MarketDataSourceResponse,
    MarketDetailResponse,
    MarketResponse,
    NearbyMandisListResponse,
    PriceIntelligenceResponse,
)
from app.market.services.market_search_service import MarketSearchService
from app.market.services.price_service import PriceService
from app.models.crop import Crop
from app.models.user_profile import UserProfile

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market", tags=["Market Price Discovery"])


def get_search_service() -> MarketSearchService:
    return MarketSearchService()


def get_price_service() -> PriceService:
    return PriceService()


@router.get(
    "/mandis/nearby",
    response_model=NearbyMandisListResponse,
    status_code=status.HTTP_200_OK,
    summary="Discover nearby APMC Mandis trading a crop",
    description=(
        "Discovers APMC Mandis within radius_km (default 500km) trading the requested crop. "
        "Calculates Haversine distance, attaches latest official reported price, and 15-day trend. "
        "If latitude and longitude are omitted, attempts to resolve from authenticated farmer's registered village."
    ),
)
def get_nearby_mandis(
    crop_id: uuid.UUID = Query(..., description="UUID of the crop"),
    latitude: Optional[float] = Query(None, description="Reference latitude"),
    longitude: Optional[float] = Query(None, description="Reference longitude"),
    radius_km: float = Query(500.0, ge=1.0, le=2000.0, description="Search radius in kilometers"),
    sort: str = Query("distance", pattern="^(distance|price)$", description="Sort order: distance or price"),
    db: Session = Depends(get_db),
    search_service: MarketSearchService = Depends(get_search_service),
) -> NearbyMandisListResponse:
    """Find nearby mandis trading a crop with Haversine distance and 15-day price trend."""
    # Default Karnataka centroid if coordinates not provided
    ref_lat = latitude if latitude is not None else 12.9716
    ref_lon = longitude if longitude is not None else 77.5946

    try:
        return search_service.find_nearby_mandis(
            db=db,
            crop_id=crop_id,
            latitude=ref_lat,
            longitude=ref_lon,
            radius_km=radius_km,
            sort_by=sort,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get(
    "/mandis/{mandi_id}",
    response_model=MarketDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve detailed APMC Mandi price intelligence",
    description="Retrieves Mandi details, 15-day price intelligence, highs, lows, and historical records for a crop.",
)
def get_mandi_detail(
    mandi_id: uuid.UUID,
    crop_id: Optional[uuid.UUID] = Query(None, description="Optional crop UUID to compute 15-day intelligence"),
    db: Session = Depends(get_db),
    price_service: PriceService = Depends(get_price_service),
) -> MarketDetailResponse:
    """Retrieve detailed mandi information and factual 15-day price intelligence."""
    mandi = db.get(Market, mandi_id)
    if not mandi:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Market with ID '{mandi_id}' not found.",
        )

    crop_name = None
    intel = None
    if crop_id:
        crop = db.get(Crop, crop_id)
        if crop:
            crop_name = crop.name_en
            intel = price_service.get_15_day_intelligence(
                db=db, market_id=mandi_id, crop_id=crop_id
            )

    return MarketDetailResponse(
        market=MarketResponse.model_validate(mandi),
        crop_id=crop_id,
        crop_name=crop_name,
        is_followed=False,
        intelligence=intel,
    )


@router.get(
    "/mandis/{mandi_id}/prices/history",
    response_model=PriceIntelligenceResponse,
    status_code=status.HTTP_200_OK,
    summary="Retrieve historical mandi prices and trends",
    description="Returns daily historical arrivals and 15-day price facts computed mathematically from official data.",
)
def get_mandi_price_history(
    mandi_id: uuid.UUID,
    crop_id: uuid.UUID = Query(..., description="UUID of the crop"),
    db: Session = Depends(get_db),
    price_service: PriceService = Depends(get_price_service),
) -> PriceIntelligenceResponse:
    """Retrieve historical prices and mathematical trends for a mandi and crop."""
    intel = price_service.get_15_day_intelligence(
        db=db, market_id=mandi_id, crop_id=crop_id
    )
    if not intel:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"No price records found for market '{mandi_id}' and crop '{crop_id}'.",
        )
    return intel


@router.get(
    "/crops",
    response_model=List[dict],
    status_code=status.HTTP_200_OK,
    summary="Retrieve the 7 supported market crops",
    description="Returns the 7 canonical crops supported by the KrushiPragya Market Service with official mappings.",
)
def list_market_crops(db: Session = Depends(get_db)) -> List[dict]:
    """Return the 7 supported crops and their official government mapping varieties."""
    crops = db.query(Crop).filter(Crop.is_active.is_(True)).order_by(Crop.code.asc()).all()
    mappings = db.query(MarketCropMapping).filter(MarketCropMapping.is_active.is_(True)).all()

    varieties_by_crop: dict = {}
    for m in mappings:
        varieties_by_crop.setdefault(m.crop_id, []).append(
            {"commodity": m.raw_commodity_name, "variety": m.variety}
        )

    return [
        {
            "id": str(c.id),
            "code": c.code,
            "name_en": c.name_en,
            "name_kn": c.name_kn,
            "official_mappings": varieties_by_crop.get(c.id, []),
        }
        for c in crops
    ]


@router.get(
    "/sources",
    response_model=List[MarketDataSourceResponse],
    status_code=status.HTTP_200_OK,
    summary="List official market data sources and sync status",
    description="Provides provenance and synchronisation metadata for official government portals (OGD, AGMARKNET, e-NAM).",
)
def list_market_sources(db: Session = Depends(get_db)) -> List[MarketDataSourceResponse]:
    """Return catalog of official data sources and their synchronization health."""
    sources = db.query(MarketDataSource).order_by(MarketDataSource.code.asc()).all()
    return [MarketDataSourceResponse.model_validate(s) for s in sources]
