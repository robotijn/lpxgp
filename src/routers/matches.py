"""Match-related API endpoints and pages.

This router provides:
- /matches: Matches page (HTML)
- /matches/{lp_id}: Match detail page (HTML)
- /api/match/{match_id}/detail: Match detail HTMX partial
- /api/match/{match_id}/generate-pitch: Generate AI pitch
- /api/match/{match_id}/feedback: Submit match feedback
- /api/match/{match_id}/status: Update match pipeline status
"""

from __future__ import annotations

from pathlib import Path
from typing import Any

import httpx
from fastapi import APIRouter, Form, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates

from src import auth
from src.config import get_settings
from src.database import get_db
from src.logging_config import get_logger
from src.shortlists import is_in_shortlist
from src.utils import is_valid_uuid

logger = get_logger(__name__)

router = APIRouter(tags=["matches"])

# Templates setup
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=templates_path)


@router.get("/matches", response_class=HTMLResponse, response_model=None)
async def matches_page(
    request: Request,
    fund_id: str | None = Query(None),
) -> HTMLResponse | RedirectResponse:
    """Render the matches page showing AI-recommended LP matches.

    Requires authentication.

    Displays scored LP-Fund matches with filtering by fund and
    statistics including high score count, average score, and
    pipeline status.

    Args:
        request: FastAPI request object.
        fund_id: Optional UUID of fund to filter matches by.

    Returns:
        Matches page HTML with match data and statistics.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    # Validate fund_id if provided - ignore invalid UUIDs to prevent crashes
    validated_fund_id: str | None = None
    if fund_id and is_valid_uuid(fund_id):
        validated_fund_id = fund_id

    # Default empty state
    empty_response: dict[str, Any] = {
        "title": "Matches - LPxGP",
        "user": user,
        "matches": [],
        "funds": [],
        "high_score_count": 0,
        "avg_score": 0,
        "in_pipeline": 0,
        "selected_fund": None,
    }

    conn = get_db()
    if not conn:
        return templates.TemplateResponse(request, "pages/matches.html", empty_response)

    try:
        with conn.cursor() as cur:
            # Fetch funds for the selector
            cur.execute("SELECT id, name, status FROM funds ORDER BY name")
            funds = cur.fetchall()

            # Fetch matches with all related data in one efficient query
            # Build query conditionally to avoid psycopg NULL type inference issues
            base_query = """
                SELECT
                    m.id, m.fund_id, m.lp_org_id, m.score,
                    m.score_breakdown, m.explanation, m.talking_points, m.concerns,
                    o.name as lp_name, o.hq_city as lp_city, o.hq_country as lp_country,
                    lp.lp_type, lp.total_aum_bn,
                    f.name as fund_name,
                    s.pipeline_stage
                FROM fund_lp_matches m
                JOIN organizations o ON o.id = m.lp_org_id
                LEFT JOIN lp_profiles lp ON lp.org_id = m.lp_org_id
                JOIN funds f ON f.id = m.fund_id
                LEFT JOIN fund_lp_status s ON s.fund_id = m.fund_id AND s.lp_org_id = m.lp_org_id
            """
            if validated_fund_id:
                cur.execute(
                    base_query + " WHERE m.fund_id = %s ORDER BY m.score DESC",
                    (validated_fund_id,),
                )
            else:
                cur.execute(base_query + " ORDER BY m.score DESC")
            matches = cur.fetchall()

        # Calculate stats
        scores = [m["score"] for m in matches if m["score"] is not None]
        high_score_count = sum(1 for s in scores if s >= 90)
        avg_score = sum(scores) / len(scores) if scores else 0
        in_pipeline = sum(1 for m in matches if m.get("pipeline_stage"))

        return templates.TemplateResponse(
            request,
            "pages/matches.html",
            {
                "title": "Matches - LPxGP",
                "matches": matches,
                "funds": funds,
                "high_score_count": high_score_count,
                "avg_score": avg_score,
                "in_pipeline": in_pipeline,
                "selected_fund": validated_fund_id,
            },
        )
    finally:
        conn.close()


@router.get("/matches/{lp_id}", response_class=HTMLResponse, response_model=None)
async def match_detail_page(
    request: Request,
    lp_id: str,
    fund_id: str | None = Query(None),
) -> HTMLResponse | RedirectResponse:
    """Match detail page showing AI analysis for LP-Fund pairing.

    Requires authentication.
    """
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not is_valid_uuid(lp_id):
        return HTMLResponse(content="Invalid LP ID", status_code=400)

    # Validate fund_id if provided
    if fund_id and not is_valid_uuid(fund_id):
        fund_id = None  # Fall back to default if invalid

    # Mock data for offline mode
    mock_lp = {
        "id": lp_id,
        "name": "CalPERS",
        "in_shortlist": is_in_shortlist(user["id"], lp_id),
    }
    mock_fund = {
        "id": fund_id or "00000000-0000-0000-0000-000000000001",
        "name": "Growth Fund III",
        "target_size_mm": 500,
    }
    mock_match = {
        "score": 92,
        "explanation": "CalPERS presents an excellent fit for Growth Fund III based on several key factors:",
        "score_breakdown": {
            "strategy": 95,
            "size_fit": 90,
            "geography": 92,
            "track_record": 88,
        },
        "talking_points": [
            "Strategy alignment: CalPERS actively invests in growth equity managers",
            "Fund size fit: Your $500M target is within their preferred range",
            "Track record: Your prior fund performance exceeds their hurdle rate",
            "ESG commitment: Both organizations prioritize responsible investing",
        ],
        "concerns": [
            "Competition: CalPERS receives many manager proposals annually",
            "Due diligence timeline: Their process typically takes 9-12 months",
            "Co-investment: They often expect co-investment opportunities",
        ],
    }

    return templates.TemplateResponse(
        request,
        "pages/match-detail.html",
        {
            "title": f"Match Analysis: {mock_lp['name']} - LPxGP",
            "user": user,
            "lp": mock_lp,
            "fund": mock_fund,
            "match": mock_match,
        },
    )


@router.get("/api/match/{match_id}/detail", response_class=HTMLResponse)
async def match_detail(request: Request, match_id: str) -> HTMLResponse:
    """Get match detail for modal display (HTMX partial)."""
    if not is_valid_uuid(match_id):
        return HTMLResponse(
            content="<p class='text-red-500'>Invalid match ID</p>", status_code=400
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content="<p class='text-navy-500'>Database not configured</p>",
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    m.id, m.fund_id, m.lp_org_id, m.score,
                    m.score_breakdown, m.explanation, m.talking_points, m.concerns,
                    o.name as lp_name, o.hq_city as lp_city, o.hq_country as lp_country,
                    o.website as lp_website,
                    lp.lp_type, lp.total_aum_bn, lp.pe_allocation_pct,
                    lp.check_size_min_mm, lp.check_size_max_mm,
                    f.name as fund_name, f.target_size_mm, f.vintage_year,
                    s.pipeline_stage, s.gp_interest, s.lp_interest,
                    s.gp_interest_reason, s.lp_interest_reason
                FROM fund_lp_matches m
                JOIN organizations o ON o.id = m.lp_org_id
                LEFT JOIN lp_profiles lp ON lp.org_id = m.lp_org_id
                JOIN funds f ON f.id = m.fund_id
                LEFT JOIN fund_lp_status s ON s.fund_id = m.fund_id AND s.lp_org_id = m.lp_org_id
                WHERE m.id = %s
            """,
                (match_id,),
            )
            match = cur.fetchone()

        if not match:
            return HTMLResponse(
                content="<p class='text-navy-500'>Match not found</p>", status_code=404
            )

        return templates.TemplateResponse(
            request,
            "partials/match_detail_modal.html",
            {"match": match},
        )
    finally:
        conn.close()


