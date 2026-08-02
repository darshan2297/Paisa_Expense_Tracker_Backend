"""`get_current_user` - the dependency every protected route in every future
feature module will use. Lives here (co-located with the `User` model it
depends on) and is re-exported via `app.deps` for a stable import path that
doesn't require other modules to know it actually lives under `auth`.
"""

from typing import Annotated

import jwt
from fastapi import Depends, Header
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import repository
from app.api.v1.auth.models import User
from app.core.database import get_session
from app.core.exceptions import UnauthorizedError
from app.core.security import TokenType, decode_token


async def get_current_user(
    authorization: Annotated[str | None, Header()] = None,
    session: AsyncSession = Depends(get_session),
) -> User:
    """Decode the bearer access token, verify it hasn't been revoked, and
    return the authenticated `User`. Raises `UnauthorizedError` (-> 401) for
    any failure mode - missing header, malformed/expired/invalid token,
    wrong token type, unknown/inactive user, or a `credential_version`
    mismatch (the token predates a password change / logout-everywhere).
    """
    if not authorization or not authorization.startswith("Bearer "):
        raise UnauthorizedError("Missing or malformed Authorization header")

    token = authorization.removeprefix("Bearer ").strip()
    try:
        claims = decode_token(token)
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc

    if claims.get("type") != TokenType.ACCESS.value:
        raise UnauthorizedError("An access token is required")

    user = await repository.get_by_id(session, claims["sub"])
    if user is None or not user.is_active:
        raise UnauthorizedError("User not found or inactive")
    if claims.get("cv") != user.credential_version:
        raise UnauthorizedError("Token has been revoked")

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
