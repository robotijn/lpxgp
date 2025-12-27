"""LP Portal routes for LP-specific views and actions.

This router provides:
- /lp-dashboard: LP dashboard showing fund matches and pipeline
- /lp-watchlist: LP watchlist page for tracking interesting funds
- /lp-pipeline: LP pipeline view (kanban-style fund tracking)
- /lp-mandate: LP mandate profile editor
- /lp-meeting-request: Request meeting with a GP
- /api/lp/fund/{fund_id}/interest: Update LP interest in a fund
- /api/v1/lp-pipeline/{fund_id}: Update LP pipeline stage
- /api/lp-mandate: Save LP mandate preferences
- /api/lp-meeting-request: Submit meeting request
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from src import auth
from src.database import get_db
from src.logging_config import get_logger
from src.utils import is_valid_uuid

logger = get_logger(__name__)

router = APIRouter(tags=["lp_portal"])

# Templates setup
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=templates_path)

# Valid LP pipeline stages (LP perspective on funds)
VALID_LP_PIPELINE_STAGES = [
    "watching",
    "interested",
    "reviewing",
    "dd_in_progress",
    "passed",
]


class LPPipelineStageUpdateRequest(BaseModel):
    """Request body for updating LP pipeline stage."""

    stage: str = Field(
        ...,
        description="LP Pipeline stage",
        pattern="^(watching|interested|reviewing|dd_in_progress|passed)$",
    )
    notes: str | None = None


@router.get("/lp-dashboard", response_class=HTMLResponse, response_model=None)
async def lp_dashboard(request: Request) -> HTMLResponse | RedirectResponse:
    """LP-specific dashboard showing fund matches and pipeline.

    For LPs to view and manage incoming fund opportunities.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Dashboard data
    matches: list[dict[str, Any]] = []
    watchlist: list[dict[str, Any]] = []
    pipeline_stats = {
        "interested": 0,
        "reviewing": 0,
        "dd_in_progress": 0,
        "passed": 0,
    }

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                # Get LP's organization through employment
                cur.execute(
                    """
                    SELECT o.id as lp_org_id
                    FROM people p
                    JOIN employment e ON e.person_id = p.id AND e.is_current = TRUE
                    JOIN organizations o ON o.id = e.org_id
                    WHERE p.auth_user_id = %s AND o.is_lp = TRUE
                    """,
                    (user.get("id"),),
                )
                lp_org = cur.fetchone()

                if lp_org:
                    lp_org_id = lp_org["lp_org_id"]

                    # Get fund matches for this LP
                    cur.execute(
                        """
                        SELECT
                            m.id, m.fund_id, m.score, m.explanation,
                            m.talking_points, m.concerns,
                            f.name as fund_name, f.target_size_mm, f.strategy,
                            f.vintage_year,
                            gp.name as gp_name,
                            s.lp_interest, s.pipeline_stage
                        FROM fund_lp_matches m
                        JOIN funds f ON f.id = m.fund_id
                        JOIN organizations gp ON gp.id = f.org_id
                        LEFT JOIN fund_lp_status s
                            ON s.fund_id = m.fund_id AND s.lp_org_id = m.lp_org_id
                        WHERE m.lp_org_id = %s
                        ORDER BY m.score DESC
                        LIMIT 20
                        """,
                        (lp_org_id,),
                    )
                    matches = cur.fetchall()

                    # Get watchlist
                    cur.execute(
                        """
                        SELECT
                            f.id, f.name, f.target_size_mm, f.strategy,
                            gp.name as gp_name,
                            s.lp_interest, s.notes
                        FROM fund_lp_status s
                        JOIN funds f ON f.id = s.fund_id
                        JOIN organizations gp ON gp.id = f.org_id
                        WHERE s.lp_org_id = %s AND s.lp_interest = 'watching'
                        ORDER BY s.updated_at DESC
                        """,
                        (lp_org_id,),
                    )
                    watchlist = cur.fetchall()

                    # Pipeline stats
                    cur.execute(
                        """
                        SELECT lp_interest, COUNT(*) as count
                        FROM fund_lp_status
                        WHERE lp_org_id = %s AND lp_interest IS NOT NULL
                        GROUP BY lp_interest
                        """,
                        (lp_org_id,),
                    )
                    for row in cur.fetchall():
                        if row["lp_interest"] in pipeline_stats:
                            pipeline_stats[row["lp_interest"]] = row["count"]
        finally:
            conn.close()

    return templates.TemplateResponse(
        request,
        "pages/lp-dashboard.html",
        {
            "title": "LP Dashboard - LPxGP",
            "user": user,
            "matches": matches,
            "watchlist": watchlist,
            "pipeline_stats": pipeline_stats,
        },
    )


