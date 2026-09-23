from unittest.mock import MagicMock
import pytest

from app.models.advisory_rule import AdvisoryRule
from app.models.crop import Crop
from app.services.weather_rule_engine import (
    WeatherMetrics,
    AdvisoryMatch,
    evaluate_rule,
    evaluate_rules_for_crop,
    normalize_crop_name,
)


@pytest.fixture
def rule_1_koleroga():
    return AdvisoryRule(
        id=1,
        crop="Arecanut",
        risk_name="Koleroga Weather Risk Context",
        risk_level="HIGH",
        condition_type="WEATHER_THRESHOLD",
        condition_config={
            "min_rainfall_mm_48h": 70.0,
            "min_humidity_pct": 85.0,
            "min_cloudy_days_streak": 3,
            "risk_context": "Koleroga",
            "risk_factors": [
                "recent heavy rainfall (>70 mm/48h)",
                "high sustained humidity (>85%)",
                "persistent cloudy streak (>=3 days)",
            ],
        },
        advisory_en="Favorable for fungal spore dispersal. Clear drainage channels.",
        advisory_kn="ಕೊಳೆರೋಗ ಹರಡಲು ಪೂರಕವಾದ ತೇವಾಂಶ. ಬಸಿಗಾಲುವೆಗಳನ್ನು ಸ್ವಚ್ಛವಾಗಿಡಿ.",
        source_name="UAHS Shivamogga",
        source_reference="Agromet Advisory",
        is_demo_rule=True,
        active=True,
        version=1,
    )


@pytest.fixture
def rule_2_bud_rot():
    return AdvisoryRule(
        id=2,
        crop="Arecanut",
        risk_name="Bud Rot Weather Risk Context",
        risk_level="MODERATE",
        condition_type="WEATHER_THRESHOLD",
        condition_config={
            "min_rainfall_mm_48h": 30.0,
            "min_humidity_pct": 80.0,
            "min_cloudy_days_streak": 3,
            "risk_context": "Bud Rot",
            "risk_factors": [
                "moderate persistent rainfall (>=30 mm/48h)",
                "elevated canopy humidity (>=80%)",
                "cloudy damp spell (>=3 days)",
            ],
        },
        advisory_en="Check palm crowns during rain breaks.",
        advisory_kn="ಅಡಿಕೆ ಮರಗಳ ಸುಳಿ ಭಾಗವನ್ನು ಗಮನಿಸಿ.",
        source_name="ICAR-CPCRI",
        source_reference="CPCRI Guidelines",
        is_demo_rule=True,
        active=True,
        version=1,
    )


@pytest.fixture
def rule_3_waterlogging():
    return AdvisoryRule(
        id=3,
        crop="Arecanut",
        risk_name="Heavy Rainfall Waterlogging Risk Context",
        risk_level="HIGH",
        condition_type="WEATHER_THRESHOLD",
        condition_config={
            "min_rainfall_mm_48h": 100.0,
            "risk_context": "Waterlogging",
            "risk_factors": [
                "extreme rainfall accumulation (>100 mm/48h)",
            ],
        },
        advisory_en="Elevated risk of soil saturation and water stagnation.",
        advisory_kn="ಮುಖ್ಯ ಚರಂಡಿಗಳಲ್ಲಿ ನೀರು ಸರಾಗವಾಗಿ ಹರಿಯುವಂತೆ ನೋಡಿಕೊಳ್ಳಿ.",
        source_name="KSNDMC",
        source_reference="KSNDMC Advisory",
        is_demo_rule=True,
        active=True,
        version=1,
    )


