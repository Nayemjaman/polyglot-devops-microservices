class ServiceError(Exception):
    def __init__(self, message: str, errors: dict[str, list[str]] | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.errors = errors


class NotFoundError(ServiceError):
    pass


class ValidationServiceError(ServiceError):
    pass
