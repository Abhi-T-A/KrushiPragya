"""Focused unit tests for Farmer Crop Management and Crop catalog Pydantic schemas."""
from datetime import datetime, timezone
from decimal import Decimal
import uuid
import pytest
from pydantic import ValidationError

from app.schemas.farmer_crop import (
    CropResponse,
    FarmerCropCreate,
    FarmerCropResponse,
    FarmerCropUpdate,
    FarmerCropWithDetailsResponse,
)


class MockCrop:
    """Mock representing an SQLAlchemy Crop ORM instance."""

    def __init__(
        self,
        id: uuid.UUID,
        code: str = "arecanut",
        name_en: str = "Arecanut",
        name_kn: str = "ಅಡಿಕೆ",
        is_active: bool = True,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
    ):
        self.id = id
        self.code = code
        self.name_en = name_en
        self.name_kn = name_kn
        self.is_active = is_active
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)


class MockFarmerCrop:
    """Mock representing an SQLAlchemy FarmerCrop ORM instance."""

    def __init__(
        self,
        id: uuid.UUID,
        farmer_id: uuid.UUID,
        crop_id: uuid.UUID,
        area_acres: Decimal | None = None,
        is_primary: bool = False,
        created_at: datetime | None = None,
        updated_at: datetime | None = None,
        crop: MockCrop | None = None,
    ):
        self.id = id
        self.farmer_id = farmer_id
        self.crop_id = crop_id
        self.area_acres = area_acres
        self.is_primary = is_primary
        self.created_at = created_at or datetime.now(timezone.utc)
        self.updated_at = updated_at or datetime.now(timezone.utc)
        self.crop = crop


# ==============================================================================
# 1. CropResponse Tests
# ==============================================================================

def test_crop_response_accepts_valid_orm_style_data():
    """Test 1: CropResponse accepts and serializes valid ORM-style data."""
    crop_id = uuid.uuid4()
    now = datetime.now(timezone.utc)
    mock_crop = MockCrop(
        id=crop_id,
        code="paddy",
        name_en="Paddy",
        name_kn="ಭತ್ತ",
        is_active=True,
        created_at=now,
        updated_at=now,
    )

    response = CropResponse.model_validate(mock_crop)

    assert response.id == crop_id
    assert response.code == "paddy"
    assert response.name_en == "Paddy"
    assert response.name_kn == "ಭತ್ತ"
    assert response.is_active is True
    assert response.created_at == now
    assert response.updated_at == now


# ==============================================================================
# 2. FarmerCropCreate Tests
# ==============================================================================

def test_farmer_crop_create_accepts_valid_crop_id():
    """Test 2: FarmerCropCreate accepts a valid crop_id."""
    crop_id = uuid.uuid4()
    schema = FarmerCropCreate(crop_id=crop_id)

    assert schema.crop_id == crop_id
    assert schema.area_acres is None
    assert schema.is_primary is False


def test_farmer_crop_create_accepts_area_acres():
    """Test 3: FarmerCropCreate accepts valid acreage as Decimal."""
    crop_id = uuid.uuid4()
    schema = FarmerCropCreate(
        crop_id=crop_id,
        area_acres=Decimal("4.50"),
        is_primary=True,
    )

    assert schema.crop_id == crop_id
    assert schema.area_acres == Decimal("4.50")
    assert schema.is_primary is True


def test_farmer_crop_create_defaults_is_primary_to_false():
    """Test 4: FarmerCropCreate defaults is_primary to False."""
    schema = FarmerCropCreate(crop_id=uuid.uuid4())
    assert schema.is_primary is False


def test_farmer_crop_create_rejects_negative_area_acres():
    """Test 5: FarmerCropCreate rejects negative area_acres."""
    with pytest.raises(ValidationError) as exc_info:
        FarmerCropCreate(
            crop_id=uuid.uuid4(),
            area_acres=Decimal("-0.01"),
        )
    assert "area_acres" in str(exc_info.value)


def test_farmer_crop_create_does_not_contain_farmer_id():
    """Test 6: FarmerCropCreate does not contain farmer_id field."""
    assert "farmer_id" not in FarmerCropCreate.model_fields


def test_farmer_crop_create_does_not_contain_id():
    """Test 7: FarmerCropCreate does not contain primary key id field."""
    assert "id" not in FarmerCropCreate.model_fields


