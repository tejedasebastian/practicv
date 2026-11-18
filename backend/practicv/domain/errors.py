class DomainError(Exception):
    """Base class for expected domain errors."""

    code = "domain_error"
    status_code = 400

    def __init__(self, message: str, details: dict | None = None) -> None:
        super().__init__(message)
        self.message = message
        self.details = details or {}


class NotFoundError(DomainError):
    code = "not_found"
    status_code = 404


class ConflictError(DomainError):
    code = "conflict"
    status_code = 409


class ValidationError(DomainError):
    code = "validation_error"
    status_code = 422


class MCPUnavailableError(DomainError):
    code = "mcp_unavailable"
    status_code = 503
