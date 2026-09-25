"""Market Search Service: Haversine distance discovery for nearby APMC Mandis."""
import math
from typing import List, Optional, Tuple
import uuid

from sqlalchemy.orm import Session

from app.market.models.market import Market
from app.market.models.market_follow import FarmerMarketFollow
from app.market.schemas.market import (
    NearbyMandisListResponse,
    NearbyMarketResponse,
)
from app.market.services.price_service import PriceService
from app.models.crop import Crop
from app.models.user_profile import UserProfile
from app.models.village import Village


def haversine_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate the great-circle distance between two points on Earth in kilometers.

    Args:
        lat1, lon1: First coordinate in decimal degrees.
        lat2, lon2: Second coordinate in decimal degrees.

    Returns:
        float: Distance in kilometers rounded to 1 decimal place.
    """
    earth_radius_km = 6371.0

    phi1 = math.radians(lat1)
    phi2 = math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)

    a = (
        math.sin(delta_phi / 2.0) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0) ** 2
    )
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))

    return round(earth_radius_km * c, 1)


class MarketSearchService:
    """Service discovering nearby mandis based on farmer location and commodity trading."""

    def __init__(self, price_service: Optional[PriceService] = None):
        self.price_service = price_service or PriceService()

    def resolve_farmer_coordinates(
        self,
        db: Session,
        farmer_id: Optional[uuid.UUID],
        fallback_lat: Optional[float] = None,
        fallback_lon: Optional[float] = None,
    ) -> Optional[Tuple[float, float]]:
        """Resolve geographic coordinates from farmer profile/village or query fallbacks."""
        if fallback_lat is not None and fallback_lon is not None:
            return (fallback_lat, fallback_lon)

        if not farmer_id:
            return None

        farmer = db.get(UserProfile, farmer_id)
        if not farmer or not farmer.village_id:
            return None

        village = db.get(Village, farmer.village_id)
        if village and village.latitude is not None and village.longitude is not None:
            return (village.latitude, village.longitude)

        return None

    def find_nearby_mandis(
        self,
        db: Session,
        crop_id: uuid.UUID,
        latitude: float,
        longitude: float,
        radius_km: float = 500.0,
        sort_by: str = "distance",
        farmer_id: Optional[uuid.UUID] = None,
    ) -> NearbyMandisListResponse:
        """Find APMC mandis trading a crop within radius_km sorted by distance or price.

        Args:
            db: Database session
            crop_id: UUID of the crop
            latitude: Reference latitude
            longitude: Reference longitude
            radius_km: Search radius in km (default 500)
            sort_by: 'distance' (default) or 'price'
            farmer_id: Optional authenticated farmer UUID to populate is_followed

        Returns:
            NearbyMandisListResponse: List of mandis with distance, latest price, and trend.
        """
        crop = db.get(Crop, crop_id)
        if not crop:
            raise ValueError(f"Crop with ID '{crop_id}' not found.")

        # Get farmer's followed mandis if farmer_id supplied
        followed_market_ids = set()
        if farmer_id:
            follow_rows = (
                db.query(FarmerMarketFollow.market_id)
                .filter(FarmerMarketFollow.farmer_id == farmer_id)
                .all()
            )
            followed_market_ids = {r[0] for r in follow_rows}

        # Query all active mandis
        active_markets: List[Market] = (
            db.query(Market)
            .filter(Market.is_active.is_(True))
            .all()
        )

        results: List[NearbyMarketResponse] = []

        for m in active_markets:
            dist = haversine_distance_km(latitude, longitude, m.latitude, m.longitude)
            if dist > radius_km:
                continue

            # Fetch latest price quote
            latest_price = self.price_service.get_latest_price_for_mandi_crop(
                db=db, market_id=m.id, crop_id=crop_id
            )

            # Determine 15-day trend
            intel = self.price_service.get_15_day_intelligence(
                db=db, market_id=m.id, crop_id=crop_id
            )
            trend = intel.trend if intel else "STABLE"

            results.append(
                NearbyMarketResponse(
                    market_id=m.id,
                    name=m.name,
                    district=m.district,
                    state=m.state,
                    distance_km=dist,
                    latest_price=latest_price,
                    trend=trend,
                    is_followed=(m.id in followed_market_ids),
                )
            )

        # Sort results
        if sort_by.lower() == "price":
            # Highest modal price first, mandis with no price at the end
            results.sort(
                key=lambda x: (
                    -(x.latest_price.modal if x.latest_price else Decimal("-1")),
                    x.distance_km,
                )
            )
        else:
            # Default: Nearest distance first
            results.sort(key=lambda x: x.distance_km)

        return NearbyMandisListResponse(
            crop=crop.name_en,
            crop_id=crop.id,
            radius_km=radius_km,
            count=len(results),
            markets=results,
        )
