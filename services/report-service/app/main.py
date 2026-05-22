from contextlib import asynccontextmanager

import httpx
from redis.asyncio import Redis
from fastapi import FastAPI, HTTPException, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.cache import DashboardCache, NullDashboardCache
from app.core.config import get_settings
from app.core.middleware import add_security_middleware
from app.db.session import create_engine, create_sessionmaker
from app.messaging import NullPublisher, RabbitMQPublisher
from app.schemas.responses import ErrorResponse


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings
    app.state.http_client = httpx.AsyncClient(timeout=settings.http_timeout_seconds)
    app.state.auth_cache = {}
    app.state.db_engine = create_engine(settings)
    app.state.db_sessionmaker = create_sessionmaker(app.state.db_engine)
    app.state.redis = Redis.from_url(settings.redis_url, decode_responses=True)
    try:
        await app.state.redis.ping()
        app.state.dashboard_cache = DashboardCache(app.state.redis, settings)
    except Exception:
        app.state.dashboard_cache = NullDashboardCache()
    app.state.event_publisher = RabbitMQPublisher(settings)
    try:
        await app.state.event_publisher.connect()
    except Exception:
        app.state.event_publisher = NullPublisher()
    try:
        yield
    finally:
        if hasattr(app.state.event_publisher, "close"):
            await app.state.event_publisher.close()
        await app.state.redis.aclose()
        await app.state.http_client.aclose()
        await app.state.db_engine.dispose()


async def http_exception_handler(request: Request, exc: HTTPException) -> JSONResponse:
    message = "Request failed"
    errors = None
    if isinstance(exc.detail, dict):
        message = exc.detail.get("message") or exc.detail.get("detail") or message
        errors = exc.detail.get("errors")
    elif exc.detail:
        message = str(exc.detail)
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(message=message, errors=errors).model_dump(),
        headers=getattr(exc, "headers", None),
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    errors: dict[str, list[str]] = {}
    for error in exc.errors():
        field = ".".join(str(part) for part in error["loc"] if part not in {"body", "query", "path"})
        errors.setdefault(field or "request", []).append(error["msg"])
    return JSONResponse(
        status_code=400,
        content=ErrorResponse(message="Validation failed", errors=errors).model_dump(),
    )


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(
        title=settings.app_name,
        version="0.1.0",
        docs_url="/docs" if settings.app_env != "production" else None,
        redoc_url="/redoc" if settings.app_env != "production" else None,
        lifespan=lifespan,
    )
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    add_security_middleware(app, settings)
    app.include_router(api_router)
    return app


app = create_app()
