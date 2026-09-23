"""Tests for Disease Detection Service and API Endpoint in KrushiPragya."""
import io
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
from PIL import Image
import torch

from app.core.config import settings
from app.main import app
from app.schemas.disease import DiseasePredictionResponse
from app.services.disease_detection_service import (
    DiseaseDetectionService,
    EmptyImageError,
    InvalidImageError,
    SUPPORTED_CROPS,
    UnsupportedCropError,
)

client = TestClient(app)


def create_synthetic_image_bytes(
    size: tuple[int, int] = (256, 256),
    color: tuple[int, int, int] = (80, 160, 90),
    format: str = "JPEG",
) -> bytes:
    """Generate deterministic in-memory synthetic image bytes."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format=format)
    return buf.getvalue()


# ==============================================================================
# 1. Model Files Existence
# ==============================================================================

def test_all_7_model_files_exist():
    """Verify that all 7 model checkpoint files exist in the model directory."""
    model_dir = settings.resolved_disease_model_dir
    assert model_dir.exists(), f"Directory {model_dir} does not exist"

    for crop, spec in SUPPORTED_CROPS.items():
        model_path = model_dir / spec.filename
        assert model_path.exists(), f"Checkpoint for crop '{crop}' missing at {model_path}"
        assert model_path.stat().st_size > 10 * 1024 * 1024, f"Checkpoint file {model_path} is suspiciously small"


# ==============================================================================
# 2. Model Loading & In-Process Caching
# ==============================================================================

def test_all_7_models_load_successfully():
    """Verify each of the 7 models can be loaded into memory on CPU."""
    service = DiseaseDetectionService()
    for crop in SUPPORTED_CROPS:
        model, classes = service.get_or_load_model(crop)
        assert model is not None
        assert isinstance(classes, list)
        assert len(classes) == SUPPORTED_CROPS[crop].expected_num_classes


def test_model_cache_prevents_reloading():
    """Verify that subsequent requests reuse the cached model instance."""
    service = DiseaseDetectionService()
    model1, classes1 = service.get_or_load_model("arecanut")
    model2, classes2 = service.get_or_load_model("arecanut")

    assert model1 is model2, "Model instance was reloaded instead of using cache"
    assert classes1 is classes2


# ==============================================================================
# 3-9. Output Dimensions
# ==============================================================================

def test_arecanut_output_dimension():
    service = DiseaseDetectionService()
    model, _ = service.get_or_load_model("arecanut")
    assert model.classifier[1].out_features == 6


def test_paddy_output_dimension():
    service = DiseaseDetectionService()
    model, _ = service.get_or_load_model("paddy")
    assert model.classifier[1].out_features == 4


def test_coconut_output_dimension():
    service = DiseaseDetectionService()
    model, _ = service.get_or_load_model("coconut")
    assert model.classifier[1].out_features == 5


def test_black_pepper_output_dimension():
    service = DiseaseDetectionService()
    model, _ = service.get_or_load_model("black_pepper")
    assert model.classifier[1].out_features == 3


def test_cardamom_output_dimension():
    service = DiseaseDetectionService()
    model, _ = service.get_or_load_model("cardamom")
    assert model.classifier[1].out_features == 3


def test_turmeric_output_dimension():
    service = DiseaseDetectionService()
    model, _ = service.get_or_load_model("turmeric")
    assert model.classifier[1].out_features == 4


def test_ginger_output_dimension():
    service = DiseaseDetectionService()
    model, _ = service.get_or_load_model("ginger")
    assert model.classifier[1].out_features == 4


# ==============================================================================
# 10-16. Class Mapping Verification
# ==============================================================================

def test_arecanut_class_mapping():
    service = DiseaseDetectionService()
    _, classes = service.get_or_load_model("arecanut")
    expected = [
        "Healthy",
        "Mahali_Koleroga",
        "Stem_bleeding",
        "bud borer",
        "stem cracking",
        "yellow leaf disease",
    ]
    assert classes == expected


def test_paddy_class_mapping():
    service = DiseaseDetectionService()
    _, classes = service.get_or_load_model("paddy")
    expected = [
        "Blast",
        "Bacterial_Leaf_Blight",
        "Brown_Plant_Hopper",
        "Sheath_Blight",
    ]
    assert classes == expected


def test_coconut_class_mapping():
    service = DiseaseDetectionService()
    _, classes = service.get_or_load_model("coconut")
    expected = [
        "Bud Root Dropping",
        "Bud Rot",
        "Gray Leaf Spot",
        "Leaf Rot",
        "Stem Bleeding",
    ]
    assert classes == expected


def test_black_pepper_class_mapping():
    service = DiseaseDetectionService()
    _, classes = service.get_or_load_model("black_pepper")
    expected = ["Footrot", "Pollu_Disease", "Slow-Decline"]
    assert classes == expected


def test_cardamom_class_mapping():
    service = DiseaseDetectionService()
    _, classes = service.get_or_load_model("cardamom")
    expected = ["Blight1000", "Healthy_1000", "Phylosticta_LS_1000"]
    assert classes == expected


def test_turmeric_class_mapping():
    service = DiseaseDetectionService()
    _, classes = service.get_or_load_model("turmeric")
    expected = ["Aphids_Disease", "Blotch", "Healthy_Leaf", "Leaf_Spot"]
    assert classes == expected


def test_ginger_class_mapping():
    service = DiseaseDetectionService()
    _, classes = service.get_or_load_model("ginger")
    expected = ["Damage-Pest", "Dehydrated", "Healthy", "Leaf-blight"]
    assert classes == expected


# ==============================================================================
# 17. Explicit Paddy Regression Test
# ==============================================================================

def test_paddy_explicit_regression_ordering():
    """Verify that Paddy class index 0 is Blast and index 1 is Bacterial_Leaf_Blight."""
    service = DiseaseDetectionService()
    _, paddy_classes = service.get_or_load_model("paddy")
    assert paddy_classes[0] == "Blast"
    assert paddy_classes[1] == "Bacterial_Leaf_Blight"
    assert paddy_classes[2] == "Brown_Plant_Hopper"
    assert paddy_classes[3] == "Sheath_Blight"


# ==============================================================================
# 18. Checkpoint Metadata Key Support ('classes' and 'class_names')
# ==============================================================================

def test_checkpoints_support_both_metadata_keys():
    """Verify generic loader handles both 'classes' and 'class_names'."""
    model_dir = settings.resolved_disease_model_dir

    # Arecanut uses 'classes'
    arecanut_ckpt = torch.load(model_dir / SUPPORTED_CROPS["arecanut"].filename, map_location="cpu")
    assert "classes" in arecanut_ckpt
    assert arecanut_ckpt.get("class_names") is None

    # Black Pepper uses 'class_names'
    bp_ckpt = torch.load(model_dir / SUPPORTED_CROPS["black_pepper"].filename, map_location="cpu")
    assert "class_names" in bp_ckpt
    assert bp_ckpt.get("classes") is None

    # Service successfully extracted classes for both
    service = DiseaseDetectionService()
    _, arecanut_classes = service.get_or_load_model("arecanut")
    _, bp_classes = service.get_or_load_model("black_pepper")
    assert len(arecanut_classes) == 6
    assert len(bp_classes) == 3


# ==============================================================================
# 19. Preprocessing Output Shape
# ==============================================================================

def test_rgb_preprocessing_shape():
    """Verify image preprocessing produces (1, 3, 224, 224) tensor."""
    service = DiseaseDetectionService()
    synthetic_bytes = create_synthetic_image_bytes(size=(512, 384))
    tensor = service.preprocess_image(synthetic_bytes)

    assert tensor.shape == torch.Size([1, 3, 224, 224])
    assert tensor.dtype == torch.float32


# ==============================================================================
# 20 & 21. Synthetic Inference for All 7 Models
# ==============================================================================

@pytest.mark.parametrize("crop", list(SUPPORTED_CROPS.keys()))
def test_synthetic_inference_succeeds_all_models(crop: str):
    """Verify synthetic inference returns valid predictions and confidence in [0, 1]."""
    service = DiseaseDetectionService()
    synthetic_bytes = create_synthetic_image_bytes()

    result = service.predict(crop, synthetic_bytes)

    assert isinstance(result, DiseasePredictionResponse)
    assert result.crop == crop
    assert isinstance(result.predicted_class, str)
    assert len(result.predicted_class) > 0
    assert 0.0 <= result.confidence <= 1.0
    assert len(result.predictions) == SUPPORTED_CROPS[crop].expected_num_classes

    # Sum of softmax probabilities should be approximately 1.0
    prob_sum = sum(p.confidence for p in result.predictions)
    assert 0.99 <= prob_sum <= 1.01

    # First ranked prediction must match top-1
    assert result.predictions[0].class_name == result.predicted_class
    assert result.predictions[0].confidence == result.confidence


# ==============================================================================
# 22. Unsupported Crop Error
# ==============================================================================

def test_unsupported_crop_raises_error():
    service = DiseaseDetectionService()
    synthetic_bytes = create_synthetic_image_bytes()

    with pytest.raises(UnsupportedCropError) as exc_info:
        service.predict("mango", synthetic_bytes)

    assert "mango" in str(exc_info.value)
    assert "arecanut" in str(exc_info.value)


# ==============================================================================
# 23. Invalid Image Error
# ==============================================================================

def test_invalid_image_raises_error():
    service = DiseaseDetectionService()
    corrupt_bytes = b"NOT_A_VALID_IMAGE_DATA_12345"

    with pytest.raises(InvalidImageError):
        service.preprocess_image(corrupt_bytes)


# ==============================================================================
# 24. Empty Upload Error
# ==============================================================================

def test_empty_image_raises_error():
    service = DiseaseDetectionService()
    with pytest.raises(EmptyImageError):
        service.preprocess_image(b"")


# ==============================================================================
# 25 & 26. API Endpoint Tests (Multipart, Statuses, Schemas)
# ==============================================================================

def test_api_predict_success():
    synthetic_bytes = create_synthetic_image_bytes()
    response = client.post(
        "/api/v1/disease/predict",
        data={"crop": "arecanut"},
        files={"file": ("leaf.jpg", synthetic_bytes, "image/jpeg")},
    )

    assert response.status_code == 200
    data = response.json()
    assert data["crop"] == "arecanut"
    assert "predicted_class" in data
    assert 0.0 <= data["confidence"] <= 1.0
    assert len(data["predictions"]) == 6
    assert data["model"] == "krushisetu_efficientnet_b0_best.pth"


def test_api_predict_unsupported_crop():
    synthetic_bytes = create_synthetic_image_bytes()
    response = client.post(
        "/api/v1/disease/predict",
        data={"crop": "rubber"},
        files={"file": ("leaf.jpg", synthetic_bytes, "image/jpeg")},
    )

    assert response.status_code == 422
    data = response.json()
    assert "Unsupported crop 'rubber'" in data["detail"]


def test_api_predict_empty_file():
    response = client.post(
        "/api/v1/disease/predict",
        data={"crop": "paddy"},
        files={"file": ("empty.jpg", b"", "image/jpeg")},
    )

    assert response.status_code == 400
    assert "empty" in response.json()["detail"].lower()


def test_api_predict_invalid_image():
    response = client.post(
        "/api/v1/disease/predict",
        data={"crop": "paddy"},
        files={"file": ("corrupt.jpg", b"invalid_binary_stream", "image/jpeg")},
    )

    assert response.status_code == 400
    assert "cannot identify" in response.json()["detail"].lower()
