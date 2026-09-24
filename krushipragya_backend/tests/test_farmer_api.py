"""API tests for Farmer Profile endpoints."""
from datetime import datetime, timezone
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient

from app.database.connection import get_db
from app.main import app
from app.models.user_profile import UserProfile
from app.schemas.farmer import FarmerProfileResponse

client = TestClient(app)


class InMemorySession:
    """In-memory transactional session simulator for deterministic API testing."""

    def __init__(self):
        self.store: dict[uuid.UUID, UserProfile] = {}
        self.pending_adds: list[UserProfile] = []
        self.committed = False
        self.rolled_back = False

    def get(self, model, entity_id):
        return self.store.get(entity_id)

    def add(self, obj: UserProfile):
        self.pending_adds.append(obj)

    def commit(self):
        for obj in self.pending_adds:
            if getattr(obj, "created_at", None) is None:
                obj.created_at = datetime.now(timezone.utc)
            if getattr(obj, "updated_at", None) is None:
                obj.updated_at = datetime.now(timezone.utc)
            self.store[obj.id] = obj
        self.pending_adds.clear()
        self.committed = True

    def refresh(self, obj: UserProfile):
        if obj.id in self.store:
            stored = self.store[obj.id]
            obj.created_at = stored.created_at
            obj.updated_at = stored.updated_at

    def rollback(self):
        self.pending_adds.clear()
        self.rolled_back = True


@pytest.fixture(autouse=True)
def override_db():
    """Ensure every test has a clean in-memory database session."""
    session = InMemorySession()
    app.dependency_overrides[get_db] = lambda: session
    yield session
    app.dependency_overrides.pop(get_db, None)


# ==============================================================================
# 1. POST /api/v1/farmers/profile Tests
# ==============================================================================

