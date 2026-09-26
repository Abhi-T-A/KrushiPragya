"""Comprehensive test suite for KrushiPragya Market Domain:
- Mandi Discovery & Haversine Distance
- 15-Day Mathematical Price Intelligence (No LLM)
- Farmer Mandi Following / Bookmarks
- Produce Listings with Factual Reference Mandi Pricing
- Buyer Offers & Farmer Negotiation Workflow
- Role-Based Access Control Enforcement (FARMER vs BUYER vs ADMIN)
"""
from datetime import date, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any, Dict, List, Optional
import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.security import create_access_token
from app.database.connection import get_db
from app.main import app
from app.market.models.market import Market
from app.market.models.market_follow import FarmerMarketFollow
from app.market.models.market_mapping import MarketCropMapping
from app.market.models.market_price import MarketPriceRecord
from app.market.models.market_source import MarketDataSource
from app.models.crop import Crop
from app.models.marketplace import BuyerOffer, MarketplaceTransaction, ProduceListing
from app.models.role import UserRole
from app.models.user_profile import UserProfile
from app.models.village import Village

client = TestClient(app)


def auth_header(user_id: uuid.UUID, email: str = "user@krushipragya.com") -> dict:
    """Helper to mint a valid Bearer token header for the given user UUID."""
    token = create_access_token(
        data={"sub": str(user_id), "email": email, "aud": "authenticated"},
        expires_delta=timedelta(hours=1),
    )
    return {"Authorization": f"Bearer {token}"}


class MockMarketDBSession:
    """In-memory database session supporting full relational query/write for market tests."""

    def __init__(self):
        self.crops: Dict[uuid.UUID, Crop] = {}
        self.markets: Dict[uuid.UUID, Market] = {}
        self.sources: Dict[uuid.UUID, MarketDataSource] = {}
        self.mappings: List[MarketCropMapping] = []
        self.price_records: List[MarketPriceRecord] = []
        self.users: Dict[uuid.UUID, UserProfile] = {}
        self.user_roles: List[UserRole] = []
        self.follows: List[FarmerMarketFollow] = []
        self.listings: Dict[uuid.UUID, ProduceListing] = {}
        self.offers: Dict[uuid.UUID, BuyerOffer] = {}
        self.transactions: Dict[uuid.UUID, MarketplaceTransaction] = {}
        self.villages: Dict[str, Village] = {}

    def get(self, model, entity_id):
        if model is Crop:
            return self.crops.get(entity_id)
        if model is Market:
            return self.markets.get(entity_id)
        if model is UserProfile:
            return self.users.get(entity_id)
        if model is ProduceListing:
            return self.listings.get(entity_id)
        if model is BuyerOffer:
            return self.offers.get(entity_id)
        if model is MarketplaceTransaction:
            return self.transactions.get(entity_id)
        if model is MarketDataSource:
            return self.sources.get(entity_id)
        if model is Village:
            return self.villages.get(entity_id)
        return None

    def add(self, entity):
        now = datetime.now(timezone.utc)
        if hasattr(entity, "created_at") and getattr(entity, "created_at", None) is None:
            entity.created_at = now
        if hasattr(entity, "updated_at") and getattr(entity, "updated_at", None) is None:
            entity.updated_at = now

        if isinstance(entity, Crop):
            self.crops[entity.id] = entity
        elif isinstance(entity, Market):
            self.markets[entity.id] = entity
        elif isinstance(entity, MarketDataSource):
            self.sources[entity.id] = entity
        elif isinstance(entity, MarketCropMapping):
            self.mappings.append(entity)
        elif isinstance(entity, MarketPriceRecord):
            self.price_records.append(entity)
        elif isinstance(entity, UserProfile):
            self.users[entity.id] = entity
        elif isinstance(entity, UserRole):
            self.user_roles.append(entity)
        elif isinstance(entity, FarmerMarketFollow):
            self.follows.append(entity)
        elif isinstance(entity, ProduceListing):
            self.listings[entity.id] = entity
        elif isinstance(entity, BuyerOffer):
            self.offers[entity.id] = entity
        elif isinstance(entity, MarketplaceTransaction):
            self.transactions[entity.id] = entity

    def delete(self, entity):
        if isinstance(entity, FarmerMarketFollow):
            self.follows = [f for f in self.follows if f.id != entity.id and not (f.farmer_id == entity.farmer_id and f.market_id == entity.market_id)]
        elif isinstance(entity, ProduceListing):
            self.listings.pop(entity.id, None)
        elif isinstance(entity, BuyerOffer):
            self.offers.pop(entity.id, None)
        elif isinstance(entity, MarketplaceTransaction):
            self.transactions.pop(entity.id, None)

    def commit(self):
        pass

    def flush(self):
        pass

    def refresh(self, entity):
        pass

    def rollback(self):
        pass

    def query(self, *entities):
        return MockMarketQuery(self, entities)


