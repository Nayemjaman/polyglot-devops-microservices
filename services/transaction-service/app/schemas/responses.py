from typing import Any

from pydantic import BaseModel


class ApiResponse(BaseModel):
    success: bool = True
    message: str
    data: Any = None


class PaginatedResponse(ApiResponse):
    pagination: "Pagination"


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: dict[str, list[str]] | None = None


from app.schemas.pagination import Pagination  # noqa: E402
