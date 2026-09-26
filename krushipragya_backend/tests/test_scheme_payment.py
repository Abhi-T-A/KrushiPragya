"""Comprehensive test suite for Government Schemes Payment and Application Flow:
1. Free scheme
2. Official-fee scheme
3. Service-fee scheme
4. Official + service fee
5. Government-borne fee
6. Unknown fee
7. Correct total calculation
8. Frontend cannot alter amount
9. UTR submission
10. Duplicate UTR
11. Invalid amount
12. Unauthorized application payment
13. Unauthorized payment verification
14. Successful manual verification
15. Failed verification
16. Payment-required application
17. Free application bypasses payment
18. Existing scheme APIs remain working
19. Arbitrary identity headers cannot impersonate users
"""
from datetime import datetime, timedelta, timezone
from decimal import Decimal
import json
from typing import Dict
import uuid
import pytest
from fastapi import status
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.core.security import create_access_token
from app.database.base import Base
from app.database.connection import get_db
from app.main import app
from app.models.government import (
    GovernmentScheme,
    PaymentTransaction,
    SchemeApplication,
    SchemeSource,
    SchemeUserState,
)
from app.models.role import UserRole
from app.models.user_profile import UserProfile

# Isolated SQLite in-memory test database
test_engine = create_engine(
    "sqlite:///:memory:",
    poolclass=StaticPool,
    connect_args={"check_same_thread": False},
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)

Base.metadata.create_all(
    bind=test_engine,
    tables=[
        UserProfile.__table__,
        UserRole.__table__,
        GovernmentScheme.__table__,
        SchemeSource.__table__,
        SchemeUserState.__table__,
        SchemeApplication.__table__,
        PaymentTransaction.__table__,
    ],
)

client = TestClient(app)


