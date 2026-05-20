import uuid
from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, Field, field_validator

from app.schemas.base import ModelOut
from app.schemas.enums import WalletType


class WalletCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: WalletType
    currency_code: str = Field(min_length=3, max_length=3)
    opening_balance: Decimal = Field(ge=0)
    is_default: bool = False

    @field_validator("currency_code")
    @classmethod
    def uppercase_currency(cls, value: str) -> str:
        return value.upper()


class WalletUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    type: WalletType | None = None
    currency_code: str | None = Field(default=None, min_length=3, max_length=3)
    is_default: bool | None = None
    is_active: bool | None = None

    @field_validator("currency_code")
    @classmethod
    def uppercase_currency(cls, value: str | None) -> str | None:
        return value.upper() if value else value


class WalletOut(ModelOut):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    name: str
    type: str
    currency_code: str
    opening_balance: Decimal
    current_balance: Decimal
    is_default: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
