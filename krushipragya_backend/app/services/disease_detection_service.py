"""Disease Detection Service for KrushiPragya Modular Monolith.

Executes CPU-based PyTorch EfficientNet-B0 inference on validated crop disease models.
Maintains an in-process cache of loaded models for optimal performance.
"""
from dataclasses import dataclass
import io
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from PIL import Image, UnidentifiedImageError
import torch
import torch.nn as nn
from torchvision import transforms
from torchvision.models import efficientnet_b0

from app.core.config import settings
from app.schemas.disease import ClassPrediction, DiseasePredictionResponse

logger = logging.getLogger(__name__)


# ==============================================================================
# Domain Exceptions
# ==============================================================================

class DiseaseDetectionError(Exception):
    """Base exception for disease detection failures."""
    pass


class UnsupportedCropError(DiseaseDetectionError):
    """Raised when an unrecognized crop identifier is provided."""

    def __init__(self, crop: str, supported_crops: List[str]):
        self.crop = crop
        self.supported_crops = supported_crops
        super().__init__(
            f"Unsupported crop '{crop}'. Supported crops: {', '.join(sorted(supported_crops))}"
        )


class EmptyImageError(DiseaseDetectionError):
    """Raised when the uploaded image payload is empty."""
    pass


class InvalidImageError(DiseaseDetectionError):
    """Raised when the image payload cannot be parsed as a valid image."""
    pass


class ModelNotFoundError(DiseaseDetectionError):
    """Raised when a required model checkpoint file is missing."""
    pass


class InvalidCheckpointError(DiseaseDetectionError):
    """Raised when a checkpoint is missing expected keys or weights."""
    pass


# ==============================================================================
# Crop Model Registry
# ==============================================================================

@dataclass(frozen=True)
class ModelSpec:
    """Specification for a trained crop disease classification model."""
    crop: str
    filename: str
    expected_num_classes: int


SUPPORTED_CROPS: Dict[str, ModelSpec] = {
    "arecanut": ModelSpec(
        crop="arecanut",
        filename="krushisetu_efficientnet_b0_best.pth",
        expected_num_classes=6,
    ),
    "paddy": ModelSpec(
        crop="paddy",
        filename="krushisetu_paddy_efficientnet_b0_best.pth",
        expected_num_classes=4,
    ),
    "coconut": ModelSpec(
        crop="coconut",
        filename="krushisetu_coconut_efficientnet_b0_best.pth",
        expected_num_classes=5,
    ),
    "black_pepper": ModelSpec(
        crop="black_pepper",
        filename="krushisetu_black_pepper_efficientnet_b0_best.pth",
        expected_num_classes=3,
    ),
    "cardamom": ModelSpec(
        crop="cardamom",
        filename="krushisetu_cardamom_efficientnet_b0_best.pth",
        expected_num_classes=3,
    ),
    "turmeric": ModelSpec(
        crop="turmeric",
        filename="krushisetu_turmeric_efficientnet_b0_best.pth",
        expected_num_classes=4,
    ),
    "ginger": ModelSpec(
        crop="ginger",
        filename="krushisetu_ginger_efficientnet_b0_best.pth",
        expected_num_classes=4,
    ),
}


# ==============================================================================
# Service Implementation
# ==============================================================================

