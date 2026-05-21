"""create report schema

Revision ID: 20260521_0001
Revises:
Create Date: 2026-05-21

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "20260521_0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute("CREATE EXTENSION IF NOT EXISTS pgcrypto")

    op.create_table(
        "report_snapshots",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_type", sa.String(length=60), nullable=False),
        sa.Column("year", sa.Integer(), nullable=False),
        sa.Column("month", sa.Integer(), nullable=True),
        sa.Column("currency_code", sa.String(length=3), nullable=False),
        sa.Column("total_income", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("total_expense", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("balance", sa.Numeric(precision=14, scale=2), nullable=False),
        sa.Column("savings_rate", sa.Numeric(precision=7, scale=2), nullable=False),
        sa.Column("category_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("wallet_breakdown", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("budget_summary", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("raw_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("generated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("year >= 1900 AND year <= 9999", name="ck_report_snapshots_year"),
        sa.CheckConstraint(
            "month IS NULL OR (month >= 1 AND month <= 12)",
            name="ck_report_snapshots_month",
        ),
        sa.CheckConstraint(
            "total_income >= 0",
            name="ck_report_snapshots_total_income_non_negative",
        ),
        sa.CheckConstraint(
            "total_expense >= 0",
            name="ck_report_snapshots_total_expense_non_negative",
        ),
        sa.CheckConstraint(
            "savings_rate >= -100 AND savings_rate <= 100",
            name="ck_report_snapshots_savings_rate_range",
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_report_snapshots_user_id", "report_snapshots", ["user_id"])
    op.create_index("ix_report_snapshots_generated_at", "report_snapshots", ["generated_at"])
    op.create_index(
        "ix_report_snapshots_user_period",
        "report_snapshots",
        ["user_id", "report_type", "year", "month"],
    )

    op.create_table(
        "report_export_jobs",
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("report_snapshot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("export_type", sa.String(length=20), nullable=False),
        sa.Column("status", sa.String(length=20), nullable=False),
        sa.Column("error_message", sa.String(length=1000), nullable=True),
        sa.Column("requested_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint(
            "status IN ('PENDING','PROCESSING','COMPLETED','FAILED')",
            name="ck_report_export_jobs_status",
        ),
        sa.CheckConstraint(
            "export_type IN ('PDF','CSV','XLSX','JSON')",
            name="ck_report_export_jobs_export_type",
        ),
        sa.ForeignKeyConstraint(["report_snapshot_id"], ["report_snapshots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_report_export_jobs_user_id", "report_export_jobs", ["user_id"])
    op.create_index(
        "ix_report_export_jobs_report_snapshot_id",
        "report_export_jobs",
        ["report_snapshot_id"],
    )
    op.create_index(
        "ix_report_export_jobs_user_status",
        "report_export_jobs",
        ["user_id", "status"],
    )
    op.create_index("ix_report_export_jobs_requested_at", "report_export_jobs", ["requested_at"])

    op.create_table(
        "dashboard_cache_snapshots",
        sa.Column("report_snapshot_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("user_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("dashboard_data", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("cache_date", sa.DateTime(timezone=True), nullable=False),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["report_snapshot_id"], ["report_snapshots.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        "ix_dashboard_cache_snapshots_report_snapshot_id",
        "dashboard_cache_snapshots",
        ["report_snapshot_id"],
    )
    op.create_index("ix_dashboard_cache_snapshots_user_id", "dashboard_cache_snapshots", ["user_id"])
    op.create_index(
        "ix_dashboard_cache_snapshots_user_cache_date",
        "dashboard_cache_snapshots",
        ["user_id", "cache_date"],
    )

    op.create_table(
        "report_files",
        sa.Column("export_job_id", postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column("file_url", sa.String(length=500), nullable=False),
        sa.Column("file_name", sa.String(length=255), nullable=False),
        sa.Column("file_type", sa.String(length=80), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column(
            "id",
            postgresql.UUID(as_uuid=True),
            server_default=sa.text("gen_random_uuid()"),
            nullable=False,
        ),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.CheckConstraint("file_size >= 0", name="ck_report_files_file_size_non_negative"),
        sa.ForeignKeyConstraint(["export_job_id"], ["report_export_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_report_files_export_job_id", "report_files", ["export_job_id"])


def downgrade() -> None:
    op.drop_index("ix_report_files_export_job_id", table_name="report_files")
    op.drop_table("report_files")
    op.drop_index("ix_dashboard_cache_snapshots_user_cache_date", table_name="dashboard_cache_snapshots")
    op.drop_index("ix_dashboard_cache_snapshots_user_id", table_name="dashboard_cache_snapshots")
    op.drop_index(
        "ix_dashboard_cache_snapshots_report_snapshot_id",
        table_name="dashboard_cache_snapshots",
    )
    op.drop_table("dashboard_cache_snapshots")
    op.drop_index("ix_report_export_jobs_requested_at", table_name="report_export_jobs")
    op.drop_index("ix_report_export_jobs_user_status", table_name="report_export_jobs")
    op.drop_index("ix_report_export_jobs_report_snapshot_id", table_name="report_export_jobs")
    op.drop_index("ix_report_export_jobs_user_id", table_name="report_export_jobs")
    op.drop_table("report_export_jobs")
    op.drop_index("ix_report_snapshots_user_period", table_name="report_snapshots")
    op.drop_index("ix_report_snapshots_generated_at", table_name="report_snapshots")
    op.drop_index("ix_report_snapshots_user_id", table_name="report_snapshots")
    op.drop_table("report_snapshots")
