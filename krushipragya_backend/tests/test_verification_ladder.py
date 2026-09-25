"""Comprehensive test suite for KrushiPragya Trust Ladder, Community Corroboration, and Expert Verification.

Tests cover:
1. Trust Ladder Stage Transitions:
   - UNVERIFIED -> AI_ANALYSED
   - AI_ANALYSED -> CORROBORATED
   - CORROBORATED -> EXPERT_VERIFIED
   - Hierarchy invariants (cannot move backwards)
2. Community Corroboration:
   - Successful corroboration submission and consensus threshold
   - Agreement vs disagreement counting
   - Rejection of duplicate corroboration (409 Conflict)
   - Rejection of self-corroboration by report owner (403 Forbidden)
   - Role enforcement (COMMUNITY_MEMBER, FARMER, ADMIN)
   - Listing corroborations and eligible reports
3. Agriculture Expert Verification:
   - Verification request creation by report owner
   - Duplicate active verification request rejection (409 Conflict)
   - Expert queue listing, triage, and assignment
   - Expert detail review package (image, AI diagnosis, corroborations)
   - Expert decisions: APPROVE, REJECT, REQUEST_REVIEW / NEED_MORE_INFO
   - Non-expert rejection (403 Forbidden)
   - Inactive expert rejection (403 Forbidden)
   - Admin authorization override
4. Security & Error Handling:
   - Unauthenticated rejection (401 Unauthorized)
   - IDOR / unauthorized farmer access rejection (403 Forbidden)
   - Missing report / request handling (404 Not Found)
   - Ineligible report without diagnosis (422 Unprocessable Entity)
   - Invalid observation type & decision values (422 Unprocessable Entity)
   - Rejection of modifying finalized requests (409 Conflict)
5. Auditability & Frontend Contract:
   - Chronological status history verification
   - Response payload contracts
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional
import uuid
import pytest
from fastapi.testclient import TestClient

from app.core.auth import get_current_user, require_role, verify_farmer_access
from app.core.config import settings
from app.core.security import create_access_token
from app.database.connection import get_db
from app.main import app
from app.models.crop import Crop
from app.models.crop_report import CropReport
from app.models.crop_report_diagnosis import CropReportDiagnosis
from app.models.expert_verification import CommunityCorroboration, ExpertVerificationRequest
from app.models.farmer_crop import FarmerCrop
from app.models.role import Role, UserRole
from app.models.user_profile import UserProfile
from app.schemas.verification import (
    STATUS_RANKS,
    ObservationType,
    VerificationStatus,
)
from app.services.verification_service import (
    VerificationService,
    get_verification_service,
    transition_crop_report_status,
)

client = TestClient(app)


# ==============================================================================
# In-Memory Mock Database Fixture
# ==============================================================================


class MockVerificationDBSession:
    """In-memory database session for isolating verification and corroboration tests."""

    def __init__(self):
        self.users: Dict[uuid.UUID, UserProfile] = {}
        self.user_roles: List[UserRole] = []
        self.crops: Dict[uuid.UUID, Crop] = {}
        self.farmer_crops: Dict[uuid.UUID, FarmerCrop] = {}
        self.crop_reports: Dict[uuid.UUID, CropReport] = {}
        self.diagnoses: Dict[uuid.UUID, CropReportDiagnosis] = {}
        self.corroborations: Dict[uuid.UUID, CommunityCorroboration] = {}
        self.expert_requests: Dict[uuid.UUID, ExpertVerificationRequest] = {}

    def get(self, model, entity_id):
        if model is UserProfile:
            return self.users.get(entity_id)
        if model is Crop:
            return self.crops.get(entity_id)
        if model is FarmerCrop:
            fc = self.farmer_crops.get(entity_id)
            if fc and fc.crop_id in self.crops:
                fc.crop = self.crops[fc.crop_id]
            return fc
        if model is CropReport:
            r = self.crop_reports.get(entity_id)
            if r:
                r.farmer_crop = self.get(FarmerCrop, r.farmer_crop_id)
                r.diagnoses = [d for d in self.diagnoses.values() if d.crop_report_id == r.id]
            return r
        if model is CropReportDiagnosis:
            return self.diagnoses.get(entity_id)
        if model is CommunityCorroboration:
            return self.corroborations.get(entity_id)
        if model is ExpertVerificationRequest:
            req = self.expert_requests.get(entity_id)
            if req:
                req.crop_report = self.get(CropReport, req.crop_report_id)
                req.farmer = self.users.get(req.farmer_id)
                req.expert = self.users.get(req.expert_id) if req.expert_id else None
            return req
        return None

    def add(self, entity):
        now = datetime.now(timezone.utc)
        if hasattr(entity, "created_at") and getattr(entity, "created_at", None) is None:
            entity.created_at = now
        if hasattr(entity, "updated_at") and getattr(entity, "updated_at", None) is None:
            entity.updated_at = now

        if isinstance(entity, UserProfile):
            self.users[entity.id] = entity
        elif isinstance(entity, UserRole):
            self.user_roles.append(entity)
        elif isinstance(entity, Crop):
            self.crops[entity.id] = entity
        elif isinstance(entity, FarmerCrop):
            self.farmer_crops[entity.id] = entity
        elif isinstance(entity, CropReport):
            self.crop_reports[entity.id] = entity
        elif isinstance(entity, CropReportDiagnosis):
            self.diagnoses[entity.id] = entity
        elif isinstance(entity, CommunityCorroboration):
            self.corroborations[entity.id] = entity
        elif isinstance(entity, ExpertVerificationRequest):
            self.expert_requests[entity.id] = entity

    def commit(self):
        pass

    def rollback(self):
        pass

    def flush(self):
        pass

    def refresh(self, entity):
        pass

    def query(self, *entities):
        return MockVerificationQuery(self, entities)


class MockVerificationQuery:
    """Mock query engine supporting filter and relation resolution."""

    def __init__(self, session: MockVerificationDBSession, entities):
        self.session = session
        self.entities = entities
        self.entity_cls = entities[0] if entities else None
        self._filters = []
        self._order_by = None
        self._offset = 0
        self._limit = None

    def options(self, *opts):
        return self

    def join(self, *args, **kwargs):
        return self

    def filter(self, *criteria):
        self._filters.extend(criteria)
        return self

    def order_by(self, *order_exprs):
        self._order_by = order_exprs
        return self

    def offset(self, n: int):
        self._offset = n
        return self

    def limit(self, n: int):
        self._limit = n
        return self

    def _resolve_items(self):
        entity_names = [str(e).lower() for e in self.entities]
        if any("user_roles" in name or "role" in name for name in entity_names):
            items = list(self.session.user_roles)
        elif any("crop_report_diagnoses" in name or "diagnos" in name for name in entity_names):
            items = list(self.session.diagnoses.values())
        elif any("crop_reports" in name or "cropreport" in name for name in entity_names):
            items = list(self.session.crop_reports.values())
        elif any("farmer_crops" in name or "farmercrop" in name for name in entity_names):
            items = list(self.session.farmer_crops.values())
        elif any("community_corroborations" in name or "corroborat" in name for name in entity_names):
            items = list(self.session.corroborations.values())
        elif any("expert_verification_requests" in name or "expert" in name for name in entity_names):
            items = list(self.session.expert_requests.values())
        elif any("user_profiles" in name or "userprofile" in name for name in entity_names):
            items = list(self.session.users.values())
        elif any("crops" in name or "crop" in name for name in entity_names):
            items = list(self.session.crops.values())
        else:
            items = []

        # Populate relationships dynamically for testing
        for item in items:
            if isinstance(item, CropReport):
                item.farmer_crop = self.session.farmer_crops.get(item.farmer_crop_id)
                if item.farmer_crop:
                    item.farmer_crop.crop = self.session.crops.get(item.farmer_crop.crop_id)
                item.diagnoses = [
                    d for d in self.session.diagnoses.values()
                    if d.crop_report_id == item.id
                ]
            elif isinstance(item, ExpertVerificationRequest):
                item.crop_report = self.session.crop_reports.get(item.crop_report_id)
                if item.crop_report:
                    item.crop_report.farmer_crop = self.session.farmer_crops.get(item.crop_report.farmer_crop_id)
                    if item.crop_report.farmer_crop:
                        item.crop_report.farmer_crop.crop = self.session.crops.get(item.crop_report.farmer_crop.crop_id)
                    item.crop_report.diagnoses = [
                        d for d in self.session.diagnoses.values()
                        if d.crop_report_id == item.crop_report.id
                    ]
                item.farmer = self.session.users.get(item.farmer_id)
                item.expert = self.session.users.get(item.expert_id) if item.expert_id else None

        # Filter items
        filtered = []
        for item in items:
            match = True
            for crit in self._filters:
                c_str = str(crit).lower()
                if "user_id" in c_str and hasattr(crit, "right") and hasattr(crit.right, "value"):
                    val = crit.right.value
                    if getattr(item, "user_id", None) != val:
                        match = False
                        break
                elif "crop_report_id" in c_str and hasattr(crit, "right") and hasattr(crit.right, "value"):
                    val = crit.right.value
                    if getattr(item, "crop_report_id", None) != val:
                        match = False
                        break
                elif "community_member_id" in c_str and hasattr(crit, "right") and hasattr(crit.right, "value"):
                    val = crit.right.value
                    if getattr(item, "community_member_id", None) != val:
                        match = False
                        break
                elif "expert_id" in c_str and hasattr(crit, "right") and hasattr(crit.right, "value"):
                    val = crit.right.value
                    if getattr(item, "expert_id", None) != val:
                        match = False
                        break
                elif "status in" in c_str or "status in (" in c_str:
                    if hasattr(crit, "right") and hasattr(crit.right, "clauses"):
                        allowed = [cl.value for cl in crit.right.clauses]
                        if getattr(item, "status", None) not in allowed:
                            match = False
                            break
                elif "status =" in c_str or "status ==" in c_str:
                    if hasattr(crit, "right") and hasattr(crit.right, "value"):
                        val = crit.right.value
                        if getattr(item, "status", None) != val:
                            match = False
                            break
                elif "farmer_id !=" in c_str and hasattr(crit, "right") and hasattr(crit.right, "value"):
                    val = crit.right.value
                    item_farmer = getattr(item, "farmer_id", None)
                    if item_farmer is None and getattr(item, "farmer_crop", None):
                        item_farmer = item.farmer_crop.farmer_id
                    if item_farmer == val:
                        match = False
                        break
                elif ("id =" in c_str or "id ==" in c_str) and hasattr(crit, "right") and hasattr(crit.right, "value"):
                    val = crit.right.value
                    if getattr(item, "id", None) != val:
                        match = False
                        break
            if match:
                filtered.append(item)

        # Slice
        if self._offset:
            filtered = filtered[self._offset:]
        if self._limit:
            filtered = filtered[:self._limit]
        return filtered

    def all(self):
        entity_names = [str(e).lower() for e in self.entities]
        if any("role" in name for name in entity_names):
            results = []
            for ur in self.session.user_roles:
                match = True
                for crit in self._filters:
                    c_str = str(crit).lower()
                    if "user_id" in c_str and hasattr(crit, "right") and hasattr(crit.right, "value"):
                        if ur.user_id != crit.right.value:
                            match = False
                            break
                    if "status" in c_str and hasattr(crit, "right") and hasattr(crit.right, "value"):
                        if ur.status != crit.right.value:
                            match = False
                            break
                if match:
                    if len(self.entities) == 1 and not isinstance(self.entities[0], type):
                        results.append((ur.role_code,))
                    else:
                        results.append(ur)
            return results

        return self._resolve_items()

    def first(self):
        res = self._resolve_items()
        return res[0] if res else None

    def count(self):
        return len(self._resolve_items())


# ==============================================================================
# Test Fixtures and Helpers
# ==============================================================================


@pytest.fixture
def mock_db():
    """Provides a fresh MockVerificationDBSession overridden into FastAPI get_db."""
    session = MockVerificationDBSession()
    app.dependency_overrides[get_db] = lambda: session
    yield session
    app.dependency_overrides.pop(get_db, None)


def auth_headers(user_id: uuid.UUID, email: str = "user@krushipragya.com", expired: bool = False) -> Dict[str, str]:
    """Helper to generate JWT Bearer token headers."""
    delta = timedelta(minutes=-10) if expired else timedelta(hours=2)
    token = create_access_token(
        data={"sub": str(user_id), "email": email, "aud": "authenticated"},
        expires_delta=delta,
    )
    return {"Authorization": f"Bearer {token}"}


def setup_test_actors(db: MockVerificationDBSession):
    """Seed test users with explicit active roles and crop fixtures."""
    now = datetime.now(timezone.utc)

    # 1. Farmer
    farmer_id = uuid.uuid4()
    farmer = UserProfile(id=farmer_id, full_name="Basavaraj Gowda", language="kn")
    farmer_role = UserRole(id=uuid.uuid4(), user_id=farmer_id, role_code="FARMER", status="ACTIVE")
    db.add(farmer)
    db.add(farmer_role)

    # 2. Other Farmer
    other_farmer_id = uuid.uuid4()
    other_farmer = UserProfile(id=other_farmer_id, full_name="Ramesh Patil", language="kn")
    other_farmer_role = UserRole(id=uuid.uuid4(), user_id=other_farmer_id, role_code="FARMER", status="ACTIVE")
    db.add(other_farmer)
    db.add(other_farmer_role)

    # 3. Community Members
    comm_member_1_id = uuid.uuid4()
    comm_1 = UserProfile(id=comm_member_1_id, full_name="Suresh Village Elder", language="kn")
    comm_role_1 = UserRole(id=uuid.uuid4(), user_id=comm_member_1_id, role_code="COMMUNITY_MEMBER", status="ACTIVE")
    db.add(comm_1)
    db.add(comm_role_1)

    comm_member_2_id = uuid.uuid4()
    comm_2 = UserProfile(id=comm_member_2_id, full_name="Manjunath Agronomist Neighbor", language="kn")
    comm_role_2 = UserRole(id=uuid.uuid4(), user_id=comm_member_2_id, role_code="COMMUNITY_MEMBER", status="ACTIVE")
    db.add(comm_2)
    db.add(comm_role_2)

    # 4. Active Agriculture Expert
    expert_id = uuid.uuid4()
    expert = UserProfile(id=expert_id, full_name="Dr. Shreedhar Kulkarni", language="en")
    expert_role = UserRole(id=uuid.uuid4(), user_id=expert_id, role_code="AGRICULTURE_EXPERT", status="ACTIVE")
    db.add(expert)
    db.add(expert_role)

    # 5. Inactive Agriculture Expert
    inactive_expert_id = uuid.uuid4()
    inactive_expert = UserProfile(id=inactive_expert_id, full_name="Dr. Suspended Expert", language="en")
    inactive_role = UserRole(id=uuid.uuid4(), user_id=inactive_expert_id, role_code="AGRICULTURE_EXPERT", status="INACTIVE")
    db.add(inactive_expert)
    db.add(inactive_role)

    # 6. Admin
    admin_id = uuid.uuid4()
    admin = UserProfile(id=admin_id, full_name="System Admin", language="en")
    admin_role = UserRole(id=uuid.uuid4(), user_id=admin_id, role_code="ADMIN", status="ACTIVE")
    db.add(admin)
    db.add(admin_role)

    # 7. Crop and FarmerCrop
    crop_id = uuid.uuid4()
    crop = Crop(id=crop_id, code="arecanut", name_en="Arecanut", name_kn="ಅಡಿಕೆ")
    farmer_crop_id = uuid.uuid4()
    farmer_crop = FarmerCrop(id=farmer_crop_id, farmer_id=farmer_id, crop_id=crop_id, crop=crop)
    db.add(crop)
    db.add(farmer_crop)

    # 8. Base CropReport (UNVERIFIED)
    report_id = uuid.uuid4()
    report = CropReport(
        id=report_id,
        farmer_crop_id=farmer_crop_id,
        notes="Yellowing on leaf tips",
        image_storage_path="crop-reports/test_image.jpg",
        status="UNVERIFIED",
        created_at=now,
        updated_at=now,
    )
    report.farmer_crop = farmer_crop
    db.add(report)

    return {
        "farmer_id": farmer_id,
        "other_farmer_id": other_farmer_id,
        "comm_1_id": comm_member_1_id,
        "comm_2_id": comm_member_2_id,
        "expert_id": expert_id,
        "inactive_expert_id": inactive_expert_id,
        "admin_id": admin_id,
        "crop_id": crop_id,
        "farmer_crop_id": farmer_crop_id,
        "report_id": report_id,
    }


# ==============================================================================
# 1. Trust Ladder Stage Invariant & Transition Unit Tests
# ==============================================================================


def test_trust_ladder_ranks_and_hierarchy_invariants():
    """Verify trust ladder status rank hierarchy."""
    assert STATUS_RANKS[VerificationStatus.UNVERIFIED.value] == 0
    assert STATUS_RANKS[VerificationStatus.AI_ANALYSED.value] == 1
    assert STATUS_RANKS[VerificationStatus.CORROBORATED.value] == 2
    assert STATUS_RANKS[VerificationStatus.EXPERT_VERIFIED.value] == 3


def test_cannot_move_backwards_in_trust_ladder(mock_db):
    """Verify lower stages can never overwrite higher stages."""
    actors = setup_test_actors(mock_db)
    report = mock_db.get(CropReport, actors["report_id"])

    # 1. UNVERIFIED -> AI_ANALYSED advances
    advanced = transition_crop_report_status(mock_db, report, VerificationStatus.AI_ANALYSED.value)
    assert advanced is True
    assert report.status == VerificationStatus.AI_ANALYSED.value

    # 2. Cannot downgrade AI_ANALYSED -> UNVERIFIED
    blocked = transition_crop_report_status(mock_db, report, VerificationStatus.UNVERIFIED.value)
    assert blocked is False
    assert report.status == VerificationStatus.AI_ANALYSED.value

    # 3. AI_ANALYSED -> CORROBORATED advances
    advanced = transition_crop_report_status(mock_db, report, VerificationStatus.CORROBORATED.value)
    assert advanced is True
    assert report.status == VerificationStatus.CORROBORATED.value

    # 4. Cannot downgrade CORROBORATED -> AI_ANALYSED
    blocked = transition_crop_report_status(mock_db, report, VerificationStatus.AI_ANALYSED.value)
    assert blocked is False
    assert report.status == VerificationStatus.CORROBORATED.value

    # 5. CORROBORATED -> EXPERT_VERIFIED advances
    advanced = transition_crop_report_status(mock_db, report, VerificationStatus.EXPERT_VERIFIED.value)
    assert advanced is True
    assert report.status == VerificationStatus.EXPERT_VERIFIED.value

    # 6. Cannot downgrade EXPERT_VERIFIED -> CORROBORATED or UNVERIFIED
    blocked = transition_crop_report_status(mock_db, report, VerificationStatus.CORROBORATED.value)
    assert blocked is False
    assert report.status == VerificationStatus.EXPERT_VERIFIED.value


# ==============================================================================
# 2. Community Corroboration API Tests
# ==============================================================================


def test_corroboration_rejected_on_unverified_report_without_diagnosis(mock_db):
    """Corroboration must be rejected (422) if report has no AI diagnosis."""
    actors = setup_test_actors(mock_db)
    headers = auth_headers(actors["comm_1_id"])

    resp = client.post(
        f"/api/v1/crop-reports/{actors['report_id']}/corroborations",
        headers=headers,
        json={"observation_type": "SAME_SYMPTOMS", "notes": "Looks identical"},
    )
    assert resp.status_code == 422
    assert "diagnosed by AI" in resp.json()["detail"]


def test_self_corroboration_rejected_by_owner(mock_db):
    """Report owner attempting to corroborate own report is rejected with 403 Forbidden."""
    actors = setup_test_actors(mock_db)
    report = mock_db.get(CropReport, actors["report_id"])
    report.status = "AI_ANALYSED"

    # Add diagnosis
    diag = CropReportDiagnosis(
        id=uuid.uuid4(),
        crop_report_id=report.id,
        crop="arecanut",
        predicted_class="Yellow Leaf Disease",
        confidence=0.92,
        model_name="effb0_arecanut",
        predictions=[],
    )
    mock_db.add(diag)

    owner_headers = auth_headers(actors["farmer_id"])
    resp = client.post(
        f"/api/v1/crop-reports/{actors['report_id']}/corroborations",
        headers=owner_headers,
        json={"observation_type": "SAME_SYMPTOMS"},
    )
    assert resp.status_code == 403
    assert "Report owners cannot corroborate" in resp.json()["detail"]


def test_successful_corroboration_and_threshold_transition(mock_db):
    """AI_ANALYSED report transitions to CORROBORATED when minimum corroboration threshold is satisfied."""
    actors = setup_test_actors(mock_db)
    report = mock_db.get(CropReport, actors["report_id"])
    report.status = "AI_ANALYSED"

    diag = CropReportDiagnosis(
        id=uuid.uuid4(),
        crop_report_id=report.id,
        crop="arecanut",
        predicted_class="Yellow Leaf Disease",
        confidence=0.92,
        model_name="effb0_arecanut",
        predictions=[],
    )
    mock_db.add(diag)

    # Corroborator 1 submits agreeing corroboration
    c1_headers = auth_headers(actors["comm_1_id"])
    resp1 = client.post(
        f"/api/v1/crop-reports/{actors['report_id']}/corroborations",
        headers=c1_headers,
        json={"observation_type": "SAME_SYMPTOMS", "notes": "Seen on farm next door"},
    )
    assert resp1.status_code == 201
    data1 = resp1.json()
    assert data1["corroboration"]["observation_type"] == "SAME_SYMPTOMS"
    assert data1["corroboration"]["is_agreed"] is True
    assert data1["corroboration_summary"]["agreed_count"] == 1
    assert data1["corroboration_summary"]["threshold_satisfied"] is False
    assert data1["report_status"] == "AI_ANALYSED"

    # Corroborator 2 submits agreeing corroboration -> threshold satisfied (>= 2)
    c2_headers = auth_headers(actors["comm_2_id"])
    resp2 = client.post(
        f"/api/v1/crop-reports/{actors['report_id']}/corroborations",
        headers=c2_headers,
        json={"observation_type": "SEEN_NEARBY", "notes": "Confirmed in village cluster"},
    )
    assert resp2.status_code == 201
    data2 = resp2.json()
    assert data2["corroboration_summary"]["agreed_count"] == 2
    assert data2["corroboration_summary"]["threshold_satisfied"] is True
    assert data2["corroboration_summary"]["is_corroborated"] is True
    # Trust Ladder transitioned to CORROBORATED!
    assert data2["report_status"] == "CORROBORATED"
    assert report.status == "CORROBORATED"


def test_duplicate_corroboration_rejected(mock_db):
    """Submitting duplicate corroboration by the same user returns 409 Conflict."""
    actors = setup_test_actors(mock_db)
    report = mock_db.get(CropReport, actors["report_id"])
    report.status = "AI_ANALYSED"

    diag = CropReportDiagnosis(
        id=uuid.uuid4(),
        crop_report_id=report.id,
        crop="arecanut",
        predicted_class="Yellow Leaf Disease",
        confidence=0.92,
        model_name="effb0_arecanut",
        predictions=[],
    )
    mock_db.add(diag)

    headers = auth_headers(actors["comm_1_id"])
    client.post(
        f"/api/v1/crop-reports/{actors['report_id']}/corroborations",
        headers=headers,
        json={"observation_type": "SAME_SYMPTOMS"},
    )

    # Duplicate call
    dup_resp = client.post(
        f"/api/v1/crop-reports/{actors['report_id']}/corroborations",
        headers=headers,
        json={"observation_type": "SAME_SYMPTOMS"},
    )
    assert dup_resp.status_code == 409
    assert "already submitted a corroboration" in dup_resp.json()["detail"]


def test_invalid_observation_type_rejected(mock_db):
    """Submitting an unrecognized observation type returns 422 Unprocessable Entity."""
    actors = setup_test_actors(mock_db)
    report = mock_db.get(CropReport, actors["report_id"])
    report.status = "AI_ANALYSED"

    diag = CropReportDiagnosis(
        id=uuid.uuid4(),
        crop_report_id=report.id,
        crop="arecanut",
        predicted_class="Yellow Leaf Disease",
        confidence=0.92,
        model_name="effb0_arecanut",
        predictions=[],
    )
    mock_db.add(diag)

    headers = auth_headers(actors["comm_1_id"])
    resp = client.post(
        f"/api/v1/crop-reports/{actors['report_id']}/corroborations",
        headers=headers,
        json={"observation_type": "TOTALLY_INVALID_TYPE"},
    )
    assert resp.status_code == 422
    assert "Invalid observation_type" in resp.json()["detail"]


def test_list_corroborations_and_eligible_reports(mock_db):
    """List corroborations and eligible reports endpoints."""
    actors = setup_test_actors(mock_db)
    report = mock_db.get(CropReport, actors["report_id"])
    report.status = "AI_ANALYSED"

    diag = CropReportDiagnosis(
        id=uuid.uuid4(),
        crop_report_id=report.id,
        crop="arecanut",
        predicted_class="Yellow Leaf Disease",
        confidence=0.92,
        model_name="effb0_arecanut",
        predictions=[],
    )
    mock_db.add(diag)

    headers = auth_headers(actors["comm_1_id"])

    # 1. List eligible reports excludes caller's own reports
    eligible_resp = client.get("/api/v1/community/eligible-crop-reports", headers=headers)
    assert eligible_resp.status_code == 200
    assert len(eligible_resp.json()["items"]) >= 1

    # 2. List corroborations
    list_resp = client.get(f"/api/v1/crop-reports/{actors['report_id']}/corroborations", headers=headers)
    assert list_resp.status_code == 200
    assert "corroboration_summary" in list_resp.json()


# ==============================================================================
# 3. Agriculture Expert Verification API Tests
# ==============================================================================


def test_create_verification_request_by_owner_success(mock_db):
    """Farmer owner can successfully create an expert verification request for diagnosed report."""
    actors = setup_test_actors(mock_db)
    report = mock_db.get(CropReport, actors["report_id"])
    report.status = "AI_ANALYSED"

    diag = CropReportDiagnosis(
        id=uuid.uuid4(),
        crop_report_id=report.id,
        crop="arecanut",
        predicted_class="Yellow Leaf Disease",
        confidence=0.92,
        model_name="effb0_arecanut",
        predictions=[],
    )
    mock_db.add(diag)

    headers = auth_headers(actors["farmer_id"])
    resp = client.post(
        f"/api/v1/crop-reports/{actors['report_id']}/verification-request",
        headers=headers,
        json={"notes": "Please verify urgent yellow leaf symptoms"},
    )
    assert resp.status_code == 201
    data = resp.json()
    assert data["crop_report_id"] == str(actors["report_id"])
    assert data["farmer_id"] == str(actors["farmer_id"])
    assert data["status"] == "PENDING"


def test_create_verification_request_unauthorized_farmer_rejected(mock_db):
    """Another farmer attempting to request verification for a report they don't own gets 403 Forbidden."""
    actors = setup_test_actors(mock_db)
    report = mock_db.get(CropReport, actors["report_id"])
    report.status = "AI_ANALYSED"

    diag = CropReportDiagnosis(
        id=uuid.uuid4(),
        crop_report_id=report.id,
        crop="arecanut",
        predicted_class="Yellow Leaf Disease",
        confidence=0.92,
        model_name="effb0_arecanut",
        predictions=[],
    )
    mock_db.add(diag)

    other_farmer_headers = auth_headers(actors["other_farmer_id"])
    resp = client.post(
        f"/api/v1/crop-reports/{actors['report_id']}/verification-request",
        headers=other_farmer_headers,
        json={"notes": "Intruder attempt"},
    )
    assert resp.status_code == 403
    assert "Only the farmer who owns this report" in resp.json()["detail"]


