"""LPxGP FastAPI Application.

AI-powered platform helping GPs find and engage LPs.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from uuid import UUID

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, Request, Query
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.config import get_settings, validate_settings_on_startup
from src.logging_config import get_logger


def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID.

    Used to validate user input before database queries to prevent
    crashes and potential injection attacks.
    """
    if not value:
        return False
    try:
        UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def get_db() -> Optional[psycopg.Connection]:
    """Get database connection if configured.

    Returns a psycopg connection with dict_row factory for easy data access.
    Caller is responsible for closing the connection.
    """
    settings = get_settings()
    if settings.database_configured:
        return psycopg.connect(settings.database_url, row_factory=dict_row)
    return None

# -----------------------------------------------------------------------------
# Application Setup
# -----------------------------------------------------------------------------

logger = get_logger(__name__)

# Paths
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
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


# -----------------------------------------------------------------------------
# Health & Status Endpoints
# -----------------------------------------------------------------------------

@app.api_route("/health", methods=["GET", "HEAD"], response_class=JSONResponse)
async def health_check():
    """Health check endpoint for load balancers and monitoring.

    Supports both GET and HEAD methods for efficient health checking.
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
    }


@app.get("/api/status", response_class=JSONResponse)
async def api_status():
    """API status with configuration info (non-sensitive)."""
    settings = get_settings()
    return {
        "status": "ok",
        "environment": settings.environment,
        "features": {
            "semantic_search": settings.enable_semantic_search,
            "agent_matching": settings.enable_agent_matching,
        },
    }


# -----------------------------------------------------------------------------
# Page Routes
# -----------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page."""
    return templates.TemplateResponse(
        request,
        "pages/home.html",
        {"title": "LPxGP - GP-LP Intelligence Platform"},
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse(
        request,
        "pages/login.html",
        {"title": "Login - LPxGP"},
    )


@app.get("/matches", response_class=HTMLResponse)
async def matches_page(request: Request, fund_id: Optional[str] = Query(None)):
    """Matches page showing AI-recommended LP matches."""
    # Validate fund_id if provided - ignore invalid UUIDs to prevent crashes
    validated_fund_id = None
    if fund_id and is_valid_uuid(fund_id):
        validated_fund_id = fund_id

    # Default empty state
    empty_response = {
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
