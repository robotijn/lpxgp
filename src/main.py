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

import json
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from datetime import UTC
from pathlib import Path
from typing import Any, cast
from uuid import UUID

import httpx
import psycopg
from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, Response
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from psycopg.rows import dict_row
from pydantic import BaseModel, Field

from src import auth
from src.config import get_settings, validate_settings_on_startup
from src.logging_config import get_logger
from src.search import (
    build_gp_search_sql,
    build_lp_search_sql,
    is_natural_language_query,
    parse_gp_search_query,
    parse_lp_search_query,
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


# =============================================================================
# User Preferences Data Model
# =============================================================================


class UserPreferences(BaseModel):
    """User notification and display preferences.

    Attributes:
        email_new_matches: Email about new LP matches.
        email_weekly_summary: Weekly summary of fund activity.
        email_marketing: Marketing and product updates.
    """

    email_new_matches: bool = True
    email_weekly_summary: bool = True
    email_marketing: bool = False


# In-memory preferences storage: user_id -> UserPreferences
_user_preferences: dict[str, UserPreferences] = {}


def get_user_preferences(user_id: str) -> UserPreferences:
    """Get preferences for a user, creating defaults if needed.

    Args:
        user_id: The user's unique identifier.

    Returns:
        UserPreferences object with current settings.
    """
    if user_id not in _user_preferences:
        _user_preferences[user_id] = UserPreferences()
    return _user_preferences[user_id]


def update_user_preferences(
    user_id: str, preferences: UserPreferences
) -> UserPreferences:
    """Update a user's preferences.

    Args:
        user_id: The user's unique identifier.
        preferences: The new preferences to set.

    Returns:
        Updated UserPreferences object.
    """
    _user_preferences[user_id] = preferences
    return preferences


# =============================================================================
# Shortlist Data Model
# =============================================================================


class ShortlistItem(BaseModel):
    """Represents an LP saved to a user's shortlist.

    Attributes:
        lp_id: The unique identifier of the LP organization.
        fund_id: Optional fund context for this shortlist entry.
        notes: User notes about why this LP was shortlisted.
        added_at: ISO timestamp when the LP was added.
        priority: Priority level (1=high, 2=medium, 3=low).
    """

    lp_id: str
    fund_id: str | None = None
    notes: str = ""
    added_at: str = Field(default_factory=lambda: "")
    priority: int = Field(default=2, ge=1, le=3)


class ShortlistAddRequest(BaseModel):
    """Request body for adding an LP to shortlist."""

    lp_id: str
    fund_id: str | None = None
    notes: str = ""
    priority: int = Field(default=2, ge=1, le=3)


class ShortlistUpdateRequest(BaseModel):
    """Request body for updating a shortlist entry."""

    notes: str | None = None
    priority: int | None = Field(default=None, ge=1, le=3)


class PipelineStageUpdateRequest(BaseModel):
    """Request body for updating pipeline stage."""

    stage: str = Field(
        ...,
        description="Pipeline stage",
        pattern="^(recommended|gp_interested|gp_pursuing|lp_reviewing|mutual_interest|in_diligence|gp_passed|lp_passed|invested)$",
    )
    notes: str | None = None


# Valid pipeline stages for validation
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


# In-memory shortlist storage: user_id -> list of ShortlistItems
_shortlists: dict[str, list[ShortlistItem]] = {}

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


@app.get("/matches", response_class=HTMLResponse, response_model=None)
async def matches_page(
    request: Request,
    fund_id: str | None = Query(None),
) -> HTMLResponse | RedirectResponse:
    """Render the matches page showing AI-recommended LP matches.

    Requires authentication.

    Displays scored LP-Fund matches with filtering by fund and
    statistics including high score count, average score, and
    pipeline status.

    Args:
        request: FastAPI request object.
        fund_id: Optional UUID of fund to filter matches by.

    Returns:
        Matches page HTML with match data and statistics.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Validate fund_id if provided - ignore invalid UUIDs to prevent crashes
    validated_fund_id: str | None = None
    if fund_id and is_valid_uuid(fund_id):
        validated_fund_id = fund_id

    # Default empty state
    empty_response: dict[str, Any] = {
        "title": "Matches - LPxGP",
        "user": user,
        "matches": [],
        "funds": [],
        "high_score_count": 0,
        "avg_score": 0,
        "in_pipeline": 0,
        "selected_fund": None,
    }

    conn = get_db()
    if not conn:
        return templates.TemplateResponse(request, "pages/matches.html", empty_response)

    try:
        with conn.cursor() as cur:
            # Fetch funds for the selector
            cur.execute("SELECT id, name, status FROM funds ORDER BY name")
            funds = cur.fetchall()

            # Fetch matches with all related data in one efficient query
            # Build query conditionally to avoid psycopg NULL type inference issues
            base_query = """
                SELECT
                    m.id, m.fund_id, m.lp_org_id, m.score,
                    m.score_breakdown, m.explanation, m.talking_points, m.concerns,
                    o.name as lp_name, o.hq_city as lp_city, o.hq_country as lp_country,
                    lp.lp_type, lp.total_aum_bn,
                    f.name as fund_name,
                    s.pipeline_stage
                FROM fund_lp_matches m
                JOIN organizations o ON o.id = m.lp_org_id
                LEFT JOIN lp_profiles lp ON lp.org_id = m.lp_org_id
                JOIN funds f ON f.id = m.fund_id
                LEFT JOIN fund_lp_status s ON s.fund_id = m.fund_id AND s.lp_org_id = m.lp_org_id
            """
            if validated_fund_id:
                cur.execute(
                    base_query + " WHERE m.fund_id = %s ORDER BY m.score DESC",
                    (validated_fund_id,)
                )
            else:
                cur.execute(base_query + " ORDER BY m.score DESC")
            matches = cur.fetchall()

        # Calculate stats
        scores = [m["score"] for m in matches if m["score"] is not None]
        high_score_count = sum(1 for s in scores if s >= 90)
        avg_score = sum(scores) / len(scores) if scores else 0
        in_pipeline = sum(1 for m in matches if m.get("pipeline_stage"))

        return templates.TemplateResponse(
            request,
            "pages/matches.html",
            {
                "title": "Matches - LPxGP",
                "matches": matches,
                "funds": funds,
                "high_score_count": high_score_count,
                "avg_score": avg_score,
                "in_pipeline": in_pipeline,
                "selected_fund": validated_fund_id,
            },
        )
    finally:
        conn.close()


@app.get("/funds", response_class=HTMLResponse, response_model=None)
async def funds_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Funds page listing GP fund profiles.

    Requires authentication.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    empty_response = {
        "title": "Funds - LPxGP",
        "user": user,
        "funds": [],
        "gp_orgs": [],
        "total_target": 0,
        "raising_count": 0,
    }

    conn = get_db()
    if not conn:
        return templates.TemplateResponse(request, "pages/funds.html", empty_response)

    try:
        with conn.cursor() as cur:
            # Get funds
            cur.execute("""
                SELECT
                    f.id, f.name, f.status, f.vintage_year,
                    f.target_size_mm, f.current_size_mm,
                    f.strategy, f.sub_strategy,
                    f.geographic_focus, f.sector_focus,
                    o.name as gp_name,
                    (SELECT COUNT(*) FROM fund_lp_matches m WHERE m.fund_id = f.id) as match_count
                FROM funds f
                JOIN organizations o ON o.id = f.org_id
                ORDER BY f.created_at DESC
            """)
            funds = cur.fetchall()

            # Get GP organizations for the create form
            cur.execute("""
                SELECT id, name FROM organizations
                WHERE is_gp = TRUE
                ORDER BY name
            """)
            gp_orgs = cur.fetchall()

        # Calculate stats
        total_target = sum(f["target_size_mm"] or 0 for f in funds)
        raising_count = sum(1 for f in funds if f["status"] == "raising")

        return templates.TemplateResponse(
            request,
            "pages/funds.html",
            {
                "title": "Funds - LPxGP",
                "funds": funds,
                "gp_orgs": gp_orgs,
                "total_target": total_target,
                "raising_count": raising_count,
            },
        )
    finally:
        conn.close()


@app.get("/lps", response_class=HTMLResponse, response_model=None)
async def lps_page(
    request: Request,
    search: str | None = Query(None),
    lp_type: str | None = Query(None),
) -> HTMLResponse | RedirectResponse:
    """LPs page for browsing and searching LP profiles.

    Requires authentication.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    empty_response = {
        "title": "LPs - LPxGP",
        "user": user,
        "lps": [],
        "total_aum": 0,
        "search": search or "",
        "lp_type": lp_type or "",
        "lp_types": [],
    }

    conn = get_db()
    if not conn:
        return templates.TemplateResponse(request, "pages/lps.html", empty_response)

    try:
        with conn.cursor() as cur:
            # Get distinct LP types for filter dropdown
            cur.execute("""
                SELECT DISTINCT lp_type FROM lp_profiles
                WHERE lp_type IS NOT NULL
                ORDER BY lp_type
            """)
            lp_types = [row["lp_type"] for row in cur.fetchall()]

            # Build query with optional filters
            base_query = """
                SELECT
                    o.id, o.name, o.hq_city, o.hq_country, o.website,
                    lp.lp_type, lp.total_aum_bn, lp.pe_allocation_pct,
                    lp.check_size_min_mm, lp.check_size_max_mm,
                    lp.geographic_preferences, lp.strategies
                FROM organizations o
                JOIN lp_profiles lp ON lp.org_id = o.id
                WHERE {where_clause}
                ORDER BY lp.total_aum_bn DESC NULLS LAST
                LIMIT 100
            """

            # Check if search is natural language (AI parsing) or simple text
            parsed_filters: dict[str, Any] = {}
            if search and is_natural_language_query(search):
                # Use AI to parse the query
                parsed_filters = await parse_lp_search_query(search)
                # Add lp_type from dropdown if specified
                if lp_type:
                    parsed_filters["lp_type"] = lp_type
                where_clause, params = build_lp_search_sql(parsed_filters)
            else:
                # Simple text search
                conditions = ["o.is_lp = TRUE"]
                simple_params: list[Any] = []
                if search:
                    conditions.append("(o.name ILIKE %s OR o.hq_city ILIKE %s)")
                    simple_params.extend([f"%{search}%", f"%{search}%"])
                if lp_type:
                    conditions.append("lp.lp_type = %s")
                    simple_params.append(lp_type)
                where_clause = " AND ".join(conditions)
                params = simple_params

            query = base_query.format(where_clause=where_clause)
            cur.execute(query, params)
            lps = cur.fetchall()

        # Calculate stats
        total_aum = sum(lp["total_aum_bn"] or 0 for lp in lps)

        return templates.TemplateResponse(
            request,
            "pages/lps.html",
            {
                "title": "LPs - LPxGP",
                "user": user,
                "lps": lps,
                "total_aum": total_aum,
                "search": search or "",
                "lp_type": lp_type or "",
                "lp_types": lp_types,
                "parsed_filters": parsed_filters,  # Show what AI extracted
            },
        )
    finally:
        conn.close()


# =============================================================================
# REST API V1: LP Search
# M1 Requirement: GET /api/v1/lps with filters
# =============================================================================


@app.get("/api/v1/lps", response_class=JSONResponse)
async def api_v1_lps(
    request: Request,
    search: str | None = Query(None),
    lp_type: str | None = Query(None),
    aum_min: float | None = Query(None, description="Minimum AUM in billions"),
    aum_max: float | None = Query(None, description="Maximum AUM in billions"),
    location: str | None = Query(None),
    strategy: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> JSONResponse:
    """REST API endpoint for LP search.

    Returns JSON for programmatic access.
    Supports filtering by type, AUM, location, strategy.
    Supports pagination.

    Args:
        search: Text search or natural language query
        lp_type: Filter by LP type (pension, endowment, etc.)
        aum_min: Minimum AUM in billions
        aum_max: Maximum AUM in billions
        location: Filter by city or country
        strategy: Filter by investment strategy
        page: Page number (1-indexed)
        per_page: Results per page (max 100)

    Returns:
        JSON with data, total, page, per_page fields
    """
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required", "code": "UNAUTHORIZED"},
        )

    # Validate page number
    if page < 1:
        page = 1

    conn = get_db()
    if not conn:
        return JSONResponse(
            content={
                "data": [],
                "total": 0,
                "page": page,
                "per_page": per_page,
            }
        )

    try:
        with conn.cursor() as cur:
            # Build filters
            conditions = ["o.is_lp = TRUE"]
            params: list[Any] = []

            # Text search
            if search:
                conditions.append("(o.name ILIKE %s OR o.hq_city ILIKE %s)")
                params.extend([f"%{search}%", f"%{search}%"])

            # LP type filter
            if lp_type:
                conditions.append("lp.lp_type = %s")
                params.append(lp_type)

            # AUM filters
            if aum_min is not None:
                conditions.append("lp.total_aum_bn >= %s")
                params.append(aum_min)
            if aum_max is not None:
                conditions.append("lp.total_aum_bn <= %s")
                params.append(aum_max)

            # Location filter
            if location:
                conditions.append("(o.hq_city ILIKE %s OR o.hq_country ILIKE %s)")
                params.extend([f"%{location}%", f"%{location}%"])

            # Strategy filter
            if strategy:
                conditions.append("%s = ANY(lp.strategies)")
                params.append(strategy)

            where_clause = " AND ".join(conditions)

            # Count total
            count_query = f"""
                SELECT COUNT(*) as total
                FROM organizations o
                JOIN lp_profiles lp ON lp.org_id = o.id
                WHERE {where_clause}
            """
            cur.execute(count_query, params)
            count_row = cur.fetchone()
            total = count_row["total"] if count_row else 0

            # Fetch paginated results
            offset = (page - 1) * per_page
            data_query = f"""
                SELECT
                    o.id, o.name, o.hq_city, o.hq_country, o.website,
                    lp.lp_type, lp.total_aum_bn, lp.pe_allocation_pct,
                    lp.check_size_min_mm, lp.check_size_max_mm,
                    lp.geographic_preferences, lp.strategies
                FROM organizations o
                JOIN lp_profiles lp ON lp.org_id = o.id
                WHERE {where_clause}
                ORDER BY lp.total_aum_bn DESC NULLS LAST
                LIMIT %s OFFSET %s
            """
            cur.execute(data_query, [*params, per_page, offset])
            rows = cur.fetchall()

            # Convert to list of dicts
            data = [serialize_row(dict(row)) for row in rows]

            return JSONResponse(
                content={
                    "data": data,
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                }
            )
    except Exception as e:
        logger.error(f"API v1 LP search error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "code": "SERVER_ERROR"},
        )
    finally:
        conn.close()


# =============================================================================
# REST API V1: GP Search
# =============================================================================


@app.get("/api/v1/gps", response_class=JSONResponse)
async def api_v1_gps(
    request: Request,
    search: str | None = Query(None),
    strategy: str | None = Query(None),
    location: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> JSONResponse:
    """REST API endpoint for GP search.

    Returns JSON for programmatic access.
    Supports filtering by strategy, location.
    Supports pagination.
    """
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required", "code": "UNAUTHORIZED"},
        )

    if page < 1:
        page = 1

    conn = get_db()
    if not conn:
        return JSONResponse(
            content={
                "data": [],
                "total": 0,
                "page": page,
                "per_page": per_page,
            }
        )

    try:
        with conn.cursor() as cur:
            conditions = ["o.is_gp = TRUE"]
            params: list[Any] = []

            if search:
                conditions.append("(o.name ILIKE %s OR o.hq_city ILIKE %s)")
                params.extend([f"%{search}%", f"%{search}%"])

            if strategy:
                conditions.append("gp.investment_philosophy ILIKE %s")
                params.append(f"%{strategy}%")

            if location:
                conditions.append("(o.hq_city ILIKE %s OR o.hq_country ILIKE %s)")
                params.extend([f"%{location}%", f"%{location}%"])

            where_clause = " AND ".join(conditions)

            # Count total
            count_query = f"""
                SELECT COUNT(*) as total
                FROM organizations o
                JOIN gp_profiles gp ON gp.org_id = o.id
                WHERE {where_clause}
            """
            cur.execute(count_query, params)
            count_row = cur.fetchone()
            total = count_row["total"] if count_row else 0

            # Fetch paginated results
            offset = (page - 1) * per_page
            data_query = f"""
                SELECT
                    o.id, o.name, o.hq_city, o.hq_country, o.website,
                    gp.investment_philosophy, gp.team_size, gp.years_investing,
                    (SELECT COUNT(*) FROM funds f WHERE f.org_id = o.id) as fund_count
                FROM organizations o
                JOIN gp_profiles gp ON gp.org_id = o.id
                WHERE {where_clause}
                ORDER BY o.name
                LIMIT %s OFFSET %s
            """
            cur.execute(data_query, [*params, per_page, offset])
            rows = cur.fetchall()

            data = [serialize_row(dict(row)) for row in rows]

            return JSONResponse(
                content={
                    "data": data,
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                }
            )
    except Exception as e:
        logger.error(f"API v1 GP search error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "code": "SERVER_ERROR"},
        )
    finally:
        conn.close()


# =============================================================================
# REST API V1: Fund Search
# =============================================================================


@app.get("/api/v1/funds", response_class=JSONResponse)
async def api_v1_funds(
    request: Request,
    search: str | None = Query(None),
    strategy: str | None = Query(None),
    status: str | None = Query(None),
    vintage_year: int | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> JSONResponse:
    """REST API endpoint for Fund search.

    Returns JSON for programmatic access.
    Supports filtering by strategy, status, vintage_year.
    Supports pagination.
    """
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required", "code": "UNAUTHORIZED"},
        )

    if page < 1:
        page = 1

    conn = get_db()
    if not conn:
        return JSONResponse(
            content={
                "data": [],
                "total": 0,
                "page": page,
                "per_page": per_page,
            }
        )

    try:
        with conn.cursor() as cur:
            conditions = ["1=1"]
            params: list[Any] = []

            if search:
                conditions.append("(f.name ILIKE %s OR o.name ILIKE %s)")
                params.extend([f"%{search}%", f"%{search}%"])

            if strategy:
                conditions.append("f.strategy = %s")
                params.append(strategy)

            if status:
                conditions.append("f.status = %s")
                params.append(status)

            if vintage_year:
                conditions.append("f.vintage_year = %s")
                params.append(vintage_year)

            where_clause = " AND ".join(conditions)

            # Count total
            count_query = f"""
                SELECT COUNT(*) as total
                FROM funds f
                JOIN organizations o ON o.id = f.org_id
                WHERE {where_clause}
            """
            cur.execute(count_query, params)
            count_row = cur.fetchone()
            total = count_row["total"] if count_row else 0

            # Fetch paginated results
            offset = (page - 1) * per_page
            data_query = f"""
                SELECT
                    f.id, f.name, f.strategy, f.status, f.vintage_year,
                    f.target_size_mm, f.hard_cap_mm, f.check_size_min_mm,
                    o.id as org_id, o.name as org_name
                FROM funds f
                JOIN organizations o ON o.id = f.org_id
                WHERE {where_clause}
                ORDER BY f.vintage_year DESC NULLS LAST, f.name
                LIMIT %s OFFSET %s
            """
            cur.execute(data_query, [*params, per_page, offset])
            rows = cur.fetchall()

            data = [serialize_row(dict(row)) for row in rows]

            return JSONResponse(
                content={
                    "data": data,
                    "total": total,
                    "page": page,
                    "per_page": per_page,
                }
            )
    except Exception as e:
        logger.error(f"API v1 Fund search error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "code": "SERVER_ERROR"},
        )
    finally:
        conn.close()


@app.get("/gps", response_class=HTMLResponse, response_model=None)
async def gps_page(
    request: Request,
    search: str | None = Query(None),
    strategy: str | None = Query(None),
) -> HTMLResponse | RedirectResponse:
    """GPs page for browsing and searching GP profiles.

    Requires authentication. Supports AI-powered natural language search.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    empty_response = {
        "title": "GPs - LPxGP",
        "user": user,
        "gps": [],
        "total_funds": 0,
        "search": search or "",
        "strategy": strategy or "",
        "strategies": [],
    }

    conn = get_db()
    if not conn:
        return templates.TemplateResponse(request, "pages/gps.html", empty_response)

    try:
        with conn.cursor() as cur:
            # Get distinct strategies from investment_philosophy for filter dropdown
            cur.execute("""
                SELECT DISTINCT
                    CASE
                        WHEN investment_philosophy ILIKE '%%buyout%%' THEN 'buyout'
                        WHEN investment_philosophy ILIKE '%%growth%%' THEN 'growth'
                        WHEN investment_philosophy ILIKE '%%venture%%' THEN 'venture'
                        WHEN investment_philosophy ILIKE '%%real estate%%' THEN 'real_estate'
                        WHEN investment_philosophy ILIKE '%%infrastructure%%' THEN 'infrastructure'
                        WHEN investment_philosophy ILIKE '%%credit%%' THEN 'credit'
                        WHEN investment_philosophy ILIKE '%%secondaries%%' THEN 'secondaries'
                        ELSE NULL
                    END as strategy
                FROM gp_profiles
                WHERE investment_philosophy IS NOT NULL
            """)
            strategies = [row["strategy"] for row in cur.fetchall() if row["strategy"]]

            # Build query with optional filters
            base_query = """
                SELECT
                    o.id, o.name, o.hq_city, o.hq_country, o.website,
                    gp.investment_philosophy, gp.team_size, gp.years_investing,
                    gp.spun_out_from, gp.notable_exits,
                    (SELECT COUNT(*) FROM funds f WHERE f.org_id = o.id) as fund_count,
                    CASE
                        WHEN gp.investment_philosophy ILIKE '%%buyout%%' THEN 'buyout'
                        WHEN gp.investment_philosophy ILIKE '%%growth%%' THEN 'growth'
                        WHEN gp.investment_philosophy ILIKE '%%venture%%' THEN 'venture'
                        WHEN gp.investment_philosophy ILIKE '%%real estate%%' THEN 'real_estate'
                        WHEN gp.investment_philosophy ILIKE '%%infrastructure%%' THEN 'infrastructure'
                        WHEN gp.investment_philosophy ILIKE '%%credit%%' THEN 'credit'
                        WHEN gp.investment_philosophy ILIKE '%%secondaries%%' THEN 'secondaries'
                        ELSE NULL
                    END as strategy
                FROM organizations o
                JOIN gp_profiles gp ON gp.org_id = o.id
                WHERE {where_clause}
                ORDER BY gp.years_investing DESC NULLS LAST, o.name
                LIMIT 100
            """

            # Check if search is natural language (AI parsing) or simple text
            parsed_filters: dict[str, Any] = {}
            if search and is_natural_language_query(search):
                # Use AI to parse the query
                parsed_filters = await parse_gp_search_query(search)
                # Add strategy from dropdown if specified
                if strategy:
                    parsed_filters["strategy"] = strategy
                where_clause, params = build_gp_search_sql(parsed_filters)
            else:
                # Simple text search
                conditions = ["o.is_gp = TRUE"]
                simple_params: list[Any] = []
                if search:
                    conditions.append("(o.name ILIKE %s OR o.hq_city ILIKE %s OR gp.investment_philosophy ILIKE %s)")
                    simple_params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
                if strategy:
                    conditions.append("gp.investment_philosophy ILIKE %s")
                    simple_params.append(f"%{strategy}%")
                where_clause = " AND ".join(conditions)
                params = simple_params

            query = base_query.format(where_clause=where_clause)
            cur.execute(query, params)
            gps = cur.fetchall()

            # Calculate total funds
            total_funds = sum(gp["fund_count"] or 0 for gp in gps)

        return templates.TemplateResponse(
            request,
            "pages/gps.html",
            {
                "title": "GPs - LPxGP",
                "user": user,
                "gps": gps,
                "total_funds": total_funds,
                "search": search or "",
                "strategy": strategy or "",
                "strategies": strategies,
                "parsed_filters": parsed_filters,  # Show what AI extracted
            },
        )
    finally:
        conn.close()


@app.get("/lps/{lp_id}", response_class=HTMLResponse, response_model=None)
async def lp_detail_page(request: Request, lp_id: str) -> HTMLResponse | RedirectResponse:
    """LP detail page showing full profile and match analysis.

    Requires authentication.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not is_valid_uuid(lp_id):
        return HTMLResponse(content="Invalid LP ID", status_code=400)

    # Mock LP data for offline mode
    mock_lp = {
        "id": lp_id,
        "name": "CalPERS",
        "full_name": "California Public Employees' Retirement System",
        "lp_type": "Public Pension",
        "hq_city": "Sacramento",
        "hq_country": "USA",
        "total_aum_bn": 450.0,
        "pe_allocation_pct": 13.0,
        "check_size_min_mm": 100,
        "check_size_max_mm": 500,
        "target_return": "Net IRR 11%+",
        "geo_preferences": "North America, Europe",
        "strategies": ["buyout", "growth_equity", "venture"],
        "score": 92,
        "in_shortlist": is_in_shortlist(user["id"], lp_id),
        "contacts": [
            {"name": "Michael Smith", "title": "Managing Investment Director, Private Equity"},
            {"name": "Jennifer Chen", "title": "Investment Director, Growth Equity"},
        ],
    }

    conn = get_db()
    if not conn:
        return templates.TemplateResponse(
            request,
            "pages/lp-detail.html",
            {"title": f"{mock_lp['name']} - LPxGP", "user": user, "lp": mock_lp},
        )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT o.id, o.name, o.hq_city, o.hq_country, o.website,
                       lp.lp_type, lp.total_aum_bn, lp.pe_allocation_pct,
                       lp.check_size_min_mm, lp.check_size_max_mm,
                       lp.geographic_preferences, lp.strategies
                FROM organizations o
                JOIN lp_profiles lp ON lp.org_id = o.id
                WHERE o.id = %s
                """,
                (lp_id,),
            )
            lp = cur.fetchone()

            if not lp:
                # Fall back to mock data if LP not in database
                return templates.TemplateResponse(
                    request,
                    "pages/lp-detail.html",
                    {"title": f"{mock_lp['name']} - LPxGP", "user": user, "lp": mock_lp},
                )

            lp["in_shortlist"] = is_in_shortlist(user["id"], lp_id)
            lp["score"] = 85  # Default score

        return templates.TemplateResponse(
            request,
            "pages/lp-detail.html",
            {"title": f"{lp['name']} - LPxGP", "user": user, "lp": lp},
        )
    finally:
        conn.close()


@app.get("/funds/{fund_id}", response_class=HTMLResponse, response_model=None)
async def fund_detail_page(request: Request, fund_id: str) -> HTMLResponse | RedirectResponse:
    """Fund detail page showing full fund profile.

    Requires authentication.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not is_valid_uuid(fund_id):
        return HTMLResponse(content="Invalid Fund ID", status_code=400)

    # Mock fund data for offline mode
    mock_fund = {
        "id": fund_id,
        "name": "Growth Fund III",
        "status": "fundraising",
        "strategy": "private_equity",
        "primary_strategy": "growth_equity",
        "target_size_mm": 500,
        "raised_mm": 150,
        "target_close": "Q2 2025",
        "geo_focus": "North America",
        "sectors": ["Technology", "Healthcare"],
        "check_min_mm": 25,
        "check_max_mm": 75,
        "stage": "Growth / Expansion",
        "prior_moic": "2.3",
        "prior_irr": "28.5",
        "portfolio_count": 18,
        "capital_deployed_mm": 550,
        "total_matches": 45,
        "high_score_matches": 12,
        "shortlisted": 8,
        "contacted": 5,
    }

    conn = get_db()
    if not conn:
        return templates.TemplateResponse(
            request,
            "pages/fund-detail.html",
            {"title": f"{mock_fund['name']} - LPxGP", "user": user, "fund": mock_fund},
        )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, status, target_size_mm, vintage_year,
                       strategy, geo_focus, sector_focus
                FROM funds
                WHERE id = %s
                """,
                (fund_id,),
            )
            fund = cur.fetchone()

            if not fund:
                # Fall back to mock data if fund not in database
                return templates.TemplateResponse(
                    request,
                    "pages/fund-detail.html",
                    {"title": f"{mock_fund['name']} - LPxGP", "user": user, "fund": mock_fund},
                )

        return templates.TemplateResponse(
            request,
            "pages/fund-detail.html",
            {"title": f"{fund['name']} - LPxGP", "user": user, "fund": fund},
        )
    except Exception:
        # Fall back to mock data on any database error
        return templates.TemplateResponse(
            request,
            "pages/fund-detail.html",
            {"title": f"{mock_fund['name']} - LPxGP", "user": user, "fund": mock_fund},
        )
    finally:
        conn.close()


@app.get("/matches/{lp_id}", response_class=HTMLResponse, response_model=None)
async def match_detail_page(
    request: Request,
    lp_id: str,
    fund_id: str | None = Query(None),
) -> HTMLResponse | RedirectResponse:
    """Match detail page showing AI analysis for LP-Fund pairing.

    Requires authentication.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not is_valid_uuid(lp_id):
        return HTMLResponse(content="Invalid LP ID", status_code=400)

    # Validate fund_id if provided
    if fund_id and not is_valid_uuid(fund_id):
        fund_id = None  # Fall back to default if invalid

    # Mock data for offline mode
    mock_lp = {
        "id": lp_id,
        "name": "CalPERS",
        "in_shortlist": is_in_shortlist(user["id"], lp_id),
    }
    mock_fund = {
        "id": fund_id or "00000000-0000-0000-0000-000000000001",
        "name": "Growth Fund III",
        "target_size_mm": 500,
    }
    mock_match = {
        "score": 92,
        "explanation": "CalPERS presents an excellent fit for Growth Fund III based on several key factors:",
        "score_breakdown": {
            "strategy": 95,
            "size_fit": 90,
            "geography": 92,
            "track_record": 88,
        },
        "talking_points": [
            "Strategy alignment: CalPERS actively invests in growth equity managers",
            "Fund size fit: Your $500M target is within their preferred range",
            "Track record: Your prior fund performance exceeds their hurdle rate",
            "ESG commitment: Both organizations prioritize responsible investing",
        ],
        "concerns": [
            "Competition: CalPERS receives many manager proposals annually",
            "Due diligence timeline: Their process typically takes 9-12 months",
            "Co-investment: They often expect co-investment opportunities",
        ],
    }

    return templates.TemplateResponse(
        request,
        "pages/match-detail.html",
        {
            "title": f"Match Analysis: {mock_lp['name']} - LPxGP",
            "user": user,
            "lp": mock_lp,
            "fund": mock_fund,
            "match": mock_match,
        },
    )


@app.get("/outreach", response_class=HTMLResponse, response_model=None)
async def outreach_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Outreach Hub for managing LP communications.

    Requires authentication.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Mock stats for offline mode
    stats = {
        "shortlisted": len(get_user_shortlist(user["id"])),
        "funds_count": 3,
        "contacted": 18,
        "contacted_week": 5,
        "meetings": 8,
        "meetings_scheduled": 3,
        "response_rate": 44,
        "responses": 8,
    }

    # Mock activities
    activities = [
        {
            "type": "meeting",
            "description": "Meeting scheduled with",
            "lp_name": "Yale Endowment",
            "lp_id": "lp-yale",
            "details": "January 15, 2025 at 2:00 PM EST",
            "fund_name": "Growth Fund III",
            "time_ago": "2 hours ago",
        },
        {
            "type": "email",
            "description": "Email sent to",
            "lp_name": "CalPERS",
            "lp_id": "lp-calpers",
            "details": "Michael Smith",
            "fund_name": "Growth Fund III",
            "time_ago": "Yesterday",
        },
        {
            "type": "pitch",
            "description": "Pitch generated for",
            "lp_name": "Ontario Teachers",
            "lp_id": "lp-ontario",
            "fund_name": "Growth Fund III",
            "time_ago": "2 days ago",
        },
    ]

    upcoming_meetings = [
        {"lp_name": "Yale Endowment", "lp_id": "lp-yale", "date": "Jan 15, 2:00 PM"},
        {"lp_name": "Stanford Endowment", "lp_id": "lp-stanford", "date": "Jan 18, 10:00 AM"},
    ]

    followups = [
        {"lp_name": "Ontario Teachers", "lp_id": "lp-ontario", "days_ago": 5},
        {"lp_name": "CalPERS", "lp_id": "lp-calpers", "days_ago": 3},
        {"lp_name": "CPPIB", "lp_id": "lp-cppib", "days_ago": 7},
    ]

    mock_funds = [
        {"id": "fund-1", "name": "Growth Fund III"},
        {"id": "fund-2", "name": "Growth Fund II"},
    ]

    return templates.TemplateResponse(
        request,
        "pages/outreach.html",
        {
            "title": "Outreach Hub - LPxGP",
            "user": user,
            "stats": stats,
            "activities": activities,
            "upcoming_meetings": upcoming_meetings,
            "followups": followups,
            "funds": mock_funds,
        },
    )


@app.get("/pipeline", response_class=HTMLResponse, response_model=None)
async def pipeline_page(
    request: Request,
    fund_id: str | None = None,
) -> HTMLResponse | RedirectResponse:
    """Kanban-style pipeline board for tracking LP relationships.

    Displays all LPs in the pipeline with their current stage.
    Cards can be dragged between columns to update status.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Define pipeline stages with colors
    stages = [
        {"id": "recommended", "name": "Recommended", "color": "bg-gray-400", "items": []},
        {"id": "gp_interested", "name": "Interested", "color": "bg-blue-400", "items": []},
        {"id": "gp_pursuing", "name": "Pursuing", "color": "bg-indigo-400", "items": []},
        {"id": "lp_reviewing", "name": "LP Reviewing", "color": "bg-yellow-400", "items": []},
        {"id": "mutual_interest", "name": "Mutual Interest", "color": "bg-green-400", "items": []},
        {"id": "in_diligence", "name": "In DD", "color": "bg-purple-400", "items": []},
        {"id": "invested", "name": "Invested", "color": "bg-emerald-500", "items": []},
        {"id": "gp_passed", "name": "GP Passed", "color": "bg-red-300", "items": []},
        {"id": "lp_passed", "name": "LP Passed", "color": "bg-red-400", "items": []},
    ]

    funds: list[dict[str, Any]] = []

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                # Get user's funds
                cur.execute(
                    """
                    SELECT f.id, f.name
                    FROM funds f
                    JOIN organizations o ON o.id = f.gp_org_id
                    WHERE o.id IN (
                        SELECT org_id FROM users WHERE id = %s
                    )
                    ORDER BY f.name
                    """,
                    (user["id"],),
                )
                funds = cur.fetchall()

                # Build filter
                fund_filter = ""
                params: list[Any] = []
                if fund_id:
                    fund_filter = "AND s.fund_id = %s"
                    params.append(fund_id)

                # Get pipeline items
                cur.execute(
                    f"""
                    SELECT
                        s.fund_id,
                        s.lp_org_id as lp_id,
                        s.pipeline_stage,
                        s.gp_interest,
                        s.lp_interest,
                        s.notes,
                        s.updated_at,
                        o.name as lp_name,
                        f.name as fund_name
                    FROM fund_lp_status s
                    JOIN organizations o ON o.id = s.lp_org_id
                    JOIN funds f ON f.id = s.fund_id
                    WHERE s.pipeline_stage IS NOT NULL
                    {fund_filter}
                    ORDER BY s.updated_at DESC
                    """,
                    params,
                )
                items = cur.fetchall()

                # Group by stage
                for item in items:
                    stage_id = item["pipeline_stage"]
                    for stage in stages:
                        if stage["id"] == stage_id:
                            stage["items"].append({
                                "fund_id": str(item["fund_id"]),
                                "lp_id": str(item["lp_id"]),
                                "lp_name": item["lp_name"],
                                "fund_name": item["fund_name"],
                                "gp_interest": item["gp_interest"],
                                "lp_interest": item["lp_interest"],
                                "notes": item["notes"],
                                "updated_at": str(item["updated_at"]) if item["updated_at"] else None,
                            })
                            break
        except Exception as e:
            logger.error(f"Pipeline page error: {e}")
        finally:
            conn.close()

    return templates.TemplateResponse(
        request,
        "pages/pipeline.html",
        {
            "user": user,
            "stages": stages,
            "funds": funds,
            "selected_fund_id": fund_id,
        },
    )


@app.get("/pipeline/{fund_id}/{lp_id}", response_class=HTMLResponse, response_model=None)
async def pipeline_detail_page(
    request: Request,
    fund_id: str,
    lp_id: str,
) -> HTMLResponse | RedirectResponse:
    """Detail page for a pipeline item with notes, contacts, and activity.

    Shows full LP info, allows editing notes, and displays activity history.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not is_valid_uuid(fund_id) or not is_valid_uuid(lp_id):
        return RedirectResponse(url="/pipeline", status_code=303)

    # Define stages for dropdown
    stages = [
        {"id": "recommended", "name": "Recommended"},
        {"id": "gp_interested", "name": "Interested"},
        {"id": "gp_pursuing", "name": "Pursuing"},
        {"id": "lp_reviewing", "name": "LP Reviewing"},
        {"id": "mutual_interest", "name": "Mutual Interest"},
        {"id": "in_diligence", "name": "In Diligence"},
        {"id": "invested", "name": "Invested"},
        {"id": "gp_passed", "name": "GP Passed"},
        {"id": "lp_passed", "name": "LP Passed"},
    ]

    lp: dict[str, Any] = {}
    fund: dict[str, Any] = {}
    status: dict[str, Any] = {}
    activities: list[dict[str, Any]] = []
    contacts: list[dict[str, Any]] = []

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                # Get LP info
                cur.execute(
                    """
                    SELECT id, name, lp_type, hq_city, hq_country,
                           total_aum_bn, pe_allocation_pct,
                           check_size_min_mm, check_size_max_mm
                    FROM organizations
                    WHERE id = %s
                    """,
                    (lp_id,),
                )
                lp = cur.fetchone() or {}

                # Get fund info
                cur.execute(
                    "SELECT id, name FROM funds WHERE id = %s",
                    (fund_id,),
                )
                fund = cur.fetchone() or {}

                # Get status
                cur.execute(
                    """
                    SELECT pipeline_stage, gp_interest, lp_interest, notes, updated_at
                    FROM fund_lp_status
                    WHERE fund_id = %s AND lp_org_id = %s
                    """,
                    (fund_id, lp_id),
                )
                status = cur.fetchone() or {"pipeline_stage": "recommended"}

                # Get activities from outreach_events
                cur.execute(
                    """
                    SELECT e.event_type, e.event_date, e.notes
                    FROM outreach_events e
                    JOIN fund_lp_matches m ON m.id = e.match_id
                    WHERE m.fund_id = %s AND m.lp_org_id = %s
                    ORDER BY e.event_date DESC
                    LIMIT 20
                    """,
                    (fund_id, lp_id),
                )
                activities = cur.fetchall()

                # Get contacts
                cur.execute(
                    """
                    SELECT p.id, p.full_name, p.email, p.linkedin_url, cp.title
                    FROM people p
                    JOIN company_people cp ON cp.person_id = p.id
                    WHERE cp.org_id = %s
                    ORDER BY cp.is_decision_maker DESC, p.full_name
                    LIMIT 5
                    """,
                    (lp_id,),
                )
                contacts = cur.fetchall()
        except Exception as e:
            logger.error(f"Pipeline detail error: {e}")
        finally:
            conn.close()

    if not lp:
        return RedirectResponse(url="/pipeline", status_code=303)

    return templates.TemplateResponse(
        request,
        "pages/pipeline-detail.html",
        {
            "user": user,
            "lp": lp,
            "fund": fund,
            "status": status,
            "stages": stages,
            "activities": activities,
            "contacts": contacts,
        },
    )


@app.get("/pitch", response_class=HTMLResponse, response_model=None)
async def pitch_generator_page(
    request: Request,
    lp_id: str | None = Query(None),
    fund_id: str | None = Query(None),
) -> HTMLResponse | RedirectResponse:
    """Pitch generator page for creating LP-specific content.

    Requires authentication.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Mock LP data
    mock_lp = {
        "id": lp_id or "lp-calpers",
        "name": "CalPERS",
        "score": 92,
        "contact_name": "Michael Smith",
        "contact_title": "Managing Investment Director",
    }

    # Mock funds
    mock_funds = [
        {"id": "fund-1", "name": "Growth Fund III", "target_size_mm": 500},
        {"id": "fund-2", "name": "Growth Fund II", "target_size_mm": 350},
    ]

    return templates.TemplateResponse(
        request,
        "pages/pitch-generator.html",
        {
            "title": f"Pitch Generator - {mock_lp['name']} - LPxGP",
            "user": user,
            "lp": mock_lp,
            "funds": mock_funds,
        },
    )


# -----------------------------------------------------------------------------
# API Endpoints (HTMX partials)
# -----------------------------------------------------------------------------

@app.get("/api/match/{match_id}/detail", response_class=HTMLResponse)
async def match_detail(request: Request, match_id: str):
    """Get match detail for modal display (HTMX partial)."""
    if not is_valid_uuid(match_id):
        return HTMLResponse(
            content="<p class='text-red-500'>Invalid match ID</p>",
            status_code=400
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content="<p class='text-navy-500'>Database not configured</p>",
            status_code=503
        )

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    m.id, m.fund_id, m.lp_org_id, m.score,
                    m.score_breakdown, m.explanation, m.talking_points, m.concerns,
                    o.name as lp_name, o.hq_city as lp_city, o.hq_country as lp_country,
                    o.website as lp_website,
                    lp.lp_type, lp.total_aum_bn, lp.pe_allocation_pct,
                    lp.check_size_min_mm, lp.check_size_max_mm,
                    f.name as fund_name, f.target_size_mm, f.vintage_year,
                    s.pipeline_stage, s.gp_interest, s.lp_interest,
                    s.gp_interest_reason, s.lp_interest_reason
                FROM fund_lp_matches m
                JOIN organizations o ON o.id = m.lp_org_id
                LEFT JOIN lp_profiles lp ON lp.org_id = m.lp_org_id
                JOIN funds f ON f.id = m.fund_id
                LEFT JOIN fund_lp_status s ON s.fund_id = m.fund_id AND s.lp_org_id = m.lp_org_id
                WHERE m.id = %s
            """, (match_id,))
            match = cur.fetchone()

        if not match:
            return HTMLResponse(
                content="<p class='text-navy-500'>Match not found</p>",
                status_code=404
            )

        return templates.TemplateResponse(
            request,
            "partials/match_detail_modal.html",
            {"match": match},
        )
    finally:
        conn.close()


