import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.schemas.attachments import AttachmentOut
from app.schemas.enums import TransactionType


class RefOut(BaseModel):
    id: uuid.UUID
    name: str
    type: str | None = None


class TransactionCreate(BaseModel):
    wallet_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    payment_method_id: uuid.UUID | None = None
    type: TransactionType
    amount: Decimal = Field(gt=0)
    currency_code: str = Field(min_length=3, max_length=3)
    title: str = Field(min_length=1, max_length=160)
    description: str | None = None
    transaction_date: date
    tags: list[str] = Field(default_factory=list)
    from_wallet_id: uuid.UUID | None = None
    to_wallet_id: uuid.UUID | None = None

    @field_validator("currency_code")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()


class TransactionUpdate(BaseModel):
    wallet_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    payment_method_id: uuid.UUID | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None
    transaction_date: date | None = None
    tags: list[str] | None = None

    @field_validator("currency_code")
    @classmethod
    def uppercase_currency(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class TransactionOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    wallet: RefOut
    category: RefOut
    payment_method: RefOut
    type: str
    amount: Decimal
    currency_code: str
    title: str
    description: str | None = None
    transaction_date: date
    tags: list[str]
    attachments: list[AttachmentOut] = Field(default_factory=list)
    is_deleted: bool
    created_at: datetime
    updated_at: datetime
