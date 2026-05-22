import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import PaymentMethod
from app.schemas.pagination import PaginationParams
from app.schemas.payment_methods import PaymentMethodCreate, PaymentMethodUpdate
from app.services.common import clean_update, commit_refresh, get_owned, paginate


async def create_payment_method(
    session: AsyncSession,
    user_id: uuid.UUID,
    payload: PaymentMethodCreate,
) -> PaymentMethod:
    method = PaymentMethod(user_id=user_id, name=payload.name, type=payload.type.value)
    session.add(method)
    return await commit_refresh(session, method)


async def list_payment_methods(
    session: AsyncSession,
    user_id: uuid.UUID,
    pagination: PaginationParams,
    method_type: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
) -> tuple[list[PaymentMethod], int]:
    statement = select(PaymentMethod).where(PaymentMethod.user_id == user_id).order_by(
        PaymentMethod.created_at.desc()
    )
    if method_type:
        statement = statement.where(PaymentMethod.type == method_type)
    if is_active is not None:
        statement = statement.where(PaymentMethod.is_active.is_(is_active))
    if search:
        statement = statement.where(PaymentMethod.name.ilike(f"%{search.strip()}%"))
    return await paginate(session, statement, pagination)


async def get_payment_method(
    session: AsyncSession,
    user_id: uuid.UUID,
    method_id: uuid.UUID,
) -> PaymentMethod:
    return await get_owned(session, PaymentMethod, user_id, method_id)


async def update_payment_method(
    session: AsyncSession,
    user_id: uuid.UUID,
    method_id: uuid.UUID,
    payload: PaymentMethodUpdate,
) -> PaymentMethod:
    method = await get_payment_method(session, user_id, method_id)
    data = clean_update(payload)
    for key, value in data.items():
        if key == "type" and value is not None:
            value = value.value
        setattr(method, key, value)
    return await commit_refresh(session, method)


async def delete_payment_method(session: AsyncSession, user_id: uuid.UUID, method_id: uuid.UUID) -> None:
    method = await get_payment_method(session, user_id, method_id)
    method.is_active = False
    await session.commit()
