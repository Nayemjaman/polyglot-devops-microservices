from fastapi import APIRouter

from app.api.routes import health, hello, reports

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(hello.router)
api_router.include_router(reports.router)
