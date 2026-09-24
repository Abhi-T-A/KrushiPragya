"""Unit tests for CropReportStorageService."""
import io
from unittest.mock import MagicMock
import uuid
import httpx
from PIL import Image
import pytest

from app.services.crop_report_storage_service import (
    CropReportStorageService,
    ImageSizeLimitExceededError,
    InvalidImageError,
    MAX_IMAGE_SIZE_BYTES,
    StorageServiceError,
    UnsupportedImageTypeError,
)


def make_test_image(format_name: str) -> bytes:
    """Create a minimal valid raster image in memory."""
    img = Image.new("RGB", (16, 16), color="green")
    buf = io.BytesIO()
    img.save(buf, format=format_name)
    return buf.getvalue()


@pytest.fixture
def mock_httpx_client():
    """Mock httpx.Client for isolated storage tests."""
    return MagicMock(spec=httpx.Client)


@pytest.fixture
def storage_service(mock_httpx_client):
    """Fixture providing CropReportStorageService with mocked HTTP client."""
    return CropReportStorageService(
        base_url="https://test-project.supabase.co",
        service_role_key="test-secret-service-role-key-999",
        bucket="crop-report-images",
        client=mock_httpx_client,
    )


# ==============================================================================
# MIME Type & Validation Tests
# ==============================================================================

def test_jpeg_accepted(storage_service):
    """Test 1: JPEG accepted."""
    jpeg_bytes = make_test_image("JPEG")
    res = storage_service.validate_image(jpeg_bytes, "image/jpeg")
    assert res == "image/jpeg"

    # Also accept image/jpg normalized to image/jpeg
    res_jpg = storage_service.validate_image(jpeg_bytes, "image/jpg")
    assert res_jpg == "image/jpeg"


def test_png_accepted(storage_service):
    """Test 2: PNG accepted."""
    png_bytes = make_test_image("PNG")
    res = storage_service.validate_image(png_bytes, "image/png")
    assert res == "image/png"


def test_webp_accepted(storage_service):
    """Test 3: WebP accepted."""
    webp_bytes = make_test_image("WEBP")
    res = storage_service.validate_image(webp_bytes, "image/webp")
    assert res == "image/webp"


def test_unsupported_mime_type_rejected(storage_service):
    """Test 4: Unsupported MIME type rejected."""
    pdf_bytes = b"%PDF-1.4 sample content"
    with pytest.raises(UnsupportedImageTypeError):
        storage_service.validate_image(pdf_bytes, "application/pdf")

    text_bytes = b"Hello world text file"
    with pytest.raises(UnsupportedImageTypeError):
        storage_service.validate_image(text_bytes, "text/plain")

    with pytest.raises(UnsupportedImageTypeError):
        storage_service.validate_image(b"dummy", "image/gif")


def test_file_over_10mb_rejected(storage_service):
    """Test 5: File >10 MB rejected."""
    oversized_bytes = b"X" * (MAX_IMAGE_SIZE_BYTES + 1)
    with pytest.raises(ImageSizeLimitExceededError):
        storage_service.validate_image(oversized_bytes, "image/jpeg")


def test_empty_or_corrupted_image_rejected(storage_service):
    """Test: Empty or corrupted image payload rejected with InvalidImageError."""
    with pytest.raises(InvalidImageError):
        storage_service.validate_image(b"", "image/jpeg")

    corrupted = b"\xFF\xD8\xFF\xE0corrupted data not an actual image"
    with pytest.raises(InvalidImageError):
        storage_service.validate_image(corrupted, "image/jpeg")


# ==============================================================================
# Path Generation & Sanitization Tests
# ==============================================================================

def test_safe_generated_storage_path(storage_service):
    """Test 6: Safe generated storage path matches expected structure."""
    farmer_id = uuid.uuid4()
    report_id = uuid.uuid4()
    path = storage_service.generate_storage_path(farmer_id, report_id, "image/jpeg")

    assert path.startswith(f"farmers/{farmer_id}/crop-reports/{report_id}/")
    assert path.endswith(".jpg")
    parts = path.split("/")
    assert len(parts) == 5
    assert parts[0] == "farmers"
    assert parts[1] == str(farmer_id)
    assert parts[2] == "crop-reports"
    assert parts[3] == str(report_id)


def test_path_contains_farmer_id(storage_service):
    """Test 7: Path contains farmer ID."""
    farmer_id = uuid.uuid4()
    report_id = uuid.uuid4()
    path = storage_service.generate_storage_path(farmer_id, report_id, "image/png")
    assert str(farmer_id) in path


def test_path_contains_report_id(storage_service):
    """Test 8: Path contains report ID."""
    farmer_id = uuid.uuid4()
    report_id = uuid.uuid4()
    path = storage_service.generate_storage_path(farmer_id, report_id, "image/webp")
    assert str(report_id) in path


