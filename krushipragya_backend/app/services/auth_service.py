"""Service managing Supabase Auth operations and farmer registration."""
import logging
from typing import Any, Dict, Optional
import uuid

from fastapi import HTTPException, status
import requests
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.role import UserRole
from app.models.user_profile import UserProfile
from app.schemas.auth import AuthResponse, LoginRequest, RefreshTokenRequest, RegisterRequest
from app.schemas.farmer import FarmerProfileCreate, FarmerProfileResponse
from app.services.farmer_profile_service import (
    FarmerProfileAlreadyExistsError,
    FarmerProfileService,
)

logger = logging.getLogger(__name__)


class AuthenticationError(Exception):
    """Base exception for authentication failures."""
    pass


class InvalidCredentialsError(AuthenticationError):
    """Raised on invalid email or password."""
    pass


class UserAlreadyExistsError(AuthenticationError):
    """Raised when an account with the email already exists."""
    pass


class SupabaseUnavailableError(AuthenticationError):
    """Raised when the Supabase auth service is unreachable."""
    pass


class AuthService:
    """Service communicating with Supabase GoTrue Auth REST API."""

    def __init__(self, profile_service: Optional[FarmerProfileService] = None):
        self.profile_service = profile_service or FarmerProfileService()

    @property
    def supabase_url(self) -> str:
        if not settings.SUPABASE_URL:
            raise SupabaseUnavailableError("SUPABASE_URL is not configured.")
        return settings.SUPABASE_URL.rstrip("/")

    @property
    def anon_key(self) -> str:
        return settings.SUPABASE_ANON_KEY or ""

    @property
    def service_role_key(self) -> Optional[str]:
        return settings.SUPABASE_SERVICE_ROLE_KEY

    def register_farmer(
        self,
        db: Session,
        payload: RegisterRequest,
    ) -> AuthResponse:
        """Register a new farmer in Supabase Auth and persist profile with FARMER role.

        Atomic flow:
        1. Register user in Supabase Auth (auto-confirm email via Admin API if service key present).
        2. Authenticate to obtain real access_token and refresh_token.
        3. Create UserProfile in database.
        4. Assign FARMER role in user_roles table.
        5. Return complete AuthResponse.
        """
        user_id_str: Optional[str] = None
        user_id: Optional[uuid.UUID] = None

        # 1. Create user in Supabase Auth
        if self.service_role_key:
            # Use Admin API to auto-confirm email (bypasses email rate limits)
            admin_url = f"{self.supabase_url}/auth/v1/admin/users"
            admin_headers = {
                "apikey": self.service_role_key,
                "Authorization": f"Bearer {self.service_role_key}",
                "Content-Type": "application/json",
            }
            admin_payload = {
                "email": payload.email,
                "password": payload.password,
                "email_confirm": True,
                "user_metadata": {
                    "full_name": payload.full_name,
                    "phone": payload.phone,
                },
            }
            try:
                res = requests.post(admin_url, json=admin_payload, headers=admin_headers, timeout=10)
            except requests.RequestException as exc:
                logger.error("Supabase Admin API unreachable during registration: %s", exc)
                raise SupabaseUnavailableError("Authentication service is temporarily unavailable.") from exc

            if res.status_code == 422 or "already registered" in res.text.lower() or "already exists" in res.text.lower():
                raise UserAlreadyExistsError(f"An account with email '{payload.email}' already exists.")
            elif res.status_code not in (200, 201):
                logger.warning("Supabase Admin user creation failed (%s): %s", res.status_code, res.text)
                err_json = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
                err_msg = err_json.get("msg") or err_json.get("message") or "Failed to create user account"
                raise AuthenticationError(err_msg)

            user_data = res.json()
            user_id_str = user_data.get("id")
            user_id = uuid.UUID(user_id_str)
        else:
            # Fallback to standard public signup endpoint
            signup_url = f"{self.supabase_url}/auth/v1/signup"
            headers = {
                "apikey": self.anon_key,
                "Content-Type": "application/json",
            }
            signup_payload = {
                "email": payload.email,
                "password": payload.password,
                "data": {
                    "full_name": payload.full_name,
                    "phone": payload.phone,
                },
            }
            try:
                res = requests.post(signup_url, json=signup_payload, headers=headers, timeout=10)
            except requests.RequestException as exc:
                raise SupabaseUnavailableError("Authentication service is temporarily unavailable.") from exc

            if res.status_code in (400, 422) and "already registered" in res.text.lower():
                raise UserAlreadyExistsError(f"An account with email '{payload.email}' already exists.")
            elif res.status_code not in (200, 201):
                err_json = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
                raise AuthenticationError(err_json.get("msg", "Failed to create user account"))

            user_data = res.json()
            user_id_str = user_data.get("id") or (user_data.get("user") or {}).get("id")
            user_id = uuid.UUID(user_id_str)

        # 2. Log in to obtain tokens
        tokens = self._supabase_login(payload.email, payload.password)

        # 3 & 4. Persist profile and FARMER role atomically
        profile_create = FarmerProfileCreate(
            id=user_id,
            full_name=payload.full_name,
            phone=payload.phone,
            village_id=payload.village_id,
            language=payload.language,
            land_holding_acres=payload.land_holding_acres,
        )
        try:
            profile_orm = self.profile_service.create_profile(db=db, payload=profile_create)
            profile_resp = FarmerProfileResponse.model_validate(profile_orm)
        except FarmerProfileAlreadyExistsError:
            profile_orm = self.profile_service.get_profile(db=db, farmer_id=user_id)
            profile_resp = FarmerProfileResponse.model_validate(profile_orm)

        return AuthResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens.get("token_type", "bearer"),
            expires_in=tokens.get("expires_in", 3600),
            user_id=user_id,
            email=payload.email,
            roles=["FARMER"],
            profile=profile_resp,
        )

    def login(
        self,
        db: Session,
        payload: LoginRequest,
    ) -> AuthResponse:
        """Authenticate existing farmer against Supabase Auth and load profile & roles."""
        tokens = self._supabase_login(payload.email, payload.password)
        user_info = tokens.get("user") or {}
        user_id_str = user_info.get("id")
        if not user_id_str:
            raise AuthenticationError("Authentication response missing user identifier.")
        user_id = uuid.UUID(user_id_str)

        # Query assigned active roles
        role_codes = []
        if hasattr(db, "query"):
            role_rows = (
                db.query(UserRole.role_code)
                .filter(UserRole.user_id == user_id, UserRole.status == "ACTIVE")
                .all()
            )
            role_codes = [r[0] for r in role_rows]

        # Query profile
        profile_resp = None
        profile_orm = db.get(UserProfile, user_id)
        if profile_orm is not None:
            profile_resp = FarmerProfileResponse.model_validate(profile_orm)

        return AuthResponse(
            access_token=tokens["access_token"],
            refresh_token=tokens["refresh_token"],
            token_type=tokens.get("token_type", "bearer"),
            expires_in=tokens.get("expires_in", 3600),
            user_id=user_id,
            email=payload.email,
            roles=role_codes,
            profile=profile_resp,
        )

    def refresh_session(self, refresh_token: str) -> Dict[str, Any]:
        """Refresh Supabase session using refresh token."""
        url = f"{self.supabase_url}/auth/v1/token?grant_type=refresh_token"
        headers = {
            "apikey": self.anon_key,
            "Content-Type": "application/json",
        }
        payload = {"refresh_token": refresh_token}
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=10)
        except requests.RequestException as exc:
            raise SupabaseUnavailableError("Authentication service is temporarily unreachable.") from exc

        if res.status_code != 200:
            err_json = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
            raise InvalidCredentialsError(err_json.get("error_description") or "Invalid or expired refresh token")

        return res.json()

    def logout(self, access_token: str) -> None:
        """Revoke session in Supabase Auth."""
        url = f"{self.supabase_url}/auth/v1/logout"
        headers = {
            "apikey": self.anon_key,
            "Authorization": f"Bearer {access_token}",
        }
        try:
            requests.post(url, headers=headers, timeout=5)
        except Exception as exc:
            logger.warning("Supabase logout request encountered: %s", exc)

    def _supabase_login(self, email: str, password: str) -> Dict[str, Any]:
        """Call Supabase password grant token endpoint."""
        url = f"{self.supabase_url}/auth/v1/token?grant_type=password"
        headers = {
            "apikey": self.anon_key,
            "Content-Type": "application/json",
        }
        payload = {"email": email, "password": password}
        try:
            res = requests.post(url, json=payload, headers=headers, timeout=10)
        except requests.RequestException as exc:
            logger.error("Supabase Auth unreachable during login: %s", exc)
            raise SupabaseUnavailableError("Authentication service is temporarily unreachable.") from exc

        if res.status_code == 400:
            err_json = res.json() if res.headers.get("content-type", "").startswith("application/json") else {}
            msg = err_json.get("error_description") or err_json.get("msg") or "Invalid email or password"
            raise InvalidCredentialsError(msg)
        elif res.status_code != 200:
            logger.warning("Supabase login returned %s: %s", res.status_code, res.text)
            raise AuthenticationError("Authentication failed. Please check credentials and try again.")

        return res.json()
