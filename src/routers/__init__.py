"""LPxGP Router modules.

This package contains FastAPI APIRouter modules for organizing routes
by domain. Each router handles a specific area of functionality.

Routers:
    health: Health check and status endpoints (/health, /api/status)
    auth: Authentication routes (/login, /register, /logout, /api/auth/*)
    pages: Core pages (/, /dashboard, /settings)
    admin: Admin routes (/admin/*)
    shortlist: Shortlist management (/shortlist, /api/shortlist/*)
"""

from src.routers.admin import router as admin_router
from src.routers.auth_routes import router as auth_router
from src.routers.health import router as health_router
from src.routers.pages import router as pages_router
from src.routers.settings_api import router as settings_api_router
from src.routers.shortlist import router as shortlist_router

__all__ = [
    "admin_router",
    "auth_router",
    "health_router",
    "pages_router",
    "settings_api_router",
    "shortlist_router",
]
