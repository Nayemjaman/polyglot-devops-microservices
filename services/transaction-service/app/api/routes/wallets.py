import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id, get_db_session
from app.api.errors import raise_service_error
from app.schemas.pagination import PaginationParams
from app.schemas.responses import ApiResponse, PaginatedResponse
from app.schemas.wallets import WalletCreate, WalletOut, WalletUpdate
from app.services import wallets as wallet_service
from app.services.exceptions import ServiceError

router = APIRouter(prefix="/api/wallets", tags=["wallets"])


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_wallet(
    payload: WalletCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        wallet = await wallet_service.create_wallet(session, user_id, payload)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(message="Wallet created successfully", data=WalletOut.model_validate(wallet))


@router.get("", response_model=PaginatedResponse)
async def list_wallets(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    type: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedResponse:
    pagination = PaginationParams(page=page, page_size=page_size)
    wallets, total = await wallet_service.list_wallets(session, user_id, pagination, type, is_active, search)
    return PaginatedResponse(
        message="Wallets fetched successfully",
        data=[WalletOut.model_validate(wallet) for wallet in wallets],
        pagination=pagination.to_response(total),
    )


@router.get("/{wallet_id}", response_model=ApiResponse)
async def get_wallet(
    wallet_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        wallet = await wallet_service.get_wallet(session, user_id, wallet_id)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(message="Wallet fetched successfully", data=WalletOut.model_validate(wallet))


@router.patch("/{wallet_id}", response_model=ApiResponse)
async def update_wallet(
    wallet_id: uuid.UUID,
    payload: WalletUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        wallet = await wallet_service.update_wallet(session, user_id, wallet_id, payload)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(message="Wallet updated successfully", data=WalletOut.model_validate(wallet))


@router.delete("/{wallet_id}", response_model=ApiResponse)
async def delete_wallet(
    wallet_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        await wallet_service.delete_wallet(session, user_id, wallet_id)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(message="Wallet deleted successfully", data=None)
