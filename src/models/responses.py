"""Standard API response wrappers."""

from typing import Any
from uuid import UUID

from pydantic import Field

from src.models.base import BaseModel


class APIResponse[T](BaseModel):
    """Standard API response wrapper."""

    success: bool = True
    data: T | None = None
    message: str | None = None
    request_id: str | None = Field(default=None, description="Request ID for tracking")


class PaginatedResponse[T](BaseModel):
    """Paginated response wrapper."""

    success: bool = True
    data: list[T] = Field(default_factory=list)

    # Pagination info
    page: int = Field(ge=1)
    page_size: int = Field(ge=1, le=100)
    total_count: int = Field(ge=0)
    total_pages: int = Field(ge=0)

    # Navigation
    has_next: bool = False
    has_previous: bool = False


class ErrorResponse(BaseModel):
    """Standard error response."""

    success: bool = False
    error: str = Field(description="Error type/code")
    message: str = Field(description="Human-readable error message")
    details: dict[str, Any] | None = Field(
        default=None,
        description="Additional error details (validation errors, etc.)",
    )
    request_id: str | None = Field(default=None, description="Request ID for tracking")

    # DO NOT include in production responses:
    # - stack_trace
    # - internal_error
    # - database_error


class ValidationErrorDetail(BaseModel):
    """Validation error detail for a single field."""

    field: str = Field(description="Field name that failed validation")
    message: str = Field(description="Validation error message")
    value: Any | None = Field(default=None, description="Invalid value (if safe to show)")


class ValidationErrorResponse(BaseModel):
    """Response for validation errors (422)."""

    success: bool = False
    error: str = "validation_error"
    message: str = "Request validation failed"
    errors: list[ValidationErrorDetail] = Field(description="List of validation errors")
    request_id: str | None = None


class RateLimitResponse(BaseModel):
    """Response for rate limit exceeded (429)."""

    success: bool = False
    error: str = "rate_limit_exceeded"
    message: str = "Too many requests"
    retry_after_seconds: int = Field(description="Seconds to wait before retrying")
    limit: int = Field(description="Request limit")
    window_seconds: int = Field(description="Time window in seconds")


class AuthErrorResponse(BaseModel):
    """Response for authentication errors (401/403)."""

    success: bool = False
    error: str = Field(description="auth_required or forbidden")
    message: str


class NotFoundResponse(BaseModel):
    """Response for resource not found (404)."""

    success: bool = False
    error: str = "not_found"
    message: str = "Resource not found"
    resource_type: str | None = Field(default=None, description="Type of resource")
    resource_id: UUID | None = Field(default=None, description="ID of resource")


class HealthCheckResponse(BaseModel):
    """Health check response."""

    status: str = Field(description="ok, degraded, or unhealthy")
    version: str | None = None
    environment: str | None = None

    # Service checks (don't expose internal details)
    services: dict[str, str] = Field(
        default_factory=dict,
        description="Service status (ok/error only, no details)",
    )
