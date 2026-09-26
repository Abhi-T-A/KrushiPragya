"""Buyer Offer Service: Buyer-to-farmer offers and negotiation workflow."""
from decimal import Decimal
import logging
from typing import List, Optional
import uuid

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.market.schemas.market import (
    BuyerOfferCreate,
    BuyerOfferResponse,
    BuyerOfferWithContextResponse,
    ProduceListingResponse,
)
from app.market.services.listing_service import ProduceListingService
from app.models.marketplace import BuyerOffer, ProduceListing
from app.models.user_profile import UserProfile

logger = logging.getLogger(__name__)


class BuyerOfferService:
    """Service managing buyer purchase offers and farmer negotiation."""

    def __init__(self, listing_service: Optional[ProduceListingService] = None):
        self.listing_service = listing_service or ProduceListingService()

    def submit_offer(
        self,
        db: Session,
        buyer_id: uuid.UUID,
        listing_id: uuid.UUID,
        payload: BuyerOfferCreate,
    ) -> BuyerOffer:
        """Submit a purchase offer from an authenticated buyer."""
        buyer = db.get(UserProfile, buyer_id)
        if not buyer:
            raise ValueError(f"Buyer with ID '{buyer_id}' not found.")

        listing = db.get(ProduceListing, listing_id)
        if not listing:
            raise ValueError(f"Produce listing '{listing_id}' not found.")

        if listing.status not in ("LISTED", "OFFER_RECEIVED", "NEGOTIATING"):
            raise ValueError(f"Cannot submit offer on listing with status '{listing.status}'.")

        # Farmer cannot make an offer on their own listing
        if listing.farmer_id == buyer_id:
            raise ValueError("You cannot submit an offer on your own produce listing.")

        offer = BuyerOffer(
            id=uuid.uuid4(),
            listing_id=listing_id,
            buyer_id=buyer_id,
            offered_price=payload.offered_price,
            quantity=payload.quantity,
            message=payload.message,
            status="PENDING",
        )
        db.add(offer)

        # Update listing status to reflect received offer
        listing.status = "OFFER_RECEIVED"
        db.commit()
        db.refresh(offer)

        logger.info("Buyer %s submitted offer %s of ₹%s on listing %s", buyer_id, offer.id, payload.offered_price, listing_id)
        return offer

    def get_listing_offers(
        self,
        db: Session,
        farmer_id: uuid.UUID,
        listing_id: uuid.UUID,
    ) -> List[BuyerOfferWithContextResponse]:
        """Retrieve all offers submitted on a listing, enforcing that the caller is the listing owner."""
        listing = db.get(ProduceListing, listing_id)
        if not listing:
            raise ValueError(f"Produce listing '{listing_id}' not found.")

        if listing.farmer_id != farmer_id:
            raise PermissionError("Access forbidden: You do not own this produce listing.")

        offers: List[BuyerOffer] = (
            db.query(BuyerOffer)
            .filter(BuyerOffer.listing_id == listing_id)
            .order_by(desc(BuyerOffer.created_at))
            .all()
        )

        detail = self.listing_service.get_listing_detail(db, listing_id)
        ref_mandi = detail.reference_mandi if detail else None

        results = []
        for o in offers:
            buyer = db.get(UserProfile, o.buyer_id)
            buyer_name = buyer.full_name if buyer else None
            # Privacy rule: Reveal contact phone only after offer acceptance
            contact_phone = None
            contact_name = None
            contact_role = None
            if o.status == "ACCEPTED" and buyer:
                contact_phone = buyer.phone
                contact_name = buyer.full_name
                contact_role = "BUYER"

            results.append(
                BuyerOfferWithContextResponse(
                    offer=BuyerOfferResponse.model_validate(o),
                    listing=ProduceListingResponse.model_validate(listing),
                    buyer_name=buyer_name,
                    farmer_expected_price=listing.expected_price,
                    reference_mandi=ref_mandi,
                    contact_phone=contact_phone,
                    contact_name=contact_name,
                    contact_role=contact_role,
                )
            )

        return results

    def get_buyer_offers(
        self,
        db: Session,
        buyer_id: uuid.UUID,
    ) -> List[BuyerOfferWithContextResponse]:
        """Retrieve all offers submitted by a specific buyer."""
        offers = (
            db.query(BuyerOffer)
            .filter(BuyerOffer.buyer_id == buyer_id)
            .order_by(desc(BuyerOffer.created_at))
            .all()
        )

        results = []
        for o in offers:
            listing = db.get(ProduceListing, o.listing_id)
            if not listing:
                continue
            detail = self.listing_service.get_listing_detail(db, listing.id)
            ref_mandi = detail.reference_mandi if detail else None

            # Privacy rule: Reveal farmer contact only after offer acceptance
            contact_phone = None
            contact_name = None
            contact_role = None
            if o.status == "ACCEPTED":
                farmer = db.get(UserProfile, listing.farmer_id)
                if farmer:
                    contact_phone = farmer.phone
                    contact_name = farmer.full_name
                    contact_role = "FARMER"

            results.append(
                BuyerOfferWithContextResponse(
                    offer=BuyerOfferResponse.model_validate(o),
                    listing=ProduceListingResponse.model_validate(listing),
                    buyer_name=None,
                    farmer_expected_price=listing.expected_price,
                    reference_mandi=ref_mandi,
                    contact_phone=contact_phone,
                    contact_name=contact_name,
                    contact_role=contact_role,
                )
            )

        return results

    def respond_to_offer(
        self,
        db: Session,
        farmer_id: uuid.UUID,
        offer_id: uuid.UUID,
        action: str,
        notes: Optional[str] = None,
    ) -> BuyerOffer:
        """Farmer accepts or rejects a buyer offer."""
        offer = db.get(BuyerOffer, offer_id)
        if not offer:
            raise ValueError(f"Offer '{offer_id}' not found.")

        listing = db.get(ProduceListing, offer.listing_id)
        if not listing or listing.farmer_id != farmer_id:
            raise PermissionError("Access forbidden: You do not own the listing associated with this offer.")

        norm_action = action.strip().upper()
        if norm_action == "ACCEPT":
            offer.status = "ACCEPTED"
            listing.status = "NEGOTIATING"
            logger.info("Farmer %s ACCEPTED offer %s from buyer %s", farmer_id, offer.id, offer.buyer_id)
        elif norm_action == "REJECT":
            offer.status = "REJECTED"
            logger.info("Farmer %s REJECTED offer %s from buyer %s", farmer_id, offer.id, offer.buyer_id)
        else:
            raise ValueError(f"Invalid offer response action '{action}'. Use ACCEPT or REJECT.")

        if notes:
            offer.message = f"{offer.message or ''}\nFarmer Response: {notes}".strip()

        db.commit()
        db.refresh(offer)
        return offer
