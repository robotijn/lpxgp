"""Structured logging configuration with sensitive field redaction.

Uses structlog for structured logging with automatic redaction of
sensitive fields to prevent information leakage in logs.
"""

import logging
import sys
from typing import Any

import structlog


# ---------------------------------------------------------------------------
# Sensitive Field Patterns
# ---------------------------------------------------------------------------

# Fields that should be completely redacted
REDACT_FIELDS = {
    "password",
    "secret",
    "token",
    "api_key",
    "apikey",
    "authorization",
    "auth_token",
    "access_token",
    "refresh_token",
    "credential",
    "private_key",
    "ssn",
    "social_security",
    "credit_card",
    "card_number",
    "cvv",
    "supabase_key",
    "supabase_service_role_key",
    "supabase_anon_key",
    "openrouter_api_key",
    "voyage_api_key",
    "langfuse_secret_key",
    "sentry_dsn",
}

# Fields to partially mask (show last 4 chars)
MASK_FIELDS = {
    "email",
    "phone",
    "ip_address",
}

REDACTED = "[REDACTED]"
MASKED_PREFIX = "***"


# ---------------------------------------------------------------------------
# Redaction Processor
# ---------------------------------------------------------------------------


def redact_sensitive_fields(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Redact sensitive fields from log events.

    This processor recursively searches through the event dict
    and redacts any fields matching sensitive patterns.
    """

    def redact_value(key: str, value: Any) -> Any:
        """Redact a single value based on its key."""
        key_lower = key.lower()

        # Check for exact match on redact fields
        if key_lower in REDACT_FIELDS:
            return REDACTED

        # Check for partial match (e.g., "user_password" contains "password")
        for pattern in REDACT_FIELDS:
            if pattern in key_lower:
                return REDACTED

        # Check for mask fields (partial redaction)
        if key_lower in MASK_FIELDS and isinstance(value, str) and len(value) > 4:
            return f"{MASKED_PREFIX}{value[-4:]}"

        return value

    def redact_dict(d: dict) -> dict:
        """Recursively redact sensitive fields in a dictionary."""
        result = {}
        for key, value in d.items():
            if isinstance(value, dict):
                result[key] = redact_dict(value)
            elif isinstance(value, list):
                result[key] = [
                    redact_dict(item) if isinstance(item, dict) else redact_value(key, item)
                    for item in value
                ]
            else:
                result[key] = redact_value(key, value)
        return result

    return redact_dict(event_dict)


# ---------------------------------------------------------------------------
# Additional Processors
# ---------------------------------------------------------------------------


def add_app_context(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Add application context to all log events."""
    from src.config import get_settings

    try:
        settings = get_settings()
        event_dict["environment"] = settings.environment
    except Exception:
        event_dict["environment"] = "unknown"

    return event_dict


def sanitize_exception(
    logger: logging.Logger,
    method_name: str,
    event_dict: dict[str, Any],
) -> dict[str, Any]:
    """Sanitize exception information to remove sensitive data from stack traces."""
    if "exception" in event_dict:
        exc_info = event_dict["exception"]
        if isinstance(exc_info, str):
            # Check for sensitive patterns in exception text
            for pattern in REDACT_FIELDS:
                if pattern.lower() in exc_info.lower():
                    event_dict["exception"] = (
                        "[Exception contained sensitive data - see internal logs]"
                    )
                    break
    return event_dict


# ---------------------------------------------------------------------------
# Configure Logging
# ---------------------------------------------------------------------------


def configure_logging(
    log_level: str = "INFO",
    json_logs: bool = False,
) -> None:
    """Configure structured logging for the application.

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        json_logs: If True, output JSON logs (for production). Otherwise, colored console output.
    """
    # Determine renderer based on environment
    if json_logs:
        renderer = structlog.processors.JSONRenderer()
    else:
        renderer = structlog.dev.ConsoleRenderer(colors=True)

    # Configure structlog
    structlog.configure(
        processors=[
            # Add timestamp
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="iso"),
            # Add caller info in debug mode
            structlog.processors.CallsiteParameterAdder(
                parameters=[
                    structlog.processors.CallsiteParameter.FILENAME,
                    structlog.processors.CallsiteParameter.LINENO,
                ]
            ),
            # Custom processors
            add_app_context,
            redact_sensitive_fields,
            sanitize_exception,
            # Stack info for exceptions
            structlog.processors.StackInfoRenderer(),
            structlog.processors.format_exc_info,
            # Prepare for final output
            structlog.processors.UnicodeDecoder(),
            renderer,
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Also configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, log_level.upper()),
    )

    # Set levels for noisy third-party loggers
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("supabase").setLevel(logging.WARNING)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """Get a configured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)


# ---------------------------------------------------------------------------
# Usage Example
# ---------------------------------------------------------------------------

# In your code:
#
#     from src.logging_config import get_logger
#
#     logger = get_logger(__name__)
#
#     # Sensitive fields are automatically redacted:
#     logger.info("User login attempt", email="user@example.com", password="secret123")
#     # Output: ... email="***@example.com" password="[REDACTED]" ...
#
#     logger.error("API call failed", api_key="sk-1234567890", error="timeout")
#     # Output: ... api_key="[REDACTED]" error="timeout" ...