@app.get("/api/lp/{lp_id}/detail", response_class=HTMLResponse)
async def lp_detail(request: Request, lp_id: str):
    """Get LP detail for modal display (HTMX partial)."""
    if not is_valid_uuid(lp_id):
        return HTMLResponse(
            content="<p class='text-red-500'>Invalid LP ID</p>",
            status_code=400
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content="<p class='text-navy-500'>Database not configured</p>",
            status_code=503
        )

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    o.id, o.name, o.hq_city, o.hq_country, o.website,
                    o.description,
                    lp.lp_type, lp.total_aum_bn, lp.pe_allocation_pct,
                    lp.check_size_min_mm, lp.check_size_max_mm,
                    lp.fund_size_min_mm, lp.fund_size_max_mm,
                    lp.strategies, lp.geographic_preferences, lp.sector_preferences,
                    lp.esg_required, lp.emerging_manager_ok,
                    lp.min_track_record_years, lp.min_fund_number,
                    lp.mandate_description
                FROM organizations o
                JOIN lp_profiles lp ON lp.org_id = o.id
                WHERE o.id = %s
            """, (lp_id,))
            lp = cur.fetchone()

            # Get contacts for this LP
            cur.execute("""
                SELECT p.id, p.full_name, e.title, p.email, p.linkedin_url
                FROM people p
                JOIN employment e ON e.person_id = p.id
                WHERE e.org_id = %s AND e.is_current = TRUE
                ORDER BY p.full_name
                LIMIT 5
            """, (lp_id,))
            contacts = cur.fetchall()

        if not lp:
            return HTMLResponse(
                content="<p class='text-navy-500'>LP not found</p>",
                status_code=404
            )

        return templates.TemplateResponse(
            request,
            "partials/lp_detail_modal.html",
            {"lp": lp, "contacts": contacts},
        )
    finally:
        conn.close()


@app.post("/api/funds", response_class=HTMLResponse)
async def create_fund(
    request: Request,
    name: str = Form(...),
    org_id: str = Form(...),
    status: str = Form(default="draft"),
    vintage_year: int | None = Form(default=None),
    target_size_mm: float | None = Form(default=None),
    strategy: str | None = Form(default=None),
    sub_strategy: str | None = Form(default=None),
    geographic_focus: str | None = Form(default=""),
    sector_focus: str | None = Form(default=""),
    check_size_min_mm: float | None = Form(default=None),
    check_size_max_mm: float | None = Form(default=None),
    investment_thesis: str | None = Form(default=None),
    management_fee_pct: float | None = Form(default=None),
    carried_interest_pct: float | None = Form(default=None),
    gp_commitment_pct: float | None = Form(default=None),
):
    """Create a new fund."""
    if not is_valid_uuid(org_id):
        return HTMLResponse(
            content="<p class='text-red-500'>Invalid organization ID</p>",
            status_code=400
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content="<p class='text-navy-500'>Database not configured</p>",
            status_code=503
        )

    try:
        # Parse array fields (comma-separated)
        geo_array = [g.strip() for g in geographic_focus.split(",") if g.strip()] if geographic_focus else []
        sector_array = [s.strip() for s in sector_focus.split(",") if s.strip()] if sector_focus else []

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO funds (
                    org_id, name, status, vintage_year, target_size_mm,
                    strategy, sub_strategy, geographic_focus, sector_focus,
                    check_size_min_mm, check_size_max_mm, investment_thesis,
                    management_fee_pct, carried_interest_pct, gp_commitment_pct
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """, (
                org_id, name, status, vintage_year, target_size_mm,
                strategy, sub_strategy, geo_array, sector_array,
                check_size_min_mm, check_size_max_mm, investment_thesis,
                management_fee_pct, carried_interest_pct, gp_commitment_pct
            ))
            result = cur.fetchone()
            _ = result["id"] if result else None  # Verify insert succeeded
            conn.commit()

        # Return success with redirect
        return HTMLResponse(
            content=f"""
            <div class="text-center p-4">
                <svg class="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                <h3 class="text-lg font-semibold text-navy-900 mb-2">Fund Created!</h3>
                <p class="text-navy-500 mb-4">{name} has been created successfully.</p>
                <a href="/funds" class="btn-primary">View All Funds</a>
            </div>
            """,
            headers={"HX-Trigger": "fundCreated"}
        )
    except Exception as e:
        logger.error(f"Failed to create fund: {e}")
        conn.rollback()
        return HTMLResponse(
            content=f"<p class='text-red-500'>Failed to create fund: {str(e)}</p>",
            status_code=500
        )
    finally:
        conn.close()


