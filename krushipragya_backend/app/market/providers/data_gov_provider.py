"""Open Government Data (Data.gov.in) Mandi Price Provider."""
from datetime import date, datetime, timezone
from decimal import Decimal, InvalidOperation
import logging
from typing import Any, Dict, List, Optional
import httpx

from app.core.config import settings
from app.market.providers.base import BaseMarketDataProvider, RawMandiPriceRecord

logger = logging.getLogger(__name__)


class DataGovMarketProvider(BaseMarketDataProvider):
    """Adapter for Government of India Open Government Data (OGD) Mandi Price API."""

    def __init__(
        self,
        api_key: Optional[str] = None,
        resource_id: Optional[str] = None,
        base_url: Optional[str] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        self.api_key = api_key or settings.DATA_GOV_API_KEY
        self.resource_id = resource_id or settings.DATA_GOV_RESOURCE_ID
        self.base_url = (base_url or settings.DATA_GOV_BASE_URL).rstrip("/")
        self._http_client = http_client

    @property
    def source_code(self) -> str:
        return "OGD_INDIA"

    @property
    def source_name(self) -> str:
        return "Open Government Data (OGD) Platform India - DMI"

    @property
    def source_type(self) -> str:
        return "GOVERNMENT_OGD"

    async def fetch_daily_prices(
        self,
        state: Optional[str] = "Karnataka",
        district: Optional[str] = None,
        commodity: Optional[str] = None,
        target_date: Optional[date] = None,
        limit: int = 1000,
    ) -> List[RawMandiPriceRecord]:
        """Fetch daily mandi records from Data.gov.in OGD API."""
        if not self.api_key:
            logger.warning("Data.gov.in API key is not configured. Mandi sync skipped live fetch.")
            return []

        url = f"{self.base_url}/{self.resource_id}"
        params: Dict[str, Any] = {
            "api-key": self.api_key,
            "format": "json",
            "limit": limit,
        }
        if state:
            params["filters[state]"] = state
        if district:
            params["filters[district]"] = district
        if commodity:
            params["filters[commodity]"] = commodity
        if target_date:
            # Format expected by OGD API: DD/MM/YYYY or YYYY-MM-DD
            params["filters[arrival_date]"] = target_date.strftime("%d/%m/%Y")

        client = self._http_client or httpx.AsyncClient(timeout=30.0)
        should_close = self._http_client is None

        try:
            response = await client.get(url, params=params)
            response.raise_for_status()
            data = response.json()
            raw_records = data.get("records", [])
            return self._parse_records(raw_records)
        except Exception as exc:
            logger.error("Failed to fetch mandi prices from Data.gov.in: %s", exc)
            raise
        finally:
            if should_close:
                await client.aclose()

    def _parse_records(self, records: List[Dict[str, Any]]) -> List[RawMandiPriceRecord]:
        parsed = []
        now = datetime.now(timezone.utc)

        for r in records:
            try:
                # Handle dates in formats: '18/09/2026', '2026-09-18'
                raw_date = str(r.get("arrival_date", "")).strip()
                if "/" in raw_date:
                    parts = raw_date.split("/")
                    if len(parts) == 3:
                        arrival_date = date(int(parts[2]), int(parts[1]), int(parts[0]))
                    else:
                        continue
                elif "-" in raw_date:
                    arrival_date = date.fromisoformat(raw_date)
                else:
                    arrival_date = date.today()

                min_p = Decimal(str(r.get("min_price", 0)))
                max_p = Decimal(str(r.get("max_price", 0)))
                modal_p = Decimal(str(r.get("modal_price", 0)))

                # Basic validation: modal price must be non-zero and within min/max bounds
                if modal_p <= 0 or min_p <= 0:
                    continue

                if min_p > max_p:
                    min_p, max_p = max_p, min_p
                if modal_p < min_p:
                    modal_p = min_p
                if modal_p > max_p:
                    modal_p = max_p

                record = RawMandiPriceRecord(
                    source_code=self.source_code,
                    source_record_id=str(r.get("_id") or r.get("id") or ""),
                    state=str(r.get("state", "Karnataka")).strip(),
                    district=str(r.get("district", "")).strip(),
                    market_name=str(r.get("market", "")).strip(),
                    commodity_raw=str(r.get("commodity", "")).strip(),
                    variety=str(r.get("variety", "Standard")).strip(),
                    grade=str(r.get("grade", "FAQ")).strip(),
                    arrival_date=arrival_date,
                    min_price=min_p,
                    max_price=max_p,
                    modal_price=modal_p,
                    arrival_quantity=Decimal(str(r.get("arrival_quantity") or 0)),
                    unit=str(r.get("unit", "Quintal")).strip(),
                    fetched_at=now,
                )
                parsed.append(record)
            except (InvalidOperation, ValueError, TypeError) as parse_err:
                logger.debug("Skipping unparseable mandi record: %s (error: %s)", r, parse_err)
                continue

        return parsed
