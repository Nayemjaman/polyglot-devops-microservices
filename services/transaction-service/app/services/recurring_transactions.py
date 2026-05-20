import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Category, RecurringTransaction, Wallet
from app.schemas.enums import TransactionType
from app.schemas.pagination import PaginationParams
from app.schemas.recurring_transactions import RecurringTransactionCreate, RecurringTransactionUpdate
from app.services.common import clean_update, get_owned, paginate
from app.services.exceptions import NotFoundError, ValidationServiceError


def recurring_options() -> list[Any]:
    return [selectinload(RecurringTransaction.wallet), selectinload(RecurringTransaction.category)]


async def create_recurring_transaction(
    session: AsyncSession,
    user_id: uuid.UUID,
    payload: RecurringTransactionCreate,
) -> RecurringTransaction:
    wallet = await get_owned(session, Wallet, user_id, payload.wallet_id)
    category = await get_owned(session, Category, user_id, payload.category_id)
    if payload.type not in {TransactionType.INCOME, TransactionType.EXPENSE}:
        raise ValidationServiceError("Only INCOME and EXPENSE recurring transactions are supported")
    if category.type != payload.type:
        raise ValidationServiceError("Recurring transaction type must match category type")
    recurring = RecurringTransaction(
        user_id=user_id,
        wallet_id=wallet.id,
        category_id=category.id,
        type=payload.type.value,
        amount=payload.amount,
        currency_code=payload.currency_code,
        title=payload.title,
        description=payload.description,
        frequency=payload.frequency.value,
        start_date=payload.start_date,
        end_date=payload.end_date,
        next_run_date=payload.next_run_date,
        is_active=payload.is_active,
    )
    session.add(recurring)
    await session.commit()
    return await get_recurring_transaction(session, user_id, recurring.id)


async def list_recurring_transactions(
    session: AsyncSession,
    user_id: uuid.UUID,
    pagination: PaginationParams,
    frequency: str | None = None,
    is_active: bool | None = None,
) -> tuple[list[RecurringTransaction], int]:
    statement = (
        select(RecurringTransaction)
        .options(*recurring_options())
        .where(RecurringTransaction.user_id == user_id)
        .order_by(RecurringTransaction.next_run_date.asc())
    )
    if frequency:
        statement = statement.where(RecurringTransaction.frequency == frequency)
    if is_active is not None:
        statement = statement.where(RecurringTransaction.is_active.is_(is_active))
    return await paginate(session, statement, pagination)


async def get_recurring_transaction(
    session: AsyncSession,
    user_id: uuid.UUID,
    recurring_id: uuid.UUID,
) -> RecurringTransaction:
    recurring = await session.scalar(
        select(RecurringTransaction)
        .options(*recurring_options())
        .where(RecurringTransaction.id == recurring_id, RecurringTransaction.user_id == user_id)
    )
    if recurring is None:
        raise NotFoundError("Recurring transaction not found")
    return recurring


async def update_recurring_transaction(
    session: AsyncSession,
    user_id: uuid.UUID,
    recurring_id: uuid.UUID,
    payload: RecurringTransactionUpdate,
) -> RecurringTransaction:
    recurring = await get_recurring_transaction(session, user_id, recurring_id)
    data = clean_update(payload)
    if "wallet_id" in data:
        await get_owned(session, Wallet, user_id, data["wallet_id"])
    if "category_id" in data:
        category = await get_owned(session, Category, user_id, data["category_id"])
        if category.type != recurring.type:
            raise ValidationServiceError("Recurring transaction type must match category type")
    for key, value in data.items():
        if key == "frequency" and value is not None:
            value = value.value
        setattr(recurring, key, value)
    await session.commit()
    return await get_recurring_transaction(session, user_id, recurring.id)


async def delete_recurring_transaction(
    session: AsyncSession,
    user_id: uuid.UUID,
    recurring_id: uuid.UUID,
) -> None:
    recurring = await get_recurring_transaction(session, user_id, recurring_id)
    recurring.is_active = False
    await session.commit()
