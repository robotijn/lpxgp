"""Rate limiting middleware using slowapi.

Configurable rate limits per endpoint with org-scoped and user-scoped options.
"""

from typing import Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from slowapi import Limiter
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address

from src.models.responses import RateLimitResponse

# ---------------------------------------------------------------------------
# Key Functions (for rate limit scoping)
# ---------------------------------------------------------------------------


def get_user_id(request: Request) -> str:
    """Get user ID for per-user rate limiting.

    Falls back to IP address for unauthenticated requests.
    """
    # Try to get user from request state (set by auth middleware)
    user = getattr(request.state, "user", None)
    if user and hasattr(user, "id"):
        return str(user.id)

    # Fall back to IP for unauthenticated requests
    return get_remote_address(request)


def get_org_id(request: Request) -> str:
    """Get org ID for per-organization rate limiting.

    Falls back to user ID, then IP address.
    """
    # Try to get org from request state
    org_id = getattr(request.state, "org_id", None)
    if org_id:
        return str(org_id)

    # Fall back to user-scoped
    return get_user_id(request)


# ---------------------------------------------------------------------------
# Limiter Instance
# ---------------------------------------------------------------------------

# Create limiter with IP as default key
limiter = Limiter(key_func=get_remote_address)


# ---------------------------------------------------------------------------
# Rate Limit Decorators
# ---------------------------------------------------------------------------

# These are the configured rate limits from the security plan:
# | Endpoint              | Limit     | Scope   |
# |-----------------------|-----------|---------|
# | POST /matches/generate| 10/min    | per org |
# | POST /pitches         | 20/hour   | per user|
# | GET /lp-search        | 100/min   | per user|
# | POST /data-imports    | 5/hour    | per org |
# | Default               | 100/min   | per user|


def rate_limit_match_generation() -> Callable:
    """Rate limit for match generation: 10/minute per org."""
    return limiter.limit("10/minute", key_func=get_org_id)


def rate_limit_pitch_generation() -> Callable:
    """Rate limit for pitch generation: 20/hour per user."""
    return limiter.limit("20/hour", key_func=get_user_id)


def rate_limit_lp_search() -> Callable:
    """Rate limit for LP search: 100/minute per user."""
    return limiter.limit("100/minute", key_func=get_user_id)


def rate_limit_data_import() -> Callable:
    """Rate limit for data imports: 5/hour per org."""
    return limiter.limit("5/hour", key_func=get_org_id)


def rate_limit_auth() -> Callable:
    """Rate limit for auth endpoints: 5/minute per IP (prevent brute force)."""
    return limiter.limit("5/minute", key_func=get_remote_address)


# ---------------------------------------------------------------------------
# Custom Rate Limit Exceeded Handler
# ---------------------------------------------------------------------------


async def rate_limit_handler(request: Request, exc: Exception) -> JSONResponse:
    """Custom handler that returns structured JSON response.

    Args:
        request: The incoming request.
        exc: The RateLimitExceeded exception (typed as Exception for FastAPI compatibility).

    Returns:
        JSON response with rate limit error details.
    """
    # Cast to RateLimitExceeded for type safety
    rate_exc = exc if isinstance(exc, RateLimitExceeded) else None
    _ = str(rate_exc.detail) if rate_exc else ""

    # Extract retry-after from headers if available
    retry_after = 60  # Default to 60 seconds

    response = RateLimitResponse(
        message="Rate limit exceeded. Please try again later.",
        retry_after_seconds=retry_after,
        limit=10,  # Will be overridden per endpoint
        window_seconds=60,
    )

    return JSONResponse(
        status_code=429,
        content=response.model_dump(),
        headers={"Retry-After": str(retry_after)},
    )


# ---------------------------------------------------------------------------
# Setup Function
# ---------------------------------------------------------------------------


def setup_rate_limiting(app: FastAPI) -> None:
    """Configure rate limiting on the FastAPI application."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, rate_limit_handler)
