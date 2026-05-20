import uuid
from datetime import date, datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.schemas.enums import RecurringFrequency, TransactionType
from app.schemas.transactions import RefOut


class RecurringTransactionCreate(BaseModel):
    wallet_id: uuid.UUID
    category_id: uuid.UUID
    type: TransactionType
    amount: Decimal = Field(gt=0)
    currency_code: str = Field(min_length=3, max_length=3)
    title: str = Field(min_length=1, max_length=160)
    description: str | None = None
    frequency: RecurringFrequency
    start_date: date
    end_date: date | None = None
    next_run_date: date
    is_active: bool = True

    @field_validator("currency_code")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()


class RecurringTransactionUpdate(BaseModel):
    wallet_id: uuid.UUID | None = None
    category_id: uuid.UUID | None = None
    amount: Decimal | None = Field(default=None, gt=0)
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    title: str | None = Field(default=None, min_length=1, max_length=160)
    description: str | None = None
    frequency: RecurringFrequency | None = None
    start_date: date | None = None
    end_date: date | None = None
    next_run_date: date | None = None
    is_active: bool | None = None

    @field_validator("currency_code")
    @classmethod
    def uppercase_currency(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class RecurringTransactionOut(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    wallet: RefOut
    category: RefOut
    type: str
    amount: Decimal
    currency_code: str
    title: str
    description: str | None = None
    frequency: str
    start_date: date
    end_date: date | None
    next_run_date: date
    is_active: bool
    created_at: datetime
    updated_at: datetime
