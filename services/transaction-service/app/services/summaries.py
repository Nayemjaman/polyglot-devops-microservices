import uuid
from decimal import Decimal
from typing import Any

from sqlalchemy import extract, func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Category, Transaction, Wallet
from app.schemas.enums import TransactionType


async def monthly_summary(
    session: AsyncSession,
    user_id: uuid.UUID,
    year: int,
    month: int,
) -> dict[str, Any]:
    rows = await session.execute(
        select(Transaction.type, func.coalesce(func.sum(Transaction.amount), 0), func.count(Transaction.id))
        .where(
            Transaction.user_id == user_id,
            Transaction.is_deleted.is_(False),
            extract("year", Transaction.transaction_date) == year,
            extract("month", Transaction.transaction_date) == month,
        )
        .group_by(Transaction.type)
    )
    income = expense = Decimal("0")
    income_count = expense_count = 0
    for tx_type, amount, count in rows:
        if tx_type == TransactionType.INCOME:
            income = amount
            income_count = count
        elif tx_type == TransactionType.EXPENSE:
            expense = amount
            expense_count = count
    return {
        "year": year,
        "month": month,
        "currency_code": "BDT",
        "total_income": income,
        "total_expense": expense,
        "balance": income - expense,
        "transaction_count": income_count + expense_count,
        "income_count": income_count,
        "expense_count": expense_count,
    }


async def yearly_summary(session: AsyncSession, user_id: uuid.UUID, year: int) -> dict[str, Any]:
    rows = await session.execute(
        select(
            extract("month", Transaction.transaction_date).label("month"),
            Transaction.type,
            func.coalesce(func.sum(Transaction.amount), 0),
        )
        .where(
            Transaction.user_id == user_id,
            Transaction.is_deleted.is_(False),
            extract("year", Transaction.transaction_date) == year,
        )
        .group_by("month", Transaction.type)
    )
    months = {
        month: {"month": month, "total_income": Decimal("0"), "total_expense": Decimal("0")}
        for month in range(1, 13)
    }
    for month, tx_type, amount in rows:
        item = months[int(month)]
        if tx_type == TransactionType.INCOME:
            item["total_income"] = amount
        elif tx_type == TransactionType.EXPENSE:
            item["total_expense"] = amount
    breakdown = []
    total_income = total_expense = Decimal("0")
    for item in months.values():
        item["balance"] = item["total_income"] - item["total_expense"]
        total_income += item["total_income"]
        total_expense += item["total_expense"]
        breakdown.append(item)
    return {
        "year": year,
        "currency_code": "BDT",
        "total_income": total_income,
        "total_expense": total_expense,
        "balance": total_income - total_expense,
        "monthly_breakdown": breakdown,
    }


async def category_summary(
    session: AsyncSession,
    user_id: uuid.UUID,
    year: int,
    month: int,
    transaction_type: str,
) -> dict[str, Any]:
    rows = await session.execute(
        select(Category.id, Category.name, func.coalesce(func.sum(Transaction.amount), 0), func.count(Transaction.id))
        .join(Category, Category.id == Transaction.category_id)
        .where(
            Transaction.user_id == user_id,
            Transaction.is_deleted.is_(False),
            Transaction.type == transaction_type,
            extract("year", Transaction.transaction_date) == year,
            extract("month", Transaction.transaction_date) == month,
        )
        .group_by(Category.id, Category.name)
    )
    items = list(rows)
    total = sum((row[2] for row in items), Decimal("0"))
    categories = [
        {
            "category_id": category_id,
            "category_name": name,
            "total_amount": amount,
            "transaction_count": count,
            "percentage": round(float((amount / total) * 100), 2) if total else 0,
        }
        for category_id, name, amount, count in items
    ]
    return {
        "year": year,
        "month": month,
        "type": transaction_type,
        "currency_code": "BDT",
        "categories": categories,
    }


async def wallet_summary(session: AsyncSession, user_id: uuid.UUID, year: int, month: int) -> dict[str, Any]:
    rows = await session.execute(
        select(
            Wallet.id,
            Wallet.name,
            Transaction.type,
            func.coalesce(func.sum(Transaction.amount), 0),
            func.count(Transaction.id),
        )
        .join(Wallet, Wallet.id == Transaction.wallet_id)
        .where(
            Transaction.user_id == user_id,
            Transaction.is_deleted.is_(False),
            extract("year", Transaction.transaction_date) == year,
            extract("month", Transaction.transaction_date) == month,
        )
        .group_by(Wallet.id, Wallet.name, Transaction.type)
    )
    wallets: dict[uuid.UUID, dict[str, Any]] = {}
    for wallet_id, name, tx_type, amount, count in rows:
        item = wallets.setdefault(
            wallet_id,
            {
                "wallet_id": wallet_id,
                "wallet_name": name,
                "total_income": Decimal("0"),
                "total_expense": Decimal("0"),
                "transaction_count": 0,
            },
        )
        if tx_type == TransactionType.INCOME:
            item["total_income"] = amount
        elif tx_type == TransactionType.EXPENSE:
            item["total_expense"] = amount
        item["transaction_count"] += count
    for item in wallets.values():
        item["balance"] = item["total_income"] - item["total_expense"]
    return {"year": year, "month": month, "currency_code": "BDT", "wallets": list(wallets.values())}
