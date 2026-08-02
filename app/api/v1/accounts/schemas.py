"""Pydantic v2 response schemas for accounts."""

import uuid

from pydantic import BaseModel


class AccountResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    name: str
    kind: str
    currency: str