@app.get("/api/organizations/gp", response_class=JSONResponse)
async def get_gp_organizations():
    """Get list of GP organizations for fund creation."""
    conn = get_db()
    if not conn:
        return JSONResponse(content=[], status_code=200)

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name FROM organizations
                WHERE is_gp = TRUE
                ORDER BY name
            """)
            orgs = cur.fetchall()
        return JSONResponse(content=[dict(o) for o in orgs])
    finally:
        conn.close()


@app.get("/api/funds/{fund_id}/edit", response_class=HTMLResponse)
async def get_fund_edit_form(request: Request, fund_id: str):
    """Get fund edit form with pre-populated data."""
    if not is_valid_uuid(fund_id):
        return HTMLResponse(content="<p class='text-red-500'>Invalid fund ID</p>", status_code=400)

    conn = get_db()
    if not conn:
        return HTMLResponse(content="<p class='text-navy-500'>Database not configured</p>", status_code=503)

    try:
        with conn.cursor() as cur:
            # Get fund data
            cur.execute("""
                SELECT f.*, o.name as gp_name
                FROM funds f
                JOIN organizations o ON f.org_id = o.id
                WHERE f.id = %s
            """, (fund_id,))
            fund = cur.fetchone()

            if not fund:
                return HTMLResponse(content="<p class='text-red-500'>Fund not found</p>", status_code=404)

            # Get GP organizations for dropdown
            cur.execute("""
                SELECT id, name FROM organizations
                WHERE is_gp = TRUE
                ORDER BY name
            """)
            gp_orgs = cur.fetchall()

        return templates.TemplateResponse(
            "partials/fund_edit_modal.html",
            {"request": request, "fund": fund, "gp_orgs": gp_orgs}
        )
    finally:
        conn.close()


@app.put("/api/funds/{fund_id}", response_class=HTMLResponse)
async def update_fund(
    request: Request,
    fund_id: str,
    name: str = Form(...),
    org_id: str = Form(...),
    status: str = Form(default="draft"),
    vintage_year: int | None = Form(default=None),
    target_size_mm: float | None = Form(default=None),
    strategy: str | None = Form(default=None),
    sub_strategy: str | None = Form(default=None),
    geographic_focus: str | None = Form(default=""),
    sector_focus: str | None = Form(default=""),
    check_size_min_mm: float | None = Form(default=None),
    check_size_max_mm: float | None = Form(default=None),
    investment_thesis: str | None = Form(default=None),
    management_fee_pct: float | None = Form(default=None),
    carried_interest_pct: float | None = Form(default=None),
    gp_commitment_pct: float | None = Form(default=None),
):
    """Update an existing fund."""
    if not is_valid_uuid(fund_id) or not is_valid_uuid(org_id):
        return HTMLResponse(
            content="<p class='text-red-500'>Invalid ID</p>",
            status_code=400
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content="<p class='text-navy-500'>Database not configured</p>",
            status_code=503
        )

    try:
        # Parse array fields (comma-separated)
        geo_array = [g.strip() for g in geographic_focus.split(",") if g.strip()] if geographic_focus else []
        sector_array = [s.strip() for s in sector_focus.split(",") if s.strip()] if sector_focus else []

        with conn.cursor() as cur:
            cur.execute("""
                UPDATE funds SET
                    org_id = %s,
                    name = %s,
                    status = %s,
                    vintage_year = %s,
                    target_size_mm = %s,
                    strategy = %s,
                    sub_strategy = %s,
                    geographic_focus = %s,
                    sector_focus = %s,
                    check_size_min_mm = %s,
                    check_size_max_mm = %s,
                    investment_thesis = %s,
                    management_fee_pct = %s,
                    carried_interest_pct = %s,
                    gp_commitment_pct = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                org_id, name, status, vintage_year, target_size_mm,
                strategy, sub_strategy, geo_array, sector_array,
                check_size_min_mm, check_size_max_mm, investment_thesis,
                management_fee_pct, carried_interest_pct, gp_commitment_pct,
                fund_id
            ))
            conn.commit()

        return HTMLResponse(
            content=f"""
            <div class="text-center p-4">
                <svg class="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                <h3 class="text-lg font-semibold text-navy-900 mb-2">Fund Updated!</h3>
                <p class="text-navy-500 mb-4">{name} has been updated successfully.</p>
            </div>
            """,
            headers={"HX-Trigger": "fundUpdated"}
        )
    except Exception as e:
        logger.error(f"Failed to update fund: {e}")
        conn.rollback()
        return HTMLResponse(
            content=f"<p class='text-red-500'>Failed to update fund: {str(e)}</p>",
            status_code=500
        )
    finally:
        conn.close()


@app.delete("/api/funds/{fund_id}", response_class=HTMLResponse)
async def delete_fund(request: Request, fund_id: str):
    """Delete a fund."""
    if not is_valid_uuid(fund_id):
        return HTMLResponse(
            content="<p class='text-red-500'>Invalid fund ID</p>",
            status_code=400
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content="<p class='text-navy-500'>Database not configured</p>",
            status_code=503
        )

    try:
        with conn.cursor() as cur:
            # Get fund name for confirmation message
            cur.execute("SELECT name FROM funds WHERE id = %s", (fund_id,))
            fund = cur.fetchone()
            if not fund:
                return HTMLResponse(
                    content="<p class='text-red-500'>Fund not found</p>",
                    status_code=404
                )
            fund_name = fund["name"]

            # Delete the fund
            cur.execute("DELETE FROM funds WHERE id = %s", (fund_id,))
            conn.commit()

        return HTMLResponse(
            content=f"""
            <div class="text-center p-4">
                <svg class="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                <h3 class="text-lg font-semibold text-navy-900 mb-2">Fund Deleted</h3>
                <p class="text-navy-500 mb-4">{fund_name} has been deleted.</p>
            </div>
            """,
            headers={"HX-Trigger": "fundDeleted"}
        )
    except Exception as e:
        logger.error(f"Failed to delete fund: {e}")
        conn.rollback()
        return HTMLResponse(
            content=f"<p class='text-red-500'>Failed to delete fund: {str(e)}</p>",
            status_code=500
        )
    finally:
        conn.close()


@app.post("/api/funds/{fund_id}/generate-matches", response_class=HTMLResponse)
async def generate_matches_for_fund(request: Request, fund_id: str):
    """Generate AI-powered matches for a fund against all LPs."""
    import json

    from src.matching import (
        FundData,
        LPData,
        calculate_match_score,
        generate_match_content,
    )

    if not is_valid_uuid(fund_id):
        return HTMLResponse(
            content="<p class='text-red-500'>Invalid fund ID</p>",
            status_code=400
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content="<p class='text-navy-500'>Database not configured</p>",
            status_code=503
        )

    settings = get_settings()
    matches_generated = 0
    matches_skipped = 0

    try:
        with conn.cursor() as cur:
            # Fetch fund details with GP info
            cur.execute("""
                SELECT f.*, o.name as gp_name
                FROM funds f
                JOIN organizations o ON o.id = f.org_id
                WHERE f.id = %s
            """, (fund_id,))
            fund = cur.fetchone()

            if not fund:
                return HTMLResponse(
                    content="<p class='text-red-500'>Fund not found</p>",
                    status_code=404
                )

            # Fetch all LP profiles with organization info
            cur.execute("""
                SELECT lp.*, o.name, o.hq_city, o.hq_country
                FROM lp_profiles lp
                JOIN organizations o ON o.id = lp.org_id
                WHERE o.is_lp = true
            """)
            lps = cur.fetchall()

            for lp in lps:
                # Calculate match score (cast dict to TypedDict for type safety)
                fund_data = cast(FundData, dict(fund))
                lp_data = cast(LPData, dict(lp))
                result = calculate_match_score(fund_data, lp_data)

                # Only create matches for scores above threshold
                if result["score"] >= 50:
                    # Generate LLM content
                    content = await generate_match_content(
                        fund_data,
                        lp_data,
                        result["score_breakdown"],
                        ollama_base_url=settings.ollama_base_url,
                        ollama_model=settings.ollama_model
                    )

                    # Upsert match
                    cur.execute("""
                        INSERT INTO fund_lp_matches
                            (fund_id, lp_org_id, score, score_breakdown, explanation, talking_points, concerns, model_version)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (fund_id, lp_org_id)
                        DO UPDATE SET
                            score = EXCLUDED.score,
                            score_breakdown = EXCLUDED.score_breakdown,
                            explanation = EXCLUDED.explanation,
                            talking_points = EXCLUDED.talking_points,
                            concerns = EXCLUDED.concerns,
                            model_version = EXCLUDED.model_version,
                            created_at = NOW()
                    """, (
                        fund_id,
                        lp["org_id"],
                        result["score"],
                        json.dumps(result["score_breakdown"]),
                        content["explanation"],
                        content["talking_points"],
                        content["concerns"],
                        settings.ollama_model
                    ))
                    matches_generated += 1
                else:
                    matches_skipped += 1

            conn.commit()

        return HTMLResponse(
            content=f"""
            <div class="text-center p-4">
                <svg class="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                <h3 class="text-lg font-semibold text-navy-900 mb-2">Matches Generated</h3>
                <p class="text-navy-500 mb-2">Found {matches_generated} matching LPs for {fund['name']}</p>
                <p class="text-navy-400 text-sm">{matches_skipped} LPs did not meet criteria</p>
            </div>
            """,
            headers={"HX-Trigger": "matchesGenerated"}
        )
    except Exception as e:
        logger.error(f"Failed to generate matches: {e}")
        conn.rollback()
        return HTMLResponse(
            content=f"<p class='text-red-500'>Failed to generate matches: {str(e)}</p>",
            status_code=500
        )
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# LP CRUD Endpoints
# -----------------------------------------------------------------------------

