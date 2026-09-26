"""API endpoints for farmer authentication and session lifecycle."""
import logging
from typing import Dict
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