def auth_header(user_id: uuid.UUID, email: str = "farmer@krushipragya.com") -> dict:
    """Mint a genuine Supabase JWT token header."""
    token = create_access_token(
        data={"sub": str(user_id), "email": email, "aud": "authenticated"},
        expires_delta=timedelta(hours=1),
    )
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def scheme_fixture():
    """Setup test fixture with schemes of each fee type and users with roles."""
    session = TestingSessionLocal()
    app.dependency_overrides[get_db] = lambda: session

    # 1. Create Users
    farmer_a_id = uuid.uuid4()
    farmer_a_prof = UserProfile(id=farmer_a_id, full_name="Farmer Ramesh", phone="9480111111")
    farmer_a_role = UserRole(user_id=farmer_a_id, role_code="FARMER", status="ACTIVE")
    session.add(farmer_a_prof)
    session.add(farmer_a_role)

    farmer_b_id = uuid.uuid4()
    farmer_b_prof = UserProfile(id=farmer_b_id, full_name="Farmer Suresh", phone="9480222222")
    farmer_b_role = UserRole(user_id=farmer_b_id, role_code="FARMER", status="ACTIVE")
    session.add(farmer_b_prof)
    session.add(farmer_b_role)

    admin_id = uuid.uuid4()
    admin_prof = UserProfile(id=admin_id, full_name="Admin Officer", phone="9480333333")
    admin_role = UserRole(user_id=admin_id, role_code="ADMIN", status="ACTIVE")
    session.add(admin_prof)
    session.add(admin_role)

    officer_id = uuid.uuid4()
    officer_prof = UserProfile(id=officer_id, full_name="Govt Verifier", phone="9480444444")
    officer_role = UserRole(user_id=officer_id, role_code="GOVERNMENT_OFFICER", status="ACTIVE")
    session.add(officer_prof)
    session.add(officer_role)

    now = datetime.now(timezone.utc)

    # 2. Schemes with distinct fee types
    # A. FREE Scheme
    scheme_free = GovernmentScheme(
        id=uuid.uuid4(),
        title="PM-KISAN Samman Nidhi",
        title_kn="ಪಿಎಂ-ಕಿಸಾನ್ ಸಮ್ಮಾನ್ ನಿಧಿ",
        description="Direct income support of Rs 6,000 per year.",
        category="Financial Assistance",
        eligibility="Small and marginal farmers",
        benefits="Rs. 6000 per year in 3 installments",
        fee_type="FREE",
        payment_required=False,
        official_fee=Decimal("0.00"),
        krushipragya_service_fee=Decimal("0.00"),
        fee_description="100% free government transfer. No application fee.",
        fee_source="pmkisan.gov.in Official Guidelines",
        fee_last_verified=now,
        status="ACTIVE",
    )
    session.add(scheme_free)

    # B. OFFICIAL_FEE Scheme
    scheme_official = GovernmentScheme(
        id=uuid.uuid4(),
        title="Arecanut Leaf Disease Compensation",
        title_kn="ಅಡಿಕೆ ಎಲೆ ಚುಕ್ಕೆ ರೋಗ ಪರಿಹಾರ",
        description="Relief fund for affected arecanut growers.",
        category="Subsidy",
        eligibility="Arecanut farmers in coastal Karnataka",
        benefits="Subsidy up to Rs 25,000 per acre",
        fee_type="OFFICIAL_FEE",
        payment_required=True,
        official_fee=Decimal("30.00"),
        krushipragya_service_fee=Decimal("0.00"),
        fee_description="Official state processing fee ₹30.",
        fee_source="Karnataka Raitha Mitra Notification 2026",
        fee_last_verified=now,
        status="ACTIVE",
    )
    session.add(scheme_official)

    # C. SERVICE_FEE Scheme
    scheme_service = GovernmentScheme(
        id=uuid.uuid4(),
        title="Solar Water Pump Assistance",
        title_kn="ಸೌರ ನೀರಾವರಿ ಪಂಪ್ ಸಹಾಯಧನ",
        description="Assisted document filing for PM-KUSUM solar pumps.",
        category="Equipment",
        eligibility="Farmers with irrigation wells",
        benefits="75% subsidy on solar pump installations",
        fee_type="SERVICE_FEE",
        payment_required=True,
        official_fee=Decimal("0.00"),
        krushipragya_service_fee=Decimal("15.00"),
        fee_description="KrushiPragya document preparation assistance fee ₹15.",
        fee_source="KrushiPragya Facilitation Desk",
        fee_last_verified=now,
        status="ACTIVE",
    )
    session.add(scheme_service)

    # D. OFFICIAL_PLUS_SERVICE_FEE Scheme
    scheme_combo = GovernmentScheme(
        id=uuid.uuid4(),
        title="Drip Irrigation Subsidy Scheme",
        title_kn="ಹನಿ ನೀರಾವರಿ ಸಹಾಯಧನ ಯೋಜನೆ",
        description="Micro-irrigation subsidy with assisted doorstep documentation.",
        category="Irrigation",
        eligibility="All registered landholding farmers",
        benefits="90% subsidy for SC/ST, 75% for general farmers",
        fee_type="OFFICIAL_PLUS_SERVICE_FEE",
        payment_required=True,
        official_fee=Decimal("30.00"),
        krushipragya_service_fee=Decimal("10.00"),
        fee_description="Official processing fee ₹30 + KrushiPragya assistance ₹10. Total ₹40.",
        fee_source="Pradhan Mantri Krishi Sinchayee Yojana Guidelines",
        fee_last_verified=now,
        status="ACTIVE",
    )
    session.add(scheme_combo)

    # E. GOVERNMENT_BORNE Scheme
    scheme_govt_borne = GovernmentScheme(
        id=uuid.uuid4(),
        title="Soil Health Card & Nutrient Advisory",
        title_kn="ಮಣ್ಣು ಆರೋಗ್ಯ ಕಾರ್ಡ್ ಯೋಜನೆ",
        description="Free soil testing and customized advisory.",
        category="Advisory",
        eligibility="All farmers",
        benefits="Free soil profile testing",
        fee_type="GOVERNMENT_BORNE",
        payment_required=False,
        official_fee=Decimal("0.00"),
        krushipragya_service_fee=Decimal("0.00"),
        fee_description="Testing costs borne by Department of Agriculture.",
        fee_source="National Mission on Sustainable Agriculture",
        fee_last_verified=now,
        status="ACTIVE",
    )
    session.add(scheme_govt_borne)

    # F. UNKNOWN Scheme (Unverified)
    scheme_unknown = GovernmentScheme(
        id=uuid.uuid4(),
        title="Unverified Pilot Organic Certification",
        title_kn="ಪರಿಶೀಲಿಸದ ಸಾವಯವ ಪ್ರಮಾಣೀಕರಣ",
        description="Proposed pilot scheme with unverified fee schedule.",
        category="Subsidy",
        eligibility="Organic growers",
        benefits="Certification subsidy",
        fee_type="UNKNOWN",
        payment_required=False,
        official_fee=None,
        krushipragya_service_fee=None,
        fee_description="Fee information needs verification.",
        fee_source=None,
        fee_last_verified=None,
        status="ACTIVE",
    )
    session.add(scheme_unknown)

    session.commit()

    yield {
        "session": session,
        "farmer_a_id": farmer_a_id,
        "farmer_b_id": farmer_b_id,
        "admin_id": admin_id,
        "officer_id": officer_id,
        "scheme_free": scheme_free,
        "scheme_official": scheme_official,
        "scheme_service": scheme_service,
        "scheme_combo": scheme_combo,
        "scheme_govt_borne": scheme_govt_borne,
        "scheme_unknown": scheme_unknown,
    }

    app.dependency_overrides.pop(get_db, None)


