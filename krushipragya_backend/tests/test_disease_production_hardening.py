"""Production Hardening Regression Test Suite for Crop Health Image Diagnosis + Qwen.

Verifies all 20 required production regression scenarios:
1. Valid disease image
2. Strong model prediction (>= 0.70)
3. Low-confidence prediction (< 0.70) -> UNCERTAIN_IMAGE
4. 55% healthy prediction -> UNCERTAIN_IMAGE
5. 64% disease prediction -> UNCERTAIN_IMAGE
6. Irrelevant image rejected
7. Low-quality image rejected (< 64x64)
8. Crop mismatch detected
9. Existing Koleroga prediction preserved with ICAR metadata
10. Yellow Leaf Disease mapping verified
11. Phytoplasma metadata is PHYTOPLASMA (NOT VIRAL)
12. Qwen success with structured Kannada output
13. Qwen unavailable -> deterministic fallback
14. Qwen timeout -> deterministic fallback
15. Invalid Qwen JSON -> deterministic fallback
16. Qwen cannot change disease (authoritative ML fields preserved)
17. Qwen invents chemical/treatment -> rejected and falls back
18. Qwen cannot change confidence (PyTorch softmax preserved)
19. Deterministic fallback produces verified Kannada content
20. Existing API compatibility for /api/v1/disease/predict & /api/ai/predict
"""
import io
import json
from unittest.mock import MagicMock, patch
import pytest
from fastapi.testclient import TestClient
from PIL import Image

from app.main import app
from app.services.disease_detection_service import (
    DiseaseDetectionService,
    VerificationRejectionError,
    CONFIRMED_DIAGNOSIS_THRESHOLD,
    HEALTHY_CONFIDENCE_THRESHOLD,
)
from app.services.disease_explanation_service import (
    DiseaseExplanationService,
    get_disease_explanation_service,
)
from app.services.disease_kb import get_disease_info, _DISEASE_KB
from app.services.llm_provider import (
    LLMConnectionError,
    LLMTimeoutError,
    LLMProviderError,
)

client = TestClient(app)


def make_test_image(size=(224, 224), color=(60, 150, 70)) -> bytes:
    """Helper to generate a valid in-memory test image."""
    img = Image.new("RGB", size, color=color)
    buf = io.BytesIO()
    img.save(buf, format="JPEG")
    return buf.getvalue()


# ==============================================================================
# 1. Valid disease image
# ==============================================================================