def test_filename_is_generated_server_side(storage_service):
    """Test 9: Filename is generated server-side as a UUID."""
    farmer_id = uuid.uuid4()
    report_id = uuid.uuid4()
    path1 = storage_service.generate_storage_path(farmer_id, report_id, "image/jpeg")
    path2 = storage_service.generate_storage_path(farmer_id, report_id, "image/jpeg")

    assert path1 != path2
    filename = path1.split("/")[-1]
    name_without_ext = filename.rsplit(".", 1)[0]
    # Verify the generated filename component is a valid UUID
    uuid.UUID(name_without_ext)


def test_client_path_traversal_cannot_affect_storage_path(storage_service):
    """Test 10: Client path traversal cannot affect storage path."""
    farmer_id = uuid.uuid4()
    report_id = uuid.uuid4()
    path = storage_service.generate_storage_path(farmer_id, report_id, "image/jpeg")

    assert ".." not in path
    assert "\\" not in path
    assert "//" not in path
    assert path.count("farmers/") == 1


# ==============================================================================
# Storage Upload & Delete Operations
# ==============================================================================

def test_storage_upload_called_with_correct_bucket(storage_service, mock_httpx_client):
    """Test 11: Storage upload called with correct bucket and headers."""
    mock_resp = MagicMock(status_code=200, text='{"Key": "uploaded"}')
    mock_httpx_client.post.return_value = mock_resp

    farmer_id = uuid.uuid4()
    report_id = uuid.uuid4()
    path = storage_service.generate_storage_path(farmer_id, report_id, "image/jpeg")
    content = make_test_image("JPEG")

    result_path = storage_service.upload_image(path, content, "image/jpeg")

    assert result_path == path
    mock_httpx_client.post.assert_called_once()
    call_args = mock_httpx_client.post.call_args
    url = call_args[0][0]
    headers = call_args[1]["headers"]

    # Verify bucket name is in URL
    assert "crop-report-images" in url
    assert path in url
    # Verify authentication headers
    assert headers["Authorization"] == "Bearer test-secret-service-role-key-999"
    assert headers["apiKey"] == "test-secret-service-role-key-999"
    assert headers["Content-Type"] == "image/jpeg"


def test_upload_failure_becomes_controlled_service_error(storage_service, mock_httpx_client):
    """Test 12: Upload failure becomes a controlled StorageServiceError."""
    # HTTP status 500 from storage server
    mock_resp = MagicMock(status_code=500, text="Internal Server Error")
    mock_httpx_client.post.return_value = mock_resp

    with pytest.raises(StorageServiceError) as exc_info:
        storage_service.upload_image("path/to/test.jpg", b"dummy", "image/jpeg")
    assert "status 500" in str(exc_info.value)

    # Network failure
    mock_httpx_client.post.side_effect = httpx.ConnectError("Connection refused")
    with pytest.raises(StorageServiceError) as exc_info2:
        storage_service.upload_image("path/to/test.jpg", b"dummy", "image/jpeg")
    assert "network failure" in str(exc_info2.value).lower()


def test_storage_delete_called_for_cleanup(storage_service, mock_httpx_client):
    """Test 13: Storage delete called for cleanup."""
    mock_resp = MagicMock(status_code=200, text="Deleted")
    mock_httpx_client.delete.return_value = mock_resp

    path = "farmers/uuid/crop-reports/uuid/img.jpg"
    success = storage_service.delete_image(path)

    assert success is True
    mock_httpx_client.delete.assert_called_once()
    call_url = mock_httpx_client.delete.call_args[0][0]
    assert "crop-report-images" in call_url
    assert path in call_url


# ==============================================================================
# Security & Secret Sanitization Tests
# ==============================================================================

def test_no_service_role_key_in_returned_values(storage_service, mock_httpx_client):
    """Test 14: No service-role key appears in returned values."""
    mock_httpx_client.post.return_value = MagicMock(status_code=200)

    path = storage_service.generate_storage_path(uuid.uuid4(), uuid.uuid4(), "image/jpeg")
    uploaded_path = storage_service.upload_image(path, make_test_image("JPEG"), "image/jpeg")

    secret_key = "test-secret-service-role-key-999"
    assert secret_key not in path
    assert secret_key not in uploaded_path


def test_no_signed_url_is_generated(storage_service):
    """Test 15: No signed URL is generated."""
    path = storage_service.generate_storage_path(uuid.uuid4(), uuid.uuid4(), "image/jpeg")
    assert "token=" not in path
    assert "signature=" not in path
    assert "?" not in path


def test_no_public_url_is_persisted(storage_service):
    """Test 16: No public URL (http:// or https://) is returned or persisted as object path."""
    path = storage_service.generate_storage_path(uuid.uuid4(), uuid.uuid4(), "image/jpeg")
    assert not path.startswith("http://")
    assert not path.startswith("https://")
    assert path.startswith("farmers/")
