"""GP (General Partner) API endpoints.

This router provides:
- /gps: GP browse page (HTML)
- /api/v1/gps: REST API for GP search
- /api/gps: CRUD operations for GP profiles
- /api/gp/{gp_id}/detail: HTMX partial for GP detail modal
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src import auth
from src.database import get_db
from src.logging_config import get_logger
from src.search import (
    build_gp_search_sql,
    is_natural_language_query,
    parse_gp_search_query,
)
from src.utils import is_valid_uuid, serialize_row

logger = get_logger(__name__)

router = APIRouter(tags=["gps"])

# Templates setup
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=templates_path)


@router.get("/api/v1/gps", response_class=JSONResponse)
async def api_v1_gps(
    request: Request,
    search: str | None = Query(None),
    strategy: str | None = Query(None),
    location: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> JSONResponse:
    """REST API endpoint for GP search.

    Returns JSON for programmatic access.
    Supports filtering by strategy, location.
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
            conditions = ["o.is_gp = TRUE"]
            params: list[Any] = []

            if search:
                conditions.append("(o.name ILIKE %s OR o.hq_city ILIKE %s)")
                params.extend([f"%{search}%", f"%{search}%"])

            if strategy:
                conditions.append("gp.investment_philosophy ILIKE %s")
                params.append(f"%{strategy}%")

            if location:
                conditions.append("(o.hq_city ILIKE %s OR o.hq_country ILIKE %s)")
                params.extend([f"%{location}%", f"%{location}%"])

            where_clause = " AND ".join(conditions)

            # Count total
            count_query = f"""
                SELECT COUNT(*) as total
                FROM organizations o
                JOIN gp_profiles gp ON gp.org_id = o.id
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
                    gp.investment_philosophy, gp.team_size, gp.years_investing,
                    (SELECT COUNT(*) FROM funds f WHERE f.org_id = o.id) as fund_count
                FROM organizations o
                JOIN gp_profiles gp ON gp.org_id = o.id
                WHERE {where_clause}
                ORDER BY o.name
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
        logger.error(f"API v1 GP search error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "code": "SERVER_ERROR"},
        )
    finally:
        conn.close()


@router.get("/gps", response_class=HTMLResponse, response_model=None)
async def gps_page(
    request: Request,
    search: str | None = Query(None),
    strategy: str | None = Query(None),
) -> HTMLResponse | RedirectResponse:
    """GPs page for browsing and searching GP profiles.

    Requires authentication. Supports AI-powered natural language search.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    empty_response = {
        "title": "GPs - LPxGP",
        "user": user,
        "gps": [],
        "total_funds": 0,
        "search": search or "",
        "strategy": strategy or "",
        "strategies": [],
    }

    conn = get_db()
    if not conn:
        return templates.TemplateResponse(request, "pages/gps.html", empty_response)

    try:
        with conn.cursor() as cur:
            # Get distinct strategies from investment_philosophy for filter dropdown
            cur.execute("""
                SELECT DISTINCT
                    CASE
                        WHEN investment_philosophy ILIKE '%%buyout%%' THEN 'buyout'
                        WHEN investment_philosophy ILIKE '%%growth%%' THEN 'growth'
                        WHEN investment_philosophy ILIKE '%%venture%%' THEN 'venture'
                        WHEN investment_philosophy ILIKE '%%real estate%%' THEN 'real_estate'
                        WHEN investment_philosophy ILIKE '%%infrastructure%%' THEN 'infrastructure'
                        WHEN investment_philosophy ILIKE '%%credit%%' THEN 'credit'
                        WHEN investment_philosophy ILIKE '%%secondaries%%' THEN 'secondaries'
                        ELSE NULL
                    END as strategy
                FROM gp_profiles
                WHERE investment_philosophy IS NOT NULL
            """)
            strategies = [row["strategy"] for row in cur.fetchall() if row["strategy"]]

            # Build query with optional filters
            base_query = """
                SELECT
                    o.id, o.name, o.hq_city, o.hq_country, o.website,
                    gp.investment_philosophy, gp.team_size, gp.years_investing,
                    gp.spun_out_from, gp.notable_exits,
                    (SELECT COUNT(*) FROM funds f WHERE f.org_id = o.id) as fund_count,
                    CASE
                        WHEN gp.investment_philosophy ILIKE '%%buyout%%' THEN 'buyout'
                        WHEN gp.investment_philosophy ILIKE '%%growth%%' THEN 'growth'
                        WHEN gp.investment_philosophy ILIKE '%%venture%%' THEN 'venture'
                        WHEN gp.investment_philosophy ILIKE '%%real estate%%' THEN 'real_estate'
                        WHEN gp.investment_philosophy ILIKE '%%infrastructure%%' THEN 'infrastructure'
                        WHEN gp.investment_philosophy ILIKE '%%credit%%' THEN 'credit'
                        WHEN gp.investment_philosophy ILIKE '%%secondaries%%' THEN 'secondaries'
                        ELSE NULL
                    END as strategy
                FROM organizations o
                JOIN gp_profiles gp ON gp.org_id = o.id
                WHERE {where_clause}
                ORDER BY gp.years_investing DESC NULLS LAST, o.name
                LIMIT 100
            """

            # Check if search is natural language (AI parsing) or simple text
            parsed_filters: dict[str, Any] = {}
            if search and is_natural_language_query(search):
                # Use AI to parse the query
                parsed_filters = await parse_gp_search_query(search)
                # Add strategy from dropdown if specified
                if strategy:
                    parsed_filters["strategy"] = strategy
                where_clause, params = build_gp_search_sql(parsed_filters)
            else:
                # Simple text search
                conditions = ["o.is_gp = TRUE"]
                simple_params: list[Any] = []
                if search:
                    conditions.append("(o.name ILIKE %s OR o.hq_city ILIKE %s OR gp.investment_philosophy ILIKE %s)")
                    simple_params.extend([f"%{search}%", f"%{search}%", f"%{search}%"])
                if strategy:
                    conditions.append("gp.investment_philosophy ILIKE %s")
                    simple_params.append(f"%{strategy}%")
                where_clause = " AND ".join(conditions)
                params = simple_params

            query = base_query.format(where_clause=where_clause)
            cur.execute(query, params)
            gps = cur.fetchall()

            # Calculate total funds
            total_funds = sum(gp["fund_count"] or 0 for gp in gps)

        return templates.TemplateResponse(
            request,
            "pages/gps.html",
            {
                "title": "GPs - LPxGP",
                "user": user,
                "gps": gps,
                "total_funds": total_funds,
                "search": search or "",
                "strategy": strategy or "",
                "strategies": strategies,
                "parsed_filters": parsed_filters,  # Show what AI extracted
            },
        )
    finally:
        conn.close()


