"""Pytest global configuration and legacy test compatibility fixtures."""
import json
from typing import Optional
import uuid
import pytest
from fastapi import Request

from app.core.auth import AuthenticatedUser, get_current_user, verify_farmer_access
from app.main import app


@pytest.fixture(autouse=True)
def legacy_auth_compatibility(request):
    """Automatically mock authentication for legacy unit tests that do not send tokens.

    Tests in 'test_rbac' explicitly test authentication and authorization, so they
    run against the live, unmocked security dependencies.
    """
    if (
        "test_rbac" in request.node.nodeid
        or "test_market" in request.node.nodeid
        or "test_verification" in request.node.nodeid
    ):
        yield
        return

    # Mock verify_farmer_access for legacy tests so farmer_id matches authenticated user
    def mock_verify_farmer_access(farmer_id: uuid.UUID) -> AuthenticatedUser:
        return AuthenticatedUser(
            id=farmer_id,
            email=f"legacy_{farmer_id}@krushipragya.com",
            roles=["FARMER"],
            is_active=True,
        )

    # Mock get_current_user for legacy tests
    async def mock_get_current_user(http_req: Request) -> AuthenticatedUser:
        # Check if caller sent a JSON body with an id
        user_id = uuid.UUID("11111111-1111-4111-8111-111111111111")
        try:
            body_bytes = await http_req.body()
            if body_bytes:
                data = json.loads(body_bytes)
                if isinstance(data, dict) and "id" in data:
                    user_id = uuid.UUID(str(data["id"]))
        except Exception:
            pass

        return AuthenticatedUser(
            id=user_id,
            email="farmer@krushipragya.com",
            roles=["FARMER"],
            is_active=True,
        )

    app.dependency_overrides[verify_farmer_access] = mock_verify_farmer_access
    app.dependency_overrides[get_current_user] = mock_get_current_user

    yield

    app.dependency_overrides.pop(verify_farmer_access, None)
    app.dependency_overrides.pop(get_current_user, None)