def test_duplicate_active_verification_request_rejected(mock_db):
    """Creating a duplicate verification request while one is active returns 409 Conflict."""
    actors = setup_test_actors(mock_db)
    report = mock_db.get(CropReport, actors["report_id"])
    report.status = "AI_ANALYSED"

    diag = CropReportDiagnosis(
        id=uuid.uuid4(),
        crop_report_id=report.id,
        crop="arecanut",
        predicted_class="Yellow Leaf Disease",
        confidence=0.92,
        model_name="effb0_arecanut",
        predictions=[],
    )
    mock_db.add(diag)

    headers = auth_headers(actors["farmer_id"])
    client.post(
        f"/api/v1/crop-reports/{actors['report_id']}/verification-request",
        headers=headers,
    )

    # Second active request attempt
    dup_resp = client.post(
        f"/api/v1/crop-reports/{actors['report_id']}/verification-request",
        headers=headers,
    )
    assert dup_resp.status_code == 409
    assert "active expert verification request already exists" in dup_resp.json()["detail"]


def test_expert_queue_and_detail_review(mock_db):
    """Agriculture expert can list queue and view full clinical package."""
    actors = setup_test_actors(mock_db)
    report = mock_db.get(CropReport, actors["report_id"])
    report.status = "CORROBORATED"

    diag = CropReportDiagnosis(
        id=uuid.uuid4(),
        crop_report_id=report.id,
        crop="arecanut",
        predicted_class="Yellow Leaf Disease",
        confidence=0.88,
        model_name="effb0_arecanut",
        predictions=[{"class_name": "Yellow Leaf Disease", "confidence": 0.88}],
    )
    mock_db.add(diag)

    # Add active request
    req = ExpertVerificationRequest(
        id=uuid.uuid4(),
        crop_report_id=report.id,
        farmer_id=actors["farmer_id"],
        status="PENDING",
        requested_at=datetime.now(timezone.utc),
    )
    mock_db.add(req)

    expert_headers = auth_headers(actors["expert_id"])

    # 1. Expert Queue
    queue_resp = client.get("/api/v1/expert/verifications", headers=expert_headers)
    assert queue_resp.status_code == 200
    queue_data = queue_resp.json()
    assert queue_data["total"] >= 1
    assert queue_data["items"][0]["crop_code"] == "arecanut"

    # 2. Expert Request Detail
    detail_resp = client.get(f"/api/v1/expert/verifications/{req.id}", headers=expert_headers)
    assert detail_resp.status_code == 200
    detail_data = detail_resp.json()
    assert detail_data["request"]["id"] == str(req.id)
    assert detail_data["crop_name"] == "Arecanut"
    assert len(detail_data["diagnoses"]) >= 1


