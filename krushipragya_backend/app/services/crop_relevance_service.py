"""Crop Relevance & Visual Gating Service for KrushiPragya AI Inference Pipeline.

Defensive gate that evaluates semantic visual relevance and selected crop compatibility
BEFORE allowing any image to reach the closed-set disease classifiers.

CRITICAL ARCHITECTURAL PRINCIPLE:
A disease classifier must NEVER classify an obviously unrelated image simply because one of
its known classes has the highest softmax argmax probability.
The classifier is closed-set and only knows trained disease classes.
Therefore, an unrelated image (e.g. laptop keyboard, car, human, desk, document)
must be rejected by this visual relevance gate.

Safe Decision States:
- VALID_IMAGE: Image passes quality, semantic visual relevance, and crop compatibility checks.
- IRRELEVANT_IMAGE: Image is clearly not a crop/plant/produce image (laptop, person, car, keyboard, etc.).
- CROP_MISMATCH: Image appears to contain a crop/plant, but not the crop selected by the farmer.
- UNCERTAIN_IMAGE: Image may contain a crop, but the system cannot reliably determine relevance.
- LOW_QUALITY: Image cannot be reliably analyzed because of blur, darkness, or low resolution.
"""
from dataclasses import dataclass, field
import io
import logging
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from PIL import Image
import torch
import torch.nn as nn
from torchvision import models, transforms

logger = logging.getLogger(__name__)

# Standard crop metadata for the 7 supported crops
CROP_METADATA: Dict[str, Dict[str, str]] = {
    "arecanut": {"code": "arecanut", "name_en": "Arecanut", "name_kn": "ಅಡಿಕೆ"},
    "paddy": {"code": "paddy", "name_en": "Paddy", "name_kn": "ಭತ್ತ"},
    "coconut": {"code": "coconut", "name_en": "Coconut", "name_kn": "ತೆಂಗು"},
    "black_pepper": {"code": "black_pepper", "name_en": "Black Pepper", "name_kn": "ಕಾಳುಮೆಣಸು"},
    "cardamom": {"code": "cardamom", "name_en": "Cardamom", "name_kn": "ಏಲಕ್ಕಿ"},
    "turmeric": {"code": "turmeric", "name_en": "Turmeric", "name_kn": "ಅರಿಶಿನ"},
    "ginger": {"code": "ginger", "name_en": "Ginger", "name_kn": "ಶುಂಠಿ"},
}

# Explicit non-crop keywords for hardware, electronics, appliances, vehicles, and furniture
EXPLICIT_NON_CROP_KEYWORDS: List[str] = [
    # Electronics, computers, keyboards, office hardware
    "keyboard", "space bar", "typewriter", "laptop", "notebook", "mouse", "monitor", "screen",
    "computer", "phone", "cellular", "telephone", "ipod", "joystick", "modem", "printer",
    "scanner", "hard disc", "loudspeaker", "microphone", "headphones", "television", "remote",
    # Appliances & indoor heating/cooling
    "space heater", "heater", "microwave", "refrigerator", "toaster", "oven", "stove",
    "washer", "dishwasher", "vacuum", "iron", "lamp",
    # Furniture, indoor surfaces
    "desk", "table", "chair", "sofa", "couch", "bed", "wardrobe", "bookcase", "cabinet",
    # Vehicles & transport
    "car", "automobile", "vehicle", "truck", "bus", "train", "plane", "aircraft", "bicycle",
    "motorcycle", "scooter", "ambulance", "fire engine", "convertible", "sports car", "taxi",
    # Apparel, footwear, personal items
    "shoe", "boot", "sneaker", "sandal", "sock", "shirt", "suit", "coat", "jacket", "dress",
    "jean", "pants", "hat", "cap", "helmet", "sunglasses", "watch", "wallet", "purse", "backpack",
    # Household & office tools, documents, paper
    "puzzle", "crossword", "scoreboard", "paper", "pen", "pencil", "binder", "stapler",
    "scissors", "ruler", "comic book", "menu", "packet", "carton", "box", "doormat",
    # Domestic pets
    "dog", "cat", "golden retriever", "labrador", "tabby",
]