# ==============================================================================
# 1. Fee Types & Calculation Tests
# ==============================================================================

def test_scheme_fee_type_free(scheme_fixture):
    """Test 1: Free scheme reports 0 fees and payment_required=False."""
    scheme = scheme_fixture["scheme_free"]
    res = client.get(f"/api/v1/schemes/{scheme.id}")
    assert res.status_code == status.HTTP_200_OK
    data = res.json()
    assert "fee_info" in data
    fee = data["fee_info"]
    assert fee["fee_type"] == "FREE"
    assert fee["payment_required"] is False
    assert fee["official_fee"] == 0.0
    assert fee["krushipragya_service_fee"] == 0.0
    assert fee["total_payable"] == 0.0


def test_scheme_fee_type_official_fee(scheme_fixture):
    """Test 2: Scheme with official government fee only."""
    scheme = scheme_fixture["scheme_official"]
    res = client.get(f"/api/v1/schemes/{scheme.id}")
    assert res.status_code == status.HTTP_200_OK
    fee = res.json()["fee_info"]
    assert fee["fee_type"] == "OFFICIAL_FEE"
    assert fee["payment_required"] is True
    assert fee["official_fee"] == 30.0
    assert fee["krushipragya_service_fee"] == 0.0
    assert fee["total_payable"] == 30.0


def test_scheme_fee_type_service_fee(scheme_fixture):
    """Test 3: Scheme with KrushiPragya assistance fee only."""
    scheme = scheme_fixture["scheme_service"]
    res = client.get(f"/api/v1/schemes/{scheme.id}")
    assert res.status_code == status.HTTP_200_OK
    fee = res.json()["fee_info"]
    assert fee["fee_type"] == "SERVICE_FEE"
    assert fee["payment_required"] is True
    assert fee["official_fee"] == 0.0
    assert fee["krushipragya_service_fee"] == 15.0
    assert fee["total_payable"] == 15.0


def test_scheme_fee_type_official_plus_service(scheme_fixture):
    """Test 4: Scheme with separate official fee (₹30) and service fee (₹10)."""
    scheme = scheme_fixture["scheme_combo"]
    res = client.get(f"/api/v1/schemes/{scheme.id}")
    assert res.status_code == status.HTTP_200_OK
    fee = res.json()["fee_info"]
    assert fee["fee_type"] == "OFFICIAL_PLUS_SERVICE_FEE"
    assert fee["payment_required"] is True
    assert fee["official_fee"] == 30.0
    assert fee["krushipragya_service_fee"] == 10.0
    assert fee["total_payable"] == 40.0
    # Transparency disclosures
    assert "ಪಾರದರ್ಶಕತೆ" in fee["notice_kn"]
    assert "transparency" in fee["notice_en"].lower()