@router.get("/lp-watchlist", response_class=HTMLResponse, response_model=None)
async def lp_watchlist_page(request: Request) -> HTMLResponse | RedirectResponse:
    """LP watchlist page for tracking interesting funds."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    watchlist: list[dict[str, Any]] = []

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                # Get LP's organization through employment
                cur.execute(
                    """
                    SELECT o.id as lp_org_id
                    FROM people p
                    JOIN employment e ON e.person_id = p.id AND e.is_current = TRUE
                    JOIN organizations o ON o.id = e.org_id
                    WHERE p.auth_user_id = %s
                    """,
                    (user.get("id"),),
                )
                lp_org = cur.fetchone()

                if lp_org:
                    cur.execute(
                        """
                        SELECT
                            f.id, f.name, f.target_size_mm, f.strategy,
                            f.vintage_year, f.status,
                            gp.name as gp_name, gp.hq_city, gp.hq_country,
                            s.lp_interest, s.notes, s.updated_at
                        FROM fund_lp_status s
                        JOIN funds f ON f.id = s.fund_id
                        JOIN organizations gp ON gp.id = f.org_id
                        WHERE s.lp_org_id = %s
                            AND s.lp_interest IN ('watching', 'interested')
                        ORDER BY s.updated_at DESC
                        """,
                        (lp_org["lp_org_id"],),
                    )
                    watchlist = cur.fetchall()
        finally:
            conn.close()

    return templates.TemplateResponse(
        request,
        "pages/lp-watchlist.html",
        {
            "title": "Watchlist - LPxGP",
            "user": user,
            "watchlist": watchlist,
        },
    )


@router.post("/api/lp/fund/{fund_id}/interest", response_class=HTMLResponse)
async def update_lp_interest(
    request: Request,
    fund_id: str,
    interest: str = Form(...),
    notes: str | None = Form(None),
) -> HTMLResponse:
    """Update LP's interest level in a fund.

    Args:
        request: FastAPI request object.
        fund_id: Fund ID.
        interest: Interest level (watching, interested, reviewing, passed).
        notes: Optional notes.

    Returns:
        HTML response with updated interest badge.
    """
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="<div>Not authenticated</div>", status_code=401)

    if not is_valid_uuid(fund_id):
        return HTMLResponse(
            content='<div class="text-red-500">Invalid fund ID</div>',
            status_code=400,
        )

    valid_interests = ["watching", "interested", "reviewing", "dd_in_progress", "passed"]
    if interest not in valid_interests:
        return HTMLResponse(
            content=f'<div class="text-red-500">Invalid interest: {interest}</div>',
            status_code=400,
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content='<div class="text-yellow-500">Database unavailable</div>',
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            # Get LP's org through employment
            cur.execute(
                """
                SELECT o.id as lp_org_id
                FROM people p
                JOIN employment e ON e.person_id = p.id AND e.is_current = TRUE
                JOIN organizations o ON o.id = e.org_id
                WHERE p.auth_user_id = %s
                """,
                (user.get("id"),),
            )
            lp_org = cur.fetchone()

            if not lp_org:
                return HTMLResponse(
                    content='<div class="text-red-500">LP org not found</div>',
                    status_code=404,
                )

            # Upsert fund_lp_status
            cur.execute(
                """
                INSERT INTO fund_lp_status (fund_id, lp_org_id, lp_interest, notes)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (fund_id, lp_org_id)
                DO UPDATE SET
                    lp_interest = EXCLUDED.lp_interest,
                    notes = COALESCE(EXCLUDED.notes, fund_lp_status.notes),
                    updated_at = NOW()
                RETURNING lp_interest
                """,
                (fund_id, lp_org["lp_org_id"], interest, notes),
            )
            conn.commit()

            # Interest badge styling
            interest_colors = {
                "watching": "bg-gray-100 text-gray-700",
                "interested": "bg-blue-100 text-blue-700",
                "reviewing": "bg-yellow-100 text-yellow-700",
                "dd_in_progress": "bg-orange-100 text-orange-700",
                "passed": "bg-red-100 text-red-700",
            }
            color = interest_colors.get(interest, "bg-gray-100 text-gray-700")
            display = interest.replace("_", " ").title()

            return HTMLResponse(
                content=f"""
                <span class="px-2 py-1 text-xs rounded-full {color}">
                    {display}
                </span>
                """,
            )
    except Exception as e:
        logger.error(f"LP interest update error: {e}")
        return HTMLResponse(
            content=f'<div class="text-red-500">Error: {e}</div>',
            status_code=500,
        )
    finally:
        conn.close()


@router.get("/lp-pipeline", response_class=HTMLResponse, response_model=None)
async def lp_pipeline_page(request: Request) -> HTMLResponse | RedirectResponse:
    """LP pipeline view - kanban-style fund tracking."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Pipeline stages with funds
    pipeline: dict[str, list[dict[str, Any]]] = {
        "watching": [],
        "interested": [],
        "reviewing": [],
        "dd_in_progress": [],
        "passed": [],
    }

    # Use user's org_id directly if available
    lp_org_id = user.get("org_id")

    conn = get_db()
    if conn:
        try:
            # Only query if we have a valid LP org_id
            if lp_org_id and is_valid_uuid(lp_org_id):
                with conn.cursor() as cur:
                    cur.execute(
                        """
                        SELECT
                            f.id, f.name, f.target_size_mm, f.strategy,
                            gp.name as gp_name,
                            s.lp_interest, s.notes, s.updated_at
                        FROM fund_lp_status s
                        JOIN funds f ON f.id = s.fund_id
                        JOIN organizations gp ON gp.id = f.org_id
                        WHERE s.lp_org_id = %s AND s.lp_interest IS NOT NULL
                        ORDER BY s.updated_at DESC
                        """,
                        (lp_org_id,),
                    )
                    for fund in cur.fetchall():
                        stage = fund.get("lp_interest", "watching")
                        if stage in pipeline:
                            pipeline[stage].append(fund)
        finally:
            conn.close()

    return templates.TemplateResponse(
        request,
        "pages/lp-pipeline.html",
        {
            "title": "Pipeline - LPxGP",
            "user": user,
            "pipeline": pipeline,
        },
    )


