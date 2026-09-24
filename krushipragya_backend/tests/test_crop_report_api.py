from datetime import datetime, timedelta, timezone
import io
import uuid
from PIL import Image
import pytest
from fastapi.testclient import TestClient

from app.api.v1.crop_report import get_crop_report_service
from app.database.connection import get_db
from app.main import app
from app.models.crop import Crop
from app.models.crop_report import CropReport
from app.models.farmer_crop import FarmerCrop
from app.models.user_profile import UserProfile
from app.schemas.crop_report import CropReportResponse
from app.services.crop_report_service import CropReportService
from app.services.crop_report_storage_service import (
    ImageSizeLimitExceededError,
    InvalidImageError,
    StorageServiceError,
    UnsupportedImageTypeError,
)

client = TestClient(app)


def make_test_image(format_name: str) -> bytes:
    """Create a minimal valid raster image in memory."""
    img = Image.new("RGB", (16, 16), color="green")
    buf = io.BytesIO()
    img.save(buf, format=format_name)
    return buf.getvalue()


class MockStorageService:
    """Mock storage service for deterministic API testing."""

    def __init__(self):
        self.uploaded_paths: list[str] = []
        self.deleted_paths: list[str] = []
        self.fail_upload = False

    def validate_image(self, content: bytes, content_type: str) -> str:
        normalized = content_type.lower().strip()
        if normalized == "image/jpg":
            normalized = "image/jpeg"
        if normalized not in ("image/jpeg", "image/png", "image/webp"):
            raise UnsupportedImageTypeError(f"Unsupported image type '{content_type}'")
        if len(content) > 10 * 1024 * 1024:
            raise ImageSizeLimitExceededError("File exceeds 10 MB")
        if len(content) == 0:
            raise InvalidImageError("Empty file")
        return normalized

    def generate_storage_path(self, farmer_id, report_id, content_type):
        ext = {"image/jpeg": ".jpg", "image/png": ".png", "image/webp": ".webp"}.get(content_type, ".jpg")
        return f"farmers/{farmer_id}/crop-reports/{report_id}/{uuid.uuid4()}{ext}"

    def upload_image(self, storage_path, content, content_type):
        if self.fail_upload:
            raise StorageServiceError("Storage server unreachable")
        self.uploaded_paths.append(storage_path)
        return storage_path

    def delete_image(self, storage_path):
        self.deleted_paths.append(storage_path)
        return True


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
        is_desc = False
        for arg in args:
            if str(arg).endswith("DESC") or "desc" in str(arg).lower():
                is_desc = True

        def sort_key(item):
            if hasattr(item, "created_at") and item.created_at is not None:
                return item.created_at
            return datetime.min.replace(tzinfo=timezone.utc)

        return FakeQuery(sorted(self.items, key=sort_key, reverse=is_desc))

    def all(self):
        return list(self.items)

    def first(self):
        return self.items[0] if self.items else None


class InMemorySession:
    """In-memory transactional session simulator supporting UserProfile, Crop, FarmerCrop, and CropReport."""

    def __init__(self):
        self.crops: dict[uuid.UUID, Crop] = {}
        self.farmers: dict[uuid.UUID, UserProfile] = {}
        self.farmer_crops: dict[uuid.UUID, FarmerCrop] = {}
        self.crop_reports: dict[uuid.UUID, CropReport] = {}
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
        if model is CropReport:
            return self.crop_reports.get(entity_id)
        return None

    def query(self, model):
        if model is Crop:
            items = list(self.crops.values())
        elif model is FarmerCrop:
            items = list(self.farmer_crops.values())
        elif model is UserProfile:
            items = list(self.farmers.values())
        elif model is CropReport:
            items = list(self.crop_reports.values())
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
                self.farmer_crops[obj.id] = obj
            elif isinstance(obj, CropReport):
                if getattr(obj, "farmer_crop", None) is None and obj.farmer_crop_id in self.farmer_crops:
                    obj.farmer_crop = self.farmer_crops[obj.farmer_crop_id]
                self.crop_reports[obj.id] = obj
        self.pending_adds.clear()
        self.committed = True

    def refresh(self, obj):
        if isinstance(obj, CropReport) and getattr(obj, "farmer_crop", None) is None:
            if obj.farmer_crop_id in self.farmer_crops:
                obj.farmer_crop = self.farmer_crops[obj.farmer_crop_id]

    def delete(self, obj):
        if isinstance(obj, CropReport) and obj.id in self.crop_reports:
            del self.crop_reports[obj.id]
        elif isinstance(obj, FarmerCrop) and obj.id in self.farmer_crops:
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
def mock_storage():
    """Fresh MockStorageService instance for testing."""
    return MockStorageService()


