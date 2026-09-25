"""Comprehensive tests for AI Input Verification Layer and Disease Inference Pipeline.

Validates the multi-stage defense gate:
1. File validation (magic bytes, size, format)
2. Image decode & dimension sanity (min 128x128, aspect ratio)
3. Image quality validation (blur variance, brightness, exposure)
4. Crop/leaf relevance validation (foliage coverage, non-leaf rejection)
5. Confidence gate (50% application threshold, predicted_class=None for low confidence)
6. Curated Disease Knowledge Base lookup (ICAR protocols, Kannada & English)
7. End-to-end API behavior on /api/v1/disease/predict and /api/ai/predict
"""
import io
import math
from unittest.mock import patch
import pytest
from fastapi.testclient import TestClient
from PIL import Image, ImageDraw, ImageFilter
import torch

from app.main import app
from app.services.disease_detection_service import (
    DiseaseDetectionService,
    ModelUnavailableError,
    SUPPORTED_CROPS,
    VerificationRejectionError,
)
from app.services.disease_kb import (
    DISEASE_KNOWLEDGE_BASE,
    get_disease_info,
)
from app.services.input_verification_service import (
    InputVerificationService,
    VerificationResult,
)

client = TestClient(app)


# ==============================================================================
# Deterministic Image Generators for Test Suite
# ==============================================================================

