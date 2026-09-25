"""Disease Detection Service for KrushiPragya Modular Monolith.

Executes CPU-based PyTorch EfficientNet-B0 inference on validated crop disease models.
Maintains an in-process cache of loaded models for optimal performance.
Protects inference with an Input Verification Layer and a 50% Confidence Gate.
"""
from dataclasses import dataclass
import io
import logging
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from PIL import Image, UnidentifiedImageError
import torch
import torch.nn as nn
from torchvision import transforms
from torchvision.models import efficientnet_b0

from app.core.config import settings
from app.schemas.disease import (
    ClassPrediction,
    DiseaseInfoResponse,
    DiseasePredictionResponse,
)
from app.services.disease_kb import get_disease_info
from app.services.input_verification_service import (
    InputVerificationService,
    get_input_verification_service,
)

logger = logging.getLogger(__name__)

# Application-level confidence gate threshold (50%)
# If confidence < 0.50, predicted_class is withheld (null) and status is marked UNCERTAIN
APPLICATION_CONFIDENCE_THRESHOLD = 0.50


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


class ModelUnavailableError(DiseaseDetectionError):
    """Raised when a model is temporarily unavailable or could not be loaded."""
    pass


class InvalidCheckpointError(DiseaseDetectionError):
    """Raised when a checkpoint is missing expected keys or weights."""
    pass


class VerificationRejectionError(DiseaseDetectionError):
    """Raised when an uploaded image is rejected by the defensive Input Verification Layer."""

    def __init__(self, reason_code: str, message: str, metrics: Optional[Dict[str, Any]] = None):
        self.reason_code = reason_code
        self.message = message
        self.metrics = metrics or {}
        super().__init__(f"Input verification rejected ({reason_code}): {message}")


# ==============================================================================
# Crop Model Registry
# ==============================================================================

@dataclass(frozen=True)
class ModelSpec:
    """Specification for a trained crop disease classification model."""
    crop: str
    model_version: str
    filename: str
    expected_num_classes: int


SUPPORTED_CROPS: Dict[str, ModelSpec] = {
    "arecanut": ModelSpec(
        crop="arecanut",
        model_version="arecanut-v1",
        filename="krushisetu_efficientnet_b0_best.pth",
        expected_num_classes=6,
    ),
    "paddy": ModelSpec(
        crop="paddy",
        model_version="paddy-v1",
        filename="krushisetu_paddy_efficientnet_b0_best.pth",
        expected_num_classes=4,
    ),
    "coconut": ModelSpec(
        crop="coconut",
        model_version="coconut-v1",
        filename="krushisetu_coconut_efficientnet_b0_best.pth",
        expected_num_classes=5,
    ),
    "black_pepper": ModelSpec(
        crop="black_pepper",
        model_version="black-pepper-v1",
        filename="krushisetu_black_pepper_efficientnet_b0_best.pth",
        expected_num_classes=3,
    ),
    "cardamom": ModelSpec(
        crop="cardamom",
        model_version="cardamom-v1",
        filename="krushisetu_cardamom_efficientnet_b0_best.pth",
        expected_num_classes=3,
    ),
    "turmeric": ModelSpec(
        crop="turmeric",
        model_version="turmeric-v1",
        filename="krushisetu_turmeric_efficientnet_b0_best.pth",
        expected_num_classes=4,
    ),
    "ginger": ModelSpec(
        crop="ginger",
        model_version="ginger-v1",
        filename="krushisetu_ginger_efficientnet_b0_best.pth",
        expected_num_classes=4,
    ),
}


# ==============================================================================
# Service Implementation
# ==============================================================================