@pytest.fixture(autouse=True)
def override_storage(mock_storage):
    """Ensure every test uses MockStorageService to isolate from Supabase."""
    service = CropReportService(storage_service=mock_storage)
    app.dependency_overrides[get_crop_report_service] = lambda: service
    yield mock_storage
    app.dependency_overrides.pop(get_crop_report_service, None)



@pytest.fixture
def farmer(override_db):
    """Seed primary farmer."""
    f = UserProfile(id=uuid.uuid4(), full_name="Basavaraj Patil", language="kn")
    override_db.add(f)
    override_db.commit()
    return f


@pytest.fixture
def other_farmer(override_db):
    """Seed secondary farmer."""
    f = UserProfile(id=uuid.uuid4(), full_name="Manjunath Hegde", language="kn")
    override_db.add(f)
    override_db.commit()
    return f


@pytest.fixture
def crop(override_db):
    """Seed canonical crop."""
    c = Crop(id=uuid.uuid4(), code="arecanut", name_en="Arecanut", name_kn="ಅಡಿಕೆ", is_active=True)
    override_db.add(c)
    override_db.commit()
    return c


@pytest.fixture
def farmer_crop(override_db, farmer, crop):
    """Seed farmer crop for primary farmer."""
    fc = FarmerCrop(id=uuid.uuid4(), farmer_id=farmer.id, crop_id=crop.id, is_primary=True)
    fc.crop = crop
    fc.farmer = farmer
    override_db.add(fc)
    override_db.commit()
    return fc


@pytest.fixture
def other_farmer_crop(override_db, other_farmer, crop):
    """Seed farmer crop for secondary farmer."""
    fc = FarmerCrop(id=uuid.uuid4(), farmer_id=other_farmer.id, crop_id=crop.id, is_primary=True)
    fc.crop = crop
    fc.farmer = other_farmer
    override_db.add(fc)
    override_db.commit()
    return fc


# ==============================================================================
# 1. POST /api/v1/farmers/{farmer_id}/crop-reports
# ==============================================================================

def test_post_creates_crop_report(farmer, farmer_crop):
    """Test 1: POST creates crop report → 201."""
    payload = {
        "farmer_crop_id": str(farmer_crop.id),
        "notes": "Leaves showing unusual yellow spots",
        "image_filename": "leaf-photo.jpg",
    }
    response = client.post(f"/api/v1/farmers/{farmer.id}/crop-reports", json=payload)
    assert response.status_code == 201
    data = response.json()
    assert data["farmer_crop_id"] == str(farmer_crop.id)
    assert data["notes"] == "Leaves showing unusual yellow spots"
    assert data["image_filename"] == "leaf-photo.jpg"
    assert data["image_storage_path"] is None
    assert "id" in data
    assert "created_at" in data
    assert "updated_at" in data


def test_post_response_matches_crop_report_response_schema(farmer, farmer_crop):
    """Test 2: POST response matches CropReportResponse schema."""
    payload = {
        "farmer_crop_id": str(farmer_crop.id),
        "notes": "Mild wilting observed",
    }
    response = client.post(f"/api/v1/farmers/{farmer.id}/crop-reports", json=payload)
    assert response.status_code == 201
    validated = CropReportResponse.model_validate(response.json())
    assert validated.farmer_crop_id == farmer_crop.id
    assert validated.notes == "Mild wilting observed"