@router.patch("/api/v1/lp-pipeline/{fund_id}", response_class=JSONResponse)
async def api_update_lp_pipeline_stage(
    request: Request,
    fund_id: str,
    body: LPPipelineStageUpdateRequest,
) -> JSONResponse:
    """Update LP pipeline stage for a fund (LP interest level).

    REST API endpoint for updating LP's interest stage in a fund.

    Args:
        request: FastAPI request object.
        fund_id: Fund ID.
        body: Request body with stage and optional notes.

    Returns:
        JSON response with updated status.
    """
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"},
        )

    if not is_valid_uuid(fund_id):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid fund_id format"},
        )

    if body.stage not in VALID_LP_PIPELINE_STAGES:
        return JSONResponse(
            status_code=400,
            content={
                "error": f"Invalid stage: {body.stage}",
                "valid_stages": VALID_LP_PIPELINE_STAGES,
            },
        )

    conn = get_db()
    if not conn:
        return JSONResponse(
            status_code=503,
            content={"error": "Database unavailable"},
        )

    try:
        with conn.cursor() as cur:
            # Get LP's organization through employment
            cur.execute(
                """
                SELECT o.id as lp_org_id
                FROM people p
                JOIN employment e ON e.person_id = p.id AND e.is_current = TRUE
                JOIN organizations o ON o.id = e.org_id
                WHERE p.auth_user_id = %s
                """,
                (user.get("id"),),
            )
            lp_org = cur.fetchone()

            if not lp_org:
                return JSONResponse(
                    status_code=404,
                    content={"error": "LP organization not found"},
                )

            lp_org_id = lp_org["lp_org_id"]

            # Upsert fund_lp_status with LP interest
            cur.execute(
                """
                INSERT INTO fund_lp_status (fund_id, lp_org_id, lp_interest, notes)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (fund_id, lp_org_id)
                DO UPDATE SET
                    lp_interest = EXCLUDED.lp_interest,
                    notes = COALESCE(EXCLUDED.notes, fund_lp_status.notes),
                    updated_at = NOW()
                RETURNING id, lp_interest, notes, updated_at
                """,
                (fund_id, lp_org_id, body.stage, body.notes),
            )
            result = cur.fetchone()
            conn.commit()

            if not result:
                return JSONResponse(
                    status_code=500,
                    content={"error": "Failed to update pipeline stage"},
                )

            return JSONResponse(
                content={
                    "success": True,
                    "stage": result["lp_interest"],
                    "notes": result["notes"],
                    "updated_at": str(result["updated_at"]) if result["updated_at"] else None,
                }
            )

    except Exception:
        conn.rollback()
        return JSONResponse(
            status_code=500,
            content={"error": "Failed to update pipeline stage"},
        )
    finally:
        conn.close()


