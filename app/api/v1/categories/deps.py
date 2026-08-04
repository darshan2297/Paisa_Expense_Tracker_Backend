"""Category lookup dependencies for other modules."""

import uuid
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.categories import repository
from app.core.database import get_session
from app.core.exceptions import NotFoundError

_UTILITIES_CATEGORY_NAME = "Utilities"
_INSURANCE_CATEGORY_NAME = "Insurance"


async def get_utilities_category_id(session: AsyncSession = Depends(get_session)) -> uuid.UUID:
    categories = await repository.list_categories(session)
    for category in categories:
        if category.name == _UTILITIES_CATEGORY_NAME:
            return category.id
    raise NotFoundError("Utilities category not found")


async def get_insurance_category_id(session: AsyncSession = Depends(get_session)) -> uuid.UUID:
    categories = await repository.list_categories(session)
    for category in categories:
        if category.name == _INSURANCE_CATEGORY_NAME:
            return category.id
    raise NotFoundError("Insurance category not found")


UtilitiesCategoryId = Annotated[uuid.UUID, Depends(get_utilities_category_id)]
InsuranceCategoryId = Annotated[uuid.UUID, Depends(get_insurance_category_id)]
