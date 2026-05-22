import uuid

from fastapi import APIRouter, Depends, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id, get_db_session
from app.api.errors import raise_service_error
from app.schemas.categories import CategoryCreate, CategoryOut, CategoryUpdate
from app.schemas.pagination import PaginationParams
from app.schemas.responses import ApiResponse, PaginatedResponse
from app.services import categories as category_service
from app.services.exceptions import ServiceError

router = APIRouter(prefix="/api/categories", tags=["categories"])


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_category(
    payload: CategoryCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        category = await category_service.create_category(session, user_id, payload)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(message="Category created successfully", data=CategoryOut.model_validate(category))


@router.get("", response_model=PaginatedResponse)
async def list_categories(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    type: str | None = None,
    is_active: bool | None = None,
    search: str | None = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedResponse:
    pagination = PaginationParams(page=page, page_size=page_size)
    categories, total = await category_service.list_categories(session, user_id, pagination, type, is_active, search)
    return PaginatedResponse(
        message="Categories fetched successfully",
        data=[CategoryOut.model_validate(category) for category in categories],
        pagination=pagination.to_response(total),
    )


@router.get("/{category_id}", response_model=ApiResponse)
async def get_category(
    category_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        category = await category_service.get_category(session, user_id, category_id)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(message="Category fetched successfully", data=CategoryOut.model_validate(category))


@router.patch("/{category_id}", response_model=ApiResponse)
async def update_category(
    category_id: uuid.UUID,
    payload: CategoryUpdate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        category = await category_service.update_category(session, user_id, category_id, payload)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(message="Category updated successfully", data=CategoryOut.model_validate(category))


@router.delete("/{category_id}", response_model=ApiResponse)
async def delete_category(
    category_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        await category_service.delete_category(session, user_id, category_id)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(message="Category deleted successfully", data=None)
