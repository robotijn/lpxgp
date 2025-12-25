"""Structured logging configuration with sensitive field redaction.

This module provides centralized logging configuration for the LPxGP
application using structlog. It includes automatic redaction of sensitive
fields to prevent information leakage in logs.

Features:
    - Structured logging with JSON or console output
    - Automatic redaction of sensitive fields (passwords, API keys, tokens)
    - Partial masking of PII fields (email, phone)
    - Application context injection
    - Exception sanitization to remove sensitive data

Example:
    Basic usage::

        from src.logging_config import get_logger, configure_logging

        # Configure at startup
        configure_logging(log_level="INFO", json_logs=False)

        # Get a logger
        logger = get_logger(__name__)

        # Log with automatic redaction
        logger.info("User login", email="user@example.com", password="secret")
        # Output: ... email="***@example.com" password="[REDACTED]" ...

Note:
    Configure logging early in application startup before other modules
    are imported to ensure consistent log formatting.
"""

from __future__ import annotations

import logging
import sys
from collections.abc import MutableMapping
from typing import Any

import structlog
from structlog.typing import WrappedLogger

# =============================================================================
# Sensitive Field Patterns
# =============================================================================

REDACT_FIELDS: set[str] = {
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
"""Fields that should be completely redacted with [REDACTED]."""

MASK_FIELDS: set[str] = {
    "email",
    "phone",
    "ip_address",
}
"""Fields to partially mask, showing only last 4 characters."""

REDACTED: str = "[REDACTED]"
"""Replacement string for fully redacted fields."""

MASKED_PREFIX: str = "***"
"""Prefix for partially masked fields (e.g., ***@example.com)."""


# =============================================================================
# Redaction Processor
# =============================================================================


def redact_sensitive_fields(
    logger: WrappedLogger,
    method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """Redact sensitive fields from log events.

    This structlog processor recursively searches through the event dict
    and redacts any fields matching sensitive patterns. It handles nested
    dictionaries and lists.

    Args:
        logger: The logger instance (required by structlog processor interface).
        method_name: The log method name (required by structlog processor interface).
        event_dict: The event dictionary containing log data.

    Returns:
        Modified event dictionary with sensitive fields redacted.

    Example:
        >>> event = {"password": "secret123", "email": "user@example.com"}
        >>> redact_sensitive_fields(None, "", event)
        {'password': '[REDACTED]', 'email': '***@example.com'}
    """

    def redact_value(key: str, value: Any) -> Any:
        """Redact a single value based on its key.

        Args:
            key: The field name to check against redaction patterns.
            value: The value to potentially redact.

        Returns:
            Redacted value if key matches a sensitive pattern, otherwise original.
        """
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

    def redact_dict(d: dict[str, Any]) -> dict[str, Any]:
        """Recursively redact sensitive fields in a dictionary.

        Args:
            d: Dictionary to process.

        Returns:
            New dictionary with sensitive fields redacted.
        """
        result: dict[str, Any] = {}
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

    # Convert MutableMapping to dict for processing
    return redact_dict(dict(event_dict))


# =============================================================================
# Additional Processors
# =============================================================================


def add_app_context(
    logger: WrappedLogger,
    method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """Add application context to all log events.

    Injects the current environment (development/staging/production)
    into every log event for filtering and correlation.

    Args:
        logger: The logger instance (required by structlog processor interface).
        method_name: The log method name (required by structlog processor interface).
        event_dict: The event dictionary containing log data.

    Returns:
        Modified event dictionary with 'environment' field added.
    """
    from src.config import get_settings

    try:
        settings = get_settings()
        event_dict["environment"] = settings.environment
    except Exception:
        event_dict["environment"] = "unknown"

    return event_dict


def sanitize_exception(
    logger: WrappedLogger,
    method_name: str,
    event_dict: MutableMapping[str, Any],
) -> MutableMapping[str, Any]:
    """Sanitize exception information to remove sensitive data from stack traces.

    Checks exception text for sensitive patterns and replaces the entire
    exception with a generic message if any are found.

    Args:
        logger: The logger instance (required by structlog processor interface).
        method_name: The log method name (required by structlog processor interface).
        event_dict: The event dictionary containing log data.

    Returns:
        Modified event dictionary with sanitized exception info.

    Note:
        This is a security measure to prevent accidental logging of
        credentials that might appear in exception messages.
    """
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


# =============================================================================
# Configure Logging
# =============================================================================


def configure_logging(
    log_level: str = "INFO",
    json_logs: bool = False,
) -> None:
    """Configure structured logging for the application.

    Sets up structlog with appropriate processors for the environment.
    Should be called once at application startup, before any logging.

    Args:
        log_level: Logging level - one of 'DEBUG', 'INFO', 'WARNING', 'ERROR'.
            Defaults to 'INFO'.
        json_logs: If True, output JSON logs suitable for log aggregation
            (production). If False, use colored console output for
            development. Defaults to False.

    Example:
        >>> # In main.py startup
        >>> configure_logging(log_level="DEBUG", json_logs=False)

        >>> # In production
        >>> configure_logging(log_level="INFO", json_logs=True)

    Note:
        This also configures the standard library logging module and
        suppresses noisy third-party loggers (httpx, supabase).
    """
    # Determine renderer based on environment
    renderer: structlog.processors.JSONRenderer | structlog.dev.ConsoleRenderer
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

    Creates a structlog logger that automatically applies all configured
    processors including redaction, context injection, and formatting.

    Args:
        name: Logger name, typically ``__name__`` for module-level loggers.

    Returns:
        Configured structlog BoundLogger instance.

    Example:
        >>> from src.logging_config import get_logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Processing started", user_id="123")
        >>> logger.error("Operation failed", error="timeout")
    """
    return structlog.get_logger(name)
