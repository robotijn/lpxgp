"""LP API endpoints for browsing and managing LP profiles.

This router provides:
- /lps: LP browse page (HTML)
- /lps/{lp_id}: LP detail page (HTML)
- /api/v1/lps: REST API for LP search with filters
- /api/lp/{lp_id}/detail: LP detail modal (HTMX partial)
- /api/lps: CRUD operations for LPs
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src import auth
from src.database import get_db
from src.logging_config import get_logger
from src.search import (
    build_lp_search_sql,
    is_natural_language_query,
    parse_lp_search_query,
)
from src.shortlists import is_in_shortlist
from src.utils import is_valid_uuid, serialize_row

logger = get_logger(__name__)

router = APIRouter(tags=["lps"])

# Templates setup
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=templates_path)


@router.get("/lps", response_class=HTMLResponse, response_model=None)
async def lps_page(
    request: Request,
    search: str | None = Query(None),
    lp_type: str | None = Query(None),
) -> HTMLResponse | RedirectResponse:
    """LPs page for browsing and searching LP profiles.

    Requires authentication.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    empty_response = {
        "title": "LPs - LPxGP",
        "user": user,
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
            base_query = """
                SELECT
                    o.id, o.name, o.hq_city, o.hq_country, o.website,
                    lp.lp_type, lp.total_aum_bn, lp.pe_allocation_pct,
                    lp.check_size_min_mm, lp.check_size_max_mm,
                    lp.geographic_preferences, lp.strategies
                FROM organizations o
                JOIN lp_profiles lp ON lp.org_id = o.id
                WHERE {where_clause}
                ORDER BY lp.total_aum_bn DESC NULLS LAST
                LIMIT 100
            """

            # Check if search is natural language (AI parsing) or simple text
            parsed_filters: dict[str, Any] = {}
            if search and is_natural_language_query(search):
                # Use AI to parse the query
                parsed_filters = await parse_lp_search_query(search)
                # Add lp_type from dropdown if specified
                if lp_type:
                    parsed_filters["lp_type"] = lp_type
                where_clause, params = build_lp_search_sql(parsed_filters)
            else:
                # Simple text search
                conditions = ["o.is_lp = TRUE"]
                simple_params: list[Any] = []
                if search:
                    conditions.append("(o.name ILIKE %s OR o.hq_city ILIKE %s)")
                    simple_params.extend([f"%{search}%", f"%{search}%"])
                if lp_type:
                    conditions.append("lp.lp_type = %s")
                    simple_params.append(lp_type)
                where_clause = " AND ".join(conditions)
                params = simple_params

            query = base_query.format(where_clause=where_clause)
            cur.execute(query, params)
            lps = cur.fetchall()

        # Calculate stats
        total_aum = sum(lp["total_aum_bn"] or 0 for lp in lps)

        return templates.TemplateResponse(
            request,
            "pages/lps.html",
            {
                "title": "LPs - LPxGP",
                "user": user,
                "lps": lps,
                "total_aum": total_aum,
                "search": search or "",
                "lp_type": lp_type or "",
                "lp_types": lp_types,
                "parsed_filters": parsed_filters,  # Show what AI extracted
            },
        )
    finally:
        conn.close()


@router.get("/api/v1/lps", response_class=JSONResponse)
async def api_v1_lps(
    request: Request,
    search: str | None = Query(None),
    lp_type: str | None = Query(None),
    aum_min: float | None = Query(None, description="Minimum AUM in billions"),
    aum_max: float | None = Query(None, description="Maximum AUM in billions"),
    location: str | None = Query(None),
    strategy: str | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> JSONResponse:
    """REST API endpoint for LP search.

    Returns JSON for programmatic access.
    Supports filtering by type, AUM, location, strategy.
    Supports pagination.

    Args:
        search: Text search or natural language query
        lp_type: Filter by LP type (pension, endowment, etc.)
        aum_min: Minimum AUM in billions
        aum_max: Maximum AUM in billions
        location: Filter by city or country
        strategy: Filter by investment strategy
        page: Page number (1-indexed)
        per_page: Results per page (max 100)

    Returns:
        JSON with data, total, page, per_page fields
    """
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required", "code": "UNAUTHORIZED"},
        )

    # Validate page number
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
            # Build filters
            conditions = ["o.is_lp = TRUE"]
            params: list[Any] = []

            # Text search
            if search:
                conditions.append("(o.name ILIKE %s OR o.hq_city ILIKE %s)")
                params.extend([f"%{search}%", f"%{search}%"])

            # LP type filter
            if lp_type:
                conditions.append("lp.lp_type = %s")
                params.append(lp_type)

            # AUM filters
            if aum_min is not None:
                conditions.append("lp.total_aum_bn >= %s")
                params.append(aum_min)
            if aum_max is not None:
                conditions.append("lp.total_aum_bn <= %s")
                params.append(aum_max)

            # Location filter
            if location:
                conditions.append("(o.hq_city ILIKE %s OR o.hq_country ILIKE %s)")
                params.extend([f"%{location}%", f"%{location}%"])

            # Strategy filter
            if strategy:
                conditions.append("%s = ANY(lp.strategies)")
                params.append(strategy)

            where_clause = " AND ".join(conditions)

            # Count total
            count_query = f"""
                SELECT COUNT(*) as total
                FROM organizations o
                JOIN lp_profiles lp ON lp.org_id = o.id
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
                    lp.lp_type, lp.total_aum_bn, lp.pe_allocation_pct,
                    lp.check_size_min_mm, lp.check_size_max_mm,
                    lp.geographic_preferences, lp.strategies
                FROM organizations o
                JOIN lp_profiles lp ON lp.org_id = o.id
                WHERE {where_clause}
                ORDER BY lp.total_aum_bn DESC NULLS LAST
                LIMIT %s OFFSET %s
            """
            cur.execute(data_query, [*params, per_page, offset])
            rows = cur.fetchall()

            # Convert to list of dicts
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
        logger.error(f"API v1 LP search error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "code": "SERVER_ERROR"},
        )
    finally:
        conn.close()


@router.get("/lps/{lp_id}", response_class=HTMLResponse, response_model=None)
async def lp_detail_page(request: Request, lp_id: str) -> HTMLResponse | RedirectResponse:
    """LP detail page showing full profile and match analysis.

    Requires authentication.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not is_valid_uuid(lp_id):
        return HTMLResponse(content="Invalid LP ID", status_code=400)

    # Mock LP data for offline mode
    mock_lp = {
        "id": lp_id,
        "name": "CalPERS",
        "full_name": "California Public Employees' Retirement System",
        "lp_type": "Public Pension",
        "hq_city": "Sacramento",
        "hq_country": "USA",
        "total_aum_bn": 450.0,
        "pe_allocation_pct": 13.0,
        "check_size_min_mm": 100,
        "check_size_max_mm": 500,
        "target_return": "Net IRR 11%+",
        "geo_preferences": "North America, Europe",
        "strategies": ["buyout", "growth_equity", "venture"],
        "score": 92,
        "in_shortlist": is_in_shortlist(user["id"], lp_id),
        "contacts": [
            {"name": "Michael Smith", "title": "Managing Investment Director, Private Equity"},
            {"name": "Jennifer Chen", "title": "Investment Director, Growth Equity"},
        ],
    }

    conn = get_db()
    if not conn:
        return templates.TemplateResponse(
            request,
            "pages/lp-detail.html",
            {"title": f"{mock_lp['name']} - LPxGP", "user": user, "lp": mock_lp},
        )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT o.id, o.name, o.hq_city, o.hq_country, o.website,
                       lp.lp_type, lp.total_aum_bn, lp.pe_allocation_pct,
                       lp.check_size_min_mm, lp.check_size_max_mm,
                       lp.geographic_preferences, lp.strategies
                FROM organizations o
                JOIN lp_profiles lp ON lp.org_id = o.id
                WHERE o.id = %s
                """,
                (lp_id,),
            )
            lp = cur.fetchone()

            if not lp:
                # Fall back to mock data if LP not in database
                return templates.TemplateResponse(
                    request,
                    "pages/lp-detail.html",
                    {"title": f"{mock_lp['name']} - LPxGP", "user": user, "lp": mock_lp},
                )

            lp["in_shortlist"] = is_in_shortlist(user["id"], lp_id)
            lp["score"] = 85  # Default score

        return templates.TemplateResponse(
            request,
            "pages/lp-detail.html",
            {"title": f"{lp['name']} - LPxGP", "user": user, "lp": lp},
        )
    finally:
        conn.close()


