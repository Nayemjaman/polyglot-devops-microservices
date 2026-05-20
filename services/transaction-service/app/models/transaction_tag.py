import uuid

from sqlalchemy import ForeignKey, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base
from app.models.mixins import UUIDPrimaryKeyMixin


class TransactionTag(UUIDPrimaryKeyMixin, Base):
    __tablename__ = "transaction_tags"
    __table_args__ = (
        UniqueConstraint("transaction_id", "tag_id", name="uq_transaction_tags_transaction_tag"),
    )

    transaction_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("transactions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    tag_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("tags.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    transaction: Mapped["Transaction"] = relationship(back_populates="transaction_tags")
    tag: Mapped["Tag"] = relationship(back_populates="transaction_tags")