def test_post_with_invalid_farmer_returns_404(farmer_crop):
    """Test 3: POST with invalid farmer → 404."""
    unknown_farmer_id = uuid.uuid4()
    payload = {
        "farmer_crop_id": str(farmer_crop.id),
        "notes": "Unknown farmer report",
    }
    response = client.post(f"/api/v1/farmers/{unknown_farmer_id}/crop-reports", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Farmer not found"


def test_post_with_invalid_farmer_crop_returns_404(farmer):
    """Test 4: POST with invalid FarmerCrop → 404."""
    unknown_fc_id = uuid.uuid4()
    payload = {
        "farmer_crop_id": str(unknown_fc_id),
        "notes": "Unknown farmer crop report",
    }
    response = client.post(f"/api/v1/farmers/{farmer.id}/crop-reports", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Farmer crop not found"


def test_post_with_farmer_crop_owned_by_another_farmer_returns_404(farmer, other_farmer_crop):
    """Test 5: POST with FarmerCrop owned by another farmer → 404."""
    payload = {
        "farmer_crop_id": str(other_farmer_crop.id),
        "notes": "Attempt to submit report for another farmer's crop",
    }
    response = client.post(f"/api/v1/farmers/{farmer.id}/crop-reports", json=payload)
    assert response.status_code == 404
    assert response.json()["detail"] == "Farmer crop not found"


# ==============================================================================
# 2. GET /api/v1/farmers/{farmer_id}/crop-reports?farmer_crop_id={id}
# ==============================================================================

def test_get_list_returns_200(farmer, farmer_crop):
    """Test 6: GET list returns 200."""
    response = client.get(
        f"/api/v1/farmers/{farmer.id}/crop-reports?farmer_crop_id={farmer_crop.id}"
    )
    assert response.status_code == 200
    assert response.json() == []


def test_get_list_returns_multiple_reports(farmer, farmer_crop):
    """Test 7: GET list returns multiple reports."""
    client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={"farmer_crop_id": str(farmer_crop.id), "notes": "Report 1"},
    )
    client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={"farmer_crop_id": str(farmer_crop.id), "notes": "Report 2"},
    )

    response = client.get(
        f"/api/v1/farmers/{farmer.id}/crop-reports?farmer_crop_id={farmer_crop.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2


def test_get_list_returns_newest_first(override_db, farmer, farmer_crop):
    """Test 8: GET list returns newest first."""
    now = datetime.now(timezone.utc)
    old_report = CropReport(
        id=uuid.uuid4(),
        farmer_crop_id=farmer_crop.id,
        notes="Older report",
        created_at=now - timedelta(days=3),
    )
    new_report = CropReport(
        id=uuid.uuid4(),
        farmer_crop_id=farmer_crop.id,
        notes="Newer report",
        created_at=now,
    )
    override_db.add(old_report)
    override_db.add(new_report)
    override_db.commit()

    response = client.get(
        f"/api/v1/farmers/{farmer.id}/crop-reports?farmer_crop_id={farmer_crop.id}"
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    assert data[0]["id"] == str(new_report.id)
    assert data[1]["id"] == str(old_report.id)


def test_get_list_with_no_reports_returns_empty_list(farmer, farmer_crop):
    """Test 9: GET list with no reports returns []."""
    response = client.get(
        f"/api/v1/farmers/{farmer.id}/crop-reports?farmer_crop_id={farmer_crop.id}"
    )
    assert response.status_code == 200
    assert response.json() == []


def test_get_list_for_another_farmer_crop_returns_404(farmer, other_farmer_crop):
    """Test 10: GET list for another farmer's FarmerCrop → 404."""
    response = client.get(
        f"/api/v1/farmers/{farmer.id}/crop-reports?farmer_crop_id={other_farmer_crop.id}"
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Farmer crop not found"


# ==============================================================================
# 3. GET /api/v1/farmers/{farmer_id}/crop-reports/{report_id}
# ==============================================================================

def test_get_single_report_returns_200(farmer, farmer_crop):
    """Test 11: GET single report → 200."""
    create_resp = client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={"farmer_crop_id": str(farmer_crop.id), "notes": "Specific report"},
    )
    report_id = create_resp.json()["id"]

    response = client.get(f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}")
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == report_id
    assert data["notes"] == "Specific report"
    assert data["farmer_crop_id"] == str(farmer_crop.id)


def test_get_missing_report_returns_404(farmer):
    """Test 12: GET missing report → 404."""
    unknown_report_id = uuid.uuid4()
    response = client.get(f"/api/v1/farmers/{farmer.id}/crop-reports/{unknown_report_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Crop report not found"


def test_get_another_farmer_report_returns_404(farmer, other_farmer, other_farmer_crop):
    """Test 13: GET another farmer's report → 404 (Security check)."""
    create_resp = client.post(
        f"/api/v1/farmers/{other_farmer.id}/crop-reports",
        json={"farmer_crop_id": str(other_farmer_crop.id), "notes": "Farmer B report"},
    )
    report_id = create_resp.json()["id"]

    # Farmer A requests Farmer B's report
    response = client.get(f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}")
    assert response.status_code == 404
    assert response.json()["detail"] == "Crop report not found"


# ==============================================================================
# 4. PATCH /api/v1/farmers/{farmer_id}/crop-reports/{report_id}
# ==============================================================================

def test_patch_notes_returns_200(farmer, farmer_crop):
    """Test 14: PATCH notes → 200."""
    create_resp = client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={
            "farmer_crop_id": str(farmer_crop.id),
            "notes": "Original notes",
            "image_filename": "photo.jpg",
        },
    )
    report_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}",
        json={"notes": "Updated observation notes"},
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["notes"] == "Updated observation notes"
    assert data["image_filename"] == "photo.jpg"  # Preserved


def test_patch_image_filename_returns_200(farmer, farmer_crop):
    """Test 15: PATCH image_filename → 200."""
    create_resp = client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={
            "farmer_crop_id": str(farmer_crop.id),
            "notes": "Leaf analysis",
            "image_filename": "old_name.jpg",
        },
    )
    report_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}",
        json={"image_filename": "new_leaf_image.jpg"},
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["image_filename"] == "new_leaf_image.jpg"
    assert data["notes"] == "Leaf analysis"  # Preserved


