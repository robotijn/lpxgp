"""Pipeline and outreach routes for managing LP relationships.

This router provides:
- /outreach: Outreach hub page (HTML)
- /pipeline: Kanban-style pipeline board (HTML)
- /pipeline/{fund_id}/{lp_id}: Pipeline detail page (HTML)
- /api/v1/pipeline/{fund_id}/{lp_id}: Update pipeline stage (JSON)
- /api/v1/pipeline/{fund_id}: Get pipeline status for a fund (JSON)
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from pydantic import BaseModel, Field

from src import auth
from src.database import get_db
from src.logging_config import get_logger
from src.shortlists import get_user_shortlist
from src.utils import is_valid_uuid

logger = get_logger(__name__)

router = APIRouter(tags=["pipeline"])

# Templates setup
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=templates_path)


# =============================================================================
# Pydantic Models
# =============================================================================


class PipelineStageUpdateRequest(BaseModel):
    """Request body for updating pipeline stage."""

    stage: str = Field(
        ...,
        description="Pipeline stage",
        pattern="^(recommended|gp_interested|gp_pursuing|lp_reviewing|mutual_interest|in_diligence|gp_passed|lp_passed|invested)$",
    )
    notes: str | None = None


# Valid pipeline stages for validation (GP perspective)
VALID_PIPELINE_STAGES = [
    "recommended",
    "gp_interested",
    "gp_pursuing",
    "lp_reviewing",
    "mutual_interest",
    "in_diligence",
    "gp_passed",
    "lp_passed",
    "invested",
]


# =============================================================================
# HTML Page Routes
# =============================================================================


@router.get("/outreach", response_class=HTMLResponse, response_model=None)
async def outreach_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Outreach Hub for managing LP communications.

    Requires authentication.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Mock stats for offline mode
    stats = {
        "shortlisted": len(get_user_shortlist(user["id"])),
        "funds_count": 3,
        "contacted": 18,
        "contacted_week": 5,
        "meetings": 8,
        "meetings_scheduled": 3,
        "response_rate": 44,
        "responses": 8,
    }

    # Mock activities
    activities = [
        {
            "type": "meeting",
            "description": "Meeting scheduled with",
            "lp_name": "Yale Endowment",
            "lp_id": "lp-yale",
            "details": "January 15, 2025 at 2:00 PM EST",
            "fund_name": "Growth Fund III",
            "time_ago": "2 hours ago",
        },
        {
            "type": "email",
            "description": "Email sent to",
            "lp_name": "CalPERS",
            "lp_id": "lp-calpers",
            "details": "Michael Smith",
            "fund_name": "Growth Fund III",
            "time_ago": "Yesterday",
        },
        {
            "type": "pitch",
            "description": "Pitch generated for",
            "lp_name": "Ontario Teachers",
            "lp_id": "lp-ontario",
            "fund_name": "Growth Fund III",
            "time_ago": "2 days ago",
        },
    ]

    upcoming_meetings = [
        {"lp_name": "Yale Endowment", "lp_id": "lp-yale", "date": "Jan 15, 2:00 PM"},
        {"lp_name": "Stanford Endowment", "lp_id": "lp-stanford", "date": "Jan 18, 10:00 AM"},
    ]

    followups = [
        {"lp_name": "Ontario Teachers", "lp_id": "lp-ontario", "days_ago": 5},
        {"lp_name": "CalPERS", "lp_id": "lp-calpers", "days_ago": 3},
        {"lp_name": "CPPIB", "lp_id": "lp-cppib", "days_ago": 7},
    ]

    mock_funds = [
        {"id": "fund-1", "name": "Growth Fund III"},
        {"id": "fund-2", "name": "Growth Fund II"},
    ]

    return templates.TemplateResponse(
        request,
        "pages/outreach.html",
        {
            "title": "Outreach Hub - LPxGP",
            "user": user,
            "stats": stats,
            "activities": activities,
            "upcoming_meetings": upcoming_meetings,
            "followups": followups,
            "funds": mock_funds,
        },
    )


@router.get("/pipeline", response_class=HTMLResponse, response_model=None)
async def pipeline_page(
    request: Request,
    fund_id: str | None = None,
) -> HTMLResponse | RedirectResponse:
    """Kanban-style pipeline board for tracking LP relationships.

    Displays all LPs in the pipeline with their current stage.
    Cards can be dragged between columns to update status.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Define pipeline stages with colors
    stages: list[dict[str, Any]] = [
        {"id": "recommended", "name": "Recommended", "color": "bg-gray-400", "cards": []},
        {"id": "gp_interested", "name": "Interested", "color": "bg-blue-400", "cards": []},
        {"id": "gp_pursuing", "name": "Pursuing", "color": "bg-indigo-400", "cards": []},
        {"id": "lp_reviewing", "name": "LP Reviewing", "color": "bg-yellow-400", "cards": []},
        {"id": "mutual_interest", "name": "Mutual Interest", "color": "bg-green-400", "cards": []},
        {"id": "in_diligence", "name": "In DD", "color": "bg-purple-400", "cards": []},
        {"id": "invested", "name": "Invested", "color": "bg-emerald-500", "cards": []},
        {"id": "gp_passed", "name": "GP Passed", "color": "bg-red-300", "cards": []},
        {"id": "lp_passed", "name": "LP Passed", "color": "bg-red-400", "cards": []},
    ]

    funds: list[dict[str, Any]] = []

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                # Get user's funds
                cur.execute(
                    """
                    SELECT f.id, f.name
                    FROM funds f
                    JOIN organizations o ON o.id = f.gp_org_id
                    WHERE o.id IN (
                        SELECT org_id FROM users WHERE id = %s
                    )
                    ORDER BY f.name
                    """,
                    (user["id"],),
                )
                funds = cur.fetchall()

                # Build filter
                fund_filter = ""
                params: list[Any] = []
                if fund_id:
                    fund_filter = "AND s.fund_id = %s"
                    params.append(fund_id)

                # Get pipeline items
                cur.execute(
                    f"""
                    SELECT
                        s.fund_id,
                        s.lp_org_id as lp_id,
                        s.pipeline_stage,
                        s.gp_interest,
                        s.lp_interest,
                        s.notes,
                        s.updated_at,
                        o.name as lp_name,
                        f.name as fund_name
                    FROM fund_lp_status s
                    JOIN organizations o ON o.id = s.lp_org_id
                    JOIN funds f ON f.id = s.fund_id
                    WHERE s.pipeline_stage IS NOT NULL
                    {fund_filter}
                    ORDER BY s.updated_at DESC
                    """,
                    params,
                )
                items = cur.fetchall()

                # Group by stage
                for item in items:
                    stage_id = item["pipeline_stage"]
                    for stage in stages:
                        if stage["id"] == stage_id:
                            stage["cards"].append({
                                "fund_id": str(item["fund_id"]),
                                "lp_id": str(item["lp_id"]),
                                "lp_name": item["lp_name"],
                                "fund_name": item["fund_name"],
                                "gp_interest": item["gp_interest"],
                                "lp_interest": item["lp_interest"],
                                "notes": item["notes"],
                                "updated_at": str(item["updated_at"]) if item["updated_at"] else None,
                            })
                            break
        except Exception as e:
            logger.error(f"Pipeline page error: {e}")
        finally:
            conn.close()

    return templates.TemplateResponse(
        request,
        "pages/pipeline.html",
        {
            "user": user,
            "stages": stages,
            "funds": funds,
            "selected_fund_id": fund_id,
        },
    )


