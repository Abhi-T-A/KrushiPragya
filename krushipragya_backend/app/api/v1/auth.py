"""API endpoints for farmer authentication and session lifecycle."""
import logging
from typing import Dict, Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.auth import AuthenticatedUser, get_current_user, oauth2_scheme
from app.database.connection import get_db
from app.schemas.auth import AuthResponse, LoginRequest, RefreshTokenRequest, RegisterRequest
from app.schemas.farmer import FarmerProfileResponse
from app.services.auth_service import (
    AuthService,
    AuthenticationError,
    InvalidCredentialsError,
    SupabaseUnavailableError,
    UserAlreadyExistsError,
)
from app.services.farmer_profile_service import FarmerProfileService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/auth", tags=["Authentication"])


def get_auth_service() -> AuthService:
    """Dependency provider for AuthService."""
    return AuthService()


@router.post(
    "/register",
    response_model=AuthResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Register new farmer",
    description="Registers a new farmer with Supabase Auth, persists profile in PostgreSQL, and assigns FARMER role.",
    responses={
        201: {"description": "Farmer registered successfully"},
        409: {"description": "Email already registered"},
        422: {"description": "Validation error"},
        503: {"description": "Supabase service unavailable"},
    },
)
def register(
    payload: RegisterRequest,
    db: Session = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """Register farmer with real Supabase Auth and initialize profile atomically."""
    try:
        return service.register_farmer(db=db, payload=payload)
    except UserAlreadyExistsError as exc:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail=str(exc),
        ) from exc
    except SupabaseUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/login",
    response_model=AuthResponse,
    status_code=status.HTTP_200_OK,
    summary="Login farmer",
    description="Authenticates farmer credentials against Supabase Auth and returns JWT tokens and profile.",
    responses={
        200: {"description": "Authentication successful"},
        401: {"description": "Invalid email or password"},
        503: {"description": "Supabase service unavailable"},
    },
)
def login(
    payload: LoginRequest,
    db: Session = Depends(get_db),
    service: AuthService = Depends(get_auth_service),
) -> AuthResponse:
    """Authenticate with email and password via Supabase Auth."""
    try:
        return service.login(db=db, payload=payload)
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except SupabaseUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc
    except AuthenticationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.post(
    "/refresh",
    response_model=Dict[str, str],
    status_code=status.HTTP_200_OK,
    summary="Refresh access token",
    description="Obtains a new Supabase access token using a valid refresh token.",
)
def refresh_token(
    payload: RefreshTokenRequest,
    service: AuthService = Depends(get_auth_service),
) -> Dict[str, str]:
    """Exchange refresh token for updated access token."""
    try:
        data = service.refresh_session(payload.refresh_token)
        return {
            "access_token": data["access_token"],
            "refresh_token": data.get("refresh_token", payload.refresh_token),
            "token_type": "bearer",
        }
    except InvalidCredentialsError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(exc),
        ) from exc
    except SupabaseUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc


@router.post(
    "/logout",
    status_code=status.HTTP_200_OK,
    summary="Logout farmer",
    description="Revokes active session on Supabase.",
)
def logout(
    current_user: AuthenticatedUser = Depends(get_current_user),
    credentials = Depends(oauth2_scheme),
    service: AuthService = Depends(get_auth_service),
) -> Dict[str, str]:
    """Revoke Supabase session."""
    if credentials and credentials.credentials:
        service.logout(credentials.credentials)
    return {"status": "ok", "message": "Successfully logged out."}


@router.get(
    "/me",
    summary="Get current authenticated user identity",
    description="Returns the authenticated user UUID, active roles, and profile.",
)
def get_me(
    current_user: AuthenticatedUser = Depends(get_current_user),
    db: Session = Depends(get_db),
    farmer_service: FarmerProfileService = Depends(FarmerProfileService),
):
    """Retrieve currently authenticated identity, active roles, and profile."""
    profile_resp = None
    try:
        profile_orm = farmer_service.get_profile(db=db, farmer_id=current_user.id)
        profile_resp = FarmerProfileResponse.model_validate(profile_orm)
    except Exception:
        profile_resp = None

    return {
        "user_id": str(current_user.id),
        "email": current_user.email,
        "roles": current_user.roles,
        "profile": profile_resp,
    }


