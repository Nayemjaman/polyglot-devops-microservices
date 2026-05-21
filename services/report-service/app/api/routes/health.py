from fastapi import APIRouter, Request
from sqlalchemy import text

from app.schemas.responses import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health() -> HealthResponse:
    return HealthResponse()


@router.get("/health/db", response_model=HealthResponse)
async def database_health(request: Request) -> HealthResponse:
    sessionmaker = request.app.state.db_sessionmaker
    async with sessionmaker() as session:
        await session.execute(text("SELECT 1"))
    return HealthResponse()