@app.post("/api/lps", response_class=HTMLResponse)
async def create_lp(
    request: Request,
    name: str = Form(...),
    lp_type: str | None = Form(default=None),
    hq_city: str | None = Form(default=None),
    hq_country: str | None = Form(default=None),
    website: str | None = Form(default=None),
    description: str | None = Form(default=None),
    total_aum_bn: float | None = Form(default=None),
    pe_allocation_pct: float | None = Form(default=None),
    strategies: str | None = Form(default=""),
    geographic_preferences: str | None = Form(default=""),
    sector_preferences: str | None = Form(default=""),
    check_size_min_mm: float | None = Form(default=None),
    check_size_max_mm: float | None = Form(default=None),
    fund_size_min_mm: float | None = Form(default=None),
    fund_size_max_mm: float | None = Form(default=None),
    min_track_record_years: int | None = Form(default=None),
    min_fund_number: int | None = Form(default=None),
    esg_required: bool = Form(default=False),
    emerging_manager_ok: bool = Form(default=False),
    mandate_description: str | None = Form(default=None),
):
    """Create a new LP (organization + lp_profile)."""
    conn = get_db()
    if not conn:
        return HTMLResponse(
            content="<p class='text-navy-500'>Database not configured</p>",
            status_code=503
        )

    try:
        # Parse array fields
        strategies_arr = [s.strip() for s in strategies.split(",") if s.strip()] if strategies else []
        geo_arr = [g.strip() for g in geographic_preferences.split(",") if g.strip()] if geographic_preferences else []
        sector_arr = [s.strip() for s in sector_preferences.split(",") if s.strip()] if sector_preferences else []

        with conn.cursor() as cur:
            # Create organization
            cur.execute("""
                INSERT INTO organizations (name, website, hq_city, hq_country, description, is_lp)
                VALUES (%s, %s, %s, %s, %s, TRUE)
                RETURNING id
            """, (name, website, hq_city, hq_country, description))
            result = cur.fetchone()
            if not result:
                raise ValueError("Failed to create organization")
            org_id = result["id"]

            # Create lp_profile
            cur.execute("""
                INSERT INTO lp_profiles (
                    org_id, lp_type, total_aum_bn, pe_allocation_pct,
                    strategies, geographic_preferences, sector_preferences,
                    check_size_min_mm, check_size_max_mm,
                    fund_size_min_mm, fund_size_max_mm,
                    min_track_record_years, min_fund_number,
                    esg_required, emerging_manager_ok, mandate_description
                ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """, (
                org_id, lp_type, total_aum_bn, pe_allocation_pct,
                strategies_arr, geo_arr, sector_arr,
                check_size_min_mm, check_size_max_mm,
                fund_size_min_mm, fund_size_max_mm,
                min_track_record_years, min_fund_number,
                esg_required, emerging_manager_ok, mandate_description
            ))
            conn.commit()

        return HTMLResponse(
            content=f"""
            <div class="text-center p-4">
                <svg class="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                <h3 class="text-lg font-semibold text-navy-900 mb-2">LP Created!</h3>
                <p class="text-navy-500 mb-4">{name} has been added to the database.</p>
            </div>
            """,
            headers={"HX-Trigger": "lpCreated"}
        )
    except Exception as e:
        logger.error(f"Failed to create LP: {e}")
        conn.rollback()
        return HTMLResponse(
            content=f"<p class='text-red-500'>Failed to create LP: {str(e)}</p>",
            status_code=500
        )
    finally:
        conn.close()


@app.get("/api/lps/{lp_id}/edit", response_class=HTMLResponse)
async def get_lp_edit_form(request: Request, lp_id: str):
    """Get LP edit form with pre-populated data."""
    if not is_valid_uuid(lp_id):
        return HTMLResponse(content="<p class='text-red-500'>Invalid LP ID</p>", status_code=400)

    conn = get_db()
    if not conn:
        return HTMLResponse(content="<p class='text-navy-500'>Database not configured</p>", status_code=503)

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    o.id, o.name, o.hq_city, o.hq_country, o.website, o.description,
                    lp.lp_type, lp.total_aum_bn, lp.pe_allocation_pct,
                    lp.strategies, lp.geographic_preferences, lp.sector_preferences,
                    lp.check_size_min_mm, lp.check_size_max_mm,
                    lp.fund_size_min_mm, lp.fund_size_max_mm,
                    lp.min_track_record_years, lp.min_fund_number,
                    lp.esg_required, lp.emerging_manager_ok, lp.mandate_description
                FROM organizations o
                JOIN lp_profiles lp ON lp.org_id = o.id
                WHERE o.id = %s
            """, (lp_id,))
            lp = cur.fetchone()

            if not lp:
                return HTMLResponse(content="<p class='text-red-500'>LP not found</p>", status_code=404)

        return templates.TemplateResponse(
            "partials/lp_edit_modal.html",
            {"request": request, "lp": lp}
        )
    finally:
        conn.close()


@app.put("/api/lps/{lp_id}", response_class=HTMLResponse)
async def update_lp(
    request: Request,
    lp_id: str,
    name: str = Form(...),
    lp_type: str | None = Form(default=None),
    hq_city: str | None = Form(default=None),
    hq_country: str | None = Form(default=None),
    website: str | None = Form(default=None),
    description: str | None = Form(default=None),
    total_aum_bn: float | None = Form(default=None),
    pe_allocation_pct: float | None = Form(default=None),
    strategies: str | None = Form(default=""),
    geographic_preferences: str | None = Form(default=""),
    sector_preferences: str | None = Form(default=""),
    check_size_min_mm: float | None = Form(default=None),
    check_size_max_mm: float | None = Form(default=None),
    fund_size_min_mm: float | None = Form(default=None),
    fund_size_max_mm: float | None = Form(default=None),
    min_track_record_years: int | None = Form(default=None),
    min_fund_number: int | None = Form(default=None),
    esg_required: bool = Form(default=False),
    emerging_manager_ok: bool = Form(default=False),
    mandate_description: str | None = Form(default=None),
):
    """Update an existing LP."""
    if not is_valid_uuid(lp_id):
        return HTMLResponse(content="<p class='text-red-500'>Invalid LP ID</p>", status_code=400)

    conn = get_db()
    if not conn:
        return HTMLResponse(content="<p class='text-navy-500'>Database not configured</p>", status_code=503)

    try:
        # Parse array fields
        strategies_arr = [s.strip() for s in strategies.split(",") if s.strip()] if strategies else []
        geo_arr = [g.strip() for g in geographic_preferences.split(",") if g.strip()] if geographic_preferences else []
        sector_arr = [s.strip() for s in sector_preferences.split(",") if s.strip()] if sector_preferences else []

        with conn.cursor() as cur:
            # Update organization
            cur.execute("""
                UPDATE organizations SET
                    name = %s, website = %s, hq_city = %s, hq_country = %s,
                    description = %s, updated_at = NOW()
                WHERE id = %s
            """, (name, website, hq_city, hq_country, description, lp_id))

            # Update lp_profile
            cur.execute("""
                UPDATE lp_profiles SET
                    lp_type = %s, total_aum_bn = %s, pe_allocation_pct = %s,
                    strategies = %s, geographic_preferences = %s, sector_preferences = %s,
                    check_size_min_mm = %s, check_size_max_mm = %s,
                    fund_size_min_mm = %s, fund_size_max_mm = %s,
                    min_track_record_years = %s, min_fund_number = %s,
                    esg_required = %s, emerging_manager_ok = %s,
                    mandate_description = %s, updated_at = NOW()
                WHERE org_id = %s
            """, (
                lp_type, total_aum_bn, pe_allocation_pct,
                strategies_arr, geo_arr, sector_arr,
                check_size_min_mm, check_size_max_mm,
                fund_size_min_mm, fund_size_max_mm,
                min_track_record_years, min_fund_number,
                esg_required, emerging_manager_ok,
                mandate_description, lp_id
            ))
            conn.commit()

        return HTMLResponse(
            content=f"""
            <div class="text-center p-4">
                <svg class="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                <h3 class="text-lg font-semibold text-navy-900 mb-2">LP Updated!</h3>
                <p class="text-navy-500 mb-4">{name} has been updated successfully.</p>
            </div>
            """,
            headers={"HX-Trigger": "lpUpdated"}
        )
    except Exception as e:
        logger.error(f"Failed to update LP: {e}")
        conn.rollback()
        return HTMLResponse(
            content=f"<p class='text-red-500'>Failed to update LP: {str(e)}</p>",
            status_code=500
        )
    finally:
        conn.close()


@app.delete("/api/lps/{lp_id}", response_class=HTMLResponse)
async def delete_lp(request: Request, lp_id: str):
    """Delete an LP (organization + lp_profile via CASCADE)."""
    if not is_valid_uuid(lp_id):
        return HTMLResponse(content="<p class='text-red-500'>Invalid LP ID</p>", status_code=400)

    conn = get_db()
    if not conn:
        return HTMLResponse(content="<p class='text-navy-500'>Database not configured</p>", status_code=503)

    try:
        with conn.cursor() as cur:
            # Get LP name
            cur.execute("SELECT name FROM organizations WHERE id = %s", (lp_id,))
            org = cur.fetchone()
            if not org:
                return HTMLResponse(content="<p class='text-red-500'>LP not found</p>", status_code=404)
            lp_name = org["name"]

            # Delete organization (CASCADE deletes lp_profile)
            cur.execute("DELETE FROM organizations WHERE id = %s", (lp_id,))
            conn.commit()

        return HTMLResponse(
            content=f"""
            <div class="text-center p-4">
                <svg class="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                <h3 class="text-lg font-semibold text-navy-900 mb-2">LP Deleted</h3>
                <p class="text-navy-500 mb-4">{lp_name} has been removed.</p>
            </div>
            """,
            headers={"HX-Trigger": "lpDeleted"}
        )
    except Exception as e:
        logger.error(f"Failed to delete LP: {e}")
        conn.rollback()
        return HTMLResponse(
            content=f"<p class='text-red-500'>Failed to delete LP: {str(e)}</p>",
            status_code=500
        )
    finally:
        conn.close()


# =============================================================================
# GP API Endpoints
# =============================================================================


@app.post("/api/gps", response_class=HTMLResponse)
async def create_gp(
    request: Request,
    name: str = Form(...),
    hq_city: str | None = Form(default=None),
    hq_country: str | None = Form(default=None),
    website: str | None = Form(default=None),
    description: str | None = Form(default=None),
    spun_out_from: str | None = Form(default=None),
    team_size: int | None = Form(default=None),
    years_investing: int | None = Form(default=None),
    investment_philosophy: str | None = Form(default=None),
    notable_exits: str | None = Form(default=""),
):
    """Create a new GP (organization + gp_profile)."""
    conn = get_db()
    if not conn:
        return HTMLResponse(
            content="<p class='text-navy-500'>Database not configured</p>",
            status_code=503
        )

    try:
        # Parse notable exits as JSON array
        exits_arr = [e.strip() for e in notable_exits.split("\n") if e.strip()] if notable_exits else []
        exits_json = exits_arr  # Store as simple string array

        with conn.cursor() as cur:
            # Create organization
            cur.execute("""
                INSERT INTO organizations (name, website, hq_city, hq_country, description, is_gp)
                VALUES (%s, %s, %s, %s, %s, TRUE)
                RETURNING id
            """, (name, website, hq_city, hq_country, description))
            result = cur.fetchone()
            if not result:
                raise ValueError("Failed to create organization")
            org_id = result["id"]

            # Create gp_profile
            cur.execute("""
                INSERT INTO gp_profiles (
                    org_id, investment_philosophy, team_size, years_investing,
                    spun_out_from, notable_exits
                ) VALUES (%s, %s, %s, %s, %s, %s::jsonb)
            """, (
                org_id, investment_philosophy, team_size, years_investing,
                spun_out_from, json.dumps(exits_json)
            ))
            conn.commit()

        return HTMLResponse(
            content=f"""
            <div class="text-center p-4">
                <svg class="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                <h3 class="text-lg font-semibold text-navy-900 mb-2">GP Created!</h3>
                <p class="text-navy-500 mb-4">{name} has been added to the database.</p>
            </div>
            """,
            headers={"HX-Trigger": "gpCreated"}
        )
    except Exception as e:
        logger.error(f"Failed to create GP: {e}")
        conn.rollback()
        return HTMLResponse(
            content=f"<p class='text-red-500'>Failed to create GP: {str(e)}</p>",
            status_code=500
        )
    finally:
        conn.close()


@app.get("/api/gps/{gp_id}/edit", response_class=HTMLResponse)
async def get_gp_edit_form(request: Request, gp_id: str):
    """Get GP edit form with pre-populated data."""
    if not is_valid_uuid(gp_id):
        return HTMLResponse(content="<p class='text-red-500'>Invalid GP ID</p>", status_code=400)

    conn = get_db()
    if not conn:
        return HTMLResponse(content="<p class='text-navy-500'>Database not configured</p>", status_code=503)

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    o.id, o.name, o.hq_city, o.hq_country, o.website, o.description,
                    gp.investment_philosophy, gp.team_size, gp.years_investing,
                    gp.spun_out_from, gp.notable_exits
                FROM organizations o
                JOIN gp_profiles gp ON gp.org_id = o.id
                WHERE o.id = %s
            """, (gp_id,))
            gp = cur.fetchone()

            if not gp:
                return HTMLResponse(content="<p class='text-red-500'>GP not found</p>", status_code=404)

        return templates.TemplateResponse(
            "partials/gp_edit_modal.html",
            {"request": request, "gp": gp}
        )
    finally:
        conn.close()


@app.put("/api/gps/{gp_id}", response_class=HTMLResponse)
async def update_gp(
    request: Request,
    gp_id: str,
    name: str = Form(...),
    hq_city: str | None = Form(default=None),
    hq_country: str | None = Form(default=None),
    website: str | None = Form(default=None),
    description: str | None = Form(default=None),
    spun_out_from: str | None = Form(default=None),
    team_size: int | None = Form(default=None),
    years_investing: int | None = Form(default=None),
    investment_philosophy: str | None = Form(default=None),
    notable_exits: str | None = Form(default=""),
):
    """Update an existing GP."""
    if not is_valid_uuid(gp_id):
        return HTMLResponse(content="<p class='text-red-500'>Invalid GP ID</p>", status_code=400)

    conn = get_db()
    if not conn:
        return HTMLResponse(content="<p class='text-navy-500'>Database not configured</p>", status_code=503)

    try:
        # Parse notable exits as JSON array
        exits_arr = [e.strip() for e in notable_exits.split("\n") if e.strip()] if notable_exits else []
        exits_json = exits_arr

        with conn.cursor() as cur:
            # Update organization
            cur.execute("""
                UPDATE organizations SET
                    name = %s, website = %s, hq_city = %s, hq_country = %s,
                    description = %s, updated_at = NOW()
                WHERE id = %s
            """, (name, website, hq_city, hq_country, description, gp_id))

            # Update gp_profile
            cur.execute("""
                UPDATE gp_profiles SET
                    investment_philosophy = %s, team_size = %s, years_investing = %s,
                    spun_out_from = %s, notable_exits = %s::jsonb, updated_at = NOW()
                WHERE org_id = %s
            """, (
                investment_philosophy, team_size, years_investing,
                spun_out_from, json.dumps(exits_json), gp_id
            ))
            conn.commit()

        return HTMLResponse(
            content=f"""
            <div class="text-center p-4">
                <svg class="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                <h3 class="text-lg font-semibold text-navy-900 mb-2">GP Updated!</h3>
                <p class="text-navy-500 mb-4">{name} has been updated successfully.</p>
            </div>
            """,
            headers={"HX-Trigger": "gpUpdated"}
        )
    except Exception as e:
        logger.error(f"Failed to update GP: {e}")
        conn.rollback()
        return HTMLResponse(
            content=f"<p class='text-red-500'>Failed to update GP: {str(e)}</p>",
            status_code=500
        )
    finally:
        conn.close()


@app.delete("/api/gps/{gp_id}", response_class=HTMLResponse)
async def delete_gp(request: Request, gp_id: str):
    """Delete a GP (organization + gp_profile via CASCADE)."""
    if not is_valid_uuid(gp_id):
        return HTMLResponse(content="<p class='text-red-500'>Invalid GP ID</p>", status_code=400)

    conn = get_db()
    if not conn:
        return HTMLResponse(content="<p class='text-navy-500'>Database not configured</p>", status_code=503)

    try:
        with conn.cursor() as cur:
            # Get GP name
            cur.execute("SELECT name FROM organizations WHERE id = %s", (gp_id,))
            org = cur.fetchone()
            if not org:
                return HTMLResponse(content="<p class='text-red-500'>GP not found</p>", status_code=404)
            gp_name = org["name"]

            # Delete organization (CASCADE deletes gp_profile)
            cur.execute("DELETE FROM organizations WHERE id = %s", (gp_id,))
            conn.commit()

        return HTMLResponse(
            content=f"""
            <div class="text-center p-4">
                <svg class="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                <h3 class="text-lg font-semibold text-navy-900 mb-2">GP Deleted</h3>
                <p class="text-navy-500 mb-4">{gp_name} has been removed.</p>
            </div>
            """,
            headers={"HX-Trigger": "gpDeleted"}
        )
    except Exception as e:
        logger.error(f"Failed to delete GP: {e}")
        conn.rollback()
        return HTMLResponse(
            content=f"<p class='text-red-500'>Failed to delete GP: {str(e)}</p>",
            status_code=500
        )
    finally:
        conn.close()


