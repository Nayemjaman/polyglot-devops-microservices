import uuid
from datetime import date

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id, get_db_session
from app.api.errors import raise_service_error
from app.api.presenters import transaction_to_out
from app.schemas.pagination import PaginationParams
from app.schemas.responses import ApiResponse, PaginatedResponse
from app.schemas.transactions import TransactionCreate, TransactionUpdate
from app.services import summaries as summary_service
from app.services import transactions as transaction_service
from app.services.exceptions import ServiceError

router = APIRouter(prefix="/api/transactions", tags=["transactions"])


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_transaction(
    payload: TransactionCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        transaction = await transaction_service.create_transaction(session, user_id, payload)
    except ServiceError as exc:
        raise_service_error(exc)
    message = (
        "Transfer transaction created successfully"
        if payload.type == "TRANSFER"
        else "Transaction created successfully"
    )
    return ApiResponse(message=message, data=transaction_to_out(transaction))


@router.get("", response_model=PaginatedResponse)
async def list_transactions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    type: str | None = None,
    category_id: uuid.UUID | None = None,
    wallet_id: uuid.UUID | None = None,
    payment_method_id: uuid.UUID | None = None,
    start_date: date | None = None,
    end_date: date | None = None,
    search: str | None = None,
    sort_by: str = Query(default="transaction_date", pattern="^(transaction_date|created_at)$"),
    sort_order: str = Query(default="desc", pattern="^(asc|desc)$"),
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedResponse:
    pagination = PaginationParams(page=page, page_size=page_size)
    transactions, total = await transaction_service.list_transactions(
        session,
        user_id,
        pagination,
        transaction_type=type,
        category_id=category_id,
        wallet_id=wallet_id,
        payment_method_id=payment_method_id,
        start_date=start_date,
        end_date=end_date,
        search=search,
        sort_by=sort_by,
        sort_order=sort_order,
    )
    return PaginatedResponse(
        message="Transactions fetched successfully",
        data=[transaction_to_out(transaction) for transaction in transactions],
        pagination=pagination.to_response(total),
    )


@router.get("/summary/monthly", response_model=ApiResponse)
async def monthly_summary(
    year: int,
    month: int = Query(ge=1, le=12),
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    data = await summary_service.monthly_summary(session, user_id, year, month)
    return ApiResponse(message="Monthly summary fetched successfully", data=data)


@router.get("/summary/yearly", response_model=ApiResponse)
async def yearly_summary(
    year: int,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    data = await summary_service.yearly_summary(session, user_id, year)
    return ApiResponse(message="Yearly summary fetched successfully", data=data)


@router.get("/summary/category-wise", response_model=ApiResponse)
async def category_wise_summary(
    year: int,
    month: int = Query(ge=1, le=12),
    type: str = "EXPENSE",
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    data = await summary_service.category_summary(session, user_id, year, month, type)
    return ApiResponse(message="Category-wise summary fetched successfully", data=data)


@router.get("/summary/wallet-wise", response_model=ApiResponse)
async def wallet_wise_summary(
    year: int,
    month: int = Query(ge=1, le=12),
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    data = await summary_service.wallet_summary(session, user_id, year, month)
    return ApiResponse(message="Wallet-wise summary fetched successfully", data=data)


@router.get("/{transaction_id}", response_model=ApiResponse)
async def get_transaction(
    transaction_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        transaction = await transaction_service.get_transaction(session, user_id, transaction_id)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(message="Transaction fetched successfully", data=transaction_to_out(transaction))


@router.patch("/{transaction_id}", response_model=ApiResponse)
async def update_transaction(
    transaction_id: uuid.UUID,
    payload: TransactionUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        transaction = await transaction_service.update_transaction(session, user_id, transaction_id, payload)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(message="Transaction updated successfully", data=transaction_to_out(transaction))


@router.delete("/{transaction_id}", response_model=ApiResponse)
async def delete_transaction(
    transaction_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        await transaction_service.delete_transaction(session, user_id, transaction_id)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(message="Transaction deleted successfully", data=None)
