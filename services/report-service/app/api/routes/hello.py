from fastapi import APIRouter

from app.schemas.responses import ApiResponse

router = APIRouter(tags=["hello"])


@router.get("/hello", response_model=ApiResponse)
async def hello() -> ApiResponse:
    return ApiResponse(message="hello from report-service", data={"service": "report-service"})