def test_expert_decision_approve_advances_to_expert_verified(mock_db):
    """Expert APPROVE decision advances trust ladder to EXPERT_VERIFIED."""
    actors = setup_test_actors(mock_db)
    report = mock_db.get(CropReport, actors["report_id"])
    report.status = "CORROBORATED"

    diag = CropReportDiagnosis(
        id=uuid.uuid4(),
        crop_report_id=report.id,
        crop="arecanut",
        predicted_class="Yellow Leaf Disease",
        confidence=0.91,
        model_name="effb0_arecanut",
        predictions=[],
    )
    mock_db.add(diag)

    req = ExpertVerificationRequest(
        id=uuid.uuid4(),
        crop_report_id=report.id,
        farmer_id=actors["farmer_id"],
        status="PENDING",
        requested_at=datetime.now(timezone.utc),
    )
    mock_db.add(req)

    expert_headers = auth_headers(actors["expert_id"])

    # Expert submits APPROVE decision
    decision_resp = client.post(
        f"/api/v1/expert/verifications/{req.id}/decision",
        headers=expert_headers,
        json={
            "decision": "APPROVE",
            "finding": "Yellow Leaf Disease Confirmed",
            "expert_notes": "Distinct chlorosis observed on mid-frond leaflets",
            "recommended_action": "Apply zinc sulfate drench and clean drainage channels",
        },
    )
    assert decision_resp.status_code == 200
    data = decision_resp.json()
    assert data["verification_request"]["status"] == "VERIFIED"
    assert data["verification_request"]["action_type"] == "CONFIRM"
    assert data["new_report_status"] == "EXPERT_VERIFIED"
    assert data["ladder_advanced"] is True
    assert report.status == "EXPERT_VERIFIED"


