"""Core page routes for public and shared pages.

This router provides:
- /: Home page
- /dashboard: User dashboard (protected)
- /settings: User settings (protected)
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src import auth
from src.preferences import get_user_preferences
from src.utils import get_db

router = APIRouter(tags=["pages"])

# Templates
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# =============================================================================
# Page Routes
# =============================================================================


@router.get("/", response_class=HTMLResponse)
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


@router.get("/dashboard", response_class=HTMLResponse, response_model=None)
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


@router.get("/settings", response_class=HTMLResponse, response_model=None)
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
