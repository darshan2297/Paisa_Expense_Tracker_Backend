"""Password hashing and JWT utility functions.

These are pure, stateless utilities — Phase-0 scaffolding only. They are NOT
yet wired to any route (no login/register endpoints exist). A later phase
will consume these from the auth feature module and, per the architecture
decision recorded in the project brief, pair access tokens with a DB-backed
`credential_version` column (instead of Redis) for revocation.
"""

import uuid
from datetime import UTC, datetime, timedelta
from enum import StrEnum
from typing import Any

import jwt
from passlib.context import CryptContext

from app.core.config import get_settings

_pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

JWT_ALGORITHM = "HS256"


class TokenType(StrEnum):
    ACCESS = "access"
    REFRESH = "refresh"


def hash_password(plain_password: str) -> str:
    """Hash a plaintext password for storage. Never store plaintext passwords."""
    # passlib ships no type stubs, so its return type is `Any` to the type
    # checker even though it's always a `str` at runtime - cast explicitly.
    return str(_pwd_context.hash(plain_password))


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Check a plaintext password against a previously hashed value."""
    return bool(_pwd_context.verify(plain_password, hashed_password))


def _create_token(
    subject: str,
    token_type: TokenType,
    expires_delta: timedelta,
    extra_claims: dict[str, Any] | None = None,
) -> str:
    """Build and sign a JWT with standard claims (sub, iat, exp, jti, type)."""
    settings = get_settings()
    now = datetime.now(UTC)
    payload: dict[str, Any] = {
        "sub": subject,
        "type": token_type.value,
        "iat": now,
        "exp": now + expires_delta,
        "jti": str(uuid.uuid4()),
    }
    if extra_claims:
        payload.update(extra_claims)
    return jwt.encode(payload, settings.JWT_SECRET_KEY, algorithm=JWT_ALGORITHM)


def create_access_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    """Issue a short-lived access token for `subject` (typically the user id)."""
    settings = get_settings()
    return _create_token(
        subject,
        TokenType.ACCESS,
        timedelta(minutes=settings.JWT_ACCESS_EXPIRE_MINUTES),
        extra_claims,
    )


def create_refresh_token(subject: str, extra_claims: dict[str, Any] | None = None) -> str:
    """Issue a long-lived refresh token for `subject` (typically the user id)."""
    settings = get_settings()
    return _create_token(
        subject,
        TokenType.REFRESH,
        timedelta(days=settings.JWT_REFRESH_EXPIRE_DAYS),
        extra_claims,
    )


def decode_token(token: str) -> dict[str, Any]:
    """Decode and verify a JWT, returning its claims.

    Raises `jwt.PyJWTError` (or a subclass, e.g. `jwt.ExpiredSignatureError`)
    on an invalid/expired token — callers in the auth feature module are
    expected to translate that into the appropriate `AppError`.
    """
    settings = get_settings()
    return jwt.decode(token, settings.JWT_SECRET_KEY, algorithms=[JWT_ALGORITHM])