def make_textured_leaf_bytes(
    size: tuple[int, int] = (256, 256),
    healthy: bool = True,
    rotation: int = 0,
    format: str = "JPEG",
) -> bytes:
    """Generate realistic synthetic leaf image bytes with natural texture and veins."""
    img = Image.new("RGB", size, (30, 80, 30))
    draw = ImageDraw.Draw(img)
    w_mid = size[0] - 60
    cy = size[1] // 2

    # Draw leaf blade
    for x in range(30, size[0] - 30):
        w = int(45 * math.sin((x - 30) / max(1, w_mid) * math.pi))
        draw.line([(x, cy - w), (x, cy + w)], fill=(45, 155, 55))
        # Vein texture
        if x % 8 == 0:
            draw.line([(x, cy), (x + 8, cy - w + 5)], fill=(65, 185, 75), width=2)
            draw.line([(x, cy), (x + 8, cy + w - 5)], fill=(65, 185, 75), width=2)

    # Midrib
    draw.line([(30, cy), (size[0] - 30, cy)], fill=(80, 200, 90), width=3)

    if not healthy:
        # Yellow chlorotic halos and brown necrotic lesions
        draw.ellipse([size[0]//2 - 16, cy - 16, size[0]//2 + 16, cy + 16], fill=(160, 115, 35))
        draw.ellipse([size[0]//2 - 8, cy - 8, size[0]//2 + 8, cy + 8], fill=(70, 40, 15))

    if rotation != 0:
        img = img.rotate(rotation, expand=False, fillcolor=(30, 80, 30))

    buf = io.BytesIO()
    img.save(buf, format=format, quality=90)
    return buf.getvalue()


def make_blurry_image_bytes(radius: float = 18.0) -> bytes:
    """Generate heavily blurred leaf image bytes that fail sharpness checks."""
    raw = make_textured_leaf_bytes()
    img = Image.open(io.BytesIO(raw)).filter(ImageFilter.GaussianBlur(radius=radius))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_slightly_blurry_image_bytes(radius: float = 0.5) -> bytes:
    """Generate slightly blurred leaf that still retains sufficient vein sharpness."""
    raw = make_textured_leaf_bytes()
    img = Image.open(io.BytesIO(raw)).filter(ImageFilter.GaussianBlur(radius=radius))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_partial_leaf_bytes() -> bytes:
    """Generate image with leaf occupying ~35% of frame on neutral surface."""
    img = Image.new("RGB", (256, 256), (120, 120, 120))
    draw = ImageDraw.Draw(img)
    draw.polygon([(0, 0), (150, 0), (170, 130), (0, 190)], fill=(45, 140, 50))
    draw.line([(0, 0), (150, 110)], fill=(70, 185, 75), width=3)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_wall_image_bytes() -> bytes:
    """Generate an indoor cream/beige wall image (no foliar tissue)."""
    img = Image.new("RGB", (256, 256), (225, 218, 205))
    draw = ImageDraw.Draw(img)
    for y in range(0, 256, 16):
        draw.line([(0, y), (256, y)], fill=(220, 212, 198), width=1)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_sky_image_bytes() -> bytes:
    """Generate a blue sky image with clouds (no foliar tissue)."""
    img = Image.new("RGB", (256, 256), (110, 175, 235))
    draw = ImageDraw.Draw(img)
    draw.ellipse([50, 50, 200, 100], fill=(230, 240, 255))
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_desk_image_bytes() -> bytes:
    """Generate a wooden desk surface (no foliar tissue)."""
    img = Image.new("RGB", (256, 256), (135, 75, 35))
    draw = ImageDraw.Draw(img)
    for x in range(0, 256, 20):
        draw.line([(x, 0), (x, 256)], fill=(120, 65, 30), width=2)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


def make_solid_color_bytes(color: tuple[int, int, int], size: tuple[int, int] = (256, 256)) -> bytes:
    """Generate a flat, uniform solid color image."""
    img = Image.new("RGB", size, color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ==============================================================================
# 1. Unit Tests: InputVerificationService Defense Gate
# ==============================================================================

class TestInputVerificationService:
    """Direct tests for the InputVerificationService defense algorithms."""

    @pytest.fixture(autouse=True)
    def setup(self):
        self.verifier = InputVerificationService()

    def test_clear_healthy_leaf_verified(self):
        data = make_textured_leaf_bytes(healthy=True)
        res = self.verifier.verify(crop="paddy", image_bytes=data)
        assert res.is_valid is True
        assert res.status == "success"
        assert res.reason_code is None
        assert res.metrics["foliage_fraction"] > 0.08
        assert res.metrics["laplacian_variance"] >= 12.0

    def test_clear_diseased_leaf_verified(self):
        data = make_textured_leaf_bytes(healthy=False)
        res = self.verifier.verify(crop="arecanut", image_bytes=data)
        assert res.is_valid is True
        assert res.status == "success"
        assert res.reason_code is None

    @pytest.mark.parametrize("angle", [45, 90, 180, 270])
    def test_rotated_leaves_not_automatically_rejected(self, angle: int):
        data = make_textured_leaf_bytes(rotation=angle)
        res = self.verifier.verify(crop="coconut", image_bytes=data)
        assert res.is_valid is True
        assert res.status == "success"
        assert res.reason_code is None

    def test_partial_leaf_accepted(self):
        data = make_partial_leaf_bytes()
        res = self.verifier.verify(crop="black_pepper", image_bytes=data)
        assert res.is_valid is True
        assert res.status == "success"
        assert res.reason_code is None

    def test_slightly_blurry_leaf_accepted(self):
        data = make_slightly_blurry_image_bytes(radius=0.5)
        res = self.verifier.verify(crop="turmeric", image_bytes=data)
        assert res.is_valid is True
        assert res.status == "success"

    def test_heavily_blurry_image_rejected(self):
        data = make_blurry_image_bytes(radius=18.0)
        res = self.verifier.verify(crop="cardamom", image_bytes=data)
        assert res.is_valid is False
        assert res.status == "rejected"
        assert res.reason_code == "IMAGE_TOO_BLURRY"
        assert "blurry" in res.message.lower()

    def test_dark_image_rejected(self):
        data = make_solid_color_bytes((10, 12, 9))
        res = self.verifier.verify(crop="ginger", image_bytes=data)
        assert res.is_valid is False
        assert res.status == "rejected"
        assert res.reason_code == "IMAGE_TOO_DARK"

    def test_overexposed_image_rejected(self):
        data = make_solid_color_bytes((248, 250, 248))
        res = self.verifier.verify(crop="paddy", image_bytes=data)
        assert res.is_valid is False
        assert res.status == "rejected"
        assert res.reason_code in ("IMAGE_OVEREXPOSED", "IRRELEVANT_IMAGE")

    def test_blank_white_image_rejected(self):
        data = make_solid_color_bytes((255, 255, 255))
        res = self.verifier.verify(crop="paddy", image_bytes=data)
        assert res.is_valid is False
        assert res.status == "rejected"
        assert res.reason_code in ("IRRELEVANT_IMAGE", "IMAGE_OVEREXPOSED")
        assert "leaf" in res.message.lower() or "white" in res.message.lower()

    def test_blank_black_image_rejected(self):
        data = make_solid_color_bytes((0, 0, 0))
        res = self.verifier.verify(crop="paddy", image_bytes=data)
        assert res.is_valid is False
        assert res.status == "rejected"
        assert res.reason_code == "IMAGE_TOO_DARK"

    def test_wall_background_rejected(self):
        data = make_wall_image_bytes()
        res = self.verifier.verify(crop="arecanut", image_bytes=data)
        assert res.is_valid is False
        assert res.status == "rejected"
        assert res.reason_code == "IRRELEVANT_IMAGE"

    def test_sky_background_rejected(self):
        data = make_sky_image_bytes()
        res = self.verifier.verify(crop="coconut", image_bytes=data)
        assert res.is_valid is False
        assert res.status == "rejected"
        assert res.reason_code == "IRRELEVANT_IMAGE"

    def test_desk_surface_rejected(self):
        data = make_desk_image_bytes()
        res = self.verifier.verify(crop="black_pepper", image_bytes=data)
        assert res.is_valid is False
        assert res.status == "rejected"
        assert res.reason_code == "IRRELEVANT_IMAGE"

    def test_small_image_rejected(self):
        data = make_textured_leaf_bytes(size=(64, 64))
        res = self.verifier.verify(crop="ginger", image_bytes=data)
        assert res.is_valid is False
        assert res.status == "rejected"
        assert res.reason_code == "IMAGE_TOO_SMALL"
        assert "resolution" in res.message.lower()

    def test_corrupted_image_bytes_rejected(self):
        corrupt = b"\xff\xd8\xff\xe0CORRUPT_BYTES_DATA_9876543210"
        res = self.verifier.verify(crop="turmeric", image_bytes=corrupt)
        assert res.is_valid is False
        assert res.status == "rejected"
        assert res.reason_code == "INVALID_IMAGE"

    def test_unsupported_file_rejected(self):
        pdf_bytes = b"%PDF-1.5 %This is not a photo file"
        res = self.verifier.verify(crop="cardamom", image_bytes=pdf_bytes)
        assert res.is_valid is False
        assert res.status == "rejected"
        assert res.reason_code == "INVALID_IMAGE"


# ==============================================================================
# 2. Disease Knowledge Base Curated Content Tests
# ==============================================================================

class TestDiseaseKnowledgeBase:
    """Validate ICAR disease guidance lookup and fallback behaviors."""

    def test_all_supported_crops_have_kb_entries(self):
        service = DiseaseDetectionService()
        for crop, spec in SUPPORTED_CROPS.items():
            _, classes = service.get_or_load_model(crop)
            for cls_name in classes:
                info = get_disease_info(crop, cls_name)
                assert info is not None, f"Missing KB entry for {crop} -> {cls_name}"
                assert info.disease_name_en != ""
                assert info.disease_name_kn != ""
                assert info.remedy_en != ""
                assert info.cultural_control != ""

    def test_healthy_classes_return_good_agricultural_practices(self):
        # Crops that have explicit healthy classes in their models
        crops_with_healthy = ["arecanut", "cardamom", "turmeric", "ginger"]
        for crop in crops_with_healthy:
            info = get_disease_info(crop, "Healthy")
            assert info is not None, f"Expected healthy info for {crop}"
            assert info.category == "HEALTHY"
            assert "ಆರೋಗ್ಯಕರ" in info.disease_name_kn or "Healthy" in info.disease_name_en
            assert len(info.remedy_en) > 10
            assert len(info.remedy_kn) > 10

    def test_unknown_class_returns_none(self):
        info = get_disease_info("paddy", "Unknown_Alien_Disease")
        assert info is None


# ==============================================================================
# 3. Model Preloading at Startup
# ==============================================================================

def test_preload_all_models_populates_cache():
    """Verify that preload_all_models caches all 7 models without runtime exceptions."""
    service = DiseaseDetectionService()
    service.preload_all_models()
    for crop, spec in SUPPORTED_CROPS.items():
        assert crop in service._models
        model, classes = service._models[crop]
        assert model is not None
        assert len(classes) == spec.expected_num_classes


# ==============================================================================
# 4. Crop Mismatch Gate Unit Test
# ==============================================================================

def test_crop_mismatch_detection():
    """Verify crop mismatch heuristic flags significant cross-model discrepancy."""
    verifier = InputVerificationService()
    is_ok, reason, msg = verifier.evaluate_crop_mismatch(
        requested_crop="paddy",
        cross_predictions={"paddy": 0.15, "arecanut": 0.92},
    )
    assert is_ok is False
    assert reason == "CROP_MISMATCH"
    assert "paddy" in msg.lower()

    # When confidence is similar or uncertain, do not falsely reject
    is_ok_plausible, _, _ = verifier.evaluate_crop_mismatch(
        requested_crop="paddy",
        cross_predictions={"paddy": 0.45, "arecanut": 0.48},
    )
    assert is_ok_plausible is True


# ==============================================================================
# 5. API Endpoint Integration Tests (/api/v1/disease/predict & /api/ai/predict)
# ==============================================================================

class TestDiseasePredictionAPI:
    """Test full HTTP API behavior for both endpoints."""

    @pytest.mark.parametrize("endpoint", ["/api/v1/disease/predict", "/api/ai/predict"])
    def test_valid_leaf_upload_succeeds(self, endpoint: str):
        image_bytes = make_textured_leaf_bytes(healthy=True)
        response = client.post(
            endpoint,
            data={"crop": "paddy"},
            files={"file": ("leaf.jpg", image_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["status"] in ("success", "uncertain")
        assert data["input_verified"] is True
        assert data["crop"] == "paddy"
        assert data["model_version"] == "paddy-v1"
        assert "confidence" in data
        assert len(data["top_predictions"]) > 0

        # If confident, verify disease_info is attached
        if data["status"] == "success":
            assert data["predicted_class"] is not None
            assert data["disease_info"] is not None
            assert "disease_name_kn" in data["disease_info"]

    def test_support_both_file_and_image_form_field(self):
        image_bytes = make_textured_leaf_bytes(healthy=True)
        response = client.post(
            "/api/ai/predict",
            data={"crop": "arecanut"},
            files={"image": ("areca.jpg", image_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["crop"] == "arecanut"
        assert data["input_verified"] is True

    def test_blank_image_rejected_without_reaching_classifier(self):
        blank_bytes = make_solid_color_bytes((255, 255, 255))
        response = client.post(
            "/api/v1/disease/predict",
            data={"crop": "paddy"},
            files={"file": ("blank.jpg", blank_bytes, "image/jpeg")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "rejected"
        assert data["reason_code"] in ("IRRELEVANT_IMAGE", "IMAGE_OVEREXPOSED")
        assert data["input_verified"] is False
        assert "leaf" in data["message"].lower() or "photo" in data["message"].lower()

    def test_wall_image_rejected(self):
        wall_bytes = make_wall_image_bytes()
        response = client.post(
            "/api/ai/predict",
            data={"crop": "paddy"},
            files={"file": ("wall.jpg", wall_bytes, "image/jpeg")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "rejected"
        assert data["reason_code"] == "IRRELEVANT_IMAGE"
        assert data["input_verified"] is False

    def test_desk_image_rejected(self):
        desk_bytes = make_desk_image_bytes()
        response = client.post(
            "/api/ai/predict",
            data={"crop": "coconut"},
            files={"file": ("desk.jpg", desk_bytes, "image/jpeg")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "rejected"
        assert data["reason_code"] == "IRRELEVANT_IMAGE"

    def test_corrupted_image_rejected(self):
        corrupt = b"\xff\xd8\xff\xe0NOT_AN_IMAGE_CONTENT"
        response = client.post(
            "/api/v1/disease/predict",
            data={"crop": "turmeric"},
            files={"file": ("corrupt.jpg", corrupt, "image/jpeg")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "rejected"
        assert data["reason_code"] == "INVALID_IMAGE"

    def test_small_image_rejected(self):
        small = make_textured_leaf_bytes(size=(64, 64))
        response = client.post(
            "/api/v1/disease/predict",
            data={"crop": "ginger"},
            files={"file": ("small.jpg", small, "image/jpeg")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "rejected"
        assert data["reason_code"] == "IMAGE_TOO_SMALL"

    def test_blurry_image_rejected(self):
        blurry = make_blurry_image_bytes(radius=18.0)
        response = client.post(
            "/api/v1/disease/predict",
            data={"crop": "cardamom"},
            files={"file": ("blur.jpg", blurry, "image/jpeg")},
        )
        assert response.status_code == 400
        data = response.json()
        assert data["status"] == "rejected"
        assert data["reason_code"] == "IMAGE_TOO_BLURRY"

    def test_confidence_gate_withholds_disease_when_low_confidence(self):
        """When model confidence is <0.50, API must return uncertain status and null predicted_class."""
        from unittest.mock import MagicMock
        image_bytes = make_textured_leaf_bytes(healthy=True)

        mock_model = MagicMock()
        mock_model.return_value = torch.tensor([[1.0, 1.1, 0.9, 1.05]])
        with patch.object(
            DiseaseDetectionService,
            "get_or_load_model",
            return_value=(mock_model, ["Blast", "Bacterial_Leaf_Blight", "Brown_Plant_Hopper", "Sheath_Blight"]),
        ):
            response = client.post(
                "/api/v1/disease/predict",
                data={"crop": "paddy"},
                files={"file": ("leaf.jpg", image_bytes, "image/jpeg")},
            )
            assert response.status_code == 200
            data = response.json()
            assert data["status"] == "uncertain"
            assert data["low_confidence"] is True
            assert data["predicted_class"] is None
            assert data["confidence"] < 0.50
            assert "could not be confidently identified" in data["message"].lower()

    def test_model_unavailable_returns_503(self):
        """When a requested crop model fails to load, API must return HTTP 503 with MODEL_UNAVAILABLE."""
        image_bytes = make_textured_leaf_bytes(healthy=True)
        with patch.object(
            DiseaseDetectionService,
            "get_or_load_model",
            side_effect=ModelUnavailableError("Model weights corrupted or not found on disk."),
        ):
            response = client.post(
                "/api/v1/disease/predict",
                data={"crop": "paddy"},
                files={"file": ("leaf.jpg", image_bytes, "image/jpeg")},
            )
            assert response.status_code == 503
            data = response.json()
            assert data["status"] == "rejected"
            assert data["reason_code"] == "MODEL_UNAVAILABLE"
            assert data["input_verified"] is False
