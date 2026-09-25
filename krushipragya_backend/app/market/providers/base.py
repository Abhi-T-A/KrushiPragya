"""Base market data provider interface and raw record schemas."""
from abc import ABC, abstractmethod
from dataclasses import dataclass
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional


@dataclass
class RawMandiPriceRecord:
    """Raw un-normalized market price record as received from an upstream authority."""

    source_code: str
    source_record_id: Optional[str]
    state: str
    district: str
    market_name: str
    commodity_raw: str
    variety: str
    grade: str
    arrival_date: date
    min_price: Decimal
    max_price: Decimal
    modal_price: Decimal
    arrival_quantity: Decimal
    unit: str
    fetched_at: datetime


class BaseMarketDataProvider(ABC):
    """Abstract base class for official agricultural market data providers (OGD, AGMARKNET, e-NAM)."""

    @property
    @abstractmethod
    def source_code(self) -> str:
        """Unique source identifier (e.g. OGD_INDIA, AGMARKNET, ENAM)."""
        pass

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Human-readable provider name."""
        pass

    @property
    @abstractmethod
    def source_type(self) -> str:
        """Category type (GOVERNMENT_OGD, AGMARKNET_PORTAL, ENAM_PORTAL)."""
        pass

    @abstractmethod
    async def fetch_daily_prices(
        self,
        state: Optional[str] = None,
        district: Optional[str] = None,
        commodity: Optional[str] = None,
        target_date: Optional[date] = None,
        limit: int = 1000,
    ) -> List[RawMandiPriceRecord]:
        """Fetch daily mandi records from the official upstream API or export.

        Args:
            state: Filter state (e.g. 'Karnataka')
            district: Filter district (e.g. 'Dakshina Kannada')
            commodity: Filter commodity name
            target_date: Date of arrival records
            limit: Maximum records to retrieve

        Returns:
            List[RawMandiPriceRecord]: Parsed raw market records.
        """
        pass
