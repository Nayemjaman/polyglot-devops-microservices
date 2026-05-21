import uuid
from collections.abc import AsyncGenerator
from datetime import datetime, timedelta, timezone

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

    cache = request.app.state.auth_cache
    cached = cache.get(authorization)
    now = datetime.now(timezone.utc)
    if cached and cached["expires_at"] > now:
        return cached["user_id"]

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
    cache[authorization] = {
        "user_id": user.id,
        "expires_at": now + timedelta(seconds=30),
    }
    return user.id
