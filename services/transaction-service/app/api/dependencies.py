from collections.abc import AsyncGenerator
import uuid

import httpx
from fastapi import Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.auth import AuthClient, AuthServiceUnavailable
from app.core.config import Settings
from app.db.session import iter_session
from app.storage.client import AttachmentStorage


async def get_settings_from_app(request: Request) -> Settings:
    return request.app.state.settings


async def get_http_client(request: Request) -> httpx.AsyncClient:
    return request.app.state.http_client


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    async for session in iter_session(request.app.state.db_sessionmaker):
        yield session


async def get_attachment_storage(request: Request) -> AttachmentStorage:
    return request.app.state.attachment_storage


async def get_current_user_id(
    request: Request,
    authorization: str | None = Header(default=None),
) -> uuid.UUID:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required"
        )

    settings = request.app.state.settings
    http_client = request.app.state.http_client
    auth_client = AuthClient(settings=settings, http_client=http_client)
    try:
        user = await auth_client.get_current_user(authorization)
    except AuthServiceUnavailable as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail="failed to verify authentication",
        ) from exc

    if user is None or user.id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="authentication required"
        )

    return user.id