def test_scheme_fee_type_government_borne(scheme_fixture):
    """Test 5: Government-borne fee scheme has 0 official fee payable by farmer."""
    scheme = scheme_fixture["scheme_govt_borne"]
    res = client.get(f"/api/v1/schemes/{scheme.id}")
    assert res.status_code == status.HTTP_200_OK
    fee = res.json()["fee_info"]
    assert fee["fee_type"] == "GOVERNMENT_BORNE"
    assert fee["official_fee"] == 0.0
    assert fee["total_payable"] == 0.0
    assert fee["payment_required"] is False


def test_scheme_fee_type_unknown_blocks_payment(scheme_fixture):
    """Test 6: Unknown fee structure shows verification warning and blocks payment."""
    scheme = scheme_fixture["scheme_unknown"]
    farmer_a_id = scheme_fixture["farmer_a_id"]
    headers = auth_header(farmer_a_id)

    # 1. Detail returns UNKNOWN and is_verified=False
    res = client.get(f"/api/v1/schemes/{scheme.id}")
    assert res.status_code == status.HTTP_200_OK
    fee = res.json()["fee_info"]
    assert fee["fee_type"] == "UNKNOWN"
    assert fee["is_verified"] is False
    assert fee["total_payable"] is None

    # 2. Applying creates draft but payment cannot proceed
    app_res = client.post(f"/api/v1/schemes/{scheme.id}/apply", headers=headers)
    assert app_res.status_code == status.HTTP_201_CREATED
    app_id = app_res.json()["id"]

    # 3. Initiating payment must fail with 400
    pay_res = client.post(f"/api/v1/schemes/applications/{app_id}/payment", headers=headers)
    assert pay_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "Fee information needs verification" in pay_res.json()["detail"]


# ==============================================================================
# 2. Payment Initiation & PhonePe Static QR Tests
# ==============================================================================

def test_correct_total_calculation_and_qr_generation(scheme_fixture):
    """Test 7: Authoritative total calculation and PhonePe Static QR generation."""
    scheme = scheme_fixture["scheme_combo"]  # ₹30 + ₹10 = ₹40
    farmer_a_id = scheme_fixture["farmer_a_id"]
    headers = auth_header(farmer_a_id)

    # Apply
    app_res = client.post(f"/api/v1/schemes/{scheme.id}/apply", headers=headers)
    assert app_res.status_code == status.HTTP_201_CREATED
    app_id = app_res.json()["id"]

    # Initiate payment
    pay_res = client.post(f"/api/v1/schemes/applications/{app_id}/payment", headers=headers)
    assert pay_res.status_code == status.HTTP_200_OK
    pay_data = pay_res.json()

    assert pay_data["payment_method"] == "PHONEPE_STATIC_QR"
    assert pay_data["official_fee"] == 30.0
    assert pay_data["service_fee"] == 10.0
    assert pay_data["total_amount"] == 40.0
    assert pay_data["payment_status"] == "PENDING"

    # Verify PhonePe QR Data
    qr = pay_data["qr_data"]
    assert qr["upi_id"] == "krushipragya@ybl"
    assert qr["amount"] == 40.0
    assert "phonepe_static_qr.png" in qr["qr_asset_path"]

    # Separate Fee Summary
    summary = pay_data["fee_summary"]
    assert summary["official_fee"] == 30.0
    assert summary["krushipragya_service_fee"] == 10.0
    assert summary["total_payable"] == 40.0
    assert summary["label_official_kn"] == "ಸರ್ಕಾರದ ಅರ್ಜಿ ಶುಲ್ಕ"
    assert summary["label_service_kn"] == "KrushiPragya ಸೇವಾ ಶುಲ್ಕ"


def test_frontend_cannot_alter_amount(scheme_fixture):
    """Test 8 & 11: Tampered/altered amount submitted with UTR is rejected."""
    scheme = scheme_fixture["scheme_combo"]  # Total is ₹40
    farmer_a_id = scheme_fixture["farmer_a_id"]
    headers = auth_header(farmer_a_id)

    app_res = client.post(f"/api/v1/schemes/{scheme.id}/apply", headers=headers)
    app_id = app_res.json()["id"]

    client.post(f"/api/v1/schemes/applications/{app_id}/payment", headers=headers)

    # Submitting altered amount ₹15.00 instead of ₹40.00
    proof_res = client.post(
        f"/api/v1/schemes/applications/{app_id}/payment/submit-proof",
        json={"utr": "123456789012", "amount_paid": 15.00},
        headers=headers,
    )
    assert proof_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "Amount mismatch" in proof_res.json()["detail"]