@router.get("/pipeline/{fund_id}/{lp_id}", response_class=HTMLResponse, response_model=None)
async def pipeline_detail_page(
    request: Request,
    fund_id: str,
    lp_id: str,
) -> HTMLResponse | RedirectResponse:
    """Detail page for a pipeline item with notes, contacts, and activity.

    Shows full LP info, allows editing notes, and displays activity history.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not is_valid_uuid(fund_id) or not is_valid_uuid(lp_id):
        return RedirectResponse(url="/pipeline", status_code=303)

    # Define stages for dropdown
    stages = [
        {"id": "recommended", "name": "Recommended"},
        {"id": "gp_interested", "name": "Interested"},
        {"id": "gp_pursuing", "name": "Pursuing"},
        {"id": "lp_reviewing", "name": "LP Reviewing"},
        {"id": "mutual_interest", "name": "Mutual Interest"},
        {"id": "in_diligence", "name": "In Diligence"},
        {"id": "invested", "name": "Invested"},
        {"id": "gp_passed", "name": "GP Passed"},
        {"id": "lp_passed", "name": "LP Passed"},
    ]

    lp: dict[str, Any] = {}
    fund: dict[str, Any] = {}
    status: dict[str, Any] = {}
    activities: list[dict[str, Any]] = []
    contacts: list[dict[str, Any]] = []

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                # Get LP info
                cur.execute(
                    """
                    SELECT id, name, lp_type, hq_city, hq_country,
                           total_aum_bn, pe_allocation_pct,
                           check_size_min_mm, check_size_max_mm
                    FROM organizations
                    WHERE id = %s
                    """,
                    (lp_id,),
                )
                lp = cur.fetchone() or {}

                # Get fund info
                cur.execute(
                    "SELECT id, name FROM funds WHERE id = %s",
                    (fund_id,),
                )
                fund = cur.fetchone() or {}

                # Get status
                cur.execute(
                    """
                    SELECT pipeline_stage, gp_interest, lp_interest, notes, updated_at
                    FROM fund_lp_status
                    WHERE fund_id = %s AND lp_org_id = %s
                    """,
                    (fund_id, lp_id),
                )
                status = cur.fetchone() or {"pipeline_stage": "recommended"}

                # Get activities from outreach_events
                cur.execute(
                    """
                    SELECT e.event_type, e.event_date, e.notes
                    FROM outreach_events e
                    JOIN fund_lp_matches m ON m.id = e.match_id
                    WHERE m.fund_id = %s AND m.lp_org_id = %s
                    ORDER BY e.event_date DESC
                    LIMIT 20
                    """,
                    (fund_id, lp_id),
                )
                activities = cur.fetchall()

                # Get contacts
                cur.execute(
                    """
                    SELECT p.id, p.full_name, p.email, p.linkedin_url, cp.title
                    FROM people p
                    JOIN company_people cp ON cp.person_id = p.id
                    WHERE cp.org_id = %s
                    ORDER BY cp.is_decision_maker DESC, p.full_name
                    LIMIT 5
                    """,
                    (lp_id,),
                )
                contacts = cur.fetchall()
        except Exception as e:
            logger.error(f"Pipeline detail error: {e}")
        finally:
            conn.close()

    if not lp:
        return RedirectResponse(url="/pipeline", status_code=303)

    return templates.TemplateResponse(
        request,
        "pages/pipeline-detail.html",
        {
            "user": user,
            "lp": lp,
            "fund": fund,
            "status": status,
            "stages": stages,
            "activities": activities,
            "contacts": contacts,
        },
    )


# =============================================================================
# API Routes
# =============================================================================


@router.patch("/api/v1/pipeline/{fund_id}/{lp_id}", response_class=JSONResponse)
async def api_update_pipeline_stage(
    request: Request,
    fund_id: str,
    lp_id: str,
    body: PipelineStageUpdateRequest,
) -> JSONResponse:
    """Update pipeline stage for a fund-LP relationship.

    REST API endpoint for updating pipeline stage and logging activity.

    Args:
        request: FastAPI request object.
        fund_id: Fund ID.
        lp_id: LP organization ID.
        body: PipelineStageUpdateRequest with stage and optional notes.

    Returns:
        JSON response with updated status.
    """
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"},
        )

    if not is_valid_uuid(fund_id) or not is_valid_uuid(lp_id):
        return JSONResponse(
            status_code=400,
            content={"error": "Invalid fund ID or LP ID"},
        )

    if body.stage not in VALID_PIPELINE_STAGES:
        return JSONResponse(
            status_code=400,
            content={
                "error": f"Invalid stage: {body.stage}",
                "valid_stages": VALID_PIPELINE_STAGES,
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
            # Upsert fund_lp_status
            cur.execute(
                """
                INSERT INTO fund_lp_status (fund_id, lp_org_id, pipeline_stage, notes)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (fund_id, lp_org_id)
                DO UPDATE SET
                    pipeline_stage = EXCLUDED.pipeline_stage,
                    notes = COALESCE(EXCLUDED.notes, fund_lp_status.notes),
                    updated_at = NOW()
                RETURNING id, pipeline_stage, notes, updated_at
                """,
                (fund_id, lp_id, body.stage, body.notes),
            )
            result = cur.fetchone()

            # Log the activity in outreach_events if match exists
            cur.execute(
                """
                SELECT id FROM fund_lp_matches
                WHERE fund_id = %s AND lp_org_id = %s
                """,
                (fund_id, lp_id),
            )
            match_row = cur.fetchone()

            if match_row:
                # Map pipeline stage to event type
                event_type_map = {
                    "gp_interested": "pitch_generated",
                    "gp_pursuing": "email_sent",
                    "lp_reviewing": "response_received",
                    "mutual_interest": "meeting_scheduled",
                    "in_diligence": "due_diligence_started",
                    "invested": "commitment_made",
                    "gp_passed": "commitment_declined",
                    "lp_passed": "commitment_declined",
                }
                event_type = event_type_map.get(body.stage)

                if event_type:
                    cur.execute(
                        """
                        INSERT INTO outreach_events
                        (match_id, event_type, event_date, notes)
                        VALUES (%s, %s, NOW(), %s)
                        """,
                        (match_row["id"], event_type, body.notes),
                    )

            conn.commit()

            return JSONResponse(
                content={
                    "success": True,
                    "fund_id": fund_id,
                    "lp_id": lp_id,
                    "stage": body.stage,
                    "notes": body.notes,
                    "updated_at": str(result["updated_at"]) if result else None,
                },
            )
    except Exception as e:
        logger.error(f"Pipeline stage update error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )
    finally:
        conn.close()


@router.get("/api/v1/pipeline/{fund_id}", response_class=JSONResponse)
async def api_get_pipeline_status(
    request: Request,
    fund_id: str,
) -> JSONResponse:
    """Get pipeline status for all LPs for a fund.

    Args:
        request: FastAPI request object.
        fund_id: Fund ID.

    Returns:
        JSON response with pipeline status for all LPs.
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
            content={"error": "Invalid fund ID"},
        )

    conn = get_db()
    if not conn:
        return JSONResponse(
            status_code=503,
            content={"error": "Database unavailable"},
        )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    s.lp_org_id,
                    o.name as lp_name,
                    s.pipeline_stage,
                    s.gp_interest,
                    s.lp_interest,
                    s.notes,
                    s.updated_at
                FROM fund_lp_status s
                JOIN organizations o ON o.id = s.lp_org_id
                WHERE s.fund_id = %s
                ORDER BY s.updated_at DESC
                """,
                (fund_id,),
            )
            rows = cur.fetchall()

            # Group by stage for pipeline view
            pipeline: dict[str, list[dict[str, Any]]] = {
                stage: [] for stage in VALID_PIPELINE_STAGES
            }

            items = []
            for row in rows:
                item = {
                    "lp_id": str(row["lp_org_id"]),
                    "lp_name": row["lp_name"],
                    "stage": row["pipeline_stage"],
                    "gp_interest": row["gp_interest"],
                    "lp_interest": row["lp_interest"],
                    "notes": row["notes"],
                    "updated_at": str(row["updated_at"]) if row["updated_at"] else None,
                }
                items.append(item)
                if row["pipeline_stage"] in pipeline:
                    pipeline[row["pipeline_stage"]].append(item)

            return JSONResponse(
                content={
                    "success": True,
                    "fund_id": fund_id,
                    "total": len(items),
                    "items": items,
                    "by_stage": {k: len(v) for k, v in pipeline.items()},
                },
            )
    except Exception as e:
        logger.error(f"Pipeline status error: {e}")
        return JSONResponse(
            status_code=500,
            content={"error": str(e)},
        )
    finally:
        conn.close()
