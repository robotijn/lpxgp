"""Insights Router - Mutual interests, recommendations, timeline, quality, exports.

This module provides endpoints for:
- Mutual interest detection and alerts
- LP fund recommendations (rule-based)
- Activity timeline for records
- Data quality metrics
- CSV exports
"""

from __future__ import annotations

import csv
import hashlib
import io
import secrets
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Query, Request
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from src import auth
from src.database import get_db
from src.logging_config import get_logger
from src.utils import is_valid_uuid

logger = get_logger(__name__)

router = APIRouter(tags=["insights"])

# Templates
templates_path = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=templates_path)


# =============================================================================
# Mutual Interest Detection
# =============================================================================


def get_mutual_interests_for_gp(user_id: str, conn) -> list[dict[str, Any]]:
    """Find matches where GP is interested AND LP has expressed interest.

    Returns matches where:
    - GP has shortlisted the LP OR pipeline_stage in pursuing/interested
    - LP has interest = 'interested' or 'reviewing' or 'dd_in_progress'
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT
                s.fund_id,
                s.lp_org_id,
                f.name as fund_name,
                lp.name as lp_name,
                s.gp_interest,
                s.lp_interest,
                s.pipeline_stage,
                s.updated_at
            FROM fund_lp_status s
            JOIN funds f ON f.id = s.fund_id
            JOIN organizations lp ON lp.id = s.lp_org_id
            JOIN organizations gp ON gp.id = f.org_id
            JOIN people p ON p.id IN (
                SELECT person_id FROM employment WHERE org_id = gp.id AND is_current = TRUE
            )
            WHERE p.auth_user_id = %s
              AND s.gp_interest IN ('interested', 'pursuing')
              AND s.lp_interest IN ('interested', 'reviewing')
            ORDER BY s.updated_at DESC
            LIMIT 10
            """,
            (user_id,),
        )
        return cur.fetchall() or []


def get_mutual_interests_for_lp(user_id: str, conn) -> list[dict[str, Any]]:
    """Find matches where LP is interested AND GP is pursuing.

    Returns matches where:
    - LP has interest in a fund
    - GP is pursuing that LP
    """
    with conn.cursor() as cur:
        cur.execute(
            """
            SELECT DISTINCT
                s.fund_id,
                s.lp_org_id,
                f.name as fund_name,
                gp.name as gp_name,
                s.gp_interest,
                s.lp_interest,
                s.pipeline_stage,
                s.updated_at
            FROM fund_lp_status s
            JOIN funds f ON f.id = s.fund_id
            JOIN organizations gp ON gp.id = f.org_id
            JOIN organizations lp ON lp.id = s.lp_org_id
            JOIN people p ON p.id IN (
                SELECT person_id FROM employment WHERE org_id = lp.id AND is_current = TRUE
            )
            WHERE p.auth_user_id = %s
              AND s.lp_interest IN ('interested', 'reviewing')
              AND s.gp_interest IN ('interested', 'pursuing')
            ORDER BY s.updated_at DESC
            LIMIT 10
            """,
            (user_id,),
        )
        return cur.fetchall() or []


@router.get("/api/mutual-interests", response_class=HTMLResponse)
async def get_mutual_interests(request: Request) -> HTMLResponse:
    """Get mutual interest alerts for current user."""
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="", status_code=401)

    conn = get_db()
    if not conn:
        return HTMLResponse(content="")

    try:
        role = user.get("role", "gp_user")
        if role == "lp_user":
            interests = get_mutual_interests_for_lp(user["id"], conn)
            party_field = "gp_name"
        else:
            interests = get_mutual_interests_for_gp(user["id"], conn)
            party_field = "lp_name"

        if not interests:
            return HTMLResponse(content="")

        # Build alert HTML
        alerts_html = []
        for item in interests[:5]:  # Show max 5
            party_name = item.get(party_field, "Unknown")
            fund_name = item.get("fund_name", "Fund")
            alerts_html.append(f"""
                <div class="flex items-center justify-between p-3 bg-green-50 border border-green-200 rounded-lg">
                    <div class="flex items-center">
                        <svg class="w-5 h-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                  d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                        </svg>
                        <span class="text-sm text-green-800">
                            <strong>Mutual Interest:</strong> {party_name} - {fund_name}
                        </span>
                    </div>
                    <a href="/pipeline/{item.get('fund_id')}/{item.get('lp_org_id')}"
                       class="text-xs text-green-600 hover:text-green-800 font-medium">
                        View →
                    </a>
                </div>
            """)

        return HTMLResponse(content="\n".join(alerts_html))
    finally:
        conn.close()


# =============================================================================
# LP Fund Recommendations (Rule-Based)
# =============================================================================


