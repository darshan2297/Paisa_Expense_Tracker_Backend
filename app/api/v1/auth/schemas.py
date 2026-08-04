"""Pydantic v2 request/response schemas for the auth + profile endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class RegisterRequest(BaseModel):
    """One-time bootstrap registration - see service.register(). There is no
    ongoing public signup; this succeeds only while the `users` table is empty.
    """

    email: EmailStr
    password: str = Field(min_length=8)
    name: str = Field(min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    # Whether this account already has an app PIN configured.
    pin_configured: bool = False


class PinStatusResponse(BaseModel):
    configured: bool


class PinSetRequest(BaseModel):
    """Create the account PIN (first time) or replace it after Forgot PIN."""

    pin: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class PinChangeRequest(BaseModel):
    current_pin: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")
    new_pin: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class PinVerifyRequest(BaseModel):
    pin: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class PinVerifyResponse(BaseModel):
    valid: bool


class PinClearRequest(BaseModel):
    pin: str = Field(min_length=6, max_length=6, pattern=r"^\d{6}$")


class ProfileResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    email: str
    name: str
    phone: str | None
    city: str | None
    occupation: str | None
    currency: str
    month_start_day: int
    dark_mode: bool
    week_start_monday: bool
    round_up_savings: bool
    digest_enabled: bool
    sound_enabled: bool
    created_at: datetime
    pin_configured: bool = False


class ProfileUpdateRequest(BaseModel):
    """All fields optional - PATCH semantics, only supplied fields are changed."""

    name: str | None = Field(default=None, min_length=1)
    phone: str | None = None
    city: str | None = None
    occupation: str | None = None
    currency: str | None = Field(default=None, min_length=3, max_length=3)
    month_start_day: int | None = Field(default=None, ge=1, le=28)
    dark_mode: bool | None = None
    week_start_monday: bool | None = None
    round_up_savings: bool | None = None
    digest_enabled: bool | None = None
    sound_enabled: bool | None = None


class ConfigurationOptionResponse(BaseModel):
    key: str
    category: str
    value_type: str
    default_value: bool | int | str
    label: str | None = None
    description: str | None = None
    allowed_values: list[bool | int | str] | None = None


class ProfileConfigResponse(BaseModel):
    """UI configuration options for profile & security settings screens."""

    auto_logout_minutes_options: list[int] = Field(default_factory=lambda: [1, 5, 15, 30])
    month_start_day_min: int = 1
    month_start_day_max: int = 28
    currencies: list[str] = Field(default_factory=lambda: ["INR"])
    options: list[ConfigurationOptionResponse] = Field(default_factory=list)