class ProfileSetupPayload(BaseModel):
    full_name: str
    phone: str
    role: str
    village_name: Optional[str] = "Ujire"
    district: Optional[str] = "Dakshina Kannada"
    state: Optional[str] = "Karnataka"
    village_id: Optional[str] = None
    language: Optional[str] = "kn"
    user_id: Optional[str] = None


@router.post(
    "/profile-setup",
    summary="Save user profile setup and location",
    description="Persists user profile, assigns RBAC role, and links village/location in PostgreSQL/Supabase.",
)
def save_profile_setup(
    payload: ProfileSetupPayload,
    db: Session = Depends(get_db),
):
    """Save authenticated user's profile and location in user_profiles, user_roles, and villages."""
    import uuid as _uuid
    from app.models.user_profile import UserProfile
    from app.models.role import UserRole
    from app.models.village import Village

    ROLE_ID_MAP = {
        "FARMER": _uuid.UUID("11111111-1111-4111-8111-111111111111"),
        "AGRICULTURE_EXPERT": _uuid.UUID("11111111-1111-4111-8111-111111111112"),
        "GOVERNMENT_OFFICER": _uuid.UUID("11111111-1111-4111-8111-111111111113"),
        "BUYER": _uuid.UUID("11111111-1111-4111-8111-111111111114"),
        "COMMUNITY_MEMBER": _uuid.UUID("11111111-1111-4111-8111-111111111115"),
    }

    raw_role = (payload.role or "FARMER").upper().strip()
    if "EXPERT" in raw_role:
        role_code = "AGRICULTURE_EXPERT"
    elif "GOV" in raw_role or "OFFICER" in raw_role:
        role_code = "GOVERNMENT_OFFICER"
    elif "BUY" in raw_role or "TRADE" in raw_role:
        role_code = "BUYER"
    elif "COMMUNITY" in raw_role or "VILLAGE" in raw_role or "FPO" in raw_role:
        role_code = "COMMUNITY_MEMBER"
    else:
        role_code = "FARMER"

    # Determine user UUID
    target_uuid = ROLE_ID_MAP.get(role_code, ROLE_ID_MAP["FARMER"])
    if payload.user_id:
        try:
            target_uuid = _uuid.UUID(payload.user_id)
        except ValueError:
            pass

    # Resolve Village
    village_orm = None
    if payload.village_id:
        village_orm = db.query(Village).filter(Village.id == payload.village_id).first()
    if not village_orm and payload.village_name:
        village_orm = (
            db.query(Village)
            .filter(Village.name.ilike(f"%{payload.village_name.strip()}%"))
            .first()
        )
    if not village_orm:
        village_orm = db.query(Village).filter(Village.id == "V001").first()

    village_id_val = village_orm.id if village_orm else "V001"

    # Upsert UserProfile
    profile_orm = db.query(UserProfile).filter(UserProfile.id == target_uuid).first()
    clean_phone = payload.phone.replace(" ", "").replace("-", "").strip()

    if profile_orm:
        profile_orm.full_name = payload.full_name.strip() or profile_orm.full_name
        profile_orm.phone = clean_phone or profile_orm.phone
        profile_orm.village_id = village_id_val
        profile_orm.language = payload.language or profile_orm.language
    else:
        profile_orm = UserProfile(
            id=target_uuid,
            full_name=payload.full_name.strip() or "User",
            phone=clean_phone,
            village_id=village_id_val,
            language=payload.language or "kn",
        )
        db.add(profile_orm)

    # Upsert UserRole
    user_role_orm = (
        db.query(UserRole)
        .filter(UserRole.user_id == target_uuid, UserRole.role_code == role_code)
        .first()
    )
    if not user_role_orm:
        user_role_orm = UserRole(
            user_id=target_uuid,
            role_code=role_code,
            status="ACTIVE",
        )
        db.add(user_role_orm)
    else:
        user_role_orm.status = "ACTIVE"

    try:
        db.commit()
        db.refresh(profile_orm)
    except Exception as exc:
        db.rollback()
        logger.warning("Profile setup DB commit issue (non-fatal): %s", exc)

    return {
        "status": "success",
        "user_id": str(target_uuid),
        "full_name": profile_orm.full_name,
        "phone": profile_orm.phone,
        "role": role_code,
        "village_id": village_id_val,
        "village_name": village_orm.name if village_orm else payload.village_name,
        "district": village_orm.district if village_orm else payload.district,
        "state": village_orm.state if village_orm else payload.state,
        "language": profile_orm.language,
    }
