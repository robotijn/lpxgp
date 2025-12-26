"""LPxGP FastAPI Application.

This module provides the main FastAPI application for the LPxGP platform,
an AI-powered tool helping General Partners (GPs) find and engage
Limited Partners (LPs) for fund investments.

Features:
    - Health and status endpoints for monitoring
    - Authentication with session-based login
    - CRUD operations for funds and LPs
    - AI-powered match generation and pitch creation
    - HTMX-based dynamic UI with Jinja2 templates

Example:
    Running the development server::

        uv run uvicorn src.main:app --reload

Attributes:
    app: The FastAPI application instance.
    templates: Jinja2Templates instance for rendering HTML.
    logger: Structured logger for this module.
"""

from __future__ import annotations

from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from pathlib import Path
from typing import Any
from uuid import UUID

import psycopg
from fastapi import FastAPI, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

from src import auth
from src.config import get_settings, validate_settings_on_startup
from src.logging_config import get_logger
from src.preferences import get_user_preferences
from src.routers import (
    admin_router,
    auth_router,
    crm_router,
    funds_router,
    gps_router,
    health_router,
    lp_portal_router,
    lps_router,
    matches_router,
    pages_router,
    pipeline_router,
    pitch_router,
    settings_api_router,
    shortlist_router,
)

# =============================================================================
# Helper Functions
# =============================================================================


def serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert a database row dict to JSON-serializable format.

    Converts UUID objects to strings and Decimal to float for JSON serialization.
    """
    from decimal import Decimal

    result: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, UUID):
            result[key] = str(value)
        elif isinstance(value, Decimal):
            result[key] = float(value)
        else:
            result[key] = value
    return result


class PipelineStageUpdateRequest(BaseModel):
    """Request body for updating pipeline stage."""

    stage: str = Field(
        ...,
        description="Pipeline stage",
        pattern="^(recommended|gp_interested|gp_pursuing|lp_reviewing|mutual_interest|in_diligence|gp_passed|lp_passed|invested)$",
    )
    notes: str | None = None


# Valid pipeline stages for validation (GP perspective)
VALID_PIPELINE_STAGES = [
    "recommended",
    "gp_interested",
    "gp_pursuing",
    "lp_reviewing",
    "mutual_interest",
    "in_diligence",
    "gp_passed",
    "lp_passed",
    "invested",
]

# Valid LP pipeline stages (LP perspective on funds)
VALID_LP_PIPELINE_STAGES = [
    "watching",
    "interested",
    "reviewing",
    "dd_in_progress",
    "passed",
]


class LPPipelineStageUpdateRequest(BaseModel):
    """Request body for updating LP pipeline stage."""

    stage: str = Field(
        ...,
        description="LP Pipeline stage",
        pattern="^(watching|interested|reviewing|dd_in_progress|passed)$",
    )
    notes: str | None = None


# =============================================================================
# Utility Functions
# =============================================================================


def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID.

    Used to validate user input before database queries to prevent
    crashes and potential injection attacks.

    Args:
        value: String to validate as UUID.

    Returns:
        True if the string is a valid UUID, False otherwise.

    Example:
        >>> is_valid_uuid("550e8400-e29b-41d4-a716-446655440000")
        True
        >>> is_valid_uuid("not-a-uuid")
        False
    """
    if not value:
        return False
    try:
        UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def get_db() -> psycopg.Connection[dict[str, Any]] | None:
    """Get database connection if configured.

    Creates a new psycopg connection with dict_row factory for easy
    data access. The caller is responsible for closing the connection.

    IMPORTANT: This function automatically selects the appropriate database:
    - In tests (pytest): Uses TEST_DATABASE_URL
    - In production: Uses DATABASE_URL
    - In development: Prefers TEST_DATABASE_URL if set

    Returns:
        psycopg Connection with dict_row factory if database is configured,
        None otherwise.

    Note:
        Always use with try/finally to ensure connection is closed::

            conn = get_db()
            if conn:
                try:
                    # ... use connection
                finally:
                    conn.close()
    """
    settings = get_settings()
    db_url = settings.active_database_url
    if db_url:
        return psycopg.connect(db_url, row_factory=dict_row)
    return None

