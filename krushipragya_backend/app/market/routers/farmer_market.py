"""Farmer Market API Endpoints: Mandi following, produce listings, and offer negotiation."""
import logging
from typing import List, Optional
import uuid

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, require_farmer, verify_farmer_access
from app.database.connection import get_db
from app.market.schemas.market import (
    BuyerOfferWithContextResponse,
    MarketResponse,
    OfferStatusAction,
    ProduceListingCreate,
    ProduceListingDetailResponse,
    ProduceListingResponse,
    ProduceListingUpdate,
)
from app.market.services.buyer_offer_service import BuyerOfferService
from app.market.services.listing_service import ProduceListingService
from app.market.services.market_follow_service import MarketFollowService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/market", tags=["Farmer Market"])


def get_follow_service() -> MarketFollowService:
    return MarketFollowService()


def get_listing_service() -> ProduceListingService:
    return ProduceListingService()


def get_offer_service() -> BuyerOfferService:
    return BuyerOfferService()


# ==============================================================================
# Mandi Following
# ==============================================================================

@router.post(
    "/mandis/{mandi_id}/follow",
    status_code=status.HTTP_200_OK,
    summary="Follow an APMC Mandi",
    description="Bookmarks a mandi for the authenticated farmer for quick tracking and alerts.",
)
def follow_mandi(
    mandi_id: uuid.UUID,
    farmer_user: AuthenticatedUser = Depends(require_farmer),
    db: Session = Depends(get_db),
    follow_service: MarketFollowService = Depends(get_follow_service),
) -> dict:
    """Bookmark an APMC mandi for the authenticated farmer."""
    try:
        follow_service.follow_market(db=db, farmer_id=farmer_user.id, market_id=mandi_id)
        return {"status": "success", "message": f"Successfully followed mandi {mandi_id}"}
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.delete(
    "/mandis/{mandi_id}/follow",
    status_code=status.HTTP_200_OK,
    summary="Unfollow an APMC Mandi",
    description="Removes a mandi bookmark for the authenticated farmer.",
)
def unfollow_mandi(
    mandi_id: uuid.UUID,
    farmer_user: AuthenticatedUser = Depends(require_farmer),
    db: Session = Depends(get_db),
    follow_service: MarketFollowService = Depends(get_follow_service),
) -> dict:
    """Remove mandi bookmark for the authenticated farmer."""
    follow_service.unfollow_market(db=db, farmer_id=farmer_user.id, market_id=mandi_id)
    return {"status": "success", "message": f"Successfully unfollowed mandi {mandi_id}"}


@router.get(
    "/mandis/followed",
    response_model=List[MarketResponse],
    status_code=status.HTTP_200_OK,
    summary="List all followed APMC Mandis",
    description="Retrieves all APMC mandis bookmarked by the authenticated farmer.",
)
def get_followed_mandis(
    farmer_user: AuthenticatedUser = Depends(require_farmer),
    db: Session = Depends(get_db),
    follow_service: MarketFollowService = Depends(get_follow_service),
) -> List[MarketResponse]:
    """Return all mandis followed by the authenticated farmer."""
    return follow_service.get_followed_markets(db=db, farmer_id=farmer_user.id)


# ==============================================================================
# Produce Listings (Farmer Side)
# ==============================================================================

@router.post(
    "/listings",
    response_model=ProduceListingResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Create a produce listing",
    description="Enables a farmer to list available harvest produce with an expected asking price.",
)
def create_produce_listing(
    payload: ProduceListingCreate,
    farmer_user: AuthenticatedUser = Depends(require_farmer),
    db: Session = Depends(get_db),
    listing_service: ProduceListingService = Depends(get_listing_service),
) -> ProduceListingResponse:
    """Create a produce listing for the authenticated farmer."""
    try:
        listing = listing_service.create_listing(
            db=db,
            farmer_id=farmer_user.id,
            payload=payload,
        )
        return ProduceListingResponse.model_validate(listing)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.get(
    "/farmers/{farmer_id}/listings",
    response_model=List[ProduceListingDetailResponse],
    status_code=status.HTTP_200_OK,
    summary="List farmer's produce listings",
    description="Retrieves all produce listings created by a specific farmer, enforcing ownership.",
)
def get_farmer_listings(
    farmer_id: uuid.UUID,
    auth_user: AuthenticatedUser = Depends(verify_farmer_access),
    db: Session = Depends(get_db),
    listing_service: ProduceListingService = Depends(get_listing_service),
) -> List[ProduceListingDetailResponse]:
    """Retrieve all produce listings belonging to the farmer."""
    return listing_service.get_farmer_listings(db=db, farmer_id=farmer_id)


