"""API tests for Farmer Crop Management and Crop catalog endpoints."""
from datetime import datetime, timezone
from decimal import Decimal
import uuid
import pytest
from fastapi.testclient import TestClient

from app.database.connection import get_db
from app.main import app
from app.models.crop import Crop
from app.models.farmer_crop import FarmerCrop
from app.models.user_profile import UserProfile
from app.schemas.farmer_crop import CropResponse, FarmerCropWithDetailsResponse

client = TestClient(app)


class FakeQuery:
    """Query object simulator for InMemorySession."""

    def __init__(self, items):
        self.items = list(items)

    def options(self, *args, **kwargs):
        return self

    def filter(self, *criteria):
        filtered = []
        for item in self.items:
            matches = True
            for c in criteria:
                col_name = getattr(c.left, "key", getattr(c.left, "name", None))
                target_val = getattr(c.right, "value", True)
                if getattr(item, col_name) != target_val:
                    matches = False
                    break
            if matches:
                filtered.append(item)
        return FakeQuery(filtered)

    def order_by(self, *args):
        def sort_key(item):
            if hasattr(item, "name_en"):
                return str(item.name_en)
            if hasattr(item, "created_at"):
                return item.created_at or datetime.min.replace(tzinfo=timezone.utc)
            return 0

        return FakeQuery(sorted(self.items, key=sort_key))

    def all(self):
        return list(self.items)

    def first(self):
        return self.items[0] if self.items else None


class InMemorySession:
    """In-memory transactional session simulator supporting UserProfile, Crop, and FarmerCrop."""

    def __init__(self):
        self.crops: dict[uuid.UUID, Crop] = {}
        self.farmers: dict[uuid.UUID, UserProfile] = {}
        self.farmer_crops: dict[uuid.UUID, FarmerCrop] = {}
        self.pending_adds: list[object] = []
        self.committed = False
        self.rolled_back = False

    def get(self, model, entity_id):
        if model is Crop:
            return self.crops.get(entity_id)
        if model is UserProfile:
            return self.farmers.get(entity_id)
        if model is FarmerCrop:
            return self.farmer_crops.get(entity_id)
        return None

    def query(self, model):
        if model is Crop:
            items = list(self.crops.values())
        elif model is FarmerCrop:
            items = list(self.farmer_crops.values())
        elif model is UserProfile:
            items = list(self.farmers.values())
        else:
            items = []
        return FakeQuery(items)

    def add(self, obj):
        self.pending_adds.append(obj)

    def commit(self):
        for obj in self.pending_adds:
            if getattr(obj, "created_at", None) is None:
                obj.created_at = datetime.now(timezone.utc)
            if getattr(obj, "updated_at", None) is None:
                obj.updated_at = datetime.now(timezone.utc)

            if isinstance(obj, Crop):
                self.crops[obj.id] = obj
            elif isinstance(obj, UserProfile):
                self.farmers[obj.id] = obj
            elif isinstance(obj, FarmerCrop):
                if getattr(obj, "crop", None) is None and obj.crop_id in self.crops:
                    obj.crop = self.crops[obj.crop_id]
                self.farmer_crops[obj.id] = obj
        self.pending_adds.clear()
        self.committed = True

    def refresh(self, obj):
        if isinstance(obj, FarmerCrop) and getattr(obj, "crop", None) is None:
            if obj.crop_id in self.crops:
                obj.crop = self.crops[obj.crop_id]

    def delete(self, obj):
        if isinstance(obj, FarmerCrop) and obj.id in self.farmer_crops:
            del self.farmer_crops[obj.id]

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


@pytest.fixture
def sample_crop(override_db):
    """Seed an active crop."""
    crop = Crop(
        id=uuid.uuid4(),
        code="arecanut",
        name_en="Arecanut",
        name_kn="ಅಡಿಕೆ",
        is_active=True,
    )
    override_db.add(crop)
    override_db.commit()
    return crop


@pytest.fixture
def inactive_crop(override_db):
    """Seed an inactive crop."""
    crop = Crop(
        id=uuid.uuid4(),
        code="tobacco",
        name_en="Tobacco",
        name_kn="ತಂಬಾಕು",
        is_active=False,
    )
    override_db.add(crop)
    override_db.commit()
    return crop


@pytest.fixture
def sample_farmer(override_db):
    """Seed a registered farmer profile."""
    farmer = UserProfile(
        id=uuid.uuid4(),
        full_name="Basavaraj Patil",
        language="kn",
    )
    override_db.add(farmer)
    override_db.commit()
    return farmer


