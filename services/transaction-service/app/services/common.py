import uuid
from typing import Any

from sqlalchemy import Select, func, select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.schemas.pagination import PaginationParams
from app.services.exceptions import ConflictError, NotFoundError


async def paginate(
    session: AsyncSession,
    statement: Select[tuple[Any]],
    pagination: PaginationParams,
) -> tuple[list[Any], int]:
    total = await session.scalar(select(func.count()).select_from(statement.subquery()))
    result = await session.execute(statement.offset(pagination.offset).limit(pagination.page_size))
    return list(result.scalars().unique()), total or 0


def clean_update(payload: Any) -> dict[str, Any]:
    return payload.model_dump(exclude_unset=True)


async def commit_refresh(session: AsyncSession, instance: Any) -> Any:
    try:
        await session.commit()
    except IntegrityError as exc:
        await session.rollback()
        raise ConflictError("Duplicate or conflicting data") from exc
    await session.refresh(instance)
    return instance


async def get_owned(
    session: AsyncSession,
    model: type[Any],
    user_id: uuid.UUID,
    item_id: uuid.UUID,
) -> Any:
    item = await session.get(model, item_id)
    if item is None or item.user_id != user_id:
        raise NotFoundError("Resource not found")
    return item