class DiseaseDetectionService:
    """Service managing image preprocessing, model caching, input verification, and CPU inference."""

    def __init__(
        self,
        model_dir: Optional[Path] = None,
        verifier: Optional[InputVerificationService] = None,
    ):
        self.model_dir = model_dir or settings.resolved_disease_model_dir
        # In-process cache: crop -> (nn.Module, list of class labels)
        self._models: Dict[str, Tuple[nn.Module, List[str]]] = {}
        self.verifier = verifier or get_input_verification_service()

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

    def preload_all_models(self) -> Dict[str, bool]:
        """Preload all 7 crop models into memory at application startup.

        Safely records availability without crashing if a model is temporarily missing.
        """
        results: Dict[str, bool] = {}
        logger.info("Preloading all 7 crop disease models into memory...")

        for crop in SUPPORTED_CROPS:
            try:
                self.get_or_load_model(crop)
                results[crop] = True
            except Exception as exc:
                logger.warning("Could not preload disease model for crop '%s': %s", crop, exc)
                results[crop] = False

        loaded_count = sum(1 for v in results.values() if v)
        logger.info("Preloaded %d of %d crop models into memory.", loaded_count, len(SUPPORTED_CROPS))
        return results

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

    def predict(
        self,
        raw_crop: str,
        image_bytes: bytes,
        verify_input: bool = True,
        enforce_confidence_gate: bool = False,
    ) -> DiseasePredictionResponse:
        """Execute disease prediction inference for a given crop and image.

        Args:
            raw_crop: Crop name string (e.g. arecanut, paddy)
            image_bytes: Raw binary image payload
            verify_input: If True, executes defensive input verification layer first
            enforce_confidence_gate: If True, withholds predicted_class (sets None) when confidence < 50%

        Returns:
            DiseasePredictionResponse with status ('success' or 'uncertain'),
            predictions, model version, and curated Disease KB attachment if confident.

        Raises:
            VerificationRejectionError: If image fails quality, lighting, or leaf relevance checks
            UnsupportedCropError: If crop is not in the 7 supported crops
            EmptyImageError: If byte array is empty
            InvalidImageError: If image cannot be identified/decoded
            ModelNotFoundError: If checkpoint file is missing on server
        """
        norm_crop = self.normalize_crop(raw_crop)
        spec = SUPPORTED_CROPS[norm_crop]

        # ======================================================================
        # 1. Defensive Input Verification Layer
        # ======================================================================
        if verify_input:
            v_res = self.verifier.verify(crop=norm_crop, image_bytes=image_bytes)
            if not v_res.is_valid:
                logger.warning(
                    "Input verification REJECTED upload for crop '%s': [%s] %s",
                    norm_crop, v_res.reason_code, v_res.message,
                )
                raise VerificationRejectionError(
                    reason_code=v_res.reason_code or "LOW_IMAGE_QUALITY",
                    message=v_res.message,
                    metrics=v_res.metrics,
                )

        # ======================================================================
        # 2. Retrieve / Load Model
        # ======================================================================
        model, classes = self.get_or_load_model(norm_crop)
        tensor = self.preprocess_image(image_bytes)

        # ======================================================================
        # 3. Model Inference & Softmax
        # ======================================================================
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
        confidence = top_prediction.confidence

        # ======================================================================
        # 4. 50% Application Confidence Gate & Disease KB Lookup
        # ======================================================================
        is_confident = confidence >= APPLICATION_CONFIDENCE_THRESHOLD

        if is_confident or not enforce_confidence_gate:
            # Passed verification + passed confidence gate (or raw inference mode) -> SUCCESS
            status = "success"
            predicted_class: Optional[str] = top_prediction.class_name
            low_confidence = not is_confident
            message = f"AI analysis completed. Identified condition: {top_prediction.class_name} with {round(confidence * 100, 1)}% model confidence."

            # Query curated Disease Knowledge Base (NO LLM)
            kb_entry = get_disease_info(norm_crop, top_prediction.class_name)
            disease_info = None
            if kb_entry and is_confident:
                disease_info = DiseaseInfoResponse(
                    disease_name_en=kb_entry.disease_name_en,
                    disease_name_kn=kb_entry.disease_name_kn,
                    scientific_name=kb_entry.scientific_name,
                    category=kb_entry.category,
                    symptoms=kb_entry.symptoms,
                    cultural_control=kb_entry.cultural_control,
                    remedy_en=kb_entry.remedy_en,
                    remedy_kn=kb_entry.remedy_kn,
                    source_institution=kb_entry.source_institution,
                )
        else:
            # Below 50% confidence with gate enforced -> UNCERTAIN (Do NOT display predicted disease as diagnosis!)
            status = "uncertain"
            predicted_class = None
            low_confidence = True
            disease_info = None  # Do NOT attach treatments when model is uncertain
            message = (
                f"The image could not be confidently identified (model confidence {round(confidence * 100, 1)}% "
                f"is below the {int(APPLICATION_CONFIDENCE_THRESHOLD * 100)}% threshold). "
                f"Please capture a clearer image of the affected leaf in good lighting."
            )
            logger.info(
                "Prediction for crop '%s' marked UNCERTAIN: top class '%s' has confidence %.2f < %.2f",
                norm_crop, top_prediction.class_name, confidence, APPLICATION_CONFIDENCE_THRESHOLD,
            )

        return DiseasePredictionResponse(
            crop=norm_crop,
            status=status,
            predicted_class=predicted_class,
            confidence=confidence,
            low_confidence=low_confidence,
            input_verified=True,
            reason_code=None if status == "success" else "LOW_CONFIDENCE",
            message=message,
            model_version=spec.model_version,
            disease_info=disease_info,
            predictions=predictions,
            top_predictions=predictions[:3],
            model=spec.filename,
        )


def get_disease_detection_service() -> DiseaseDetectionService:
    """Dependency provider returning singleton DiseaseDetectionService."""
    return DiseaseDetectionService()
