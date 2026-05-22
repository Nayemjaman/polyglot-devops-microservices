import uuid

from fastapi import APIRouter, Depends, Query, Request, status
from fastapi.responses import RedirectResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_id, get_db_session
from app.api.errors import raise_service_error
from app.repositories.reports import ReportRepository
from app.schemas.pagination import PaginationParams
from app.schemas.reports import ExportRequest
from app.schemas.responses import ApiResponse, PaginatedResponse
from app.services.exceptions import ServiceError
from app.services.reports import ReportService

router = APIRouter(prefix="/api/reports", tags=["reports"])


def get_report_service(session: AsyncSession) -> ReportService:
    return ReportService(ReportRepository(session))


@router.get("/monthly", response_model=ApiResponse)
async def monthly_report(
    year: int = Query(..., ge=1900, le=9999),
    month: int = Query(..., ge=1, le=12),
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    data = await get_report_service(session).monthly_report(user_id, year, month)
    await session.commit()
    return ApiResponse(message="Monthly report generated successfully", data=data)


@router.get("/yearly", response_model=ApiResponse)
async def yearly_report(
    year: int = Query(..., ge=1900, le=9999),
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    data = await get_report_service(session).yearly_report(user_id, year)
    await session.commit()
    return ApiResponse(message="Yearly report generated successfully", data=data)


@router.get("/income-vs-expense", response_model=ApiResponse)
async def income_vs_expense_report(
    year: int = Query(..., ge=1900, le=9999),
    month: int | None = Query(default=None, ge=1, le=12),
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    data = await get_report_service(session).income_vs_expense(user_id, year, month)
    await session.commit()
    return ApiResponse(message="Income vs expense report generated successfully", data=data)


@router.get("/category-wise", response_model=ApiResponse)
async def category_wise_report(
    year: int = Query(..., ge=1900, le=9999),
    month: int = Query(..., ge=1, le=12),
    type: str | None = Query(default="EXPENSE"),
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    data = await get_report_service(session).category_wise(user_id, year, month, type)
    await session.commit()
    return ApiResponse(message="Category-wise report generated successfully", data=data)


@router.get("/wallet-wise", response_model=ApiResponse)
async def wallet_wise_report(
    year: int = Query(..., ge=1900, le=9999),
    month: int = Query(..., ge=1, le=12),
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    data = await get_report_service(session).wallet_wise(user_id, year, month)
    await session.commit()
    return ApiResponse(message="Wallet-wise report generated successfully", data=data)


@router.get("/budget-performance", response_model=ApiResponse)
async def budget_performance_report(
    year: int = Query(..., ge=1900, le=9999),
    month: int = Query(..., ge=1, le=12),
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    data = await get_report_service(session).budget_performance(user_id, year, month)
    await session.commit()
    return ApiResponse(message="Budget performance report generated successfully", data=data)


@router.get("/savings", response_model=ApiResponse)
async def savings_report(
    year: int = Query(..., ge=1900, le=9999),
    month: int = Query(..., ge=1, le=12),
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    data = await get_report_service(session).savings(user_id, year, month)
    await session.commit()
    return ApiResponse(message="Savings report generated successfully", data=data)


@router.get("/dashboard", response_model=ApiResponse)
async def dashboard(
    request: Request,
    year: int = Query(..., ge=1900, le=9999),
    month: int = Query(..., ge=1, le=12),
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    cached = await request.app.state.dashboard_cache.get(user_id, year, month)
    if cached is not None:
        return ApiResponse(message="Dashboard data fetched successfully", data=cached)
    data = await get_report_service(session).dashboard(user_id, year, month)
    await session.commit()
    await request.app.state.dashboard_cache.set(user_id, year, month, data)
    return ApiResponse(message="Dashboard data fetched successfully", data=data)


@router.get("/dashboard/monthly-summary", response_model=ApiResponse)
async def dashboard_monthly_summary(
    year: int = Query(..., ge=1900, le=9999),
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    data = await get_report_service(session).dashboard_monthly_summary(user_id, year)
    await session.commit()
    return ApiResponse(message="Dashboard monthly summary fetched successfully", data=data)


@router.post("/export", response_model=ApiResponse, status_code=status.HTTP_201_CREATED)
async def create_export_job(
    request: Request,
    payload: ExportRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        data = await get_report_service(session).create_export_job(user_id, payload)
    except ServiceError as exc:
        await session.rollback()
        raise_service_error(exc)
    await session.commit()
    await request.app.state.event_publisher.publish(
        "report.export.requested",
        {
            "export_job_id": str(data.export_job_id),
            "report_snapshot_id": str(data.report_snapshot_id),
            "user_id": str(user_id),
            "report_type": data.report_type,
            "export_type": data.export_type,
        },
    )
    return ApiResponse(message="Report export job created successfully", data=data)


@router.get("/export-jobs", response_model=PaginatedResponse)
async def list_export_jobs(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    status: str | None = None,
    export_type: str | None = None,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> PaginatedResponse:
    pagination = PaginationParams(page=page, page_size=page_size)
    try:
        data, total = await get_report_service(session).list_export_jobs(
            user_id,
            pagination,
            status,
            export_type,
        )
    except ServiceError as exc:
        raise_service_error(exc)
    return PaginatedResponse(
        message="Export jobs fetched successfully",
        data=data,
        pagination=pagination.to_response(total),
    )


@router.get("/export-jobs/{id}", response_model=ApiResponse)
async def get_export_job(
    id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
) -> ApiResponse:
    try:
        data = await get_report_service(session).get_export_job(user_id, id)
    except ServiceError as exc:
        raise_service_error(exc)
    return ApiResponse(message="Export job fetched successfully", data=data)


@router.get("/files/{id}/download")
async def download_report_file(
    id: uuid.UUID,
    user_id: uuid.UUID = Depends(get_current_user_id),
    session: AsyncSession = Depends(get_db_session),
):
    try:
        file = await get_report_service(session).get_file(user_id, id)
    except ServiceError as exc:
        raise_service_error(exc)
    return RedirectResponse(url=file.file_url)
