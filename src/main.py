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

import httpx
import psycopg
from fastapi import FastAPI, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from psycopg.rows import dict_row

from src import auth
from src.config import get_settings, validate_settings_on_startup
from src.logging_config import get_logger

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
    if settings.database_configured:
        return psycopg.connect(settings.database_url, row_factory=dict_row)
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
) -> HTMLResponse | RedirectResponse:
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
        return templates.TemplateResponse(
            request,
            "partials/auth_error.html",
            {"error": "Invalid email or password"},
            status_code=401,
        )

    return auth.login_response(user, redirect_to="/dashboard")


@app.post("/api/auth/register", response_model=None)
async def api_register(
    request: Request,
    email: str = Form(...),
    password: str = Form(...),
    name: str = Form(...),
    role: str = Form(default="gp"),
) -> HTMLResponse | RedirectResponse:
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
        user = auth.create_user(email=email, password=password, name=name, role=role)
        return auth.login_response(user, redirect_to="/dashboard")
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
                stats["total_funds"] = cur.fetchone()["count"]

                cur.execute("SELECT COUNT(*) FROM lps")
                stats["total_lps"] = cur.fetchone()["count"]

                cur.execute("SELECT COUNT(*) FROM fund_lp_matches")
                stats["total_matches"] = cur.fetchone()["count"]
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

    Requires authentication.

    Args:
        request: FastAPI request object.

    Returns:
        Settings page HTML or redirect to login if not authenticated.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    return templates.TemplateResponse(
        request,
        "pages/settings.html",
        {
            "title": "Settings - LPxGP",
            "user": user,
        },
    )


@app.get("/matches", response_class=HTMLResponse)
async def matches_page(
    request: Request,
    fund_id: str | None = Query(None),
) -> HTMLResponse:
    """Render the matches page showing AI-recommended LP matches.

    Displays scored LP-Fund matches with filtering by fund and
    statistics including high score count, average score, and
    pipeline status.

    Args:
        request: FastAPI request object.
        fund_id: Optional UUID of fund to filter matches by.

    Returns:
        Matches page HTML with match data and statistics.
    """
    # Validate fund_id if provided - ignore invalid UUIDs to prevent crashes
    validated_fund_id: str | None = None
    if fund_id and is_valid_uuid(fund_id):
        validated_fund_id = fund_id

    # Default empty state
    empty_response: dict[str, Any] = {
        "title": "Matches - LPxGP",
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


@app.get("/funds", response_class=HTMLResponse)
async def funds_page(request: Request):
    """Funds page listing GP fund profiles."""
    empty_response = {
        "title": "Funds - LPxGP",
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


@app.get("/lps", response_class=HTMLResponse)
async def lps_page(
    request: Request,
    search: str | None = Query(None),
    lp_type: str | None = Query(None),
):
    """LPs page for browsing and searching LP profiles."""
    empty_response = {
        "title": "LPs - LPxGP",
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
            query = """
                SELECT
                    o.id, o.name, o.hq_city, o.hq_country, o.website,
                    lp.lp_type, lp.total_aum_bn, lp.pe_allocation_pct,
                    lp.check_size_min_mm, lp.check_size_max_mm,
                    lp.geographic_preferences, lp.strategies
                FROM organizations o
                JOIN lp_profiles lp ON lp.org_id = o.id
                WHERE 1=1
            """
            params = []

            if search:
                query += " AND (o.name ILIKE %s OR o.hq_city ILIKE %s)"
                params.extend([f"%{search}%", f"%{search}%"])

            if lp_type:
                query += " AND lp.lp_type = %s"
                params.append(lp_type)

            query += " ORDER BY lp.total_aum_bn DESC NULLS LAST LIMIT 100"

            cur.execute(query, params)
            lps = cur.fetchall()

        # Calculate stats
        total_aum = sum(lp["total_aum_bn"] or 0 for lp in lps)

        return templates.TemplateResponse(
            request,
            "pages/lps.html",
            {
                "title": "LPs - LPxGP",
                "lps": lps,
                "total_aum": total_aum,
                "search": search or "",
                "lp_type": lp_type or "",
                "lp_types": lp_types,
            },
        )
    finally:
        conn.close()


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
            fund_id = cur.fetchone()["id"]
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

    from src.matching import calculate_match_score, generate_match_content

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
                # Calculate match score
                result = calculate_match_score(dict(fund), dict(lp))

                # Only create matches for scores above threshold
                if result["score"] >= 50:
                    # Generate LLM content
                    content = await generate_match_content(
                        dict(fund),
                        dict(lp),
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
            org_id = cur.fetchone()["id"]

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