# =============================================================================
# LP Mandate
# =============================================================================

# Options for mandate form
STRATEGY_OPTIONS = [
    ("buyout", "Buyout"),
    ("growth", "Growth Equity"),
    ("venture", "Venture Capital"),
    ("credit", "Private Credit"),
    ("real_estate", "Real Estate"),
    ("infrastructure", "Infrastructure"),
    ("secondaries", "Secondaries"),
    ("fund_of_funds", "Fund of Funds"),
]

GEOGRAPHY_OPTIONS = [
    ("north_america", "North America"),
    ("europe", "Europe"),
    ("asia_pacific", "Asia Pacific"),
    ("latin_america", "Latin America"),
    ("middle_east", "Middle East & Africa"),
    ("global", "Global"),
]

SECTOR_OPTIONS = [
    ("technology", "Technology"),
    ("healthcare", "Healthcare"),
    ("financial_services", "Financial Services"),
    ("consumer", "Consumer"),
    ("industrials", "Industrials"),
    ("energy", "Energy"),
    ("real_estate", "Real Estate"),
    ("generalist", "Generalist"),
]


@router.get("/lp-mandate", response_class=HTMLResponse, response_model=None)
async def lp_mandate_page(request: Request) -> HTMLResponse | RedirectResponse:
    """LP mandate profile editor page.

    Allows LPs to configure their investment preferences for matching.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Default empty mandate
    mandate: dict[str, Any] = {
        "strategies": [],
        "geographies": [],
        "sectors": [],
        "check_size_min_mm": None,
        "check_size_max_mm": None,
    }

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                # Get LP's organization
                cur.execute(
                    """
                    SELECT o.id as lp_org_id
                    FROM people p
                    JOIN employment e ON e.person_id = p.id AND e.is_current = TRUE
                    JOIN organizations o ON o.id = e.org_id
                    WHERE p.auth_user_id = %s AND o.is_lp = TRUE
                    """,
                    (user.get("id"),),
                )
                lp_org = cur.fetchone()

                if lp_org:
                    # Get current mandate from lp_profiles
                    cur.execute(
                        """
                        SELECT
                            strategies, geographic_preferences,
                            sector_preferences, check_size_min_mm, check_size_max_mm
                        FROM lp_profiles
                        WHERE org_id = %s
                        """,
                        (lp_org["lp_org_id"],),
                    )
                    profile = cur.fetchone()
                    if profile:
                        mandate = {
                            "strategies": profile.get("strategies") or [],
                            "geographies": profile.get("geographic_preferences") or [],
                            "sectors": profile.get("sector_preferences") or [],
                            "check_size_min_mm": profile.get("check_size_min_mm"),
                            "check_size_max_mm": profile.get("check_size_max_mm"),
                        }
        finally:
            conn.close()

    return templates.TemplateResponse(
        request,
        "pages/lp-mandate.html",
        {
            "title": "Investment Mandate - LPxGP",
            "user": user,
            "mandate": mandate,
            "strategy_options": STRATEGY_OPTIONS,
            "geography_options": GEOGRAPHY_OPTIONS,
            "sector_options": SECTOR_OPTIONS,
        },
    )


@router.post("/api/lp-mandate", response_class=HTMLResponse)
async def save_lp_mandate(
    request: Request,
    strategies: list[str] = Form(default=[]),
    geographies: list[str] = Form(default=[]),
    sectors: list[str] = Form(default=[]),
    check_size_min_mm: float | None = Form(default=None),
    check_size_max_mm: float | None = Form(default=None),
) -> HTMLResponse:
    """Save LP mandate preferences.

    Updates the LP's investment preferences in lp_profiles.
    """
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(
            content='<div class="text-red-500">Not authenticated</div>',
            status_code=401,
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content='<div class="text-yellow-500">Database unavailable</div>',
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            # Get LP's organization
            cur.execute(
                """
                SELECT o.id as lp_org_id
                FROM people p
                JOIN employment e ON e.person_id = p.id AND e.is_current = TRUE
                JOIN organizations o ON o.id = e.org_id
                WHERE p.auth_user_id = %s AND o.is_lp = TRUE
                """,
                (user.get("id"),),
            )
            lp_org = cur.fetchone()

            if not lp_org:
                return HTMLResponse(
                    content='<div class="text-red-500">LP organization not found</div>',
                    status_code=404,
                )

            # Update lp_profiles
            cur.execute(
                """
                UPDATE lp_profiles
                SET
                    strategies = %s,
                    geographic_preferences = %s,
                    sector_preferences = %s,
                    check_size_min_mm = %s,
                    check_size_max_mm = %s,
                    updated_at = NOW()
                WHERE org_id = %s
                """,
                (
                    strategies if strategies else None,
                    geographies if geographies else None,
                    sectors if sectors else None,
                    check_size_min_mm,
                    check_size_max_mm,
                    lp_org["lp_org_id"],
                ),
            )
            conn.commit()

            return HTMLResponse(
                content="""
                <div class="flex items-center text-green-600">
                    <svg class="w-5 h-5 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                    </svg>
                    Mandate saved successfully
                </div>
                """,
            )
    except Exception as e:
        logger.error(f"LP mandate save error: {e}")
        return HTMLResponse(
            content=f'<div class="text-red-500">Error: {e}</div>',
            status_code=500,
        )
    finally:
        conn.close()


# =============================================================================
# LP Meeting Request
# =============================================================================


@router.get("/lp-meeting-request", response_class=HTMLResponse, response_model=None)
async def lp_meeting_request_page(
    request: Request,
    fund_id: str = Query(...),
) -> HTMLResponse | RedirectResponse:
    """Meeting request form for LP to request a meeting with a GP.

    Args:
        request: FastAPI request object.
        fund_id: The fund to request a meeting about.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not is_valid_uuid(fund_id):
        return RedirectResponse(url="/lp-dashboard", status_code=303)

    fund: dict[str, Any] = {}

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT
                        f.id, f.name, f.target_size_mm, f.strategy,
                        f.vintage_year, f.geographic_focus as geo_focus,
                        gp.name as gp_name
                    FROM funds f
                    JOIN organizations gp ON gp.id = f.org_id
                    WHERE f.id = %s
                    """,
                    (fund_id,),
                )
                fund = cur.fetchone() or {}
        finally:
            conn.close()

    if not fund:
        return RedirectResponse(url="/lp-dashboard", status_code=303)

    return templates.TemplateResponse(
        request,
        "pages/lp-meeting-request.html",
        {
            "title": f"Request Meeting - {fund.get('name', 'Fund')} - LPxGP",
            "user": user,
            "fund": fund,
        },
    )


# =============================================================================
# LP Portal Routes (new paths for enhanced LP experience)
# =============================================================================


@router.get("/lp-portal", response_class=HTMLResponse, response_model=None)
async def lp_portal_home(request: Request) -> HTMLResponse | RedirectResponse:
    """LP Portal home - redirects to dashboard."""
    return RedirectResponse(url="/lp-dashboard", status_code=303)


@router.get("/lp-portal/funds", response_class=HTMLResponse, response_model=None)
async def lp_portal_funds(request: Request) -> HTMLResponse | RedirectResponse:
    """LP Portal funds list - redirects to watchlist."""
    return RedirectResponse(url="/lp-watchlist", status_code=303)


@router.get("/lp-portal/mandate", response_class=HTMLResponse, response_model=None)
async def lp_portal_mandate(request: Request) -> HTMLResponse | RedirectResponse:
    """LP Portal mandate editor."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Mock mandate data for the new UI
    mandate: dict[str, Any] = {
        "strategies": ["growth", "buyout"],
        "regions": ["north_america", "europe"],
        "min_irr": 15,
        "target_moic": 2.0,
        "min_commitment_mm": 10,
        "max_commitment_mm": 100,
        "min_fund_size_mm": 100,
        "max_fund_size_mm": 2000,
        "min_track_record_years": 5,
        "min_prior_funds": 1,
        "first_time_managers": False,
        "emerging_managers": True,
        "co_investment": True,
        "esg_policy": "consider",
        "exclusions": ["tobacco", "weapons"],
        "status": "Active",
    }

    return templates.TemplateResponse(
        request,
        "pages/lp-portal/mandate.html",
        {"title": "Investment Mandate - LPxGP", "user": user, "mandate": mandate},
    )


