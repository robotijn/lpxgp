"""User preferences and team management API routes.

This router provides:
- GET /api/settings/preferences: Get user preferences
- PUT /api/settings/preferences: Update user preferences
- POST /api/settings/preferences/toggle/{pref_name}: Toggle a preference
- GET /settings/team: Team management page
- POST /api/team/invite: Send team invite (mock email)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel

from src import auth
from src.preferences import (
    UserPreferences,
    get_user_preferences,
    update_user_preferences,
)

router = APIRouter(tags=["settings"])

# Templates
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# =============================================================================
# Team Invite Data Models
# =============================================================================


class TeamInviteRequest(BaseModel):
    """Request body for team invite."""

    email: str
    role: str = "gp"
    message: str = ""


# In-memory storage for pending invites (demo purposes)
_pending_invites: dict[str, list[dict[str, Any]]] = {}


@router.get("/api/settings/preferences", response_class=JSONResponse)
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


@router.put("/api/settings/preferences", response_class=JSONResponse)
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


@router.post("/api/settings/preferences/toggle/{pref_name}", response_class=HTMLResponse)
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
# Team Management Endpoints
# =============================================================================


@router.get("/settings/team", response_class=HTMLResponse, response_model=None)
async def team_management_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Render the team management page.

    Shows current team members and pending invites.
    Allows sending new invites.

    Args:
        request: FastAPI request object.

    Returns:
        Team management page HTML or redirect to login.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Get pending invites for this user's organization
    user_id = user["id"]
    pending = _pending_invites.get(user_id, [])

    # Demo team members (in production, query from database)
    team_members = [
        {"name": user["name"], "email": user["email"], "role": user["role"], "is_current": True}
    ]

    return templates.TemplateResponse(
        request,
        "pages/settings-team.html",
        {
            "title": "Team Management - LPxGP",
            "user": user,
            "team_members": team_members,
            "pending_invites": pending,
        },
    )


@router.post("/api/team/invite", response_class=HTMLResponse)
async def send_team_invite(
    request: Request,
    email: str = Form(...),
    role: str = Form(default="gp"),
    message: str = Form(default=""),
) -> HTMLResponse:
    """Send a team invite (mock - doesn't actually send email).

    In production, this would:
    1. Validate the email
    2. Create an invite record in the database
    3. Send an email via SendGrid/Resend/etc.

    Args:
        request: FastAPI request object.
        email: Email address to invite.
        role: Role to assign (gp, lp, admin).
        message: Optional personal message.

    Returns:
        HTML partial with success/error message.
    """
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(
            content='<div class="text-red-500">Authentication required</div>',
            status_code=401,
        )

    # Validate email format (basic check)
    if not email or "@" not in email:
        return HTMLResponse(
            content='<div class="p-4 bg-red-50 text-red-700 rounded-lg">Invalid email address</div>',
            status_code=400,
        )

    # Validate role
    valid_roles = ["gp", "lp", "admin"]
    if role not in valid_roles:
        return HTMLResponse(
            content='<div class="p-4 bg-red-50 text-red-700 rounded-lg">Invalid role</div>',
            status_code=400,
        )

    # Store the invite (in-memory for demo)
    user_id = user["id"]
    if user_id not in _pending_invites:
        _pending_invites[user_id] = []

    # Check for duplicate
    for invite in _pending_invites[user_id]:
        if invite["email"] == email:
            return HTMLResponse(
                content='<div class="p-4 bg-yellow-50 text-yellow-700 rounded-lg">Invite already sent to this email</div>',
                status_code=400,
            )

    # Add the invite
    from datetime import UTC, datetime

    invite = {
        "email": email,
        "role": role,
        "message": message,
        "sent_at": datetime.now(UTC).isoformat(),
        "status": "pending",
    }
    _pending_invites[user_id].append(invite)

    # Return success message with updated invite list
    invite_html = f'''
    <div class="p-4 bg-green-50 text-green-700 rounded-lg mb-4">
        ✓ Invite sent to {email} (demo - no email actually sent)
    </div>
    <div class="border rounded-lg divide-y">
        {"".join(f'''
        <div class="p-4 flex items-center justify-between">
            <div>
                <p class="font-medium text-navy-900">{inv["email"]}</p>
                <p class="text-sm text-navy-500">Role: {inv["role"].upper()} · Sent: {inv["sent_at"][:10]}</p>
            </div>
            <span class="px-2 py-1 text-xs bg-yellow-100 text-yellow-800 rounded">Pending</span>
        </div>
        ''' for inv in _pending_invites[user_id])}
    </div>
    '''

    return HTMLResponse(content=invite_html)


@router.get("/api/team/invites", response_class=JSONResponse)
async def get_team_invites(request: Request) -> JSONResponse:
    """Get pending team invites.

    Args:
        request: FastAPI request object.

    Returns:
        JSON response with pending invites.
    """
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"},
        )

    user_id = user["id"]
    pending = _pending_invites.get(user_id, [])

    return JSONResponse(
        content={
            "success": True,
            "invites": pending,
        },
    )
