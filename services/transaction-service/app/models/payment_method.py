import uuid

from sqlalchemy import Boolean, Index, String, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import TimestampMixin, UUIDPrimaryKeyMixin


class PaymentMethod(UUIDPrimaryKeyMixin, TimestampMixin, Base):
    __tablename__ = "payment_methods"
    __table_args__ = (
        UniqueConstraint("user_id", "name", name="uq_payment_methods_user_name"),
        Index("ix_payment_methods_user_active", "user_id", "is_active"),
    )

    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False, index=True)
    name: Mapped[str] = mapped_column(String(120), nullable=False)
    type: Mapped[str] = mapped_column(String(40), nullable=False)
    is_active: Mapped[bool] = mapped_column(Boolean, nullable=False, server_default="true")

    transactions: Mapped[list["Transaction"]] = relationship(back_populates="payment_method")
