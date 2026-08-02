"""Business logic for authentication and profile management.

Receives/returns plain values or Pydantic schemas; never constructs an
`HTTPException` or a `Response` - see docs/DEVELOPER_PHILOSOPHY.md §2.1.
"""

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import repository
from app.api.v1.auth.models import User
from app.api.v1.auth.schemas import ProfileResponse, ProfileUpdateRequest, TokenPairResponse
from app.core.exceptions import UnauthorizedError
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)


def _issue_token_pair(user: User) -> TokenPairResponse:
    """Issue a fresh access+refresh pair carrying the user's current
    `credential_version` (`cv`) claim - checked on every authenticated
    request so a password change/logout invalidates prior tokens instantly.
    """
    extra_claims = {"cv": user.credential_version}
    return TokenPairResponse(
        access_token=create_access_token(str(user.id), extra_claims),
        refresh_token=create_refresh_token(str(user.id), extra_claims),
    )


async def login(session: AsyncSession, email: str, password: str) -> TokenPairResponse:
    user = await repository.get_by_email(session, email)
    # Deliberately identical error for "no such user" and "wrong password" -
    # distinguishing them lets an attacker enumerate valid emails.
    if user is None or not user.is_active or not verify_password(password, user.hashed_password):
        raise UnauthorizedError("Incorrect email or password")
    return _issue_token_pair(user)


async def refresh_tokens(session: AsyncSession, refresh_token: str) -> TokenPairResponse:
    try:
        claims = decode_token(refresh_token)
    except jwt.PyJWTError as exc:
        raise UnauthorizedError("Invalid or expired refresh token") from exc

    if claims.get("type") != TokenType.REFRESH.value:
        raise UnauthorizedError("A refresh token is required")

    user = await repository.get_by_id(session, claims["sub"])
    if user is None or not user.is_active:
        raise UnauthorizedError("Invalid or expired refresh token")
    if claims.get("cv") != user.credential_version:
        raise UnauthorizedError("Token has been revoked")

    # Rotate: the old refresh token's claims are still valid (cv unchanged),
    # but a brand new jti/exp pair is issued so it can't be replayed forever.
    return _issue_token_pair(user)


async def logout(session: AsyncSession, user: User) -> None:
    """Invalidate every outstanding token for this user (this request's
    access token included) by bumping `credential_version`.
    """
    user.credential_version += 1
    await session.flush()


async def change_password(
    session: AsyncSession, user: User, current_password: str, new_password: str
) -> None:
    if not verify_password(current_password, user.hashed_password):
        raise UnauthorizedError("Current password is incorrect")
    user.hashed_password = hash_password(new_password)
    user.credential_version += 1  # log out everywhere else, per security philosophy
    await session.flush()


def to_profile_response(user: User) -> ProfileResponse:
    return ProfileResponse.model_validate(user)


async def update_profile(
    session: AsyncSession, user: User, payload: ProfileUpdateRequest
) -> ProfileResponse:
    update_data = payload.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(user, field, value)
    await session.flush()
    return to_profile_response(user)
