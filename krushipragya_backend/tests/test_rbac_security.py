"""Security and RBAC test suite for KrushiPragya backend.

Validates:
1. Supabase JWT authentication enforcement (401 on missing/expired/invalid token).
2. Role-based access control (403 when user lacks required role).
3. Farmer resource ownership enforcement (403 IDOR rejection when farmer_id != user_id).
4. ADMIN role authorization override.
5. Successful authorized access when token, role, and ownership align.
"""
from datetime import datetime, timedelta, timezone
from typing import Dict, List
import uuid
import pytest
from fastapi import APIRouter, Depends, status
from fastapi.testclient import TestClient

import jwt
from app.core.auth import (
    AuthenticatedUser,
    get_current_user,
    require_admin,
    require_buyer,
    require_community_member,
    require_expert,
    require_farmer,
    require_government_officer,
    require_role,
    verify_farmer_access,
)
from app.core.config import settings
from app.core.security import create_access_token
from app.database.connection import get_db
from app.main import app
from app.models.crop import Crop
from app.models.farmer_crop import FarmerCrop
from app.models.role import Role, UserRole
from app.models.user_profile import UserProfile

client = TestClient(app)

# Router to verify role guard dependencies in isolation
guard_router = APIRouter(prefix="/api/test-rbac", tags=["Test RBAC"])


@guard_router.get("/farmer-only")
def farmer_endpoint(user: AuthenticatedUser = Depends(require_farmer)):
    return {"status": "ok", "role": "FARMER", "user_id": str(user.id)}


@guard_router.get("/expert-only")
def expert_endpoint(user: AuthenticatedUser = Depends(require_expert)):
    return {"status": "ok", "role": "AGRICULTURE_EXPERT", "user_id": str(user.id)}


@guard_router.get("/govt-only")
def govt_endpoint(user: AuthenticatedUser = Depends(require_government_officer)):
    return {"status": "ok", "role": "GOVERNMENT_OFFICER", "user_id": str(user.id)}


@guard_router.get("/buyer-only")
def buyer_endpoint(user: AuthenticatedUser = Depends(require_buyer)):
    return {"status": "ok", "role": "BUYER", "user_id": str(user.id)}


@guard_router.get("/community-only")
def community_endpoint(user: AuthenticatedUser = Depends(require_community_member)):
    return {"status": "ok", "role": "COMMUNITY_MEMBER", "user_id": str(user.id)}


@guard_router.get("/admin-only")
def admin_endpoint(user: AuthenticatedUser = Depends(require_admin)):
    return {"status": "ok", "role": "ADMIN", "user_id": str(user.id)}


# Include test router once
if not any(getattr(r, "path", None) == "/api/test-rbac/farmer-only" for r in app.routes):
    app.include_router(guard_router)


class MockSecurityDBSession:
    """Mock database session populated with test users and roles."""

    def __init__(self):
        self.users: Dict[uuid.UUID, UserProfile] = {}
        self.roles: Dict[str, Role] = {}
        self.user_roles: List[UserRole] = []
        self.farmer_crops: Dict[uuid.UUID, FarmerCrop] = {}
        self.crops: Dict[uuid.UUID, Crop] = {}

    def get(self, model, entity_id):
        if model is UserProfile:
            return self.users.get(entity_id)
        if model is Crop:
            return self.crops.get(entity_id)
        if model is FarmerCrop:
            return self.farmer_crops.get(entity_id)
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

    def commit(self):
        pass

    def rollback(self):
        pass

    def refresh(self, entity):
        pass

    def query(self, *entities):
        return MockQuery(self, entities)


class MockQuery:
    def __init__(self, session: MockSecurityDBSession, entities):
        self.session = session
        self.entities = entities
        self._user_id_filter = None
        self._farmer_id_filter = None
        self._status_filter = None
        self._role_code_filter = None

    def filter(self, *criteria):
        for c in criteria:
            c_str = str(c)
            if "user_id" in c_str and hasattr(c, "right") and hasattr(c.right, "value"):
                self._user_id_filter = c.right.value
            if "farmer_id" in c_str and hasattr(c, "right") and hasattr(c.right, "value"):
                self._farmer_id_filter = c.right.value
            if "status" in c_str and hasattr(c, "right") and hasattr(c.right, "value"):
                self._status_filter = c.right.value
            if "role_code" in c_str and hasattr(c, "right") and hasattr(c.right, "value"):
                self._role_code_filter = c.right.value
        return self

    def options(self, *args, **kwargs):
        return self

    def order_by(self, *args, **kwargs):
        return self

    def all(self):
        # If querying UserRole
        entity_names = [str(e) for e in self.entities]
        if any("role" in name.lower() for name in entity_names):
            results = []
            for ur in self.session.user_roles:
                if self._user_id_filter and ur.user_id != self._user_id_filter:
                    continue
                if self._role_code_filter and ur.role_code != self._role_code_filter:
                    continue
                if self._status_filter and ur.status != self._status_filter:
                    continue
                if len(self.entities) == 1 and not isinstance(self.entities[0], type):
                    results.append((ur.role_code,))
                else:
                    results.append(ur)
            return results

        # If querying FarmerCrop
        if any("farmer_crop" in name.lower() for name in entity_names):
            results = []
            for fc in self.session.farmer_crops.values():
                if self._farmer_id_filter and fc.farmer_id != self._farmer_id_filter:
                    continue
                results.append(fc)
            return results

        return []

    def first(self):
        res = self.all()
        return res[0] if res else None


