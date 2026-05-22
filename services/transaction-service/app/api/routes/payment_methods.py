import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id, get_db_session
from app.api.errors import raise_service_error
from app.schemas.pagination import PaginationParams
from app.schemas.payment_methods import PaymentMethodCreate, PaymentMethodOut, PaymentMethodUpdate
from app.schemas.responses import ApiResponse, PaginatedResponse
from app.services import payment_methods as payment_method_service
from app.services.exceptions import ServiceError

router = APIRouter(prefix="/api/payment-methods", tags=["payment-methods"])


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_payment_method(
    payload: PaymentMethodCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        method = await payment_method_service.create_payment_method(session, user_id, payload)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(
        message="Payment method created successfully",
        data=PaymentMethodOut.model_validate(method),
    )


@router.get("", response_model=PaginatedResponse)
async def list_payment_methods(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    type: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedResponse:
    pagination = PaginationParams(page=page, page_size=page_size)
    methods, total = await payment_method_service.list_payment_methods(session, user_id, pagination, type, is_active, search)
    return PaginatedResponse(
        message="Payment methods fetched successfully",
        data=[PaymentMethodOut.model_validate(method) for method in methods],
        pagination=pagination.to_response(total),
    )


@router.get("/{method_id}", response_model=ApiResponse)
async def get_payment_method(
    method_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        method = await payment_method_service.get_payment_method(session, user_id, method_id)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(
        message="Payment method fetched successfully",
        data=PaymentMethodOut.model_validate(method),
    )


@router.patch("/{method_id}", response_model=ApiResponse)
async def update_payment_method(
    method_id: uuid.UUID,
    payload: PaymentMethodUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        method = await payment_method_service.update_payment_method(session, user_id, method_id, payload)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(
        message="Payment method updated successfully",
        data=PaymentMethodOut.model_validate(method),
    )


@router.delete("/{method_id}", response_model=ApiResponse)
async def delete_payment_method(
    method_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        await payment_method_service.delete_payment_method(session, user_id, method_id)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(message="Payment method deleted successfully", data=None)
