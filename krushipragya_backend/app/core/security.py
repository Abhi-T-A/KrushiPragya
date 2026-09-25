"""Security utilities for JWT token validation and creation."""
from datetime import datetime, timedelta, timezone
import logging
from typing import Any, Dict, Optional

from fastapi import HTTPException, status
import jwt

from app.core.config import settings

logger = logging.getLogger(__name__)


def decode_supabase_jwt(token: str) -> Dict[str, Any]:
    """Decode and validate a Supabase JWT access token.

    Args:
        token: The raw JWT string from the Bearer authorization header.

    Returns:
        Dict[str, Any]: The decoded token payload claims.

    Raises:
        HTTPException(401): If token is expired, invalid, or malformed.
    """
    secret = settings.effective_jwt_secret
    if not secret:
        logger.error("JWT secret key is not configured in settings.")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Authentication subsystem configuration error",
        )

    try:
        decode_kwargs: Dict[str, Any] = {
            "key": secret,
            "algorithms": ["HS256"],
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
