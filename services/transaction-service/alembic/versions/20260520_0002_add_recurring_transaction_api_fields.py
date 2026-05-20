"""add recurring transaction api fields

Revision ID: 20260520_0002
Revises: 20260520_0001
Create Date: 2026-05-20

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "20260520_0002"
down_revision: Union[str, None] = "20260520_0001"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column(
        "recurring_transactions",
        sa.Column("currency_code", sa.String(length=3), server_default="BDT", nullable=False),
    )
    op.add_column("recurring_transactions", sa.Column("description", sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column("recurring_transactions", "description")
    op.drop_column("recurring_transactions", "currency_code")
