import uuid
from datetime import datetime

from pydantic import BaseModel, Field

from app.schemas.base import ModelOut
from app.schemas.enums import CategoryType


class CategoryCreate(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    type: CategoryType
    icon: str | None = Field(default=None, max_length=80)
    color: str | None = Field(default=None, max_length=40)
    parent_category_id: uuid.UUID | None = None


class CategoryUpdate(BaseModel):
    name: str | None = Field(default=None, min_length=1, max_length=120)
    icon: str | None = Field(default=None, max_length=80)
    color: str | None = Field(default=None, max_length=40)
    parent_category_id: uuid.UUID | None = None
    is_active: bool | None = None


class CategoryOut(ModelOut):
    id: uuid.UUID
    user_id: uuid.UUID | None = None
    name: str
    type: str
    icon: str | None
    color: str | None
    parent_category_id: uuid.UUID | None
    is_system: bool
    is_active: bool
    created_at: datetime
    updated_at: datetime
