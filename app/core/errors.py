class AppError(Exception):
    """Base error for all application-specific errors."""


class AudioValidationError(AppError):
    """Raised when uploaded audio is invalid."""


class ModelServerError(AppError):
    """Raised when the LFM3 model server fails or is unreachable."""