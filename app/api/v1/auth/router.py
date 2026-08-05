"""HTTP layer for auth + profile. Thin adapters only - no business logic,
no direct DB access. See docs/DEVELOPER_PHILOSOPHY.md §2.1.

Two router objects (`auth_router` at `/auth`, `profile_router` at `/profile`)
because the URL convention (docs/API_STANDARDS.md) puts profile under its
own top-level resource path, even though both share this module's `User`
model/service - splitting them into separate feature modules would mean
one importing the other's model, which the project's module-isolation rule
forbids.
"""

from fastapi import APIRouter, Depends, Request, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.auth import repository, service
from app.api.v1.auth.deps import CurrentUser
from app.api.v1.auth.schemas import (
    ChangePasswordRequest,
    LoginRequest,
    PinChangeRequest,
    PinClearRequest,
    PinSetRequest,
    PinStatusResponse,
    PinVerifyRequest,
    PinVerifyResponse,
    ProfileConfigResponse,
    ProfileResponse,
    ProfileUpdateRequest,
    RefreshRequest,
    RegisterRequest,
    TokenPairResponse,
)
from app.api.v1.configuration import service as config_service
from app.core.database import get_session
from app.middleware.rate_limit import default_limit, strict_limit

auth_router = APIRouter(prefix="/auth")
profile_router = APIRouter(prefix="/profile")


@auth_router.get(
    "/registration-open",
    summary="Whether one-time bootstrap registration is still available",
)
@default_limit()
async def registration_open(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> dict[str, bool]:
    """Lets the frontend decide whether to show the registration screen at
    all, without needing to attempt a register and parse a 409. Public
    (no auth) - this is the whole point of a first-run check.
    """
    return {"open": await repository.count_users(session) == 0}


@auth_router.post("/register", summary="One-time bootstrap account creation")
@strict_limit()
async def register(
    request: Request,
    payload: RegisterRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenPairResponse:
    from app.api.v1.security import service as security_service

    user = await service.register(session, payload.email, payload.password, payload.name)
    session_id = await security_service.record_login(session, user, request)
    await session.commit()
    return await service.issue_tokens_for_session(user, session_id)


@auth_router.post("/login", summary="Log in with email + password")
@strict_limit()
async def login(
    request: Request,
    payload: LoginRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenPairResponse:
    from app.api.v1.security import service as security_service

    user = await service.login(session, payload.email, payload.password)
    session_id = await security_service.record_login(session, user, request)
    await session.commit()
    return await service.issue_tokens_for_session(user, session_id)


@auth_router.post("/refresh", summary="Exchange a refresh token for a new pair")
@strict_limit()
async def refresh(
    request: Request,
    payload: RefreshRequest,
    session: AsyncSession = Depends(get_session),
) -> TokenPairResponse:
    # Do not mint a new device session here. Legacy no-`sid` refresh tokens
    # must sign in again — otherwise remote "Sign out" cannot stop them.
    return await service.refresh_tokens(session, payload.refresh_token)


@auth_router.post("/logout", status_code=204, summary="Invalidate all outstanding tokens")
@default_limit()
async def logout(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.logout(session, current_user)
    from app.api.v1.security import service as security_service

    await security_service.record_logout(session, current_user)
    await session.commit()
    return Response(status_code=204)


@auth_router.post("/change-password", status_code=204)
@strict_limit()
async def change_password(
    request: Request,
    payload: ChangePasswordRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> Response:
    await service.change_password(
        session, current_user, payload.current_password, payload.new_password
    )
    from app.api.v1.security import service as security_service

    await security_service.record_password_change(session, current_user, request)
    await session.commit()
    return Response(status_code=204)


@auth_router.get("/pin", summary="Whether the account has an app PIN")
@default_limit()
async def get_pin_status(
    request: Request,
    current_user: CurrentUser,
) -> PinStatusResponse:
    return service.get_pin_status(current_user)


@auth_router.post("/pin", summary="Create or replace the account app PIN")
@strict_limit()
async def set_pin(
    request: Request,
    payload: PinSetRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> PinStatusResponse:
    return await service.set_pin(session, current_user, payload.pin)


@auth_router.put("/pin", summary="Change the account app PIN")
@strict_limit()
async def change_pin(
    request: Request,
    payload: PinChangeRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> PinStatusResponse:
    return await service.change_pin(session, current_user, payload.current_pin, payload.new_pin)


@auth_router.post("/pin/verify", summary="Verify the account app PIN")
@strict_limit()
async def verify_pin(
    request: Request,
    payload: PinVerifyRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> PinVerifyResponse:
    return await service.verify_pin(session, current_user, payload.pin)


@auth_router.post("/pin/clear", summary="Clear the account app PIN")
@strict_limit()
async def clear_pin(
    request: Request,
    payload: PinClearRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> PinStatusResponse:
    return await service.clear_pin(session, current_user, payload.pin)


@profile_router.get("/config", summary="Get profile & security UI configuration options")
@default_limit()
async def get_profile_config(
    request: Request,
    session: AsyncSession = Depends(get_session),
) -> ProfileConfigResponse:
    data = await config_service.build_profile_config(session)
    return ProfileConfigResponse(**data)


@profile_router.get("", summary="Get the current user's profile")
@default_limit()
async def get_profile(
    request: Request,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> ProfileResponse:
    return await service.get_profile(session, current_user)


@profile_router.patch("", summary="Update the current user's profile/preferences")
@default_limit()
async def update_profile(
    request: Request,
    payload: ProfileUpdateRequest,
    current_user: CurrentUser,
    session: AsyncSession = Depends(get_session),
) -> ProfileResponse:
    return await service.update_profile(session, current_user, payload)