def test_patch_partial_update_preserves_omitted_fields(farmer, farmer_crop):
    """Test 16: PATCH partial update preserves omitted fields."""
    create_resp = client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={
            "farmer_crop_id": str(farmer_crop.id),
            "notes": "Notes should stay",
            "image_filename": "image_should_stay.png",
        },
    )
    report_id = create_resp.json()["id"]

    # Empty patch
    patch_resp = client.patch(
        f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}",
        json={},
    )
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    assert data["notes"] == "Notes should stay"
    assert data["image_filename"] == "image_should_stay.png"


def test_patch_another_farmer_report_returns_404(farmer, other_farmer, other_farmer_crop):
    """Test 17: PATCH another farmer's report → 404 (Security check)."""
    create_resp = client.post(
        f"/api/v1/farmers/{other_farmer.id}/crop-reports",
        json={"farmer_crop_id": str(other_farmer_crop.id), "notes": "Farmer B notes"},
    )
    report_id = create_resp.json()["id"]

    patch_resp = client.patch(
        f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}",
        json={"notes": "Hacked notes"},
    )
    assert patch_resp.status_code == 404
    assert patch_resp.json()["detail"] == "Crop report not found"


def test_patch_cannot_modify_farmer_crop_id(farmer, farmer_crop, other_farmer_crop):
    """Test 18: PATCH cannot modify farmer_crop_id."""
    create_resp = client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={"farmer_crop_id": str(farmer_crop.id), "notes": "Original crop"},
    )
    report_id = create_resp.json()["id"]

    # Attempt to send farmer_crop_id in PATCH payload
    patch_resp = client.patch(
        f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}",
        json={"farmer_crop_id": str(other_farmer_crop.id), "notes": "Attempted move"},
    )
    # Schema validation does not accept farmer_crop_id (extra fields ignored or rejected)
    assert patch_resp.status_code == 200
    data = patch_resp.json()
    # farmer_crop_id remains unmodified
    assert data["farmer_crop_id"] == str(farmer_crop.id)
    assert data["notes"] == "Attempted move"


# ==============================================================================
# 5. DELETE /api/v1/farmers/{farmer_id}/crop-reports/{report_id}
# ==============================================================================

def test_delete_report_returns_204_and_no_body(farmer, farmer_crop):
    """Test 19 & 20: DELETE report → 204 with no response body."""
    create_resp = client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={"farmer_crop_id": str(farmer_crop.id), "notes": "Delete me"},
    )
    report_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}")
    assert del_resp.status_code == 204
    assert del_resp.content == b""

    # Verify report is gone
    get_resp = client.get(f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}")
    assert get_resp.status_code == 404