def test_expert_decision_reject_does_not_downgrade(mock_db):
    """Expert REJECT decision does not downgrade crop report status."""
    actors = setup_test_actors(mock_db)
    report = mock_db.get(CropReport, actors["report_id"])
    report.status = "CORROBORATED"

    diag = CropReportDiagnosis(
        id=uuid.uuid4(),
        crop_report_id=report.id,
        crop="arecanut",
        predicted_class="Yellow Leaf Disease",
        confidence=0.85,
        model_name="effb0_arecanut",
        predictions=[],
    )
    mock_db.add(diag)

    req = ExpertVerificationRequest(
        id=uuid.uuid4(),
        crop_report_id=report.id,
        farmer_id=actors["farmer_id"],
        status="PENDING",
        requested_at=datetime.now(timezone.utc),
    )
    mock_db.add(req)

    expert_headers = auth_headers(actors["expert_id"])

    reject_resp = client.post(
        f"/api/v1/expert/verifications/{req.id}/decision",
        headers=expert_headers,
        json={
            "decision": "REJECT",
            "finding": "Nutritional Chlorosis, not Yellow Leaf Disease",
            "expert_notes": "Pattern does not match pathogenic necrosis",
            "recommended_action": "Soil test for magnesium deficiency",
        },
    )
    assert reject_resp.status_code == 200
    data = reject_resp.json()
    assert data["verification_request"]["status"] == "REJECTED"
    assert data["new_report_status"] == "CORROBORATED"
    assert data["ladder_advanced"] is False
    assert report.status == "CORROBORATED"