@router.post("/api/gps", response_class=HTMLResponse)
async def create_gp(
    request: Request,
    name: str = Form(...),
    hq_city: str | None = Form(default=None),
    hq_country: str | None = Form(default=None),
    website: str | None = Form(default=None),
    description: str | None = Form(default=None),
    spun_out_from: str | None = Form(default=None),
    team_size: int | None = Form(default=None),
    years_investing: int | None = Form(default=None),
    investment_philosophy: str | None = Form(default=None),
    notable_exits: str | None = Form(default=""),
):
    """Create a new GP (organization + gp_profile)."""
    conn = get_db()
    if not conn:
        return HTMLResponse(
            content="<p class='text-navy-500'>Database not configured</p>",
            status_code=503
        )

    try:
        # Parse notable exits as JSON array
        exits_arr = [e.strip() for e in notable_exits.split("\n") if e.strip()] if notable_exits else []
        exits_json = exits_arr  # Store as simple string array

        with conn.cursor() as cur:
            # Create organization
            cur.execute("""
                INSERT INTO organizations (name, website, hq_city, hq_country, description, is_gp)
                VALUES (%s, %s, %s, %s, %s, TRUE)
                RETURNING id
            """, (name, website, hq_city, hq_country, description))
            result = cur.fetchone()
            if not result:
                raise ValueError("Failed to create organization")
            org_id = result["id"]

            # Create gp_profile
            cur.execute("""
                INSERT INTO gp_profiles (
                    org_id, investment_philosophy, team_size, years_investing,
                    spun_out_from, notable_exits
                ) VALUES (%s, %s, %s, %s, %s, %s::jsonb)
            """, (
                org_id, investment_philosophy, team_size, years_investing,
                spun_out_from, json.dumps(exits_json)
            ))
            conn.commit()

        return HTMLResponse(
            content=f"""
            <div class="text-center p-4">
                <svg class="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                <h3 class="text-lg font-semibold text-navy-900 mb-2">GP Created!</h3>
                <p class="text-navy-500 mb-4">{name} has been added to the database.</p>
            </div>
            """,
            headers={"HX-Trigger": "gpCreated"}
        )
    except Exception as e:
        logger.error(f"Failed to create GP: {e}")
        conn.rollback()
        return HTMLResponse(
            content=f"<p class='text-red-500'>Failed to create GP: {str(e)}</p>",
            status_code=500
        )
    finally:
        conn.close()


