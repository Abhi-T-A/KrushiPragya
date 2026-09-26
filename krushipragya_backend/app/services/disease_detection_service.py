"""Disease Detection Service for KrushiPragya Modular Monolith.

Executes CPU-based PyTorch EfficientNet-B0 inference on validated crop disease models.
Maintains an in-process cache of loaded models for optimal performance.
Protects inference with an Input Verification Layer and a 50% Confidence Gate.
"""
from dataclasses import dataclass
from datetime import datetime, timezone
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
from app.services.crop_relevance_service import CROP_METADATA
from app.services.disease_explanation_service import get_disease_explanation_service
from app.services.disease_kb import get_disease_info
from app.services.input_verification_service import (
    InputVerificationService,
    get_input_verification_service,
)

logger = logging.getLogger(__name__)

# Application-level confidence gate threshold (35%)
# Configured to 35% so field photos with ~40-50% confidence can proceed to the diagnosis
# screen with a 'low_confidence' flag, allowing farmers to review AI insights or request Expert Verification.
CONFIRMED_DIAGNOSIS_THRESHOLD = 0.35
HEALTHY_CONFIDENCE_THRESHOLD = 0.35
APPLICATION_CONFIDENCE_THRESHOLD = 0.35

MAX_IMAGE_FILE_SIZE = 15 * 1024 * 1024  # 15 MB
MIN_IMAGE_DIMENSION = 64
MAX_IMAGE_DIMENSION = 5000


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

        if len(image_bytes) > MAX_IMAGE_FILE_SIZE:
            raise VerificationRejectionError(
                reason_code="IMAGE_TOO_LARGE",
                message=f"Uploaded image exceeds maximum allowable size of {MAX_IMAGE_FILE_SIZE // (1024 * 1024)}MB.",
                metrics={"file_size_bytes": len(image_bytes), "max_allowed_bytes": MAX_IMAGE_FILE_SIZE},
            )

        try:
            img = Image.open(io.BytesIO(image_bytes))
            img.load()  # Force decode raster data to catch corruptions
        except (UnidentifiedImageError, OSError, ValueError) as exc:
            raise InvalidImageError(f"Cannot identify or decode image file: {exc}") from exc

        width, height = img.size
        if width < MIN_IMAGE_DIMENSION or height < MIN_IMAGE_DIMENSION:
            raise VerificationRejectionError(
                reason_code="LOW_IMAGE_QUALITY",
                message=f"Image resolution ({width}x{height}) is too low. Minimum required is {MIN_IMAGE_DIMENSION}x{MIN_IMAGE_DIMENSION} pixels.",
                metrics={"width": width, "height": height, "min_required": MIN_IMAGE_DIMENSION},
            )

        if width > MAX_IMAGE_DIMENSION or height > MAX_IMAGE_DIMENSION:
            raise VerificationRejectionError(
                reason_code="IMAGE_TOO_LARGE",
                message=f"Image resolution ({width}x{height}) exceeds maximum allowed {MAX_IMAGE_DIMENSION}x{MAX_IMAGE_DIMENSION} pixels.",
                metrics={"width": width, "height": height, "max_allowed": MAX_IMAGE_DIMENSION},
            )

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
            enforce_confidence_gate: If True, withholds predicted_class (sets None) when confidence < 70%

        Returns:
            DiseasePredictionResponse with authoritative fields:
            status ('success' or 'uncertain'), state, predicted_class, confidence,
            disease, disease_name_kn, knowledge_base_reference, explanation_kn,
            approved_actions, verification_state, generated_at, is_llm_generated, fallback_used.

        Raises:
            VerificationRejectionError: If image fails quality, lighting, or leaf relevance checks
            UnsupportedCropError: If crop is not in the 7 supported crops
            EmptyImageError: If byte array is empty
            InvalidImageError: If image cannot be identified/decoded
            ModelNotFoundError: If checkpoint file is missing on server
        """
        norm_crop = self.normalize_crop(raw_crop)
        spec = SUPPORTED_CROPS[norm_crop]
        logger.info("[DISEASE] inference started for crop '%s'", norm_crop)

        # ======================================================================
        # 1. Defensive Input Verification Layer & Relevance Gate
        # ======================================================================
        if verify_input:
            v_res = self.verifier.verify(crop=norm_crop, image_bytes=image_bytes)
            if not v_res.is_valid:
                logger.warning(
                    "[DISEASE] image validation: REJECTED for crop '%s': [%s] %s",
                    norm_crop, v_res.reason_code, v_res.message,
                )
                raise VerificationRejectionError(
                    reason_code=v_res.reason_code or "LOW_IMAGE_QUALITY",
                    message=v_res.message,
                    metrics=v_res.metrics,
                )
            logger.info("[DISEASE] image validation: PASSED for crop '%s'", norm_crop)

        # ======================================================================
        # 2. Retrieve / Load Model & Preprocess
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
        logger.info(
            "[DISEASE] model executed: %s (%s) -> top prediction: %s (confidence: %.4f)",
            spec.filename, spec.model_version, top_prediction.class_name, confidence,
        )
        logger.info(
            "[DISEASE] inference completed: raw_class='%s', confidence=%.4f",
            top_prediction.class_name, confidence,
        )

        # ======================================================================
        # 4. Crop Compatibility Cross-Check (Detect CROP_MISMATCH)
        # ======================================================================
        if enforce_confidence_gate and confidence < 0.35:
            # Check other already loaded models to see if another crop is overwhelmingly confident
            for other_crop, spec_other in SUPPORTED_CROPS.items():
                if other_crop != norm_crop and other_crop in self._models:
                    other_model, other_classes = self._models[other_crop]
                    with torch.no_grad():
                        other_logits = other_model(tensor)
                        other_probs = torch.softmax(other_logits, dim=1)[0]
                        max_other_conf = float(torch.max(other_probs).item())
                    if max_other_conf >= 0.80 and confidence < 0.25:
                        logger.info(
                            "[DISEASE] crop compatibility: CROP_MISMATCH detected (selected='%s' [%.2f], other='%s' [%.2f])",
                            norm_crop, confidence, other_crop, max_other_conf,
                        )
                        raise VerificationRejectionError(
                            reason_code="CROP_MISMATCH",
                            message=f"The selected crop does not match the uploaded image.",
                            metrics={"selected_crop": norm_crop, "matched_crop": other_crop, "other_confidence": round(max_other_conf, 4)},
                        )

        # ======================================================================
        # 5. Deterministic Disease KB Lookup (NO LLM)
        # ======================================================================
        kb_entry = get_disease_info(norm_crop, top_prediction.class_name)
        if kb_entry:
            logger.info(
                "[DISEASE] KB mapping: %s -> %s (scientific: %s, category: %s)",
                top_prediction.class_name, kb_entry.disease_name_en,
                kb_entry.scientific_name, kb_entry.category,
            )

        # ======================================================================
        # 6. Confidence Gate & Authoritative Assignment
        # ======================================================================
        # "Healthy" is also a diagnosis requiring sufficient confidence
        is_healthy_class = (kb_entry and kb_entry.category == "HEALTHY") or ("healthy" in top_prediction.class_name.lower())
        threshold_to_apply = HEALTHY_CONFIDENCE_THRESHOLD if is_healthy_class else CONFIRMED_DIAGNOSIS_THRESHOLD

        is_confident = confidence >= threshold_to_apply

        crop_info = CROP_METADATA.get(norm_crop, {})
        crop_name_en = crop_info.get("name_en", norm_crop.title())
        crop_name_kn = crop_info.get("name_kn", norm_crop)

        if is_confident or not enforce_confidence_gate:
            # Confirmed diagnosis or raw inference testing mode
            status = "success"
            state = "VALID_IMAGE"
            verification_state = "AI_ANALYSED"
            predicted_class: Optional[str] = top_prediction.class_name
            diagnosis: Optional[str] = top_prediction.class_name
            low_confidence = confidence < 0.65
            message = (
                f"AI analysis completed. Identified condition: {top_prediction.class_name} "
                f"with {round(confidence * 100, 1)}% model confidence."
            )

            if kb_entry and is_confident:
                disease = kb_entry.disease_name_en
                disease_name_kn = kb_entry.disease_name_kn
                knowledge_base_reference = kb_entry.source_institution
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

                # Qwen explanation/localization ONLY (Never diagnoses, receives only approved facts)
                explanation_service = get_disease_explanation_service()
                explanation_obj = explanation_service.explain_diagnosis(
                    crop_code=norm_crop,
                    crop_name_en=crop_name_en,
                    crop_name_kn=crop_name_kn,
                    raw_class=top_prediction.class_name,
                    raw_confidence=confidence,
                    kb_entry=kb_entry,
                )
                explanation_kn = explanation_obj.summary_kn
                approved_actions = explanation_obj.actions_kn
                is_llm_generated = explanation_obj.is_llm_generated
                fallback_used = explanation_obj.fallback_used

            elif kb_entry:
                # Unenforced confidence gate (raw test mode) with KB entry
                disease = kb_entry.disease_name_en
                disease_name_kn = kb_entry.disease_name_kn
                knowledge_base_reference = kb_entry.source_institution
                disease_info = None
                explanation_kn = f"{crop_name_kn} ಬೆಳೆಯಲ್ಲಿ {kb_entry.disease_name_kn} ಸ್ಥಿತಿ ಪತ್ತೆಯಾಗಿದೆ."
                approved_actions = [kb_entry.remedy_kn] if kb_entry.remedy_kn else []
                is_llm_generated = False
                fallback_used = True
            else:
                disease = top_prediction.class_name
                disease_name_kn = top_prediction.class_name
                knowledge_base_reference = "KrushiPragya Knowledge Base"
                disease_info = None
                explanation_kn = f"{crop_name_kn} ಬೆಳೆಯಲ್ಲಿ {top_prediction.class_name} ಸ್ಥಿತಿ ಪತ್ತೆಯಾಗಿದೆ."
                approved_actions = []
                is_llm_generated = False
                fallback_used = True

        else:
            # Below conservative 70% threshold -> UNCERTAIN_IMAGE
            # Do NOT present weak predictions as confirmed diagnoses
            status = "uncertain"
            state = "UNCERTAIN_IMAGE"
            verification_state = "UNCERTAIN_IMAGE"
            predicted_class = None
            diagnosis = None
            disease = None
            disease_name_kn = None
            knowledge_base_reference = None
            low_confidence = True
            disease_info = None
            approved_actions = []
            is_llm_generated = False
            fallback_used = True
            explanation_kn = (
                "ಚಿತ್ರವನ್ನು ಖಚಿತವಾಗಿ ಗುರುತಿಸಲಾಗಲಿಲ್ಲ (ಮಾದರಿ ವಿಶ್ವಾಸಾರ್ಹತೆ ಕನಿಷ್ಠ ಮಟ್ಟಕ್ಕಿಂತ ಕಡಿಮೆಯಿದೆ). "
                "ದಯವಿಟ್ಟು ಸ್ಪಷ್ಟ ಬೆಳಕಿನಲ್ಲಿ ಬಾಧಿತ ಎಲೆಯ ಹತ್ತಿರದ ಚಿತ್ರವನ್ನು ಮರು-ಅಪ್ಲೋಡ್ ಮಾಡಿ."
            )
            message = (
                f"The image could not be confidently identified (confidence "
                f"{round(confidence * 100, 1)}% is below the {int(threshold_to_apply * 100)}% threshold). "
                f"Please capture a clearer image of the affected leaf in good lighting."
            )
            logger.info(
                "[DISEASE] final state: UNCERTAIN_IMAGE (confidence %.4f < %.2f)",
                confidence, threshold_to_apply,
            )

        logger.info(
            "[DISEASE] final state: %s | Qwen explanation: is_llm=%s, fallback_used=%s",
            verification_state, is_llm_generated, fallback_used,
        )

        return DiseasePredictionResponse(
            crop=norm_crop,
            status=status,
            state=state,
            predicted_class=predicted_class,
            diagnosis=diagnosis,
            confidence=confidence,
            low_confidence=low_confidence,
            input_verified=True,
            reason_code=None if status == "success" else "UNCERTAIN_IMAGE",
            message=message,
            model_version=spec.model_version,
            disease_info=disease_info,
            predictions=predictions,
            top_predictions=predictions[:3],
            model=spec.filename,
            disease=disease,
            disease_name_kn=disease_name_kn,
            knowledge_base_reference=knowledge_base_reference,
            explanation_kn=explanation_kn,
            approved_actions=approved_actions,
            verification_state=verification_state,
            generated_at=datetime.now(timezone.utc).isoformat(),
            is_llm_generated=is_llm_generated,
            fallback_used=fallback_used,
        )


def get_disease_detection_service() -> DiseaseDetectionService:
    """Dependency provider returning singleton DiseaseDetectionService."""
    return DiseaseDetectionService()

