"""`get_current_user` - the dependency every protected route in every future
feature module will use. Lives here (co-located with the `User` model it
depends on) and is re-exported via `app.deps` for a stable import path that
doesn't require other modules to know it actually lives under `auth`.
"""

import uuid
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
    wrong token type, unknown/inactive user, a `credential_version`
    mismatch (password change / logout-everywhere), or a revoked device
    session (`sid` bound to a signed-out trusted device).
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

    # Every access token must be bound to a trusted-device session. Without
    # `sid`, Security → Sign out cannot invalidate that client.
    raw_sid = claims.get("sid")
    if not (isinstance(raw_sid, str) and raw_sid):
        raise UnauthorizedError("Session has been signed out")
    try:
        session_id = uuid.UUID(raw_sid)
    except ValueError as exc:
        raise UnauthorizedError("Invalid or expired token") from exc
    from app.api.v1.security import service as security_service

    await security_service.assert_session_active(session, user.id, session_id)

    return user


CurrentUser = Annotated[User, Depends(get_current_user)]