class MockMarketQuery:
    """Mock query engine matching SQLAlchemy query patterns."""

    def __init__(self, session: MockMarketDBSession, entities):
        self.session = session
        self.entities = entities
        self._filters = []
        self._order_by = None
        self._limit = None
        self._offset = None
        self._join_target = None

    def filter(self, *criteria):
        self._filters.extend(criteria)
        return self

    def join(self, target, *args, **kwargs):
        self._join_target = target
        return self

    def order_by(self, *args, **kwargs):
        self._order_by = args
        return self

    def limit(self, val):
        self._limit = val
        return self

    def offset(self, val):
        self._offset = val
        return self

    def count(self) -> int:
        return len(self.all())

    def first(self):
        res = self.all()
        return res[0] if res else None

    def all(self) -> List[Any]:
        entity_name = str(self.entities[0]).lower()

        # 1. ProduceListing query
        if "producelisting" in entity_name:
            listings = list(self.session.listings.values())
            for crit in self._filters:
                c_str = str(crit).lower()
                val = getattr(getattr(crit, "right", None), "value", None)
                if "farmer_id" in c_str and val is not None:
                    listings = [l for l in listings if str(l.farmer_id) == str(val)]
                if "crop_id" in c_str and val is not None:
                    listings = [l for l in listings if str(l.crop_id) == str(val)]
                if "status" in c_str and val is not None:
                    listings = [l for l in listings if str(l.status).upper() == str(val).upper()]
            listings.sort(key=lambda l: l.created_at, reverse=True)
            if self._offset is not None:
                listings = listings[self._offset:]
            if self._limit is not None:
                listings = listings[:self._limit]
            return listings

        # 2. BuyerOffer query
        if "buyeroffer" in entity_name:
            offers = list(self.session.offers.values())
            for crit in self._filters:
                c_str = str(crit)
                if "listing_id" in c_str and hasattr(crit, "right") and hasattr(crit.right, "value"):
                    offers = [o for o in offers if str(o.listing_id) == str(crit.right.value)]
                if "buyer_id" in c_str and hasattr(crit, "right") and hasattr(crit.right, "value"):
                    offers = [o for o in offers if str(o.buyer_id) == str(crit.right.value)]
            offers.sort(key=lambda o: o.created_at, reverse=True)
            return offers

        # 3. MarketPriceRecord query
        if "marketpricerecord" in entity_name or "pricerecord" in entity_name:
            records = list(self.session.price_records)
            for crit in self._filters:
                c_str = str(crit)
                if "market_id" in c_str and hasattr(crit, "right") and hasattr(crit.right, "value"):
                    records = [r for r in records if r.market_id == crit.right.value]
                if "crop_id" in c_str and hasattr(crit, "right") and hasattr(crit.right, "value"):
                    records = [r for r in records if r.crop_id == crit.right.value]
                if ">=" in c_str and "arrival_date" in c_str and hasattr(crit, "right") and hasattr(crit.right, "value"):
                    records = [r for r in records if r.arrival_date >= crit.right.value]
                if "<=" in c_str and "arrival_date" in c_str and hasattr(crit, "right") and hasattr(crit.right, "value"):
                    records = [r for r in records if r.arrival_date <= crit.right.value]
            records.sort(key=lambda r: r.arrival_date)
            if self._order_by and any("desc" in str(o).lower() for o in self._order_by):
                records.reverse()
            return records

        # 4. FarmerMarketFollow query
        if "follow" in entity_name:
            follows = list(self.session.follows)
            for crit in self._filters:
                c_str = str(crit)
                if "farmer_id" in c_str and hasattr(crit, "right") and hasattr(crit.right, "value"):
                    follows = [f for f in follows if f.farmer_id == crit.right.value]
                if "market_id" in c_str and hasattr(crit, "right") and hasattr(crit.right, "value"):
                    follows = [f for f in follows if f.market_id == crit.right.value]
            if len(self.entities) == 1 and not isinstance(self.entities[0], type):
                return [(f.market_id,) for f in follows]
            return follows

        # 5. MarketCropMapping query
        if "mapping" in entity_name:
            mappings = list(self.session.mappings)
            for crit in self._filters:
                c_str = str(crit)
                if "is_active" in c_str:
                    mappings = [m for m in mappings if m.is_active]
            return mappings

        # 6. MarketDataSource query
        if "source" in entity_name:
            sources = list(self.session.sources.values())
            for crit in self._filters:
                c_str = str(crit)
                if "code" in c_str and hasattr(crit, "right") and hasattr(crit.right, "value"):
                    sources = [s for s in sources if s.code == crit.right.value]
            return sources

        # 6b. MarketplaceTransaction query
        if "transaction" in entity_name:
            txs = list(self.session.transactions.values())
            for crit in self._filters:
                c_str = str(crit).lower()
                val = getattr(getattr(crit, "right", None), "value", None)
                if "idempotency_key" in c_str and val is not None:
                    txs = [t for t in txs if t.idempotency_key == val]
                if "gateway_order_id" in c_str and val is not None:
                    txs = [t for t in txs if t.gateway_order_id == val]
                if "buyer_id" in c_str and val is not None:
                    txs = [t for t in txs if str(t.buyer_id) == str(val)]
                if "farmer_id" in c_str and val is not None:
                    txs = [t for t in txs if str(t.farmer_id) == str(val)]
            return txs

        # 7. Market query
        if "market." in entity_name or entity_name.endswith(".market'>") or "models.market" in entity_name:
            mandis = list(self.session.markets.values())
            if self._join_target is not None:
                # Joined with FarmerMarketFollow
                for crit in self._filters:
                    c_str = str(crit)
                    if "farmer_id" in c_str and hasattr(crit, "right") and hasattr(crit.right, "value"):
                        f_id = crit.right.value
                        followed_ids = {f.market_id for f in self.session.follows if f.farmer_id == f_id}
                        mandis = [m for m in mandis if m.id in followed_ids]
            else:
                for crit in self._filters:
                    c_str = str(crit)
                    if "code" in c_str and hasattr(crit, "right") and hasattr(crit.right, "value"):
                        mandis = [m for m in mandis if m.code == crit.right.value]
                    if "is_active" in c_str:
                        mandis = [m for m in mandis if m.is_active]
            return mandis

        # 8. Crop query
        if "crop" in entity_name:
            crops = list(self.session.crops.values())
            for crit in self._filters:
                c_str = str(crit)
                if "code" in c_str and hasattr(crit, "right") and hasattr(crit.right, "value"):
                    crops = [c for c in crops if c.code == crit.right.value]
                if "is_active" in c_str:
                    crops = [c for c in crops if c.is_active]
            return crops

        # 9. UserRole query (for auth)
        if "role" in entity_name:
            results = []
            for ur in self.session.user_roles:
                match = True
                for crit in self._filters:
                    c_str = str(crit)
                    if "user_id" in c_str and hasattr(crit, "right") and hasattr(crit.right, "value"):
                        if ur.user_id != crit.right.value:
                            match = False
                    if "status" in c_str and hasattr(crit, "right") and hasattr(crit.right, "value"):
                        if ur.status != crit.right.value:
                            match = False
                if match:
                    if len(self.entities) == 1 and not isinstance(self.entities[0], type):
                        results.append((ur.role_code,))
                    else:
                        results.append(ur)
            return results

        return []