def test_post_creates_farmer_profile():
    """Test 1: POST /api/v1/farmers/profile creates profile and returns 201."""
    farmer_id = str(uuid.uuid4())
    payload = {
        "id": farmer_id,
        "full_name": "Manjunath Patil",
        "phone": "+919845012345",
        "village_id": "V001",
        "language": "kn",
        "land_holding_acres": "12.50",
    }

    response = client.post("/api/v1/farmers/profile", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["id"] == farmer_id
    assert data["full_name"] == "Manjunath Patil"
    assert data["phone"] == "+919845012345"
    assert data["village_id"] == "V001"
    assert data["language"] == "kn"
    assert data["land_holding_acres"] == "12.50"
    assert "created_at" in data
    assert "updated_at" in data

    # Verify response conforms to FarmerProfileResponse
    validated = FarmerProfileResponse.model_validate(data)
    assert str(validated.id) == farmer_id


def test_post_invalid_language_returns_422():
    """Test 2: POST with invalid language returns 422 Unprocessable Entity."""
    payload = {
        "id": str(uuid.uuid4()),
        "full_name": "Test Farmer",
        "language": "hindi",
    }

    response = client.post("/api/v1/farmers/profile", json=payload)
    assert response.status_code == 422
    assert "language" in str(response.json()).lower()


def test_post_negative_land_holding_returns_422():
    """Test 3: POST with negative land holding returns 422 Unprocessable Entity."""
    payload = {
        "id": str(uuid.uuid4()),
        "full_name": "Test Farmer",
        "land_holding_acres": "-2.50",
    }

    response = client.post("/api/v1/farmers/profile", json=payload)
    assert response.status_code == 422
    assert "land_holding_acres" in str(response.json()).lower()


def test_post_duplicate_farmer_id_returns_409():
    """Test 4: POST with duplicate farmer ID returns 409 Conflict."""
    farmer_id = str(uuid.uuid4())
    payload = {
        "id": farmer_id,
        "full_name": "First Creation",
        "language": "kn",
    }

    # First POST succeeds
    resp1 = client.post("/api/v1/farmers/profile", json=payload)
    assert resp1.status_code == 201

    # Second POST with identical ID fails with 409 Conflict
    resp2 = client.post("/api/v1/farmers/profile", json=payload)
    assert resp2.status_code == 409
    data = resp2.json()
    assert data["detail"] == "Farmer profile already exists"


# ==============================================================================
# 2. GET /api/v1/farmers/profile/{farmer_id} Tests
# ==============================================================================

def test_get_existing_farmer_profile():
    """Test 5: GET /api/v1/farmers/profile/{farmer_id} returns 200 and profile."""
    farmer_id = str(uuid.uuid4())
    payload = {
        "id": farmer_id,
        "full_name": "Siddaramaiah",
        "phone": "9876543210",
        "village_id": "V010",
        "language": "en",
        "land_holding_acres": "5.00",
    }

    # Create profile
    create_resp = client.post("/api/v1/farmers/profile", json=payload)
    assert create_resp.status_code == 201

    # Retrieve profile
    get_resp = client.get(f"/api/v1/farmers/profile/{farmer_id}")
    assert get_resp.status_code == 200
    data = get_resp.json()
    assert data["id"] == farmer_id
    assert data["full_name"] == "Siddaramaiah"
    assert data["language"] == "en"
    assert data["land_holding_acres"] == "5.00"

    # Schema validation
    FarmerProfileResponse.model_validate(data)


def test_get_unknown_farmer_returns_404():
    """Test 6: GET with non-existent farmer UUID returns 404 Not Found."""
    unknown_id = str(uuid.uuid4())
    response = client.get(f"/api/v1/farmers/profile/{unknown_id}")

    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Farmer profile not found"


def test_get_malformed_uuid_returns_422():
    """Test 7: GET with malformed UUID returns 422 Unprocessable Entity."""
    response = client.get("/api/v1/farmers/profile/not-a-valid-uuid-12345")
    assert response.status_code == 422


# ==============================================================================
# 3. PATCH /api/v1/farmers/profile/{farmer_id} Tests
# ==============================================================================

def test_patch_partial_update():
    """Test 8: PATCH updates only specified fields while preserving others."""
    farmer_id = str(uuid.uuid4())
    create_payload = {
        "id": farmer_id,
        "full_name": "Initial Name",
        "phone": "1111111111",
        "village_id": "V001",
        "language": "kn",
        "land_holding_acres": "4.00",
    }
    client.post("/api/v1/farmers/profile", json=create_payload)

    # Patch only phone and language
    patch_payload = {
        "phone": "9999999999",
        "language": "en",
    }
    response = client.patch(f"/api/v1/farmers/profile/{farmer_id}", json=patch_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["phone"] == "9999999999"
    assert data["language"] == "en"
    # Preserved fields
    assert data["full_name"] == "Initial Name"
    assert data["village_id"] == "V001"
    assert data["land_holding_acres"] == "4.00"


def test_patch_explicitly_sets_nullable_field_to_null():
    """Test 9: PATCH explicitly sets nullable field to null while preserving unset fields."""
    farmer_id = str(uuid.uuid4())
    create_payload = {
        "id": farmer_id,
        "full_name": "Farmer With Phone",
        "phone": "9845012345",
        "village_id": "V002",
        "land_holding_acres": "7.50",
    }
    client.post("/api/v1/farmers/profile", json=create_payload)

    # Explicitly clear phone and village_id to null
    patch_payload = {
        "phone": None,
        "village_id": None,
    }
    response = client.patch(f"/api/v1/farmers/profile/{farmer_id}", json=patch_payload)

    assert response.status_code == 200
    data = response.json()
    assert data["phone"] is None
    assert data["village_id"] is None
    assert data["full_name"] == "Farmer With Phone"
    assert data["land_holding_acres"] == "7.50"


def test_patch_unknown_farmer_returns_404():
    """Test 10: PATCH with non-existent farmer UUID returns 404 Not Found."""
    unknown_id = str(uuid.uuid4())
    patch_payload = {"full_name": "Ghost Farmer"}

    response = client.patch(f"/api/v1/farmers/profile/{unknown_id}", json=patch_payload)
    assert response.status_code == 404
    data = response.json()
    assert data["detail"] == "Farmer profile not found"


def test_patch_invalid_language_returns_422():
    """Test 11: PATCH with invalid language returns 422 Unprocessable Entity."""
    farmer_id = str(uuid.uuid4())
    create_payload = {"id": farmer_id, "full_name": "Test Farmer"}
    client.post("/api/v1/farmers/profile", json=create_payload)

    response = client.patch(f"/api/v1/farmers/profile/{farmer_id}", json={"language": "invalid_lang"})
    assert response.status_code == 422


# ==============================================================================
# 4. OpenAPI / Swagger Schema Verification
# ==============================================================================

def test_openapi_contains_farmer_endpoints():
    """Test 12: OpenAPI schema contains all 3 farmer endpoints with correct methods."""
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()

    paths = schema["paths"]
    assert "/api/v1/farmers/profile" in paths
    assert "post" in paths["/api/v1/farmers/profile"]

    assert "/api/v1/farmers/profile/{farmer_id}" in paths
    assert "get" in paths["/api/v1/farmers/profile/{farmer_id}"]
    assert "patch" in paths["/api/v1/farmers/profile/{farmer_id}"]
