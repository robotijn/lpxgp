"""Error handling middleware - sanitize exceptions to prevent information leakage."""

import logging
import traceback
import uuid
from typing import Any

from fastapi import FastAPI, Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import ValidationError

logger = logging.getLogger(__name__)


# Patterns that indicate sensitive information
SENSITIVE_PATTERNS = [
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "auth",
    "credential",
    "private",
    "ssn",
    "credit_card",
    "supabase",
    "postgres",
    "database",
    "connection",
    "dsn",
    "host",
    "port",
]


def sanitize_error_message(message: str) -> str:
    """Remove sensitive information from error messages."""
    message_lower = message.lower()

    # Check for sensitive patterns
    for pattern in SENSITIVE_PATTERNS:
        if pattern in message_lower:
            return "An internal error occurred. Please try again."

    # Remove stack traces
    if "Traceback" in message or "File " in message:
        return "An internal error occurred. Please try again."

    # Remove SQL queries
    if "SELECT" in message.upper() or "INSERT" in message.upper():
        return "A database error occurred. Please try again."

    # Remove file paths
    if "/home/" in message or "/usr/" in message or "\\Users\\" in message:
        return "An internal error occurred. Please try again."

    return message


def create_error_response(
    error: str,
    message: str,
    status_code: int,
    request_id: str | None = None,
    details: dict[str, Any] | None = None,
) -> JSONResponse:
    """Create a standardized error response."""
    content = {
        "success": False,
        "error": error,
        "message": sanitize_error_message(message),
    }

    if request_id:
        content["request_id"] = request_id

    if details:
        # Sanitize details too
        sanitized_details = {}
        for key, value in details.items():
            if isinstance(value, str):
                sanitized_details[key] = sanitize_error_message(value)
            else:
                sanitized_details[key] = value
        content["details"] = sanitized_details

    return JSONResponse(status_code=status_code, content=content)


async def validation_exception_handler(
    request: Request,
    exc: RequestValidationError,
) -> JSONResponse:
    """Handle Pydantic validation errors."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Extract validation errors without exposing internal details
    errors = []
    for error in exc.errors():
        field = ".".join(str(loc) for loc in error.get("loc", []))
        message = error.get("msg", "Invalid value")

        # Don't include the actual invalid value for sensitive fields
        field_lower = field.lower()
        include_value = not any(p in field_lower for p in ["password", "token", "secret", "key"])

        error_detail = {
            "field": field,
            "message": message,
        }

        if include_value and "input" in error:
            # Truncate long values
            value = str(error["input"])
            if len(value) > 100:
                value = value[:100] + "..."
            error_detail["value"] = value

        errors.append(error_detail)

    # Log the full error for debugging (server-side only)
    logger.warning(
        "Validation error",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "errors": errors,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "success": False,
            "error": "validation_error",
            "message": "Request validation failed",
            "errors": errors,
            "request_id": request_id,
        },
    )


async def generic_exception_handler(
    request: Request,
    exc: Exception,
) -> JSONResponse:
    """Handle all other exceptions - sanitize to prevent info leakage."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Log the full exception server-side
    logger.error(
        "Unhandled exception",
        extra={
            "request_id": request_id,
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
            "exception_message": str(exc),
            "traceback": traceback.format_exc(),
        },
    )

    # Return sanitized error to client
    return create_error_response(
        error="internal_error",
        message="An unexpected error occurred. Please try again.",
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        request_id=request_id,
    )


async def http_exception_handler(
    request: Request,
    exc: Any,  # HTTPException
) -> JSONResponse:
    """Handle HTTP exceptions."""
    request_id = getattr(request.state, "request_id", str(uuid.uuid4()))

    # Map status codes to error types
    error_types = {
        400: "bad_request",
        401: "auth_required",
        403: "forbidden",
        404: "not_found",
        405: "method_not_allowed",
        409: "conflict",
        429: "rate_limit_exceeded",
        500: "internal_error",
        502: "bad_gateway",
        503: "service_unavailable",
    }

    error_type = error_types.get(exc.status_code, "error")

    return create_error_response(
        error=error_type,
        message=str(exc.detail) if hasattr(exc, "detail") else "An error occurred",
        status_code=exc.status_code,
        request_id=request_id,
    )


def setup_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers on the FastAPI app."""
    from fastapi.exceptions import HTTPException

    app.add_exception_handler(RequestValidationError, validation_exception_handler)
    app.add_exception_handler(ValidationError, validation_exception_handler)
    app.add_exception_handler(HTTPException, http_exception_handler)
    app.add_exception_handler(Exception, generic_exception_handler)


# Request ID middleware
async def request_id_middleware(request: Request, call_next):
    """Add request ID to each request for tracking."""
    request_id = request.headers.get("X-Request-ID", str(uuid.uuid4()))
    request.state.request_id = request_id

    response = await call_next(request)
    response.headers["X-Request-ID"] = request_id

    return response