@pytest.fixture
def rule_4_dry_window():
    return AdvisoryRule(
        id=4,
        crop="Arecanut",
        risk_name="Post-Monsoon Dry Operational Window",
        risk_level="LOW",
        condition_type="WEATHER_THRESHOLD",
        condition_config={
            "max_rainfall_mm_48h": 5.0,
            "max_humidity_pct": 72.0,
            "min_temp_max_c": 28.0,
            "risk_context": "Dry Window",
            "risk_factors": [
                "negligible rainfall (<5 mm/48h)",
                "moderate relative humidity (<72%)",
                "clear daytime sunshine",
            ],
        },
        advisory_en="Favorable operational window for plantation maintenance and nut drying.",
        advisory_kn="ಅಡಿಕೆ ಕೊಯ್ಲು ಮತ್ತು ಕಣಗಳಲ್ಲಿ ಒಣಗಿಸುವಿಕೆಗೆ ಅನುಕೂಲಕರವಾಗಿದೆ.",
        source_name="Directorate of Horticulture, Karnataka",
        source_reference="Horticulture Guide",
        is_demo_rule=True,
        active=True,
        version=1,
    )


def test_rule_1_fully_matches(rule_1_koleroga):
    """Test 1: Rule 1 matches when rainfall >= 70, humidity >= 85, streak >= 3."""
    metrics = WeatherMetrics(
        rainfall_mm_48h=80.0,
        humidity_pct=90.0,
        cloudy_days_streak=4,
    )
    match = evaluate_rule(rule_1_koleroga, metrics)
    assert match is not None
    assert isinstance(match, AdvisoryMatch)
    assert match.rule_id == 1
    assert match.crop == "Arecanut"
    assert match.risk_name == "Koleroga Weather Risk Context"
    assert match.risk_level == "HIGH"
    assert match.risk_context == "Koleroga"
    assert len(match.matched_factors) == 3


def test_rule_1_fails_when_rainfall_low(rule_1_koleroga):
    """Test 2: Rule 1 does not match when rainfall_mm_48h is below threshold (50 < 70)."""
    metrics = WeatherMetrics(
        rainfall_mm_48h=50.0,
        humidity_pct=90.0,
        cloudy_days_streak=4,
    )
    match = evaluate_rule(rule_1_koleroga, metrics)
    assert match is None


def test_rule_1_missing_metric(rule_1_koleroga):
    """Test 3: Rule 1 does not match if a required metric is None (do not treat as zero)."""
    metrics = WeatherMetrics(
        rainfall_mm_48h=80.0,
        humidity_pct=90.0,
        cloudy_days_streak=None,
    )
    match = evaluate_rule(rule_1_koleroga, metrics)
    assert match is None


def test_rule_3_waterlogging_matches(rule_3_waterlogging):
    """Test 4: Rule 3 matches when rainfall_mm_48h >= 100."""
    metrics = WeatherMetrics(rainfall_mm_48h=120.0)
    match = evaluate_rule(rule_3_waterlogging, metrics)
    assert match is not None
    assert match.risk_context == "Waterlogging"
    assert match.risk_level == "HIGH"
    assert "extreme rainfall accumulation (>100 mm/48h)" in match.matched_factors


def test_rule_4_dry_window_matches(rule_4_dry_window):
    """Test 5: Rule 4 matches when rainfall <= 5, humidity <= 72, temp_max >= 28."""
    metrics = WeatherMetrics(
        rainfall_mm_48h=2.0,
        humidity_pct=65.0,
        temp_max_c=30.0,
    )
    match = evaluate_rule(rule_4_dry_window, metrics)
    assert match is not None
    assert match.risk_context == "Dry Window"
    assert match.risk_level == "LOW"


def test_rule_4_fails_when_rainfall_too_high(rule_4_dry_window):
    """Test 6: Rule 4 fails when rainfall exceeds max threshold (10 > 5)."""
    metrics = WeatherMetrics(
        rainfall_mm_48h=10.0,
        humidity_pct=65.0,
        temp_max_c=30.0,
    )
    match = evaluate_rule(rule_4_dry_window, metrics)
    assert match is None


