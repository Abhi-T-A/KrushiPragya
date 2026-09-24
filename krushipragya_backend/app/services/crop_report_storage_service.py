"""Storage service for Crop Report images using Supabase Storage REST API."""
import io
import logging
from pathlib import Path
from typing import Optional
import uuid

import httpx
from PIL import Image, UnidentifiedImageError

from app.core.config import settings

logger = logging.getLogger(__name__)

# Constants
MAX_IMAGE_SIZE_BYTES = 10 * 1024 * 1024  # 10 MB

SUPPORTED_MIME_TYPES = {
    "image/jpeg": ".jpg",
    "image/jpg": ".jpg",
    "image/png": ".png",
    "image/webp": ".webp",
}


# ==============================================================================
# Storage Exceptions
# ==============================================================================

class StorageError(Exception):
    """Base exception for storage operations."""
    pass


CropReportStorageError = StorageError



class UnsupportedImageTypeError(StorageError):
    """Raised when an unsupported image MIME type is provided."""
    pass


class InvalidImageError(StorageError):
    """Raised when the image file cannot be parsed or verified."""
    pass


class ImageSizeLimitExceededError(StorageError):
    """Raised when the uploaded image exceeds the maximum size limit."""
    pass


class StorageServiceError(StorageError):
    """Raised when the underlying storage infrastructure fails."""
    pass


# ==============================================================================
# Service Implementation
# ==============================================================================

