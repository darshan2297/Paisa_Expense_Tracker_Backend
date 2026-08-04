"""Pydantic schemas for notifications."""

import datetime as dt
import uuid

from pydantic import BaseModel, Field


class NotificationResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    kind: str
    title: str
    body: str
    read_at: dt.datetime | None
    entity_type: str | None
    entity_id: uuid.UUID | None
    created_at: dt.datetime


class PushTokenCreateRequest(BaseModel):
    expo_push_token: str = Field(min_length=1, max_length=512)
    device_label: str | None = None
