import uuid
import csv
import io
from datetime import datetime, timezone
from decimal import Decimal
from typing import Any

from app.models import ReportExportJob, ReportFile, ReportSnapshot
from app.repositories.reports import ReportRepository
from app.schemas.pagination import PaginationParams
from app.schemas.reports import ExportCreatedOut, ExportJobOut, ExportRequest, ReportFileOut
from app.services.exceptions import NotFoundError, ValidationServiceError

REPORT_TYPES = {
    "MONTHLY",
    "YEARLY",
    "INCOME_VS_EXPENSE",
    "CATEGORY_WISE",
    "WALLET_WISE",
    "BUDGET_PERFORMANCE",
    "SAVINGS",
    "DASHBOARD",
}
EXPORT_TYPES = {"PDF", "CSV", "XLSX"}
EXPORT_STATUSES = {"PENDING", "PROCESSING", "COMPLETED", "FAILED"}


class ReportService:
    def __init__(self, repo: ReportRepository) -> None:
        self.repo = repo

    async def monthly_report(self, user_id: uuid.UUID, year: int, month: int) -> dict[str, Any]:
        snapshot = await self._create_snapshot(user_id, "MONTHLY", year, month)
        return {
            "report_snapshot_id": snapshot.id,
            "report_type": "MONTHLY",
            "user_id": user_id,
            "year": year,
            "month": month,
            "currency_code": snapshot.currency_code,
            "summary": self._summary(snapshot),
            "category_breakdown": snapshot.category_breakdown.get("items", []),
            "wallet_breakdown": snapshot.wallet_breakdown.get("items", []),
            "budget_summary": snapshot.budget_summary,
            "generated_at": snapshot.generated_at,
        }

    async def yearly_report(self, user_id: uuid.UUID, year: int) -> dict[str, Any]:
        snapshot = await self._create_snapshot(user_id, "YEARLY", year, None)
        return {
            "report_snapshot_id": snapshot.id,
            "report_type": "YEARLY",
            "user_id": user_id,
            "year": year,
            "currency_code": snapshot.currency_code,
            "summary": self._summary(snapshot, include_count=False),
            "monthly_breakdown": snapshot.raw_data.get("monthly_breakdown", self._empty_months()),
            "generated_at": snapshot.generated_at,
        }

    async def income_vs_expense(
        self, user_id: uuid.UUID, year: int, month: int | None
    ) -> dict[str, Any]:
        snapshot = await self._create_snapshot(user_id, "INCOME_VS_EXPENSE", year, month)
        total = snapshot.total_income + snapshot.total_expense
        income_percentage = self._percentage(snapshot.total_income, total)
        expense_percentage = self._percentage(snapshot.total_expense, total)
        data: dict[str, Any] = {
            "year": year,
            "currency_code": snapshot.currency_code,
            "total_income": snapshot.total_income,
            "total_expense": snapshot.total_expense,
            "balance": snapshot.balance,
            "income_percentage": income_percentage,
            "expense_percentage": expense_percentage,
            "chart_data": [
                {"label": "Income", "value": snapshot.total_income},
                {"label": "Expense", "value": snapshot.total_expense},
            ],
        }
        if month is not None:
            data["month"] = month
        return data

    async def category_wise(
        self,
        user_id: uuid.UUID,
        year: int,
        month: int,
        transaction_type: str | None,
    ) -> dict[str, Any]:
        snapshot = await self._create_snapshot(user_id, "CATEGORY_WISE", year, month)
        categories = snapshot.category_breakdown.get("items", [])
        return {
            "year": year,
            "month": month,
            "type": (transaction_type or "EXPENSE").upper(),
            "currency_code": snapshot.currency_code,
            "total_amount": sum(
                (Decimal(str(item.get("total_amount", 0))) for item in categories), Decimal("0")
            ),
            "categories": categories,
        }

    async def wallet_wise(self, user_id: uuid.UUID, year: int, month: int) -> dict[str, Any]:
        snapshot = await self._create_snapshot(user_id, "WALLET_WISE", year, month)
        return {
            "year": year,
            "month": month,
            "currency_code": snapshot.currency_code,
            "wallets": snapshot.wallet_breakdown.get("items", []),
        }

    async def budget_performance(self, user_id: uuid.UUID, year: int, month: int) -> dict[str, Any]:
        snapshot = await self._create_snapshot(user_id, "BUDGET_PERFORMANCE", year, month)
        return {
            "year": year,
            "month": month,
            "currency_code": snapshot.currency_code,
            **snapshot.budget_summary,
        }

    async def savings(self, user_id: uuid.UUID, year: int, month: int) -> dict[str, Any]:
        snapshot = await self._create_snapshot(user_id, "SAVINGS", year, month)
        savings_amount = snapshot.balance
        status, recommendation = self._savings_status(snapshot.savings_rate)
        return {
            "year": year,
            "month": month,
            "currency_code": snapshot.currency_code,
            "total_income": snapshot.total_income,
            "total_expense": snapshot.total_expense,
            "savings_amount": savings_amount,
            "savings_rate": snapshot.savings_rate,
            "status": status,
            "recommendation": recommendation,
        }

    async def dashboard(self, user_id: uuid.UUID, year: int, month: int) -> dict[str, Any]:
        snapshot = await self._create_snapshot(user_id, "DASHBOARD", year, month)
        budget_used = Decimal(str(snapshot.budget_summary.get("used_percentage", 0)))
        return {
            "year": year,
            "month": month,
            "currency_code": snapshot.currency_code,
            "cards": {
                "total_income": snapshot.total_income,
                "total_expense": snapshot.total_expense,
                "balance": snapshot.balance,
                "savings_rate": snapshot.savings_rate,
                "budget_used_percentage": budget_used,
            },
            "charts": {
                "income_vs_expense": [
                    {"label": "Income", "value": snapshot.total_income},
                    {"label": "Expense", "value": snapshot.total_expense},
                ],
                "category_expense": [
                    {"label": item.get("category_name"), "value": item.get("total_amount")}
                    for item in snapshot.category_breakdown.get("items", [])
                ],
                "budget_usage": [
                    {
                        "label": "Used",
                        "value": snapshot.budget_summary.get("total_spent_amount", 0),
                    },
                    {
                        "label": "Remaining",
                        "value": snapshot.budget_summary.get("remaining_amount", 0),
                    },
                ],
            },
            "recent_insights": [
                {
                    "type": "SAVINGS",
                    "message": f"Your savings status is {self._savings_status(snapshot.savings_rate)[0]}.",
                }
            ],
            "generated_at": snapshot.generated_at,
        }

    async def dashboard_monthly_summary(self, user_id: uuid.UUID, year: int) -> dict[str, Any]:
        snapshot = await self._create_snapshot(user_id, "DASHBOARD", year, None)
        return {
            "year": year,
            "currency_code": snapshot.currency_code,
            "months": snapshot.raw_data.get("monthly_breakdown", self._empty_months()),
        }

    async def create_export_job(
        self, user_id: uuid.UUID, payload: ExportRequest
    ) -> ExportCreatedOut:
        self._validate_export_request(payload)
        snapshot = await self._create_snapshot(
            user_id, payload.report_type, payload.year, payload.month
        )
        now = datetime.now(timezone.utc)
        job = await self.repo.create_export_job(
            ReportExportJob(
                user_id=user_id,
                report_snapshot_id=snapshot.id,
                export_type=payload.export_type,
                status="PROCESSING",
                requested_at=now,
                started_at=now,
            )
        )
        content, _ = self.render_export_file(snapshot, payload.export_type)
        file = ReportFile(
            export_job_id=job.id,
            file_url=f"memory://reports/{job.id}.{payload.export_type.lower()}",
            file_name=f"{snapshot.report_type.lower()}-{snapshot.year}-{snapshot.month or 'all'}.{payload.export_type.lower()}",
            file_type=payload.export_type,
            file_size=len(content.encode("utf-8")),
        )
        job = await self.repo.mark_export_job_completed(job, datetime.now(timezone.utc), file)
        return ExportCreatedOut(
            export_job_id=job.id,
            report_snapshot_id=snapshot.id,
            report_type=snapshot.report_type,
            export_type=job.export_type,
            status=job.status,
            requested_at=job.requested_at,
        )

    async def list_export_jobs(
        self,
        user_id: uuid.UUID,
        pagination: PaginationParams,
        status: str | None,
        export_type: str | None,
    ) -> tuple[list[ExportJobOut], int]:
        if status and status.upper() not in EXPORT_STATUSES:
            raise ValidationServiceError(
                "Validation failed", {"status": ["Invalid export job status"]}
            )
        if export_type and export_type.upper() not in EXPORT_TYPES:
            raise ValidationServiceError(
                "Validation failed", {"export_type": ["Invalid export type"]}
            )
        jobs, total = await self.repo.list_export_jobs(user_id, pagination, status, export_type)
        return [self._job_out(job, include_user=False) for job in jobs], total

    async def get_export_job(self, user_id: uuid.UUID, job_id: uuid.UUID) -> ExportJobOut:
        job = await self.repo.get_export_job(user_id, job_id)
        if job is None:
            raise NotFoundError("Export job not found")
        if job.status in {"PENDING", "PROCESSING"} or not job.files:
            content, _ = self.render_export_file(job.report_snapshot, job.export_type)
            file = ReportFile(
                export_job_id=job.id,
                file_url=f"memory://reports/{job.id}.{job.export_type.lower()}",
                file_name=f"{job.report_snapshot.report_type.lower()}-{job.report_snapshot.year}-{job.report_snapshot.month or 'all'}.{job.export_type.lower()}",
                file_type=job.export_type,
                file_size=len(content.encode("utf-8")),
            )
            job = await self.repo.mark_export_job_completed(job, datetime.now(timezone.utc), file)
        return self._job_out(job, include_user=True)

    async def get_export_created(self, user_id: uuid.UUID, job_id: uuid.UUID) -> ExportCreatedOut:
        job = await self.repo.get_export_job(user_id, job_id)
        if job is None:
            raise NotFoundError("Export job not found")
        return ExportCreatedOut(
            export_job_id=job.id,
            report_snapshot_id=job.report_snapshot_id,
            report_type=job.report_snapshot.report_type,
            export_type=job.export_type,
            status=job.status,
            requested_at=job.requested_at,
        )

    async def get_file(self, user_id: uuid.UUID, file_id: uuid.UUID):
        file = await self.repo.get_file(user_id, file_id)
        if file is None:
            raise NotFoundError("Report file not found")
        return file

    def render_export_file(self, snapshot: ReportSnapshot, export_type: str) -> tuple[str, str]:
        payload = {
            "report_snapshot_id": str(snapshot.id),
            "report_type": snapshot.report_type,
            "year": snapshot.year,
            "month": snapshot.month,
            "total_income": str(snapshot.total_income),
            "total_expense": str(snapshot.total_expense),
            "balance": str(snapshot.balance),
            "savings_rate": str(snapshot.savings_rate),
            "currency_code": snapshot.currency_code,
            "generated_at": snapshot.generated_at.isoformat() if snapshot.generated_at else "",
        }
        if export_type == "CSV":
            output = io.StringIO()
            writer = csv.DictWriter(output, fieldnames=list(payload.keys()))
            writer.writeheader()
            writer.writerow(payload)
            return output.getvalue(), "text/csv"
        lines = [f"{key}: {value}" for key, value in payload.items()]
        if export_type == "PDF":
            return "\n".join(lines), "application/pdf"
        return "\n".join(lines), "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"

    async def _create_snapshot(
        self,
        user_id: uuid.UUID,
        report_type: str,
        year: int,
        month: int | None,
    ) -> ReportSnapshot:
        now = datetime.now(timezone.utc)
        snapshot = ReportSnapshot(
            user_id=user_id,
            report_type=report_type,
            year=year,
            month=month,
            currency_code="BDT",
            total_income=Decimal("0"),
            total_expense=Decimal("0"),
            balance=Decimal("0"),
            savings_rate=Decimal("0"),
            category_breakdown={"items": []},
            wallet_breakdown={"items": []},
            budget_summary={
                "total_budget_amount": 0,
                "total_spent_amount": 0,
                "remaining_amount": 0,
                "used_percentage": 0,
                "status": "NO_BUDGET",
                "categories": [],
            },
            raw_data={"monthly_breakdown": self._empty_months()},
            generated_at=now,
        )
        return await self.repo.create_snapshot(snapshot)

    def _validate_export_request(self, payload: ExportRequest) -> None:
        errors: dict[str, list[str]] = {}
        if payload.report_type not in REPORT_TYPES:
            errors["report_type"] = ["Invalid report type"]
        if payload.export_type not in EXPORT_TYPES:
            errors["export_type"] = ["Invalid export type"]
        if payload.report_type not in {"YEARLY", "DASHBOARD"} and payload.month is None:
            errors["month"] = ["Month is required for this report type"]
        if errors:
            raise ValidationServiceError("Validation failed", errors)

    def _summary(self, snapshot: ReportSnapshot, include_count: bool = True) -> dict[str, Any]:
        summary: dict[str, Any] = {
            "total_income": snapshot.total_income,
            "total_expense": snapshot.total_expense,
            "balance": snapshot.balance,
            "savings_rate": snapshot.savings_rate,
        }
        if include_count:
            summary["transaction_count"] = snapshot.raw_data.get("transaction_count", 0)
        return summary

    def _job_out(self, job: ReportExportJob, include_user: bool) -> ExportJobOut:
        file = job.files[0] if job.files else None
        return ExportJobOut(
            id=job.id,
            user_id=job.user_id if include_user else None,
            report_snapshot_id=job.report_snapshot_id,
            report_type=job.report_snapshot.report_type,
            export_type=job.export_type,
            status=job.status,
            error_message=job.error_message,
            requested_at=job.requested_at,
            started_at=job.started_at,
            completed_at=job.completed_at,
            file=ReportFileOut(
                id=file.id,
                file_url=file.file_url if include_user else None,
                file_name=file.file_name,
                file_type=file.file_type,
                file_size=file.file_size,
            )
            if file
            else None,
        )

    def _savings_status(self, savings_rate: Decimal) -> tuple[str, str]:
        if savings_rate >= Decimal("50"):
            return "EXCELLENT", "You saved more than 50% of your income."
        if savings_rate >= Decimal("30"):
            return "GOOD", "You saved more than 30% of your income."
        if savings_rate >= Decimal("10"):
            return "AVERAGE", "Your savings are positive but can improve."
        if savings_rate > Decimal("0"):
            return "LOW", "Your savings rate is low."
        return "NEGATIVE", "Your expenses are equal to or higher than your income."

    def _percentage(self, value: Decimal, total: Decimal) -> Decimal:
        if total == 0:
            return Decimal("0")
        return (value / total * Decimal("100")).quantize(Decimal("0.01"))

    def _empty_months(self) -> list[dict[str, Any]]:
        return [
            {
                "month": month,
                "total_income": 0,
                "total_expense": 0,
                "balance": 0,
                "savings_rate": 0,
            }
            for month in range(1, 13)
        ]
