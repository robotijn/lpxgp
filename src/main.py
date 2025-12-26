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
from src.preferences import get_user_preferences
from src.routers import (
    admin_router,
    auth_router,
    gps_router,
    health_router,
    lp_portal_router,
    pages_router,
    pipeline_router,
    settings_api_router,
    shortlist_router,
)
from src.search import (
    build_lp_search_sql,
    is_natural_language_query,
    parse_lp_search_query,
)
from src.shortlists import (
    is_in_shortlist,
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