def test_utr_submission_transitions_to_pending_verification(scheme_fixture):
    """Test 9: Valid 12-digit UTR submission sets status to PENDING_VERIFICATION."""
    scheme = scheme_fixture["scheme_combo"]
    farmer_a_id = scheme_fixture["farmer_a_id"]
    headers = auth_header(farmer_a_id)

    app_res = client.post(f"/api/v1/schemes/{scheme.id}/apply", headers=headers)
    app_id = app_res.json()["id"]

    client.post(f"/api/v1/schemes/applications/{app_id}/payment", headers=headers)

    valid_utr = "202609260001"
    proof_res = client.post(
        f"/api/v1/schemes/applications/{app_id}/payment/submit-proof",
        json={"utr": valid_utr, "amount_paid": 40.00},
        headers=headers,
    )
    assert proof_res.status_code == status.HTTP_200_OK
    data = proof_res.json()
    assert data["payment_status"] == "PENDING_VERIFICATION"
    assert data["application_status"] == "PAYMENT_PENDING"
    assert data["payment_reference"] == valid_utr
    assert "ಪರಿಶೀಲಿಸುತ್ತಿದೆ" in data["message_kn"]


def test_duplicate_utr_rejected(scheme_fixture):
    """Test 10: Reusing an already submitted UTR on another application is rejected."""
    scheme = scheme_fixture["scheme_combo"]
    farmer_a_id = scheme_fixture["farmer_a_id"]
    farmer_b_id = scheme_fixture["farmer_b_id"]
    headers_a = auth_header(farmer_a_id)
    headers_b = auth_header(farmer_b_id)

    # Farmer A submits UTR
    app_a = client.post(f"/api/v1/schemes/{scheme.id}/apply", headers=headers_a).json()["id"]
    client.post(f"/api/v1/schemes/applications/{app_a}/payment", headers=headers_a)
    client.post(
        f"/api/v1/schemes/applications/{app_a}/payment/submit-proof",
        json={"utr": "UNIQUE_UTR_8888", "amount_paid": 40.00},
        headers=headers_a,
    )

    # Farmer B attempts to reuse Farmer A's UTR
    app_b = client.post(f"/api/v1/schemes/{scheme.id}/apply", headers=headers_b).json()["id"]
    client.post(f"/api/v1/schemes/applications/{app_b}/payment", headers=headers_b)
    dup_res = client.post(
        f"/api/v1/schemes/applications/{app_b}/payment/submit-proof",
        json={"utr": "UNIQUE_UTR_8888", "amount_paid": 40.00},
        headers=headers_b,
    )
    assert dup_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "already been submitted" in dup_res.json()["detail"]


def test_invalid_utr_format_rejected(scheme_fixture):
    """Test 11: Too short or invalid format UTR is rejected."""
    scheme = scheme_fixture["scheme_combo"]
    farmer_a_id = scheme_fixture["farmer_a_id"]
    headers = auth_header(farmer_a_id)

    app_id = client.post(f"/api/v1/schemes/{scheme.id}/apply", headers=headers).json()["id"]
    client.post(f"/api/v1/schemes/applications/{app_id}/payment", headers=headers)

    # Short UTR
    bad_res = client.post(
        f"/api/v1/schemes/applications/{app_id}/payment/submit-proof",
        json={"utr": "123", "amount_paid": 40.00},
        headers=headers,
    )
    assert bad_res.status_code in (status.HTTP_422_UNPROCESSABLE_ENTITY, status.HTTP_400_BAD_REQUEST)


# ==============================================================================
# 3. Ownership & Authorization Tests
# ==============================================================================