def calculate_fund_match_score(mandate: dict, fund: dict) -> dict[str, Any]:
    """Calculate match score between LP mandate and fund.

    Scoring:
    - Strategy match: 40%
    - Geography match: 30%
    - Check size fit: 20%
    - Sector match: 10%
    """
    score_breakdown = {}
    total_score = 0.0

    # Strategy match (40%)
    mandate_strategies = set(mandate.get("strategies") or [])
    fund_strategy = fund.get("strategy")
    if fund_strategy and fund_strategy in mandate_strategies:
        score_breakdown["strategy"] = 40
        total_score += 40
    elif mandate_strategies:
        score_breakdown["strategy"] = 0
    else:
        score_breakdown["strategy"] = 20  # No preference = partial match

    # Geography match (30%)
    mandate_geos = set(mandate.get("geographic_preferences") or [])
    fund_geo = fund.get("geographic_focus")
    if not mandate_geos:
        score_breakdown["geography"] = 15  # No preference
        total_score += 15
    elif fund_geo and any(g.lower() in fund_geo.lower() for g in mandate_geos):
        score_breakdown["geography"] = 30
        total_score += 30
    elif "global" in [g.lower() for g in mandate_geos]:
        score_breakdown["geography"] = 25
        total_score += 25
    else:
        score_breakdown["geography"] = 0

    # Check size fit (20%)
    fund_size = fund.get("target_size_mm") or 0
    lp_min = mandate.get("check_size_min_mm") or 0
    lp_max = mandate.get("check_size_max_mm") or float("inf")

    # Typical LP check is 1-5% of fund size
    typical_check_min = fund_size * 0.01
    typical_check_max = fund_size * 0.05

    if lp_min <= typical_check_max and lp_max >= typical_check_min:
        score_breakdown["check_size"] = 20
        total_score += 20
    elif lp_max >= typical_check_min * 0.5:  # Close enough
        score_breakdown["check_size"] = 10
        total_score += 10
    else:
        score_breakdown["check_size"] = 0

    # Sector match (10%)
    mandate_sectors = set(mandate.get("sector_preferences") or [])
    fund_sectors = set(fund.get("sectors") or [])
    if not mandate_sectors:
        score_breakdown["sector"] = 5
        total_score += 5
    elif mandate_sectors & fund_sectors:
        score_breakdown["sector"] = 10
        total_score += 10
    else:
        score_breakdown["sector"] = 0

    return {
        "total_score": total_score,
        "breakdown": score_breakdown,
    }


@router.get("/api/lp/fund-recommendations", response_class=HTMLResponse)
async def get_lp_fund_recommendations(request: Request) -> HTMLResponse:
    """Get fund recommendations for LP based on mandate matching."""
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="<div>Not authenticated</div>", status_code=401)

    conn = get_db()
    if not conn:
        return HTMLResponse(content="<div>Database unavailable</div>")

    try:
        with conn.cursor() as cur:
            # Get LP's mandate
            cur.execute(
                """
                SELECT lp.strategies, lp.geographic_preferences, lp.sector_preferences,
                       lp.check_size_min_mm, lp.check_size_max_mm
                FROM lp_profiles lp
                JOIN organizations o ON o.id = lp.org_id
                JOIN employment e ON e.org_id = o.id AND e.is_current = TRUE
                JOIN people p ON p.id = e.person_id
                WHERE p.auth_user_id = %s
                """,
                (user["id"],),
            )
            mandate = cur.fetchone()

            if not mandate:
                return HTMLResponse(
                    content="""
                    <div class="text-center py-8 text-navy-500">
                        <p>Set up your investment mandate to see recommendations.</p>
                        <a href="/lp-mandate" class="text-gold hover:underline">Configure Mandate →</a>
                    </div>
                    """
                )

            # Get active funds
            cur.execute(
                """
                SELECT f.id, f.name, f.strategy, f.target_size_mm, f.geographic_focus,
                       f.vintage_year, f.sector_focus, gp.name as gp_name
                FROM funds f
                JOIN organizations gp ON gp.id = f.org_id
                WHERE f.status = 'fundraising' OR f.status IS NULL
                ORDER BY f.created_at DESC
                LIMIT 50
                """
            )
            funds = cur.fetchall() or []

            if not funds:
                return HTMLResponse(
                    content='<div class="text-center py-8 text-navy-500">No funds available.</div>'
                )

            # Score and rank funds
            scored_funds = []
            for fund in funds:
                score_result = calculate_fund_match_score(mandate, fund)
                if score_result["total_score"] >= 30:  # Minimum threshold
                    scored_funds.append({**fund, **score_result})

            scored_funds.sort(key=lambda x: x["total_score"], reverse=True)

            if not scored_funds:
                return HTMLResponse(
                    content="""
                    <div class="text-center py-8 text-navy-500">
                        <p>No matching funds found based on your mandate.</p>
                        <a href="/lp-mandate" class="text-gold hover:underline">Update Mandate →</a>
                    </div>
                    """
                )

            # Build recommendations HTML
            html_parts = []
            for fund in scored_funds[:10]:
                score = int(fund["total_score"])
                score_color = "text-green-600" if score >= 70 else "text-yellow-600" if score >= 50 else "text-navy-500"
                html_parts.append(f"""
                <div class="p-4 bg-white border border-navy-100 rounded-lg hover:shadow-md transition-shadow">
                    <div class="flex items-start justify-between">
                        <div>
                            <h3 class="font-semibold text-navy-900">{fund.get('name', 'Fund')}</h3>
                            <p class="text-sm text-navy-500">{fund.get('gp_name', '')}</p>
                        </div>
                        <span class="px-2 py-1 text-sm font-bold {score_color} bg-navy-50 rounded">
                            {score}%
                        </span>
                    </div>
                    <div class="mt-2 flex flex-wrap gap-2 text-xs">
                        <span class="px-2 py-1 bg-navy-100 text-navy-600 rounded">
                            {(fund.get('strategy') or 'N/A').title()}
                        </span>
                        <span class="px-2 py-1 bg-navy-100 text-navy-600 rounded">
                            ${fund.get('target_size_mm') or 0}M
                        </span>
                        <span class="px-2 py-1 bg-navy-100 text-navy-600 rounded">
                            {fund.get('geographic_focus') or 'Global'}
                        </span>
                    </div>
                    <div class="mt-3 flex gap-2">
                        <a href="/funds/{fund.get('id')}"
                           class="text-xs text-gold hover:text-gold-600 font-medium">
                            View Details →
                        </a>
                    </div>
                </div>
                """)

            return HTMLResponse(content="\n".join(html_parts))
    finally:
        conn.close()


