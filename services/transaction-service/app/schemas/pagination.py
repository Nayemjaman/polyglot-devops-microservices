from math import ceil

from pydantic import BaseModel, Field


class Pagination(BaseModel):
    page: int
    page_size: int
    total_items: int
    total_pages: int


class PaginationParams(BaseModel):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)

    @property
    def offset(self) -> int:
        return (self.page - 1) * self.page_size

    def to_response(self, total_items: int) -> Pagination:
        return Pagination(
            page=self.page,
            page_size=self.page_size,
            total_items=total_items,
            total_pages=ceil(total_items / self.page_size) if total_items else 0,
        )
