import uuid
from datetime import date
from decimal import Decimal
from typing import Any

from sqlalchemy import delete, or_, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Category, PaymentMethod, Tag, Transaction, TransactionTag, Wallet
from app.schemas.enums import TransactionType
from app.schemas.pagination import PaginationParams
from app.schemas.transactions import TransactionCreate, TransactionUpdate
from app.services.common import clean_update, get_owned, paginate
from app.services.exceptions import NotFoundError, ValidationServiceError


def apply_balance(wallet: Wallet, transaction_type: str, amount: Decimal, reverse: bool = False) -> None:
    multiplier = Decimal("-1") if reverse else Decimal("1")
    if transaction_type == TransactionType.INCOME:
        wallet.current_balance += amount * multiplier
    elif transaction_type == TransactionType.EXPENSE:
        wallet.current_balance -= amount * multiplier


async def validate_transaction_refs(
    session: AsyncSession,
    user_id: uuid.UUID,
    wallet_id: uuid.UUID | None,
    category_id: uuid.UUID | None,
    payment_method_id: uuid.UUID | None,
    transaction_type: str,
) -> tuple[Wallet, Category, PaymentMethod]:
    if transaction_type not in {TransactionType.INCOME, TransactionType.EXPENSE}:
        raise ValidationServiceError("Only INCOME and EXPENSE transactions are supported for MVP")
    if not wallet_id or not category_id or not payment_method_id:
        raise ValidationServiceError(
            "Validation failed",
            {
                "wallet_id": ["Wallet is required"],
                "category_id": ["Category is required"],
                "payment_method_id": ["Payment method is required"],
            },
        )
    wallet = await get_owned(session, Wallet, user_id, wallet_id)
    category = await get_owned(session, Category, user_id, category_id)
    method = await get_owned(session, PaymentMethod, user_id, payment_method_id)
    if category.type != transaction_type:
        raise ValidationServiceError(
            "Validation failed",
            {"category_id": [f"{transaction_type} transaction requires {transaction_type} category"]},
        )
    return wallet, category, method


async def set_transaction_tags(
    session: AsyncSession,
    user_id: uuid.UUID,
    transaction: Transaction,
    tag_names: list[str],
) -> None:
    names = sorted({name.strip().lower() for name in tag_names if name.strip()})
    await session.execute(delete(TransactionTag).where(TransactionTag.transaction_id == transaction.id))
    await session.flush()
    for name in names:
        tag = await session.scalar(select(Tag).where(Tag.user_id == user_id, Tag.name == name))
        if tag is None:
            tag = Tag(user_id=user_id, name=name)
            session.add(tag)
            await session.flush()
        session.add(TransactionTag(transaction_id=transaction.id, tag_id=tag.id))


def transaction_options() -> list[Any]:
    return [
        selectinload(Transaction.wallet),
        selectinload(Transaction.category),
        selectinload(Transaction.payment_method),
        selectinload(Transaction.attachments),
        selectinload(Transaction.transaction_tags).selectinload(TransactionTag.tag),
    ]


async def create_transaction(
    session: AsyncSession,
    user_id: uuid.UUID,
    payload: TransactionCreate,
) -> Transaction:
    wallet, category, method = await validate_transaction_refs(
        session,
        user_id,
        payload.wallet_id,
        payload.category_id,
        payload.payment_method_id,
        payload.type.value,
    )
    transaction = Transaction(
        user_id=user_id,
        wallet_id=wallet.id,
        category_id=category.id,
        payment_method_id=method.id,
        type=payload.type.value,
        amount=payload.amount,
        currency_code=payload.currency_code,
        title=payload.title,
        description=payload.description,
        transaction_date=payload.transaction_date,
    )
    session.add(transaction)
    await session.flush()
    await set_transaction_tags(session, user_id, transaction, payload.tags)
    apply_balance(wallet, transaction.type, transaction.amount)
    await session.flush()
    return await get_transaction(session, user_id, transaction.id)


async def list_transactions(
    session: AsyncSession,
    user_id: uuid.UUID,
    pagination: PaginationParams,
    transaction_type: str | None = None,
    category_id: uuid.UUID | None = None,
    wallet_id: uuid.UUID | None = None,
    payment_method_id: uuid.UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    search: str | None = None,
    sort_by: str = "transaction_date",
    sort_order: str = "desc",
) -> tuple[list[Transaction], int]:
    statement = (
        select(Transaction)
        .options(*transaction_options())
        .where(Transaction.user_id == user_id, Transaction.is_deleted.is_(False))
    )
    if transaction_type:
        statement = statement.where(Transaction.type == transaction_type)
    if category_id:
        statement = statement.where(Transaction.category_id == category_id)
    if wallet_id:
        statement = statement.where(Transaction.wallet_id == wallet_id)
    if payment_method_id:
        statement = statement.where(Transaction.payment_method_id == payment_method_id)
    if start_date:
        statement = statement.where(Transaction.transaction_date >= start_date)
    if end_date:
        statement = statement.where(Transaction.transaction_date <= end_date)
    if search:
        pattern = f"%{search}%"
        statement = statement.where(or_(Transaction.title.ilike(pattern), Transaction.description.ilike(pattern)))
    sort_column = Transaction.created_at if sort_by == "created_at" else Transaction.transaction_date
    statement = statement.order_by(sort_column.asc() if sort_order == "asc" else sort_column.desc())
    return await paginate(session, statement, pagination)


async def get_transaction(session: AsyncSession, user_id: uuid.UUID, transaction_id: uuid.UUID) -> Transaction:
    transaction = await session.scalar(
        select(Transaction)
        .options(*transaction_options())
        .where(
            Transaction.id == transaction_id,
            Transaction.user_id == user_id,
            Transaction.is_deleted.is_(False),
        )
    )
    if transaction is None:
        raise NotFoundError("Transaction not found")
    return transaction


async def update_transaction(
    session: AsyncSession,
    user_id: uuid.UUID,
    transaction_id: uuid.UUID,
    payload: TransactionUpdate,
) -> Transaction:
    transaction = await get_transaction(session, user_id, transaction_id)
    old_wallet = transaction.wallet
    apply_balance(old_wallet, transaction.type, transaction.amount, reverse=True)
    data = clean_update(payload)
    wallet_id = data.get("wallet_id", transaction.wallet_id)
    category_id = data.get("category_id", transaction.category_id)
    payment_method_id = data.get("payment_method_id", transaction.payment_method_id)
    wallet, _, _ = await validate_transaction_refs(
        session,
        user_id,
        wallet_id,
        category_id,
        payment_method_id,
        transaction.type,
    )
    tags = data.pop("tags", None)
    for key, value in data.items():
        setattr(transaction, key, value)
    await session.flush()
    if tags is not None:
        await set_transaction_tags(session, user_id, transaction, tags)
    apply_balance(wallet, transaction.type, transaction.amount)
    await session.flush()
    return await get_transaction(session, user_id, transaction.id)


async def delete_transaction(session: AsyncSession, user_id: uuid.UUID, transaction_id: uuid.UUID) -> None:
    transaction = await get_transaction(session, user_id, transaction_id)
    apply_balance(transaction.wallet, transaction.type, transaction.amount, reverse=True)
    transaction.is_deleted = True
    await session.flush()
