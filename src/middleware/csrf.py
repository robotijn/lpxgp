"""CSRF protection middleware using double-submit cookie pattern.

This implementation is designed to work well with HTMX which can send
CSRF tokens via headers on every request.
"""

import hashlib
import hmac
import secrets
from datetime import datetime, timedelta, timezone
from typing import Callable

from fastapi import FastAPI, HTTPException, Request, Response, status


# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

CSRF_COOKIE_NAME = "csrf_token"
CSRF_HEADER_NAME = "X-CSRF-Token"
CSRF_FORM_FIELD = "csrf_token"
CSRF_TOKEN_LENGTH = 32
CSRF_TOKEN_MAX_AGE = timedelta(hours=24)

# Methods that require CSRF protection
PROTECTED_METHODS = {"POST", "PUT", "PATCH", "DELETE"}

# Paths exempt from CSRF (webhooks, public APIs)
EXEMPT_PATHS = {
    "/api/webhooks/",
    "/health",
    "/ready",
}


# ---------------------------------------------------------------------------
# Token Generation & Validation
# ---------------------------------------------------------------------------


def generate_csrf_token() -> str:
    """Generate a cryptographically secure CSRF token."""
    return secrets.token_urlsafe(CSRF_TOKEN_LENGTH)


def validate_csrf_token(cookie_token: str | None, request_token: str | None) -> bool:
    """Validate CSRF token using constant-time comparison.

    Args:
        cookie_token: Token from the cookie
        request_token: Token from header or form body

    Returns:
        True if tokens match, False otherwise
    """
    if not cookie_token or not request_token:
        return False

    # Use constant-time comparison to prevent timing attacks
    return hmac.compare_digest(cookie_token, request_token)


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------


async def csrf_middleware(request: Request, call_next: Callable) -> Response:
    """CSRF protection middleware.

    - Sets CSRF cookie on every response if not present
    - Validates CSRF token on protected methods (POST, PUT, PATCH, DELETE)
    - Skips validation for exempt paths
    """
    # Check if path is exempt
    path = request.url.path
    if any(path.startswith(exempt) for exempt in EXEMPT_PATHS):
        return await call_next(request)

    # Get existing CSRF token from cookie
    cookie_token = request.cookies.get(CSRF_COOKIE_NAME)

    # For protected methods, validate the token
    if request.method in PROTECTED_METHODS:
        # Get token from header (preferred, works with HTMX)
        request_token = request.headers.get(CSRF_HEADER_NAME)

        # Fall back to form field if header not present
        if not request_token and request.method == "POST":
            # Try to get from form data (for traditional form submissions)
            content_type = request.headers.get("content-type", "")
            if "application/x-www-form-urlencoded" in content_type:
                try:
                    form = await request.form()
                    request_token = form.get(CSRF_FORM_FIELD)
                except Exception:
                    pass

        # Validate token
        if not validate_csrf_token(cookie_token, request_token):
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="CSRF validation failed",
            )

    # Process request
    response = await call_next(request)

    # Set CSRF cookie if not present or refresh it
    if not cookie_token:
        new_token = generate_csrf_token()
        response.set_cookie(
            key=CSRF_COOKIE_NAME,
            value=new_token,
            max_age=int(CSRF_TOKEN_MAX_AGE.total_seconds()),
            httponly=False,  # Must be readable by JavaScript/HTMX
            samesite="strict",
            secure=True,  # Only send over HTTPS
        )

    return response


# ---------------------------------------------------------------------------
# Template Helper
# ---------------------------------------------------------------------------


def get_csrf_token(request: Request) -> str:
    """Get CSRF token for use in templates.

    Usage in Jinja2:
        <input type="hidden" name="csrf_token" value="{{ csrf_token }}">

    Or in HTMX:
        <div hx-headers='{"X-CSRF-Token": "{{ csrf_token }}"}'>
    """
    token = request.cookies.get(CSRF_COOKIE_NAME)
    if not token:
        # Generate a new token if none exists
        token = generate_csrf_token()
    return token


# ---------------------------------------------------------------------------
# Setup Function
# ---------------------------------------------------------------------------


def setup_csrf_protection(app: FastAPI) -> None:
    """Configure CSRF protection on the FastAPI application.

    Also adds the csrf_token helper to Jinja2 context.
    """
    from starlette.middleware.base import BaseHTTPMiddleware

    app.add_middleware(BaseHTTPMiddleware, dispatch=csrf_middleware)

    # Note: You should also add get_csrf_token to your Jinja2 template globals
    # in your template configuration.