def test_unauthorized_application_payment_rejected(scheme_fixture):
    """Test 12: Farmer B cannot initiate payment or submit proof for Farmer A's application."""
    scheme = scheme_fixture["scheme_combo"]
    farmer_a_id = scheme_fixture["farmer_a_id"]
    farmer_b_id = scheme_fixture["farmer_b_id"]
    headers_a = auth_header(farmer_a_id)
    headers_b = auth_header(farmer_b_id)

    app_a = client.post(f"/api/v1/schemes/{scheme.id}/apply", headers=headers_a).json()["id"]

    # Farmer B attempts to initiate payment on app_a -> 403
    unauth_init = client.post(f"/api/v1/schemes/applications/{app_a}/payment", headers=headers_b)
    assert unauth_init.status_code == status.HTTP_403_FORBIDDEN

    # Farmer B attempts to submit proof on app_a -> 403
    unauth_proof = client.post(
        f"/api/v1/schemes/applications/{app_a}/payment/submit-proof",
        json={"utr": "123456789012", "amount_paid": 40.00},
        headers=headers_b,
    )
    assert unauth_proof.status_code == status.HTTP_403_FORBIDDEN


def test_unauthorized_payment_verification_rejected(scheme_fixture):
    """Test 13: Standard farmer cannot call /verify endpoint (403)."""
    scheme = scheme_fixture["scheme_combo"]
    farmer_a_id = scheme_fixture["farmer_a_id"]
    headers_a = auth_header(farmer_a_id)

    app_id = client.post(f"/api/v1/schemes/{scheme.id}/apply", headers=headers_a).json()["id"]
    client.post(f"/api/v1/schemes/applications/{app_id}/payment", headers=headers_a)
    client.post(
        f"/api/v1/schemes/applications/{app_id}/payment/submit-proof",
        json={"utr": "123456789012", "amount_paid": 40.00},
        headers=headers_a,
    )

    # Farmer attempts to verify own payment -> 403 Forbidden
    ver_res = client.post(
        f"/api/v1/schemes/applications/{app_id}/payment/verify",
        json={"action": "APPROVE"},
        headers=headers_a,
    )
    assert ver_res.status_code == status.HTTP_403_FORBIDDEN


def test_successful_manual_verification_generates_receipt(scheme_fixture):
    """Test 14: Authorized Admin or Officer approves UTR and generates formal receipt."""
    scheme = scheme_fixture["scheme_combo"]
    farmer_a_id = scheme_fixture["farmer_a_id"]
    officer_id = scheme_fixture["officer_id"]
    headers_farmer = auth_header(farmer_a_id)
    headers_officer = auth_header(officer_id)

    app_id = client.post(f"/api/v1/schemes/{scheme.id}/apply", headers=headers_farmer).json()["id"]
    client.post(f"/api/v1/schemes/applications/{app_id}/payment", headers=headers_farmer)
    client.post(
        f"/api/v1/schemes/applications/{app_id}/payment/submit-proof",
        json={"utr": "BANK_UTR_99990000", "amount_paid": 40.00},
        headers=headers_farmer,
    )

    # Officer approves
    ver_res = client.post(
        f"/api/v1/schemes/applications/{app_id}/payment/verify",
        json={"action": "APPROVE", "notes": "Bank statement confirmed credit"},
        headers=headers_officer,
    )
    assert ver_res.status_code == status.HTTP_200_OK
    receipt = ver_res.json()
    assert receipt["payment_status"] == "PAID"
    assert receipt["total_paid"] == 40.0
    assert receipt["official_fee"] == 30.0
    assert receipt["krushipragya_service_fee"] == 10.0
    assert receipt["payment_reference"] == "BANK_UTR_99990000"
    assert "KP-REC-" in receipt["receipt_id"]
    assert receipt["payment_method"] == "PHONEPE_STATIC_QR"

    # Farmer retrieves payment details and receipt
    pay_get = client.get(f"/api/v1/schemes/applications/{app_id}/payment", headers=headers_farmer)
    assert pay_get.status_code == status.HTTP_200_OK
    get_data = pay_get.json()
    assert get_data["payment_status"] == "PAID"
    assert get_data["receipt"]["receipt_id"] == receipt["receipt_id"]