@app.get("/api/gp/{gp_id}/detail", response_class=HTMLResponse)
async def get_gp_detail(request: Request, gp_id: str):
    """Get GP detail partial for modal display."""
    if not is_valid_uuid(gp_id):
        return HTMLResponse(content="<p class='text-red-500'>Invalid GP ID</p>", status_code=400)

    conn = get_db()
    if not conn:
        return HTMLResponse(content="<p class='text-navy-500'>Database not configured</p>", status_code=503)

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    o.id, o.name, o.hq_city, o.hq_country, o.website, o.description,
                    gp.investment_philosophy, gp.team_size, gp.years_investing,
                    gp.spun_out_from, gp.notable_exits,
                    (SELECT COUNT(*) FROM funds f WHERE f.org_id = o.id) as fund_count
                FROM organizations o
                JOIN gp_profiles gp ON gp.org_id = o.id
                WHERE o.id = %s
            """, (gp_id,))
            gp = cur.fetchone()

            if not gp:
                return HTMLResponse(content="<p class='text-red-500'>GP not found</p>", status_code=404)

            # Get associated funds
            cur.execute("""
                SELECT id, name, status, vintage_year, target_size_mm, strategy
                FROM funds
                WHERE org_id = %s
                ORDER BY vintage_year DESC NULLS LAST
            """, (gp_id,))
            funds = cur.fetchall()

        return templates.TemplateResponse(
            "partials/gp_detail_modal.html",
            {"request": request, "gp": gp, "funds": funds}
        )
    finally:
        conn.close()


@app.post("/api/match/{match_id}/generate-pitch", response_class=HTMLResponse)
async def generate_pitch(
    request: Request,
    match_id: str,
    pitch_type: str = Form(default="email"),
    tone: str = Form(default="professional"),
):
    """Generate an AI pitch for a match (HTMX partial)."""
    if not is_valid_uuid(match_id):
        return HTMLResponse(
            content="<p class='text-red-500'>Invalid match ID</p>",
            status_code=400
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content="<p class='text-navy-500'>Database not configured</p>",
            status_code=503
        )

    try:
        # Fetch match data for pitch generation
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    m.id, m.score, m.explanation, m.talking_points, m.concerns,
                    o.name as lp_name, o.hq_city as lp_city,
                    lp.lp_type, lp.total_aum_bn,
                    f.name as fund_name, f.target_size_mm,
                    gp.name as gp_name
                FROM fund_lp_matches m
                JOIN organizations o ON o.id = m.lp_org_id
                LEFT JOIN lp_profiles lp ON lp.org_id = m.lp_org_id
                JOIN funds f ON f.id = m.fund_id
                JOIN organizations gp ON gp.id = f.org_id
                WHERE m.id = %s
            """, (match_id,))
            match = cur.fetchone()

        if not match:
            return HTMLResponse(
                content="<p class='text-navy-500'>Match not found</p>",
                status_code=404
            )

        # Build the prompt for pitch generation
        talking_points = match.get("talking_points") or []
        concerns = match.get("concerns") or []

        prompt = f"""Generate a {tone} {pitch_type} pitch for a GP reaching out to an LP.

GP: {match['gp_name']}
Fund: {match['fund_name']} (Target: ${match['target_size_mm']}M)

LP: {match['lp_name']}
Type: {match['lp_type'] or 'Institutional Investor'}
Location: {match['lp_city']}
AUM: ${match['total_aum_bn']}B

Match Score: {match['score']}%
Why they match: {match['explanation']}

Key talking points:
{chr(10).join(f'- {p}' for p in talking_points[:3])}

Potential concerns to address:
{chr(10).join(f'- {c}' for c in concerns[:2])}

Generate a compelling {pitch_type} that:
1. Opens with a personalized hook relevant to the LP
2. Briefly introduces the fund and its differentiation
3. References why this LP is a good fit
4. Includes a clear call to action
5. Keeps it concise (under 200 words for email, under 100 for summary)

Output only the {pitch_type} content, no preamble."""

        # Try to generate with Ollama (local dev) or return mock
        settings = get_settings()
        pitch_content = None

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json={
                        "model": settings.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                    }
                )
                if response.status_code == 200:
                    result = response.json()
                    pitch_content = result.get("response", "").strip()
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")

        # Fallback to mock pitch if Ollama unavailable
        if not pitch_content:
            if pitch_type == "email":
                pitch_content = f"""Subject: {match['fund_name']} - Investment Opportunity Aligned with {match['lp_name']}'s Strategy

Dear {match['lp_name']} Investment Team,

I hope this message finds you well. I'm reaching out from {match['gp_name']} regarding our {match['fund_name']}, which I believe aligns exceptionally well with your investment mandate.

{match['explanation']}

Our fund targets ${match['target_size_mm']}M and focuses on opportunities that match your portfolio strategy. {talking_points[0] if talking_points else ''}

I would welcome the opportunity to schedule a brief call to discuss how {match['fund_name']} might complement your portfolio.

Best regards,
{match['gp_name']} Team"""
            else:
                pitch_content = f"""{match['fund_name']} presents a compelling opportunity for {match['lp_name']}.

{match['explanation']}

Key highlights:
• Target fund size: ${match['target_size_mm']}M
• {talking_points[0] if talking_points else 'Strong alignment with LP mandate'}
• {talking_points[1] if len(talking_points) > 1 else 'Experienced management team'}

Match score: {match['score']}%"""

        return templates.TemplateResponse(
            request,
            "partials/pitch_result.html",
            {
                "match": match,
                "pitch_type": pitch_type,
                "tone": tone,
                "pitch_content": pitch_content,
            },
        )
    finally:
        conn.close()


# =============================================================================
# Shortlist Endpoints
# =============================================================================


def get_user_shortlist(user_id: str) -> list[ShortlistItem]:
    """Get the shortlist for a user.

    Args:
        user_id: The user's unique identifier.

    Returns:
        List of ShortlistItem objects for this user.
    """
    return _shortlists.get(user_id, [])


def add_to_shortlist(user_id: str, item: ShortlistItem) -> ShortlistItem:
    """Add an LP to a user's shortlist.

    Args:
        user_id: The user's unique identifier.
        item: The ShortlistItem to add.

    Returns:
        The added ShortlistItem with timestamp set.

    Raises:
        ValueError: If LP is already in shortlist.
    """
    from datetime import datetime

    if user_id not in _shortlists:
        _shortlists[user_id] = []

    # Check if already exists
    for existing in _shortlists[user_id]:
        if existing.lp_id == item.lp_id and existing.fund_id == item.fund_id:
            raise ValueError("LP already in shortlist")

    # Set timestamp
    item.added_at = datetime.now(UTC).isoformat()
    _shortlists[user_id].append(item)
    return item


def remove_from_shortlist(user_id: str, lp_id: str, fund_id: str | None = None) -> bool:
    """Remove an LP from a user's shortlist.

    Args:
        user_id: The user's unique identifier.
        lp_id: The LP organization ID to remove.
        fund_id: Optional fund context to match.

    Returns:
        True if item was removed, False if not found.
    """
    if user_id not in _shortlists:
        return False

    original_len = len(_shortlists[user_id])
    _shortlists[user_id] = [
        item
        for item in _shortlists[user_id]
        if not (item.lp_id == lp_id and item.fund_id == fund_id)
    ]
    return len(_shortlists[user_id]) < original_len


def update_shortlist_item(
    user_id: str, lp_id: str, updates: ShortlistUpdateRequest
) -> ShortlistItem | None:
    """Update a shortlist item's notes or priority.

    Args:
        user_id: The user's unique identifier.
        lp_id: The LP organization ID to update.
        updates: The fields to update.

    Returns:
        Updated ShortlistItem or None if not found.
    """
    if user_id not in _shortlists:
        return None

    for item in _shortlists[user_id]:
        if item.lp_id == lp_id:
            if updates.notes is not None:
                item.notes = updates.notes
            if updates.priority is not None:
                item.priority = updates.priority
            return item
    return None


def is_in_shortlist(user_id: str, lp_id: str) -> bool:
    """Check if an LP is in the user's shortlist.

    Args:
        user_id: The user's unique identifier.
        lp_id: The LP organization ID to check.

    Returns:
        True if LP is in shortlist, False otherwise.
    """
    if user_id not in _shortlists:
        return False
    return any(item.lp_id == lp_id for item in _shortlists[user_id])


def clear_user_shortlist(user_id: str) -> int:
    """Clear all items from a user's shortlist.

    Args:
        user_id: The user's unique identifier.

    Returns:
        Number of items that were cleared.
    """
    if user_id not in _shortlists:
        return 0
    count = len(_shortlists[user_id])
    _shortlists[user_id] = []
    return count


@app.get("/shortlist", response_class=HTMLResponse, response_model=None)
async def shortlist_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Shortlist page showing saved LPs.

    Displays the user's shortlisted LPs with their details,
    notes, and priority levels.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    shortlist = get_user_shortlist(user["id"])

    # Enrich shortlist items with LP details from database
    enriched_items = []
    conn = get_db()

    if conn and shortlist:
        try:
            with conn.cursor() as cur:
                for item in shortlist:
                    if is_valid_uuid(item.lp_id):
                        cur.execute(
                            """
                            SELECT o.id, o.name, lp.lp_type, o.hq_city, o.hq_country,
                                   lp.total_aum_bn, lp.pe_allocation_pct,
                                   lp.check_size_min_mm, lp.check_size_max_mm
                            FROM organizations o
                            LEFT JOIN lp_profiles lp ON lp.org_id = o.id
                            WHERE o.id = %s AND o.is_lp = TRUE
                            """,
                            (item.lp_id,),
                        )
                        lp_data = cur.fetchone()
                        if lp_data:
                            enriched_items.append(
                                {
                                    "item": item,
                                    "lp": lp_data,
                                }
                            )
        except psycopg.Error as e:
            logger.error(f"Database error fetching shortlist LPs: {e}")
        finally:
            conn.close()
    elif shortlist:
        # No database - just show basic info
        for item in shortlist:
            enriched_items.append(
                {
                    "item": item,
                    "lp": {"id": item.lp_id, "name": f"LP {item.lp_id[:8]}..."},
                }
            )

    # Calculate stats
    stats = {
        "total": len(shortlist),
        "high_priority": sum(1 for item in shortlist if item.priority == 1),
        "with_notes": sum(1 for item in shortlist if item.notes),
    }

    return templates.TemplateResponse(
        request,
        "pages/shortlist.html",
        {
            "title": "Shortlist - LPxGP",
            "user": user,
            "items": enriched_items,
            "stats": stats,
        },
    )


@app.post("/api/shortlist", response_class=JSONResponse)
async def api_add_to_shortlist(
    request: Request,
    body: ShortlistAddRequest,
) -> JSONResponse:
    """Add an LP to the user's shortlist.

    Args:
        request: FastAPI request object.
        body: Shortlist add request with lp_id and optional notes/priority.

    Returns:
        JSON response with success status and the added item.
    """
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"},
        )

    if not body.lp_id or not is_valid_uuid(body.lp_id):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid LP ID"},
        )

    try:
        item = ShortlistItem(
            lp_id=body.lp_id,
            fund_id=body.fund_id,
            notes=body.notes,
            priority=body.priority,
        )
        added_item = add_to_shortlist(user["id"], item)
        return JSONResponse(
            status_code=201,
            content={
                "success": True,
                "message": "LP added to shortlist",
                "item": added_item.model_dump(),
            },
        )
    except ValueError as e:
        return JSONResponse(
            status_code=409,
            content={"error": str(e)},
        )


@app.delete("/api/shortlist/{lp_id}", response_class=JSONResponse)
async def api_remove_from_shortlist(
    request: Request,
    lp_id: str,
) -> JSONResponse:
    """Remove an LP from the user's shortlist.

    Args:
        request: FastAPI request object.
        lp_id: The LP organization ID to remove.

    Returns:
        JSON response with success status.
    """
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"},
        )

    if not is_valid_uuid(lp_id):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid LP ID"},
        )

    removed = remove_from_shortlist(user["id"], lp_id)
    if removed:
        return JSONResponse(
            content={"success": True, "message": "LP removed from shortlist"},
        )
    else:
        return JSONResponse(
            status_code=404,
            content={"error": "LP not found in shortlist"},
        )


@app.patch("/api/shortlist/{lp_id}", response_class=JSONResponse)
async def api_update_shortlist_item(
    request: Request,
    lp_id: str,
    body: ShortlistUpdateRequest,
) -> JSONResponse:
    """Update a shortlist item's notes or priority.

    Args:
        request: FastAPI request object.
        lp_id: The LP organization ID to update.
        body: Update request with optional notes and priority.

    Returns:
        JSON response with updated item.
    """
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"},
        )

    if not is_valid_uuid(lp_id):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid LP ID"},
        )

    updated = update_shortlist_item(user["id"], lp_id, body)
    if updated:
        return JSONResponse(
            content={
                "success": True,
                "message": "Shortlist item updated",
                "item": updated.model_dump(),
            },
        )
    else:
        return JSONResponse(
            status_code=404,
            content={"error": "LP not found in shortlist"},
        )


@app.get("/api/shortlist", response_class=JSONResponse)
async def api_get_shortlist(request: Request) -> JSONResponse:
    """Get the current user's shortlist.

    Args:
        request: FastAPI request object.

    Returns:
        JSON response with list of shortlisted LPs.
    """
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"},
        )

    shortlist = get_user_shortlist(user["id"])
    return JSONResponse(
        content={
            "success": True,
            "count": len(shortlist),
            "items": [item.model_dump() for item in shortlist],
        },
    )


@app.get("/api/shortlist/check/{lp_id}", response_class=JSONResponse)
async def api_check_shortlist(request: Request, lp_id: str) -> JSONResponse:
    """Check if an LP is in the user's shortlist.

    Args:
        request: FastAPI request object.
        lp_id: The LP organization ID to check.

    Returns:
        JSON response with in_shortlist boolean.
    """
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"},
        )

    in_shortlist = is_in_shortlist(user["id"], lp_id)
    return JSONResponse(
        content={"in_shortlist": in_shortlist, "lp_id": lp_id},
    )


@app.delete("/api/shortlist", response_class=JSONResponse)
async def api_clear_shortlist(request: Request) -> JSONResponse:
    """Clear all items from the user's shortlist.

    Args:
        request: FastAPI request object.

    Returns:
        JSON response with count of cleared items.
    """
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"},
        )

    count = clear_user_shortlist(user["id"])
    return JSONResponse(
        content={
            "success": True,
            "message": f"Cleared {count} items from shortlist",
            "cleared_count": count,
        },
    )


# HTMX partials for shortlist buttons
@app.post("/api/shortlist/{lp_id}/toggle", response_class=HTMLResponse)
async def api_toggle_shortlist(request: Request, lp_id: str) -> HTMLResponse:
    """Toggle an LP's shortlist status and return updated button HTML.

    This endpoint is designed for HTMX to swap the shortlist button
    after a user clicks it.

    Args:
        request: FastAPI request object.
        lp_id: The LP organization ID to toggle.

    Returns:
        HTML partial with updated shortlist button.
    """
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(
            content='<span class="text-red-500 text-sm">Login required</span>',
            status_code=401,
        )

    if not is_valid_uuid(lp_id):
        return HTMLResponse(
            content='<span class="text-red-500 text-sm">Invalid LP</span>',
            status_code=400,
        )

    if is_in_shortlist(user["id"], lp_id):
        # Remove from shortlist
        remove_from_shortlist(user["id"], lp_id)
        is_saved = False
    else:
        # Add to shortlist
        item = ShortlistItem(lp_id=lp_id)
        try:
            add_to_shortlist(user["id"], item)
            is_saved = True
        except ValueError:
            is_saved = True  # Already exists

    # Return updated button HTML
    if is_saved:
        button_html = f'''
        <button hx-post="/api/shortlist/{lp_id}/toggle"
                hx-swap="outerHTML"
                class="flex items-center gap-1 text-sm text-gold hover:text-gold-600"
                title="Remove from shortlist">
            <svg class="w-4 h-4 fill-current" viewBox="0 0 24 24">
                <path d="M12 21.35l-1.45-1.32C5.4 15.36 2 12.28 2 8.5 2 5.42 4.42 3 7.5 3c1.74 0 3.41.81 4.5 2.09C13.09 3.81 14.76 3 16.5 3 19.58 3 22 5.42 22 8.5c0 3.78-3.4 6.86-8.55 11.54L12 21.35z"/>
            </svg>
            Saved
        </button>
        '''
    else:
        button_html = f'''
        <button hx-post="/api/shortlist/{lp_id}/toggle"
                hx-swap="outerHTML"
                class="flex items-center gap-1 text-sm text-navy-500 hover:text-gold"
                title="Add to shortlist">
            <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                      d="M4.318 6.318a4.5 4.5 0 000 6.364L12 20.364l7.682-7.682a4.5 4.5 0 00-6.364-6.364L12 7.636l-1.318-1.318a4.5 4.5 0 00-6.364 0z"/>
            </svg>
            Save
        </button>
        '''

    return HTMLResponse(content=button_html.strip())


# =============================================================================
# User Preferences Endpoints
# =============================================================================


@app.get("/api/settings/preferences", response_class=JSONResponse)
async def api_get_preferences(request: Request) -> JSONResponse:
    """Get current user's preferences.

    Args:
        request: FastAPI request object.

    Returns:
        JSON response with user preferences.
    """
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"},
        )

    preferences = get_user_preferences(user["id"])
    return JSONResponse(
        content={
            "success": True,
            "preferences": preferences.model_dump(),
        },
    )


@app.put("/api/settings/preferences", response_class=JSONResponse)
async def api_update_preferences(
    request: Request,
    body: UserPreferences,
) -> JSONResponse:
    """Update user preferences.

    Args:
        request: FastAPI request object.
        body: New preferences.

    Returns:
        JSON response with updated preferences.
    """
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"},
        )

    updated = update_user_preferences(user["id"], body)
    return JSONResponse(
        content={
            "success": True,
            "message": "Preferences updated",
            "preferences": updated.model_dump(),
        },
    )


@app.post("/api/settings/preferences/toggle/{pref_name}", response_class=HTMLResponse)
async def api_toggle_preference(
    request: Request,
    pref_name: str,
) -> HTMLResponse:
    """Toggle a single preference setting via HTMX.

    Args:
        request: FastAPI request object.
        pref_name: The preference to toggle (email_new_matches, etc.).

    Returns:
        HTML partial with updated checkbox.
    """
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(
            content='<span class="text-red-500 text-sm">Login required</span>',
            status_code=401,
        )

    valid_prefs = ["email_new_matches", "email_weekly_summary", "email_marketing"]
    if pref_name not in valid_prefs:
        return HTMLResponse(
            content='<span class="text-red-500 text-sm">Invalid preference</span>',
            status_code=400,
        )

    preferences = get_user_preferences(user["id"])
    current_value = getattr(preferences, pref_name)
    new_value = not current_value
    setattr(preferences, pref_name, new_value)
    update_user_preferences(user["id"], preferences)

    # Return updated checkbox HTML
    checked = "checked" if new_value else ""
    checkbox_html = f'''
    <input type="checkbox" {checked}
           hx-post="/api/settings/preferences/toggle/{pref_name}"
           hx-swap="outerHTML"
           class="rounded border-navy-300 text-gold focus:ring-gold">
    '''

    return HTMLResponse(content=checkbox_html.strip())


# =============================================================================
# Admin Dashboard Endpoints
# =============================================================================


def is_admin(user: auth.CurrentUser | None) -> bool:
    """Check if user has admin role.

    Args:
        user: The current user or None.

    Returns:
        True if user is admin, False otherwise.
    """
    if not user:
        return False
    return user.get("role") == "admin"


def can_manage_data(user: auth.CurrentUser | None) -> bool:
    """Check if user can manage LP/Company data.

    Allowed roles: admin, fa (fund advisor), gp.
    LP users cannot manage data.

    Args:
        user: The current user or None.

    Returns:
        True if user has data management permissions, False otherwise.
    """
    if not user:
        return False
    return user.get("role") in ("admin", "fa", "gp")