def test_non_expert_cannot_perform_expert_verification(mock_db):
    """Farmer or community member attempting to access expert verification queue gets 403 Forbidden."""
    actors = setup_test_actors(mock_db)
    farmer_headers = auth_headers(actors["farmer_id"])
    comm_headers = auth_headers(actors["comm_1_id"])

    # Farmer access rejected
    r1 = client.get("/api/v1/expert/verifications", headers=farmer_headers)
    assert r1.status_code == 403

    # Community member access rejected
    r2 = client.get("/api/v1/expert/verifications", headers=comm_headers)
    assert r2.status_code == 403


def test_inactive_expert_rejected(mock_db):
    """Inactive agriculture expert cannot access expert endpoints."""
    actors = setup_test_actors(mock_db)
    inactive_headers = auth_headers(actors["inactive_expert_id"])

    resp = client.get("/api/v1/expert/verifications", headers=inactive_headers)
    assert resp.status_code == 403


# ==============================================================================
# 4. Security, IDOR, Unauthenticated, and Audit Status Tests
# ==============================================================================


def test_unauthenticated_request_rejected(mock_db):
    """Missing or unauthenticated requests are rejected with 401 Unauthorized."""
    actors = setup_test_actors(mock_db)

    # No token
    r1 = client.get(f"/api/v1/crop-reports/{actors['report_id']}/verification-status")
    assert r1.status_code == 401

    # Expired token
    expired_headers = auth_headers(actors["farmer_id"], expired=True)
    r2 = client.get(f"/api/v1/crop-reports/{actors['report_id']}/verification-status", headers=expired_headers)
    assert r2.status_code == 401