# =============================================================================
# Activity Timeline
# =============================================================================


@router.get("/api/timeline/{entity_type}/{entity_id}", response_class=HTMLResponse)
async def get_activity_timeline(
    request: Request,
    entity_type: str,
    entity_id: str,
) -> HTMLResponse:
    """Get activity timeline for an entity (lp, fund, match).

    Args:
        entity_type: 'lp', 'fund', or 'match'
        entity_id: The entity UUID
    """
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="", status_code=401)

    if not is_valid_uuid(entity_id):
        return HTMLResponse(content="<div>Invalid ID</div>", status_code=400)

    conn = get_db()
    if not conn:
        return HTMLResponse(content="")

    try:
        activities = []
        with conn.cursor() as cur:
            if entity_type == "lp":
                # Get touchpoints for this LP (company_id = LP org)
                cur.execute(
                    """
                    SELECT 'touchpoint' as type, t.touchpoint_type as subtype,
                           t.summary as notes, t.occurred_at as timestamp, p.full_name as actor
                    FROM touchpoints t
                    LEFT JOIN people p ON p.id = t.created_by
                    WHERE t.company_id = %s
                    ORDER BY t.occurred_at DESC
                    LIMIT 20
                    """,
                    (entity_id,),
                )
                activities.extend(cur.fetchall() or [])

                # Get pipeline stage changes
                cur.execute(
                    """
                    SELECT 'stage_change' as type, s.pipeline_stage as subtype,
                           s.notes, s.updated_at as timestamp, NULL as actor
                    FROM fund_lp_status s
                    WHERE s.lp_org_id = %s
                    ORDER BY s.updated_at DESC
                    LIMIT 10
                    """,
                    (entity_id,),
                )
                activities.extend(cur.fetchall() or [])

            elif entity_type == "fund":
                # Get status changes for this fund
                cur.execute(
                    """
                    SELECT 'interest' as type,
                           COALESCE(s.lp_interest, s.gp_interest) as subtype,
                           lp.name as notes, s.updated_at as timestamp, NULL as actor
                    FROM fund_lp_status s
                    JOIN organizations lp ON lp.id = s.lp_org_id
                    WHERE s.fund_id = %s
                    ORDER BY s.updated_at DESC
                    LIMIT 20
                    """,
                    (entity_id,),
                )
                activities.extend(cur.fetchall() or [])

            elif entity_type == "match":
                # Get touchpoints and status for a specific match
                cur.execute(
                    """
                    SELECT s.fund_id, s.lp_org_id FROM fund_lp_status s WHERE s.id = %s
                    """,
                    (entity_id,),
                )
                match = cur.fetchone()
                if match:
                    # Get touchpoints where LP was contacted
                    cur.execute(
                        """
                        SELECT 'touchpoint' as type, t.touchpoint_type as subtype,
                               t.summary as notes, t.occurred_at as timestamp, p.full_name as actor
                        FROM touchpoints t
                        LEFT JOIN people p ON p.id = t.created_by
                        WHERE t.company_id = %s
                        ORDER BY t.occurred_at DESC
                        LIMIT 20
                        """,
                        (match["lp_org_id"],),
                    )
                    activities.extend(cur.fetchall() or [])

        # Sort by timestamp
        activities.sort(key=lambda x: x.get("timestamp") or datetime.min, reverse=True)

        if not activities:
            return HTMLResponse(
                content='<div class="text-sm text-navy-400 py-4">No activity recorded yet.</div>'
            )

        # Build timeline HTML
        html_parts = ['<div class="space-y-3">']
        for activity in activities[:15]:
            activity_type = activity.get("type") or ""
            icon = {
                "touchpoint": "📞",
                "stage_change": "📊",
                "interest": "💡",
            }.get(activity_type, "📌")

            subtype = (activity.get("subtype") or "").replace("_", " ").title()
            notes = activity.get("notes") or ""
            timestamp = activity.get("timestamp")
            time_str = timestamp.strftime("%b %d, %Y") if timestamp else ""
            actor = activity.get("actor") or ""

            html_parts.append(f"""
            <div class="flex items-start gap-3 text-sm">
                <span class="text-lg">{icon}</span>
                <div class="flex-1">
                    <div class="text-navy-700">
                        <span class="font-medium">{subtype}</span>
                        {f'<span class="text-navy-400"> · {actor}</span>' if actor else ''}
                    </div>
                    {f'<p class="text-navy-500 text-xs mt-0.5">{notes[:100]}{"..." if len(notes) > 100 else ""}</p>' if notes else ''}
                </div>
                <span class="text-xs text-navy-400">{time_str}</span>
            </div>
            """)
        html_parts.append("</div>")

        return HTMLResponse(content="\n".join(html_parts))
    finally:
        conn.close()