@app.get("/admin", response_class=HTMLResponse, response_model=None)
async def admin_dashboard(request: Request) -> HTMLResponse | RedirectResponse:
    """Admin dashboard showing platform overview.

    Requires admin role. Shows platform stats, pending actions,
    and system health.

    Args:
        request: FastAPI request object.

    Returns:
        Admin dashboard HTML or redirect to login/dashboard.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not is_admin(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    # Platform stats
    stats = {
        "companies": 0,
        "users": 0,
        "lps": 0,
        "matches": 0,
    }

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM organizations WHERE is_gp = TRUE")
                result = cur.fetchone()
                stats["companies"] = result["count"] if result else 0

                cur.execute("SELECT COUNT(*) FROM organizations WHERE is_lp = TRUE")
                result = cur.fetchone()
                stats["lps"] = result["count"] if result else 0

                cur.execute("SELECT COUNT(*) FROM fund_lp_matches")
                result = cur.fetchone()
                stats["matches"] = result["count"] if result else 0
        except Exception:
            pass
        finally:
            conn.close()

    # Count registered users (from in-memory store)
    stats["users"] = len(auth._mock_users)

    # System health checks
    health = {
        "database": conn is not None,
        "auth": True,  # Always true if we got here
    }

    return templates.TemplateResponse(
        request,
        "pages/admin/dashboard.html",
        {
            "title": "Admin Dashboard - LPxGP",
            "user": user,
            "stats": stats,
            "health": health,
        },
    )


@app.get("/admin/users", response_class=HTMLResponse, response_model=None)
async def admin_users_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Admin users management page.

    Requires admin role. Shows list of registered users.

    Args:
        request: FastAPI request object.

    Returns:
        Admin users page HTML or redirect.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not is_admin(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    # Get users from in-memory store (masked passwords)
    users = []
    for email, user_data in auth._mock_users.items():
        users.append({
            "id": user_data["id"],
            "email": email,
            "name": user_data["name"],
            "role": user_data["role"],
        })

    return templates.TemplateResponse(
        request,
        "pages/admin/users.html",
        {
            "title": "Users - Admin - LPxGP",
            "user": user,
            "users": users,
            "total_users": len(users),
        },
    )


@app.get("/admin/health", response_class=HTMLResponse, response_model=None)
async def admin_health_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Admin system health page.

    Requires admin role. Shows detailed system health information.

    Args:
        request: FastAPI request object.

    Returns:
        Admin health page HTML or redirect.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not is_admin(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    settings = get_settings()

    # Detailed health checks
    health_checks = []

    # Database check
    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            health_checks.append({
                "name": "Database",
                "status": "healthy",
                "message": "Connection successful",
            })
        except Exception as e:
            health_checks.append({
                "name": "Database",
                "status": "unhealthy",
                "message": str(e),
            })
        finally:
            conn.close()
    else:
        health_checks.append({
            "name": "Database",
            "status": "unconfigured",
            "message": "Database not configured",
        })

    # Auth check
    health_checks.append({
        "name": "Authentication",
        "status": "healthy",
        "message": f"{len(auth._mock_users)} users registered",
    })

    # Environment info
    health_checks.append({
        "name": "Environment",
        "status": "info",
        "message": settings.environment,
    })

    return templates.TemplateResponse(
        request,
        "pages/admin/health.html",
        {
            "title": "System Health - Admin - LPxGP",
            "user": user,
            "health_checks": health_checks,
        },
    )


@app.get("/api/admin/stats", response_class=JSONResponse)
async def api_admin_stats(request: Request) -> JSONResponse:
    """Get platform statistics for admin dashboard.

    Args:
        request: FastAPI request object.

    Returns:
        JSON response with platform stats.
    """
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"},
        )

    if not is_admin(user):
        return JSONResponse(
            status_code=403,
            content={"error": "Admin access required"},
        )

    stats = {
        "companies": 0,
        "users": len(auth._mock_users),
        "lps": 0,
        "matches": 0,
    }

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM organizations WHERE is_gp = TRUE")
                result = cur.fetchone()
                stats["companies"] = result["count"] if result else 0

                cur.execute("SELECT COUNT(*) FROM organizations WHERE is_lp = TRUE")
                result = cur.fetchone()
                stats["lps"] = result["count"] if result else 0

                cur.execute("SELECT COUNT(*) FROM fund_lp_matches")
                result = cur.fetchone()
                stats["matches"] = result["count"] if result else 0
        except Exception:
            pass
        finally:
            conn.close()

    return JSONResponse(content={"success": True, "stats": stats})


# -----------------------------------------------------------------------------
# LP & Company CRUD Endpoints (accessible by admin, fa, gp)
# -----------------------------------------------------------------------------


@app.get("/admin/lps", response_class=HTMLResponse, response_model=None)
async def admin_lps_page(
    request: Request,
    page: int = 1,
    q: str | None = None,
    type: str | None = None,
) -> HTMLResponse | RedirectResponse:
    """LP database management page.

    Accessible by admin, fa, and gp roles. Shows list of LPs
    with search and filtering.

    Args:
        request: FastAPI request object.
        page: Page number for pagination.
        q: Search query string.
        type: Filter by LP type.

    Returns:
        LP list page HTML or redirect.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not can_manage_data(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    # Pagination settings
    per_page = 25

    # Mock LP data for demo
    mock_lps: list[dict[str, Any]] = [
        {
            "id": "lp-001",
            "name": "CalPERS",
            "description": "California Public Employees' Retirement System",
            "lp_type": "pension",
            "location": "Sacramento, CA",
            "total_aum_bn": 450,
            "is_active": True,
        },
        {
            "id": "lp-002",
            "name": "Yale Endowment",
            "description": "Yale University Investments Office",
            "lp_type": "endowment",
            "location": "New Haven, CT",
            "total_aum_bn": 41,
            "is_active": True,
        },
        {
            "id": "lp-003",
            "name": "Smith Family Office",
            "description": "Multi-family office",
            "lp_type": "family_office",
            "location": "New York, NY",
            "total_aum_bn": 2,
            "is_active": True,
        },
        {
            "id": "lp-004",
            "name": "Ontario Teachers'",
            "description": "Ontario Teachers' Pension Plan",
            "lp_type": "pension",
            "location": "Toronto, Canada",
            "total_aum_bn": 250,
            "is_active": True,
        },
        {
            "id": "lp-005",
            "name": "GIC",
            "description": "Government of Singapore Investment Corporation",
            "lp_type": "sovereign_wealth",
            "location": "Singapore",
            "total_aum_bn": 690,
            "is_active": True,
        },
    ]

    # Try to get LPs from database
    lps: list[dict[str, Any]] = []
    stats: dict[str, int] = {"total": 0, "pensions": 0, "endowments": 0, "family_offices": 0, "other": 0}

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                # Build query with filters
                query = """
                    SELECT lp.id, o.name, o.description, lp.lp_type,
                           CONCAT(o.hq_city, ', ', o.hq_country) as location,
                           lp.total_aum_bn, lp.is_active
                    FROM lp_profiles lp
                    JOIN organizations o ON lp.org_id = o.id
                    WHERE 1=1
                """
                params: list = []

                if q:
                    query += " AND o.name ILIKE %s"
                    params.append(f"%{q}%")

                if type:
                    query += " AND lp.lp_type = %s"
                    params.append(type)

                query += " ORDER BY o.name LIMIT %s OFFSET %s"
                params.extend([per_page, (page - 1) * per_page])

                cur.execute(query, params)
                rows = cur.fetchall()
                lps = [dict(row) for row in rows]

                # Get stats
                cur.execute("SELECT COUNT(*) FROM lp_profiles")
                result = cur.fetchone()
                stats["total"] = result["count"] if result else 0

                cur.execute("SELECT COUNT(*) FROM lp_profiles WHERE lp_type = 'pension'")
                result = cur.fetchone()
                stats["pensions"] = result["count"] if result else 0

                cur.execute("SELECT COUNT(*) FROM lp_profiles WHERE lp_type = 'endowment'")
                result = cur.fetchone()
                stats["endowments"] = result["count"] if result else 0

                cur.execute("SELECT COUNT(*) FROM lp_profiles WHERE lp_type = 'family_office'")
                result = cur.fetchone()
                stats["family_offices"] = result["count"] if result else 0

                cur.execute("SELECT COUNT(*) FROM lp_profiles WHERE lp_type NOT IN ('pension', 'endowment', 'family_office')")
                result = cur.fetchone()
                stats["other"] = result["count"] if result else 0

        except Exception as e:
            logger.warning(f"Failed to fetch LPs from database: {e}")
            lps = mock_lps
            stats = {"total": 5, "pensions": 2, "endowments": 1, "family_offices": 1, "other": 1}
        finally:
            conn.close()
    else:
        # Use mock data
        lps = mock_lps
        stats = {"total": 5, "pensions": 2, "endowments": 1, "family_offices": 1, "other": 1}

        # Apply filters to mock data
        if q:
            lps = [lp for lp in lps if q.lower() in lp["name"].lower()]
        if type:
            lps = [lp for lp in lps if lp["lp_type"] == type]

    total_pages = max(1, (stats["total"] + per_page - 1) // per_page)

    return templates.TemplateResponse(
        request,
        "pages/admin/lps.html",
        {
            "title": "LP Database - LPxGP",
            "user": user,
            "lps": lps,
            "stats": stats,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "search_query": q,
            "filter_type": type,
        },
    )


@app.get("/admin/lps/new", response_class=HTMLResponse, response_model=None)
async def admin_lp_new_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Create new LP page.

    Accessible by admin, fa, and gp roles.

    Args:
        request: FastAPI request object.

    Returns:
        New LP form HTML or redirect.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not can_manage_data(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        request,
        "pages/admin/lp-detail.html",
        {
            "title": "Add New LP - LPxGP",
            "user": user,
            "lp": None,
        },
    )


@app.get("/admin/lps/{lp_id}", response_class=HTMLResponse, response_model=None)
async def admin_lp_detail_page(request: Request, lp_id: str) -> HTMLResponse | RedirectResponse:
    """LP detail/edit page.

    Accessible by admin, fa, and gp roles.

    Args:
        request: FastAPI request object.
        lp_id: LP profile ID.

    Returns:
        LP edit form HTML or redirect.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not can_manage_data(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    # Mock LP data for demo
    mock_lps = {
        "lp-001": {
            "id": "lp-001",
            "name": "CalPERS",
            "description": "California Public Employees' Retirement System",
            "lp_type": "pension",
            "location": "Sacramento, CA, USA",
            "total_aum_bn": 450,
            "pe_allocation": "13%",
            "typical_commitment_min_m": 100,
            "typical_commitment_max_m": 500,
            "preferred_strategies": ["buyout", "growth_equity", "infrastructure"],
            "preferred_geographies": ["North America", "Europe"],
            "investment_mandate": "CalPERS maintains a diversified private equity portfolio with allocations across buyout, growth equity, and venture capital strategies.",
            "is_active": True,
            "updated_at": "2 weeks ago",
        },
        "lp-002": {
            "id": "lp-002",
            "name": "Yale Endowment",
            "description": "Yale University Investments Office",
            "lp_type": "endowment",
            "location": "New Haven, CT, USA",
            "total_aum_bn": 41,
            "pe_allocation": "41%",
            "typical_commitment_min_m": 25,
            "typical_commitment_max_m": 150,
            "preferred_strategies": ["venture_capital", "buyout"],
            "preferred_geographies": ["Global"],
            "investment_mandate": "Pioneer of the endowment model with significant allocations to alternative investments.",
            "is_active": True,
            "updated_at": "1 week ago",
        },
    }

    lp = None
    conn = get_db()
    if conn:
        try:
            from uuid import UUID
            UUID(lp_id)  # Validate UUID format

            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT lp.id, o.name, o.description, lp.lp_type,
                           CONCAT(o.hq_city, ', ', o.hq_country) as location,
                           lp.total_aum_bn, lp.typical_commitment_min_m,
                           lp.typical_commitment_max_m, lp.preferred_strategies,
                           lp.preferred_geographies, lp.investment_mandate,
                           lp.is_active, lp.updated_at
                    FROM lp_profiles lp
                    JOIN organizations o ON lp.org_id = o.id
                    WHERE lp.id = %s
                    """,
                    [lp_id],
                )
                row = cur.fetchone()
                if row:
                    lp = dict(row)
        except ValueError:
            # Not a valid UUID, try mock data
            lp = mock_lps.get(lp_id)
        except Exception as e:
            logger.warning(f"Failed to fetch LP from database: {e}")
            lp = mock_lps.get(lp_id)
        finally:
            conn.close()
    else:
        lp = mock_lps.get(lp_id)

    if not lp:
        return RedirectResponse(url="/admin/lps", status_code=303)

    return templates.TemplateResponse(
        request,
        "pages/admin/lp-detail.html",
        {
            "title": f"Edit {lp['name']} - LPxGP",
            "user": user,
            "lp": lp,
        },
    )


@app.post("/admin/lps/new", response_class=HTMLResponse, response_model=None)
async def admin_lp_create(request: Request) -> HTMLResponse | RedirectResponse:
    """Create new LP.

    Accessible by admin, fa, and gp roles.

    Args:
        request: FastAPI request object.

    Returns:
        Redirect to LP list or error.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not can_manage_data(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    form = await request.form()
    name = str(form.get("name", "")).strip()
    lp_type = str(form.get("lp_type", "")).strip()

    if not name or not lp_type:
        # Return form with error
        return templates.TemplateResponse(
            request,
            "pages/admin/lp-detail.html",
            {
                "title": "Add New LP - LPxGP",
                "user": user,
                "lp": None,
                "error": "Name and Type are required",
            },
        )

    # For now, just redirect back to list (database insert would go here)
    logger.info(f"Would create LP: {name} ({lp_type})")
    return RedirectResponse(url="/admin/lps", status_code=303)


@app.post("/admin/lps/{lp_id}", response_class=HTMLResponse, response_model=None)
async def admin_lp_update(request: Request, lp_id: str) -> HTMLResponse | RedirectResponse:
    """Update LP.

    Accessible by admin, fa, and gp roles.

    Args:
        request: FastAPI request object.
        lp_id: LP profile ID.

    Returns:
        Redirect to LP list or error.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not can_manage_data(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    form = await request.form()
    name = str(form.get("name", "")).strip()
    lp_type = str(form.get("lp_type", "")).strip()

    if not name or not lp_type:
        return RedirectResponse(url=f"/admin/lps/{lp_id}", status_code=303)

    # For now, just redirect back to list (database update would go here)
    logger.info(f"Would update LP {lp_id}: {name} ({lp_type})")
    return RedirectResponse(url="/admin/lps", status_code=303)


@app.delete("/admin/lps/{lp_id}", response_model=None)
async def admin_lp_delete(request: Request, lp_id: str) -> JSONResponse | RedirectResponse:
    """Delete LP.

    Accessible by admin, fa, and gp roles.

    Args:
        request: FastAPI request object.
        lp_id: LP profile ID.

    Returns:
        JSON success response or redirect.
    """
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(content={"error": "Not authenticated"}, status_code=401)

    if not can_manage_data(user):
        return JSONResponse(content={"error": "Insufficient permissions"}, status_code=403)

    # For now, just log (database delete would go here)
    logger.info(f"Would delete LP {lp_id}")
    return JSONResponse(content={"success": True})


@app.get("/admin/companies", response_class=HTMLResponse, response_model=None)
async def admin_companies_page(
    request: Request,
    page: int = 1,
    q: str | None = None,
    status: str | None = None,
) -> HTMLResponse | RedirectResponse:
    """Companies management page.

    Accessible by admin, fa, and gp roles. Shows list of GP organizations.

    Args:
        request: FastAPI request object.
        page: Page number for pagination.
        q: Search query string.
        status: Filter by status (active/pending/inactive).

    Returns:
        Companies list page HTML or redirect.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not can_manage_data(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    # Pagination settings
    per_page = 25

    # Mock company data for demo
    mock_companies: list[dict[str, Any]] = [
        {
            "id": "org-001",
            "name": "Acme Capital",
            "initials": "AC",
            "color": "navy",
            "type": "Private Equity",
            "admin_email": "john@acmecapital.com",
            "user_count": 4,
            "fund_count": 3,
            "status": "active",
            "created_at": "Dec 1, 2024",
        },
        {
            "id": "org-002",
            "name": "Beta Ventures",
            "initials": "BV",
            "color": "green",
            "type": "Venture Capital",
            "admin_email": None,
            "user_count": 0,
            "fund_count": 0,
            "status": "pending",
            "created_at": "Dec 18, 2024",
        },
        {
            "id": "org-003",
            "name": "Gamma Partners",
            "initials": "GP",
            "color": "purple",
            "type": "Growth Equity",
            "admin_email": "alex@gammapartners.com",
            "user_count": 2,
            "fund_count": 1,
            "status": "inactive",
            "created_at": "Oct 15, 2024",
        },
        {
            "id": "org-004",
            "name": "Delta Capital",
            "initials": "DC",
            "color": "blue",
            "type": "Private Equity",
            "admin_email": "sarah@deltacap.com",
            "user_count": 6,
            "fund_count": 4,
            "status": "active",
            "created_at": "Sep 20, 2024",
        },
    ]

    companies: list[dict[str, Any]] = []
    total_companies = 0

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                # Build query with filters
                query = """
                    SELECT o.id, o.name, o.description,
                           UPPER(LEFT(o.name, 1)) || UPPER(LEFT(SPLIT_PART(o.name, ' ', 2), 1)) as initials,
                           o.created_at
                    FROM organizations o
                    WHERE o.is_gp = TRUE
                """
                params: list = []

                if q:
                    query += " AND o.name ILIKE %s"
                    params.append(f"%{q}%")

                query += " ORDER BY o.name LIMIT %s OFFSET %s"
                params.extend([per_page, (page - 1) * per_page])

                cur.execute(query, params)
                rows = cur.fetchall()
                for row in rows:
                    company = dict(row)
                    company["color"] = "navy"
                    company["type"] = "Private Equity"
                    company["admin_email"] = None
                    company["user_count"] = 0
                    company["fund_count"] = 0
                    company["status"] = "active"
                    company["created_at"] = company["created_at"].strftime("%b %d, %Y") if company.get("created_at") else "Unknown"
                    companies.append(company)

                # Get total count
                cur.execute("SELECT COUNT(*) FROM organizations WHERE is_gp = TRUE")
                result = cur.fetchone()
                total_companies = result["count"] if result else 0

        except Exception as e:
            logger.warning(f"Failed to fetch companies from database: {e}")
            companies = mock_companies
            total_companies = len(mock_companies)
        finally:
            conn.close()
    else:
        # Use mock data
        companies = mock_companies
        total_companies = len(mock_companies)

        # Apply filters to mock data
        if q:
            companies = [c for c in companies if q.lower() in c["name"].lower()]
        if status:
            companies = [c for c in companies if c["status"] == status]
        total_companies = len(companies)

    total_pages = max(1, (total_companies + per_page - 1) // per_page)

    return templates.TemplateResponse(
        request,
        "pages/admin/companies.html",
        {
            "title": "Companies - LPxGP",
            "user": user,
            "companies": companies,
            "total_companies": total_companies,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "search_query": q,
            "filter_status": status,
        },
    )


@app.get("/admin/companies/{org_id}", response_class=HTMLResponse, response_model=None)
async def admin_company_detail_page(request: Request, org_id: str) -> HTMLResponse | RedirectResponse:
    """Company detail page.

    Accessible by admin, fa, and gp roles.

    Args:
        request: FastAPI request object.
        org_id: Organization ID.

    Returns:
        Company detail page HTML or redirect.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not can_manage_data(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    # Mock company data for demo
    mock_companies: dict[str, dict[str, Any]] = {
        "org-001": {
            "id": "org-001",
            "name": "Acme Capital",
            "initials": "AC",
            "color": "navy",
            "type": "Private Equity - Growth",
            "location": "San Francisco, CA",
            "website": "acmecapital.com",
            "status": "active",
            "created_at": "December 1, 2024",
            "user_count": 4,
            "fund_count": 3,
            "match_count": 127,
            "last_login": "2 hours ago",
            "searches_30d": 127,
            "pitches_30d": 23,
            "users": [
                {"name": "John Partner", "email": "john@acmecapital.com", "initials": "JP", "color": "navy", "role": "admin", "status": "Active"},
                {"name": "Sarah Johnson", "email": "sarah@acmecapital.com", "initials": "SJ", "color": "green", "role": "member", "status": "Active"},
                {"name": "Mike Chen", "email": "mike@acmecapital.com", "initials": "MC", "color": "purple", "role": "member", "status": "Active"},
            ],
            "funds": [
                {"name": "Growth Fund III", "target": 500, "status": "Raising", "matches": 45},
                {"name": "Growth Fund II", "target": 350, "status": "Investing", "matches": 52},
                {"name": "Growth Fund I", "target": 200, "status": "Harvesting", "matches": 30},
            ],
        },
        "org-002": {
            "id": "org-002",
            "name": "Beta Ventures",
            "initials": "BV",
            "color": "green",
            "type": "Venture Capital",
            "location": None,
            "website": None,
            "status": "pending",
            "created_at": "December 18, 2024",
            "user_count": 0,
            "fund_count": 0,
            "match_count": 0,
            "last_login": "Never",
            "searches_30d": 0,
            "pitches_30d": 0,
            "users": [],
            "funds": [],
        },
    }

    company: dict[str, Any] | None = None
    conn = get_db()
    if conn:
        try:
            from uuid import UUID
            UUID(org_id)  # Validate UUID format

            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT o.id, o.name, o.description, o.website,
                           CONCAT(o.hq_city, ', ', o.hq_country) as location,
                           o.created_at
                    FROM organizations o
                    WHERE o.id = %s AND o.is_gp = TRUE
                    """,
                    [org_id],
                )
                row = cur.fetchone()
                if row:
                    company = dict(row)
                    company["initials"] = company["name"][:2].upper() if company["name"] else "??"
                    company["color"] = "navy"
                    company["type"] = "Private Equity"
                    company["status"] = "active"
                    company["created_at"] = company["created_at"].strftime("%B %d, %Y") if company.get("created_at") else "Unknown"
                    company["user_count"] = 0
                    company["fund_count"] = 0
                    company["match_count"] = 0
                    company["last_login"] = "Unknown"
                    company["searches_30d"] = 0
                    company["pitches_30d"] = 0
                    company["users"] = []
                    company["funds"] = []
        except ValueError:
            # Not a valid UUID, try mock data
            company = mock_companies.get(org_id)
        except Exception as e:
            logger.warning(f"Failed to fetch company from database: {e}")
            company = mock_companies.get(org_id)
        finally:
            conn.close()
    else:
        company = mock_companies.get(org_id)

    if not company:
        return RedirectResponse(url="/admin/companies", status_code=303)

    return templates.TemplateResponse(
        request,
        "pages/admin/company-detail.html",
        {
            "title": f"{company['name']} - LPxGP",
            "user": user,
            "company": company,
        },
    )


@app.delete("/admin/companies/{org_id}", response_model=None)
async def admin_company_deactivate(request: Request, org_id: str) -> JSONResponse:
    """Deactivate a company.

    Accessible by admin, fa, and gp roles.

    Args:
        request: FastAPI request object.
        org_id: Organization ID.

    Returns:
        JSON success response.
    """
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(content={"error": "Not authenticated"}, status_code=401)

    if not can_manage_data(user):
        return JSONResponse(content={"error": "Insufficient permissions"}, status_code=403)

    # For now, just log (database update would go here)
    logger.info(f"Would deactivate company {org_id}")
    return JSONResponse(content={"success": True})


@app.get("/admin/people", response_class=HTMLResponse, response_model=None)
async def admin_people_page(
    request: Request,
    q: str | None = None,
    role: str | None = None,
    page: int = 1,
    per_page: int = 50,
) -> HTMLResponse | RedirectResponse:
    """Admin people management page.

    Lists all people in the market database with search and filters.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not can_manage_data(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    people: list[dict[str, Any]] = []
    stats = {"total": 0, "decision_makers": 0, "with_email": 0, "with_linkedin": 0}
    pagination = {"page": page, "per_page": per_page, "total": 0, "total_pages": 1}

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                # Build query
                where_clauses = []
                params: list[Any] = []

                if q:
                    where_clauses.append(
                        "(p.full_name ILIKE %s OR p.email ILIKE %s)"
                    )
                    params.extend([f"%{q}%", f"%{q}%"])

                if role == "decision_maker":
                    where_clauses.append("cp.is_decision_maker = TRUE")

                where_sql = (
                    "WHERE " + " AND ".join(where_clauses) if where_clauses else ""
                )

                # Get stats
                cur.execute("SELECT COUNT(*) as total FROM people")
                row = cur.fetchone()
                stats["total"] = row["total"] if row else 0

                cur.execute(
                    "SELECT COUNT(*) FROM company_people WHERE is_decision_maker = TRUE"
                )
                row = cur.fetchone()
                stats["decision_makers"] = row["count"] if row else 0

                cur.execute(
                    "SELECT COUNT(*) FROM people WHERE email IS NOT NULL AND email != ''"
                )
                row = cur.fetchone()
                stats["with_email"] = row["count"] if row else 0

                cur.execute(
                    "SELECT COUNT(*) FROM people WHERE linkedin_url IS NOT NULL"
                )
                row = cur.fetchone()
                stats["with_linkedin"] = row["count"] if row else 0

                # Get total count
                count_sql = f"""
                    SELECT COUNT(DISTINCT p.id) as total
                    FROM people p
                    LEFT JOIN company_people cp ON cp.person_id = p.id
                    {where_sql}
                """
                cur.execute(count_sql, params)
                row = cur.fetchone()
                pagination["total"] = row["total"] if row else 0
                pagination["total_pages"] = max(
                    1, (pagination["total"] + per_page - 1) // per_page
                )

                # Get people
                offset = (page - 1) * per_page
                query = f"""
                    SELECT DISTINCT
                        p.id, p.full_name, p.email, p.linkedin_url,
                        cp.title, cp.is_decision_maker,
                        o.name as company_name
                    FROM people p
                    LEFT JOIN company_people cp ON cp.person_id = p.id
                    LEFT JOIN organizations o ON o.id = cp.org_id
                    {where_sql}
                    ORDER BY p.full_name
                    LIMIT %s OFFSET %s
                """
                cur.execute(query, params + [per_page, offset])
                people = cur.fetchall()
        except Exception as e:
            logger.error(f"Admin people error: {e}")
        finally:
            conn.close()

    return templates.TemplateResponse(
        request,
        "pages/admin/people.html",
        {
            "user": user,
            "people": people,
            "stats": stats,
            "pagination": pagination,
            "search_query": q,
            "filter_role": role,
        },
    )


# =============================================================================
# PHASE 2: Match Feedback & Status APIs
# =============================================================================


@app.post("/api/match/{match_id}/feedback", response_class=HTMLResponse)
async def match_feedback(
    request: Request,
    match_id: str,
    feedback: str = Form(...),
    reason: str | None = Form(None),
) -> HTMLResponse:
    """Record feedback on a match (thumbs up/down/dismiss).

    Args:
        request: FastAPI request object.
        match_id: Match ID (fund_lp_match id).
        feedback: Feedback type (positive, negative, dismissed).
        reason: Optional reason for dismissal.

    Returns:
        HTML response with updated match card or success message.
    """
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="<div>Not authenticated</div>", status_code=401)

    if not is_valid_uuid(match_id):
        return HTMLResponse(
            content='<div class="text-red-500">Invalid match ID</div>',
            status_code=400,
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content='<div class="text-yellow-500">Database unavailable</div>',
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            # Update match with feedback
            cur.execute(
                """
                UPDATE fund_lp_matches
                SET
                    gp_feedback = %s,
                    gp_feedback_reason = %s,
                    gp_feedback_at = NOW()
                WHERE id = %s
                RETURNING id, score, gp_feedback
                """,
                (feedback, reason, match_id),
            )
            result = cur.fetchone()

            if not result:
                return HTMLResponse(
                    content='<div class="text-red-500">Match not found</div>',
                    status_code=404,
                )

            conn.commit()

            # Return updated feedback UI
            feedback_icons = {
                "positive": "👍",
                "negative": "👎",
                "dismissed": "❌",
            }
            icon = feedback_icons.get(feedback, "")

            return HTMLResponse(
                content=f"""
                <div class="flex items-center gap-2 text-sm text-navy-600">
                    <span>{icon}</span>
                    <span>Feedback recorded</span>
                </div>
                """,
            )
    except Exception as e:
        logger.error(f"Match feedback error: {e}")
        return HTMLResponse(
            content=f'<div class="text-red-500">Error: {e}</div>',
            status_code=500,
        )
    finally:
        conn.close()


@app.post("/api/match/{match_id}/status", response_class=HTMLResponse)
async def update_match_status(
    request: Request,
    match_id: str,
    stage: str = Form(...),
    notes: str | None = Form(None),
) -> HTMLResponse:
    """Update pipeline stage for a match.

    Args:
        request: FastAPI request object.
        match_id: Match ID.
        stage: Pipeline stage (new, contacted, meeting_scheduled, etc.).
        notes: Optional notes.

    Returns:
        HTML response with updated status badge.
    """
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="<div>Not authenticated</div>", status_code=401)

    if not is_valid_uuid(match_id):
        return HTMLResponse(
            content='<div class="text-red-500">Invalid match ID</div>',
            status_code=400,
        )

    valid_stages = [
        "new",
        "contacted",
        "meeting_scheduled",
        "meeting_held",
        "dd_in_progress",
        "committed",
        "passed",
    ]
    if stage not in valid_stages:
        return HTMLResponse(
            content=f'<div class="text-red-500">Invalid stage: {stage}</div>',
            status_code=400,
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content='<div class="text-yellow-500">Database unavailable</div>',
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            # Get fund_id and lp_org_id from match
            cur.execute(
                "SELECT fund_id, lp_org_id FROM fund_lp_matches WHERE id = %s",
                (match_id,),
            )
            match = cur.fetchone()
            if not match:
                return HTMLResponse(
                    content='<div class="text-red-500">Match not found</div>',
                    status_code=404,
                )

            # Upsert fund_lp_status
            cur.execute(
                """
                INSERT INTO fund_lp_status (fund_id, lp_org_id, pipeline_stage, notes)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (fund_id, lp_org_id)
                DO UPDATE SET
                    pipeline_stage = EXCLUDED.pipeline_stage,
                    notes = COALESCE(EXCLUDED.notes, fund_lp_status.notes),
                    updated_at = NOW()
                RETURNING pipeline_stage
                """,
                (match["fund_id"], match["lp_org_id"], stage, notes),
            )
            conn.commit()

            # Status badge styling
            stage_colors = {
                "new": "bg-gray-100 text-gray-700",
                "contacted": "bg-blue-100 text-blue-700",
                "meeting_scheduled": "bg-yellow-100 text-yellow-700",
                "meeting_held": "bg-purple-100 text-purple-700",
                "dd_in_progress": "bg-orange-100 text-orange-700",
                "committed": "bg-green-100 text-green-700",
                "passed": "bg-red-100 text-red-700",
            }
            color = stage_colors.get(stage, "bg-gray-100 text-gray-700")
            display = stage.replace("_", " ").title()

            return HTMLResponse(
                content=f"""
                <span class="px-2 py-1 text-xs rounded-full {color}">
                    {display}
                </span>
                """,
            )
    except Exception as e:
        logger.error(f"Match status update error: {e}")
        return HTMLResponse(
            content=f'<div class="text-red-500">Error: {e}</div>',
            status_code=500,
        )
    finally:
        conn.close()


@app.patch("/api/v1/pipeline/{fund_id}/{lp_id}", response_class=JSONResponse)
async def api_update_pipeline_stage(
    request: Request,
    fund_id: str,
    lp_id: str,
    body: PipelineStageUpdateRequest,
) -> JSONResponse:
    """Update pipeline stage for a fund-LP relationship.

    REST API endpoint for updating pipeline stage and logging activity.

    Args:
        request: FastAPI request object.
        fund_id: Fund ID.
        lp_id: LP organization ID.
        body: PipelineStageUpdateRequest with stage and optional notes.

    Returns:
        JSON response with updated status.
    """
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"},
        )

    if not is_valid_uuid(fund_id) or not is_valid_uuid(lp_id):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid fund ID or LP ID"},
        )

    if body.stage not in VALID_PIPELINE_STAGES:
        return JSONResponse(
            status_code=400,
            content={
                "error": f"Invalid stage: {body.stage}",
                "valid_stages": VALID_PIPELINE_STAGES,
            },
        )

    conn = get_db()
    if not conn:
        return JSONResponse(
            status_code=503,
            content={"error": "Database unavailable"},
        )

    try:
        with conn.cursor() as cur:
            # Upsert fund_lp_status
            cur.execute(
                """
                INSERT INTO fund_lp_status (fund_id, lp_org_id, pipeline_stage, notes)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (fund_id, lp_org_id)
                DO UPDATE SET
                    pipeline_stage = EXCLUDED.pipeline_stage,
                    notes = COALESCE(EXCLUDED.notes, fund_lp_status.notes),
                    updated_at = NOW()
                RETURNING id, pipeline_stage, notes, updated_at
                """,
                (fund_id, lp_id, body.stage, body.notes),
            )
            result = cur.fetchone()

            # Log the activity in outreach_events if match exists
            cur.execute(
                """
                SELECT id FROM fund_lp_matches
                WHERE fund_id = %s AND lp_org_id = %s
                """,
                (fund_id, lp_id),
            )
            match_row = cur.fetchone()

            if match_row:
                # Map pipeline stage to event type
                event_type_map = {
                    "gp_interested": "pitch_generated",
                    "gp_pursuing": "email_sent",
                    "lp_reviewing": "response_received",
                    "mutual_interest": "meeting_scheduled",
                    "in_diligence": "due_diligence_started",
                    "invested": "commitment_made",
                    "gp_passed": "commitment_declined",
                    "lp_passed": "commitment_declined",
                }
                event_type = event_type_map.get(body.stage)

                if event_type:
                    cur.execute(
                        """
                        INSERT INTO outreach_events
                        (match_id, event_type, event_date, notes)
                        VALUES (%s, %s, NOW(), %s)
                        """,
                        (match_row["id"], event_type, body.notes),
                    )

            conn.commit()

            return JSONResponse(
                content={
                    "success": True,
                    "fund_id": fund_id,
                    "lp_id": lp_id,
                    "stage": body.stage,
                    "notes": body.notes,
                    "updated_at": str(result["updated_at"]) if result else None,
                },
            )
    except Exception as e:
        logger.error(f"Pipeline stage update error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )
    finally:
        conn.close()


@app.get("/api/v1/pipeline/{fund_id}", response_class=JSONResponse)
async def api_get_pipeline_status(
    request: Request,
    fund_id: str,
) -> JSONResponse:
    """Get pipeline status for all LPs for a fund.

    Args:
        request: FastAPI request object.
        fund_id: Fund ID.

    Returns:
        JSON response with pipeline status for all LPs.
    """
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"},
        )

    if not is_valid_uuid(fund_id):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid fund ID"},
        )

    conn = get_db()
    if not conn:
        return JSONResponse(
            status_code=503,
            content={"error": "Database unavailable"},
        )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    s.lp_org_id,
                    o.name as lp_name,
                    s.pipeline_stage,
                    s.gp_interest,
                    s.lp_interest,
                    s.notes,
                    s.updated_at
                FROM fund_lp_status s
                JOIN organizations o ON o.id = s.lp_org_id
                WHERE s.fund_id = %s
                ORDER BY s.updated_at DESC
                """,
                (fund_id,),
            )
            rows = cur.fetchall()

            # Group by stage for pipeline view
            pipeline: dict[str, list[dict[str, Any]]] = {
                stage: [] for stage in VALID_PIPELINE_STAGES
            }

            items = []
            for row in rows:
                item = {
                    "lp_id": str(row["lp_org_id"]),
                    "lp_name": row["lp_name"],
                    "stage": row["pipeline_stage"],
                    "gp_interest": row["gp_interest"],
                    "lp_interest": row["lp_interest"],
                    "notes": row["notes"],
                    "updated_at": str(row["updated_at"]) if row["updated_at"] else None,
                }
                items.append(item)
                if row["pipeline_stage"] in pipeline:
                    pipeline[row["pipeline_stage"]].append(item)

            return JSONResponse(
                content={
                    "success": True,
                    "fund_id": fund_id,
                    "total": len(items),
                    "items": items,
                    "by_stage": {k: len(v) for k, v in pipeline.items()},
                },
            )
    except Exception as e:
        logger.error(f"Pipeline status error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )
    finally:
        conn.close()


# =============================================================================
# PHASE 3: CRM/IR Features - Events, Touchpoints, Tasks
# =============================================================================


@app.get("/events", response_class=HTMLResponse, response_model=None)
async def events_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Events management page for IR team.

    Lists all events with filtering and CRUD operations.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Default empty state
    events: list[dict[str, Any]] = []
    upcoming_count = 0
    past_count = 0

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        e.*,
                        COUNT(DISTINCT ea.id) as attendee_count
                    FROM events e
                    LEFT JOIN event_attendance ea ON ea.event_id = e.id
                    GROUP BY e.id
                    ORDER BY e.start_date DESC NULLS LAST
                    """
                )
                events = cur.fetchall()

                # Count upcoming vs past
                from datetime import date

                today = date.today()
                for event in events:
                    if event.get("start_date"):
                        if event["start_date"] >= today:
                            upcoming_count += 1
                        else:
                            past_count += 1
        finally:
            conn.close()

    return templates.TemplateResponse(
        request,
        "pages/events.html",
        {
            "title": "Events - LPxGP",
            "user": user,
            "events": events,
            "upcoming_count": upcoming_count,
            "past_count": past_count,
        },
    )