@router.get("/api/lp/{lp_id}/detail", response_class=HTMLResponse)
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


# -----------------------------------------------------------------------------
# LP CRUD Endpoints
# -----------------------------------------------------------------------------

@router.post("/api/lps", response_class=HTMLResponse)
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
    from html import escape

    # Input validation
    # Sanitize name: remove null bytes and strip whitespace
    name = name.replace("\x00", "").strip()
    if not name:
        return HTMLResponse(
            content="<p class='text-red-500'>Name cannot be empty or whitespace only</p>",
            status_code=400,
        )
    if len(name) > 500:
        return HTMLResponse(
            content="<p class='text-red-500'>Name too long (max 500 characters)</p>",
            status_code=400,
        )

    # Validate numeric fields - must be non-negative
    if total_aum_bn is not None and total_aum_bn < 0:
        return HTMLResponse(
            content="<p class='text-red-500'>Total AUM cannot be negative</p>",
            status_code=400,
        )

    # Validate percentages (0-100)
    if pe_allocation_pct is not None and (pe_allocation_pct < 0 or pe_allocation_pct > 100):
        return HTMLResponse(
            content="<p class='text-red-500'>PE allocation must be between 0 and 100</p>",
            status_code=400,
        )

    # Validate sizes - must be non-negative
    for field_name, field_val in [
        ("Check size min", check_size_min_mm),
        ("Check size max", check_size_max_mm),
        ("Fund size min", fund_size_min_mm),
        ("Fund size max", fund_size_max_mm),
    ]:
        if field_val is not None and field_val < 0:
            return HTMLResponse(
                content=f"<p class='text-red-500'>{field_name} cannot be negative</p>",
                status_code=400,
            )

    # Validate LP type enum if provided
    valid_lp_types = [
        "pension", "endowment", "foundation", "family_office",
        "insurance", "sovereign_wealth", "fund_of_funds", "corporate",
        "bank", "other", None
    ]
    if lp_type and lp_type not in valid_lp_types:
        return HTMLResponse(
            content=f"<p class='text-red-500'>Invalid LP type: {escape(lp_type)}</p>",
            status_code=400,
        )

    # XSS prevention - escape HTML in name for response
    safe_name = escape(name)

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
            result = cur.fetchone()
            if not result:
                raise ValueError("Failed to create organization")
            org_id = result["id"]

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
                <p class="text-navy-500 mb-4">{safe_name} has been added to the database.</p>
            </div>
            """,
            headers={"HX-Trigger": "lpCreated"}
        )
    except Exception as e:
        logger.error(f"Failed to create LP: {e}")
        conn.rollback()
        error_msg = str(e).lower()
        # Return 400 for constraint violations (user input errors)
        if "constraint" in error_msg or "violates" in error_msg:
            return HTMLResponse(
                content="<p class='text-red-500'>Invalid input data. Please check your values.</p>",
                status_code=400,
            )
        return HTMLResponse(
            content="<p class='text-red-500'>Failed to create LP. Please try again.</p>",
            status_code=400
        )
    finally:
        conn.close()


@router.get("/api/lps/{lp_id}/edit", response_class=HTMLResponse)
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


@router.put("/api/lps/{lp_id}", response_class=HTMLResponse)
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


@router.delete("/api/lps/{lp_id}", response_class=HTMLResponse)
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
