import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from pydantic import BaseModel, Field, field_validator


class ReportQuery(BaseModel):
    year: int = Field(ge=1900, le=9999)
    month: int | None = Field(default=None, ge=1, le=12)


class ExportRequest(BaseModel):
    report_type: str
    export_type: str
    year: int = Field(ge=1900, le=9999)
    month: int | None = Field(default=None, ge=1, le=12)
    filters: dict[str, Any] = Field(default_factory=dict)

    @field_validator("report_type", "export_type")
    @classmethod
    def uppercase(cls, value: str) -> str:
        return value.upper()


class ReportFileOut(BaseModel):
    id: uuid.UUID
    file_url: str | None = None
    file_name: str
    file_type: str
    file_size: int


class ExportJobOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    report_snapshot_id: uuid.UUID
    report_type: str
    export_type: str
    status: str
    error_message: str | None = None
    requested_at: datetime
    started_at: datetime | None = None
    completed_at: datetime | None = None
    file: ReportFileOut | None = None


class ExportCreatedOut(BaseModel):
    export_job_id: uuid.UUID
    report_snapshot_id: uuid.UUID
    report_type: str
    export_type: str
    status: str
    requested_at: datetime


class SummaryOut(BaseModel):
    total_income: Decimal
    total_expense: Decimal
    balance: Decimal
    savings_rate: Decimal
    transaction_count: int = 0
