"""Market Follow Service: Farmer bookmarking and following of APMC Mandis."""
import logging
from typing import List
import uuid

from sqlalchemy.orm import Session

from app.market.models.market import Market
from app.market.models.market_follow import FarmerMarketFollow
from app.market.schemas.market import MarketResponse
from app.models.user_profile import UserProfile

logger = logging.getLogger(__name__)


class MarketFollowService:
    """Service managing farmer bookmarks / follows of APMC mandis."""

    def follow_market(self, db: Session, farmer_id: uuid.UUID, market_id: uuid.UUID) -> bool:
        """Add a follow bookmark for a farmer on a specific market yard."""
        farmer = db.get(UserProfile, farmer_id)
        if not farmer:
            raise ValueError(f"Farmer with ID '{farmer_id}' not found.")

        market = db.get(Market, market_id)
        if not market:
            raise ValueError(f"Market with ID '{market_id}' not found.")

        existing = (
            db.query(FarmerMarketFollow)
            .filter(
                FarmerMarketFollow.farmer_id == farmer_id,
                FarmerMarketFollow.market_id == market_id,
            )
            .first()
        )
        if existing:
            return True  # Already followed

        follow = FarmerMarketFollow(farmer_id=farmer_id, market_id=market_id)
        db.add(follow)
        db.commit()
        logger.info("Farmer %s followed market %s", farmer_id, market_id)
        return True

    def unfollow_market(self, db: Session, farmer_id: uuid.UUID, market_id: uuid.UUID) -> bool:
        """Remove a follow bookmark for a farmer on a market yard."""
        follow = (
            db.query(FarmerMarketFollow)
            .filter(
                FarmerMarketFollow.farmer_id == farmer_id,
                FarmerMarketFollow.market_id == market_id,
            )
            .first()
        )
        if follow:
            db.delete(follow)
            db.commit()
            logger.info("Farmer %s unfollowed market %s", farmer_id, market_id)
        return True

    def get_followed_markets(self, db: Session, farmer_id: uuid.UUID) -> List[MarketResponse]:
        """List all APMC mandis followed by a farmer."""
        records = (
            db.query(Market)
            .join(FarmerMarketFollow, FarmerMarketFollow.market_id == Market.id)
            .filter(FarmerMarketFollow.farmer_id == farmer_id)
            .order_by(Market.name.asc())
            .all()
        )
        return [MarketResponse.model_validate(m) for m in records]
