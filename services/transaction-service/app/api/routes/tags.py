import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id, get_db_session
from app.api.errors import raise_service_error
from app.schemas.responses import ApiResponse
from app.schemas.tags import TagCreate, TagOut
from app.services import tags as tag_service
from app.services.exceptions import ServiceError

router = APIRouter(prefix="/api/tags", tags=["tags"])


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_tag(
    payload: TagCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        tag = await tag_service.create_tag(session, user_id, payload.name)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(message="Tag created successfully", data=TagOut.model_validate(tag))


@router.get("", response_model=ApiResponse)
async def list_tags(
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    tags = await tag_service.list_tags(session, user_id)
    return ApiResponse(message="Tags fetched successfully", data=[TagOut.model_validate(tag) for tag in tags])


@router.delete("/{tag_id}", response_model=ApiResponse)
async def delete_tag(
    tag_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        await tag_service.delete_tag(session, user_id, tag_id)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(message="Tag deleted successfully", data=None)
