import uuid

from fastapi import APIRouter, Depends, File, UploadFile, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import (
    get_attachment_storage,
    get_current_user_id,
    get_db_session,
    get_settings_from_app,
)
from app.api.errors import raise_service_error
from app.schemas.attachments import AttachmentOut
from app.schemas.responses import ApiResponse
from app.core.config import Settings
from app.services import attachments as attachment_service
from app.services.exceptions import ServiceError
from app.storage.client import AttachmentStorage
from app.storage.keys import build_attachment_object_key

router = APIRouter(prefix="/api/transactions/{transaction_id}/attachments", tags=["attachments"])


@router.post("", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def upload_attachment(
    transaction_id: uuid.UUID,
    file: UploadFile = File(...),
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
    storage: AttachmentStorage = Depends(get_attachment_storage),
    settings: Settings = Depends(get_settings_from_app),
) -> ApiResponse:
    content_type = file.content_type or "application/octet-stream"
    try:
        attachment = await attachment_service.create_empty_attachment_record(
            session,
            user_id,
            transaction_id,
            content_type,
            file.filename or "attachment",
        )
        object_key = build_attachment_object_key(
            prefix=settings.storage_path_prefix,
            user_id=user_id,
            transaction_id=transaction_id,
            attachment_id=attachment.id,
            filename=file.filename or "attachment",
        )
        await storage.upload_fileobj(file.file, object_key, content_type)
        attachment = await attachment_service.save_attachment_url(
            session, attachment, storage.public_url(object_key)
        )
    except ServiceError as exc:
        raise_service_error(exc)

    return ApiResponse(
        message="Attachment uploaded successfully",
        data=AttachmentOut.model_validate(attachment),
    )


@router.get("", response_model=ApiResponse)
async def list_attachments(
    transaction_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        attachments = await attachment_service.list_attachments(session, user_id, transaction_id)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(
        message="Attachments fetched successfully",
        data=[AttachmentOut.model_validate(attachment) for attachment in attachments],
    )


@router.delete("/{attachment_id}", response_model=ApiResponse)
async def delete_attachment(
    transaction_id: uuid.UUID,
    attachment_id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
    storage: AttachmentStorage = Depends(get_attachment_storage),
) -> ApiResponse:
    try:
        attachment = await attachment_service.delete_attachment(
            session, user_id, transaction_id, attachment_id
        )
        object_key = attachment.file_url.split(f"/{storage.bucket_name}/", 1)[-1]
        if object_key and object_key != attachment.file_url:
            await storage.delete_object(object_key)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(message="Attachment deleted successfully", data=None)