@router.get("/lp-portal/meetings", response_class=HTMLResponse, response_model=None)
async def lp_portal_meetings(request: Request) -> HTMLResponse | RedirectResponse:
    """LP Portal meeting scheduler."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    meetings: list[dict[str, Any]] = []
    funds: list[dict[str, Any]] = []

    return templates.TemplateResponse(
        request,
        "pages/lp-portal/meetings.html",
        {"title": "Meetings - LPxGP", "user": user, "meetings": meetings, "funds": funds},
    )


@router.get("/lp-portal/compare", response_class=HTMLResponse, response_model=None)
async def lp_portal_compare_funds(
    request: Request,
    fund_ids: str | None = Query(None),
) -> HTMLResponse | RedirectResponse:
    """LP Portal - compare multiple funds side-by-side."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    funds: list[dict[str, Any]] = []

    if fund_ids:
        ids = [fid.strip() for fid in fund_ids.split(",") if is_valid_uuid(fid.strip())]

        conn = get_db()
        if conn and ids:
            try:
                with conn.cursor() as cur:
                    placeholders = ",".join(["%s"] * len(ids))
                    cur.execute(f"""
                        SELECT f.*, o.name as gp_name
                        FROM funds f
                        JOIN organizations o ON o.id = f.org_id
                        WHERE f.id IN ({placeholders})
                    """, ids)
                    funds = [dict(row) for row in cur.fetchall()]
            finally:
                conn.close()

    # Demo data if no funds
    if not funds:
        funds = [
            {
                "id": "demo-1",
                "name": "Growth Fund IV",
                "gp_name": "Apex Capital",
                "strategy": "growth",
                "target_size_mm": 500,
                "vintage_year": 2024,
                "management_fee_pct": 2.0,
                "carried_interest_pct": 20,
                "gp_commitment_pct": 2,
                "prior_irr": 28,
                "prior_moic": 2.5,
                "mandate_fit": 92,
            },
            {
                "id": "demo-2",
                "name": "Tech Fund II",
                "gp_name": "Venture Plus",
                "strategy": "venture",
                "target_size_mm": 250,
                "vintage_year": 2024,
                "management_fee_pct": 2.5,
                "carried_interest_pct": 20,
                "gp_commitment_pct": 3,
                "prior_irr": 35,
                "prior_moic": 3.2,
                "mandate_fit": 85,
            },
        ]

    return templates.TemplateResponse(
        request,
        "pages/lp-portal/compare-funds.html",
        {"title": "Compare Funds - LPxGP", "user": user, "funds": funds},
    )


