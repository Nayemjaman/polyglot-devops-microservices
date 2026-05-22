import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id, get_db_session
from app.api.errors import raise_service_error
from app.api.presenters import recurring_transaction_to_out
from app.schemas.pagination import PaginationParams
from app.schemas.recurring_transactions import RecurringTransactionCreate, RecurringTransactionUpdate
from app.schemas.responses import ApiResponse, PaginatedResponse
from app.services import recurring_transactions as recurring_transaction_service
from app.services.exceptions import ServiceError

router = APIRouter(prefix="/api/recurring-transactions", tags=["recurring-transactions"])


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_recurring_transaction(
    payload: RecurringTransactionCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        recurring = await recurring_transaction_service.create_recurring_transaction(session, user_id, payload)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(
        message="Recurring transaction created successfully",
        data=recurring_transaction_to_out(recurring),
    )


@router.get("", response_model=PaginatedResponse)
async def list_recurring_transactions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    frequency: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedResponse:
    pagination = PaginationParams(page=page, page_size=page_size)
    recurring_items, total = await recurring_transaction_service.list_recurring_transactions(
        session,
        user_id,
        pagination,
        frequency=frequency,
        is_active=is_active,
        search=search,
    )
    return PaginatedResponse(
        message="Recurring transactions fetched successfully",
        data=[recurring_transaction_to_out(item) for item in recurring_items],
        pagination=pagination.to_response(total),
    )


@router.patch("/{recurring_id}", response_model=ApiResponse)
async def update_recurring_transaction(
    recurring_id: uuid.UUID,
    payload: RecurringTransactionUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        recurring = await recurring_transaction_service.update_recurring_transaction(session, user_id, recurring_id, payload)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(
        message="Recurring transaction updated successfully",
        data=recurring_transaction_to_out(recurring),
    )


@router.delete("/{recurring_id}", response_model=ApiResponse)
async def delete_recurring_transaction(
    recurring_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        await recurring_transaction_service.delete_recurring_transaction(session, user_id, recurring_id)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(message="Recurring transaction deleted successfully", data=None)
