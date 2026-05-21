from fastapi import HTTPException, status

from app.services.exceptions import NotFoundError, ServiceError, ValidationServiceError


def raise_service_error(exc: ServiceError) -> None:
    if isinstance(exc, ValidationServiceError):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"message": exc.message, "errors": exc.errors},
        ) from exc
    if isinstance(exc, NotFoundError):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail={"message": exc.message}) from exc
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail={"message": exc.message},
    ) from exc