@app.post("/api/events", response_class=HTMLResponse)
async def create_event(
    request: Request,
    name: str = Form(...),
    event_type: str = Form("conference"),
    start_date: str | None = Form(None),
    end_date: str | None = Form(None),
    city: str | None = Form(None),
    country: str | None = Form(None),
    notes: str | None = Form(None),
) -> HTMLResponse:
    """Create a new event."""
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="<div>Not authenticated</div>", status_code=401)

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content='<div class="text-yellow-500">Database unavailable</div>',
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            # Get user's org_id
            cur.execute(
                "SELECT org_id FROM people WHERE auth_user_id = %s",
                (user.get("id"),),
            )
            person = cur.fetchone()
            org_id = person["org_id"] if person else None

            if not org_id:
                # Create a default org if none exists
                cur.execute(
                    "SELECT id FROM organizations LIMIT 1"
                )
                org = cur.fetchone()
                org_id = org["id"] if org else None

            cur.execute(
                """
                INSERT INTO events (
                    org_id, name, event_type, start_date, end_date,
                    city, country, notes, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'planning')
                RETURNING id
                """,
                (
                    org_id,
                    name,
                    event_type,
                    start_date or None,
                    end_date or None,
                    city,
                    country,
                    notes,
                ),
            )
            cur.fetchone()  # Consume the RETURNING result
            conn.commit()

            return HTMLResponse(
                content=f"""
                <div class="text-center p-4">
                    <div class="text-green-500 text-lg mb-2">✓ Event Created</div>
                    <p class="text-navy-600">{name}</p>
                    <script>
                        setTimeout(() => window.location.href = '/events', 1500);
                    </script>
                </div>
                """,
            )
    except Exception as e:
        logger.error(f"Event creation error: {e}")
        return HTMLResponse(
            content=f'<div class="text-red-500">Error: {e}</div>',
            status_code=500,
        )
    finally:
        conn.close()