@dataclass
class CropRelevanceResult:
    """Structured decision output from CropRelevanceService."""
    is_relevant: bool
    state: str  # VALID_IMAGE, IRRELEVANT_IMAGE, CROP_MISMATCH, UNCERTAIN_IMAGE, LOW_QUALITY
    message: str
    message_kn: str
    crop_code: str
    crop_name_en: str
    crop_name_kn: str
    metrics: Dict[str, Any] = field(default_factory=dict)
    top_categories: List[Dict[str, Any]] = field(default_factory=list)


class CropRelevanceService:
    """Lightweight visual relevance and crop compatibility gate.
    
    Evaluates whether an image contains botanical/crop material compatible with
    the user-selected crop before allowing disease model inference.
    """

    _instance: Optional["CropRelevanceService"] = None

    def __init__(self):
        self._model: Optional[nn.Module] = None
        self._categories: List[str] = []
        self._preprocess = None
        self._non_crop_class_indices: Set[int] = set()
        self._initialize_classifier()

    def _initialize_classifier(self) -> None:
        """Initialize lightweight MobileNetV3 semantic classifier from cached weights."""
        try:
            weights = models.MobileNet_V3_Small_Weights.DEFAULT
            self._categories = weights.meta["categories"]
            self._preprocess = weights.transforms()

            # Pre-classify ImageNet categories into non-crop indices
            for idx, cat in enumerate(self._categories):
                c_lower = cat.lower()
                if any(k in c_lower for k in EXPLICIT_NON_CROP_KEYWORDS):
                    self._non_crop_class_indices.add(idx)

            # Instantiate MobileNetV3 small in evaluation mode (CPU)
            model = models.mobilenet_v3_small(weights=weights)
            model.eval()
            self._model = model
            logger.info(
                "CropRelevanceService initialized with MobileNetV3 (%d non-crop categories mapped)",
                len(self._non_crop_class_indices),
            )
        except Exception as exc:
            logger.warning("Could not load MobileNetV3 for CropRelevanceService: %s", exc)
            self._model = None

    def check_botanical_chlorophyll(self, img: Image.Image) -> Tuple[float, float, bool]:
        """Compute chlorophyll green fraction and vegetation consistency.
        
        Real plant foliage contains active chlorophyll:
        Green component significantly dominates over Red and Blue:
        G > R + 8 and G > B + 8.
        Necrotic spots only occur ON or alongside green vegetative tissue.
        A wooden table, brown leather, or indoor desk has 0% chlorophyll green.
        """
        rgb_img = img if img.mode == "RGB" else img.convert("RGB")
        arr = np.array(rgb_img, dtype=np.float32)
        r, g, b = arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

        # Active chlorophyll vegetative tissue (clear vegetative green)
        green_mask = (g > r + 8.0) & (g > b + 8.0) & (g > 35.0)
        green_fraction = float(green_mask.mean())

        # Brown/yellow necrotic lesion tissue
        necrotic_mask = (r > b + 15.0) & (g > b + 10.0) & (r > 55.0) & (g > 45.0) & (b < 155.0)
        necrotic_fraction = float(necrotic_mask.mean())

        # An image contains genuine chlorophyll if at least 1.5% of pixels are active vegetative green
        has_chlorophyll = green_fraction >= 0.015

        return round(green_fraction, 4), round(necrotic_fraction, 4), has_chlorophyll

    def classify_visual_relevance(
        self,
        img: Image.Image,
        crop: str,
    ) -> CropRelevanceResult:
        """Evaluate semantic visual relevance of the image using MobileNetV3 + botanical analysis.
        
        Args:
            img: Decoded PIL image.
            crop: Normalized crop identifier (e.g. coconut, paddy).
            
        Returns:
            CropRelevanceResult with state, farmer-facing messages, and metrics.
        """
        norm_crop = crop.strip().lower().replace("-", "_").replace(" ", "_")
        crop_info = CROP_METADATA.get(norm_crop, {
            "code": norm_crop,
            "name_en": norm_crop.title(),
            "name_kn": norm_crop,
        })

        # Ensure RGB format
        rgb_img = img if img.mode == "RGB" else img.convert("RGB")

        # 1. Botanical Chlorophyll Check
        green_fraction, necrotic_fraction, has_chlorophyll = self.check_botanical_chlorophyll(rgb_img)

        # 2. Semantic Classification via MobileNetV3
        top_cats: List[Dict[str, Any]] = []
        non_crop_prob = 0.0
        top_1_is_non_crop = False
        top_1_name = "unknown"
        top_1_conf = 0.0

        if self._model is not None and self._preprocess is not None:
            try:
                t = self._preprocess(rgb_img).unsqueeze(0)
                with torch.no_grad():
                    logits = self._model(t)
                    probs = torch.softmax(logits, dim=1)[0]

                top5 = torch.topk(probs, 5)
                for rank, (idx, conf_t) in enumerate(zip(top5.indices, top5.values)):
                    i = int(idx.item())
                    c = round(float(conf_t.item()), 4)
                    cat_name = self._categories[i]
                    is_nc = i in self._non_crop_class_indices
                    top_cats.append({
                        "category": cat_name,
                        "confidence": c,
                        "is_non_crop": is_nc,
                    })
                    if rank == 0:
                        top_1_name = cat_name
                        top_1_conf = c
                        top_1_is_non_crop = is_nc

                    if is_nc:
                        non_crop_prob += c

            except Exception as exc:
                logger.warning("MobileNet inference failed in CropRelevanceService: %s", exc)

        non_crop_prob = round(non_crop_prob, 4)

        metrics = {
            "green_fraction": green_fraction,
            "necrotic_fraction": necrotic_fraction,
            "has_chlorophyll": has_chlorophyll,
            "non_crop_probability": non_crop_prob,
            "top_prediction": top_1_name,
            "top_confidence": top_1_conf,
        }

        # 3. Decision Gate
        # Rule 1: Explicit Non-Crop Object Detected (Hardware, Electronics, Appliances, Vehicles, Furniture)
        is_explicit_non_crop = (
            (top_1_is_non_crop and top_1_conf >= 0.10)
            or (non_crop_prob >= 0.25)
        )

        if is_explicit_non_crop:
            logger.info(
                "[DISEASE] relevance result: REJECTED as IRRELEVANT_IMAGE (top='%s' [%.2f], non_crop=%.2f, green=%.4f)",
                top_1_name, top_1_conf, non_crop_prob, green_fraction,
            )
            return CropRelevanceResult(
                is_relevant=False,
                state="IRRELEVANT_IMAGE",
                message="The uploaded image does not appear to contain the selected crop.",
                message_kn="ಈ ಚಿತ್ರವು ಆಯ್ಕೆ ಮಾಡಿದ ಬೆಳೆಗೆ ಸಂಬಂಧಿಸಿದಂತೆ ಕಾಣುತ್ತಿಲ್ಲ.",
                crop_code=crop_info["code"],
                crop_name_en=crop_info["name_en"],
                crop_name_kn=crop_info["name_kn"],
                metrics=metrics,
                top_categories=top_cats,
            )

        # Rule 2: Complete Absence of Vegetative Chlorophyll
        # A crop leaf MUST have vegetative tissue. If there is 0% chlorophyll green,
        # necrotic/brown tones are just a wooden desk, floor, box, or wall.
        if not has_chlorophyll and green_fraction < 0.015:
            logger.info(
                "[DISEASE] relevance result: REJECTED as IRRELEVANT_IMAGE (no chlorophyll vegetative tissue detected: green=%.4f)",
                green_fraction,
            )
            return CropRelevanceResult(
                is_relevant=False,
                state="IRRELEVANT_IMAGE",
                message="The uploaded image does not appear to contain the selected crop.",
                message_kn="ಈ ಚಿತ್ರವು ಆಯ್ಕೆ ಮಾಡಿದ ಬೆಳೆಗೆ ಸಂಬಂಧಿಸಿದಂತೆ ಕಾಣುತ್ತಿಲ್ಲ.",
                crop_code=crop_info["code"],
                crop_name_en=crop_info["name_en"],
                crop_name_kn=crop_info["name_kn"],
                metrics=metrics,
                top_categories=top_cats,
            )

        # Passed semantic relevance!
        logger.info(
            "[DISEASE] relevance result: PASSED (crop='%s', green=%.4f, non_crop_prob=%.4f)",
            norm_crop, green_fraction, non_crop_prob,
        )
        return CropRelevanceResult(
            is_relevant=True,
            state="VALID_IMAGE",
            message="Image successfully verified as relevant crop foliage.",
            message_kn="ಚಿತ್ರವು ಕೃಷಿ ಬೆಳೆಗೆ ಸಂಬಂಧಿಸಿದೆ ಎಂದು ದೃಢೀಕರಿಸಲಾಗಿದೆ.",
            crop_code=crop_info["code"],
            crop_name_en=crop_info["name_en"],
            crop_name_kn=crop_info["name_kn"],
            metrics=metrics,
            top_categories=top_cats,
        )

    def evaluate_crop_compatibility(
        self,
        requested_crop: str,
        cross_predictions: Optional[Dict[str, float]] = None,
    ) -> Tuple[bool, str, str, str]:
        """Check whether the image is compatible with the farmer-selected crop.
        
        If requested crop model confidence is extremely low (< 0.25) while another
        specialized crop model is overwhelmingly confident (> 0.80), flags CROP_MISMATCH.
        
        Returns:
            Tuple of (is_compatible, state, message_en, message_kn)
        """
        norm_crop = requested_crop.strip().lower().replace("-", "_").replace(" ", "_")
        crop_info = CROP_METADATA.get(norm_crop, {
            "code": norm_crop,
            "name_en": norm_crop.title(),
            "name_kn": norm_crop,
        })

        if not cross_predictions or len(cross_predictions) <= 1:
            return True, "VALID_IMAGE", "Crop compatibility verified.", "ಬೆಳೆ ಹೊಂದಾಣಿಕೆ ದೃಢಪಟ್ಟಿದೆ."

        req_conf = cross_predictions.get(norm_crop, 0.0)
        max_other_crop = ""
        max_other_conf = 0.0

        for other_crop, conf in cross_predictions.items():
            if other_crop != norm_crop and conf > max_other_conf:
                max_other_conf = conf
                max_other_crop = other_crop

        if req_conf < 0.25 and max_other_conf >= 0.80:
            other_info = CROP_METADATA.get(max_other_crop, {"name_en": max_other_crop.title(), "name_kn": max_other_crop})
            logger.info(
                "[DISEASE] crop compatibility: CROP_MISMATCH (requested='%s' [%.2f], but matched='%s' [%.2f])",
                norm_crop, req_conf, max_other_crop, max_other_conf,
            )
            msg_en = f"The selected crop ({crop_info['name_en']}) does not match the uploaded image (appears to be {other_info['name_en']})."
            msg_kn = f"ಆಯ್ಕೆ ಮಾಡಿದ ಬೆಳೆ ಮತ್ತು ಚಿತ್ರ ಹೊಂದಿಕೆಯಾಗುತ್ತಿಲ್ಲ."
            return False, "CROP_MISMATCH", msg_en, msg_kn

        return True, "VALID_IMAGE", "Crop compatibility verified.", "ಬೆಳೆ ಹೊಂದಾಣಿಕೆ ದೃಢಪಟ್ಟಿದೆ."


def get_crop_relevance_service() -> CropRelevanceService:
    """Singleton provider for CropRelevanceService."""
    if CropRelevanceService._instance is None:
        CropRelevanceService._instance = CropRelevanceService()
    return CropRelevanceService._instance
