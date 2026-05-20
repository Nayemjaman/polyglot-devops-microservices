import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.base import ModelOut
from app.schemas.enums import PaymentMethodType


class PaymentMethodCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: PaymentMethodType


class PaymentMethodUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    type: PaymentMethodType | None = None
    is_active: bool | None = None


class PaymentMethodOut(ModelOut):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    name: str
    type: str
    is_active: bool
    created_at: datetime
    updated_at: datetime
