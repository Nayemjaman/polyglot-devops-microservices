class ServiceError(Exception):
    status_code = 400

    def __init__(self, message: str, errors: dict[str, list[str]] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.errors = errors


class NotFoundError(ServiceError):
    status_code = 404


class ConflictError(ServiceError):
    status_code = 409


class ValidationServiceError(ServiceError):
    status_code = 400
