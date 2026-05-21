import uuid

from sqlalchemy import Select, func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import ReportExportJob, ReportFile, ReportSnapshot
from app.schemas.pagination import PaginationParams


class ReportRepository:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_snapshot(self, snapshot: ReportSnapshot) -> ReportSnapshot:
        self.session.add(snapshot)
        await self.session.flush()
        await self.session.refresh(snapshot)
        return snapshot

    async def create_export_job(self, job: ReportExportJob) -> ReportExportJob:
        self.session.add(job)
        await self.session.flush()
        await self.session.refresh(job, attribute_names=["report_snapshot", "files"])
        return job

    async def list_export_jobs(
        self,
        user_id: uuid.UUID,
        pagination: PaginationParams,
        status: str | None = None,
        export_type: str | None = None,
    ) -> tuple[list[ReportExportJob], int]:
        query = (
            select(ReportExportJob)
            .options(selectinload(ReportExportJob.report_snapshot), selectinload(ReportExportJob.files))
            .where(ReportExportJob.user_id == user_id)
        )
        query = self._apply_export_filters(query, status, export_type)

        count_query = select(func.count()).select_from(ReportExportJob).where(
            ReportExportJob.user_id == user_id
        )
        count_query = self._apply_export_filters(count_query, status, export_type)
        total = int(await self.session.scalar(count_query) or 0)

        result = await self.session.execute(
            query.order_by(ReportExportJob.requested_at.desc())
            .limit(pagination.page_size)
            .offset(pagination.offset)
        )
        return list(result.scalars().all()), total

    async def get_export_job(self, user_id: uuid.UUID, job_id: uuid.UUID) -> ReportExportJob | None:
        result = await self.session.execute(
            select(ReportExportJob)
            .options(selectinload(ReportExportJob.report_snapshot), selectinload(ReportExportJob.files))
            .where(ReportExportJob.id == job_id, ReportExportJob.user_id == user_id)
        )
        return result.scalar_one_or_none()

    async def get_file(self, user_id: uuid.UUID, file_id: uuid.UUID) -> ReportFile | None:
        result = await self.session.execute(
            select(ReportFile)
            .join(ReportExportJob)
            .where(ReportFile.id == file_id, ReportExportJob.user_id == user_id)
        )
        return result.scalar_one_or_none()

    def _apply_export_filters(
        self,
        query: Select,
        status: str | None,
        export_type: str | None,
    ) -> Select:
        if status:
            query = query.where(ReportExportJob.status == status.upper())
        if export_type:
            query = query.where(ReportExportJob.export_type == export_type.upper())
        return query
