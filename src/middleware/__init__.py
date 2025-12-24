"""LPxGP Middleware - Security and error handling."""

from src.middleware.csrf import (
    get_csrf_token,
    setup_csrf_protection,
)
from src.middleware.error_handler import (
    request_id_middleware,
    sanitize_error_message,
    setup_exception_handlers,
)
from src.middleware.rate_limit import (
    limiter,
    rate_limit_auth,
    rate_limit_data_import,
    rate_limit_lp_search,
    rate_limit_match_generation,
    rate_limit_pitch_generation,
    setup_rate_limiting,
)

__all__ = [
    # Error handling
    "setup_exception_handlers",
    "sanitize_error_message",
    "request_id_middleware",
    # CSRF
    "setup_csrf_protection",
    "get_csrf_token",
    # Rate limiting
    "setup_rate_limiting",
    "limiter",
    "rate_limit_auth",
    "rate_limit_match_generation",
    "rate_limit_pitch_generation",
    "rate_limit_lp_search",
    "rate_limit_data_import",
]