def test_failed_payment_verification(scheme_fixture):
    """Test 15: Officer rejects fraudulent or uncredited UTR."""
    scheme = scheme_fixture["scheme_combo"]
    farmer_a_id = scheme_fixture["farmer_a_id"]
    officer_id = scheme_fixture["officer_id"]
    headers_farmer = auth_header(farmer_a_id)
    headers_officer = auth_header(officer_id)

    app_id = client.post(f"/api/v1/schemes/{scheme.id}/apply", headers=headers_farmer).json()["id"]
    client.post(f"/api/v1/schemes/applications/{app_id}/payment", headers=headers_farmer)
    client.post(
        f"/api/v1/schemes/applications/{app_id}/payment/submit-proof",
        json={"utr": "FAKE_UTR_00000", "amount_paid": 40.00},
        headers=headers_farmer,
    )

    # Officer rejects
    ver_res = client.post(
        f"/api/v1/schemes/applications/{app_id}/payment/verify",
        json={"action": "REJECT", "notes": "No matching credit in PhonePe merchant statement"},
        headers=headers_officer,
    )
    assert ver_res.status_code == status.HTTP_400_BAD_REQUEST

    # Check status is FAILED
    pay_get = client.get(f"/api/v1/schemes/applications/{app_id}/payment", headers=headers_farmer)
    assert pay_get.json()["payment_status"] == "FAILED"


# ==============================================================================
# 4. Application Lifecycle & Free Scheme Tests
# ==============================================================================

def test_payment_required_application_cannot_submit_before_paid(scheme_fixture):
    """Test 16: Fee-bearing application cannot be submitted when unpaid."""
    scheme = scheme_fixture["scheme_combo"]
    farmer_a_id = scheme_fixture["farmer_a_id"]
    headers = auth_header(farmer_a_id)

    app_id = client.post(f"/api/v1/schemes/{scheme.id}/apply", headers=headers).json()["id"]

    # Attempt to submit without payment
    sub_res = client.post(f"/api/v1/schemes/applications/{app_id}/submit", headers=headers)
    assert sub_res.status_code == status.HTTP_400_BAD_REQUEST
    assert "Cannot submit application without verified payment" in sub_res.json()["detail"]


def test_free_application_bypasses_payment_and_submits_directly(scheme_fixture):
    """Test 17: Free scheme application bypasses payment and submits directly."""
    scheme = scheme_fixture["scheme_free"]
    farmer_a_id = scheme_fixture["farmer_a_id"]
    headers = auth_header(farmer_a_id)

    # 1. Apply
    app_res = client.post(f"/api/v1/schemes/{scheme.id}/apply", headers=headers)
    assert app_res.status_code == status.HTTP_201_CREATED
    app_data = app_res.json()
    assert app_data["status"] == "READY_FOR_SUBMISSION"
    assert app_data["payment_status"] == "NOT_REQUIRED"
    assert app_data["can_submit"] is True

    # 2. Submit directly
    sub_res = client.post(f"/api/v1/schemes/applications/{app_data['id']}/submit", headers=headers)
    assert sub_res.status_code == status.HTTP_200_OK
    assert sub_res.json()["status"] == "SUBMITTED"
    assert sub_res.json()["submitted_at"] is not None

    # 3. Track in farmer's applications
    track_res = client.get("/api/v1/schemes/my-applications", headers=headers)
    assert track_res.status_code == status.HTTP_200_OK
    my_apps = track_res.json()
    assert any(a["id"] == app_data["id"] and a["status"] == "SUBMITTED" for a in my_apps)


def test_existing_scheme_apis_remain_working(scheme_fixture):
    """Test 18: Existing public schemes APIs return fee_info and operate normally."""
    # List endpoint
    list_res = client.get("/api/v1/schemes?state=all")
    assert list_res.status_code == status.HTTP_200_OK
    data = list_res.json()
    assert "items" in data
    assert len(data["items"]) >= 5
    for item in data["items"]:
        assert "fee_info" in item
        assert "fee_type" in item["fee_info"]


def test_arbitrary_identity_headers_rejected(scheme_fixture):
    """Test 19: Spoofed headers (x-farmer-id) are rejected without valid Bearer JWT."""
    scheme = scheme_fixture["scheme_combo"]
    fake_farmer_id = str(uuid.uuid4())

    res = client.post(
        f"/api/v1/schemes/{scheme.id}/apply",
        headers={"x-farmer-id": fake_farmer_id, "x-farmer-phone": "9999999999"},
    )
    assert res.status_code == status.HTTP_401_UNAUTHORIZED
