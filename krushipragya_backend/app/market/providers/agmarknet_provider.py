"""AGMARKNET and e-NAM market data providers."""
from datetime import date
import logging
from typing import List, Optional
import httpx

from app.core.config import settings
from app.market.providers.base import BaseMarketDataProvider, RawMandiPriceRecord

logger = logging.getLogger(__name__)


class AgmarknetProvider(BaseMarketDataProvider):
    """Adapter for Directorate of Marketing & Inspection (DMI) AGMARKNET portal."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        self.base_url = (base_url or settings.AGMARKNET_BASE_URL).rstrip("/")
        self._http_client = http_client

    @property
    def source_code(self) -> str:
        return "AGMARKNET"

    @property
    def source_name(self) -> str:
        return "AGMARKNET - Agricultural Marketing Information Network"

    @property
    def source_type(self) -> str:
        return "AGMARKNET_PORTAL"

    async def fetch_daily_prices(
        self,
        state: Optional[str] = "Karnataka",
        district: Optional[str] = None,
        commodity: Optional[str] = None,
        target_date: Optional[date] = None,
        limit: int = 1000,
    ) -> List[RawMandiPriceRecord]:
        """Fetch daily arrivals from AGMARKNET API or scrapers."""
        # AGMARKNET provides HTML bulletins and SOAP/REST endpoints depending on state APMC integration
        logger.info("Polling AGMARKNET for state=%s commodity=%s", state, commodity)
        return []


class ENAMProvider(BaseMarketDataProvider):
    """Adapter for National Agriculture Market (e-NAM) electronic trading platform."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        http_client: Optional[httpx.AsyncClient] = None,
    ):
        self.base_url = (base_url or settings.ENAM_BASE_URL).rstrip("/")
        self._http_client = http_client

    @property
    def source_code(self) -> str:
        return "ENAM"

    @property
    def source_name(self) -> str:
        return "National Agriculture Market (e-NAM)"

    @property
    def source_type(self) -> str:
        return "ENAM_PORTAL"

    async def fetch_daily_prices(
        self,
        state: Optional[str] = "Karnataka",
        district: Optional[str] = None,
        commodity: Optional[str] = None,
        target_date: Optional[date] = None,
        limit: int = 1000,
    ) -> List[RawMandiPriceRecord]:
        """Fetch electronic trading price discovery from e-NAM."""
        logger.info("Polling e-NAM for state=%s commodity=%s", state, commodity)
        return []
