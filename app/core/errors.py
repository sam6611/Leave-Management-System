class AppError(Exception):
    def __init__(self, code: str, message: str, status_code: int = 400, details: dict | None = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.status_code = status_code
        self.details = details


class NotFoundError(AppError):
    def __init__(self, message: str = "Resource not found"):
        super().__init__(code="not_found", message=message, status_code=404)


class UnauthorizedError(AppError):
    def __init__(self, message: str = "Unauthorized"):
        super().__init__(code="unauthorized", message=message, status_code=401)


class ForbiddenError(AppError):
    def __init__(self, message: str = "Forbidden"):
        super().__init__(code="forbidden", message=message, status_code=403)


class ConflictError(AppError):
    def __init__(self, message: str = "Conflict"):
        super().__init__(code="conflict", message=message, status_code=409)
