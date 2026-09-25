"""Authentication and Role-Based Access Control (RBAC) dependencies."""
import logging
from typing import Callable, List, Optional
import uuid

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from pydantic import BaseModel, ConfigDict
from sqlalchemy.orm import Session

from app.core.security import decode_supabase_jwt
from app.database.connection import get_db
from app.models.role import UserRole
from app.models.user_profile import UserProfile

logger = logging.getLogger(__name__)

# FastAPI security scheme for Bearer token extraction
oauth2_scheme = HTTPBearer(auto_error=False)


class AuthenticatedUser(BaseModel):
    """Domain model representing an authenticated user identity and active roles."""

    model_config = ConfigDict(from_attributes=True)

    id: uuid.UUID
    email: Optional[str] = None
    roles: List[str] = []
    is_active: bool = True

    def has_role(self, role_code: str) -> bool:
        """Check if user has a specific role (case-insensitive) or ADMIN."""
        normalized = role_code.strip().upper()
        return "ADMIN" in self.roles or normalized in self.roles


def get_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> AuthenticatedUser:
    """Validate Supabase JWT and resolve authenticated user identity and roles.

    Args:
        credentials: Bearer token from the Authorization header.
        db: Active database session.

    Returns:
        AuthenticatedUser: The validated user with assigned role codes.

    Raises:
        HTTPException(401): If Bearer token is missing, invalid, or expired.
    """
    if credentials is None or not credentials.credentials:
        logger.warning("Unauthenticated request: missing Bearer token in Authorization header.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required. Please provide a valid Bearer token.",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials
    payload = decode_supabase_jwt(token)

    # Supabase standard subject claim stores user UUID
    sub = payload.get("sub") or payload.get("user_id")
    if not sub:
        logger.warning("Invalid token payload: missing 'sub' claim.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token payload: missing subject identifier",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        user_uuid = uuid.UUID(str(sub))
    except (ValueError, TypeError) as exc:
        logger.warning("Invalid user ID UUID format in token.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid user ID format in token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    # Query active role codes from the source-of-truth user_roles table
    try:
        role_rows = (
            db.query(UserRole.role_code)
            .filter(
                UserRole.user_id == user_uuid,
                UserRole.status == "ACTIVE",
            )
            .all()
        )
        assigned_roles = [r[0] for r in role_rows]
    except Exception as exc:
        logger.error("Failed to query user roles from database for %s: %s", user_uuid, exc, exc_info=True)
        # If DB query fails, treat as empty roles
        assigned_roles = []

    email = payload.get("email")

    return AuthenticatedUser(
        id=user_uuid,
        email=email,
        roles=assigned_roles,
        is_active=True,
    )


def require_role(*required_roles: str) -> Callable[[AuthenticatedUser], AuthenticatedUser]:
    """Create a FastAPI dependency requiring at least one of the specified roles.

    Rules:
        - 401: Raised if user is unauthenticated (handled by get_current_user).
        - 403: Raised if user is authenticated but lacks required role.
        - ADMIN role bypasses role-specific restrictions.

    Args:
        *required_roles: Role code(s) required (e.g. 'FARMER', 'ADMIN').

    Returns:
        Callable[[AuthenticatedUser], AuthenticatedUser]: Role validator dependency.
    """
    normalized_required = {r.strip().upper() for r in required_roles}

    def role_checker(
        current_user: AuthenticatedUser = Depends(get_current_user),
    ) -> AuthenticatedUser:
        user_roles_set = set(current_user.roles)

        # Allow if user is ADMIN or has any of the required roles
        if "ADMIN" in user_roles_set or bool(user_roles_set & normalized_required):
            return current_user

        logger.warning(
            "Access forbidden for user %s: has roles %s, requires one of %s",
            current_user.id,
            current_user.roles,
            list(normalized_required),
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=f"Access forbidden: Insufficient role permissions. Required: {', '.join(sorted(normalized_required))}",
        )

    return role_checker


# Convenience role dependencies
require_farmer = require_role("FARMER")
require_expert = require_role("AGRICULTURE_EXPERT")
require_government_officer = require_role("GOVERNMENT_OFFICER")
require_buyer = require_role("BUYER")
require_community_member = require_role("COMMUNITY_MEMBER")
require_admin = require_role("ADMIN")


def verify_farmer_access(
    farmer_id: uuid.UUID,
    current_user: AuthenticatedUser = Depends(require_role("FARMER")),
) -> AuthenticatedUser:
    """Verify that the authenticated user has the FARMER role and owns the farmer resource.

    Enforces ownership:
        1. Valid authenticated Supabase JWT
        2. FARMER role
        3. farmer_id == authenticated user ID (or user is ADMIN)

    Args:
        farmer_id: Target farmer UUID from path parameter.
        current_user: Validated user from require_role('FARMER').

    Returns:
        AuthenticatedUser: The validated farmer user.

    Raises:
        HTTPException(403): If the authenticated farmer attempts to access another farmer's resource.
    """
    if current_user.id != farmer_id and "ADMIN" not in current_user.roles:
        logger.warning(
            "IDOR attempt blocked: User %s tried to access farmer resource %s",
            current_user.id,
            farmer_id,
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access forbidden: You do not have permission to access another farmer's data",
        )

    return current_user


def get_optional_current_user(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(oauth2_scheme),
    db: Session = Depends(get_db),
) -> Optional[AuthenticatedUser]:
    """Resolve authenticated user if Bearer token is provided, or return None if unauthenticated."""
    if credentials is None or not credentials.credentials:
        return None
    try:
        return get_current_user(credentials=credentials, db=db)
    except Exception:
        return None
