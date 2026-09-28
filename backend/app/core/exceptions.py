class AppError(Exception):
    """Base class for controlled errors that are safe to show to API clients."""

    status_code = 400
    error_code = "bad_request"

    def __init__(self, message: str, *, status_code: int | None = None, error_code: str | None = None):
        super().__init__(message)
        self.message = message
        if status_code is not None:
            self.status_code = status_code
        if error_code is not None:
            self.error_code = error_code


class UnauthorizedError(AppError):
    status_code = 401
    error_code = "unauthorized"


class ForbiddenError(AppError):
    status_code = 403
    error_code = "forbidden"


class NotFoundError(AppError):
    status_code = 404
    error_code = "not_found"


class ConflictError(AppError):
    status_code = 409
    error_code = "conflict"


class CircularDependencyError(ConflictError):
    error_code = "circular_dependency"


class FileValidationError(AppError):
    status_code = 400
    error_code = "invalid_file"


class UnsupportedFileTypeError(AppError):
    status_code = 415
    error_code = "unsupported_file_type"


class AIServiceError(AppError):
    status_code = 502
    error_code = "ai_service_error"
