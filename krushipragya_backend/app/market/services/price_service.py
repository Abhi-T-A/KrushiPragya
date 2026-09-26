"""Price Service: 15-day price intelligence and mathematical trend calculation.

Strict Architectural Rule:
All price calculations, highs, lows, and trends are computed mathematically.
The LLM is NEVER used to invent or guess prices.
"""
from datetime import date, datetime, timedelta
from decimal import Decimal
import logging
from typing import List, Optional
import uuid

from sqlalchemy import and_, desc
from sqlalchemy.orm import Session

from app.market.models.market import Market
from app.market.models.market_price import MarketPriceRecord
from app.market.schemas.market import (
    LatestPriceInfo,
    PriceHistoryItem,
    PriceIntelligenceResponse,
)
from app.models.crop import Crop

logger = logging.getLogger(__name__)


class PriceService:
    """Service providing mathematical price discovery and 15-day intelligence."""

    def get_latest_price_for_mandi_crop(
        self,
        db: Session,
        market_id: uuid.UUID,
        crop_id: uuid.UUID,
    ) -> Optional[LatestPriceInfo]:
        """Retrieve the most recent reported price quote for a mandi and crop."""
        latest_record = (
            db.query(MarketPriceRecord)
            .filter(
                MarketPriceRecord.market_id == market_id,
                MarketPriceRecord.crop_id == crop_id,
            )
            .order_by(desc(MarketPriceRecord.arrival_date))
            .first()
        )
        if not latest_record:
            return None

        return LatestPriceInfo(
            min=latest_record.min_price,
            max=latest_record.max_price,
            modal=latest_record.modal_price,
            unit=latest_record.unit.lower(),
            date=latest_record.arrival_date,
            arrival_quantity=latest_record.arrival_quantity,
            is_seeded=getattr(latest_record, "is_seeded", True),
            data_mode=getattr(latest_record, "data_mode", "DEMO_SEEDED"),
        )

    def get_15_day_intelligence(
        self,
        db: Session,
        market_id: uuid.UUID,
        crop_id: uuid.UUID,
        anchor_date: Optional[date] = None,
    ) -> Optional[PriceIntelligenceResponse]:
        """Compute factual 15-day price intelligence, highs, lows, and trends.

        Args:
            db: Database session
            market_id: UUID of the APMC mandi
            crop_id: UUID of the canonical crop
            anchor_date: Optional reference date (defaults to latest recorded arrival date)

        Returns:
            Optional[PriceIntelligenceResponse]: Computed statistics or None if no data exists.
        """
        # 1. Fetch market and crop info
        market = db.get(Market, market_id)
        crop = db.get(Crop, crop_id)
        if not market or not crop:
            return None

        # 2. Find latest price date if anchor not provided
        if not anchor_date:
            latest_rec = (
                db.query(MarketPriceRecord)
                .filter(
                    MarketPriceRecord.market_id == market_id,
                    MarketPriceRecord.crop_id == crop_id,
                )
                .order_by(desc(MarketPriceRecord.arrival_date))
                .first()
            )
            if not latest_rec:
                return None
            anchor_date = latest_rec.arrival_date

        start_date = anchor_date - timedelta(days=15)

        # 3. Fetch all price records in the 15-day window
        records: List[MarketPriceRecord] = (
            db.query(MarketPriceRecord)
            .filter(
                MarketPriceRecord.market_id == market_id,
                MarketPriceRecord.crop_id == crop_id,
                MarketPriceRecord.arrival_date >= start_date,
                MarketPriceRecord.arrival_date <= anchor_date,
            )
            .order_by(MarketPriceRecord.arrival_date.asc())
            .all()
        )

        if not records:
            return None

        # 4. Map into daily history
        history_items: List[PriceHistoryItem] = []
        modal_prices: List[Decimal] = []
        all_min: List[Decimal] = []
        all_max: List[Decimal] = []

        for r in records:
            history_items.append(
                PriceHistoryItem(
                    date=r.arrival_date,
                    min_price=r.min_price,
                    max_price=r.max_price,
                    modal_price=r.modal_price,
                    arrival_quantity=r.arrival_quantity,
                    variety=r.variety,
                    unit=r.unit.lower(),
                    is_seeded=getattr(r, "is_seeded", True),
                    data_mode=getattr(r, "data_mode", "DEMO_SEEDED"),
                )
            )
            modal_prices.append(r.modal_price)
            all_min.append(r.min_price)
            all_max.append(r.max_price)

        current_record = records[-1]
        current_modal = current_record.modal_price
        current_min = current_record.min_price
        current_max = current_record.max_price

        # Yesterday / previous available session price
        yesterday_modal: Optional[Decimal] = None
        if len(records) > 1:
            yesterday_modal = records[-2].modal_price

        # Highest and lowest in 15 days
        highest_15 = max(all_max) if all_max else current_max
        lowest_15 = min(all_min) if all_min else current_min

        # Percentage change vs previous reported session
        if yesterday_modal and yesterday_modal > 0:
            change_pct = float(
                round(((current_modal - yesterday_modal) / yesterday_modal) * Decimal("100.0"), 2)
            )
        else:
            change_pct = 0.0

        # Mathematical trend calculation across window
        if len(modal_prices) >= 2:
            first_modal = modal_prices[0]
            last_modal = modal_prices[-1]
            overall_diff_pct = float(((last_modal - first_modal) / first_modal) * Decimal("100.0"))
            if overall_diff_pct > 1.0:
                trend = "UP"
            elif overall_diff_pct < -1.0:
                trend = "DOWN"
            else:
                trend = "STABLE"
        else:
            trend = "STABLE"

        is_seeded = getattr(current_record, "is_seeded", True)
        data_mode = getattr(current_record, "data_mode", "DEMO_SEEDED")
        source_name = "Demo Benchmark Mandi Rates" if is_seeded else "Open Government Data (OGD)"

        return PriceIntelligenceResponse(
            crop=crop.name_en,
            crop_id=crop.id,
            market_id=market.id,
            market_name=market.name,
            current=current_modal,
            current_min=current_min,
            current_max=current_max,
            yesterday=yesterday_modal,
            highest_15_days=highest_15,
            lowest_15_days=lowest_15,
            trend=trend,
            change_percent=change_pct,
            price_date=current_record.arrival_date,
            unit=current_record.unit.lower(),
            history=history_items,
            is_seeded=is_seeded,
            data_mode=data_mode,
            source_name=source_name,
            latest_price=current_modal,
            trend_15d=trend,
            period_min_price=lowest_15,
            period_max_price=highest_15,
        )
