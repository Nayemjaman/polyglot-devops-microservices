import uuid
from decimal import Decimal

from sqlalchemy import Boolean, Index, Numeric, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class Wallet(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "wallets"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_wallets_user_name"),
        Index("ix_wallets_user_active", "user_id", "is_active"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    currency_code: Mapped[str] = mapped_column(String(3), nullable=False)
    opening_balance: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        server_default="0",
    )
    current_balance: Mapped[Decimal] = mapped_column(
        Numeric(14, 2),
        nullable=False,
        server_default="0",
    )
    is_default: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="false")
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="wallet")
    recurring_transactions: Mapped[list["RecurringTransaction"]] = relationship(
        back_populates="wallet"
    )