# ==============================================================================
# 3. FarmerCropUpdate Tests
# ==============================================================================

def test_farmer_crop_update_allows_partial_update():
    """Test 8: FarmerCropUpdate allows partial updates where all fields are optional."""
    # Completely empty update
    empty_update = FarmerCropUpdate()
    assert empty_update.area_acres is None
    assert empty_update.is_primary is None

    # Partial update with only is_primary
    primary_update = FarmerCropUpdate(is_primary=True)
    assert primary_update.is_primary is True
    assert primary_update.area_acres is None
    assert primary_update.model_dump(exclude_unset=True) == {"is_primary": True}


def test_farmer_crop_update_allows_only_area_acres_and_is_primary():
    """Test 9: FarmerCropUpdate defines only area_acres and is_primary mutable fields."""
    expected_fields = {"area_acres", "is_primary"}
    assert set(FarmerCropUpdate.model_fields.keys()) == expected_fields


def test_farmer_crop_update_rejects_negative_area_acres():
    """Test 10: FarmerCropUpdate rejects negative area_acres."""
    with pytest.raises(ValidationError) as exc_info:
        FarmerCropUpdate(area_acres=Decimal("-1.50"))
    assert "area_acres" in str(exc_info.value)


def test_farmer_crop_update_does_not_allow_crop_id():
    """Test 11: FarmerCropUpdate does not allow modifying crop_id."""
    assert "crop_id" not in FarmerCropUpdate.model_fields


# ==============================================================================
# 4. FarmerCropResponse & WithDetails Tests
# ==============================================================================

def test_farmer_crop_response_serializes_orm_style_data():
    """Test 12: FarmerCropResponse serializes ORM-style data."""
    fc_id = uuid.uuid4()
    farmer_id = uuid.uuid4()
    crop_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_fc = MockFarmerCrop(
        id=fc_id,
        farmer_id=farmer_id,
        crop_id=crop_id,
        area_acres=Decimal("8.75"),
        is_primary=True,
        created_at=now,
        updated_at=now,
    )

    response = FarmerCropResponse.model_validate(mock_fc)

    assert response.id == fc_id
    assert response.farmer_id == farmer_id
    assert response.crop_id == crop_id
    assert response.area_acres == Decimal("8.75")
    assert response.is_primary is True
    assert response.created_at == now
    assert response.updated_at == now


def test_farmer_crop_with_details_response_serializes_nested_crop():
    """Test 13: FarmerCropWithDetailsResponse serializes nested CropResponse."""
    fc_id = uuid.uuid4()
    farmer_id = uuid.uuid4()
    crop_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    mock_crop = MockCrop(
        id=crop_id,
        code="coconut",
        name_en="Coconut",
        name_kn="ತೆಂಗು",
        is_active=True,
        created_at=now,
        updated_at=now,
    )
    mock_fc = MockFarmerCrop(
        id=fc_id,
        farmer_id=farmer_id,
        crop_id=crop_id,
        area_acres=Decimal("20.00"),
        is_primary=False,
        created_at=now,
        updated_at=now,
        crop=mock_crop,
    )

    response = FarmerCropWithDetailsResponse.model_validate(mock_fc)

    assert response.id == fc_id
    assert response.crop.id == crop_id
    assert response.crop.code == "coconut"
    assert response.crop.name_en == "Coconut"
    assert response.crop.name_kn == "ತೆಂಗು"
    assert response.crop.is_active is True


def test_decimal_acreage_remains_decimal():
    """Test 14: Decimal acreage remains Decimal rather than being converted to float."""
    crop_id = uuid.uuid4()
    input_acreage = Decimal("14.50")
    create_schema = FarmerCropCreate(crop_id=crop_id, area_acres=input_acreage)

    assert isinstance(create_schema.area_acres, Decimal)
    assert create_schema.area_acres == input_acreage

    update_schema = FarmerCropUpdate(area_acres=input_acreage)
    assert isinstance(update_schema.area_acres, Decimal)
    assert update_schema.area_acres == input_acreage

    mock_fc = MockFarmerCrop(
        id=uuid.uuid4(),
        farmer_id=uuid.uuid4(),
        crop_id=crop_id,
        area_acres=input_acreage,
    )
    resp = FarmerCropResponse.model_validate(mock_fc)
    assert isinstance(resp.area_acres, Decimal)
    assert resp.area_acres == input_acreage
