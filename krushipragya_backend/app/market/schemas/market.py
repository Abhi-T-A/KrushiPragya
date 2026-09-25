"""Pydantic schemas for the KrushiPragya Market Domain."""
from datetime import date, datetime
from decimal import Decimal
from typing import List, Optional
import uuid
from pydantic import BaseModel, ConfigDict, Field


# ==============================================================================
# 1. Market / Mandi Schemas
# ==============================================================================

class LatestPriceInfo(BaseModel):
    """Latest reported APMC market price quote."""
    model_config = ConfigDict(populate_by_name=True)

    min_price: Decimal = Field(..., alias="min", serialization_alias="min", description="Reported minimum price in INR")
    max_price: Decimal = Field(..., alias="max", serialization_alias="max", description="Reported maximum price in INR")
    modal: Decimal = Field(..., description="Reported modal price in INR")
    unit: str = Field(default="quintal", description="Unit of pricing (e.g. quintal)")
    price_date: date = Field(..., alias="date", serialization_alias="date", description="Official price quotation date")
    arrival_quantity: Optional[Decimal] = Field(default=None, description="Arrival quantity")
    is_seeded: bool = Field(default=True, description="True if quote is from demo benchmark seed; False if live government sync")
    data_mode: str = Field(default="DEMO_SEEDED", description="Data provenance mode: LIVE or DEMO_SEEDED")

    @property
    def min(self) -> Decimal:
        return self.min_price

    @property
    def max(self) -> Decimal:
        return self.max_price

    @property
    def date(self) -> date:
        return self.price_date


class MarketResponse(BaseModel):
    """APMC Mandi summary response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    state: str
    district: str
    taluk: Optional[str] = None
    latitude: float
    longitude: float
    is_active: bool


class NearbyMarketResponse(BaseModel):
    """APMC Mandi item in Nearby Mandis discovery list."""
    market_id: uuid.UUID
    name: str
    district: str
    state: str
    distance_km: float = Field(..., description="Haversine distance in kilometers from farmer location")
    latest_price: Optional[LatestPriceInfo] = None
    trend: str = Field(default="STABLE", description="15-day price direction: UP, DOWN, STABLE")
    is_followed: bool = Field(default=False, description="Whether farmer follows this mandi")


class NearbyMandisListResponse(BaseModel):
    """Response wrapper for nearby mandis discovery."""
    crop: str = Field(..., description="Canonical crop name")
    crop_id: uuid.UUID
    radius_km: float
    count: int
    markets: List[NearbyMarketResponse]


# ==============================================================================
# 2. Price Record & 15-Day Intelligence Schemas
# ==============================================================================

class MarketPriceRecordResponse(BaseModel):
    """Individual official mandi price record."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    market_id: uuid.UUID
    crop_id: uuid.UUID
    arrival_date: date
    commodity_raw: str
    variety: str
    grade: str
    min_price: Decimal
    max_price: Decimal
    modal_price: Decimal
    arrival_quantity: Decimal
    unit: str
    fetched_at: datetime
    is_seeded: bool = True
    data_mode: str = "DEMO_SEEDED"


class PriceHistoryItem(BaseModel):
    """Single date point in price history."""
    model_config = ConfigDict(populate_by_name=True)

    price_date: date = Field(..., alias="date", serialization_alias="date")
    min_price: Decimal
    max_price: Decimal
    modal_price: Decimal
    arrival_quantity: Decimal
    variety: str
    unit: str
    is_seeded: bool = True
    data_mode: str = "DEMO_SEEDED"

    @property
    def date(self) -> date:
        return self.price_date


class PriceIntelligenceResponse(BaseModel):
    """15-day price intelligence facts computed directly from official data."""
    crop: str
    crop_id: uuid.UUID
    market_id: uuid.UUID
    market_name: str
    current: Decimal = Field(..., description="Today's/most recent reported modal price")
    current_min: Decimal
    current_max: Decimal
    yesterday: Optional[Decimal] = Field(None, description="Previous session modal price")
    highest_15_days: Decimal = Field(..., description="Highest price observed in past 15 days")
    lowest_15_days: Decimal = Field(..., description="Lowest price observed in past 15 days")
    trend: str = Field(..., description="Price direction: UP, DOWN, STABLE")
    change_percent: float = Field(..., description="Percentage change vs previous session")
    price_date: date = Field(..., description="Date of latest official price quotation")
    unit: str = Field(default="quintal")
    history: List[PriceHistoryItem] = Field(default_factory=list)
    is_seeded: bool = Field(default=True, description="True if based on demo benchmark seed; False if live government sync")
    data_mode: str = Field(default="DEMO_SEEDED", description="Data provenance mode: LIVE or DEMO_SEEDED")
    source_name: Optional[str] = Field(default="Demo Benchmark Mandi Rates", description="Data source name")


class MarketDetailResponse(BaseModel):
    """Detailed Mandi view including today's quote, 15-day trends and follow status."""
    market: MarketResponse
    crop_id: Optional[uuid.UUID] = None
    crop_name: Optional[str] = None
    is_followed: bool = False
    intelligence: Optional[PriceIntelligenceResponse] = None


# ==============================================================================
# 3. Reference Mandi Price (for Produce Listings & Buyer Transparency)
# ==============================================================================