@pytest.fixture
def market_setup():
    """Setup test fixture with in-memory database session."""
    session = MockMarketDBSession()
    app.dependency_overrides[get_db] = lambda: session

    # 1. Populate the 7 canonical crops
    crops_def = [
        ("c0000000-0000-4000-8000-000000000001", "arecanut", "Arecanut", "ಅಡಿಕೆ"),
        ("c0000000-0000-4000-8000-000000000002", "paddy", "Paddy", "ಭತ್ತ"),
        ("c0000000-0000-4000-8000-000000000003", "black_pepper", "Black Pepper", "ಕಾಳುಮೆಣಸು"),
        ("c0000000-0000-4000-8000-000000000004", "cardamom", "Cardamom", "ಏಲಕ್ಕಿ"),
        ("c0000000-0000-4000-8000-000000000005", "coconut", "Coconut", "ತೆಂಗಿನಕಾಯಿ"),
        ("c0000000-0000-4000-8000-000000000006", "turmeric", "Turmeric", "ಅರಿಶಿನ"),
        ("c0000000-0000-4000-8000-000000000007", "ginger", "Ginger", "ಶುಂಠಿ"),
    ]
    crops = {}
    for cid_str, code, name_en, name_kn in crops_def:
        c = Crop(id=uuid.UUID(cid_str), code=code, name_en=name_en, name_kn=name_kn, is_active=True)
        session.add(c)
        crops[code] = c

    # 2. Add OGD Data Source (Marked as DEMO_SEEDED for Hackathon)
    source = MarketDataSource(
        id=uuid.uuid4(),
        code="OGD_INDIA",
        name="Demo Benchmark Mandi Rates (Hackathon Demo Seed)",
        source_type="DEMO_SEEDED",
        base_url="https://api.data.gov.in/resource/9ef84268-d588-465a-a308-a864a43d0070",
        sync_status="SEEDED_DEMO",
        is_demo=True,
        data_mode="DEMO_SEEDED",
        is_active=True,
    )
    session.add(source)

    # 3. Add Mandis (Puttur, Mangalore, Sirsi, Ujire)
    mandi_puttur = Market(
        id=uuid.uuid4(),
        code="KA_DK_PUTTUR",
        name="Puttur APMC Yard",
        state="Karnataka",
        district="Dakshina Kannada",
        taluk="Puttur",
        latitude=12.7663,
        longitude=75.2033,
        is_active=True,
    )
    mandi_mangalore = Market(
        id=uuid.uuid4(),
        code="KA_DK_MANGALORE",
        name="Mangalore APMC Mandi",
        state="Karnataka",
        district="Dakshina Kannada",
        taluk="Mangaluru",
        latitude=12.8703,
        longitude=74.8806,
        is_active=True,
    )
    mandi_ujire = Market(
        id=uuid.uuid4(),
        code="KA_DK_UJIRE",
        name="Ujire Market Yard",
        state="Karnataka",
        district="Dakshina Kannada",
        taluk="Belthangady",
        latitude=12.9856,
        longitude=75.3283,
        is_active=True,
    )
    session.add(mandi_puttur)
    session.add(mandi_mangalore)
    session.add(mandi_ujire)

    # 4. Add Commodity Mappings
    for comm, var in [("Arecanut", "Chali"), ("Arecanut", "Bette"), ("Paddy(Dhan)(Common)", "Common")]:
        mapping = MarketCropMapping(
            id=uuid.uuid4(),
            crop_id=crops["arecanut"].id if "Areca" in comm else crops["paddy"].id,
            canonical_crop_code="arecanut" if "Areca" in comm else "paddy",
            raw_commodity_name=comm,
            variety=var,
            is_active=True,
        )
        session.add(mapping)

    # 5. Add 15-day price records for Arecanut in Puttur (50,000 -> 53,000 UP trend)
    anchor = date(2026, 9, 25)
    for day_i in range(15):
        dt = anchor - timedelta(days=(14 - day_i))
        modal = Decimal(str(50000 + (day_i * 200)))
        rec = MarketPriceRecord(
            id=uuid.uuid4(),
            market_id=mandi_puttur.id,
            crop_id=crops["arecanut"].id,
            source_id=source.id,
            arrival_date=dt,
            commodity_raw="Arecanut",
            variety="Chali",
            grade="FAQ",
            min_price=modal - Decimal("3000"),
            modal_price=modal,
            max_price=modal + Decimal("3000"),
            arrival_quantity=Decimal("150.0"),
            unit="Quintal",
            is_seeded=True,
            data_mode="DEMO_SEEDED",
        )
        session.add(rec)

    # 6. Create Users and Roles
    farmer_id = uuid.uuid4()
    farmer_profile = UserProfile(id=farmer_id, full_name="Subrahmanya Bhat", phone="9480112233")
    farmer_role = UserRole(user_id=farmer_id, role_code="FARMER", status="ACTIVE")
    session.add(farmer_profile)
    session.add(farmer_role)

    buyer_id = uuid.uuid4()
    buyer_profile = UserProfile(id=buyer_id, full_name="Coastal Traders Mangalore", phone="9480445566")
    buyer_role = UserRole(user_id=buyer_id, role_code="BUYER", status="ACTIVE")
    session.add(buyer_profile)
    session.add(buyer_role)

    admin_id = uuid.uuid4()
    admin_profile = UserProfile(id=admin_id, full_name="System Admin", phone="9480778899")
    admin_role = UserRole(user_id=admin_id, role_code="ADMIN", status="ACTIVE")
    session.add(admin_profile)
    session.add(admin_role)

    yield {
        "crops": crops,
        "arecanut": crops["arecanut"],
        "paddy": crops["paddy"],
        "mandi_puttur": mandi_puttur,
        "mandi_mangalore": mandi_mangalore,
        "mandi_ujire": mandi_ujire,
        "farmer_id": farmer_id,
        "buyer_id": buyer_id,
        "admin_id": admin_id,
        "session": session,
    }

    app.dependency_overrides.pop(get_db, None)


# ==============================================================================
# 1. Public Market Price Discovery Tests
# ==============================================================================

def test_list_supported_market_crops(market_setup):
    """Verify market crops endpoint returns the 7 canonical crops."""
    response = client.get("/api/v1/market/crops")
    assert response.status_code == status.HTTP_200_OK
    crops = response.json()
    assert len(crops) >= 7
    codes = {c["code"] for c in crops}
    expected_crops = {"arecanut", "paddy", "coconut", "black_pepper", "cardamom", "turmeric", "ginger"}
    assert expected_crops.issubset(codes)


def test_list_market_data_sources(market_setup):
    """Verify provenance data sources are exposed and demo sources clearly marked."""
    response = client.get("/api/v1/market/sources")
    assert response.status_code == status.HTTP_200_OK
    sources = response.json()
    assert len(sources) >= 1
    codes = [s["code"] for s in sources]
    assert "OGD_INDIA" in codes
    ogd_src = next(s for s in sources if s["code"] == "OGD_INDIA")
    assert ogd_src["source_type"] == "DEMO_SEEDED"
    assert ogd_src["sync_status"] == "SEEDED_DEMO"
    assert ogd_src["is_demo"] is True