@app.get("/api/events/{event_id}", response_class=HTMLResponse)
async def get_event_detail(request: Request, event_id: str) -> HTMLResponse:
    """Get event detail modal content."""
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="<div>Not authenticated</div>", status_code=401)

    if not is_valid_uuid(event_id):
        return HTMLResponse(
            content='<div class="text-red-500">Invalid event ID</div>',
            status_code=400,
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content='<div class="text-yellow-500">Database unavailable</div>',
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT e.*,
                    COUNT(DISTINCT ea.id) as attendee_count
                FROM events e
                LEFT JOIN event_attendance ea ON ea.event_id = e.id
                WHERE e.id = %s
                GROUP BY e.id
                """,
                (event_id,),
            )
            event = cur.fetchone()

            if not event:
                return HTMLResponse(
                    content='<div class="text-red-500">Event not found</div>',
                    status_code=404,
                )

            # Get attendees
            cur.execute(
                """
                SELECT ea.*, p.full_name, o.name as org_name
                FROM event_attendance ea
                LEFT JOIN people p ON p.id = ea.person_id
                LEFT JOIN organizations o ON o.id = ea.company_id
                WHERE ea.event_id = %s
                """,
                (event_id,),
            )
            attendees = cur.fetchall()

            return templates.TemplateResponse(
                request,
                "partials/event_detail_modal.html",
                {"event": event, "attendees": attendees},
            )
    finally:
        conn.close()


@app.delete("/api/events/{event_id}", response_class=HTMLResponse)
async def delete_event(request: Request, event_id: str) -> HTMLResponse:
    """Delete an event."""
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="<div>Not authenticated</div>", status_code=401)

    if not is_valid_uuid(event_id):
        return HTMLResponse(
            content='<div class="text-red-500">Invalid event ID</div>',
            status_code=400,
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content='<div class="text-yellow-500">Database unavailable</div>',
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            cur.execute("DELETE FROM events WHERE id = %s", (event_id,))
            conn.commit()

            return HTMLResponse(
                content="""
                <div class="text-center p-4">
                    <div class="text-green-500">Event deleted</div>
                    <script>
                        document.body.dispatchEvent(new Event('eventDeleted'));
                        setTimeout(() => window.location.reload(), 1000);
                    </script>
                </div>
                """,
            )
    except Exception as e:
        logger.error(f"Event deletion error: {e}")
        return HTMLResponse(
            content=f'<div class="text-red-500">Error: {e}</div>',
            status_code=500,
        )
    finally:
        conn.close()


@app.get("/touchpoints", response_class=HTMLResponse, response_model=None)
async def touchpoints_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Touchpoints/interactions log page."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    touchpoints: list[dict[str, Any]] = []

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        t.*,
                        p.full_name as person_name,
                        o.name as company_name,
                        e.name as event_name
                    FROM touchpoints t
                    LEFT JOIN people p ON p.id = t.person_id
                    LEFT JOIN organizations o ON o.id = t.company_id
                    LEFT JOIN events e ON e.id = t.event_id
                    ORDER BY t.occurred_at DESC
                    LIMIT 100
                    """
                )
                touchpoints = cur.fetchall()
        finally:
            conn.close()

    return templates.TemplateResponse(
        request,
        "pages/touchpoints.html",
        {
            "title": "Touchpoints - LPxGP",
            "user": user,
            "touchpoints": touchpoints,
        },
    )


@app.post("/api/touchpoints", response_class=HTMLResponse)
async def create_touchpoint(
    request: Request,
    touchpoint_type: str = Form(...),
    occurred_at: str = Form(...),
    summary: str | None = Form(None),
    person_id: str | None = Form(None),
    company_id: str | None = Form(None),
    sentiment: str | None = Form(None),
    follow_up_required: bool = Form(False),
) -> HTMLResponse:
    """Log a new touchpoint/interaction."""
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="<div>Not authenticated</div>", status_code=401)

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content='<div class="text-yellow-500">Database unavailable</div>',
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            # Get user's org_id
            cur.execute(
                "SELECT id, org_id FROM people WHERE auth_user_id = %s",
                (user.get("id"),),
            )
            person = cur.fetchone()
            org_id = person["org_id"] if person else None
            created_by = person["id"] if person else None

            if not org_id:
                cur.execute("SELECT id FROM organizations LIMIT 1")
                org = cur.fetchone()
                org_id = org["id"] if org else None

            cur.execute(
                """
                INSERT INTO touchpoints (
                    org_id, touchpoint_type, occurred_at, summary,
                    person_id, company_id, sentiment, follow_up_required,
                    created_by
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                RETURNING id
                """,
                (
                    org_id,
                    touchpoint_type,
                    occurred_at,
                    summary,
                    person_id if person_id and is_valid_uuid(person_id) else None,
                    company_id if company_id and is_valid_uuid(company_id) else None,
                    sentiment,
                    follow_up_required,
                    created_by,
                ),
            )
            conn.commit()

            return HTMLResponse(
                content="""
                <div class="text-center p-4">
                    <div class="text-green-500 text-lg mb-2">✓ Touchpoint Logged</div>
                    <script>
                        setTimeout(() => window.location.href = '/touchpoints', 1500);
                    </script>
                </div>
                """,
            )
    except Exception as e:
        logger.error(f"Touchpoint creation error: {e}")
        return HTMLResponse(
            content=f'<div class="text-red-500">Error: {e}</div>',
            status_code=500,
        )
    finally:
        conn.close()


@app.get("/tasks", response_class=HTMLResponse, response_model=None)
async def tasks_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Task management page."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    tasks: list[dict[str, Any]] = []
    pending_count = 0
    overdue_count = 0

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        t.*,
                        p.full_name as contact_name,
                        o.name as company_name,
                        e.name as event_name,
                        ap.full_name as assigned_name
                    FROM tasks t
                    LEFT JOIN people p ON p.id = t.person_id
                    LEFT JOIN organizations o ON o.id = t.company_id
                    LEFT JOIN events e ON e.id = t.event_id
                    LEFT JOIN people ap ON ap.id = t.assigned_to
                    ORDER BY
                        CASE t.priority
                            WHEN 'urgent' THEN 1
                            WHEN 'high' THEN 2
                            WHEN 'medium' THEN 3
                            ELSE 4
                        END,
                        t.due_date ASC NULLS LAST
                    """
                )
                tasks = cur.fetchall()

                from datetime import date

                today = date.today()
                for task in tasks:
                    if task["status"] in ("pending", "in_progress"):
                        pending_count += 1
                        if task.get("due_date") and task["due_date"] < today:
                            overdue_count += 1
        finally:
            conn.close()

    return templates.TemplateResponse(
        request,
        "pages/tasks.html",
        {
            "title": "Tasks - LPxGP",
            "user": user,
            "tasks": tasks,
            "pending_count": pending_count,
            "overdue_count": overdue_count,
        },
    )


@app.post("/api/tasks", response_class=HTMLResponse)
async def create_task(
    request: Request,
    title: str = Form(...),
    description: str | None = Form(None),
    due_date: str | None = Form(None),
    priority: str = Form("medium"),
    person_id: str | None = Form(None),
    company_id: str | None = Form(None),
) -> HTMLResponse:
    """Create a new task."""
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="<div>Not authenticated</div>", status_code=401)

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content='<div class="text-yellow-500">Database unavailable</div>',
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            # Get user's org_id and person_id
            cur.execute(
                "SELECT id, org_id FROM people WHERE auth_user_id = %s",
                (user.get("id"),),
            )
            person = cur.fetchone()
            org_id = person["org_id"] if person else None
            assigned_to = person["id"] if person else None

            if not org_id:
                cur.execute("SELECT id FROM organizations LIMIT 1")
                org = cur.fetchone()
                org_id = org["id"] if org else None

            cur.execute(
                """
                INSERT INTO tasks (
                    org_id, title, description, due_date, priority,
                    person_id, company_id, assigned_to, status
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, 'pending')
                RETURNING id
                """,
                (
                    org_id,
                    title,
                    description,
                    due_date or None,
                    priority,
                    person_id if person_id and is_valid_uuid(person_id) else None,
                    company_id if company_id and is_valid_uuid(company_id) else None,
                    assigned_to,
                ),
            )
            conn.commit()

            return HTMLResponse(
                content="""
                <div class="text-center p-4">
                    <div class="text-green-500 text-lg mb-2">✓ Task Created</div>
                    <script>
                        setTimeout(() => window.location.href = '/tasks', 1500);
                    </script>
                </div>
                """,
            )
    except Exception as e:
        logger.error(f"Task creation error: {e}")
        return HTMLResponse(
            content=f'<div class="text-red-500">Error: {e}</div>',
            status_code=500,
        )
    finally:
        conn.close()


@app.put("/api/tasks/{task_id}/complete", response_class=HTMLResponse)
async def complete_task(request: Request, task_id: str) -> HTMLResponse:
    """Mark a task as complete."""
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="<div>Not authenticated</div>", status_code=401)

    if not is_valid_uuid(task_id):
        return HTMLResponse(
            content='<div class="text-red-500">Invalid task ID</div>',
            status_code=400,
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content='<div class="text-yellow-500">Database unavailable</div>',
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE tasks
                SET status = 'completed', completed_at = NOW()
                WHERE id = %s
                RETURNING title
                """,
                (task_id,),
            )
            result = cur.fetchone()
            conn.commit()

            if not result:
                return HTMLResponse(
                    content='<div class="text-red-500">Task not found</div>',
                    status_code=404,
                )

            return HTMLResponse(
                content="""
                <span class="px-2 py-1 text-xs bg-green-100 text-green-700 rounded-full">
                    Completed ✓
                </span>
                """,
            )
    except Exception as e:
        logger.error(f"Task complete error: {e}")
        return HTMLResponse(
            content=f'<div class="text-red-500">Error: {e}</div>',
            status_code=500,
        )
    finally:
        conn.close()


# =============================================================================
# PHASE 4: LP Dashboard & Features
# =============================================================================


@app.get("/lp-dashboard", response_class=HTMLResponse, response_model=None)
async def lp_dashboard(request: Request) -> HTMLResponse | RedirectResponse:
    """LP-specific dashboard showing fund matches and pipeline.

    For LPs to view and manage incoming fund opportunities.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Dashboard data
    matches: list[dict[str, Any]] = []
    watchlist: list[dict[str, Any]] = []
    pipeline_stats = {
        "interested": 0,
        "reviewing": 0,
        "dd_in_progress": 0,
        "passed": 0,
    }

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                # Get LP's organization through employment
                cur.execute(
                    """
                    SELECT o.id as lp_org_id
                    FROM people p
                    JOIN employment e ON e.person_id = p.id AND e.is_current = TRUE
                    JOIN organizations o ON o.id = e.org_id
                    WHERE p.auth_user_id = %s AND o.is_lp = TRUE
                    """,
                    (user.get("id"),),
                )
                lp_org = cur.fetchone()

                if lp_org:
                    lp_org_id = lp_org["lp_org_id"]

                    # Get fund matches for this LP
                    cur.execute(
                        """
                        SELECT
                            m.id, m.fund_id, m.score, m.explanation,
                            m.talking_points, m.concerns,
                            f.name as fund_name, f.target_size_mm, f.strategy,
                            f.vintage_year,
                            gp.name as gp_name,
                            s.lp_interest, s.pipeline_stage
                        FROM fund_lp_matches m
                        JOIN funds f ON f.id = m.fund_id
                        JOIN organizations gp ON gp.id = f.gp_org_id
                        LEFT JOIN fund_lp_status s
                            ON s.fund_id = m.fund_id AND s.lp_org_id = m.lp_org_id
                        WHERE m.lp_org_id = %s
                        ORDER BY m.score DESC
                        LIMIT 20
                        """,
                        (lp_org_id,),
                    )
                    matches = cur.fetchall()

                    # Get watchlist
                    cur.execute(
                        """
                        SELECT
                            f.id, f.name, f.target_size_mm, f.strategy,
                            gp.name as gp_name,
                            s.lp_interest, s.notes
                        FROM fund_lp_status s
                        JOIN funds f ON f.id = s.fund_id
                        JOIN organizations gp ON gp.id = f.gp_org_id
                        WHERE s.lp_org_id = %s AND s.lp_interest = 'watching'
                        ORDER BY s.updated_at DESC
                        """,
                        (lp_org_id,),
                    )
                    watchlist = cur.fetchall()

                    # Pipeline stats
                    cur.execute(
                        """
                        SELECT lp_interest, COUNT(*) as count
                        FROM fund_lp_status
                        WHERE lp_org_id = %s AND lp_interest IS NOT NULL
                        GROUP BY lp_interest
                        """,
                        (lp_org_id,),
                    )
                    for row in cur.fetchall():
                        if row["lp_interest"] in pipeline_stats:
                            pipeline_stats[row["lp_interest"]] = row["count"]
        finally:
            conn.close()

    return templates.TemplateResponse(
        request,
        "pages/lp-dashboard.html",
        {
            "title": "LP Dashboard - LPxGP",
            "user": user,
            "matches": matches,
            "watchlist": watchlist,
            "pipeline_stats": pipeline_stats,
        },
    )


@app.get("/lp-watchlist", response_class=HTMLResponse, response_model=None)
async def lp_watchlist_page(request: Request) -> HTMLResponse | RedirectResponse:
    """LP watchlist page for tracking interesting funds."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    watchlist: list[dict[str, Any]] = []

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                # Get LP's organization through employment
                cur.execute(
                    """
                    SELECT o.id as lp_org_id
                    FROM people p
                    JOIN employment e ON e.person_id = p.id AND e.is_current = TRUE
                    JOIN organizations o ON o.id = e.org_id
                    WHERE p.auth_user_id = %s
                    """,
                    (user.get("id"),),
                )
                lp_org = cur.fetchone()

                if lp_org:
                    cur.execute(
                        """
                        SELECT
                            f.id, f.name, f.target_size_mm, f.strategy,
                            f.vintage_year, f.status,
                            gp.name as gp_name, gp.hq_city, gp.hq_country,
                            s.lp_interest, s.notes, s.updated_at
                        FROM fund_lp_status s
                        JOIN funds f ON f.id = s.fund_id
                        JOIN organizations gp ON gp.id = f.gp_org_id
                        WHERE s.lp_org_id = %s
                            AND s.lp_interest IN ('watching', 'interested')
                        ORDER BY s.updated_at DESC
                        """,
                        (lp_org["lp_org_id"],),
                    )
                    watchlist = cur.fetchall()
        finally:
            conn.close()

    return templates.TemplateResponse(
        request,
        "pages/lp-watchlist.html",
        {
            "title": "Watchlist - LPxGP",
            "user": user,
            "watchlist": watchlist,
        },
    )


@app.post("/api/lp/fund/{fund_id}/interest", response_class=HTMLResponse)
async def update_lp_interest(
    request: Request,
    fund_id: str,
    interest: str = Form(...),
    notes: str | None = Form(None),
) -> HTMLResponse:
    """Update LP's interest level in a fund.

    Args:
        fund_id: Fund ID.
        interest: Interest level (watching, interested, reviewing, passed).
        notes: Optional notes.
    """
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="<div>Not authenticated</div>", status_code=401)

    if not is_valid_uuid(fund_id):
        return HTMLResponse(
            content='<div class="text-red-500">Invalid fund ID</div>',
            status_code=400,
        )

    valid_interests = ["watching", "interested", "reviewing", "dd_in_progress", "passed"]
    if interest not in valid_interests:
        return HTMLResponse(
            content=f'<div class="text-red-500">Invalid interest: {interest}</div>',
            status_code=400,
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content='<div class="text-yellow-500">Database unavailable</div>',
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            # Get LP's org through employment
            cur.execute(
                """
                SELECT o.id as lp_org_id
                FROM people p
                JOIN employment e ON e.person_id = p.id AND e.is_current = TRUE
                JOIN organizations o ON o.id = e.org_id
                WHERE p.auth_user_id = %s
                """,
                (user.get("id"),),
            )
            lp_org = cur.fetchone()

            if not lp_org:
                return HTMLResponse(
                    content='<div class="text-red-500">LP org not found</div>',
                    status_code=404,
                )

            # Upsert fund_lp_status
            cur.execute(
                """
                INSERT INTO fund_lp_status (fund_id, lp_org_id, lp_interest, notes)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (fund_id, lp_org_id)
                DO UPDATE SET
                    lp_interest = EXCLUDED.lp_interest,
                    notes = COALESCE(EXCLUDED.notes, fund_lp_status.notes),
                    updated_at = NOW()
                RETURNING lp_interest
                """,
                (fund_id, lp_org["lp_org_id"], interest, notes),
            )
            conn.commit()

            # Interest badge styling
            interest_colors = {
                "watching": "bg-gray-100 text-gray-700",
                "interested": "bg-blue-100 text-blue-700",
                "reviewing": "bg-yellow-100 text-yellow-700",
                "dd_in_progress": "bg-orange-100 text-orange-700",
                "passed": "bg-red-100 text-red-700",
            }
            color = interest_colors.get(interest, "bg-gray-100 text-gray-700")
            display = interest.replace("_", " ").title()

            return HTMLResponse(
                content=f"""
                <span class="px-2 py-1 text-xs rounded-full {color}">
                    {display}
                </span>
                """,
            )
    except Exception as e:
        logger.error(f"LP interest update error: {e}")
        return HTMLResponse(
            content=f'<div class="text-red-500">Error: {e}</div>',
            status_code=500,
        )
    finally:
        conn.close()


@app.get("/lp-pipeline", response_class=HTMLResponse, response_model=None)
async def lp_pipeline_page(request: Request) -> HTMLResponse | RedirectResponse:
    """LP pipeline view - kanban-style fund tracking."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Pipeline stages with funds
    pipeline: dict[str, list[dict[str, Any]]] = {
        "watching": [],
        "interested": [],
        "reviewing": [],
        "dd_in_progress": [],
        "passed": [],
    }

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                # Get LP's organization through employment
                cur.execute(
                    """
                    SELECT o.id as lp_org_id
                    FROM people p
                    JOIN employment e ON e.person_id = p.id AND e.is_current = TRUE
                    JOIN organizations o ON o.id = e.org_id
                    WHERE p.auth_user_id = %s
                    """,
                    (user.get("id"),),
                )
                lp_org = cur.fetchone()

                if lp_org:
                    cur.execute(
                        """
                        SELECT
                            f.id, f.name, f.target_size_mm, f.strategy,
                            gp.name as gp_name,
                            s.lp_interest, s.notes, s.updated_at
                        FROM fund_lp_status s
                        JOIN funds f ON f.id = s.fund_id
                        JOIN organizations gp ON gp.id = f.gp_org_id
                        WHERE s.lp_org_id = %s AND s.lp_interest IS NOT NULL
                        ORDER BY s.updated_at DESC
                        """,
                        (lp_org["lp_org_id"],),
                    )
                    for fund in cur.fetchall():
                        stage = fund.get("lp_interest", "watching")
                        if stage in pipeline:
                            pipeline[stage].append(fund)
        finally:
            conn.close()

    return templates.TemplateResponse(
        request,
        "pages/lp-pipeline.html",
        {
            "title": "Pipeline - LPxGP",
            "user": user,
            "pipeline": pipeline,
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
