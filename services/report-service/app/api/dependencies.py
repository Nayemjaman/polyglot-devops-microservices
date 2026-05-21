import uuid
from collections.abc import AsyncGenerator

from fastapi import Header, HTTPException, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.clients.auth import AuthError, get_authenticated_user


async def get_db_session(request: Request) -> AsyncGenerator[AsyncSession, None]:
    sessionmaker = request.app.state.db_sessionmaker
    async with sessionmaker() as session:
        yield session


async def get_current_user_id(
    request: Request,
    authorization: str | None = Header(default=None),
) -> uuid.UUID:
    if not authorization:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Authentication required"},
        )

    try:
        user = await get_authenticated_user(
            request.app.state.http_client,
            request.app.state.settings.auth_service_url,
            authorization,
        )
    except AuthError as exc:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": "Authentication required"},
        ) from exc
    return user.id
