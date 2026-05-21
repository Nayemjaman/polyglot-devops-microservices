import uuid

from sqlalchemy import CheckConstraint, ForeignKey, Index, String
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import CreatedAtMixin, UUIDPrimaryKeyMixin


class ReportFile(UUIDPrimaryKeyMixin, CreatedAtMixin, Base):
    __tablename__ = "report_files"
    __table_args__ = (
        CheckConstraint("file_size >= 0", name="ck_report_files_file_size_non_negative"),
        Index("ix_report_files_export_job_id", "export_job_id"),
    )

    export_job_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("report_export_jobs.id", ondelete="CASCADE"),
        nullable=False,
    )
    file_url: Mapped[str] = mapped_column(String(500), nullable=False)
    file_name: Mapped[str] = mapped_column(String(255), nullable=False)
    file_type: Mapped[str] = mapped_column(String(80), nullable=False)
    file_size: Mapped[int] = mapped_column(nullable=False)

    export_job: Mapped["ReportExportJob"] = relationship(back_populates="files")