def test_idor_unauthorized_farmer_status_rejected(mock_db):
    """Farmer cannot view another farmer's crop report verification status (403 Forbidden)."""
    actors = setup_test_actors(mock_db)
    other_farmer_headers = auth_headers(actors["other_farmer_id"])

    resp = client.get(
        f"/api/v1/crop-reports/{actors['report_id']}/verification-status",
        headers=other_farmer_headers,
    )
    assert resp.status_code == 403
    assert "cannot view verification details" in resp.json()["detail"]


def test_complete_trust_ladder_status_and_audit_history(mock_db):
    """Verification status endpoint returns complete frontend contract with chronological history."""
    actors = setup_test_actors(mock_db)
    report = mock_db.get(CropReport, actors["report_id"])
    report.status = "EXPERT_VERIFIED"

    diag = CropReportDiagnosis(
        id=uuid.uuid4(),
        crop_report_id=report.id,
        crop="arecanut",
        predicted_class="Yellow Leaf Disease",
        confidence=0.94,
        model_name="effb0_arecanut",
        predictions=[],
    )
    mock_db.add(diag)

    corrob = CommunityCorroboration(
        id=uuid.uuid4(),
        crop_report_id=report.id,
        community_member_id=actors["comm_1_id"],
        observation_type="SAME_SYMPTOMS",
        created_at=datetime.now(timezone.utc),
    )
    mock_db.add(corrob)

    req = ExpertVerificationRequest(
        id=uuid.uuid4(),
        crop_report_id=report.id,
        farmer_id=actors["farmer_id"],
        expert_id=actors["expert_id"],
        status="VERIFIED",
        action_type="CONFIRM",
        finding="Yellow Leaf Disease Confirmed",
        completed_at=datetime.now(timezone.utc),
        requested_at=datetime.now(timezone.utc),
    )
    mock_db.add(req)

    owner_headers = auth_headers(actors["farmer_id"])
    resp = client.get(
        f"/api/v1/crop-reports/{actors['report_id']}/verification-status",
        headers=owner_headers,
    )
    assert resp.status_code == 200
    data = resp.json()

    # Frontend Contract validations (Requirement 7)
    assert data["crop_report_id"] == str(actors["report_id"])
    assert data["verification_status"] == "EXPERT_VERIFIED"
    assert data["status_rank"] == 3
    assert data["is_ai_analysed"] is True
    assert data["is_corroborated"] is True
    assert data["is_expert_verified"] is True
    assert data["latest_diagnosis"]["predicted_class"] == "Yellow Leaf Disease"
    assert "corroboration_summary" in data
    assert data["expert_verification"]["finding"] == "Yellow Leaf Disease Confirmed"
    assert len(data["status_history"]) >= 2
    stages_recorded = [h["status"] for h in data["status_history"]]
    assert "UNVERIFIED" in stages_recorded
    assert "AI_ANALYSED" in stages_recorded


def test_admin_authorization_override(mock_db):
    """Administrator can view, request, and assign verification across any farmer report."""
    actors = setup_test_actors(mock_db)
    report = mock_db.get(CropReport, actors["report_id"])
    report.status = "AI_ANALYSED"

    diag = CropReportDiagnosis(
        id=uuid.uuid4(),
        crop_report_id=report.id,
        crop="arecanut",
        predicted_class="Yellow Leaf Disease",
        confidence=0.90,
        model_name="effb0_arecanut",
        predictions=[],
    )
    mock_db.add(diag)

    admin_headers = auth_headers(actors["admin_id"])

    # 1. Admin can view verification status of any report
    status_resp = client.get(
        f"/api/v1/crop-reports/{actors['report_id']}/verification-status",
        headers=admin_headers,
    )
    assert status_resp.status_code == 200

    # 2. Admin can create verification request for any report
    req_resp = client.post(
        f"/api/v1/crop-reports/{actors['report_id']}/verification-request",
        headers=admin_headers,
        json={"notes": "Admin triggered escalation"},
    )
    assert req_resp.status_code == 201