class DiseaseDetectionService:
    """Service managing image preprocessing, model caching, and CPU inference."""

    def __init__(self, model_dir: Optional[Path] = None):
        self.model_dir = model_dir or settings.resolved_disease_model_dir
        # In-process cache: crop -> (nn.Module, list of class labels)
        self._models: Dict[str, Tuple[nn.Module, List[str]]] = {}

        # Standard ImageNet eval transform (224x224, Normalized)
        self._eval_transform = transforms.Compose([
            transforms.Resize((224, 224)),
            transforms.ToTensor(),
            transforms.Normalize(
                mean=[0.485, 0.456, 0.406],
                std=[0.229, 0.224, 0.225],
            ),
        ])

    @staticmethod
    def normalize_crop(raw_crop: str) -> str:
        """Normalize raw crop string to lowercase snake_case."""
        if not raw_crop:
            raise UnsupportedCropError("", list(SUPPORTED_CROPS.keys()))
        norm = raw_crop.strip().lower().replace("-", "_").replace(" ", "_")
        if norm not in SUPPORTED_CROPS:
            raise UnsupportedCropError(raw_crop, list(SUPPORTED_CROPS.keys()))
        return norm

    def get_or_load_model(self, crop: str) -> Tuple[nn.Module, List[str]]:
        """Retrieve a cached model or load it from disk into memory."""
        norm_crop = self.normalize_crop(crop)

        if norm_crop in self._models:
            return self._models[norm_crop]

        spec = SUPPORTED_CROPS[norm_crop]
        model_path = self.model_dir / spec.filename

        if not model_path.exists():
            raise ModelNotFoundError(
                f"Model checkpoint for '{norm_crop}' not found at {model_path}"
            )

        logger.info("Loading disease model checkpoint for '%s' from %s...", norm_crop, model_path)

        try:
            checkpoint = torch.load(model_path, map_location="cpu", weights_only=False)
        except Exception as exc:
            raise InvalidCheckpointError(
                f"Failed to load checkpoint file for '{norm_crop}': {exc}"
            ) from exc

        if "model_state_dict" not in checkpoint:
            raise InvalidCheckpointError(
                f"Checkpoint for '{norm_crop}' is missing 'model_state_dict'."
            )

        # Support both 'classes' and 'class_names' keys in checkpoints
        classes = checkpoint.get("classes") or checkpoint.get("class_names")
        if not classes or not isinstance(classes, list):
            raise InvalidCheckpointError(
                f"Checkpoint for '{norm_crop}' does not contain a valid class list ('classes' or 'class_names')."
            )

        num_classes = len(classes)
        if num_classes != spec.expected_num_classes:
            raise InvalidCheckpointError(
                f"Class count mismatch for '{norm_crop}': expected {spec.expected_num_classes}, found {num_classes}."
            )

        # Instantiate EfficientNet-B0 and adapt classification head
        model = efficientnet_b0(weights=None)
        in_features = model.classifier[1].in_features
        model.classifier[1] = nn.Linear(in_features, num_classes)

        # Load weights and switch to eval mode
        try:
            model.load_state_dict(checkpoint["model_state_dict"], strict=True)
        except Exception as exc:
            raise InvalidCheckpointError(
                f"Weights mismatch loading state_dict for '{norm_crop}': {exc}"
            ) from exc

        model.eval()

        self._models[norm_crop] = (model, classes)
        logger.info(
            "Successfully cached model for '%s' (%d classes: %s)",
            norm_crop,
            num_classes,
            classes,
        )
        return self._models[norm_crop]

    def preprocess_image(self, image_bytes: bytes) -> torch.Tensor:
        """Validate raw bytes and transform into a (1, 3, 224, 224) normalized tensor."""
        if not image_bytes or len(image_bytes) == 0:
            raise EmptyImageError("Uploaded image file is empty.")

        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.load()  # Force decode raster data to catch corruptions
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise InvalidImageError(f"Cannot identify or decode image file: {exc}") from exc

        # Ensure RGB format (converts RGBA, Grayscale, CMYK, etc.)
        if img.mode != "RGB":
            img = img.convert("RGB")

        # Apply transforms and add batch dimension
        tensor = self._eval_transform(img).unsqueeze(0)
        return tensor

    def predict(self, raw_crop: str, image_bytes: bytes) -> DiseasePredictionResponse:
        """Execute disease prediction inference for a given crop and image."""
        norm_crop = self.normalize_crop(raw_crop)
        spec = SUPPORTED_CROPS[norm_crop]

        model, classes = self.get_or_load_model(norm_crop)
        tensor = self.preprocess_image(image_bytes)

        with torch.no_grad():
            logits = model(tensor)
            probabilities = torch.softmax(logits, dim=1)[0]

        ranked_indices = torch.argsort(probabilities, descending=True).tolist()
        predictions = [
            ClassPrediction(
                class_name=classes[idx],
                confidence=round(float(probabilities[idx].item()), 4),
            )
            for idx in ranked_indices
        ]

        top_prediction = predictions[0]

        return DiseasePredictionResponse(
            crop=norm_crop,
            predicted_class=top_prediction.class_name,
            confidence=top_prediction.confidence,
            predictions=predictions,
            model=spec.filename,
        )