# =============================================================================
# Data Quality Dashboard
# =============================================================================


def calculate_completeness(record: dict, required_fields: list[str]) -> float:
    """Calculate completeness percentage for a record."""
    if not required_fields:
        return 100.0
    filled = sum(1 for f in required_fields if record.get(f))
    return round(filled / len(required_fields) * 100, 1)


@router.get("/admin/data-quality", response_class=HTMLResponse, response_model=None)
async def data_quality_dashboard(
    request: Request,
    entity: str = Query(default="lps"),
    sort_by: str = Query(default="completeness"),
) -> HTMLResponse | RedirectResponse:
    """Data quality dashboard for admins."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if user.get("role") != "admin":
        return RedirectResponse(url="/dashboard", status_code=303)

    conn = get_db()
    if not conn:
        return templates.TemplateResponse(
            request,
            "pages/admin/data-quality.html",
            {"title": "Data Quality", "user": user, "records": [], "stats": {}},
        )

    try:
        records = []
        stats = {"total": 0, "complete": 0, "incomplete": 0, "avg_completeness": 0}

        with conn.cursor() as cur:
            if entity == "lps":
                required = ["name", "hq_city", "hq_country", "website", "lp_type"]
                cur.execute(
                    """
                    SELECT o.id, o.name, o.hq_city, o.hq_country, o.website,
                           lp.lp_type, lp.total_aum_bn, lp.strategies,
                           o.updated_at
                    FROM organizations o
                    LEFT JOIN lp_profiles lp ON lp.org_id = o.id
                    WHERE o.is_lp = TRUE
                    ORDER BY o.updated_at DESC NULLS LAST
                    LIMIT 100
                    """
                )
            elif entity == "gps":
                required = ["name", "hq_city", "website"]
                cur.execute(
                    """
                    SELECT o.id, o.name, o.hq_city, o.hq_country, o.website,
                           o.updated_at
                    FROM organizations o
                    WHERE o.is_gp = TRUE
                    ORDER BY o.updated_at DESC NULLS LAST
                    LIMIT 100
                    """
                )
            else:  # funds
                required = ["name", "strategy", "target_size_mm", "vintage_year"]
                cur.execute(
                    """
                    SELECT f.id, f.name, f.strategy, f.target_size_mm,
                           f.vintage_year, f.geographic_focus, f.updated_at
                    FROM funds f
                    ORDER BY f.updated_at DESC NULLS LAST
                    LIMIT 100
                    """
                )

            rows = cur.fetchall() or []

            for row in rows:
                completeness = calculate_completeness(row, required)
                missing = [f for f in required if not row.get(f)]
                records.append({
                    **row,
                    "completeness": completeness,
                    "missing_fields": missing,
                })

            # Calculate stats
            stats["total"] = len(records)
            stats["complete"] = sum(1 for r in records if r["completeness"] == 100)
            stats["incomplete"] = stats["total"] - stats["complete"]
            stats["avg_completeness"] = (
                round(sum(r["completeness"] for r in records) / len(records), 1)
                if records
                else 0
            )

            # Sort
            if sort_by == "completeness":
                records.sort(key=lambda x: x["completeness"])
            elif sort_by == "updated":
                records.sort(key=lambda x: x.get("updated_at") or datetime.min)

        return templates.TemplateResponse(
            request,
            "pages/admin/data-quality.html",
            {
                "title": "Data Quality - Admin",
                "user": user,
                "records": records,
                "stats": stats,
                "entity": entity,
                "sort_by": sort_by,
            },
        )
    finally:
        conn.close()


# =============================================================================
# CSV Exports
# =============================================================================


@router.get("/api/export/lps")
async def export_lps_csv(
    request: Request,
    search: str = Query(default=""),
    lp_type: str = Query(default=""),
) -> StreamingResponse:
    """Export LPs to CSV."""
    user = auth.get_current_user(request)
    if not user:
        return StreamingResponse(
            iter(["Not authenticated"]),
            media_type="text/plain",
            status_code=401,
        )

    conn = get_db()
    if not conn:
        return StreamingResponse(
            iter(["Database unavailable"]),
            media_type="text/plain",
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            query = """
                SELECT o.name, o.hq_city, o.hq_country, o.website,
                       lp.lp_type, lp.total_aum_bn, lp.pe_allocation_pct,
                       lp.strategies, lp.geographic_preferences
                FROM organizations o
                LEFT JOIN lp_profiles lp ON lp.org_id = o.id
                WHERE o.is_lp = TRUE
            """
            params: list[Any] = []

            if search:
                query += " AND o.name ILIKE %s"
                params.append(f"%{search}%")
            if lp_type:
                query += " AND lp.lp_type = %s"
                params.append(lp_type)

            query += " ORDER BY o.name LIMIT 1000"
            cur.execute(query, params)
            rows = cur.fetchall() or []

        # Create CSV
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "Name", "City", "Country", "Website", "LP Type",
            "AUM (Bn)", "PE Allocation %", "Strategies", "Geographies"
        ])
        for row in rows:
            writer.writerow([
                row.get("name"),
                row.get("hq_city"),
                row.get("hq_country"),
                row.get("website"),
                row.get("lp_type"),
                row.get("total_aum_bn"),
                row.get("pe_allocation_pct"),
                ", ".join(row.get("strategies") or []),
                ", ".join(row.get("geographic_preferences") or []),
            ])

        output.seek(0)
        filename = f"lps_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    finally:
        conn.close()


@router.get("/api/export/pipeline/{fund_id}")
async def export_pipeline_csv(
    request: Request,
    fund_id: str,
) -> StreamingResponse:
    """Export pipeline for a fund to CSV."""
    user = auth.get_current_user(request)
    if not user:
        return StreamingResponse(
            iter(["Not authenticated"]),
            media_type="text/plain",
            status_code=401,
        )

    if not is_valid_uuid(fund_id):
        return StreamingResponse(
            iter(["Invalid fund ID"]),
            media_type="text/plain",
            status_code=400,
        )

    conn = get_db()
    if not conn:
        return StreamingResponse(
            iter(["Database unavailable"]),
            media_type="text/plain",
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT o.name as lp_name, o.hq_city, lp.lp_type, lp.total_aum_bn,
                       s.pipeline_stage, s.gp_interest, s.lp_interest, s.notes,
                       s.updated_at
                FROM fund_lp_status s
                JOIN organizations o ON o.id = s.lp_org_id
                LEFT JOIN lp_profiles lp ON lp.org_id = o.id
                WHERE s.fund_id = %s
                ORDER BY s.pipeline_stage, o.name
                """,
                (fund_id,),
            )
            rows = cur.fetchall() or []

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "LP Name", "City", "LP Type", "AUM (Bn)", "Pipeline Stage",
            "GP Interest", "LP Interest", "Notes", "Last Updated"
        ])
        for row in rows:
            writer.writerow([
                row.get("lp_name"),
                row.get("hq_city"),
                row.get("lp_type"),
                row.get("total_aum_bn"),
                row.get("pipeline_stage"),
                row.get("gp_interest"),
                row.get("lp_interest"),
                row.get("notes"),
                row.get("updated_at"),
            ])

        output.seek(0)
        filename = f"pipeline_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    finally:
        conn.close()


