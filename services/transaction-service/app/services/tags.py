import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Tag
from app.services.common import commit_refresh, get_owned
from app.services.exceptions import ValidationServiceError


async def create_tag(session: AsyncSession, user_id: uuid.UUID, name: str) -> Tag:
    clean_name = name.strip().lower()
    if not clean_name:
        raise ValidationServiceError("Validation failed", {"name": ["Name is required"]})
    tag = await session.scalar(select(Tag).where(Tag.user_id == user_id, Tag.name == clean_name))
    if tag is not None:
        return tag
    tag = Tag(user_id=user_id, name=clean_name)
    session.add(tag)
    return await commit_refresh(session, tag)


async def list_tags(session: AsyncSession, user_id: uuid.UUID) -> list[Tag]:
    result = await session.scalars(select(Tag).where(Tag.user_id == user_id).order_by(Tag.name.asc()))
    return list(result)


async def delete_tag(session: AsyncSession, user_id: uuid.UUID, tag_id: uuid.UUID) -> None:
    tag = await get_owned(session, Tag, user_id, tag_id)
    await session.delete(tag)
    await session.commit()
