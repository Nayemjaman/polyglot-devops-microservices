import uuid
from datetime import datetime

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class ReportExportJob(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "report_export_jobs"
    __table_args__ = (
        CheckConstraint(
            "status IN ('PENDING','PROCESSING','COMPLETED','FAILED')",
            name="ck_report_export_jobs_status",
        ),
        CheckConstraint(
            "export_type IN ('PDF','CSV','XLSX','JSON')",
            name="ck_report_export_jobs_export_type",
        ),
        Index("ix_report_export_jobs_user_status", "user_id", "status"),
        Index("ix_report_export_jobs_requested_at", "requested_at"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    report_snapshot_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("report_snapshots.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    export_type: Mapped[str] = mapped_column(String(20), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False, default="PENDING")
    error_message: Mapped[str | None] = mapped_column(String(1000), nullable=True)
    requested_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    report_snapshot: Mapped["ReportSnapshot"] = relationship(back_populates="export_jobs")
    files: Mapped[list["ReportFile"]] = relationship(
        back_populates="export_job",
        cascade="all, delete-orphan",
        passive_deletes=True,
    )