def test_delete_missing_report_returns_404(farmer):
    """Test 21: DELETE missing report → 404."""
    unknown_report_id = uuid.uuid4()
    del_resp = client.delete(f"/api/v1/farmers/{farmer.id}/crop-reports/{unknown_report_id}")
    assert del_resp.status_code == 404
    assert del_resp.json()["detail"] == "Crop report not found"


def test_delete_another_farmer_report_returns_404(farmer, other_farmer, other_farmer_crop):
    """Test 22: DELETE another farmer's report → 404 (Security check)."""
    create_resp = client.post(
        f"/api/v1/farmers/{other_farmer.id}/crop-reports",
        json={"farmer_crop_id": str(other_farmer_crop.id), "notes": "Farmer B report"},
    )
    report_id = create_resp.json()["id"]

    del_resp = client.delete(f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}")
    assert del_resp.status_code == 404
    assert del_resp.json()["detail"] == "Crop report not found"


# ==============================================================================
# 6. Validation Errors & OpenAPI Verification
# ==============================================================================

def test_invalid_uuid_path_parameter_returns_422(farmer):
    """Test 23: Invalid UUID path parameter → 422."""
    response = client.get(f"/api/v1/farmers/{farmer.id}/crop-reports/not-a-valid-uuid")
    assert response.status_code == 422


def test_invalid_request_body_returns_422(farmer):
    """Test 24: Invalid request body → 422."""
    # Missing required farmer_crop_id
    response = client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={"notes": "Missing farmer_crop_id"},
    )
    assert response.status_code == 422

    # notes > 1000 characters
    long_notes = "a" * 1001
    resp2 = client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={"farmer_crop_id": str(uuid.uuid4()), "notes": long_notes},
    )
    assert resp2.status_code == 422


def test_openapi_contains_expected_crop_report_endpoints():
    """Test 25: OpenAPI contains the expected crop-report endpoints and /docs returns 200."""
    docs_resp = client.get("/docs")
    assert docs_resp.status_code == 200

    openapi_resp = client.get("/openapi.json")
    assert openapi_resp.status_code == 200
    schema = openapi_resp.json()
    paths = schema["paths"]

    # Collection routes
    assert "/api/v1/farmers/{farmer_id}/crop-reports" in paths
    assert "post" in paths["/api/v1/farmers/{farmer_id}/crop-reports"]
    assert "get" in paths["/api/v1/farmers/{farmer_id}/crop-reports"]

    # Member routes
    assert "/api/v1/farmers/{farmer_id}/crop-reports/{report_id}" in paths
    assert "get" in paths["/api/v1/farmers/{farmer_id}/crop-reports/{report_id}"]
    assert "patch" in paths["/api/v1/farmers/{farmer_id}/crop-reports/{report_id}"]
    assert "delete" in paths["/api/v1/farmers/{farmer_id}/crop-reports/{report_id}"]

    # Image upload route
    assert "/api/v1/farmers/{farmer_id}/crop-reports/{report_id}/image" in paths
    assert "put" in paths["/api/v1/farmers/{farmer_id}/crop-reports/{report_id}/image"]


# ==============================================================================
# 7. PUT /api/v1/farmers/{farmer_id}/crop-reports/{report_id}/image (Image Upload)
# ==============================================================================

def test_upload_image_jpeg_success(farmer, farmer_crop, mock_storage):
    """Test 26: Upload valid JPEG image → 200 and image_storage_path updated."""
    # Create report first
    create_resp = client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={"farmer_crop_id": str(farmer_crop.id), "notes": "Leaves with spots"},
    )
    assert create_resp.status_code == 201
    report_id = create_resp.json()["id"]

    # Upload JPEG
    img_bytes = make_test_image("JPEG")
    files = {"file": ("test_leaf.jpg", img_bytes, "image/jpeg")}
    response = client.put(
        f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}/image",
        files=files,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["id"] == report_id
    assert data["image_filename"] == "test_leaf.jpg"
    assert data["image_storage_path"] is not None
    assert data["image_storage_path"].startswith(f"farmers/{farmer.id}/crop-reports/{report_id}/")
    assert data["image_storage_path"].endswith(".jpg")
    assert len(mock_storage.uploaded_paths) == 1
    # Verify response matches Pydantic schema
    CropReportResponse(**data)