# =============================================================================
# Application Setup
# =============================================================================

logger = get_logger(__name__)
"""Module-level logger with automatic redaction of sensitive fields."""

# Paths
BASE_DIR: Path = Path(__file__).parent
"""Base directory for the src package."""

TEMPLATES_DIR: Path = BASE_DIR / "templates"
"""Directory containing Jinja2 templates."""

STATIC_DIR: Path = BASE_DIR / "static"
"""Directory containing static files (images, etc.)."""


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    """Application lifespan handler for startup and shutdown events.

    Handles application lifecycle events:
    - Startup: Validates configuration, initializes resources
    - Shutdown: Cleans up resources

    Args:
        app: The FastAPI application instance.

    Yields:
        None during the application's active lifetime.

    Raises:
        Exception: If configuration validation fails on startup.
    """
    # Startup
    logger.info("Starting LPxGP application")
    try:
        validate_settings_on_startup()
        logger.info("Configuration validated")
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down LPxGP application")


# Create FastAPI app
app = FastAPI(
    title="LPxGP",
    description="AI-powered platform helping GPs find and engage LPs",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))

# Include routers
app.include_router(health_router)
app.include_router(auth_router)
app.include_router(pages_router)
app.include_router(admin_router)
app.include_router(settings_api_router)
app.include_router(shortlist_router)
app.include_router(gps_router)
app.include_router(funds_router)
app.include_router(lps_router)
app.include_router(matches_router)
app.include_router(pitch_router)
app.include_router(crm_router)
app.include_router(pipeline_router)
app.include_router(lp_portal_router)


# =============================================================================
# Health & Status Endpoints
# =============================================================================


@app.api_route("/health", methods=["GET", "HEAD"], response_class=JSONResponse)
async def health_check() -> dict[str, str]:
    """Health check endpoint for load balancers and monitoring.

    Returns basic application health status. Supports both GET and HEAD
    methods for efficient health checking by load balancers.

    Returns:
        JSON object with 'status' and 'version' fields.
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
    }


@app.get("/api/status", response_class=JSONResponse)
async def api_status() -> dict[str, Any]:
    """API status with non-sensitive configuration info.

    Returns current environment and feature flag status. Does not expose
    any sensitive configuration values like API keys.

    Returns:
        JSON object with status, environment, and feature flags.
    """
    settings = get_settings()
    return {
        "status": "ok",
        "environment": settings.environment,
        "features": {
            "semantic_search": settings.enable_semantic_search,
            "agent_matching": settings.enable_agent_matching,
        },
    }


# =============================================================================
# Page Routes
# =============================================================================


@app.get("/", response_class=HTMLResponse)
async def home(request: Request) -> HTMLResponse:
    """Render the home page.

    Args:
        request: FastAPI request object.

    Returns:
        Rendered home page HTML.
    """
    return templates.TemplateResponse(
        request,
        "pages/home.html",
        {"title": "LPxGP - GP-LP Intelligence Platform"},
    )


@app.get("/login", response_class=HTMLResponse, response_model=None)
async def login_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Render the login page.

    Redirects authenticated users to the dashboard.

    Args:
        request: FastAPI request object.

    Returns:
        Login page HTML or redirect to dashboard if already authenticated.
    """
    user = auth.get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        request,
        "pages/login.html",
        {"title": "Login - LPxGP"},
    )


