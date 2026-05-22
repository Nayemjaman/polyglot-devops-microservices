import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Wallet
from app.schemas.pagination import PaginationParams
from app.schemas.wallets import WalletCreate, WalletUpdate
from app.services.common import clean_update, commit_refresh, get_owned, paginate


async def unset_other_defaults(
    session: AsyncSession,
    user_id: uuid.UUID,
    wallet_id: uuid.UUID | None,
) -> None:
    wallets = await session.scalars(
        select(Wallet).where(Wallet.user_id == user_id, Wallet.is_default.is_(True))
    )
    for wallet in wallets:
        if wallet_id is None or wallet.id != wallet_id:
            wallet.is_default = False


async def create_wallet(session: AsyncSession, user_id: uuid.UUID, payload: WalletCreate) -> Wallet:
    if payload.is_default:
        await unset_other_defaults(session, user_id, None)
    wallet = Wallet(
        user_id=user_id,
        name=payload.name,
        type=payload.type.value,
        currency_code=payload.currency_code,
        opening_balance=payload.opening_balance,
        current_balance=payload.opening_balance,
        is_default=payload.is_default,
    )
    session.add(wallet)
    return await commit_refresh(session, wallet)


async def list_wallets(
    session: AsyncSession,
    user_id: uuid.UUID,
    pagination: PaginationParams,
    wallet_type: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
) -> tuple[list[Wallet], int]:
    statement = select(Wallet).where(Wallet.user_id == user_id).order_by(Wallet.created_at.desc())
    if wallet_type:
        statement = statement.where(Wallet.type == wallet_type)
    if is_active is not None:
        statement = statement.where(Wallet.is_active.is_(is_active))
    if search:
        statement = statement.where(Wallet.name.ilike(f"%{search.strip()}%"))
    return await paginate(session, statement, pagination)


async def get_wallet(session: AsyncSession, user_id: uuid.UUID, wallet_id: uuid.UUID) -> Wallet:
    return await get_owned(session, Wallet, user_id, wallet_id)


async def update_wallet(
    session: AsyncSession,
    user_id: uuid.UUID,
    wallet_id: uuid.UUID,
    payload: WalletUpdate,
) -> Wallet:
    wallet = await get_wallet(session, user_id, wallet_id)
    data = clean_update(payload)
    if data.get("is_default") is True:
        await unset_other_defaults(session, user_id, wallet.id)
    for key, value in data.items():
        if key == "type" and value is not None:
            value = value.value
        setattr(wallet, key, value)
    return await commit_refresh(session, wallet)


async def delete_wallet(session: AsyncSession, user_id: uuid.UUID, wallet_id: uuid.UUID) -> None:
    wallet = await get_wallet(session, user_id, wallet_id)
    wallet.is_active = False
    await session.commit()