@router.post("/api/match/{match_id}/generate-pitch", response_class=HTMLResponse)
async def generate_pitch(
    request: Request,
    match_id: str,
    pitch_type: str = Form(default="email"),
    tone: str = Form(default="professional"),
) -> HTMLResponse:
    """Generate an AI pitch for a match (HTMX partial)."""
    if not is_valid_uuid(match_id):
        return HTMLResponse(
            content="<p class='text-red-500'>Invalid match ID</p>", status_code=400
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content="<p class='text-navy-500'>Database not configured</p>",
            status_code=503,
        )

    try:
        # Fetch match data for pitch generation
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT
                    m.id, m.score, m.explanation, m.talking_points, m.concerns,
                    o.name as lp_name, o.hq_city as lp_city,
                    lp.lp_type, lp.total_aum_bn,
                    f.name as fund_name, f.target_size_mm,
                    gp.name as gp_name
                FROM fund_lp_matches m
                JOIN organizations o ON o.id = m.lp_org_id
                LEFT JOIN lp_profiles lp ON lp.org_id = m.lp_org_id
                JOIN funds f ON f.id = m.fund_id
                JOIN organizations gp ON gp.id = f.org_id
                WHERE m.id = %s
            """,
                (match_id,),
            )
            match = cur.fetchone()

        if not match:
            return HTMLResponse(
                content="<p class='text-navy-500'>Match not found</p>", status_code=404
            )

        # Build the prompt for pitch generation
        talking_points = match.get("talking_points") or []
        concerns = match.get("concerns") or []

        prompt = f"""Generate a {tone} {pitch_type} pitch for a GP reaching out to an LP.

