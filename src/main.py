"""LPxGP FastAPI Application.

AI-powered platform helping GPs find and engage LPs.
"""

from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.config import get_settings, validate_settings_on_startup
from src.logging_config import get_logger

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

@app.get("/health", response_class=JSONResponse)
async def health_check():
    """Health check endpoint for load balancers and monitoring."""
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
