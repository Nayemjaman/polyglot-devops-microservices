from typing import Any

from pydantic import BaseModel, Field


class ApiResponse(BaseModel):
    success: bool = True
    message: str
    data: Any = None


class PaginatedResponse(BaseModel):
    success: bool = True
    message: str
    data: Any = None
    pagination: dict[str, int]


class ErrorResponse(BaseModel):
    success: bool = False
    message: str
    errors: dict[str, list[str]] | None = None


class HealthResponse(BaseModel):
    status: str = Field(default="ok")
    service: str = Field(default="report-service")
