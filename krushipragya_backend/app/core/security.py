"""Security utilities for JWT token validation and creation."""
from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
import jwt

from app.core.config import settings

logger = logging.getLogger(__name__)


from jwt import PyJWKClient

_jwks_client: Optional[PyJWKClient] = None


def get_jwks_client() -> Optional[PyJWKClient]:
    """Lazy-initialize singleton PyJWKClient for Supabase JWKS verification."""
    global _jwks_client
    if _jwks_client is None and getattr(settings, "SUPABASE_URL", None):
        jwks_url = f"{settings.SUPABASE_URL.rstrip('/')}/auth/v1/.well-known/jwks.json"
        headers: Dict[str, str] = {}
        if getattr(settings, "SUPABASE_ANON_KEY", None):
            headers["apikey"] = settings.SUPABASE_ANON_KEY
        try:
            _jwks_client = PyJWKClient(jwks_url, cache_jwk_set=True, lifespan=3600, headers=headers)
        except Exception as exc:
            logger.warning("Could not initialize Supabase JWKS client: %s", exc)
            _jwks_client = None
    return _jwks_client


def decode_supabase_jwt(token: str) -> Dict[str, Any]:
    """Decode and validate a Supabase JWT access token.

    Supports both:
    1. ES256 (standard Supabase modern asymmetric signing via JWKS)
    2. HS256 (Supabase symmetric HMAC secret / test harness)

    Args:
        token: The raw JWT string from the Bearer authorization header.

    Returns:
        Dict[str, Any]: The decoded token payload claims.

    Raises:
        HTTPException(401): If token is expired, invalid, or malformed.
    """
    try:
        unverified_header = jwt.get_unverified_header(token)
    except Exception as exc:
        logger.warning("JWT validation failed: malformed token header: %s", exc)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc

    alg = unverified_header.get("alg")
    if not alg or alg.lower() == "none":
        logger.warning("JWT validation failed: unsigned or 'none' algorithm token rejected.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Determine verification key and allowed algorithm strictly to avoid confusion
    if alg == "ES256":
        jwks_client = get_jwks_client()
        if not jwks_client:
            logger.error("ES256 token received but Supabase JWKS client is unavailable.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication subsystem configuration error",
            )
        try:
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            key = signing_key.key
        except Exception as exc:
            logger.warning("Could not find matching signing key in JWKS for token: %s", exc)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid authentication token",
                headers={"WWW-Authenticate": "Bearer"},
            ) from exc
        allowed_algorithms = ["ES256"]
    elif alg == "HS256":
        key = settings.effective_jwt_secret
        if not key:
            logger.error("JWT secret key is not configured in settings.")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Authentication subsystem configuration error",
            )
        allowed_algorithms = ["HS256"]
    else:
        logger.warning("JWT validation failed: unsupported or unexpected algorithm '%s'.", alg)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    try:
        decode_kwargs: Dict[str, Any] = {
            "key": key,
            "algorithms": allowed_algorithms,
            "options": {
                "verify_signature": True,
                "verify_exp": True,
                "verify_aud": False,
            },
        }

        # Validate audience if explicitly configured
        if getattr(settings, "JWT_AUDIENCE", None):
            decode_kwargs["audience"] = settings.JWT_AUDIENCE
            decode_kwargs["options"]["verify_aud"] = True

        # Validate issuer if explicitly configured
        if getattr(settings, "JWT_ISSUER", None):
            decode_kwargs["issuer"] = settings.JWT_ISSUER
            decode_kwargs["options"]["verify_iss"] = True

        payload = jwt.decode(token, **decode_kwargs)
        return payload
    except jwt.ExpiredSignatureError as exc:
        logger.warning("JWT validation failed: signature has expired.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication token has expired",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except jwt.InvalidTokenError as exc:
        logger.warning("JWT validation failed: invalid token signature or claims.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid authentication token",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc
    except Exception as exc:
        logger.error("Unexpected error validating JWT: %s", exc, exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        ) from exc


def create_access_token(
    data: Dict[str, Any],
    expires_delta: Optional[timedelta] = None,
) -> str:
    """Create a signed JWT token (primarily used for test harness and system authentication).

    Args:
        data: Claims to encode in the token.
        expires_delta: Optional custom lifetime duration.

    Returns:
        str: Encoded and signed JWT token string.
    """
    to_encode = data.copy()
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"iat": now, "exp": expire})
    secret = settings.effective_jwt_secret
    return jwt.encode(to_encode, secret, algorithm=settings.JWT_ALGORITHM)