@pytest.fixture
def security_db():
    session = MockSecurityDBSession()
    app.dependency_overrides[get_db] = lambda: session
    yield session
    app.dependency_overrides.pop(get_db, None)


def auth_header(user_id: uuid.UUID, email: str = "user@krushipragya.com", expired: bool = False) -> Dict[str, str]:
    """Helper to mint a Bearer token header."""
    delta = timedelta(minutes=-10) if expired else timedelta(hours=1)
    token = create_access_token(
        data={"sub": str(user_id), "email": email, "aud": "authenticated"},
        expires_delta=delta,
    )
    return {"Authorization": f"Bearer {token}"}


# ==============================================================================
# 1. Unauthenticated Requests (401)
# ==============================================================================

def test_missing_token_returns_401():
    """Unauthenticated request to protected endpoint returns 401."""
    farmer_id = uuid.uuid4()
    response = client.get(f"/api/v1/farmers/{farmer_id}/crops")
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "detail" in response.json()


def test_malformed_token_returns_401():
    """Malformed or invalid JWT returns 401."""
    farmer_id = uuid.uuid4()
    response = client.get(
        f"/api/v1/farmers/{farmer_id}/crops",
        headers={"Authorization": "Bearer this-is-not-a-valid-jwt"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_expired_token_returns_401():
    """Expired token returns 401."""
    farmer_id = uuid.uuid4()
    headers = auth_header(farmer_id, expired=True)
    response = client.get(f"/api/v1/farmers/{farmer_id}/crops", headers=headers)
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "expired" in response.json()["detail"].lower()


# ==============================================================================
# 2. Role Guards Enforcement (403)
# ==============================================================================

def test_insufficient_role_returns_403(security_db):
    """User with BUYER role attempting to access FARMER endpoint is rejected with 403."""
    buyer_id = uuid.uuid4()
    security_db.user_roles.append(UserRole(user_id=buyer_id, role_code="BUYER", status="ACTIVE"))

    headers = auth_header(buyer_id)
    response = client.get("/api/test-rbac/farmer-only", headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "FARMER" in response.json()["detail"]


def test_role_guards_grant_access_for_matching_role(security_db):
    """Users with appropriate roles successfully access their respective endpoints."""
    # 1. Farmer
    farmer_id = uuid.uuid4()
    security_db.user_roles.append(UserRole(user_id=farmer_id, role_code="FARMER", status="ACTIVE"))
    res = client.get("/api/test-rbac/farmer-only", headers=auth_header(farmer_id))
    assert res.status_code == 200
    assert res.json()["role"] == "FARMER"

    # 2. Expert
    expert_id = uuid.uuid4()
    security_db.user_roles.append(UserRole(user_id=expert_id, role_code="AGRICULTURE_EXPERT", status="ACTIVE"))
    res = client.get("/api/test-rbac/expert-only", headers=auth_header(expert_id))
    assert res.status_code == 200
    assert res.json()["role"] == "AGRICULTURE_EXPERT"

    # 3. Government Officer
    govt_id = uuid.uuid4()
    security_db.user_roles.append(UserRole(user_id=govt_id, role_code="GOVERNMENT_OFFICER", status="ACTIVE"))
    res = client.get("/api/test-rbac/govt-only", headers=auth_header(govt_id))
    assert res.status_code == 200
    assert res.json()["role"] == "GOVERNMENT_OFFICER"

    # 4. Buyer
    buyer_id = uuid.uuid4()
    security_db.user_roles.append(UserRole(user_id=buyer_id, role_code="BUYER", status="ACTIVE"))
    res = client.get("/api/test-rbac/buyer-only", headers=auth_header(buyer_id))
    assert res.status_code == 200
    assert res.json()["role"] == "BUYER"

    # 5. Community Member
    cm_id = uuid.uuid4()
    security_db.user_roles.append(UserRole(user_id=cm_id, role_code="COMMUNITY_MEMBER", status="ACTIVE"))
    res = client.get("/api/test-rbac/community-only", headers=auth_header(cm_id))
    assert res.status_code == 200
    assert res.json()["role"] == "COMMUNITY_MEMBER"


def test_admin_role_can_access_any_role_endpoint(security_db):
    """ADMIN role bypasses role-specific restriction and can access any guard."""
    admin_id = uuid.uuid4()
    security_db.user_roles.append(UserRole(user_id=admin_id, role_code="ADMIN", status="ACTIVE"))
    headers = auth_header(admin_id)

    assert client.get("/api/test-rbac/farmer-only", headers=headers).status_code == 200
    assert client.get("/api/test-rbac/expert-only", headers=headers).status_code == 200
    assert client.get("/api/test-rbac/govt-only", headers=headers).status_code == 200
    assert client.get("/api/test-rbac/buyer-only", headers=headers).status_code == 200
    assert client.get("/api/test-rbac/community-only", headers=headers).status_code == 200


# ==============================================================================
# 3. Farmer Ownership & IDOR Protection (403)
# ==============================================================================

def test_farmer_a_accessing_farmer_b_profile_returns_403(security_db):
    """Farmer A cannot access Farmer B's profile (IDOR blocked)."""
    farmer_a_id = uuid.uuid4()
    farmer_b_id = uuid.uuid4()

    # Assign FARMER role to Farmer A
    security_db.user_roles.append(UserRole(user_id=farmer_a_id, role_code="FARMER", status="ACTIVE"))

    # Farmer A tries to read Farmer B's profile
    headers = auth_header(farmer_a_id)
    response = client.get(f"/api/v1/farmers/profile/{farmer_b_id}", headers=headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "permission" in response.json()["detail"].lower()


def test_farmer_a_accessing_farmer_b_crops_returns_403(security_db):
    """Farmer A cannot access Farmer B's crop portfolio (IDOR blocked)."""
    farmer_a_id = uuid.uuid4()
    farmer_b_id = uuid.uuid4()

    security_db.user_roles.append(UserRole(user_id=farmer_a_id, role_code="FARMER", status="ACTIVE"))

    headers = auth_header(farmer_a_id)
    response = client.get(f"/api/v1/farmers/{farmer_b_id}/crops", headers=headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "permission" in response.json()["detail"].lower()


def test_farmer_a_cannot_post_crop_report_for_farmer_b(security_db):
    """Farmer A cannot create a crop report under Farmer B's identity (IDOR blocked)."""
    farmer_a_id = uuid.uuid4()
    farmer_b_id = uuid.uuid4()

    security_db.user_roles.append(UserRole(user_id=farmer_a_id, role_code="FARMER", status="ACTIVE"))

    headers = auth_header(farmer_a_id)
    payload = {
        "farmer_crop_id": str(uuid.uuid4()),
        "notes": "Forged observation",
    }
    response = client.post(f"/api/v1/farmers/{farmer_b_id}/crop-reports", json=payload, headers=headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_farmer_a_cannot_request_advisory_for_farmer_b(security_db):
    """Farmer A cannot invoke LLM advisory under Farmer B's account (IDOR blocked)."""
    farmer_a_id = uuid.uuid4()
    farmer_b_id = uuid.uuid4()

    security_db.user_roles.append(UserRole(user_id=farmer_a_id, role_code="FARMER", status="ACTIVE"))

    headers = auth_header(farmer_a_id)
    response = client.post(f"/api/v1/farmers/{farmer_b_id}/advisory", json={}, headers=headers)

    assert response.status_code == status.HTTP_403_FORBIDDEN


def test_farmer_a_can_access_own_crops(security_db):
    """Farmer A with valid token and FARMER role can successfully query own crops."""
    farmer_a_id = uuid.uuid4()
    security_db.user_roles.append(UserRole(user_id=farmer_a_id, role_code="FARMER", status="ACTIVE"))

    # Seed profile and crops in in-memory session
    profile = UserProfile(id=farmer_a_id, full_name="Ramesh Gowda")
    security_db.users[farmer_a_id] = profile

    headers = auth_header(farmer_a_id)
    response = client.get(f"/api/v1/farmers/{farmer_a_id}/crops", headers=headers)

    assert response.status_code == status.HTTP_200_OK
    assert isinstance(response.json(), list)


def test_admin_can_access_any_farmer_crops(security_db):
    """ADMIN role can access another farmer's resources for support/administrative purposes."""
    admin_id = uuid.uuid4()
    farmer_b_id = uuid.uuid4()

    security_db.user_roles.append(UserRole(user_id=admin_id, role_code="ADMIN", status="ACTIVE"))
    security_db.users[farmer_b_id] = UserProfile(id=farmer_b_id, full_name="Suresh Kumar")

    headers = auth_header(admin_id)
    response = client.get(f"/api/v1/farmers/{farmer_b_id}/crops", headers=headers)

    assert response.status_code == status.HTTP_200_OK


# ==============================================================================
# 4. Inactive Roles, Tampered Tokens & Profile Creation Safety
# ==============================================================================

def test_unsigned_none_algorithm_token_rejected_with_401():
    """Unsigned tokens (algorithm 'none') are strictly rejected with 401."""
    user_id = uuid.uuid4()
    # Create token with alg=none (no signature)
    token = jwt.encode({"sub": str(user_id), "aud": "authenticated"}, key="", algorithm="none")
    response = client.get(
        f"/api/v1/farmers/{user_id}/crops",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_invalid_sub_format_non_uuid_returns_401():
    """Tokens with a non-UUID 'sub' claim are rejected with 401."""
    token = create_access_token(
        data={"sub": "not-a-valid-uuid-string", "aud": "authenticated"},
    )
    response = client.get(
        f"/api/v1/farmers/{uuid.uuid4()}/crops",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "invalid user id format" in response.json()["detail"].lower()


def test_token_missing_sub_returns_401():
    """Tokens missing 'sub' claim are rejected with 401."""
    token = create_access_token(
        data={"email": "no_sub@krushipragya.com", "aud": "authenticated"},
    )
    response = client.get(
        f"/api/v1/farmers/{uuid.uuid4()}/crops",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED
    assert "missing subject" in response.json()["detail"].lower()


def test_token_signed_with_wrong_secret_returns_401():
    """Tokens signed with an incorrect secret are rejected with 401."""
    user_id = uuid.uuid4()
    tampered_token = jwt.encode(
        {"sub": str(user_id), "aud": "authenticated"},
        key="completely-wrong-unauthorized-secret-key-12345",
        algorithm="HS256",
    )
    response = client.get(
        f"/api/v1/farmers/{user_id}/crops",
        headers={"Authorization": f"Bearer {tampered_token}"},
    )
    assert response.status_code == status.HTTP_401_UNAUTHORIZED


def test_suspended_and_revoked_roles_are_rejected_with_403(security_db):
    """Users with SUSPENDED or REVOKED roles are rejected with 403."""
    suspended_user_id = uuid.uuid4()
    revoked_user_id = uuid.uuid4()

    security_db.user_roles.append(
        UserRole(user_id=suspended_user_id, role_code="FARMER", status="SUSPENDED")
    )
    security_db.user_roles.append(
        UserRole(user_id=revoked_user_id, role_code="FARMER", status="REVOKED")
    )

    suspended_headers = auth_header(suspended_user_id)
    revoked_headers = auth_header(revoked_user_id)

    res_suspended = client.get("/api/test-rbac/farmer-only", headers=suspended_headers)
    assert res_suspended.status_code == status.HTTP_403_FORBIDDEN

    res_revoked = client.get("/api/test-rbac/farmer-only", headers=revoked_headers)
    assert res_revoked.status_code == status.HTTP_403_FORBIDDEN


def test_farmer_profile_create_cross_user_returns_403(security_db):
    """Authenticated user cannot create profile for a different user UUID."""
    logged_in_id = uuid.uuid4()
    victim_id = uuid.uuid4()

    headers = auth_header(logged_in_id)
    payload = {
        "id": str(victim_id),
        "full_name": "Ramesh Impersonator",
        "phone": "9876543210",
        "village_id": "VILL-001",
        "language": "kn",
        "land_holding_acres": 3.5,
    }
    response = client.post("/api/v1/farmers/profile", json=payload, headers=headers)
    assert response.status_code == status.HTTP_403_FORBIDDEN
    assert "another user id" in response.json()["detail"].lower()


def test_farmer_profile_create_assigns_farmer_role_safely(security_db):
    """Creating own profile safely creates profile and assigns FARMER role."""
    new_user_id = uuid.uuid4()

    headers = auth_header(new_user_id)
    payload = {
        "id": str(new_user_id),
        "full_name": "Siddaramaiah Gowda",
        "phone": "9988776655",
        "village_id": "VILL-005",
        "language": "kn",
        "land_holding_acres": 5.0,
    }
    response = client.post("/api/v1/farmers/profile", json=payload, headers=headers)
    assert response.status_code == status.HTTP_201_CREATED
    assert response.json()["id"] == str(new_user_id)

    # Verify FARMER role was added in user_roles
    roles = [ur.role_code for ur in security_db.user_roles if ur.user_id == new_user_id and ur.status == "ACTIVE"]
    assert "FARMER" in roles