GP: {match['gp_name']}
Fund: {match['fund_name']} (Target: ${match['target_size_mm']}M)

LP: {match['lp_name']}
Type: {match['lp_type'] or 'Institutional Investor'}
Location: {match['lp_city']}
AUM: ${match['total_aum_bn']}B

Match Score: {match['score']}%
Why they match: {match['explanation']}

Key talking points:
{chr(10).join(f'- {p}' for p in talking_points[:3])}

Potential concerns to address:
{chr(10).join(f'- {c}' for c in concerns[:2])}

Generate a compelling {pitch_type} that:
1. Opens with a personalized hook relevant to the LP
2. Briefly introduces the fund and its differentiation
3. References why this LP is a good fit
4. Includes a clear call to action
5. Keeps it concise (under 200 words for email, under 100 for summary)

Output only the {pitch_type} content, no preamble."""

        # Try to generate with Ollama (local dev) or return mock
        settings = get_settings()
        pitch_content = None

        try:
            async with httpx.AsyncClient(timeout=180.0) as client:
                response = await client.post(
                    f"{settings.ollama_base_url}/api/generate",
                    json={
                        "model": settings.ollama_model,
                        "prompt": prompt,
                        "stream": False,
                    },
                )
                if response.status_code == 200:
                    result = response.json()
                    pitch_content = result.get("response", "").strip()
        except Exception as e:
            logger.warning(f"Ollama not available: {e}")

        # Fallback to mock pitch if Ollama unavailable
        if not pitch_content:
            if pitch_type == "email":
                pitch_content = f"""Subject: {match['fund_name']} - Investment Opportunity Aligned with {match['lp_name']}'s Strategy

Dear {match['lp_name']} Investment Team,

I hope this message finds you well. I'm reaching out from {match['gp_name']} regarding our {match['fund_name']}, which I believe aligns exceptionally well with your investment mandate.

{match['explanation']}

Our fund targets ${match['target_size_mm']}M and focuses on opportunities that match your portfolio strategy. {talking_points[0] if talking_points else ''}

I would welcome the opportunity to schedule a brief call to discuss how {match['fund_name']} might complement your portfolio.

Best regards,
{match['gp_name']} Team"""
            else:
                pitch_content = f"""{match['fund_name']} presents a compelling opportunity for {match['lp_name']}.

{match['explanation']}

Key highlights:
* Target fund size: ${match['target_size_mm']}M
* {talking_points[0] if talking_points else 'Strong alignment with LP mandate'}
* {talking_points[1] if len(talking_points) > 1 else 'Experienced management team'}