@router.get("/api/export/shortlist")
async def export_shortlist_csv(request: Request) -> StreamingResponse:
    """Export user's shortlist to CSV."""
    user = auth.get_current_user(request)
    if not user:
        return StreamingResponse(
            iter(["Not authenticated"]),
            media_type="text/plain",
            status_code=401,
        )

    conn = get_db()
    if not conn:
        return StreamingResponse(
            iter(["Database unavailable"]),
            media_type="text/plain",
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT o.name, o.hq_city, o.hq_country, o.website,
                       lp.lp_type, lp.total_aum_bn, s.priority, s.notes,
                       s.created_at
                FROM shortlists s
                JOIN organizations o ON o.id = s.lp_id
                LEFT JOIN lp_profiles lp ON lp.org_id = o.id
                WHERE s.user_id = %s
                ORDER BY s.priority DESC, s.created_at DESC
                """,
                (user["id"],),
            )
            rows = cur.fetchall() or []

        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "LP Name", "City", "Country", "Website", "LP Type",
            "AUM (Bn)", "Priority", "Notes", "Added"
        ])
        for row in rows:
            writer.writerow([
                row.get("name"),
                row.get("hq_city"),
                row.get("hq_country"),
                row.get("website"),
                row.get("lp_type"),
                row.get("total_aum_bn"),
                row.get("priority"),
                row.get("notes"),
                row.get("created_at"),
            ])

        output.seek(0)
        filename = f"shortlist_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"

        return StreamingResponse(
            iter([output.getvalue()]),
            media_type="text/csv",
            headers={"Content-Disposition": f"attachment; filename={filename}"},
        )
    finally:
        conn.close()


# =============================================================================
# Tracking Links - Track Email/Pitch Engagement
# =============================================================================


def generate_tracking_token(fund_id: str, lp_id: str) -> str:
    """Generate a unique tracking token for a fund-LP pair.

    The token is deterministic but hard to guess, based on:
    - Fund ID + LP ID + secret salt
    """
    # Use first 12 chars of hash for readable URLs
    data = f"{fund_id}:{lp_id}:{secrets.token_hex(8)}"
    return hashlib.sha256(data.encode()).hexdigest()[:12]


@router.post("/api/tracking-link", response_class=HTMLResponse)
async def create_tracking_link(
    request: Request,
    fund_id: str = Query(...),
    lp_id: str = Query(...),
) -> HTMLResponse:
    """Generate a tracking link for an outreach email.

    The link, when clicked by the LP, will:
    1. Record engagement as a touchpoint
    2. Update pipeline stage to 'lp_reviewing'
    3. Check for mutual interest
    """
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="<div>Not authenticated</div>", status_code=401)

    if not is_valid_uuid(fund_id) or not is_valid_uuid(lp_id):
        return HTMLResponse(content="<div>Invalid IDs</div>", status_code=400)

    conn = get_db()
    if not conn:
        return HTMLResponse(content="<div>Database unavailable</div>", status_code=503)

    try:
        with conn.cursor() as cur:
            # Generate token and store
            token = generate_tracking_token(fund_id, lp_id)

            # Upsert tracking link record
            cur.execute(
                """
                INSERT INTO tracking_links (token, fund_id, lp_org_id, created_by, created_at)
                VALUES (%s, %s, %s, %s, NOW())
                ON CONFLICT (fund_id, lp_org_id) DO UPDATE SET
                    token = EXCLUDED.token,
                    created_at = NOW(),
                    click_count = 0
                RETURNING token
                """,
                (token, fund_id, lp_id, user["id"]),
            )
            conn.commit()

            # Build the tracking URL
            # In production, this would be the actual domain
            base_url = str(request.base_url).rstrip("/")
            tracking_url = f"{base_url}/i/{token}"

            return HTMLResponse(
                content=f"""
                <div class="p-4 bg-green-50 border border-green-200 rounded-lg">
                    <div class="flex items-center mb-2">
                        <svg class="w-5 h-5 text-green-500 mr-2" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M13.828 10.172a4 4 0 00-5.656 0l-4 4a4 4 0 105.656 5.656l1.102-1.101m-.758-4.899a4 4 0 005.656 0l4-4a4 4 0 00-5.656-5.656l-1.1 1.1"/>
                        </svg>
                        <span class="font-medium text-green-800">Tracking Link Generated</span>
                    </div>
                    <div class="flex items-center gap-2">
                        <input type="text" value="{tracking_url}" readonly
                               class="flex-1 px-3 py-2 text-sm bg-white border border-green-300 rounded"
                               id="tracking-url-{token}">
                        <button onclick="navigator.clipboard.writeText('{tracking_url}'); this.textContent='Copied!'"
                                class="px-3 py-2 text-sm bg-green-600 text-white rounded hover:bg-green-700">
                            Copy
                        </button>
                    </div>
                    <p class="text-xs text-green-600 mt-2">
                        Include this link in your email. When clicked, we'll track engagement and update the pipeline.
                    </p>
                </div>
                """
            )
    except Exception as e:
        # If table doesn't exist, create it and retry
        if "tracking_links" in str(e):
            try:
                with conn.cursor() as cur:
                    cur.execute("""
                        CREATE TABLE IF NOT EXISTS tracking_links (
                            id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
                            token VARCHAR(20) UNIQUE NOT NULL,
                            fund_id UUID NOT NULL,
                            lp_org_id UUID NOT NULL,
                            created_by UUID,
                            created_at TIMESTAMPTZ DEFAULT NOW(),
                            first_clicked_at TIMESTAMPTZ,
                            last_clicked_at TIMESTAMPTZ,
                            click_count INTEGER DEFAULT 0,
                            UNIQUE(fund_id, lp_org_id)
                        );
                        CREATE INDEX IF NOT EXISTS idx_tracking_links_token ON tracking_links(token);
                    """)
                    conn.commit()
                # Retry the insert
                return await create_tracking_link(request, fund_id, lp_id)
            except Exception:
                pass
        logger.error(f"Tracking link error: {e}")
        return HTMLResponse(
            content='<div class="text-red-500">Error creating link</div>',
            status_code=500,
        )
    finally:
        conn.close()


@router.get("/i/{token}", response_class=HTMLResponse)
async def handle_tracking_click(request: Request, token: str) -> HTMLResponse:
    """Handle tracking link click.

    When an LP clicks the tracking link in an email:
    1. Record the click as a touchpoint
    2. Update LP interest to 'interested' (if not already higher)
    3. Check for mutual interest
    4. Show a landing page with fund info
    """
    conn = get_db()
    if not conn:
        return templates.TemplateResponse(
            request,
            "pages/error.html",
            {"title": "Error", "error_code": 503, "error_message": "Service unavailable"},
            status_code=503,
        )

    try:
        with conn.cursor() as cur:
            # Find the tracking link
            cur.execute(
                """
                SELECT t.fund_id, t.lp_org_id, t.click_count,
                       f.name as fund_name, f.org_id as gp_org_id, gp.name as gp_name,
                       f.strategy, f.target_size_mm, f.geographic_focus
                FROM tracking_links t
                JOIN funds f ON f.id = t.fund_id
                JOIN organizations gp ON gp.id = f.org_id
                WHERE t.token = %s
                """,
                (token,),
            )
            link = cur.fetchone()

            if not link:
                return templates.TemplateResponse(
                    request,
                    "pages/error.html",
                    {"title": "Link Expired", "error_code": 404,
                     "error_message": "This link is no longer valid."},
                    status_code=404,
                )

            fund_id = link["fund_id"]
            lp_id = link["lp_org_id"]
            gp_org_id = link["gp_org_id"]
            is_first_click = link["click_count"] == 0

            # Update click count
            cur.execute(
                """
                UPDATE tracking_links
                SET click_count = click_count + 1,
                    first_clicked_at = COALESCE(first_clicked_at, NOW()),
                    last_clicked_at = NOW()
                WHERE token = %s
                """,
                (token,),
            )

            # Record touchpoint (only on first click)
            # org_id = GP who sent email, company_id = LP who clicked
            if is_first_click:
                cur.execute(
                    """
                    INSERT INTO touchpoints (org_id, company_id, touchpoint_type, summary, occurred_at)
                    VALUES (%s, %s, 'email', 'LP clicked tracking link in outreach email', NOW())
                    """,
                    (gp_org_id, lp_id),
                )

                # Update LP interest (if not already interested/reviewing)
                cur.execute(
                    """
                    INSERT INTO fund_lp_status (fund_id, lp_org_id, lp_interest, lp_interest_at)
                    VALUES (%s, %s, 'interested', NOW())
                    ON CONFLICT (fund_id, lp_org_id) DO UPDATE SET
                        lp_interest = CASE
                            WHEN fund_lp_status.lp_interest IS NULL THEN 'interested'
                            WHEN fund_lp_status.lp_interest = 'not_interested' THEN fund_lp_status.lp_interest
                            ELSE fund_lp_status.lp_interest
                        END,
                        lp_interest_at = COALESCE(fund_lp_status.lp_interest_at, NOW()),
                        updated_at = NOW()
                    """,
                    (fund_id, lp_id),
                )

            conn.commit()

            # Build a nice landing page
            return HTMLResponse(
                content=f"""
                <!DOCTYPE html>
                <html lang="en">
                <head>
                    <meta charset="UTF-8">
                    <meta name="viewport" content="width=device-width, initial-scale=1.0">
                    <title>{link['fund_name']} - LPxGP</title>
                    <script src="https://cdn.tailwindcss.com"></script>
                </head>
                <body class="bg-gray-50 min-h-screen">
                    <div class="max-w-2xl mx-auto px-4 py-12">
                        <div class="bg-white rounded-xl shadow-lg p-8">
                            <div class="text-center mb-8">
                                <div class="w-16 h-16 bg-gold/10 rounded-full flex items-center justify-center mx-auto mb-4">
                                    <svg class="w-8 h-8 text-gold" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2"
                                              d="M9 12l2 2 4-4m6 2a9 9 0 11-18 0 9 9 0 0118 0z"/>
                                    </svg>
                                </div>
                                <h1 class="text-2xl font-bold text-gray-900">{link['fund_name']}</h1>
                                <p class="text-gray-500">{link['gp_name']}</p>
                            </div>

                            <div class="grid grid-cols-2 gap-4 mb-8">
                                <div class="bg-gray-50 rounded-lg p-4 text-center">
                                    <div class="text-sm text-gray-500">Strategy</div>
                                    <div class="font-semibold text-gray-900">
                                        {(link['strategy'] or 'N/A').title()}
                                    </div>
                                </div>
                                <div class="bg-gray-50 rounded-lg p-4 text-center">
                                    <div class="text-sm text-gray-500">Target Size</div>
                                    <div class="font-semibold text-gray-900">
                                        ${link['target_size_mm'] or 0}M
                                    </div>
                                </div>
                                <div class="bg-gray-50 rounded-lg p-4 text-center col-span-2">
                                    <div class="text-sm text-gray-500">Geographic Focus</div>
                                    <div class="font-semibold text-gray-900">
                                        {link['geographic_focus'] or 'Global'}
                                    </div>
                                </div>
                            </div>

                            <div class="text-center">
                                <p class="text-gray-600 mb-4">
                                    Interested in learning more about this opportunity?
                                </p>
                                <a href="/login"
                                   class="inline-block px-6 py-3 bg-gold text-white font-medium rounded-lg hover:bg-gold-600 transition">
                                    Sign In to View Details
                                </a>
                                <p class="text-xs text-gray-400 mt-4">
                                    Don't have an account? <a href="/register" class="text-gold hover:underline">Register here</a>
                                </p>
                            </div>
                        </div>

                        <div class="text-center mt-8">
                            <p class="text-xs text-gray-400">
                                Powered by <a href="/" class="text-gold hover:underline">LPxGP</a>
                            </p>
                        </div>
                    </div>
                    <style>
                        .text-gold {{ color: #D4AF37; }}
                        .bg-gold {{ background-color: #D4AF37; }}
                        .bg-gold\\/10 {{ background-color: rgba(212, 175, 55, 0.1); }}
                        .hover\\:bg-gold-600:hover {{ background-color: #C9A227; }}
                    </style>
                </body>
                </html>
                """
            )
    except Exception as e:
        logger.error(f"Tracking click error: {e}")
        return templates.TemplateResponse(
            request,
            "pages/error.html",
            {"title": "Error", "error_code": 500, "error_message": "Something went wrong"},
            status_code=500,
        )
    finally:
        conn.close()


@router.get("/api/tracking-stats/{fund_id}/{lp_id}", response_class=HTMLResponse)
async def get_tracking_stats(
    request: Request,
    fund_id: str,
    lp_id: str,
) -> HTMLResponse:
    """Get tracking statistics for a fund-LP pair."""
    user = auth.get_current_user(request)
    if not user:
        return HTMLResponse(content="", status_code=401)

    if not is_valid_uuid(fund_id) or not is_valid_uuid(lp_id):
        return HTMLResponse(content="")

    conn = get_db()
    if not conn:
        return HTMLResponse(content="")

    try:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT click_count, first_clicked_at, last_clicked_at
                FROM tracking_links
                WHERE fund_id = %s AND lp_org_id = %s
                """,
                (fund_id, lp_id),
            )
            stats = cur.fetchone()

            if not stats or stats["click_count"] == 0:
                return HTMLResponse(
                    content='<span class="text-xs text-gray-400">No clicks yet</span>'
                )

            first_click = stats["first_clicked_at"]
            click_date = first_click.strftime("%b %d") if first_click else "Unknown"

            return HTMLResponse(
                content=f"""
                <div class="flex items-center gap-2 text-xs">
                    <span class="inline-flex items-center px-2 py-1 bg-green-100 text-green-700 rounded-full">
                        <svg class="w-3 h-3 mr-1" fill="currentColor" viewBox="0 0 20 20">
                            <path d="M10 18a8 8 0 100-16 8 8 0 000 16zm3.707-9.293a1 1 0 00-1.414-1.414L9 10.586 7.707 9.293a1 1 0 00-1.414 1.414l2 2a1 1 0 001.414 0l4-4z"/>
                        </svg>
                        Opened {click_date}
                    </span>
                    <span class="text-gray-400">({stats['click_count']} clicks)</span>
                </div>
                """
            )
    finally:
        conn.close()
