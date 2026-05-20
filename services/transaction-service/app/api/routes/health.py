from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_attachment_storage, get_db_session
from app.schemas.common import HealthResponse
from app.storage.client import AttachmentStorage, StorageUnavailableError

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health_check() -> HealthResponse:
    return HealthResponse(status="ok", service="transaction-service")


@router.get("/health/db", response_model=HealthResponse)
async def database_health_check(
    session: AsyncSession = Depends(get_db_session),
) -> HealthResponse:
    try:
        await session.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="database unavailable",
        ) from exc

    return HealthResponse(status="ok", service="transaction-service")


@router.get("/health/storage", response_model=HealthResponse)
async def storage_health_check(
    storage: AttachmentStorage = Depends(get_attachment_storage),
) -> HealthResponse:
    try:
        await storage.check_bucket()
    except StorageUnavailableError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="attachment storage unavailable",
        ) from exc

    return HealthResponse(status="ok", service="transaction-service")
