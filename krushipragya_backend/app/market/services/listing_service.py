"""Produce Listing Service: Farmer produce listings with transparent reference mandi pricing."""
from decimal import Decimal
import logging
from typing import List, Optional
import uuid

from sqlalchemy import desc
from sqlalchemy.orm import Session

from app.market.models.market import Market
from app.market.models.market_price import MarketPriceRecord
from app.market.schemas.market import (
    ProduceListingCreate,
    ProduceListingDetailResponse,
    ProduceListingResponse,
    ProduceListingUpdate,
    ReferenceMandiPrice,
)
from app.market.services.market_search_service import haversine_distance_km
from app.models.crop import Crop
from app.models.marketplace import BuyerOffer, ProduceListing
from app.models.user_profile import UserProfile
from app.models.village import Village

logger = logging.getLogger(__name__)


class ProduceListingService:
    """Service managing farmer produce listings and attaching factual mandi price references."""

    def create_listing(
        self,
        db: Session,
        farmer_id: uuid.UUID,
        payload: ProduceListingCreate,
    ) -> ProduceListing:
        """Create a new produce listing for an authenticated farmer."""
        farmer = db.get(UserProfile, farmer_id)
        if not farmer:
            raise ValueError(f"Farmer with ID '{farmer_id}' does not exist.")

        crop = db.get(Crop, payload.crop_id)
        if not crop:
            raise ValueError(f"Crop with ID '{payload.crop_id}' does not exist.")

        listing = ProduceListing(
            id=uuid.uuid4(),
            farmer_id=farmer_id,
            crop_id=payload.crop_id,
            quantity=payload.quantity,
            unit=payload.unit,
            quality_grade=payload.quality_grade,
            expected_price=payload.expected_price,
            location=payload.location,
            status="LISTED",
        )
        db.add(listing)
        db.commit()
        db.refresh(listing)
        logger.info("Farmer %s created produce listing %s for crop %s", farmer_id, listing.id, payload.crop_id)
        return listing

    def get_listing_by_id(self, db: Session, listing_id: uuid.UUID) -> Optional[ProduceListing]:
        """Retrieve raw ProduceListing entity."""
        return db.get(ProduceListing, listing_id)

    def get_listing_detail(
        self,
        db: Session,
        listing_id: uuid.UUID,
    ) -> Optional[ProduceListingDetailResponse]:
        """Retrieve detailed produce listing with factual reference mandi price attached."""
        listing = db.get(ProduceListing, listing_id)
        if not listing:
            return None

        crop = db.get(Crop, listing.crop_id)
        crop_name = crop.name_en if crop else "Unknown"

        farmer = db.get(UserProfile, listing.farmer_id)
        farmer_name = farmer.full_name if farmer else None

        # Resolve reference APMC mandi price
        ref_mandi = self._resolve_reference_mandi_price(db, listing, farmer)

        offers_count = (
            db.query(BuyerOffer)
            .filter(BuyerOffer.listing_id == listing_id)
            .count()
        )

        return ProduceListingDetailResponse(
            listing=ProduceListingResponse.model_validate(listing),
            crop_name=crop_name,
            farmer_name=farmer_name,
            reference_mandi=ref_mandi,
            offers_count=offers_count,
        )

    def search_listings(
        self,
        db: Session,
        crop_id: Optional[uuid.UUID] = None,
        quality_grade: Optional[str] = None,
        max_price: Optional[Decimal] = None,
        min_quantity: Optional[Decimal] = None,
        status: str = "LISTED",
        limit: int = 50,
        offset: int = 0,
    ) -> List[ProduceListingDetailResponse]:
        """Search available produce listings with transparent reference mandi pricing."""
        query = db.query(ProduceListing).filter(ProduceListing.status == status)

        if crop_id:
            query = query.filter(ProduceListing.crop_id == crop_id)
        if quality_grade:
            query = query.filter(ProduceListing.quality_grade == quality_grade)
        if max_price:
            query = query.filter(ProduceListing.expected_price <= max_price)
        if min_quantity:
            query = query.filter(ProduceListing.quantity >= min_quantity)

        listings: List[ProduceListing] = (
            query.order_by(desc(ProduceListing.created_at))
            .offset(offset)
            .limit(limit)
            .all()
        )

        results: List[ProduceListingDetailResponse] = []
        for l in listings:
            detail = self.get_listing_detail(db, l.id)
            if detail:
                results.append(detail)

        return results

    def get_farmer_listings(
        self,
        db: Session,
        farmer_id: uuid.UUID,
    ) -> List[ProduceListingDetailResponse]:
        """Retrieve all listings belonging to a specific farmer."""
        listings = (
            db.query(ProduceListing)
            .filter(ProduceListing.farmer_id == farmer_id)
            .order_by(desc(ProduceListing.created_at))
            .all()
        )
        results = []
        for l in listings:
            detail = self.get_listing_detail(db, l.id)
            if detail:
                results.append(detail)
        return results

    def update_listing(
        self,
        db: Session,
        farmer_id: uuid.UUID,
        listing_id: uuid.UUID,
        payload: ProduceListingUpdate,
    ) -> ProduceListing:
        """Update an existing listing, enforcing farmer ownership."""
        listing = db.get(ProduceListing, listing_id)
        if not listing:
            raise ValueError(f"Produce listing '{listing_id}' not found.")

        if listing.farmer_id != farmer_id:
            raise PermissionError("Access forbidden: You do not own this produce listing.")

        update_data = payload.model_dump(exclude_unset=True)
        for key, val in update_data.items():
            if hasattr(listing, key) and val is not None:
                setattr(listing, key, val)

        db.commit()
        db.refresh(listing)
        return listing

    def _resolve_reference_mandi_price(
        self,
        db: Session,
        listing: ProduceListing,
        farmer: Optional[UserProfile],
    ) -> Optional[ReferenceMandiPrice]:
        """Find the most relevant nearby APMC mandi trading this crop to attach reference price."""
        # Check if farmer has village coordinates
        farmer_lat: Optional[float] = None
        farmer_lon: Optional[float] = None
        if farmer and farmer.village_id:
            village = db.get(Village, farmer.village_id)
            if village and village.latitude and village.longitude:
                farmer_lat = village.latitude
                farmer_lon = village.longitude

        # Find latest price records for this crop across active mandis joined with Market
        price_and_market = (
            db.query(MarketPriceRecord, Market)
            .join(Market, MarketPriceRecord.market_id == Market.id)
            .filter(MarketPriceRecord.crop_id == listing.crop_id)
            .order_by(desc(MarketPriceRecord.arrival_date))
            .limit(10)
            .all()
        )

        if not price_and_market:
            return None

        best_record, best_mandi = price_and_market[0]
        min_dist: Optional[float] = None

        if farmer_lat is not None and farmer_lon is not None:
            closest_dist = float("inf")
            for prec, mandi in price_and_market:
                d = haversine_distance_km(farmer_lat, farmer_lon, mandi.latitude, mandi.longitude)
                if d < closest_dist:
                    closest_dist = d
                    best_record = prec
                    best_mandi = mandi
                    min_dist = d

        return ReferenceMandiPrice(
            mandi_name=best_mandi.name,
            mandi_id=best_mandi.id,
            district=best_mandi.district,
            state=best_mandi.state,
            distance_km=min_dist,
            min_price=best_record.min_price,
            modal_price=best_record.modal_price,
            max_price=best_record.max_price,
            price_date=best_record.arrival_date,
            unit=best_record.unit.lower(),
            is_seeded=getattr(best_record, "is_seeded", True),
            data_mode=getattr(best_record, "data_mode", "DEMO_SEEDED"),
        )
