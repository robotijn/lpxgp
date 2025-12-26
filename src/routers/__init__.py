"""LPxGP Router modules.

This package contains FastAPI APIRouter modules for organizing routes
by domain. Each router handles a specific area of functionality.

Routers:
    health: Health check and status endpoints (/health, /api/status)
    auth: Authentication routes (/login, /register, /logout, /api/auth/*)
    pages: Core pages (/, /dashboard, /settings)
    admin: Admin routes (/admin/*)
    gps: GP (General Partner) routes (/gps, /api/gps/*, /api/v1/gps)
    funds: Fund management (/funds, /api/funds/*, /api/v1/funds)
    lps: LP management (/lps, /api/lps/*, /api/v1/lps)
    matches: Match viewing and actions (/matches, /api/match/*)
    pitch: Pitch generator (/pitch)
    crm: CRM features - events, touchpoints, tasks (/events, /touchpoints, /tasks)
    shortlist: Shortlist management (/shortlist, /api/shortlist/*)
    pipeline: Pipeline and outreach (/pipeline, /outreach, /api/v1/pipeline/*)
    lp_portal: LP-specific views and actions (/lp-dashboard, /lp-watchlist, /lp-pipeline, /api/lp/*)
"""

from src.routers.admin import router as admin_router
from src.routers.auth_routes import router as auth_router
from src.routers.crm import router as crm_router
from src.routers.funds import router as funds_router
from src.routers.gps import router as gps_router
from src.routers.health import router as health_router
from src.routers.lp_portal import router as lp_portal_router
from src.routers.lps import router as lps_router
from src.routers.matches import router as matches_router
from src.routers.pages import router as pages_router
from src.routers.pipeline import router as pipeline_router
from src.routers.pitch import router as pitch_router
from src.routers.settings_api import router as settings_api_router
from src.routers.shortlist import router as shortlist_router

__all__ = [
    "admin_router",
    "auth_router",
    "crm_router",
    "funds_router",
    "gps_router",
    "health_router",
    "lp_portal_router",
    "lps_router",
    "matches_router",
    "pages_router",
    "pipeline_router",
    "pitch_router",
    "settings_api_router",
    "shortlist_router",
]