@app.get("/register", response_class=HTMLResponse, response_model=None)
async def register_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Render the registration page.

    Redirects authenticated users to the dashboard.

    Args:
        request: FastAPI request object.

    Returns:
        Registration page HTML or redirect to dashboard if already authenticated.
    """
    user = auth.get_current_user(request)
    if user:
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        request,
        "pages/register.html",
        {"title": "Register - LPxGP"},
    )


@app.post("/api/auth/login", response_model=None)
async def api_login(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
) -> HTMLResponse | RedirectResponse | Response:
    """Handle login form submission via HTMX.

    Authenticates the user and either redirects to dashboard on success
    or returns an error partial for HTMX to display.

    Args:
        request: FastAPI request object.
        email: User's email address from form.
        password: User's password from form.

    Returns:
        Redirect to dashboard on success, or error HTML partial on failure.
    """
    user = auth.authenticate_user(email, password)

    if not user:
        # HTMX ignores non-2xx responses by default, so return 200 for HTMX
        # but 401 for regular requests (API clients, unit tests)
        is_htmx = request.headers.get("HX-Request") == "true"
        return templates.TemplateResponse(
            request,
            "partials/auth_error.html",
            {"error": "Invalid email or password"},
            status_code=200 if is_htmx else 401,
        )

    return auth.login_response(user, redirect_to="/dashboard", request=request)


@app.post("/api/auth/register", response_model=None)
async def api_register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    role: str = Form(default="gp"),
) -> HTMLResponse | RedirectResponse | Response:
    """Handle registration form submission via HTMX.

    Creates a new user account and logs them in on success.

    Args:
        request: FastAPI request object.
        email: User's email address from form.
        password: User's password from form.
        name: User's display name from form.
        role: User role ('gp', 'lp', or 'admin'). Defaults to 'gp'.

    Returns:
        Redirect to dashboard on success, or error HTML partial on failure.
    """
    try:
        # Validate and cast role to UserRole
        validated_role: auth.UserRole
        if role == "lp":
            validated_role = "lp"
        elif role == "admin":
            validated_role = "admin"
        else:
            validated_role = "gp"
        user = auth.create_user(email=email, password=password, name=name, role=validated_role)
        return auth.login_response(user, redirect_to="/dashboard", request=request)
    except ValueError as e:
        return templates.TemplateResponse(
            request,
            "partials/auth_error.html",
            {"error": str(e)},
            status_code=400,
        )


@app.get("/logout")
async def logout(request: Request) -> RedirectResponse:
    """Handle user logout.

    Clears the session and redirects to the home page.

    Args:
        request: FastAPI request object.

    Returns:
        Redirect to home page with cleared session cookie.
    """
    return auth.logout_response(request, redirect_to="/")


@app.get("/dashboard", response_class=HTMLResponse, response_model=None)
async def dashboard_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Render the user dashboard (protected route).

    Requires authentication. Shows summary statistics for funds, LPs,
    and matches.

    Args:
        request: FastAPI request object.

    Returns:
        Dashboard HTML or redirect to login if not authenticated.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Get stats for dashboard
    stats: dict[str, int] = {
        "total_funds": 0,
        "total_lps": 0,
        "total_matches": 0,
        "active_outreach": 0,
    }

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM funds")
                result = cur.fetchone()
                stats["total_funds"] = result["count"] if result else 0

                cur.execute("SELECT COUNT(*) FROM organizations WHERE is_lp = TRUE")
                result = cur.fetchone()
                stats["total_lps"] = result["count"] if result else 0

                cur.execute("SELECT COUNT(*) FROM fund_lp_matches")
                result = cur.fetchone()
                stats["total_matches"] = result["count"] if result else 0
        except Exception:
            pass
        finally:
            conn.close()

    return templates.TemplateResponse(
        request,
        "pages/dashboard.html",
        {
            "title": "Dashboard - LPxGP",
            "user": user,
            "stats": stats,
        },
    )


@app.get("/settings", response_class=HTMLResponse, response_model=None)
async def settings_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Render the user settings page (protected route).

    Requires authentication. Displays user profile info and
    notification preferences.

    Args:
        request: FastAPI request object.

    Returns:
        Settings page HTML or redirect to login if not authenticated.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    preferences = get_user_preferences(user["id"])

    return templates.TemplateResponse(
        request,
        "pages/settings.html",
        {
            "title": "Settings - LPxGP",
            "user": user,
            "preferences": preferences,
        },
    )
# -----------------------------------------------------------------------------
# Error Handlers
# -----------------------------------------------------------------------------

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 handler."""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=404,
            content={"error": "Not found", "path": request.url.path},
        )
    return templates.TemplateResponse(
        request,
        "pages/error.html",
        {"title": "Not Found", "error_code": 404, "error_message": "Page not found"},
        status_code=404,
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    """Custom 500 handler."""
    logger.error(f"Server error: {exc}", exc_info=True)
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"},
        )
    return templates.TemplateResponse(
        request,
        "pages/error.html",
        {"title": "Error", "error_code": 500, "error_message": "Something went wrong"},
        status_code=500,
    )