@router.get("/api/gps/{gp_id}/edit", response_class=HTMLResponse)
async def get_gp_edit_form(request: Request, gp_id: str):
    """Get GP edit form with pre-populated data."""
    if not is_valid_uuid(gp_id):
        return HTMLResponse(content="<p class='text-red-500'>Invalid GP ID</p>", status_code=400)

    conn = get_db()
    if not conn:
        return HTMLResponse(content="<p class='text-navy-500'>Database not configured</p>", status_code=503)

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    o.id, o.name, o.hq_city, o.hq_country, o.website, o.description,
                    gp.investment_philosophy, gp.team_size, gp.years_investing,
                    gp.spun_out_from, gp.notable_exits
                FROM organizations o
                JOIN gp_profiles gp ON gp.org_id = o.id
                WHERE o.id = %s
            """, (gp_id,))
            gp = cur.fetchone()

            if not gp:
                return HTMLResponse(content="<p class='text-red-500'>GP not found</p>", status_code=404)

        return templates.TemplateResponse(
            "partials/gp_edit_modal.html",
            {"request": request, "gp": gp}
        )
    finally:
        conn.close()


@router.put("/api/gps/{gp_id}", response_class=HTMLResponse)
async def update_gp(
    request: Request,
    gp_id: str,
    name: str = Form(...),
    hq_city: str | None = Form(default=None),
    hq_country: str | None = Form(default=None),
    website: str | None = Form(default=None),
    description: str | None = Form(default=None),
    spun_out_from: str | None = Form(default=None),
    team_size: int | None = Form(default=None),
    years_investing: int | None = Form(default=None),
    investment_philosophy: str | None = Form(default=None),
    notable_exits: str | None = Form(default=""),
):
    """Update an existing GP."""
    if not is_valid_uuid(gp_id):
        return HTMLResponse(content="<p class='text-red-500'>Invalid GP ID</p>", status_code=400)

    conn = get_db()
    if not conn:
        return HTMLResponse(content="<p class='text-navy-500'>Database not configured</p>", status_code=503)

    try:
        # Parse notable exits as JSON array
        exits_arr = [e.strip() for e in notable_exits.split("\n") if e.strip()] if notable_exits else []
        exits_json = exits_arr

        with conn.cursor() as cur:
            # Update organization
            cur.execute("""
                UPDATE organizations SET
                    name = %s, website = %s, hq_city = %s, hq_country = %s,
                    description = %s, updated_at = NOW()
                WHERE id = %s
            """, (name, website, hq_city, hq_country, description, gp_id))

            # Update gp_profile
            cur.execute("""
                UPDATE gp_profiles SET
                    investment_philosophy = %s, team_size = %s, years_investing = %s,
                    spun_out_from = %s, notable_exits = %s::jsonb, updated_at = NOW()
                WHERE org_id = %s
            """, (
                investment_philosophy, team_size, years_investing,
                spun_out_from, json.dumps(exits_json), gp_id
            ))
            conn.commit()

        return HTMLResponse(
            content=f"""
            <div class="text-center p-4">
                <svg class="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                <h3 class="text-lg font-semibold text-navy-900 mb-2">GP Updated!</h3>
                <p class="text-navy-500 mb-4">{name} has been updated successfully.</p>
            </div>
            """,
            headers={"HX-Trigger": "gpUpdated"}
        )
    except Exception as e:
        logger.error(f"Failed to update GP: {e}")
        conn.rollback()
        return HTMLResponse(
            content=f"<p class='text-red-500'>Failed to update GP: {str(e)}</p>",
            status_code=500
        )
    finally:
        conn.close()


@router.delete("/api/gps/{gp_id}", response_class=HTMLResponse)
async def delete_gp(request: Request, gp_id: str):
    """Delete a GP (organization + gp_profile via CASCADE)."""
    if not is_valid_uuid(gp_id):
        return HTMLResponse(content="<p class='text-red-500'>Invalid GP ID</p>", status_code=400)

    conn = get_db()
    if not conn:
        return HTMLResponse(content="<p class='text-navy-500'>Database not configured</p>", status_code=503)

    try:
        with conn.cursor() as cur:
            # Get GP name
            cur.execute("SELECT name FROM organizations WHERE id = %s", (gp_id,))
            org = cur.fetchone()
            if not org:
                return HTMLResponse(content="<p class='text-red-500'>GP not found</p>", status_code=404)
            gp_name = org["name"]

            # Delete organization (CASCADE deletes gp_profile)
            cur.execute("DELETE FROM organizations WHERE id = %s", (gp_id,))
            conn.commit()

        return HTMLResponse(
            content=f"""
            <div class="text-center p-4">
                <svg class="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                <h3 class="text-lg font-semibold text-navy-900 mb-2">GP Deleted</h3>
                <p class="text-navy-500 mb-4">{gp_name} has been removed.</p>
            </div>
            """,
            headers={"HX-Trigger": "gpDeleted"}
        )
    except Exception as e:
        logger.error(f"Failed to delete GP: {e}")
        conn.rollback()
        return HTMLResponse(
            content=f"<p class='text-red-500'>Failed to delete GP: {str(e)}</p>",
            status_code=500
        )
    finally:
        conn.close()


@router.get("/api/gp/{gp_id}/detail", response_class=HTMLResponse)
async def get_gp_detail(request: Request, gp_id: str):
    """Get GP detail partial for modal display."""
    if not is_valid_uuid(gp_id):
        return HTMLResponse(content="<p class='text-red-500'>Invalid GP ID</p>", status_code=400)

    conn = get_db()
    if not conn:
        return HTMLResponse(content="<p class='text-navy-500'>Database not configured</p>", status_code=503)

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    o.id, o.name, o.hq_city, o.hq_country, o.website, o.description,
                    gp.investment_philosophy, gp.team_size, gp.years_investing,
                    gp.spun_out_from, gp.notable_exits,
                    (SELECT COUNT(*) FROM funds f WHERE f.org_id = o.id) as fund_count
                FROM organizations o
                JOIN gp_profiles gp ON gp.org_id = o.id
                WHERE o.id = %s
            """, (gp_id,))
            gp = cur.fetchone()

            if not gp:
                return HTMLResponse(content="<p class='text-red-500'>GP not found</p>", status_code=404)

            # Get associated funds
            cur.execute("""
                SELECT id, name, status, vintage_year, target_size_mm, strategy
                FROM funds
                WHERE org_id = %s
                ORDER BY vintage_year DESC NULLS LAST
            """, (gp_id,))
            funds = cur.fetchall()

        return templates.TemplateResponse(
            "partials/gp_detail_modal.html",
            {"request": request, "gp": gp, "funds": funds}
        )
    finally:
        conn.close()
