import uuid
from datetime import datetime
from decimal import Decimal
from typing import Any

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class ReportSnapshot(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "report_snapshots"
    __table_args__ = (
        CheckConstraint("year >= 1900 AND year <= 9999", name="ck_report_snapshots_year"),
        CheckConstraint(
            "month IS NULL OR (month >= 1 AND month <= 12)", name="ck_report_snapshots_month"
        ),
        CheckConstraint("total_income >= 0", name="ck_report_snapshots_total_income_non_negative"),
        CheckConstraint(
            "total_expense >= 0", name="ck_report_snapshots_total_expense_non_negative"
        ),
        CheckConstraint(
            "savings_rate >= -100 AND savings_rate <= 100",
            name="ck_report_snapshots_savings_rate_range",
        ),
        Index("ix_report_snapshots_user_period", "user_id", "report_type", "year", "month"),
        Index("ix_report_snapshots_generated_at", "generated_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    report_type: Mapped[str] = mapped_column(String(60), nullable=False)
    year: Mapped[int] = mapped_column(nullable=False)
    month: Mapped[int | None] = mapped_column(nullable=True)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    total_income: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    total_expense: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    balance: Mapped[Decimal] = mapped_column(Numeric(14, 2), nullable=False, default=0)
    savings_rate: Mapped[Decimal] = mapped_column(Numeric(7, 2), nullable=False, default=0)
    category_breakdown: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    wallet_breakdown: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    budget_summary: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    raw_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    generated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    export_jobs: Mapped[list["ReportExportJob"]] = relationship(
        back_populates="report_snapshot",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
    dashboard_cache_snapshots: Mapped[list["DashboardCacheSnapshot"]] = relationship(
        back_populates="report_snapshot",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )


class DashboardCacheSnapshot(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "dashboard_cache_snapshots"
    __table_args__ = (
        Index("ix_dashboard_cache_snapshots_user_cache_date", "user_id", "cache_date"),
    )

    report_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("report_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    dashboard_data: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)
    cache_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)

    report_snapshot: Mapped[ReportSnapshot] = relationship(
        back_populates="dashboard_cache_snapshots",
    )
