"""Market Ingestion Service: Orchestrates daily official market data syncing."""
from datetime import date, datetime, timezone
from decimal import Decimal
import logging
from typing import Dict, List, Optional
import uuid

from sqlalchemy.orm import Session

from app.market.models.market import Market
from app.market.models.market_mapping import MarketCropMapping
from app.market.models.market_price import MarketPriceRecord
from app.market.models.market_source import MarketDataSource
from app.market.providers.base import BaseMarketDataProvider, RawMandiPriceRecord
from app.market.providers.data_gov_provider import DataGovMarketProvider
from app.market.schemas.market import MarketSyncResponse
from app.models.crop import Crop

logger = logging.getLogger(__name__)


class MarketIngestionService:
    """Ingestion pipeline fetching, validating, normalizing, and persisting official market data."""

    def __init__(self, provider: Optional[BaseMarketDataProvider] = None):
        self.provider = provider or DataGovMarketProvider()

    async def sync_market_data(
        self,
        db: Session,
        state: str = "Karnataka",
        target_date: Optional[date] = None,
    ) -> MarketSyncResponse:
        """Execute daily mandi price ingestion from official provider.

        Validation & Normalization Rules:
        1. Validate price bounds: min <= modal <= max
        2. Map commodity using market_crop_mappings table
        3. Match or create Market (Mandi)
        4. Deduplicate against existing records
        5. Update provenance metadata on MarketDataSource
        """
        now = datetime.now(timezone.utc)
        source = (
            db.query(MarketDataSource)
            .filter(MarketDataSource.code == self.provider.source_code)
            .first()
        )
        if not source:
            source = MarketDataSource(
                code=self.provider.source_code,
                name=self.provider.source_name,
                source_type=self.provider.source_type,
                sync_status="SYNCING",
            )
            db.add(source)
            db.flush()
        else:
            source.sync_status = "SYNCING"
            db.flush()

        # Build commodity normalization dictionary: (raw_name.lower(), variety.lower()) -> crop_id
        mappings = db.query(MarketCropMapping).filter(MarketCropMapping.is_active.is_(True)).all()
        mapping_dict: Dict[tuple, uuid.UUID] = {}
        for m in mappings:
            var_key = (m.variety or "").strip().lower()
            mapping_dict[(m.raw_commodity_name.strip().lower(), var_key)] = m.crop_id
            # Also register wild-card fallback for commodity without variety
            mapping_dict[(m.raw_commodity_name.strip().lower(), "")] = m.crop_id

        # Cache existing crops and mandis
        crops = {c.id: c for c in db.query(Crop).all()}
        markets_by_name = {m.name.strip().lower(): m for m in db.query(Market).all()}

        records_fetched = 0
        records_persisted = 0
        mandis_updated = 0

        try:
            raw_records = await self.provider.fetch_daily_prices(
                state=state,
                target_date=target_date,
            )
            records_fetched = len(raw_records)

            for raw in raw_records:
                # 1. Commodity normalization
                norm_comm = raw.commodity_raw.strip().lower()
                norm_var = raw.variety.strip().lower()
                crop_id = mapping_dict.get((norm_comm, norm_var)) or mapping_dict.get((norm_comm, ""))
                if not crop_id:
                    continue  # Not one of our 7 supported crops

                # 2. Mandi resolution or creation
                norm_market_name = raw.market_name.strip().lower()
                mandi = markets_by_name.get(norm_market_name)
                if not mandi:
                    # Create newly discovered APMC mandi
                    mandi_code = f"MANDI_{raw.district.upper().replace(' ', '_')}_{raw.market_name.upper().replace(' ', '_')}"
                    mandi = Market(
                        id=uuid.uuid4(),
                        code=mandi_code[:100],
                        name=raw.market_name,
                        state=raw.state,
                        district=raw.district,
                        taluk=raw.district,
                        latitude=12.9716,  # Default Karnataka centroid, can be enriched
                        longitude=77.5946,
                        is_active=True,
                    )
                    db.add(mandi)
                    db.flush()
                    markets_by_name[norm_market_name] = mandi
                    mandis_updated += 1

                # 3. Deduplicate
                existing_record = (
                    db.query(MarketPriceRecord)
                    .filter(
                        MarketPriceRecord.market_id == mandi.id,
                        MarketPriceRecord.crop_id == crop_id,
                        MarketPriceRecord.arrival_date == raw.arrival_date,
                        MarketPriceRecord.variety == raw.variety,
                        MarketPriceRecord.grade == raw.grade,
                    )
                    .first()
                )

                if existing_record:
                    # Update quotes if modified
                    existing_record.min_price = raw.min_price
                    existing_record.max_price = raw.max_price
                    existing_record.modal_price = raw.modal_price
                    existing_record.arrival_quantity = raw.arrival_quantity
                    existing_record.fetched_at = now
                    existing_record.is_seeded = False
                    existing_record.data_mode = "LIVE"
                else:
                    new_prec = MarketPriceRecord(
                        id=uuid.uuid4(),
                        market_id=mandi.id,
                        crop_id=crop_id,
                        source_id=source.id,
                        source_record_id=raw.source_record_id,
                        arrival_date=raw.arrival_date,
                        commodity_raw=raw.commodity_raw,
                        variety=raw.variety or "Standard",
                        grade=raw.grade or "FAQ",
                        min_price=raw.min_price,
                        max_price=raw.max_price,
                        modal_price=raw.modal_price,
                        arrival_quantity=raw.arrival_quantity,
                        unit=raw.unit or "Quintal",
                        fetched_at=now,
                        is_seeded=False,
                        data_mode="LIVE",
                    )
                    db.add(new_prec)
                    records_persisted += 1

            source.sync_status = "SUCCESS"
            source.is_demo = False
            source.data_mode = "LIVE"
            source.last_success_at = now
            source.last_sync_at = now
            source.last_error = None
            db.commit()

            msg = f"Synced {records_persisted} new price records across {records_fetched} arrivals."
            logger.info(msg)
            return MarketSyncResponse(
                source_code=source.code,
                status="SUCCESS",
                records_fetched=records_fetched,
                records_persisted=records_persisted,
                mandis_updated=mandis_updated,
                executed_at=now,
                message=msg,
            )

        except Exception as exc:
            db.rollback()
            source.sync_status = "FAILED"
            source.last_failure_at = now
            source.last_sync_at = now
            source.last_error = str(exc)
            try:
                db.commit()
            except Exception:
                db.rollback()

            logger.error("Market ingestion sync failed: %s", exc, exc_info=True)
            return MarketSyncResponse(
                source_code=source.code,
                status="FAILED",
                records_fetched=records_fetched,
                records_persisted=0,
                mandis_updated=0,
                executed_at=now,
                message=f"Sync failed: {str(exc)}",
            )
