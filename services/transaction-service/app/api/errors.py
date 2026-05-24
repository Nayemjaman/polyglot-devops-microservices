from fastapi import HTTPException

from app.services.exceptions import ServiceError


def raise_service_error(exc: ServiceError) -> None:
    raise HTTPException(
        status_code=exc.status_code, detail={"message": exc.message, "errors": exc.errors}
    )
