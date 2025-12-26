"""LP Portal routes for LP-specific views and actions.

This router provides:
- /lp-dashboard: LP dashboard showing fund matches and pipeline
- /lp-watchlist: LP watchlist page for tracking interesting funds
- /lp-pipeline: LP pipeline view (kanban-style fund tracking)
- /api/lp/fund/{fund_id}/interest: Update LP interest in a fund
- /api/v1/lp-pipeline/{fund_id}: Update LP pipeline stage
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Form, Request
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
                        JOIN organizations gp ON gp.id = f.gp_org_id
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
                        JOIN organizations gp ON gp.id = f.gp_org_id
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
                        JOIN organizations gp ON gp.id = f.gp_org_id
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
                            gp.name as gp_name,
                            s.lp_interest, s.notes, s.updated_at
                        FROM fund_lp_status s
                        JOIN funds f ON f.id = s.fund_id
                        JOIN organizations gp ON gp.id = f.gp_org_id
                        WHERE s.lp_org_id = %s AND s.lp_interest IS NOT NULL
                        ORDER BY s.updated_at DESC
                        """,
                        (lp_org["lp_org_id"],),
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