def test_upload_image_png_success(farmer, farmer_crop, mock_storage):
    """Test 27: Upload valid PNG image → 200 and .png extension."""
    create_resp = client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={"farmer_crop_id": str(farmer_crop.id)},
    )
    report_id = create_resp.json()["id"]

    img_bytes = make_test_image("PNG")
    files = {"file": ("sample.png", img_bytes, "image/png")}
    response = client.put(
        f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}/image",
        files=files,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["image_storage_path"].endswith(".png")
    assert data["image_filename"] == "sample.png"


def test_upload_image_webp_success(farmer, farmer_crop, mock_storage):
    """Test 28: Upload valid WebP image → 200 and .webp extension."""
    create_resp = client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={"farmer_crop_id": str(farmer_crop.id)},
    )
    report_id = create_resp.json()["id"]

    img_bytes = make_test_image("WEBP")
    files = {"file": ("sample.webp", img_bytes, "image/webp")}
    response = client.put(
        f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}/image",
        files=files,
    )
    assert response.status_code == 200
    data = response.json()
    assert data["image_storage_path"].endswith(".webp")
    assert data["image_filename"] == "sample.webp"


def test_upload_image_unsupported_mime_rejected(farmer, farmer_crop):
    """Test 29: Unsupported MIME type (PDF) → 400 Bad Request."""
    create_resp = client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={"farmer_crop_id": str(farmer_crop.id)},
    )
    report_id = create_resp.json()["id"]

    pdf_bytes = b"%PDF-1.4 mock pdf content"
    files = {"file": ("manual.pdf", pdf_bytes, "application/pdf")}
    response = client.put(
        f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}/image",
        files=files,
    )
    assert response.status_code == 400
    assert "Unsupported image type" in response.json()["detail"]


def test_upload_image_oversized_rejected(farmer, farmer_crop):
    """Test 30: File exceeding 10 MB limit → 413 Request Entity Too Large."""
    create_resp = client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={"farmer_crop_id": str(farmer_crop.id)},
    )
    report_id = create_resp.json()["id"]

    oversized = b"x" * (10 * 1024 * 1024 + 1)
    files = {"file": ("large.jpg", oversized, "image/jpeg")}
    response = client.put(
        f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}/image",
        files=files,
    )
    assert response.status_code == 413
    assert "10 MB" in response.json()["detail"]


def test_upload_image_empty_file_rejected(farmer, farmer_crop):
    """Test 31: Empty image file (0 bytes) → 400 Bad Request."""
    create_resp = client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={"farmer_crop_id": str(farmer_crop.id)},
    )
    report_id = create_resp.json()["id"]

    files = {"file": ("empty.jpg", b"", "image/jpeg")}
    response = client.put(
        f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}/image",
        files=files,
    )
    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_upload_image_missing_file_rejected(farmer, farmer_crop):
    """Test 32: Missing file in multipart body → 422 Unprocessable Entity."""
    create_resp = client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={"farmer_crop_id": str(farmer_crop.id)},
    )
    report_id = create_resp.json()["id"]

    response = client.put(
        f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}/image",
        data={"some_field": "val"},
    )
    assert response.status_code == 422