# ==============================================================================
# 1. GET /api/v1/crops
# ==============================================================================

def test_get_crops_returns_active_catalog(sample_crop, inactive_crop):
    """Test 1: GET /crops returns active crop catalog."""
    response = client.get("/api/v1/crops")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["id"] == str(sample_crop.id)
    assert data[0]["code"] == "arecanut"
    assert data[0]["name_en"] == "Arecanut"
    assert data[0]["is_active"] is True
    # Confirm inactive crop is excluded
    assert not any(c["id"] == str(inactive_crop.id) for c in data)


def test_get_crops_returns_200():
    """Test 2: GET /crops returns 200 even when catalog is empty."""
    response = client.get("/api/v1/crops")
    assert response.status_code == 200
    assert response.json() == []


# ==============================================================================
# 2. POST /api/v1/farmers/{farmer_id}/crops
# ==============================================================================

def test_post_farmer_crop_returns_201(sample_farmer, sample_crop):
    """Test 3: POST farmer crop returns 201."""
    payload = {
        "crop_id": str(sample_crop.id),
        "area_acres": "4.50",
        "is_primary": True,
    }
    response = client.post(f"/api/v1/farmers/{sample_farmer.id}/crops", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["farmer_id"] == str(sample_farmer.id)
    assert data["crop_id"] == str(sample_crop.id)
    assert data["area_acres"] == "4.50"
    assert data["is_primary"] is True
    assert "id" in data


def test_post_farmer_crop_includes_nested_crop_details(sample_farmer, sample_crop):
    """Test 4: POST response includes nested crop details."""
    payload = {
        "crop_id": str(sample_crop.id),
        "area_acres": "3.00",
        "is_primary": False,
    }
    response = client.post(f"/api/v1/farmers/{sample_farmer.id}/crops", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert "crop" in data
    nested_crop = data["crop"]
    assert nested_crop["id"] == str(sample_crop.id)
    assert nested_crop["code"] == sample_crop.code
    assert nested_crop["name_en"] == sample_crop.name_en
    assert nested_crop["name_kn"] == sample_crop.name_kn
    assert nested_crop["is_active"] is True
    # Validate against schema
    FarmerCropWithDetailsResponse.model_validate(data)


def test_post_unknown_farmer_returns_404(sample_crop):
    """Test 5: POST unknown farmer returns 404."""
    unknown_farmer_id = uuid.uuid4()
    payload = {
        "crop_id": str(sample_crop.id),
        "area_acres": "2.00",
    }
    response = client.post(f"/api/v1/farmers/{unknown_farmer_id}/crops", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Farmer not found"


def test_post_unknown_crop_returns_404(sample_farmer):
    """Test 6: POST unknown crop returns 404."""
    unknown_crop_id = uuid.uuid4()
    payload = {
        "crop_id": str(unknown_crop_id),
        "area_acres": "2.00",
    }
    response = client.post(f"/api/v1/farmers/{sample_farmer.id}/crops", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Crop not found"


def test_post_inactive_crop_returns_409(sample_farmer, inactive_crop):
    """Test 7: POST inactive crop returns 409."""
    payload = {
        "crop_id": str(inactive_crop.id),
        "area_acres": "1.00",
    }
    response = client.post(f"/api/v1/farmers/{sample_farmer.id}/crops", json=payload)
    assert response.status_code == 409
    assert response.json()["detail"] == "Crop is inactive"


def test_post_duplicate_crop_returns_409(sample_farmer, sample_crop):
    """Test 8: POST duplicate crop returns 409."""
    payload = {
        "crop_id": str(sample_crop.id),
        "area_acres": "5.00",
    }
    # First registration
    resp1 = client.post(f"/api/v1/farmers/{sample_farmer.id}/crops", json=payload)
    assert resp1.status_code == 201

    # Duplicate registration
    resp2 = client.post(f"/api/v1/farmers/{sample_farmer.id}/crops", json=payload)
    assert resp2.status_code == 409
    assert resp2.json()["detail"] == "Farmer already has this crop"


def test_post_invalid_acreage_returns_422(sample_farmer, sample_crop):
    """Test 9: POST invalid acreage returns 422."""
    payload = {
        "crop_id": str(sample_crop.id),
        "area_acres": "-3.50",
    }
    response = client.post(f"/api/v1/farmers/{sample_farmer.id}/crops", json=payload)
    assert response.status_code == 422
    assert "area_acres" in str(response.json()).lower()


# ==============================================================================
# 3. GET /api/v1/farmers/{farmer_id}/crops
# ==============================================================================

def test_get_farmer_crops_returns_200(sample_farmer, sample_crop):
    """Test 10: GET farmer crops returns 200."""
    payload = {"crop_id": str(sample_crop.id), "area_acres": "2.00"}
    client.post(f"/api/v1/farmers/{sample_farmer.id}/crops", json=payload)

    response = client.get(f"/api/v1/farmers/{sample_farmer.id}/crops")
    assert response.status_code == 200
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["crop"]["code"] == "arecanut"


def test_get_farmer_crops_returns_only_that_farmers_relationships(
    override_db, sample_farmer, sample_crop
):
    """Test 11: GET farmer crops returns only that farmer's relationships."""
    # Farmer 2
    farmer_2 = UserProfile(id=uuid.uuid4(), full_name="Farmer Two", language="en")
    override_db.add(farmer_2)
    override_db.commit()

    # Crop 2
    crop_2 = Crop(
        id=uuid.uuid4(),
        code="cotton",
        name_en="Cotton",
        name_kn="ಹತ್ತಿ",
        is_active=True,
    )
    override_db.add(crop_2)
    override_db.commit()

    # Register crop for farmer 1
    client.post(
        f"/api/v1/farmers/{sample_farmer.id}/crops",
        json={"crop_id": str(sample_crop.id), "area_acres": "1.00"},
    )
    # Register crop for farmer 2
    client.post(
        f"/api/v1/farmers/{farmer_2.id}/crops",
        json={"crop_id": str(crop_2.id), "area_acres": "3.00"},
    )

    # Fetch farmer 1 crops
    resp1 = client.get(f"/api/v1/farmers/{sample_farmer.id}/crops")
    assert resp1.status_code == 200
    data1 = resp1.json()
    assert len(data1) == 1
    assert data1[0]["farmer_id"] == str(sample_farmer.id)
    assert data1[0]["crop_id"] == str(sample_crop.id)

    # Fetch farmer 2 crops
    resp2 = client.get(f"/api/v1/farmers/{farmer_2.id}/crops")
    assert resp2.status_code == 200
    data2 = resp2.json()
    assert len(data2) == 1
    assert data2[0]["farmer_id"] == str(farmer_2.id)
    assert data2[0]["crop_id"] == str(crop_2.id)


def test_get_farmer_crops_unknown_farmer_returns_404():
    """Test 12: GET unknown farmer returns 404."""
    unknown_farmer_id = uuid.uuid4()
    response = client.get(f"/api/v1/farmers/{unknown_farmer_id}/crops")
    assert response.status_code == 404
    assert response.json()["detail"] == "Farmer not found"


# ==============================================================================
# 4. GET /api/v1/farmers/{farmer_id}/crops/{crop_id}
# ==============================================================================

def test_get_individual_farmer_crop_returns_200(sample_farmer, sample_crop):
    """Test 13: GET individual farmer crop returns 200."""
    create_resp = client.post(
        f"/api/v1/farmers/{sample_farmer.id}/crops",
        json={"crop_id": str(sample_crop.id), "area_acres": "5.50"},
    )
    farmer_crop_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/farmers/{sample_farmer.id}/crops/{farmer_crop_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == farmer_crop_id
    assert data["farmer_id"] == str(sample_farmer.id)
    assert data["crop"]["name_en"] == "Arecanut"


def test_get_individual_farmer_crop_cannot_access_another_farmer_relationship(
    override_db, sample_farmer, sample_crop
):
    """Test 14: GET individual farmer crop cannot access another farmer's relationship."""
    # Farmer 2
    farmer_2 = UserProfile(id=uuid.uuid4(), full_name="Farmer Two", language="en")
    override_db.add(farmer_2)
    override_db.commit()

    # Create relationship for farmer 1
    create_resp = client.post(
        f"/api/v1/farmers/{sample_farmer.id}/crops",
        json={"crop_id": str(sample_crop.id), "area_acres": "5.50"},
    )
    farmer_crop_id = create_resp.json()["id"]

    # Try to access farmer 1's relationship using farmer 2's URL
    response = client.get(f"/api/v1/farmers/{farmer_2.id}/crops/{farmer_crop_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Farmer crop not found"


def test_get_unknown_farmer_crop_returns_404(sample_farmer):
    """Test 15: GET unknown farmer-crop returns 404."""
    unknown_fc_id = uuid.uuid4()
    response = client.get(f"/api/v1/farmers/{sample_farmer.id}/crops/{unknown_fc_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Farmer crop not found"


# ==============================================================================
# 5. PATCH /api/v1/farmers/{farmer_id}/crops/{crop_id}
# ==============================================================================

def test_patch_acreage_returns_200(sample_farmer, sample_crop):
    """Test 16: PATCH acreage returns 200."""
    create_resp = client.post(
        f"/api/v1/farmers/{sample_farmer.id}/crops",
        json={"crop_id": str(sample_crop.id), "area_acres": "2.00", "is_primary": True},
    )
    farmer_crop_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/api/v1/farmers/{sample_farmer.id}/crops/{farmer_crop_id}",
        json={"area_acres": "8.50"},
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["area_acres"] == "8.50"
    assert data["is_primary"] is True  # Preserved


def test_patch_primary_flag_returns_200(sample_farmer, sample_crop):
    """Test 17: PATCH primary flag returns 200."""
    create_resp = client.post(
        f"/api/v1/farmers/{sample_farmer.id}/crops",
        json={"crop_id": str(sample_crop.id), "area_acres": "3.00", "is_primary": False},
    )
    farmer_crop_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/api/v1/farmers/{sample_farmer.id}/crops/{farmer_crop_id}",
        json={"is_primary": True},
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["is_primary"] is True
    assert data["area_acres"] == "3.00"  # Preserved


def test_patch_preserves_unspecified_fields(sample_farmer, sample_crop):
    """Test 18: PATCH preserves unspecified fields."""
    create_resp = client.post(
        f"/api/v1/farmers/{sample_farmer.id}/crops",
        json={"crop_id": str(sample_crop.id), "area_acres": "6.00", "is_primary": True},
    )
    farmer_crop_id = create_resp.json()["id"]

    # Empty patch should preserve everything
    patch_resp = client.patch(
        f"/api/v1/farmers/{sample_farmer.id}/crops/{farmer_crop_id}",
        json={},
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["area_acres"] == "6.00"
    assert data["is_primary"] is True


def test_patch_explicit_null_acreage_works(sample_farmer, sample_crop):
    """Test 19: PATCH explicit null acreage works."""
    create_resp = client.post(
        f"/api/v1/farmers/{sample_farmer.id}/crops",
        json={"crop_id": str(sample_crop.id), "area_acres": "4.00", "is_primary": True},
    )
    farmer_crop_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/api/v1/farmers/{sample_farmer.id}/crops/{farmer_crop_id}",
        json={"area_acres": None},
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["area_acres"] is None
    assert data["is_primary"] is True


def test_patch_unknown_farmer_returns_404(sample_farmer, sample_crop):
    """Test 20: PATCH unknown farmer returns 404."""
    create_resp = client.post(
        f"/api/v1/farmers/{sample_farmer.id}/crops",
        json={"crop_id": str(sample_crop.id), "area_acres": "4.00"},
    )
    farmer_crop_id = create_resp.json()["id"]
    unknown_farmer_id = uuid.uuid4()

    patch_resp = client.patch(
        f"/api/v1/farmers/{unknown_farmer_id}/crops/{farmer_crop_id}",
        json={"area_acres": "5.00"},
    )
    assert patch_resp.status_code == 404
    assert patch_resp.json()["detail"] == "Farmer not found"


def test_patch_unknown_relationship_returns_404(sample_farmer):
    """Test 21: PATCH unknown relationship returns 404."""
    unknown_fc_id = uuid.uuid4()
    patch_resp = client.patch(
        f"/api/v1/farmers/{sample_farmer.id}/crops/{unknown_fc_id}",
        json={"area_acres": "5.00"},
    )
    assert patch_resp.status_code == 404
    assert patch_resp.json()["detail"] == "Farmer crop not found"


# ==============================================================================
# 6. DELETE /api/v1/farmers/{farmer_id}/crops/{crop_id}
# ==============================================================================

def test_delete_returns_204(sample_farmer, sample_crop):
    """Test 22: DELETE returns 204."""
    create_resp = client.post(
        f"/api/v1/farmers/{sample_farmer.id}/crops",
        json={"crop_id": str(sample_crop.id), "area_acres": "3.00"},
    )
    farmer_crop_id = create_resp.json()["id"]

    delete_resp = client.delete(f"/api/v1/farmers/{sample_farmer.id}/crops/{farmer_crop_id}")
    assert delete_resp.status_code == 204
    assert delete_resp.content == b""


def test_delete_removes_only_farmer_crop_relationship(sample_farmer, sample_crop):
    """Test 23: DELETE removes only the farmer-crop relationship."""
    create_resp = client.post(
        f"/api/v1/farmers/{sample_farmer.id}/crops",
        json={"crop_id": str(sample_crop.id), "area_acres": "3.00"},
    )
    farmer_crop_id = create_resp.json()["id"]

    # Delete
    delete_resp = client.delete(f"/api/v1/farmers/{sample_farmer.id}/crops/{farmer_crop_id}")
    assert delete_resp.status_code == 204

    # Subsequent GET returns 404
    get_resp = client.get(f"/api/v1/farmers/{sample_farmer.id}/crops/{farmer_crop_id}")
    assert get_resp.status_code == 404


def test_delete_does_not_remove_crop_catalog_entry(override_db, sample_farmer, sample_crop):
    """Test 24: DELETE does not remove the Crop catalog entry."""
    create_resp = client.post(
        f"/api/v1/farmers/{sample_farmer.id}/crops",
        json={"crop_id": str(sample_crop.id), "area_acres": "3.00"},
    )
    farmer_crop_id = create_resp.json()["id"]

    client.delete(f"/api/v1/farmers/{sample_farmer.id}/crops/{farmer_crop_id}")

    # Crop still exists in catalog
    crops_resp = client.get("/api/v1/crops")
    assert crops_resp.status_code == 200
    assert any(c["id"] == str(sample_crop.id) for c in crops_resp.json())


def test_delete_unknown_farmer_returns_404(sample_farmer, sample_crop):
    """Test 25: DELETE unknown farmer returns 404."""
    create_resp = client.post(
        f"/api/v1/farmers/{sample_farmer.id}/crops",
        json={"crop_id": str(sample_crop.id), "area_acres": "3.00"},
    )
    farmer_crop_id = create_resp.json()["id"]
    unknown_farmer_id = uuid.uuid4()

    delete_resp = client.delete(f"/api/v1/farmers/{unknown_farmer_id}/crops/{farmer_crop_id}")
    assert delete_resp.status_code == 404
    assert delete_resp.json()["detail"] == "Farmer not found"


def test_delete_unknown_relationship_returns_404(sample_farmer):
    """Test 26: DELETE unknown relationship returns 404."""
    unknown_fc_id = uuid.uuid4()
    delete_resp = client.delete(f"/api/v1/farmers/{sample_farmer.id}/crops/{unknown_fc_id}")
    assert delete_resp.status_code == 404
    assert delete_resp.json()["detail"] == "Farmer crop not found"


# ==============================================================================
# 7. OpenAPI and Documentation Tests
# ==============================================================================

def test_openapi_contains_all_six_crop_endpoints():
    """Test 27: OpenAPI contains all six crop-management endpoints and /docs returns 200."""
    # Check /docs returns 200
    docs_resp = client.get("/docs")
    assert docs_resp.status_code == 200

    # Check /openapi.json contains all 6 endpoints
    response = client.get("/openapi.json")
    assert response.status_code == 200
    schema = response.json()
    paths = schema["paths"]

    # 1. GET /api/v1/crops
    assert "/api/v1/crops" in paths
    assert "get" in paths["/api/v1/crops"]

    # 2 & 3. POST and GET /api/v1/farmers/{farmer_id}/crops
    assert "/api/v1/farmers/{farmer_id}/crops" in paths
    assert "post" in paths["/api/v1/farmers/{farmer_id}/crops"]
    assert "get" in paths["/api/v1/farmers/{farmer_id}/crops"]

    # 4, 5 & 6. GET, PATCH, DELETE /api/v1/farmers/{farmer_id}/crops/{crop_id}
    assert "/api/v1/farmers/{farmer_id}/crops/{crop_id}" in paths
    assert "get" in paths["/api/v1/farmers/{farmer_id}/crops/{crop_id}"]
    assert "patch" in paths["/api/v1/farmers/{farmer_id}/crops/{crop_id}"]
    assert "delete" in paths["/api/v1/farmers/{farmer_id}/crops/{crop_id}"]
