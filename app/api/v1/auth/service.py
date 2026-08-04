"""Business logic for authentication and profile management."""

import jwt
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import repository
from app.api.v1.auth.models import User
from app.api.v1.auth.schemas import (
    PinStatusResponse,
    PinVerifyResponse,
    ProfileResponse,
    ProfileUpdateRequest,
    TokenPairResponse,
)
from app.api.v1.configuration import service as config_service
from app.api.v1.configuration.catalog import PROFILE_CONFIG_KEYS
from app.core.exceptions import ConflictError, UnauthorizedError, ValidationError
from app.core.security import (
    TokenType,
    create_access_token,
    create_refresh_token,
    decode_token,
    hash_password,
    verify_password,
)
from app.deps import ensure_default_account

_PROFILE_FIELDS = frozenset({"name", "phone", "city", "occupation"})


def _as_int(value: object) -> int:
    if isinstance(value, int):
        return value
    raise TypeError(f"Expected int, got {type(value).__name__}")


def _issue_token_pair(user: User) -> TokenPairResponse:
    extra_claims = {"cv": user.credential_version}
    return TokenPairResponse(
        access_token=create_access_token(str(user.id), extra_claims),
        refresh_token=create_refresh_token(str(user.id), extra_claims),
        pin_configured=user.hashed_pin is not None,
    )


def _to_profile_response(user: User, values: dict[str, object]) -> ProfileResponse:
    return ProfileResponse(
        id=user.id,
        email=user.email,
        name=user.name,
        phone=user.phone,
        city=user.city,
        occupation=user.occupation,
        currency=str(values["currency"]),
        month_start_day=_as_int(values["month_start_day"]),
        dark_mode=bool(values["dark_mode"]),
        week_start_monday=bool(values["week_start_monday"]),
        round_up_savings=bool(values["round_up_savings"]),
        digest_enabled=bool(values["digest_enabled"]),
        sound_enabled=bool(values["sound_enabled"]),
        created_at=user.created_at,
        pin_configured=user.hashed_pin is not None,
    )


async def register(
    session: AsyncSession, email: str, password: str, name: str
) -> TokenPairResponse:
    if await repository.count_users(session) > 0:
        raise ConflictError("Registration is closed - an account already exists")

    user = await repository.create_user(
        session,
        email=email,
        hashed_password=hash_password(password),
        name=name,
    )
    await ensure_default_account(session, user.id)
    return _issue_token_pair(user)


async def login(session: AsyncSession, email: str, password: str) -> TokenPairResponse:
    user = await repository.get_by_email(session, email)
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

    return _issue_token_pair(user)


async def logout(session: AsyncSession, user: User) -> None:
    user.credential_version += 1
    await session.flush()


async def change_password(
    session: AsyncSession, user: User, current_password: str, new_password: str
) -> None:
    if not verify_password(current_password, user.hashed_password):
        raise UnauthorizedError("Current password is incorrect")
    user.hashed_password = hash_password(new_password)
    user.credential_version += 1
    await session.flush()


def get_pin_status(user: User) -> PinStatusResponse:
    return PinStatusResponse(configured=user.hashed_pin is not None)


async def set_pin(session: AsyncSession, user: User, pin: str) -> PinStatusResponse:
    """Create or replace the account PIN (first setup / forgot-PIN reset)."""
    user.hashed_pin = hash_password(pin)
    await session.flush()
    return PinStatusResponse(configured=True)


async def change_pin(
    session: AsyncSession, user: User, current_pin: str, new_pin: str
) -> PinStatusResponse:
    if user.hashed_pin is None:
        raise ValidationError("No app PIN is configured yet")
    if not verify_password(current_pin, user.hashed_pin):
        raise UnauthorizedError("Current PIN is incorrect")
    if current_pin == new_pin:
        raise ValidationError("New PIN must be different from the current PIN")
    user.hashed_pin = hash_password(new_pin)
    await session.flush()
    return PinStatusResponse(configured=True)


async def verify_pin(session: AsyncSession, user: User, pin: str) -> PinVerifyResponse:
    if user.hashed_pin is None:
        return PinVerifyResponse(valid=False)
    return PinVerifyResponse(valid=verify_password(pin, user.hashed_pin))


async def clear_pin(session: AsyncSession, user: User, pin: str) -> PinStatusResponse:
    if user.hashed_pin is None:
        return PinStatusResponse(configured=False)
    if not verify_password(pin, user.hashed_pin):
        raise UnauthorizedError("PIN is incorrect")
    user.hashed_pin = None
    await session.flush()
    return PinStatusResponse(configured=False)


async def get_profile(session: AsyncSession, user: User) -> ProfileResponse:
    values = await config_service.get_resolved_subset(session, user.id, PROFILE_CONFIG_KEYS)
    return _to_profile_response(user, values)


async def update_profile(
    session: AsyncSession, user: User, payload: ProfileUpdateRequest
) -> ProfileResponse:
    update_data = payload.model_dump(exclude_unset=True)

    profile_updates = {k: v for k, v in update_data.items() if k in _PROFILE_FIELDS}
    config_updates = {k: v for k, v in update_data.items() if k in PROFILE_CONFIG_KEYS}

    for field, value in profile_updates.items():
        setattr(user, field, value)

    if config_updates:
        await config_service.set_values(session, user.id, config_updates)

    values = await config_service.get_resolved_subset(session, user.id, PROFILE_CONFIG_KEYS)
    await session.flush()
    return _to_profile_response(user, values)
