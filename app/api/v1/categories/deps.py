"""Category lookup dependencies for other modules."""

import uuid
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.v1.categories import repository
from app.core.database import get_session
from app.core.exceptions import NotFoundError

_UTILITIES_CATEGORY_NAME = "Utilities"


async def get_utilities_category_id(session: AsyncSession = Depends(get_session)) -> uuid.UUID:
    categories = await repository.list_categories(session)
    for category in categories:
        if category.name == _UTILITIES_CATEGORY_NAME:
            return category.id
    raise NotFoundError("Utilities category not found")


UtilitiesCategoryId = Annotated[uuid.UUID, Depends(get_utilities_category_id)]