Match score: {match['score']}%"""

        return templates.TemplateResponse(
            request,
            "partials/pitch_result.html",
            {
                "match": match,
                "pitch_type": pitch_type,
                "tone": tone,
                "pitch_content": pitch_content,
            },
        )
    finally:
        conn.close()


@router.post("/api/match/{match_id}/feedback", response_class=HTMLResponse)
async def match_feedback(
    request: Request,
    match_id: str,
    feedback: str = Form(...),
    reason: str | None = Form(None),
) -> HTMLResponse:
    """Record feedback on a match (thumbs up/down/dismiss).

    Args:
        request: FastAPI request object.
        match_id: Match ID (fund_lp_match id).
        feedback: Feedback type (positive, negative, dismissed).
        reason: Optional reason for dismissal.

    Returns:
        HTML response with updated match card or success message.
    """
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="<div>Not authenticated</div>", status_code=401)

    if not is_valid_uuid(match_id):
        return HTMLResponse(
            content='<div class="text-red-500">Invalid match ID</div>',
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
            # Update match with feedback
            cur.execute(
                """
                UPDATE fund_lp_matches
                SET
                    gp_feedback = %s,
                    gp_feedback_reason = %s,
                    gp_feedback_at = NOW()
                WHERE id = %s
                RETURNING id, score, gp_feedback
                """,
                (feedback, reason, match_id),
            )
            result = cur.fetchone()

            if not result:
                return HTMLResponse(
                    content='<div class="text-red-500">Match not found</div>',
                    status_code=404,
                )

            conn.commit()

            # Return updated feedback UI
            feedback_icons = {
                "positive": "👍",
                "negative": "👎",
                "dismissed": "❌",
            }
            icon = feedback_icons.get(feedback, "")

            return HTMLResponse(
                content=f"""
                <div class="flex items-center gap-2 text-sm text-navy-600">
                    <span>{icon}</span>
                    <span>Feedback recorded</span>
                </div>
                """,
            )
    except Exception as e:
        logger.error(f"Match feedback error: {e}")
        return HTMLResponse(
            content=f'<div class="text-red-500">Error: {e}</div>',
            status_code=500,
        )
    finally:
        conn.close()


@router.post("/api/match/{match_id}/status", response_class=HTMLResponse)
async def update_match_status(
    request: Request,
    match_id: str,
    stage: str = Form(...),
    notes: str | None = Form(None),
) -> HTMLResponse:
    """Update pipeline stage for a match.

    Args:
        request: FastAPI request object.
        match_id: Match ID.
        stage: Pipeline stage (new, contacted, meeting_scheduled, etc.).
        notes: Optional notes.

    Returns:
        HTML response with updated status badge.
    """
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="<div>Not authenticated</div>", status_code=401)

    if not is_valid_uuid(match_id):
        return HTMLResponse(
            content='<div class="text-red-500">Invalid match ID</div>',
            status_code=400,
        )

    valid_stages = [
        "new",
        "contacted",
        "meeting_scheduled",
        "meeting_held",
        "dd_in_progress",
        "committed",
        "passed",
    ]
    if stage not in valid_stages:
        return HTMLResponse(
            content=f'<div class="text-red-500">Invalid stage: {stage}</div>',
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
            # Get fund_id and lp_org_id from match
            cur.execute(
                "SELECT fund_id, lp_org_id FROM fund_lp_matches WHERE id = %s",
                (match_id,),
            )
            match = cur.fetchone()
            if not match:
                return HTMLResponse(
                    content='<div class="text-red-500">Match not found</div>',
                    status_code=404,
                )

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
                RETURNING pipeline_stage
                """,
                (match["fund_id"], match["lp_org_id"], stage, notes),
            )
            conn.commit()

            # Status badge styling
            stage_colors = {
                "new": "bg-gray-100 text-gray-700",
                "contacted": "bg-blue-100 text-blue-700",
                "meeting_scheduled": "bg-yellow-100 text-yellow-700",
                "meeting_held": "bg-purple-100 text-purple-700",
                "dd_in_progress": "bg-orange-100 text-orange-700",
                "committed": "bg-green-100 text-green-700",
                "passed": "bg-red-100 text-red-700",
            }
            color = stage_colors.get(stage, "bg-gray-100 text-gray-700")
            display = stage.replace("_", " ").title()

            return HTMLResponse(
                content=f"""
                <span class="px-2 py-1 text-xs rounded-full {color}">
                    {display}
                </span>
                """,
            )
    except Exception as e:
        logger.error(f"Match status update error: {e}")
        return HTMLResponse(
            content=f'<div class="text-red-500">Error: {e}</div>',
            status_code=500,
        )
    finally:
        conn.close()
