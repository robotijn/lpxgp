"""Shortlist API endpoints for managing saved LPs.

This router provides:
- /shortlist: Shortlist page (HTML)
- /api/shortlist: CRUD operations for shortlist items
- /api/shortlist/{lp_id}/toggle: HTMX toggle button
"""

from __future__ import annotations

from pathlib import Path

import psycopg
from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src import auth
from src.database import get_db
from src.logging_config import get_logger
from src.shortlists import (
    ShortlistAddRequest,
    ShortlistItem,
    ShortlistUpdateRequest,
    add_to_shortlist,
    clear_user_shortlist,
    get_user_shortlist,
    is_in_shortlist,
    remove_from_shortlist,
    update_shortlist_item,
)
from src.utils import is_valid_uuid

logger = get_logger(__name__)

router = APIRouter(tags=["shortlist"])

# Templates setup
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=templates_path)


@router.get("/shortlist", response_class=HTMLResponse, response_model=None)
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


@router.post("/api/shortlist", response_class=JSONResponse)
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


@router.delete("/api/shortlist/{lp_id}", response_class=JSONResponse)
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


@router.patch("/api/shortlist/{lp_id}", response_class=JSONResponse)
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


@router.get("/api/shortlist", response_class=JSONResponse)
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


@router.get("/api/shortlist/check/{lp_id}", response_class=JSONResponse)
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

    in_list = is_in_shortlist(user["id"], lp_id)
    return JSONResponse(
        content={"in_shortlist": in_list, "lp_id": lp_id},
    )


@router.delete("/api/shortlist", response_class=JSONResponse)
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
@router.post("/api/shortlist/{lp_id}/toggle", response_class=HTMLResponse)
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