def test_1_valid_disease_image_api():
    """Scenario 1: Valid disease image through /api/v1/disease/predict."""
    img_bytes = make_test_image()
    response = client.post(
        "/api/v1/disease/predict",
        data={"crop": "arecanut"},
        files={"file": ("leaf.jpg", img_bytes, "image/jpeg")},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["crop"] == "arecanut"
    assert "confidence" in data
    assert "status" in data
    assert "state" in data
    assert "verification_state" in data
    assert "generated_at" in data
    assert "explanation_kn" in data


# ==============================================================================
# 20. Existing API compatibility for /api/v1/disease/predict & /api/ai/predict
# ==============================================================================

def test_20_existing_api_compatibility():
    """Scenario 20: Both /api/v1/disease/predict and /api/ai/predict return consistent contract."""
    img_bytes = make_test_image()
    for endpoint in ["/api/v1/disease/predict", "/api/ai/predict"]:
        response = client.post(
            endpoint,
            data={"crop": "arecanut"},
            files={"file": ("leaf.jpg", img_bytes, "image/jpeg")},
        )
        assert response.status_code == 200
        data = response.json()
        assert "predicted_class" in data
        assert "confidence" in data
        assert "status" in data
        assert "state" in data
        assert "disease" in data
        assert "approved_actions" in data


# ==============================================================================
# 2. Strong model prediction (>= 0.70)
# ==============================================================================

def test_2_strong_model_prediction():
    """Scenario 2: A prediction with >= 0.70 confidence produces a confirmed diagnosis."""
    service = DiseaseDetectionService()
    img_bytes = make_test_image()

    # Mock model inference to return strong probability 0.85
    with patch.object(service, "get_or_load_model") as mock_load:
        mock_model = MagicMock()
        # Mock logits giving 85% to class 0 (Mahali_Koleroga)
        mock_logits = MagicMock()
        mock_load.return_value = (mock_model, ["Mahali_Koleroga", "Healthy", "stem_bleeding", "bud_borer", "stem_cracking", "yellow_leaf_disease"])

        with patch("torch.no_grad"), patch("torch.softmax") as mock_softmax:
            import torch
            mock_softmax.return_value = [torch.tensor([0.85, 0.05, 0.03, 0.03, 0.02, 0.02])]

            result = service.predict("arecanut", img_bytes, verify_input=False, enforce_confidence_gate=True)

            assert result.status == "success"
            assert result.state == "VALID_IMAGE"
            assert result.verification_state == "AI_ANALYSED"
            assert result.predicted_class == "Mahali_Koleroga"
            assert result.confidence == 0.85
            assert result.low_confidence is False
            assert result.disease == "Koleroga / Mahali (Fruit Rot)"


# ==============================================================================
# 3. Low-confidence prediction (< 0.70) -> UNCERTAIN_IMAGE
# ==============================================================================

def test_3_low_confidence_prediction():
    """Scenario 3: A weak prediction (< 0.70) must become UNCERTAIN_IMAGE."""
    service = DiseaseDetectionService()
    img_bytes = make_test_image()

    with patch.object(service, "get_or_load_model") as mock_load:
        mock_model = MagicMock()
        mock_load.return_value = (mock_model, ["Mahali_Koleroga", "Healthy", "stem_bleeding", "bud_borer", "stem_cracking", "yellow_leaf_disease"])

        with patch("torch.no_grad"), patch("torch.softmax") as mock_softmax:
            import torch
            mock_softmax.return_value = [torch.tensor([0.48, 0.30, 0.10, 0.05, 0.04, 0.03])]

            result = service.predict("arecanut", img_bytes, verify_input=False, enforce_confidence_gate=True)

            assert result.status == "uncertain"
            assert result.state == "UNCERTAIN_IMAGE"
            assert result.verification_state == "UNCERTAIN_IMAGE"
            assert result.predicted_class is None
            assert result.diagnosis is None
            assert result.disease is None
            assert result.low_confidence is True
            assert "ಖಚಿತವಾಗಿ ಗುರುತಿಸಲಾಗಲಿಲ್ಲ" in result.explanation_kn


# ==============================================================================
# 4. 55% Healthy prediction -> UNCERTAIN_IMAGE
# ==============================================================================

def test_4_55_pct_healthy_prediction_becomes_uncertain():
    """Scenario 4: 55% Healthy Cardamom must NOT produce 'Your crop is healthy'; becomes UNCERTAIN_IMAGE."""
    service = DiseaseDetectionService()
    img_bytes = make_test_image()

    with patch.object(service, "get_or_load_model") as mock_load:
        mock_model = MagicMock()
        mock_load.return_value = (mock_model, ["Healthy_1000", "Blight1000", "Phylosticta_LS_1000"])

        with patch("torch.no_grad"), patch("torch.softmax") as mock_softmax:
            import torch
            mock_softmax.return_value = [torch.tensor([0.55, 0.25, 0.20])]

            result = service.predict("cardamom", img_bytes, verify_input=False, enforce_confidence_gate=True)

            assert result.status == "uncertain"
            assert result.state == "UNCERTAIN_IMAGE"
            assert result.predicted_class is None
            assert result.diagnosis is None
            assert result.confidence == 0.55
            assert "ಖಚಿತವಾಗಿ ಗುರುತಿಸಲಾಗಲಿಲ್ಲ" in result.explanation_kn


# ==============================================================================
# 5. 64% Disease prediction -> UNCERTAIN_IMAGE
# ==============================================================================

def test_5_64_pct_disease_prediction_becomes_uncertain():
    """Scenario 5: 64% Yellow Leaf Disease must NOT be presented as a reliable diagnosis; becomes UNCERTAIN_IMAGE."""
    service = DiseaseDetectionService()
    img_bytes = make_test_image()

    with patch.object(service, "get_or_load_model") as mock_load:
        mock_model = MagicMock()
        mock_load.return_value = (mock_model, ["yellow_leaf_disease", "Healthy", "Mahali_Koleroga", "bud_borer", "stem_bleeding", "stem_cracking"])

        with patch("torch.no_grad"), patch("torch.softmax") as mock_softmax:
            import torch
            mock_softmax.return_value = [torch.tensor([0.64, 0.20, 0.10, 0.03, 0.02, 0.01])]

            result = service.predict("arecanut", img_bytes, verify_input=False, enforce_confidence_gate=True)

            assert result.status == "uncertain"
            assert result.state == "UNCERTAIN_IMAGE"
            assert result.predicted_class is None
            assert result.diagnosis is None
            assert result.confidence == 0.64
            assert "ಖಚಿತವಾಗಿ ಗುರುತಿಸಲಾಗಲಿಲ್ಲ" in result.explanation_kn


# ==============================================================================
# 6. Irrelevant image rejected
# ==============================================================================

def test_6_irrelevant_image_rejected():
    """Scenario 6: Completely white/blank image fails leaf relevance check."""
    white_img = Image.new("RGB", (256, 256), color=(255, 255, 255))
    buf = io.BytesIO()
    white_img.save(buf, format="JPEG")
    white_bytes = buf.getvalue()

    response = client.post(
        "/api/v1/disease/predict",
        data={"crop": "arecanut"},
        files={"file": ("laptop.jpg", white_bytes, "image/jpeg")},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "rejected"
    assert data["input_verified"] is False


# ==============================================================================
# 7. Low-quality image rejected (< 64x64)
# ==============================================================================

def test_7_low_quality_image_rejected():
    """Scenario 7: Micro image (32x32) rejected with 400."""
    micro_img = Image.new("RGB", (32, 32), color=(50, 150, 50))
    buf = io.BytesIO()
    micro_img.save(buf, format="JPEG")
    micro_bytes = buf.getvalue()

    response = client.post(
        "/api/v1/disease/predict",
        data={"crop": "arecanut"},
        files={"file": ("tiny.jpg", micro_bytes, "image/jpeg")},
    )
    assert response.status_code == 400
    data = response.json()
    assert data["status"] == "rejected"
    assert data["reason_code"] in ("LOW_IMAGE_QUALITY", "IMAGE_TOO_SMALL", "LOW_QUALITY")


# ==============================================================================
# 8. Crop mismatch detected
# ==============================================================================

def test_8_crop_mismatch_detected():
    """Scenario 8: When selected crop is completely mismatched, detects CROP_MISMATCH."""
    service = DiseaseDetectionService()
    img_bytes = make_test_image()

    with patch.object(service, "get_or_load_model") as mock_load:
        mock_model = MagicMock()
        mock_load.return_value = (mock_model, ["Mahali_Koleroga", "Healthy", "stem_bleeding", "bud_borer", "stem_cracking", "yellow_leaf_disease"])

        # Populate another model in cache
        other_mock = MagicMock()
        service._models["coconut"] = (other_mock, ["Bud Rot", "Healthy", "Leaf Rot", "Gray Leaf Spot", "Stem Bleeding"])

        with patch("torch.no_grad"), patch("torch.softmax") as mock_softmax:
            import torch
            # Current crop has 0.15 confidence, other crop (coconut) has 0.92 confidence
            mock_softmax.side_effect = [
                torch.tensor([[0.15, 0.20, 0.15, 0.15, 0.15, 0.20]]),  # arecanut
                torch.tensor([[0.92, 0.02, 0.02, 0.02, 0.02]]),         # coconut
            ]

            with pytest.raises(VerificationRejectionError) as exc_info:
                service.predict("arecanut", img_bytes, verify_input=False, enforce_confidence_gate=True)

            assert exc_info.value.reason_code == "CROP_MISMATCH"


# ==============================================================================
# 9. Existing Koleroga prediction preserved with ICAR metadata
# ==============================================================================

def test_9_existing_koleroga_prediction_preserved():
    """Scenario 9: Koleroga with 0.73 confidence retains exact ML prediction & verified ICAR metadata."""
    service = DiseaseDetectionService()
    img_bytes = make_test_image()

    with patch.object(service, "get_or_load_model") as mock_load:
        mock_model = MagicMock()
        mock_load.return_value = (mock_model, ["Mahali_Koleroga", "Healthy", "stem_bleeding", "bud_borer", "stem_cracking", "yellow_leaf_disease"])

        with patch("torch.no_grad"), patch("torch.softmax") as mock_softmax:
            import torch
            mock_softmax.return_value = [torch.tensor([0.73, 0.10, 0.05, 0.05, 0.04, 0.03])]

            result = service.predict("arecanut", img_bytes, verify_input=False, enforce_confidence_gate=True)

            assert result.status == "success"
            assert result.predicted_class == "Mahali_Koleroga"
            assert result.confidence == 0.73
            assert result.disease == "Koleroga / Mahali (Fruit Rot)"
            assert result.disease_name_kn == "ಕೊಳೆ ರೋಗ (ಮಹಾಳಿ)"
            assert result.knowledge_base_reference == "ICAR-CPCRI Kasaragod"
            assert result.disease_info.scientific_name == "Phytophthora meadii"
            assert result.disease_info.category == "FUNGAL"


# ==============================================================================
# 10. Yellow Leaf Disease mapping verified
# ==============================================================================

def test_10_yellow_leaf_disease_mapping():
    """Scenario 10: Verified KB mapping for Yellow Leaf Disease."""
    kb_item = get_disease_info("arecanut", "yellow_leaf_disease")
    assert kb_item is not None
    assert kb_item.disease_name_en == "Yellow Leaf Disease (YLD)"
    assert kb_item.disease_name_kn == "ಹಳದಿ ಎಲೆ ರೋಗ"
    assert "Proutista moesta" in kb_item.scientific_name


# ==============================================================================
# 11. Phytoplasma metadata is PHYTOPLASMA (NOT VIRAL)
# ==============================================================================

def test_11_phytoplasma_metadata_not_viral():
    """Scenario 11: Yellow Leaf Disease must NOT be classified as VIRAL; it is PHYTOPLASMA."""
    kb_item = get_disease_info("arecanut", "yellow_leaf_disease")
    assert kb_item is not None
    assert kb_item.category == "PHYTOPLASMA"
    assert kb_item.category != "VIRAL"
    assert "Phytoplasma" in kb_item.scientific_name


# ==============================================================================
# 12. Qwen success with structured Kannada output
# ==============================================================================

def test_12_qwen_success_structured_output():
    """Scenario 12: Qwen generates valid structured Kannada output matching schema."""
    kb_item = get_disease_info("arecanut", "Mahali_Koleroga")
    service = DiseaseExplanationService()

    valid_qwen_json = json.dumps({
        "title_kn": "ಅಡಿಕೆ - ಕೊಳೆ ರೋಗ (ಮಹಾಳಿ)",
        "summary_kn": "ಅಡಿಕೆ ಬೆಳೆಯಲ್ಲಿ ಕೊಳೆ ರೋಗದ ಲಕ್ಷಣಗಳು ಕಂಡುಬಂದಿವೆ (ವಿಶ್ವಾಸಾರ್ಹತೆ: 73.0%). ಮುಂಗಾರು ಮಳೆಯಿಂದಾಗಿ ಕಾಯಿ ಉದುರುವ ಸಂಭವವಿದೆ.",
        "actions_kn": [
            "ಮುಂಗಾರು ಮಳೆ ಆರಂಭಕ್ಕೂ ಮುನ್ನ ಅಡಿಕೆ ಗೊಂಚಲುಗಳಿಗೆ 1% ಬೋರ್ಡೋ ಮಿಶ್ರಣ ಸಿಂಪಡಿಸಿ.",
            "ಬಿದ್ದ ಕೊಳೆ ಅಡಿಕೆಗಳನ್ನು ಆರಿಸಿ ನಾಶಪಡಿಸಿ."
        ],
        "timing_kn": "ಕೂಡಲೇ ಅಥವಾ ಮಳೆ ಬಿಡುವಿನ ವೇಳೆಯಲ್ಲಿ",
        "reason_kn": "ಮಾದರಿ ವಿಶ್ವಾಸಾರ್ಹತೆ: 73.0% | ರೋಗಕಾರಕ: Phytophthora meadii (FUNGAL)"
    })

    mock_llm = MagicMock()
    mock_llm.generate.return_value = valid_qwen_json
    service._llm = mock_llm

    result = service.explain_diagnosis(
        crop_code="arecanut",
        crop_name_en="Arecanut",
        crop_name_kn="ಅಡಿಕೆ",
        raw_class="Mahali_Koleroga",
        raw_confidence=0.73,
        kb_entry=kb_item,
    )

    assert result.is_llm_generated is True
    assert result.fallback_used is False
    assert result.title_kn == "ಅಡಿಕೆ - ಕೊಳೆ ರೋಗ (ಮಹಾಳಿ)"
    assert len(result.actions_kn) == 2


# ==============================================================================
# 13. Qwen unavailable -> deterministic fallback
# ==============================================================================

def test_13_qwen_unavailable_deterministic_fallback():
    """Scenario 13: When Ollama/Qwen is unavailable, seamlessly falls back to deterministic KB."""
    kb_item = get_disease_info("arecanut", "Mahali_Koleroga")
    service = DiseaseExplanationService()

    mock_llm = MagicMock()
    mock_llm.generate.side_effect = LLMConnectionError("Ollama connection refused at localhost:11434")
    service._llm = mock_llm

    result = service.explain_diagnosis(
        crop_code="arecanut",
        crop_name_en="Arecanut",
        crop_name_kn="ಅಡಿಕೆ",
        raw_class="Mahali_Koleroga",
        raw_confidence=0.73,
        kb_entry=kb_item,
    )

    assert result.is_llm_generated is False
    assert result.fallback_used is True
    assert "ಕೊಳೆ ರೋಗ (ಮಹಾಳಿ)" in result.title_kn
    assert "Phytophthora meadii" in result.reason_kn
    assert len(result.actions_kn) > 0


# ==============================================================================
# 14. Qwen timeout -> deterministic fallback
# ==============================================================================

def test_14_qwen_timeout_deterministic_fallback():
    """Scenario 14: When Qwen times out, returns deterministic fallback without hanging."""
    kb_item = get_disease_info("arecanut", "Mahali_Koleroga")
    service = DiseaseExplanationService()

    mock_llm = MagicMock()
    mock_llm.generate.side_effect = LLMTimeoutError("Ollama request timed out after 6.0s")
    service._llm = mock_llm

    result = service.explain_diagnosis(
        crop_code="arecanut",
        crop_name_en="Arecanut",
        crop_name_kn="ಅಡಿಕೆ",
        raw_class="Mahali_Koleroga",
        raw_confidence=0.73,
        kb_entry=kb_item,
    )

    assert result.is_llm_generated is False
    assert result.fallback_used is True
    assert "ಕೊಳೆ ರೋಗ (ಮಹಾಳಿ)" in result.title_kn


# ==============================================================================
# 15. Invalid Qwen JSON -> deterministic fallback
# ==============================================================================

def test_15_invalid_qwen_json_deterministic_fallback():
    """Scenario 15: Broken JSON or non-JSON text from Qwen is safely rejected."""
    kb_item = get_disease_info("arecanut", "Mahali_Koleroga")
    service = DiseaseExplanationService()

    mock_llm = MagicMock()
    mock_llm.generate.return_value = "This is not JSON at all. I think this is Koleroga."
    service._llm = mock_llm

    result = service.explain_diagnosis(
        crop_code="arecanut",
        crop_name_en="Arecanut",
        crop_name_kn="ಅಡಿಕೆ",
        raw_class="Mahali_Koleroga",
        raw_confidence=0.73,
        kb_entry=kb_item,
    )

    assert result.is_llm_generated is False
    assert result.fallback_used is True


# ==============================================================================
# 16. Qwen cannot change disease (authoritative ML fields preserved)
# ==============================================================================

def test_16_qwen_cannot_change_disease():
    """Scenario 16: Top-level API response fields strictly reflect ML + KB, never overwritten by Qwen."""
    service = DiseaseDetectionService()
    img_bytes = make_test_image()

    with patch.object(service, "get_or_load_model") as mock_load:
        mock_model = MagicMock()
        mock_load.return_value = (mock_model, ["Mahali_Koleroga", "Healthy", "stem_bleeding", "bud_borer", "stem_cracking", "yellow_leaf_disease"])

        with patch("torch.no_grad"), patch("torch.softmax") as mock_softmax:
            import torch
            mock_softmax.return_value = [torch.tensor([0.75, 0.10, 0.05, 0.04, 0.03, 0.03])]

            # Even if explanation service returns something else
            mock_expl = MagicMock()
            mock_expl.summary_kn = "ಏನೋ ವಿವರಣೆ"
            mock_expl.actions_kn = ["ಕ್ರಮ 1"]
            mock_expl.is_llm_generated = True
            mock_expl.fallback_used = False

            with patch("app.services.disease_detection_service.get_disease_explanation_service") as mock_get_expl:
                mock_get_expl.return_value.explain_diagnosis.return_value = mock_expl

                result = service.predict("arecanut", img_bytes, verify_input=False, enforce_confidence_gate=True)

                # Authoritative fields must NOT change
                assert result.predicted_class == "Mahali_Koleroga"
                assert result.disease == "Koleroga / Mahali (Fruit Rot)"
                assert result.confidence == 0.75
                assert result.crop == "arecanut"


# ==============================================================================
# 17. Qwen invents chemical/treatment -> rejected and falls back
# ==============================================================================

def test_17_qwen_invents_treatment_rejected():
    """Scenario 17: If Qwen mentions an unapproved harsh chemical, output validation rejects it."""
    kb_item = get_disease_info("arecanut", "Mahali_Koleroga")
    service = DiseaseExplanationService()

    hallucinated_qwen_json = json.dumps({
        "title_kn": "ಅಡಿಕೆ - ಕೊಳೆ ರೋಗ",
        "summary_kn": "ಅಡಿಕೆ ಬೆಳೆಯಲ್ಲಿ ಕೊಳೆ ರೋಗ ಕಂಡುಬಂದಿದೆ.",
        "actions_kn": [
            "Use heavy dose of Chlorpyrifos 20 EC @ 50ml/L immediately!",  # Unapproved harsh chemical & absurd dosage
        ],
        "timing_kn": "ಕೂಡಲೇ",
        "reason_kn": "ಕಾರಣ: ಶಿಲೀಂಧ್ರ"
    })

    mock_llm = MagicMock()
    mock_llm.generate.return_value = hallucinated_qwen_json
    service._llm = mock_llm

    result = service.explain_diagnosis(
        crop_code="arecanut",
        crop_name_en="Arecanut",
        crop_name_kn="ಅಡಿಕೆ",
        raw_class="Mahali_Koleroga",
        raw_confidence=0.73,
        kb_entry=kb_item,
    )

    # Validation must reject and fall back to deterministic content
    assert result.is_llm_generated is False
    assert result.fallback_used is True
    # The hallucinated chemical must NOT be in the actions
    for action in result.actions_kn:
        assert "chlorpyrifos" not in action.lower()


# ==============================================================================
# 18. Qwen cannot change confidence (PyTorch softmax preserved)
# ==============================================================================

def test_18_qwen_cannot_change_confidence():
    """Scenario 18: Exact PyTorch softmax float confidence is preserved in API response."""
    service = DiseaseDetectionService()
    img_bytes = make_test_image()

    with patch.object(service, "get_or_load_model") as mock_load:
        mock_model = MagicMock()
        mock_load.return_value = (mock_model, ["Mahali_Koleroga", "Healthy", "stem_bleeding", "bud_borer", "stem_cracking", "yellow_leaf_disease"])

        with patch("torch.no_grad"), patch("torch.softmax") as mock_softmax:
            import torch
            mock_softmax.return_value = [torch.tensor([0.7345, 0.1000, 0.0500, 0.0500, 0.0400, 0.0255])]

            result = service.predict("arecanut", img_bytes, verify_input=False, enforce_confidence_gate=True)

            assert result.confidence == 0.7345


# ==============================================================================
# 19. Deterministic fallback produces verified Kannada content
# ==============================================================================

def test_19_deterministic_fallback_quality():
    """Scenario 19: Deterministic fallback creates grammatically sound Kannada content from KB."""
    kb_item = get_disease_info("arecanut", "yellow_leaf_disease")
    service = DiseaseExplanationService()

    approved_facts = service.build_approved_facts(
        crop_code="arecanut",
        crop_name_en="Arecanut",
        crop_name_kn="ಅಡಿಕೆ",
        raw_class="yellow_leaf_disease",
        raw_confidence=0.78,
        kb_entry=kb_item,
    )

    fallback = service.generate_deterministic_fallback(approved_facts, kb_item)
    assert fallback.is_llm_generated is False
    assert fallback.fallback_used is True
    assert "ಅಡಿಕೆ - ಹಳದಿ ಎಲೆ ರೋಗ" in fallback.title_kn
    assert "ಹಳದಿ ಎಲೆ ರೋಗ" in fallback.summary_kn
    assert "Phytoplasma" in fallback.reason_kn
    assert len(fallback.actions_kn) > 0
