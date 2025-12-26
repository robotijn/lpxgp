"""Fund management routes for creating, viewing, and managing GP funds.

This router provides:
- GET /funds: Funds listing page (HTML)
- GET /funds/{fund_id}: Fund detail page (HTML)
- GET /api/v1/funds: REST API for fund search
- POST /api/funds: Create a new fund
- GET /api/funds/{fund_id}/edit: Get fund edit form
- PUT /api/funds/{fund_id}: Update a fund
- DELETE /api/funds/{fund_id}: Delete a fund
- POST /api/funds/{fund_id}/generate-matches: Generate AI matches
- GET /api/organizations/gp: Get list of GP organizations
"""

from __future__ import annotations

import json
from decimal import Decimal
from pathlib import Path
from typing import Any, cast
from uuid import UUID

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src import auth
from src.config import get_settings
from src.database import get_db
from src.logging_config import get_logger
from src.utils import is_valid_uuid

logger = get_logger(__name__)

router = APIRouter(tags=["funds"])

# Templates setup
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=templates_path)


def serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert a database row dict to JSON-serializable format.

    Converts UUID objects to strings and Decimal to float for JSON serialization.
    """
    result: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, UUID):
            result[key] = str(value)
        elif isinstance(value, Decimal):
            result[key] = float(value)
        else:
            result[key] = value
    return result


# =============================================================================
# Fund Pages
# =============================================================================


@router.get("/funds", response_class=HTMLResponse, response_model=None)
async def funds_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Funds page listing GP fund profiles.

    Requires authentication.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    empty_response = {
        "title": "Funds - LPxGP",
        "user": user,
        "funds": [],
        "gp_orgs": [],
        "total_target": 0,
        "raising_count": 0,
    }

    conn = get_db()
    if not conn:
        return templates.TemplateResponse(request, "pages/funds.html", empty_response)

    try:
        with conn.cursor() as cur:
            # Get funds
            cur.execute("""
                SELECT
                    f.id, f.name, f.status, f.vintage_year,
                    f.target_size_mm, f.current_size_mm,
                    f.strategy, f.sub_strategy,
                    f.geographic_focus, f.sector_focus,
                    o.name as gp_name,
                    (SELECT COUNT(*) FROM fund_lp_matches m WHERE m.fund_id = f.id) as match_count
                FROM funds f
                JOIN organizations o ON o.id = f.org_id
                ORDER BY f.created_at DESC
            """)
            funds = cur.fetchall()

            # Get GP organizations for the create form
            cur.execute("""
                SELECT id, name FROM organizations
                WHERE is_gp = TRUE
                ORDER BY name
            """)
            gp_orgs = cur.fetchall()

        # Calculate stats
        total_target = sum(f["target_size_mm"] or 0 for f in funds)
        raising_count = sum(1 for f in funds if f["status"] == "raising")

        return templates.TemplateResponse(
            request,
            "pages/funds.html",
            {
                "title": "Funds - LPxGP",
                "funds": funds,
                "gp_orgs": gp_orgs,
                "total_target": total_target,
                "raising_count": raising_count,
            },
        )
    finally:
        conn.close()


@router.get("/funds/{fund_id}", response_class=HTMLResponse, response_model=None)
async def fund_detail_page(request: Request, fund_id: str) -> HTMLResponse | RedirectResponse:
    """Fund detail page showing full fund profile.

    Requires authentication.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not is_valid_uuid(fund_id):
        return HTMLResponse(content="Invalid Fund ID", status_code=400)

    # Mock fund data for offline mode
    mock_fund = {
        "id": fund_id,
        "name": "Growth Fund III",
        "status": "fundraising",
        "strategy": "private_equity",
        "primary_strategy": "growth_equity",
        "target_size_mm": 500,
        "raised_mm": 150,
        "target_close": "Q2 2025",
        "geo_focus": "North America",
        "sectors": ["Technology", "Healthcare"],
        "check_min_mm": 25,
        "check_max_mm": 75,
        "stage": "Growth / Expansion",
        "prior_moic": "2.3",
        "prior_irr": "28.5",
        "portfolio_count": 18,
        "capital_deployed_mm": 550,
        "total_matches": 45,
        "high_score_matches": 12,
        "shortlisted": 8,
        "contacted": 5,
    }

    conn = get_db()
    if not conn:
        return templates.TemplateResponse(
            request,
            "pages/fund-detail.html",
            {"title": f"{mock_fund['name']} - LPxGP", "user": user, "fund": mock_fund},
        )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT id, name, status, target_size_mm, vintage_year,
                       strategy, geo_focus, sector_focus
                FROM funds
                WHERE id = %s
                """,
                (fund_id,),
            )
            fund = cur.fetchone()

            if not fund:
                # Fall back to mock data if fund not in database
                return templates.TemplateResponse(
                    request,
                    "pages/fund-detail.html",
                    {"title": f"{mock_fund['name']} - LPxGP", "user": user, "fund": mock_fund},
                )

        return templates.TemplateResponse(
            request,
            "pages/fund-detail.html",
            {"title": f"{fund['name']} - LPxGP", "user": user, "fund": fund},
        )
    except Exception:
        # Fall back to mock data on any database error
        return templates.TemplateResponse(
            request,
            "pages/fund-detail.html",
            {"title": f"{mock_fund['name']} - LPxGP", "user": user, "fund": mock_fund},
        )
    finally:
        conn.close()


# =============================================================================
# REST API V1: Fund Search
# =============================================================================


@router.get("/api/v1/funds", response_class=JSONResponse)
async def api_v1_funds(
    request: Request,
    search: str | None = Query(None),
    strategy: str | None = Query(None),
    status: str | None = Query(None),
    vintage_year: int | None = Query(None),
    page: int = Query(1, ge=1),
    per_page: int = Query(20, ge=1, le=100),
) -> JSONResponse:
    """REST API endpoint for Fund search.

    Returns JSON for programmatic access.
    Supports filtering by strategy, status, vintage_year.
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
            conditions = ["1=1"]
            params: list[Any] = []

            if search:
                conditions.append("(f.name ILIKE %s OR o.name ILIKE %s)")
                params.extend([f"%{search}%", f"%{search}%"])

            if strategy:
                conditions.append("f.strategy = %s")
                params.append(strategy)

            if status:
                conditions.append("f.status = %s")
                params.append(status)

            if vintage_year:
                conditions.append("f.vintage_year = %s")
                params.append(vintage_year)

            where_clause = " AND ".join(conditions)

            # Count total
            count_query = f"""
                SELECT COUNT(*) as total
                FROM funds f
                JOIN organizations o ON o.id = f.org_id
                WHERE {where_clause}
            """
            cur.execute(count_query, params)
            count_row = cur.fetchone()
            total = count_row["total"] if count_row else 0

            # Fetch paginated results
            offset = (page - 1) * per_page
            data_query = f"""
                SELECT
                    f.id, f.name, f.strategy, f.status, f.vintage_year,
                    f.target_size_mm, f.hard_cap_mm, f.check_size_min_mm,
                    o.id as org_id, o.name as org_name
                FROM funds f
                JOIN organizations o ON o.id = f.org_id
                WHERE {where_clause}
                ORDER BY f.vintage_year DESC NULLS LAST, f.name
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
        logger.error(f"API v1 Fund search error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error", "code": "SERVER_ERROR"},
        )
    finally:
        conn.close()


# =============================================================================
# Fund CRUD API Endpoints
# =============================================================================


@router.post("/api/funds", response_class=HTMLResponse)
async def create_fund(
    request: Request,
    name: str = Form(...),
    org_id: str = Form(...),
    status: str = Form(default="draft"),
    vintage_year: int | None = Form(default=None),
    target_size_mm: float | None = Form(default=None),
    strategy: str | None = Form(default=None),
    sub_strategy: str | None = Form(default=None),
    geographic_focus: str | None = Form(default=""),
    sector_focus: str | None = Form(default=""),
    check_size_min_mm: float | None = Form(default=None),
    check_size_max_mm: float | None = Form(default=None),
    investment_thesis: str | None = Form(default=None),
    management_fee_pct: float | None = Form(default=None),
    carried_interest_pct: float | None = Form(default=None),
    gp_commitment_pct: float | None = Form(default=None),
):
    """Create a new fund."""
    if not is_valid_uuid(org_id):
        return HTMLResponse(
            content="<p class='text-red-500'>Invalid organization ID</p>",
            status_code=400
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content="<p class='text-navy-500'>Database not configured</p>",
            status_code=503
        )

    try:
        # Parse array fields (comma-separated)
        geo_array = [g.strip() for g in geographic_focus.split(",") if g.strip()] if geographic_focus else []
        sector_array = [s.strip() for s in sector_focus.split(",") if s.strip()] if sector_focus else []

        with conn.cursor() as cur:
            cur.execute("""
                INSERT INTO funds (
                    org_id, name, status, vintage_year, target_size_mm,
                    strategy, sub_strategy, geographic_focus, sector_focus,
                    check_size_min_mm, check_size_max_mm, investment_thesis,
                    management_fee_pct, carried_interest_pct, gp_commitment_pct
                ) VALUES (
                    %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s
                ) RETURNING id
            """, (
                org_id, name, status, vintage_year, target_size_mm,
                strategy, sub_strategy, geo_array, sector_array,
                check_size_min_mm, check_size_max_mm, investment_thesis,
                management_fee_pct, carried_interest_pct, gp_commitment_pct
            ))
            result = cur.fetchone()
            _ = result["id"] if result else None  # Verify insert succeeded
            conn.commit()

        # Return success with redirect
        return HTMLResponse(
            content=f"""
            <div class="text-center p-4">
                <svg class="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                <h3 class="text-lg font-semibold text-navy-900 mb-2">Fund Created!</h3>
                <p class="text-navy-500 mb-4">{name} has been created successfully.</p>
                <a href="/funds" class="btn-primary">View All Funds</a>
            </div>
            """,
            headers={"HX-Trigger": "fundCreated"}
        )
    except Exception as e:
        logger.error(f"Failed to create fund: {e}")
        conn.rollback()
        return HTMLResponse(
            content=f"<p class='text-red-500'>Failed to create fund: {e!s}</p>",
            status_code=500
        )
    finally:
        conn.close()


@router.get("/api/organizations/gp", response_class=JSONResponse)
async def get_gp_organizations():
    """Get list of GP organizations for fund creation."""
    conn = get_db()
    if not conn:
        return JSONResponse(content=[], status_code=200)

    try:
        with conn.cursor() as cur:
            cur.execute("""
                SELECT id, name FROM organizations
                WHERE is_gp = TRUE
                ORDER BY name
            """)
            orgs = cur.fetchall()
        return JSONResponse(content=[dict(o) for o in orgs])
    finally:
        conn.close()


@router.get("/api/funds/{fund_id}/edit", response_class=HTMLResponse)
async def get_fund_edit_form(request: Request, fund_id: str):
    """Get fund edit form with pre-populated data."""
    if not is_valid_uuid(fund_id):
        return HTMLResponse(content="<p class='text-red-500'>Invalid fund ID</p>", status_code=400)

    conn = get_db()
    if not conn:
        return HTMLResponse(content="<p class='text-navy-500'>Database not configured</p>", status_code=503)

    try:
        with conn.cursor() as cur:
            # Get fund data
            cur.execute("""
                SELECT f.*, o.name as gp_name
                FROM funds f
                JOIN organizations o ON f.org_id = o.id
                WHERE f.id = %s
            """, (fund_id,))
            fund = cur.fetchone()

            if not fund:
                return HTMLResponse(content="<p class='text-red-500'>Fund not found</p>", status_code=404)

            # Get GP organizations for dropdown
            cur.execute("""
                SELECT id, name FROM organizations
                WHERE is_gp = TRUE
                ORDER BY name
            """)
            gp_orgs = cur.fetchall()

        return templates.TemplateResponse(
            "partials/fund_edit_modal.html",
            {"request": request, "fund": fund, "gp_orgs": gp_orgs}
        )
    finally:
        conn.close()


@router.put("/api/funds/{fund_id}", response_class=HTMLResponse)
async def update_fund(
    request: Request,
    fund_id: str,
    name: str = Form(...),
    org_id: str = Form(...),
    status: str = Form(default="draft"),
    vintage_year: int | None = Form(default=None),
    target_size_mm: float | None = Form(default=None),
    strategy: str | None = Form(default=None),
    sub_strategy: str | None = Form(default=None),
    geographic_focus: str | None = Form(default=""),
    sector_focus: str | None = Form(default=""),
    check_size_min_mm: float | None = Form(default=None),
    check_size_max_mm: float | None = Form(default=None),
    investment_thesis: str | None = Form(default=None),
    management_fee_pct: float | None = Form(default=None),
    carried_interest_pct: float | None = Form(default=None),
    gp_commitment_pct: float | None = Form(default=None),
):
    """Update an existing fund."""
    if not is_valid_uuid(fund_id) or not is_valid_uuid(org_id):
        return HTMLResponse(
            content="<p class='text-red-500'>Invalid ID</p>",
            status_code=400
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content="<p class='text-navy-500'>Database not configured</p>",
            status_code=503
        )

    try:
        # Parse array fields (comma-separated)
        geo_array = [g.strip() for g in geographic_focus.split(",") if g.strip()] if geographic_focus else []
        sector_array = [s.strip() for s in sector_focus.split(",") if s.strip()] if sector_focus else []

        with conn.cursor() as cur:
            cur.execute("""
                UPDATE funds SET
                    org_id = %s,
                    name = %s,
                    status = %s,
                    vintage_year = %s,
                    target_size_mm = %s,
                    strategy = %s,
                    sub_strategy = %s,
                    geographic_focus = %s,
                    sector_focus = %s,
                    check_size_min_mm = %s,
                    check_size_max_mm = %s,
                    investment_thesis = %s,
                    management_fee_pct = %s,
                    carried_interest_pct = %s,
                    gp_commitment_pct = %s,
                    updated_at = NOW()
                WHERE id = %s
            """, (
                org_id, name, status, vintage_year, target_size_mm,
                strategy, sub_strategy, geo_array, sector_array,
                check_size_min_mm, check_size_max_mm, investment_thesis,
                management_fee_pct, carried_interest_pct, gp_commitment_pct,
                fund_id
            ))
            conn.commit()

        return HTMLResponse(
            content=f"""
            <div class="text-center p-4">
                <svg class="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                <h3 class="text-lg font-semibold text-navy-900 mb-2">Fund Updated!</h3>
                <p class="text-navy-500 mb-4">{name} has been updated successfully.</p>
            </div>
            """,
            headers={"HX-Trigger": "fundUpdated"}
        )
    except Exception as e:
        logger.error(f"Failed to update fund: {e}")
        conn.rollback()
        return HTMLResponse(
            content=f"<p class='text-red-500'>Failed to update fund: {e!s}</p>",
            status_code=500
        )
    finally:
        conn.close()


@router.delete("/api/funds/{fund_id}", response_class=HTMLResponse)
async def delete_fund(request: Request, fund_id: str):
    """Delete a fund."""
    if not is_valid_uuid(fund_id):
        return HTMLResponse(
            content="<p class='text-red-500'>Invalid fund ID</p>",
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
            # Get fund name for confirmation message
            cur.execute("SELECT name FROM funds WHERE id = %s", (fund_id,))
            fund = cur.fetchone()
            if not fund:
                return HTMLResponse(
                    content="<p class='text-red-500'>Fund not found</p>",
                    status_code=404
                )
            fund_name = fund["name"]

            # Delete the fund
            cur.execute("DELETE FROM funds WHERE id = %s", (fund_id,))
            conn.commit()

        return HTMLResponse(
            content=f"""
            <div class="text-center p-4">
                <svg class="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                <h3 class="text-lg font-semibold text-navy-900 mb-2">Fund Deleted</h3>
                <p class="text-navy-500 mb-4">{fund_name} has been deleted.</p>
            </div>
            """,
            headers={"HX-Trigger": "fundDeleted"}
        )
    except Exception as e:
        logger.error(f"Failed to delete fund: {e}")
        conn.rollback()
        return HTMLResponse(
            content=f"<p class='text-red-500'>Failed to delete fund: {e!s}</p>",
            status_code=500
        )
    finally:
        conn.close()


@router.post("/api/funds/{fund_id}/generate-matches", response_class=HTMLResponse)
async def generate_matches_for_fund(request: Request, fund_id: str):
    """Generate AI-powered matches for a fund against all LPs."""
    from src.matching import (
        FundData,
        LPData,
        calculate_match_score,
        generate_match_content,
    )

    if not is_valid_uuid(fund_id):
        return HTMLResponse(
            content="<p class='text-red-500'>Invalid fund ID</p>",
            status_code=400
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content="<p class='text-navy-500'>Database not configured</p>",
            status_code=503
        )

    settings = get_settings()
    matches_generated = 0
    matches_skipped = 0

    try:
        with conn.cursor() as cur:
            # Fetch fund details with GP info
            cur.execute("""
                SELECT f.*, o.name as gp_name
                FROM funds f
                JOIN organizations o ON o.id = f.org_id
                WHERE f.id = %s
            """, (fund_id,))
            fund = cur.fetchone()

            if not fund:
                return HTMLResponse(
                    content="<p class='text-red-500'>Fund not found</p>",
                    status_code=404
                )

            # Fetch all LP profiles with organization info
            cur.execute("""
                SELECT lp.*, o.name, o.hq_city, o.hq_country
                FROM lp_profiles lp
                JOIN organizations o ON o.id = lp.org_id
                WHERE o.is_lp = true
            """)
            lps = cur.fetchall()

            for lp in lps:
                # Calculate match score (cast dict to TypedDict for type safety)
                fund_data = cast(FundData, dict(fund))
                lp_data = cast(LPData, dict(lp))
                result = calculate_match_score(fund_data, lp_data)

                # Only create matches for scores above threshold
                if result["score"] >= 50:
                    # Generate LLM content
                    content = await generate_match_content(
                        fund_data,
                        lp_data,
                        result["score_breakdown"],
                        ollama_base_url=settings.ollama_base_url,
                        ollama_model=settings.ollama_model
                    )

                    # Upsert match
                    cur.execute("""
                        INSERT INTO fund_lp_matches
                            (fund_id, lp_org_id, score, score_breakdown, explanation, talking_points, concerns, model_version)
                        VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                        ON CONFLICT (fund_id, lp_org_id)
                        DO UPDATE SET
                            score = EXCLUDED.score,
                            score_breakdown = EXCLUDED.score_breakdown,
                            explanation = EXCLUDED.explanation,
                            talking_points = EXCLUDED.talking_points,
                            concerns = EXCLUDED.concerns,
                            model_version = EXCLUDED.model_version,
                            created_at = NOW()
                    """, (
                        fund_id,
                        lp["org_id"],
                        result["score"],
                        json.dumps(result["score_breakdown"]),
                        content["explanation"],
                        content["talking_points"],
                        content["concerns"],
                        settings.ollama_model
                    ))
                    matches_generated += 1
                else:
                    matches_skipped += 1

            conn.commit()

        return HTMLResponse(
            content=f"""
            <div class="text-center p-4">
                <svg class="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                </svg>
                <h3 class="text-lg font-semibold text-navy-900 mb-2">Matches Generated</h3>
                <p class="text-navy-500 mb-2">Found {matches_generated} matching LPs for {fund['name']}</p>
                <p class="text-navy-400 text-sm">{matches_skipped} LPs did not meet criteria</p>
            </div>
            """,
            headers={"HX-Trigger": "matchesGenerated"}
        )
    except Exception as e:
        logger.error(f"Failed to generate matches: {e}")
        conn.rollback()
        return HTMLResponse(
            content=f"<p class='text-red-500'>Failed to generate matches: {e!s}</p>",
            status_code=500
        )
    finally:
        conn.close()