def test_upload_image_invalid_farmer_returns_404(farmer, farmer_crop):
    """Test 33: Nonexistent farmer ID → 404 Not Found."""
    fake_farmer_id = uuid.uuid4()
    files = {"file": ("leaf.jpg", make_test_image("JPEG"), "image/jpeg")}
    response = client.put(
        f"/api/v1/farmers/{fake_farmer_id}/crop-reports/{uuid.uuid4()}/image",
        files=files,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Farmer not found"


def test_upload_image_report_owned_by_another_farmer_returns_404(farmer, other_farmer, farmer_crop):
    """Test 34: Upload to report owned by another farmer → 404 Not Found."""
    create_resp = client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={"farmer_crop_id": str(farmer_crop.id)},
    )
    report_id = create_resp.json()["id"]

    files = {"file": ("leaf.jpg", make_test_image("JPEG"), "image/jpeg")}
    response = client.put(
        f"/api/v1/farmers/{other_farmer.id}/crop-reports/{report_id}/image",
        files=files,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Crop report not found"


def test_upload_image_missing_report_returns_404(farmer):
    """Test 35: Upload to missing report ID → 404 Not Found."""
    fake_report_id = uuid.uuid4()
    files = {"file": ("leaf.jpg", make_test_image("JPEG"), "image/jpeg")}
    response = client.put(
        f"/api/v1/farmers/{farmer.id}/crop-reports/{fake_report_id}/image",
        files=files,
    )
    assert response.status_code == 404
    assert response.json()["detail"] == "Crop report not found"


def test_upload_image_storage_failure_returns_500(farmer, farmer_crop, mock_storage):
    """Test 36: Supabase storage failure → 500 Internal Server Error."""
    create_resp = client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={"farmer_crop_id": str(farmer_crop.id)},
    )
    report_id = create_resp.json()["id"]

    mock_storage.fail_upload = True
    files = {"file": ("leaf.jpg", make_test_image("JPEG"), "image/jpeg")}
    response = client.put(
        f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}/image",
        files=files,
    )
    assert response.status_code == 500
    assert response.json()["detail"] == "Storage service failure"


def test_upload_image_replacement_workflow(farmer, farmer_crop, mock_storage):
    """Test 37: Image replacement uploads new object and cleans up previous storage object."""
    create_resp = client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={"farmer_crop_id": str(farmer_crop.id)},
    )
    report_id = create_resp.json()["id"]

    # 1. First upload (JPEG)
    files1 = {"file": ("first.jpg", make_test_image("JPEG"), "image/jpeg")}
    resp1 = client.put(
        f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}/image",
        files=files1,
    )
    assert resp1.status_code == 200
    path1 = resp1.json()["image_storage_path"]
    assert path1 in mock_storage.uploaded_paths

    # 2. Second upload (PNG) replaces first
    files2 = {"file": ("second.png", make_test_image("PNG"), "image/png")}
    resp2 = client.put(
        f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}/image",
        files=files2,
    )
    assert resp2.status_code == 200
    path2 = resp2.json()["image_storage_path"]
    assert path2 != path1
    assert path2 in mock_storage.uploaded_paths
    # Old path was cleaned up
    assert path1 in mock_storage.deleted_paths


def test_delete_crop_report_cleans_up_storage_image(farmer, farmer_crop, mock_storage):
    """Test 38: Deleting a crop report deletes the associated Supabase storage object."""
    create_resp = client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={"farmer_crop_id": str(farmer_crop.id)},
    )
    report_id = create_resp.json()["id"]

    # Upload image
    files = {"file": ("photo.jpg", make_test_image("JPEG"), "image/jpeg")}
    upload_resp = client.put(
        f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}/image",
        files=files,
    )
    assert upload_resp.status_code == 200
    storage_path = upload_resp.json()["image_storage_path"]

    # Delete crop report
    del_resp = client.delete(f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}")
    assert del_resp.status_code == 204

    # Storage cleanup was called
    assert storage_path in mock_storage.deleted_paths


def test_upload_image_no_secrets_in_response(farmer, farmer_crop):
    """Test 39: API response does not expose service-role keys, tokens, or signed URLs."""
    create_resp = client.post(
        f"/api/v1/farmers/{farmer.id}/crop-reports",
        json={"farmer_crop_id": str(farmer_crop.id)},
    )
    report_id = create_resp.json()["id"]

    files = {"file": ("safe.jpg", make_test_image("JPEG"), "image/jpeg")}
    response = client.put(
        f"/api/v1/farmers/{farmer.id}/crop-reports/{report_id}/image",
        files=files,
    )
    assert response.status_code == 200

    raw_text = response.text.lower()
    assert "service_role" not in raw_text
    assert "supabase_key" not in raw_text
    assert "token=" not in raw_text
    assert "bearer" not in raw_text
    assert "secret" not in raw_text

    # Internal path only, no URL scheme
    storage_path = response.json()["image_storage_path"]
    assert not storage_path.startswith("http://")
    assert not storage_path.startswith("https://")
    assert "?" not in storage_path

