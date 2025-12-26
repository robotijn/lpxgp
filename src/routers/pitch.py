"""Pitch generator routes.

This router provides:
- /pitch: Pitch generator page for creating LP-specific content
"""

from __future__ import annotations

from pathlib import Path

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src import auth

router = APIRouter(tags=["pitch"])

# Templates
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


@router.get("/pitch", response_class=HTMLResponse, response_model=None)
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
