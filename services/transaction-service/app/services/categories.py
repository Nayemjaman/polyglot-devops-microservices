import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category
from app.schemas.categories import CategoryCreate, CategoryUpdate
from app.schemas.pagination import PaginationParams
from app.services.common import clean_update, commit_refresh, get_owned, paginate
from app.services.exceptions import ValidationServiceError


async def create_category(
    session: AsyncSession, user_id: uuid.UUID, payload: CategoryCreate
) -> Category:
    if payload.parent_category_id:
        await get_owned(session, Category, user_id, payload.parent_category_id)
    category = Category(
        user_id=user_id,
        name=payload.name,
        type=payload.type.value,
        icon=payload.icon,
        color=payload.color,
        parent_category_id=payload.parent_category_id,
    )
    session.add(category)
    return await commit_refresh(session, category)


async def list_categories(
    session: AsyncSession,
    user_id: uuid.UUID,
    pagination: PaginationParams,
    category_type: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
) -> tuple[list[Category], int]:
    statement = (
        select(Category).where(Category.user_id == user_id).order_by(Category.created_at.desc())
    )
    if category_type:
        statement = statement.where(Category.type == category_type)
    if is_active is not None:
        statement = statement.where(Category.is_active.is_(is_active))
    if search:
        statement = statement.where(Category.name.ilike(f"%{search.strip()}%"))
    return await paginate(session, statement, pagination)


async def get_category(
    session: AsyncSession, user_id: uuid.UUID, category_id: uuid.UUID
) -> Category:
    return await get_owned(session, Category, user_id, category_id)


async def update_category(
    session: AsyncSession,
    user_id: uuid.UUID,
    category_id: uuid.UUID,
    payload: CategoryUpdate,
) -> Category:
    category = await get_category(session, user_id, category_id)
    data = clean_update(payload)
    if data.get("parent_category_id"):
        if data["parent_category_id"] == category.id:
            raise ValidationServiceError("Category cannot be its own parent")
        await get_owned(session, Category, user_id, data["parent_category_id"])
    for key, value in data.items():
        setattr(category, key, value)
    return await commit_refresh(session, category)


async def delete_category(
    session: AsyncSession, user_id: uuid.UUID, category_id: uuid.UUID
) -> None:
    category = await get_category(session, user_id, category_id)
    category.is_active = False
    await session.commit()
