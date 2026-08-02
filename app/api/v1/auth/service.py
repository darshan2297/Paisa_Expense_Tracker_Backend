"""Business logic for authentication and profile management.

Receives/returns plain values or Pydantic schemas; never constructs an
`HTTPException` or a `Response` - see docs/DEVELOPER_PHILOSOPHY.md §2.1.
"""

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import repository
from app.api.v1.auth.models import User
from app.api.v1.auth.schemas import ProfileResponse, ProfileUpdateRequest, TokenPairResponse
from app.core.exceptions import ConflictError, UnauthorizedError
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.deps import ensure_default_account


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


async def register(
    session: AsyncSession, email: str, password: str, name: str
) -> TokenPairResponse:
    """One-time bootstrap account creation. This app has no ongoing public
    signup (see docs/DEVELOPMENT_GUIDE.md) - this succeeds exactly once,
    while the `users` table is empty, and permanently refuses afterward.

    Known, accepted limitation: the empty-check and the insert are not in a
    single atomic operation (no advisory lock), so two truly concurrent
    bootstrap requests could theoretically both pass the check. Given this
    only ever matters in the few seconds between deploying the app and
    creating its one real account - before any traffic reaches it - that
    race isn't worth the added complexity of a lock for a single-user app.
    """
    if await repository.count_users(session) > 0:
        raise ConflictError("Registration is closed - an account already exists")

    user = await repository.create_user(
        session,
        email=email,
        hashed_password=hash_password(password),
        name=name,
    )
    # Every user needs an account to attach transactions to (F2/F3) - routed
    # through app.deps rather than importing app.api.v1.accounts directly,
    # per docs/DEVELOPER_PHILOSOPHY.md §2.2.
    await ensure_default_account(session, user.id)
    return _issue_token_pair(user)


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