def test_crop_normalization_variants():
    """Test 7: 'arecanut', 'Arecanut', 'ARECANUT' all resolve to 'Arecanut'."""
    mock_db = MagicMock()
    mock_crop = Crop(code="arecanut", name_en="Arecanut", name_kn="ಅಡಿಕೆ")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_crop

    assert normalize_crop_name(mock_db, "arecanut") == "Arecanut"
    assert normalize_crop_name(mock_db, "Arecanut") == "Arecanut"
    assert normalize_crop_name(mock_db, "ARECANUT") == "Arecanut"
    assert normalize_crop_name(mock_db, "  arecanut  ") == "Arecanut"


def test_inactive_rule_excluded(rule_1_koleroga):
    """Test 8: Inactive rule is excluded when active_only=True."""
    mock_db = MagicMock()
    mock_crop = Crop(code="arecanut", name_en="Arecanut", name_kn="ಅಡಿಕೆ")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_crop

    # Inactive rule
    inactive_rule = AdvisoryRule(
        id=99,
        crop="Arecanut",
        risk_name="Old Inactive Rule",
        risk_level="LOW",
        condition_type="WEATHER_THRESHOLD",
        condition_config={"min_rainfall_mm_48h": 10.0},
        advisory_en="Inactive",
        advisory_kn="ನಿಷ್ಕ್ರಿಯ",
        source_name="Old Source",
        is_demo_rule=True,
        active=False,
        version=1,
    )

    # When active_only=True, DB query filters active=True
    query_mock = mock_db.query.return_value.filter.return_value
    query_mock.filter.return_value.order_by.return_value.all.return_value = [rule_1_koleroga]

    metrics = WeatherMetrics(rainfall_mm_48h=80.0, humidity_pct=90.0, cloudy_days_streak=4)
    matches = evaluate_rules_for_crop(mock_db, "arecanut", metrics, active_only=True)

    assert len(matches) == 1
    assert matches[0].rule_id == 1


def test_multiple_matching_rules(rule_1_koleroga, rule_2_bud_rot, rule_3_waterlogging):
    """Test 9: When weather satisfies multiple rules, all matching rules are returned."""
    mock_db = MagicMock()
    mock_crop = Crop(code="arecanut", name_en="Arecanut", name_kn="ಅಡಿಕೆ")
    mock_db.query.return_value.filter.return_value.first.return_value = mock_crop

    query_mock = mock_db.query.return_value.filter.return_value
    query_mock.filter.return_value.order_by.return_value.all.return_value = [
        rule_1_koleroga,
        rule_2_bud_rot,
        rule_3_waterlogging,
    ]

    # Extreme rainfall: 110mm / 48h, 88% humidity, 4 cloudy days streak
    # Matches:
    # - Rule 1 Koleroga (>=70mm, >=85%, >=3 streak) -> MATCH
    # - Rule 2 Bud Rot (>=30mm, >=80%, >=3 streak) -> MATCH
    # - Rule 3 Waterlogging (>=100mm) -> MATCH
    metrics = WeatherMetrics(
        rainfall_mm_48h=110.0,
        humidity_pct=88.0,
        cloudy_days_streak=4,
    )
    matches = evaluate_rules_for_crop(mock_db, "arecanut", metrics, active_only=True)

    assert len(matches) == 3
    matched_ids = [m.rule_id for m in matches]
    assert matched_ids == [1, 2, 3]


def test_unknown_condition_key_handled_safely():
    """Test 10: Unknown condition keys in config are handled safely and do not match."""
    rule_with_unknown_operator = AdvisoryRule(
        id=999,
        crop="Arecanut",
        risk_name="Unknown Operator Rule",
        risk_level="HIGH",
        condition_type="WEATHER_THRESHOLD",
        condition_config={
            "min_rainfall_mm_48h": 20.0,
            "unknown_metric_threshold": 999.0,  # Unsupported key
            "risk_context": "Unknown",
        },
        advisory_en="Test",
        advisory_kn="ಪರೀಕ್ಷೆ",
        source_name="Test",
        is_demo_rule=True,
        active=True,
        version=1,
    )

    metrics = WeatherMetrics(rainfall_mm_48h=50.0)
    match = evaluate_rule(rule_with_unknown_operator, metrics)
    # Must explicitly return None and not match
    assert match is None