class CropReportStorageService:
    """Service managing image validation, path generation, upload, and deletion in Supabase Storage."""

    def __init__(
        self,
        base_url: Optional[str] = None,
        service_role_key: Optional[str] = None,
        bucket: Optional[str] = None,
        client: Optional[httpx.Client] = None,
    ):
        self.base_url = (base_url or settings.SUPABASE_URL or "").rstrip("/")
        self.service_role_key = service_role_key or settings.SUPABASE_SERVICE_ROLE_KEY or ""
        self.bucket = bucket or settings.SUPABASE_CROP_REPORT_BUCKET or "crop-report-images"
        self._client = client

    @property
    def client(self) -> httpx.Client:
        """Return HTTP client instance."""
        if self._client is None:
            self._client = httpx.Client(timeout=30.0)
        return self._client

    def validate_image(self, content: bytes, content_type: str) -> str:
        """Validate image MIME type, payload size, and raster format integrity.

        Args:
            content: Raw byte content of the image
            content_type: Declared MIME type of the uploaded file

        Returns:
            str: Normalized MIME type (e.g. 'image/jpeg', 'image/png', 'image/webp')

        Raises:
            UnsupportedImageTypeError: If MIME type is not supported
            ImageSizeLimitExceededError: If content exceeds 10 MB
            InvalidImageError: If payload is empty or cannot be decoded as a valid image
        """
        # 1. Content-Type check
        normalized_mime = content_type.lower().strip()
        if normalized_mime == "image/jpg":
            normalized_mime = "image/jpeg"

        if normalized_mime not in SUPPORTED_MIME_TYPES:
            logger.warning("Unsupported MIME type rejected: %s", content_type)
            raise UnsupportedImageTypeError(
                f"Unsupported image type '{content_type}'. Allowed types: image/jpeg, image/png, image/webp"
            )

        # 2. Size limit check
        if len(content) > MAX_IMAGE_SIZE_BYTES:
            logger.warning(
                "Image size limit exceeded: %d bytes (max %d bytes)",
                len(content),
                MAX_IMAGE_SIZE_BYTES,
            )
            raise ImageSizeLimitExceededError(
                f"Image size exceeds maximum limit of 10 MB ({len(content)} bytes uploaded)."
            )

        if len(content) == 0:
            logger.warning("Empty image payload rejected")
            raise InvalidImageError("Image payload cannot be empty.")

        # 3. Raster format verification using Pillow
        try:
            img = Image.open(io.BytesIO(content))
            img.verify()
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            logger.warning("Corrupted or invalid image data: %s", exc)
            raise InvalidImageError(f"Cannot identify or decode image payload: {exc}") from exc

        return normalized_mime

    def generate_storage_path(
        self,
        farmer_id: uuid.UUID,
        report_id: uuid.UUID,
        content_type: str,
    ) -> str:
        """Generate a safe, server-side storage object key.

        Structure:
            farmers/{farmer_id}/crop-reports/{report_id}/{random_uuid}{ext}

        Args:
            farmer_id: UUID of the owning farmer
            report_id: UUID of the crop report
            content_type: Validated MIME type

        Returns:
            str: Safe internal storage path
        """
        normalized_mime = content_type.lower().strip()
        if normalized_mime == "image/jpg":
            normalized_mime = "image/jpeg"

        extension = SUPPORTED_MIME_TYPES.get(normalized_mime, ".jpg")
        random_filename = f"{uuid.uuid4()}{extension}"
        return f"farmers/{farmer_id}/crop-reports/{report_id}/{random_filename}"

    def upload_image(
        self,
        storage_path: str,
        content: bytes,
        content_type: str,
    ) -> str:
        """Upload raw image bytes to Supabase Storage at the specified storage path.

        Args:
            storage_path: Internal object key generated by generate_storage_path
            content: Raw image bytes
            content_type: Content-Type header value

        Returns:
            str: The persisted storage path reference

        Raises:
            StorageServiceError: If upload request fails
        """
        if not self.base_url or not self.service_role_key:
            logger.warning("Supabase storage credentials not fully configured")

        url = f"{self.base_url}/storage/v1/object/{self.bucket}/{storage_path}"
        headers = {
            "Authorization": f"Bearer {self.service_role_key}",
            "apiKey": self.service_role_key,
            "Content-Type": content_type,
            "x-upsert": "true",
        }

        try:
            response = self.client.post(url, headers=headers, content=content)
            if response.status_code not in (200, 201):
                logger.error(
                    "Storage upload failed for %s with status %d: %s",
                    storage_path,
                    response.status_code,
                    response.text,
                )
                raise StorageServiceError(
                    f"Storage upload failed with HTTP status {response.status_code}"
                )
            logger.info("Successfully uploaded image to storage path: %s", storage_path)
            return storage_path
        except httpx.HTTPError as exc:
            logger.error("HTTP network failure during storage upload: %s", exc)
            raise StorageServiceError(f"HTTP network failure during storage upload: {exc}") from exc

    def delete_image(self, storage_path: str) -> bool:
        """Delete an image object from Supabase Storage.

        Args:
            storage_path: Internal object key to delete

        Returns:
            bool: True if deletion succeeded or object was not found, False otherwise
        """
        if not storage_path:
            return True

        url = f"{self.base_url}/storage/v1/object/{self.bucket}/{storage_path}"
        headers = {
            "Authorization": f"Bearer {self.service_role_key}",
            "apiKey": self.service_role_key,
        }

        try:
            response = self.client.delete(url, headers=headers)
            if response.status_code in (200, 204):
                logger.info("Successfully deleted storage object: %s", storage_path)
                return True
            logger.warning(
                "Storage delete for %s returned status %d: %s",
                storage_path,
                response.status_code,
                response.text,
            )
            return False
        except httpx.HTTPError as exc:
            logger.warning("HTTP network failure during storage deletion: %s", exc)
            return False

    def download_image(self, storage_path: str) -> bytes:
        """Download raw image bytes from Supabase Storage for a given storage path.

        Args:
            storage_path: Internal object key in Supabase storage

        Returns:
            bytes: Raw binary content of the stored image

        Raises:
            StorageServiceError: If download fails or image is not found
        """
        if not storage_path:
            raise StorageServiceError("Storage path cannot be empty.")

        url = f"{self.base_url}/storage/v1/object/{self.bucket}/{storage_path}"
        headers = {
            "Authorization": f"Bearer {self.service_role_key}",
            "apiKey": self.service_role_key,
        }

        try:
            response = self.client.get(url, headers=headers)
            if response.status_code != 200:
                logger.error(
                    "Storage download failed for %s with status %d: %s",
                    storage_path,
                    response.status_code,
                    response.text,
                )
                raise StorageServiceError(
                    f"Storage download failed with HTTP status {response.status_code}"
                )
            logger.info("Successfully downloaded image from storage path: %s", storage_path)
            return response.content
        except httpx.HTTPError as exc:
            logger.error("HTTP network failure during storage download: %s", exc)
            raise StorageServiceError(f"HTTP network failure during storage download: {exc}") from exc



def get_crop_report_storage_service() -> CropReportStorageService:
    """Dependency provider / singleton factory for CropReportStorageService."""
    return CropReportStorageService()