@router.get(
    "/listings/{listing_id}",
    response_model=ProduceListingDetailResponse,
    status_code=status.HTTP_200_OK,
    summary="Get produce listing details with reference mandi price",
    description="Returns produce listing details alongside the factual reference price from the nearest active mandi.",
)
def get_produce_listing_detail(
    listing_id: uuid.UUID,
    db: Session = Depends(get_db),
    listing_service: ProduceListingService = Depends(get_listing_service),
) -> ProduceListingDetailResponse:
    """Retrieve listing details with attached reference mandi price."""
    detail = listing_service.get_listing_detail(db=db, listing_id=listing_id)
    if not detail:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Produce listing '{listing_id}' not found.",
        )
    return detail


@router.patch(
    "/listings/{listing_id}",
    response_model=ProduceListingResponse,
    status_code=status.HTTP_200_OK,
    summary="Update produce listing",
    description="Enables the listing owner to update status, quantity, or asking price.",
)
def update_produce_listing(
    listing_id: uuid.UUID,
    payload: ProduceListingUpdate,
    farmer_user: AuthenticatedUser = Depends(require_farmer),
    db: Session = Depends(get_db),
    listing_service: ProduceListingService = Depends(get_listing_service),
) -> ProduceListingResponse:
    """Update a produce listing enforcing farmer ownership."""
    try:
        updated = listing_service.update_listing(
            db=db,
            farmer_id=farmer_user.id,
            listing_id=listing_id,
            payload=payload,
        )
        return ProduceListingResponse.model_validate(updated)
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


# ==============================================================================
# Offer Review & Negotiation (Farmer Side)
# ==============================================================================

@router.get(
    "/listings/{listing_id}/offers",
    response_model=List[BuyerOfferWithContextResponse],
    status_code=status.HTTP_200_OK,
    summary="View buyer offers on a produce listing",
    description="Enables the farmer to review all buyer offers on their listing with complete transparent price discovery.",
)
def get_listing_offers(
    listing_id: uuid.UUID,
    farmer_user: AuthenticatedUser = Depends(require_farmer),
    db: Session = Depends(get_db),
    offer_service: BuyerOfferService = Depends(get_offer_service),
) -> List[BuyerOfferWithContextResponse]:
    """Retrieve all buyer offers submitted on the farmer's listing."""
    try:
        return offer_service.get_listing_offers(
            db=db,
            farmer_id=farmer_user.id,
            listing_id=listing_id,
        )
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc


@router.post(
    "/offers/{offer_id}/respond",
    status_code=status.HTTP_200_OK,
    summary="Respond to a buyer offer (ACCEPT / REJECT)",
    description="Enables a farmer to accept or reject a purchase offer submitted on their produce listing.",
)
def respond_to_offer(
    offer_id: uuid.UUID,
    payload: OfferStatusAction,
    farmer_user: AuthenticatedUser = Depends(require_farmer),
    db: Session = Depends(get_db),
    offer_service: BuyerOfferService = Depends(get_offer_service),
) -> dict:
    """Accept or reject a buyer offer."""
    try:
        updated_offer = offer_service.respond_to_offer(
            db=db,
            farmer_id=farmer_user.id,
            offer_id=offer_id,
            action=payload.action,
            notes=payload.notes,
        )
        return {
            "status": "success",
            "offer_id": str(updated_offer.id),
            "new_status": updated_offer.status,
            "message": f"Offer {payload.action.lower()}ed successfully.",
        }
    except PermissionError as exc:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=str(exc)) from exc
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc)) from exc
