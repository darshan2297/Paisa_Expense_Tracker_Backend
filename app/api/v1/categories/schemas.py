"""Pydantic v2 response schemas for categories."""

import uuid

from pydantic import BaseModel


class CategoryResponse(BaseModel):
    model_config = {"from_attributes": True}

    id: uuid.UUID
    kind: str
    name: str
    color: str
    sort_order: int
