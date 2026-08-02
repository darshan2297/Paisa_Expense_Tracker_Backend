"""Pydantic v2 request/response schemas for the auth + profile endpoints."""

import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class LoginRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=1)


class RefreshRequest(BaseModel):
    refresh_token: str


class ChangePasswordRequest(BaseModel):
    current_password: str = Field(min_length=1)
    new_password: str = Field(min_length=8)


class TokenPairResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


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