class ReferenceMandiPrice(BaseModel):
    """Official APMC Mandi reference price attached to a produce listing for price discovery."""
    mandi_name: str
    mandi_id: uuid.UUID
    district: str
    state: str
    distance_km: Optional[float] = None
    min_price: Decimal
    modal_price: Decimal
    max_price: Decimal
    price_date: date
    unit: str = "quintal"
    is_seeded: bool = Field(default=True, description="True if reference is demo benchmark seed; False if live sync")
    data_mode: str = Field(default="DEMO_SEEDED", description="Data provenance mode: LIVE or DEMO_SEEDED")


# ==============================================================================
# 4. Produce Listing Schemas (Farmer Produce)
# ==============================================================================

class ProduceListingCreate(BaseModel):
    """Request payload to create a produce listing."""
    crop_id: uuid.UUID
    quantity: Decimal = Field(..., gt=0, description="Available produce quantity")
    unit: str = Field(default="quintal", description="Unit of measurement (quintal, kg, bag, tonne)")
    quality_grade: str = Field(default="A", description="Quality grade (e.g. A, B, Premium)")
    expected_price: Decimal = Field(..., gt=0, description="Farmer's asking price per unit in INR (₹)")
    location: str = Field(..., min_length=2, max_length=200, description="Village / pickup location")


class ProduceListingUpdate(BaseModel):
    """Partial update payload for produce listing."""
    quantity: Optional[Decimal] = Field(None, gt=0)
    unit: Optional[str] = None
    quality_grade: Optional[str] = None
    expected_price: Optional[Decimal] = Field(None, gt=0)
    location: Optional[str] = None
    status: Optional[str] = Field(None, description="LISTED, OFFER_RECEIVED, NEGOTIATING, SOLD, DELISTED")


class ProduceListingResponse(BaseModel):
    """Produce listing summary response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    farmer_id: uuid.UUID
    crop_id: uuid.UUID
    quantity: Decimal
    unit: str
    quality_grade: str
    expected_price: Decimal
    location: str
    status: str
    created_at: datetime
    updated_at: datetime


class ProduceListingDetailResponse(BaseModel):
    """Full produce listing details for buyers and farmers, including transparent Mandi reference."""
    listing: ProduceListingResponse
    crop_name: str
    farmer_name: Optional[str] = None
    # Key principle: Official Mandi reference price displayed alongside farmer's expected asking price
    reference_mandi: Optional[ReferenceMandiPrice] = Field(
        None,
        description="Factual official Mandi price reference from the nearest active mandi",
    )
    offers_count: int = 0


# ==============================================================================
# 5. Buyer Offer Schemas (Buyer ↔ Farmer Negotiation)
# ==============================================================================

class BuyerOfferCreate(BaseModel):
    """Request payload for a buyer submitting an offer on a produce listing."""
    offered_price: Decimal = Field(..., gt=0, description="Buyer's offer price per unit in INR (₹)")
    quantity: Decimal = Field(..., gt=0, description="Desired purchase quantity")
    message: Optional[str] = Field(None, max_length=500, description="Optional note or negotiation terms")


class BuyerOfferResponse(BaseModel):
    """Buyer offer response schema."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    listing_id: uuid.UUID
    buyer_id: uuid.UUID
    offered_price: Decimal
    quantity: Decimal
    message: Optional[str] = None
    status: str = Field(..., description="PENDING, ACCEPTED, REJECTED, NEGOTIATING, COMPLETED")
    created_at: datetime
    updated_at: datetime


class BuyerOfferWithContextResponse(BaseModel):
    """Buyer offer response with complete transparent price discovery context."""
    offer: BuyerOfferResponse
    listing: ProduceListingResponse
    buyer_name: Optional[str] = None
    farmer_expected_price: Decimal
    reference_mandi: Optional[ReferenceMandiPrice] = None


class OfferStatusAction(BaseModel):
    """Action payload to accept, reject, or negotiate an offer."""
    action: str = Field(..., pattern="^(ACCEPT|REJECT)$", description="Action to perform: ACCEPT or REJECT")
    notes: Optional[str] = Field(None, max_length=500)


# ==============================================================================
# 6. Provenance & Ingestion Sync Schemas
# ==============================================================================

class MarketDataSourceResponse(BaseModel):
    """Data source provenance status response."""
    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    code: str
    name: str
    source_type: str
    base_url: Optional[str] = None
    is_active: bool
    last_success_at: Optional[datetime] = None
    last_failure_at: Optional[datetime] = None
    last_sync_at: Optional[datetime] = None
    sync_status: str
    is_demo: bool = False
    data_mode: str = "LIVE"
    last_error: Optional[str] = None


class MarketSyncRequest(BaseModel):
    """Request payload to trigger market data ingestion."""
    source_code: Optional[str] = Field(default="OGD_INDIA", description="Source to ingest: OGD_INDIA, ALL")
    target_date: Optional[date] = None
    state: Optional[str] = "Karnataka"


class MarketSyncResponse(BaseModel):
    """Response summary of market data sync execution."""
    source_code: str
    status: str
    records_fetched: int
    records_persisted: int
    mandis_updated: int
    executed_at: datetime
    message: str
