"""Buyer Market API Endpoints: Produce listing search, offer submission, and sync."""
from decimal import Decimal
import logging
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, require_admin, require_buyer
from app.database.connection import get_db
from app.market.schemas.market import (
    BuyerOfferCreate,
    BuyerOfferResponse,
    BuyerOfferWithContextResponse,
    MarketSyncRequest,
    MarketSyncResponse,
    ProduceListingDetailResponse,
)
from app.market.services.buyer_offer_service import BuyerOfferService
from app.market.services.listing_service import ProduceListingService
from app.market.services.market_ingestion_service import MarketIngestionService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market", tags=["Buyer Market"])


def get_listing_service() -> ProduceListingService:
    return ProduceListingService()


def get_offer_service() -> BuyerOfferService:
    return BuyerOfferService()


def get_ingestion_service() -> MarketIngestionService:
    return MarketIngestionService()


@router.get(
    "/listings",
    response_model=List[ProduceListingDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="Search available farmer produce listings",
    description=(
        "Enables buyers, traders, and public to discover available produce listings. "
        "Filter by crop, quality grade, maximum price, or minimum quantity. "
        "Every listing includes transparent comparison against the nearest active official APMC Mandi price reference."
    ),
)
def search_produce_listings(
    crop_id: Optional[uuid.UUID] = Query(None, description="Filter by canonical crop UUID"),
    quality_grade: Optional[str] = Query(None, description="Filter by grade (e.g. A, B, Premium)"),
    max_price: Optional[Decimal] = Query(None, gt=0, description="Maximum asking price per unit in INR"),
    min_quantity: Optional[Decimal] = Query(None, gt=0, description="Minimum available quantity"),
    status: str = Query("LISTED", description="Listing status filter (default: LISTED)"),
    limit: int = Query(50, ge=1, le=200),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db),
    listing_service: ProduceListingService = Depends(get_listing_service),
) -> List[ProduceListingDetailResponse]:
    """Search active produce listings with transparent reference mandi pricing."""
    return listing_service.search_listings(
        db=db,
        crop_id=crop_id,
        quality_grade=quality_grade,
        max_price=max_price,
        min_quantity=min_quantity,
        status=status,
        limit=limit,
        offset=offset,
    )


@router.post(
    "/listings/{listing_id}/offers",
    response_model=BuyerOfferResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Submit purchase offer on a produce listing",
    description="Enables an authenticated buyer to submit an offer with offered price, desired quantity, and message.",
)
def submit_buyer_offer(
    listing_id: uuid.UUID,
    payload: BuyerOfferCreate,
    buyer_user: AuthenticatedUser = Depends(require_buyer),
    db: Session = Depends(get_db),
    offer_service: BuyerOfferService = Depends(get_offer_service),
) -> BuyerOfferResponse:
    """Submit purchase offer from authenticated buyer."""
    try:
        offer = offer_service.submit_offer(
            db=db,
            buyer_id=buyer_user.id,
            listing_id=listing_id,
            payload=payload,
        )
        return BuyerOfferResponse.model_validate(offer)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc


@router.get(
    "/buyers/{buyer_id}/offers",
    response_model=List[BuyerOfferWithContextResponse],
    status_code=status.HTTP_200_OK,
    summary="List buyer's submitted offers",
    description="Retrieves all purchase offers submitted by the authenticated buyer.",
)
def get_buyer_submitted_offers(
    buyer_id: uuid.UUID,
    buyer_user: AuthenticatedUser = Depends(require_buyer),
    db: Session = Depends(get_db),
    offer_service: BuyerOfferService = Depends(get_offer_service),
) -> List[BuyerOfferWithContextResponse]:
    """Retrieve offers submitted by the authenticated buyer."""
    if buyer_user.id != buyer_id and "ADMIN" not in buyer_user.roles:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You cannot view offers submitted by another buyer.",
        )
    return offer_service.get_buyer_offers(db=db, buyer_id=buyer_id)


# ==============================================================================
# Admin Market Ingestion Trigger
# ==============================================================================

@router.post(
    "/sync",
    response_model=MarketSyncResponse,
    status_code=status.HTTP_200_OK,
    summary="Trigger daily official market data synchronization",
    description="Triggers live ingestion from configured official source (Data.gov.in / OGD). Restricted to ADMIN role.",
)
async def trigger_market_sync(
    payload: Optional[MarketSyncRequest] = None,
    admin_user: AuthenticatedUser = Depends(require_admin),
    db: Session = Depends(get_db),
    ingestion_service: MarketIngestionService = Depends(get_ingestion_service),
) -> MarketSyncResponse:
    """Trigger official market price synchronization."""
    target_date = payload.target_date if payload else None
    state = payload.state if payload and payload.state else "Karnataka"

    return await ingestion_service.sync_market_data(
        db=db,
        state=state,
        target_date=target_date,
    )