def test_discover_nearby_mandis(market_setup):
    """Discover mandis near Ujire (lat: 12.9856, lon: 75.3283) for Arecanut."""
    arecanut = market_setup["arecanut"]
    response = client.get(
        f"/api/v1/market/mandis/nearby?crop_id={arecanut.id}&latitude=12.9856&longitude=75.3283&radius_km=100&sort=distance"
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["crop"] == "Arecanut"
    assert data["count"] >= 1
    markets = data["markets"]
    assert len(markets) >= 1

    first_mandi = markets[0]
    assert "distance_km" in first_mandi
    assert first_mandi["distance_km"] >= 0
    assert first_mandi["trend"] in ("UP", "DOWN", "STABLE")
    if first_mandi["latest_price"]:
        assert first_mandi["latest_price"]["modal"] > 0
        assert first_mandi["latest_price"]["min"] <= first_mandi["latest_price"]["modal"] <= first_mandi["latest_price"]["max"]
        assert first_mandi["latest_price"]["is_seeded"] is True
        assert first_mandi["latest_price"]["data_mode"] == "DEMO_SEEDED"


def test_mandi_detail_and_15_day_intelligence(market_setup):
    """Verify 15-day price intelligence facts computed mathematically (No LLM)."""
    mandi = market_setup["mandi_puttur"]
    arecanut = market_setup["arecanut"]

    response = client.get(f"/api/v1/market/mandis/{mandi.id}?crop_id={arecanut.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()

    assert data["market"]["code"] == "KA_DK_PUTTUR"
    intel = data["intelligence"]
    assert intel is not None
    assert float(intel["current"]) > 0
    assert float(intel["highest_15_days"]) >= float(intel["current"])
    assert float(intel["lowest_15_days"]) <= float(intel["current"])
    assert intel["trend"] in ("UP", "DOWN", "STABLE")
    assert isinstance(intel["change_percent"], float)
    assert len(intel["history"]) >= 10
    assert intel["is_seeded"] is True
    assert intel["data_mode"] == "DEMO_SEEDED"
    assert "Demo" in intel["source_name"]


def test_mandi_price_history_endpoint(market_setup):
    """Verify price history endpoint returns daily timeline with demo provenance."""
    mandi = market_setup["mandi_puttur"]
    arecanut = market_setup["arecanut"]

    response = client.get(f"/api/v1/market/mandis/{mandi.id}/prices/history?crop_id={arecanut.id}")
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert "history" in data
    assert len(data["history"]) >= 10
    assert data["history"][0]["is_seeded"] is True
    assert data["history"][0]["data_mode"] == "DEMO_SEEDED"


# ==============================================================================
# 2. Farmer Mandi Following Tests
# ==============================================================================

def test_farmer_follow_unfollow_mandi(market_setup):
    """Farmer follows and unfollows an APMC Mandi."""
    farmer_id = market_setup["farmer_id"]
    mandi = market_setup["mandi_puttur"]
    headers = auth_header(farmer_id)

    # 1. Follow
    follow_res = client.post(f"/api/v1/market/mandis/{mandi.id}/follow", headers=headers)
    assert follow_res.status_code == status.HTTP_200_OK

    # 2. Get Followed
    get_res = client.get("/api/v1/market/mandis/followed", headers=headers)
    assert get_res.status_code == status.HTTP_200_OK
    followed = get_res.json()
    assert any(m["id"] == str(mandi.id) for m in followed)

    # 3. Unfollow
    unfollow_res = client.delete(f"/api/v1/market/mandis/{mandi.id}/follow", headers=headers)
    assert unfollow_res.status_code == status.HTTP_200_OK


def test_buyer_cannot_follow_mandi(market_setup):
    """User with BUYER role cannot call farmer follow endpoint (403)."""
    buyer_id = market_setup["buyer_id"]
    mandi = market_setup["mandi_puttur"]
    headers = auth_header(buyer_id)

    res = client.post(f"/api/v1/market/mandis/{mandi.id}/follow", headers=headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN


# ==============================================================================
# 3. Produce Listing & Reference Mandi Pricing Tests
# ==============================================================================

def test_farmer_create_produce_listing(market_setup):
    """Farmer lists harvest produce with expected price; verified against nearest mandi."""
    farmer_id = market_setup["farmer_id"]
    arecanut = market_setup["arecanut"]
    headers = auth_header(farmer_id)

    payload = {
        "crop_id": str(arecanut.id),
        "quantity": 25.0,
        "unit": "quintal",
        "quality_grade": "A",
        "expected_price": 54000.0,
        "location": "Ujire, Belthangady",
    }
    response = client.post("/api/v1/market/listings", json=payload, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    listing = response.json()
    assert listing["farmer_id"] == str(farmer_id)
    assert float(listing["expected_price"]) == 54000.0
    assert listing["status"] == "LISTED"

    listing_id = listing["id"]

    # Retrieve listing detail: MUST include Reference Mandi Price!
    detail_res = client.get(f"/api/v1/market/listings/{listing_id}")
    assert detail_res.status_code == status.HTTP_200_OK
    detail = detail_res.json()
    assert detail["crop_name"] == "Arecanut"
    assert float(detail["listing"]["expected_price"]) == 54000.0

    # Key Architectural Principle: Reference Mandi price is present but distinct from asking price
    ref_mandi = detail["reference_mandi"]
    assert ref_mandi is not None
    assert "mandi_name" in ref_mandi
    assert "modal_price" in ref_mandi
    assert "min_price" in ref_mandi
    assert "max_price" in ref_mandi


def test_cross_farmer_cannot_view_other_farmer_private_listings(market_setup):
    """Farmer A cannot query /farmers/{farmer_b_id}/listings (IDOR 403)."""
    farmer_a_id = market_setup["farmer_id"]
    farmer_b_id = uuid.uuid4()
    headers = auth_header(farmer_a_id)

    res = client.get(f"/api/v1/market/farmers/{farmer_b_id}/listings", headers=headers)
    assert res.status_code == status.HTTP_403_FORBIDDEN


# ==============================================================================
# 4. Buyer Offer & Negotiation Workflow Tests
# ==============================================================================

def test_buyer_offer_submission_and_farmer_acceptance(market_setup):
    """Complete Negotiation Flow:
    1. Farmer creates produce listing (Expected: ₹54,000)
    2. Buyer searches produce listings (views Mandi Reference + Farmer Expected)
    3. Buyer sends Offer (Offered: ₹53,000)
    4. Farmer reviews offer with complete context
    5. Farmer accepts offer
    """
    farmer_id = market_setup["farmer_id"]
    buyer_id = market_setup["buyer_id"]
    arecanut = market_setup["arecanut"]

    # 1. Farmer lists produce
    farmer_headers = auth_header(farmer_id)
    listing_payload = {
        "crop_id": str(arecanut.id),
        "quantity": 30.0,
        "unit": "quintal",
        "quality_grade": "Premium",
        "expected_price": 54000.0,
        "location": "Puttur",
    }
    listing_res = client.post("/api/v1/market/listings", json=listing_payload, headers=farmer_headers)
    assert listing_res.status_code == status.HTTP_201_CREATED
    listing_id = listing_res.json()["id"]

    # 2. Buyer searches listings
    search_res = client.get(f"/api/v1/market/listings?crop_id={arecanut.id}")
    assert search_res.status_code == status.HTTP_200_OK
    listings_found = search_res.json()
    assert any(l["listing"]["id"] == listing_id for l in listings_found)

    # 3. Buyer submits offer
    buyer_headers = auth_header(buyer_id)
    offer_payload = {
        "offered_price": 53000.0,
        "quantity": 30.0,
        "message": "Can pick up directly from your farm yard on Monday.",
    }
    offer_res = client.post(f"/api/v1/market/listings/{listing_id}/offers", json=offer_payload, headers=buyer_headers)
    assert offer_res.status_code == status.HTTP_201_CREATED
    offer = offer_res.json()
    assert float(offer["offered_price"]) == 53000.0
    assert offer["status"] == "PENDING"
    offer_id = offer["id"]

    # 4. Farmer views incoming offers
    farmer_offers_res = client.get(f"/api/v1/market/listings/{listing_id}/offers", headers=farmer_headers)
    assert farmer_offers_res.status_code == status.HTTP_200_OK
    offers_list = farmer_offers_res.json()
    assert len(offers_list) >= 1
    first_offer_ctx = offers_list[0]
    assert float(first_offer_ctx["farmer_expected_price"]) == 54000.0
    assert float(first_offer_ctx["offer"]["offered_price"]) == 53000.0

    # 5. Farmer accepts offer
    accept_res = client.post(
        f"/api/v1/market/offers/{offer_id}/respond",
        json={"action": "ACCEPT", "notes": "Agreed. See you Monday 10 AM."},
        headers=farmer_headers,
    )
    assert accept_res.status_code == status.HTTP_200_OK
    assert accept_res.json()["new_status"] == "ACCEPTED"


def test_farmer_cannot_bid_on_own_produce(market_setup):
    """Farmer attempting to submit offer on their own listing is rejected (400)."""
    farmer_id = market_setup["farmer_id"]
    arecanut = market_setup["arecanut"]
    headers = auth_header(farmer_id)

    # Create listing
    listing_res = client.post(
        "/api/v1/market/listings",
        json={
            "crop_id": str(arecanut.id),
            "quantity": 10.0,
            "unit": "quintal",
            "quality_grade": "A",
            "expected_price": 50000.0,
            "location": "Sullia",
        },
        headers=headers,
    )
    listing_id = listing_res.json()["id"]

    # Self-offer rejected with 403 (insufficient role)
    offer_res = client.post(
        f"/api/v1/market/listings/{listing_id}/offers",
        json={"offered_price": 49000.0, "quantity": 10.0},
        headers=headers,
    )
    assert offer_res.status_code in (status.HTTP_403_FORBIDDEN, status.HTTP_400_BAD_REQUEST)


# ==============================================================================
# 5. Admin Market Sync Tests
# ==============================================================================

def test_admin_can_trigger_sync(market_setup):
    """Admin role can trigger market synchronization."""
    admin_id = market_setup["admin_id"]
    headers = auth_header(admin_id)

    response = client.post(
        "/api/v1/market/sync",
        json={"source_code": "OGD_INDIA", "state": "Karnataka"},
        headers=headers,
    )
    assert response.status_code == status.HTTP_200_OK
    data = response.json()
    assert data["source_code"] == "OGD_INDIA"
    assert "status" in data


def test_non_admin_cannot_trigger_sync(market_setup):
    """Non-admin user triggering sync is rejected with 403."""
    farmer_id = market_setup["farmer_id"]
    headers = auth_header(farmer_id)

    response = client.post("/api/v1/market/sync", json={}, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN


# ==============================================================================
# 6. Privacy & Payment Tests
# ==============================================================================

def test_contact_privacy_hidden_before_accepted_and_revealed_after(market_setup):
    """Phone number must be hidden before offer is accepted, and revealed only after acceptance."""
    farmer_id = market_setup["farmer_id"]
    buyer_id = market_setup["buyer_id"]
    arecanut = market_setup["crops"]["arecanut"]
    farmer_headers = auth_header(farmer_id)
    buyer_headers = auth_header(buyer_id)

    # 1. Farmer creates listing
    listing_res = client.post(
        "/api/v1/market/listings",
        json={
            "crop_id": str(arecanut.id),
            "quantity": 10.0,
            "unit": "quintal",
            "quality_grade": "A",
            "expected_price": 52000.0,
            "location": "Puttur",
        },
        headers=farmer_headers,
    )
    assert listing_res.status_code == status.HTTP_201_CREATED
    listing_id = listing_res.json()["id"]

    # 2. Public / buyer listing detail does NOT expose phone
    detail_res = client.get(f"/api/v1/market/listings/{listing_id}")
    assert detail_res.status_code == status.HTTP_200_OK
    assert "phone" not in detail_res.json()
    assert "farmer_phone" not in detail_res.json()

    # 3. Buyer submits offer
    offer_res = client.post(
        f"/api/v1/market/listings/{listing_id}/offers",
        json={"offered_price": 51000.0, "quantity": 10.0, "message": "Ready to buy immediately"},
        headers=buyer_headers,
    )
    assert offer_res.status_code == status.HTTP_201_CREATED
    offer_id = offer_res.json()["id"]

    # 4. While PENDING, farmer checks offers -> contact_phone MUST be None
    farmer_offers = client.get(f"/api/v1/market/listings/{listing_id}/offers", headers=farmer_headers).json()
    assert len(farmer_offers) >= 1
    pending_offer = next(o for o in farmer_offers if o["offer"]["id"] == offer_id)
    assert pending_offer["contact_phone"] is None

    # 5. Farmer ACCEPTS offer
    accept_res = client.post(
        f"/api/v1/market/offers/{offer_id}/respond",
        json={"action": "ACCEPT", "notes": "Price agreed, deal confirmed"},
        headers=farmer_headers,
    )
    assert accept_res.status_code == status.HTTP_200_OK

    # 6. Now that offer is ACCEPTED:
    # Farmer viewing offers sees buyer's authorized phone number
    updated_farmer_offers = client.get(f"/api/v1/market/listings/{listing_id}/offers", headers=farmer_headers).json()
    accepted_farmer_view = next(o for o in updated_farmer_offers if o["offer"]["id"] == offer_id)
    assert accepted_farmer_view["contact_phone"] is not None
    assert accepted_farmer_view["contact_role"] == "BUYER"

    # Buyer viewing their submitted offers sees farmer's authorized phone number
    buyer_offers = client.get(f"/api/v1/market/buyers/{buyer_id}/offers", headers=buyer_headers).json()
    accepted_buyer_view = next(o for o in buyer_offers if o["offer"]["id"] == offer_id)
    assert accepted_buyer_view["contact_phone"] is not None
    assert accepted_buyer_view["contact_role"] == "FARMER"


def test_payment_order_creation_requires_accepted_offer(market_setup):
    """Payment order creation requires buyer role and an ACCEPTED offer."""
    farmer_id = market_setup["farmer_id"]
    buyer_id = market_setup["buyer_id"]
    arecanut = market_setup["crops"]["arecanut"]
    farmer_headers = auth_header(farmer_id)
    buyer_headers = auth_header(buyer_id)

    # Farmer creates listing
    listing_res = client.post(
        "/api/v1/market/listings",
        json={
            "crop_id": str(arecanut.id),
            "quantity": 5.0,
            "unit": "quintal",
            "quality_grade": "A",
            "expected_price": 50000.0,
            "location": "Shimoga",
        },
        headers=farmer_headers,
    )
    listing_id = listing_res.json()["id"]

    # Buyer submits offer
    offer_res = client.post(
        f"/api/v1/market/listings/{listing_id}/offers",
        json={"offered_price": 49500.0, "quantity": 5.0},
        headers=buyer_headers,
    )
    offer_id = offer_res.json()["id"]

    # Attempt to create payment while PENDING -> Must be rejected (400 Bad Request)
    pay_res = client.post(
        "/api/v1/market/payments/create-order",
        json={"offer_id": offer_id, "idempotency_key": "test-key-001"},
        headers=buyer_headers,
    )
    assert pay_res.status_code == status.HTTP_400_BAD_REQUEST

    # Farmer accepts offer
    client.post(
        f"/api/v1/market/offers/{offer_id}/respond",
        json={"action": "ACCEPT"},
        headers=farmer_headers,
    )

    # Buyer creates payment order on ACCEPTED offer -> Succeeds (201 Created)
    pay_res_2 = client.post(
        "/api/v1/market/payments/create-order",
        json={"offer_id": offer_id, "idempotency_key": "test-key-001"},
        headers=buyer_headers,
    )
    assert pay_res_2.status_code == status.HTTP_201_CREATED
    data = pay_res_2.json()
    assert "transaction_id" in data
    assert data["amount"] == "247500.00"
    assert data["payment_status"] == "PAYMENT_PENDING"


def test_payu_provider_selection_and_inactive_razorpay():
    """Verify PayU is active by default and Razorpay remains available but inactive."""
    from app.market.services.payment_provider import (
        PayUPaymentProvider,
        RazorpayPaymentProvider,
        get_payment_provider,
    )

    # 1. Default provider should be PayU
    provider = get_payment_provider()
    assert isinstance(provider, PayUPaymentProvider)
    assert provider.provider_name == "payu"

    # 2. Razorpay provider remains available and instantiable
    rzp = RazorpayPaymentProvider(key_id="rzp_test_123", key_secret="rzp_secret_456")
    assert rzp.provider_name == "razorpay"
    assert rzp.is_configured() is True


def test_payu_hash_generation_and_verification():
    """Verify PayU SHA-512 payment request hash and reverse hash verification."""
    from app.market.services.payment_provider import PayUPaymentProvider

    provider = PayUPaymentProvider(
        merchant_key="test_key_123",
        merchant_salt="test_salt_456",
        environment="test",
    )
    assert provider.is_configured() is True
    assert "test.payu.in" in provider.action_url

    # Generate request hash
    txnid = "tx_sample_001"
    amount = Decimal("1500.00")
    productinfo = "Arecanut Produce"
    firstname = "Ramesh"
    email = "ramesh@krushipragya.in"

    request_hash = provider.generate_hash(
        txnid=txnid,
        amount=amount,
        productinfo=productinfo,
        firstname=firstname,
        email=email,
        udf1="offer_1",
        udf2="listing_1",
    )
    assert isinstance(request_hash, str)
    assert len(request_hash) == 128  # sha512 hex length

    valid_resp_hash = provider.generate_response_hash(
        txnid=txnid,
        amount=amount,
        productinfo=productinfo,
        firstname=firstname,
        email=email,
        status="success",
        udf1="offer_1",
    )

    valid_payload = {
        "status": "success",
        "txnid": txnid,
        "amount": "1500.00",
        "productinfo": productinfo,
        "firstname": firstname,
        "email": email,
        "udf1": "offer_1",
        "hash": valid_resp_hash,
    }
    assert provider.verify_payment_hash(valid_payload) is True

    # Tampered / invalid hash must be rejected
    invalid_payload = dict(valid_payload, hash="tampered_hash_value_123")
    assert provider.verify_payment_hash(invalid_payload) is False


def test_payment_order_creation_payu_unconfigured_and_configured(market_setup, monkeypatch):
    """Test order creation handles unconfigured and configured PayU credentials safely."""
    farmer_id = market_setup["farmer_id"]
    buyer_id = market_setup["buyer_id"]
    arecanut = market_setup["crops"]["arecanut"]
    farmer_headers = auth_header(farmer_id)
    buyer_headers = auth_header(buyer_id)

    # 1. Create listing and accept offer
    listing_res = client.post(
        "/api/v1/market/listings",
        json={
            "crop_id": str(arecanut.id),
            "quantity": 2.0,
            "unit": "quintal",
            "quality_grade": "A",
            "expected_price": 52000.0,
            "location": "Ujire",
        },
        headers=farmer_headers,
    )
    listing_id = listing_res.json()["id"]

    offer_res = client.post(
        f"/api/v1/market/listings/{listing_id}/offers",
        json={"offered_price": 51000.0, "quantity": 2.0},
        headers=buyer_headers,
    )
    offer_id = offer_res.json()["id"]

    client.post(
        f"/api/v1/market/offers/{offer_id}/respond",
        json={"action": "ACCEPT"},
        headers=farmer_headers,
    )

    # Case A: PayU Unconfigured
    from app.market.services.payment_provider import PayUPaymentProvider
    unconfigured_provider = PayUPaymentProvider(merchant_key=None, merchant_salt=None)
    from app.market.routers.market_payment import get_payment_service
    from app.market.services.market_payment_service import MarketPaymentService
    app.dependency_overrides[get_payment_service] = lambda: MarketPaymentService(unconfigured_provider)

    res_unconf = client.post(
        "/api/v1/market/payments/create-order",
        json={"offer_id": offer_id, "idempotency_key": "unconf-key-1"},
        headers=buyer_headers,
    )
    assert res_unconf.status_code == status.HTTP_201_CREATED
    data_unconf = res_unconf.json()
    assert data_unconf["gateway_configured"] is False
    assert data_unconf["checkout_data"] is None
    assert "Online payment is currently unavailable" in data_unconf["message_en"]

    # Case B: PayU Configured with test credentials
    configured_provider = PayUPaymentProvider(
        merchant_key="test_mkey_abc",
        merchant_salt="test_salt_xyz",
        environment="test",
    )
    app.dependency_overrides[get_payment_service] = lambda: MarketPaymentService(configured_provider)

    res_conf = client.post(
        "/api/v1/market/payments/create-order",
        json={"offer_id": offer_id, "idempotency_key": "conf-key-1"},
        headers=buyer_headers,
    )
    assert res_conf.status_code == status.HTTP_201_CREATED
    data_conf = res_conf.json()
    assert data_conf["gateway_configured"] is True
    assert data_conf["provider"] == "payu"
    assert data_conf["checkout_data"] is not None
    assert "test.payu.in" in data_conf["checkout_data"]["action_url"]
    assert data_conf["checkout_data"]["params"]["key"] == "test_mkey_abc"
    assert "hash" in data_conf["checkout_data"]["params"]
    # Merchant salt must NEVER appear in client payload
    assert "test_salt_xyz" not in str(data_conf)

    # Clean up override
    app.dependency_overrides.pop(get_payment_service, None)


def test_payment_order_invalid_offer_rejected(market_setup):
    """Attempting payment order on non-existent or rejected offers must fail."""
    buyer_id = market_setup["buyer_id"]
    farmer_id = market_setup["farmer_id"]
    buyer_headers = auth_header(buyer_id)
    farmer_headers = auth_header(farmer_id)
    arecanut = market_setup["crops"]["arecanut"]

    # 1. Nonexistent offer
    random_id = str(uuid.uuid4())
    res_fake = client.post(
        "/api/v1/market/payments/create-order",
        json={"offer_id": random_id},
        headers=buyer_headers,
    )
    assert res_fake.status_code == status.HTTP_400_BAD_REQUEST

    # 2. Offer rejected by farmer
    listing_res = client.post(
        "/api/v1/market/listings",
        json={
            "crop_id": str(arecanut.id),
            "quantity": 1.0,
            "unit": "quintal",
            "quality_grade": "A",
            "expected_price": 50000.0,
            "location": "Puttur",
        },
        headers=farmer_headers,
    )
    listing_id = listing_res.json()["id"]

    offer_res = client.post(
        f"/api/v1/market/listings/{listing_id}/offers",
        json={"offered_price": 30000.0, "quantity": 1.0},
        headers=buyer_headers,
    )
    offer_id = offer_res.json()["id"]

    client.post(
        f"/api/v1/market/offers/{offer_id}/respond",
        json={"action": "REJECT"},
        headers=farmer_headers,
    )

    res_rejected = client.post(
        "/api/v1/market/payments/create-order",
        json={"offer_id": offer_id},
        headers=buyer_headers,
    )
    assert res_rejected.status_code == status.HTTP_400_BAD_REQUEST


def test_payment_order_idempotency(market_setup):
    """Submitting identical idempotency_key returns the existing transaction."""
    farmer_id = market_setup["farmer_id"]
    buyer_id = market_setup["buyer_id"]
    arecanut = market_setup["crops"]["arecanut"]
    farmer_headers = auth_header(farmer_id)
    buyer_headers = auth_header(buyer_id)

    listing_res = client.post(
        "/api/v1/market/listings",
        json={
            "crop_id": str(arecanut.id),
            "quantity": 3.0,
            "unit": "quintal",
            "quality_grade": "A",
            "expected_price": 50000.0,
            "location": "Ujire",
        },
        headers=farmer_headers,
    )
    listing_id = listing_res.json()["id"]

    offer_res = client.post(
        f"/api/v1/market/listings/{listing_id}/offers",
        json={"offered_price": 50000.0, "quantity": 3.0},
        headers=buyer_headers,
    )
    offer_id = offer_res.json()["id"]

    client.post(
        f"/api/v1/market/offers/{offer_id}/respond",
        json={"action": "ACCEPT"},
        headers=farmer_headers,
    )

    # First request
    res1 = client.post(
        "/api/v1/market/payments/create-order",
        json={"offer_id": offer_id, "idempotency_key": "unique-idemp-key-100"},
        headers=buyer_headers,
    )
    assert res1.status_code == status.HTTP_201_CREATED
    tx_id_1 = res1.json()["transaction_id"]

    # Second request with same idempotency key
    res2 = client.post(
        "/api/v1/market/payments/create-order",
        json={"offer_id": offer_id, "idempotency_key": "unique-idemp-key-100"},
        headers=buyer_headers,
    )
    assert res2.status_code == status.HTTP_201_CREATED
    tx_id_2 = res2.json()["transaction_id"]
    assert tx_id_1 == tx_id_2


def test_payu_payment_verification_valid_and_invalid(market_setup):
    """Test cryptographic verification of PayU payments and transition to PAID."""
    import hashlib
    farmer_id = market_setup["farmer_id"]
    buyer_id = market_setup["buyer_id"]
    arecanut = market_setup["crops"]["arecanut"]
    farmer_headers = auth_header(farmer_id)
    buyer_headers = auth_header(buyer_id)

    from app.market.services.payment_provider import PayUPaymentProvider
    configured_provider = PayUPaymentProvider(
        merchant_key="test_key_v",
        merchant_salt="test_salt_v",
        environment="test",
    )
    from app.market.routers.market_payment import get_payment_service
    from app.market.services.market_payment_service import MarketPaymentService
    app.dependency_overrides[get_payment_service] = lambda: MarketPaymentService(configured_provider)

    listing_res = client.post(
        "/api/v1/market/listings",
        json={
            "crop_id": str(arecanut.id),
            "quantity": 1.0,
            "unit": "quintal",
            "quality_grade": "A",
            "expected_price": 50000.0,
            "location": "Ujire",
        },
        headers=farmer_headers,
    )
    listing_id = listing_res.json()["id"]

    offer_res = client.post(
        f"/api/v1/market/listings/{listing_id}/offers",
        json={"offered_price": 50000.0, "quantity": 1.0},
        headers=buyer_headers,
    )
    offer_id = offer_res.json()["id"]

    client.post(
        f"/api/v1/market/offers/{offer_id}/respond",
        json={"action": "ACCEPT"},
        headers=farmer_headers,
    )

    pay_res = client.post(
        "/api/v1/market/payments/create-order",
        json={"offer_id": offer_id, "idempotency_key": "v-key-01"},
        headers=buyer_headers,
    )
    tx_data = pay_res.json()
    tx_id = tx_data["transaction_id"]
    txnid = tx_data["gateway_order_id"]

    # 1. Invalid signature submitted -> PAYMENT_FAILED
    inv_res = client.post(
        "/api/v1/market/payments/verify",
        json={
            "transaction_id": tx_id,
            "payu_txnid": txnid,
            "payu_payment_id": "mih_999",
            "payu_status": "success",
            "payu_hash": "bad_hash_signature",
        },
        headers=buyer_headers,
    )
    assert inv_res.status_code == status.HTTP_200_OK
    assert inv_res.json()["payment_status"] == "PAYMENT_FAILED"

    # 2. Valid signature submitted -> PAYMENT_SUCCESS and PAID
    valid_hash = configured_provider.generate_response_hash(
        txnid=txnid,
        amount="50000.00",
        productinfo="Produce Listing",
        firstname="Buyer",
        email="buyer@krushipragya.in",
        status="success",
    )

    valid_res = client.post(
        "/api/v1/market/payments/verify",
        json={
            "transaction_id": tx_id,
            "payu_txnid": txnid,
            "payu_payment_id": "mih_12345",
            "payu_status": "success",
            "payu_hash": valid_hash,
        },
        headers=buyer_headers,
    )
    assert valid_res.status_code == status.HTTP_200_OK
    v_data = valid_res.json()
    assert v_data["payment_status"] == "PAYMENT_SUCCESS"
    assert v_data["order_status"] == "PAID"

    # 3. Already verified payment cannot be transitioned again
    repeat_res = client.post(
        "/api/v1/market/payments/verify",
        json={
            "transaction_id": tx_id,
            "payu_txnid": txnid,
            "payu_payment_id": "mih_12345",
            "payu_status": "success",
            "payu_hash": valid_hash,
        },
        headers=buyer_headers,
    )
    assert repeat_res.status_code == status.HTTP_200_OK
    assert repeat_res.json()["payment_status"] == "PAYMENT_SUCCESS"

    app.dependency_overrides.pop(get_payment_service, None)


def test_payu_webhook_handling_and_duplicate_idempotency(market_setup):
    """Test PayU authoritative webhook processing and idempotency."""
    import hashlib
    farmer_id = market_setup["farmer_id"]
    buyer_id = market_setup["buyer_id"]
    arecanut = market_setup["crops"]["arecanut"]
    farmer_headers = auth_header(farmer_id)
    buyer_headers = auth_header(buyer_id)

    from app.market.services.payment_provider import PayUPaymentProvider
    configured_provider = PayUPaymentProvider(
        merchant_key="test_wh_key",
        merchant_salt="test_wh_salt",
        environment="test",
    )
    from app.market.routers.market_payment import get_payment_service
    from app.market.services.market_payment_service import MarketPaymentService
    app.dependency_overrides[get_payment_service] = lambda: MarketPaymentService(configured_provider)

    listing_res = client.post(
        "/api/v1/market/listings",
        json={
            "crop_id": str(arecanut.id),
            "quantity": 1.0,
            "unit": "quintal",
            "quality_grade": "A",
            "expected_price": 50000.0,
            "location": "Ujire",
        },
        headers=farmer_headers,
    )
    listing_id = listing_res.json()["id"]

    offer_res = client.post(
        f"/api/v1/market/listings/{listing_id}/offers",
        json={"offered_price": 50000.0, "quantity": 1.0},
        headers=buyer_headers,
    )
    offer_id = offer_res.json()["id"]

    client.post(
        f"/api/v1/market/offers/{offer_id}/respond",
        json={"action": "ACCEPT"},
        headers=farmer_headers,
    )

    pay_res = client.post(
        "/api/v1/market/payments/create-order",
        json={"offer_id": offer_id, "idempotency_key": "wh-key-01"},
        headers=buyer_headers,
    )
    txnid = pay_res.json()["gateway_order_id"]

    # 1. Webhook with invalid hash -> rejected (400)
    wh_inv = client.post(
        "/api/v1/market/payments/webhook",
        json={
            "status": "success",
            "txnid": txnid,
            "amount": "50000.00",
            "productinfo": "Produce Listing",
            "firstname": "Buyer",
            "email": "buyer@krushipragya.in",
            "hash": "tampered_hash",
        },
    )
    assert wh_inv.status_code == status.HTTP_400_BAD_REQUEST

    # 2. Webhook with valid hash -> success
    valid_hash = configured_provider.generate_response_hash(
        txnid=txnid,
        amount="50000.00",
        productinfo="Produce Listing",
        firstname="Buyer",
        email="buyer@krushipragya.in",
        status="success",
    )

    wh_val = client.post(
        "/api/v1/market/payments/webhook",
        json={
            "status": "success",
            "txnid": txnid,
            "amount": "50000.00",
            "productinfo": "Produce Listing",
            "firstname": "Buyer",
            "email": "buyer@krushipragya.in",
            "mihpayid": "mih_wh_999",
            "hash": valid_hash,
        },
    )
    assert wh_val.status_code == status.HTTP_200_OK
    assert wh_val.json()["status"] == "success"

    # 3. Duplicate webhook -> idempotently returns already_processed
    wh_dup = client.post(
        "/api/v1/market/payments/webhook",
        json={
            "status": "success",
            "txnid": txnid,
            "amount": "50000.00",
            "productinfo": "Produce Listing",
            "firstname": "Buyer",
            "email": "buyer@krushipragya.in",
            "mihpayid": "mih_wh_999",
            "hash": valid_hash,
        },
    )
    assert wh_dup.status_code == status.HTTP_200_OK
    assert wh_dup.json()["status"] == "already_processed"

    app.dependency_overrides.pop(get_payment_service, None)


def test_transaction_ownership_and_unauthorized_access(market_setup):
    """Enforce that only transaction buyer or seller can retrieve transaction."""
    farmer_id = market_setup["farmer_id"]
    buyer_id = market_setup["buyer_id"]
    arecanut = market_setup["crops"]["arecanut"]
    farmer_headers = auth_header(farmer_id)
    buyer_headers = auth_header(buyer_id)

    listing_res = client.post(
        "/api/v1/market/listings",
        json={
            "crop_id": str(arecanut.id),
            "quantity": 1.0,
            "unit": "quintal",
            "quality_grade": "A",
            "expected_price": 50000.0,
            "location": "Ujire",
        },
        headers=farmer_headers,
    )
    listing_id = listing_res.json()["id"]

    offer_res = client.post(
        f"/api/v1/market/listings/{listing_id}/offers",
        json={"offered_price": 50000.0, "quantity": 1.0},
        headers=buyer_headers,
    )
    offer_id = offer_res.json()["id"]

    client.post(
        f"/api/v1/market/offers/{offer_id}/respond",
        json={"action": "ACCEPT"},
        headers=farmer_headers,
    )

    pay_res = client.post(
        "/api/v1/market/payments/create-order",
        json={"offer_id": offer_id, "idempotency_key": "own-key-01"},
        headers=buyer_headers,
    )
    tx_id = pay_res.json()["transaction_id"]

    # 1. Buyer can retrieve
    res_b = client.get(f"/api/v1/market/payments/transactions/{tx_id}", headers=buyer_headers)
    assert res_b.status_code == status.HTTP_200_OK

    # 2. Farmer (seller) can retrieve
    res_f = client.get(f"/api/v1/market/payments/transactions/{tx_id}", headers=farmer_headers)
    assert res_f.status_code == status.HTTP_200_OK

    # 3. Third party cannot retrieve (403)
    unauthorized_id = uuid.uuid4()
    session = market_setup["session"]
    unauth_profile = UserProfile(
        id=unauthorized_id,
        phone="9999900000",
        full_name="Unauthorized User",
    )
    unauth_role = UserRole(user_id=unauthorized_id, role_code="BUYER", status="ACTIVE")
    session.add(unauth_profile)
    session.add(unauth_role)
    unauth_headers = auth_header(unauthorized_id)

    res_unauth = client.get(f"/api/v1/market/payments/transactions/{tx_id}", headers=unauth_headers)
    assert res_unauth.status_code == status.HTTP_403_FORBIDDEN


# ==============================================================================
# 9. Regression Tests: Nearby Mandis Sorting & Graceful Null Price Handling
# ==============================================================================

def test_nearby_mandis_ujire_arecanut_sort_regression(market_setup):
    """Regression test: Ujire + Arecanut + 500km with both distance and price sorting.
    Verifies that Decimal sorting does not crash with NameError and returns valid metadata.
    """
    arecanut = market_setup["crops"]["arecanut"]

    # 1. Test sort=distance
    res_dist = client.get(
        f"/api/v1/market/mandis/nearby?crop_id={arecanut.id}&latitude=13.0039&longitude=75.3216&radius_km=500&sort=distance"
    )
    assert res_dist.status_code == status.HTTP_200_OK
    data_dist = res_dist.json()
    assert data_dist["crop"] == "Arecanut"
    assert data_dist["count"] >= 1
    assert data_dist["source_status"] == "DEMO"
    assert data_dist["sync_status"] == "UNAVAILABLE"
    assert len(data_dist["markets"]) >= 1

    # 2. Test sort=price (previously crashed with NameError: name 'Decimal' is not defined)
    res_price = client.get(
        f"/api/v1/market/mandis/nearby?crop_id={arecanut.id}&latitude=13.0039&longitude=75.3216&radius_km=500&sort=price"
    )
    assert res_price.status_code == status.HTTP_200_OK
    data_price = res_price.json()
    assert data_price["count"] >= 1
    markets_price = data_price["markets"]
    assert len(markets_price) >= 1

    # Ensure prices are in descending order where present
    priced = [float(m["latest_price"]["modal"]) for m in markets_price if m["latest_price"] and m["latest_price"]["modal"]]
    if len(priced) >= 2:
        for i in range(len(priced) - 1):
            assert priced[i] >= priced[i + 1]


def test_nearby_mandis_market_without_price_graceful(market_setup):
    """Verify that a market with no price records returns latest_price=null without HTTP 500."""
    session = market_setup["session"]
    arecanut = market_setup["crops"]["arecanut"]

    # Create a fresh market within radius that has zero price records for arecanut
    unpriced_market = Market(
        id=uuid.uuid4(),
        code="KA_DK_BELTHANGADY_NEW",
        name="Belthangady Rural Yard",
        state="Karnataka",
        district="Dakshina Kannada",
        taluk="Belthangady",
        latitude=13.0100,
        longitude=75.3200,
        is_active=True,
    )
    session.add(unpriced_market)
    session.commit()

    # Query with sort=distance
    res_dist = client.get(
        f"/api/v1/market/mandis/nearby?crop_id={arecanut.id}&latitude=13.0039&longitude=75.3216&radius_km=500&sort=distance"
    )
    assert res_dist.status_code == status.HTTP_200_OK
    data_dist = res_dist.json()
    belthangady = next((m for m in data_dist["markets"] if m["name"] == "Belthangady Rural Yard"), None)
    assert belthangady is not None
    assert belthangady["latest_price"] is None
    assert belthangady["trend"] == "STABLE"

    # Query with sort=price (unpriced markets must be sorted gracefully at the end)
    res_price = client.get(
        f"/api/v1/market/mandis/nearby?crop_id={arecanut.id}&latitude=13.0039&longitude=75.3216&radius_km=500&sort=price"
    )
    assert res_price.status_code == status.HTTP_200_OK
    data_price = res_price.json()
    belthangady_price = next((m for m in data_price["markets"] if m["name"] == "Belthangady Rural Yard"), None)
    assert belthangady_price is not None
    assert belthangady_price["latest_price"] is None