@router.post("/api/lp-meeting-request", response_class=HTMLResponse)
async def submit_meeting_request(
    request: Request,
    fund_id: str = Form(...),
    preferred_date_1: str = Form(...),
    preferred_date_2: str | None = Form(default=None),
    preferred_date_3: str | None = Form(default=None),
    meeting_format: str = Form(default="video_call"),
    topics: str = Form(...),
    contact_name: str = Form(...),
    contact_title: str | None = Form(default=None),
    contact_email: str = Form(...),
    contact_phone: str | None = Form(default=None),
    additional_notes: str | None = Form(default=None),
) -> HTMLResponse:
    """Submit a meeting request from LP to GP.

    Creates a meeting request record and updates the pipeline status.
    """
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(
            content='<div class="text-red-500">Not authenticated</div>',
            status_code=401,
        )

    if not is_valid_uuid(fund_id):
        return HTMLResponse(
            content='<div class="text-red-500">Invalid fund ID</div>',
            status_code=400,
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content='<div class="text-yellow-500">Database unavailable</div>',
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            # Get LP's organization
            cur.execute(
                """
                SELECT o.id as lp_org_id, o.name as lp_name
                FROM people p
                JOIN employment e ON e.person_id = p.id AND e.is_current = TRUE
                JOIN organizations o ON o.id = e.org_id
                WHERE p.auth_user_id = %s AND o.is_lp = TRUE
                """,
                (user.get("id"),),
            )
            lp_org = cur.fetchone()

            if not lp_org:
                return HTMLResponse(
                    content='<div class="text-red-500">LP organization not found</div>',
                    status_code=404,
                )

            # Get fund info for the notification
            cur.execute(
                "SELECT name FROM funds WHERE id = %s",
                (fund_id,),
            )
            fund = cur.fetchone()
            fund_name = fund["name"] if fund else "Unknown Fund"

            # Update pipeline status to indicate meeting requested
            cur.execute(
                """
                INSERT INTO fund_lp_status (fund_id, lp_org_id, lp_interest, notes)
                VALUES (%s, %s, 'reviewing', %s)
                ON CONFLICT (fund_id, lp_org_id)
                DO UPDATE SET
                    lp_interest = 'reviewing',
                    notes = EXCLUDED.notes,
                    updated_at = NOW()
                """,
                (
                    fund_id,
                    lp_org["lp_org_id"],
                    f"Meeting requested: {topics[:200]}",
                ),
            )

            # Check if there's a match record to log the meeting request
            cur.execute(
                """
                SELECT id FROM fund_lp_matches
                WHERE fund_id = %s AND lp_org_id = %s
                """,
                (fund_id, lp_org["lp_org_id"]),
            )
            match_row = cur.fetchone()

            if match_row:
                # Log meeting request in outreach_events
                cur.execute(
                    """
                    INSERT INTO outreach_events
                    (match_id, event_type, event_date, notes)
                    VALUES (%s, 'meeting_requested', NOW(), %s)
                    """,
                    (
                        match_row["id"],
                        f"LP requested meeting. Format: {meeting_format}. Dates: {preferred_date_1}",
                    ),
                )

            conn.commit()

            return HTMLResponse(
                content=f"""
                <div class="bg-green-50 border border-green-200 rounded-lg p-6 text-center">
                    <svg class="w-12 h-12 text-green-500 mx-auto mb-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M5 13l4 4L19 7"/>
                    </svg>
                    <h3 class="text-lg font-semibold text-green-800 mb-2">Meeting Request Sent!</h3>
                    <p class="text-green-600 mb-4">
                        Your meeting request for <strong>{fund_name}</strong> has been submitted.
                        The GP will be notified and will respond to your request.
                    </p>
                    <a href="/lp-pipeline" class="inline-block px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700">
                        View Pipeline
                    </a>
                </div>
                """,
            )
    except Exception as e:
        logger.error(f"Meeting request error: {e}")
        return HTMLResponse(
            content=f'<div class="text-red-500">Error submitting request: {e}</div>',
            status_code=500,
        )
    finally:
        conn.close()
