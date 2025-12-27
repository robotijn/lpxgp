"""Admin routes for platform management.

This router provides:
- /admin: Admin dashboard
- /admin/users: User management
- /admin/health: System health
- /admin/lps: LP database management
- /admin/companies: Company management
- /admin/people: People management
- /api/admin/stats: Platform stats API
"""

from __future__ import annotations

import csv
import io
from datetime import datetime
from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse, StreamingResponse
from fastapi.templating import Jinja2Templates

from src import auth
from src.config import get_settings
from src.logging_config import get_logger
from src.utils import get_db

router = APIRouter(tags=["admin"])
logger = get_logger(__name__)

# Templates
TEMPLATES_DIR = Path(__file__).parent.parent / "templates"
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# =============================================================================
# Helper Functions
# =============================================================================


def is_admin(user: auth.CurrentUser | None) -> bool:
    """Check if user has admin role."""
    if not user:
        return False
    return user.get("role") == "admin"


def can_manage_data(user: auth.CurrentUser | None) -> bool:
    """Check if user can manage LP/Company data.

    Allowed roles: admin, fa (fund advisor), gp.
    LP users cannot manage data.
    """
    if not user:
        return False
    return user.get("role") in ("admin", "fa", "gp")


# =============================================================================
# Admin Dashboard
# =============================================================================


@router.get("/admin", response_class=HTMLResponse, response_model=None)
async def admin_dashboard(request: Request) -> HTMLResponse | RedirectResponse:
    """Admin dashboard showing platform overview."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not is_admin(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    stats = {
        "companies": 0,
        "users": 0,
        "lps": 0,
        "matches": 0,
    }

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM organizations WHERE is_gp = TRUE")
                result = cur.fetchone()
                stats["companies"] = result["count"] if result else 0

                cur.execute("SELECT COUNT(*) FROM organizations WHERE is_lp = TRUE")
                result = cur.fetchone()
                stats["lps"] = result["count"] if result else 0

                cur.execute("SELECT COUNT(*) FROM fund_lp_matches")
                result = cur.fetchone()
                stats["matches"] = result["count"] if result else 0
        except Exception:
            pass
        finally:
            conn.close()

    stats["users"] = len(auth._mock_users)

    health = {
        "database": conn is not None,
        "auth": True,
    }

    return templates.TemplateResponse(
        request,
        "pages/admin/dashboard.html",
        {
            "title": "Admin Dashboard - LPxGP",
            "user": user,
            "stats": stats,
            "health": health,
        },
    )


@router.get("/admin/users", response_class=HTMLResponse, response_model=None)
async def admin_users_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Admin users management page."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not is_admin(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    users = []
    for email, user_data in auth._mock_users.items():
        users.append({
            "id": user_data["id"],
            "email": email,
            "name": user_data["name"],
            "role": user_data["role"],
        })

    return templates.TemplateResponse(
        request,
        "pages/admin/users.html",
        {
            "title": "Users - Admin - LPxGP",
            "user": user,
            "users": users,
            "total_users": len(users),
        },
    )


@router.get("/admin/health", response_class=HTMLResponse, response_model=None)
async def admin_health_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Admin system health page."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not is_admin(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    settings = get_settings()
    health_checks = []

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
            health_checks.append({
                "name": "Database",
                "status": "healthy",
                "message": "Connection successful",
            })
        except Exception as e:
            health_checks.append({
                "name": "Database",
                "status": "unhealthy",
                "message": str(e),
            })
        finally:
            conn.close()
    else:
        health_checks.append({
            "name": "Database",
            "status": "unconfigured",
            "message": "Database not configured",
        })

    health_checks.append({
        "name": "Authentication",
        "status": "healthy",
        "message": f"{len(auth._mock_users)} users registered",
    })

    health_checks.append({
        "name": "Environment",
        "status": "info",
        "message": settings.environment,
    })

    return templates.TemplateResponse(
        request,
        "pages/admin/health.html",
        {
            "title": "System Health - Admin - LPxGP",
            "user": user,
            "health_checks": health_checks,
        },
    )


@router.get("/api/admin/stats", response_class=JSONResponse)
async def api_admin_stats(request: Request) -> JSONResponse:
    """Get platform statistics for admin dashboard."""
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(
            status_code=401,
            content={"error": "Authentication required"},
        )

    if not is_admin(user):
        return JSONResponse(
            status_code=403,
            content={"error": "Admin access required"},
        )

    stats = {
        "companies": 0,
        "users": len(auth._mock_users),
        "lps": 0,
        "matches": 0,
    }

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("SELECT COUNT(*) FROM organizations WHERE is_gp = TRUE")
                result = cur.fetchone()
                stats["companies"] = result["count"] if result else 0

                cur.execute("SELECT COUNT(*) FROM organizations WHERE is_lp = TRUE")
                result = cur.fetchone()
                stats["lps"] = result["count"] if result else 0

                cur.execute("SELECT COUNT(*) FROM fund_lp_matches")
                result = cur.fetchone()
                stats["matches"] = result["count"] if result else 0
        except Exception:
            pass
        finally:
            conn.close()

    return JSONResponse(content={"success": True, "stats": stats})


# =============================================================================
# CSV Export
# =============================================================================


@router.get("/api/admin/export/lps", response_model=None)
async def export_lps_csv(request: Request) -> StreamingResponse | JSONResponse:
    """Export LPs to CSV file."""
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Authentication required"})

    if not can_manage_data(user):
        return JSONResponse(status_code=403, content={"error": "Insufficient permissions"})

    lps: list[dict[str, Any]] = []

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, description, lp_type, location, total_aum_bn,
                           pe_allocation_pct, preferred_strategies, preferred_geographies,
                           min_fund_size_mm, max_fund_size_mm, is_active, created_at
                    FROM organizations
                    WHERE is_lp = TRUE
                    ORDER BY name
                """)
                rows = cur.fetchall()
                lps = [dict(row) for row in rows]
        except Exception as e:
            logger.warning(f"Failed to export LPs: {e}")
        finally:
            conn.close()

    if not lps:
        lps = [
            {"id": "lp-001", "name": "CalPERS", "lp_type": "pension", "location": "California, USA", "total_aum_bn": 440, "is_active": True},
            {"id": "lp-002", "name": "Yale Endowment", "lp_type": "endowment", "location": "Connecticut, USA", "total_aum_bn": 41, "is_active": True},
        ]

    output = io.StringIO()
    if lps:
        fieldnames = list(lps[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(lps)

    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"lps_export_{timestamp}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/api/admin/export/funds", response_model=None)
async def export_funds_csv(request: Request) -> StreamingResponse | JSONResponse:
    """Export Funds to CSV file."""
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Authentication required"})

    if not can_manage_data(user):
        return JSONResponse(status_code=403, content={"error": "Insufficient permissions"})

    funds: list[dict[str, Any]] = []

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT f.id, f.name, f.description, f.strategy, f.target_size_mm,
                           f.vintage, f.status, o.name as org_name
                    FROM funds f
                    LEFT JOIN organizations o ON o.id = f.org_id
                    ORDER BY f.name
                """)
                rows = cur.fetchall()
                funds = [dict(row) for row in rows]
        except Exception as e:
            logger.warning(f"Failed to export funds: {e}")
        finally:
            conn.close()

    if not funds:
        funds = [
            {"id": "fund-001", "name": "Growth Fund III", "org_name": "Acme Capital", "strategy": "growth_equity", "target_size_mm": 500, "vintage": 2024, "status": "fundraising"},
            {"id": "fund-002", "name": "Buyout Fund IV", "org_name": "Acme Capital", "strategy": "buyout", "target_size_mm": 1200, "vintage": 2023, "status": "active"},
        ]

    output = io.StringIO()
    if funds:
        fieldnames = list(funds[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(funds)

    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"funds_export_{timestamp}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


@router.get("/api/admin/export/companies", response_model=None)
async def export_companies_csv(request: Request) -> StreamingResponse | JSONResponse:
    """Export Companies to CSV file."""
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Authentication required"})

    if not can_manage_data(user):
        return JSONResponse(status_code=403, content={"error": "Insufficient permissions"})

    companies: list[dict[str, Any]] = []

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT id, name, description, website, hq_city, hq_country,
                           is_gp, is_lp, created_at
                    FROM organizations
                    WHERE is_gp = TRUE
                    ORDER BY name
                """)
                rows = cur.fetchall()
                companies = [dict(row) for row in rows]
        except Exception as e:
            logger.warning(f"Failed to export companies: {e}")
        finally:
            conn.close()

    if not companies:
        companies = [
            {"id": "org-001", "name": "Acme Capital", "website": "https://acmecapital.com", "hq_city": "New York", "hq_country": "USA", "is_gp": True},
            {"id": "org-002", "name": "Beta Ventures", "website": None, "hq_city": "San Francisco", "hq_country": "USA", "is_gp": True},
        ]

    output = io.StringIO()
    if companies:
        fieldnames = list(companies[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(companies)

    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"companies_export_{timestamp}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )


# =============================================================================
# LP Management
# =============================================================================


@router.get("/admin/lps", response_class=HTMLResponse, response_model=None)
async def admin_lps_page(
    request: Request,
    page: int = 1,
    q: str | None = None,
    type: str | None = None,
) -> HTMLResponse | RedirectResponse:
    """LP database management page."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not can_manage_data(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    per_page = 25

    mock_lps: list[dict[str, Any]] = [
        {"id": "lp-001", "name": "CalPERS", "description": "California Public Employees' Retirement System", "lp_type": "pension", "location": "Sacramento, CA", "total_aum_bn": 450, "is_active": True},
        {"id": "lp-002", "name": "Yale Endowment", "description": "Yale University Investments Office", "lp_type": "endowment", "location": "New Haven, CT", "total_aum_bn": 41, "is_active": True},
        {"id": "lp-003", "name": "Smith Family Office", "description": "Multi-family office", "lp_type": "family_office", "location": "New York, NY", "total_aum_bn": 2, "is_active": True},
        {"id": "lp-004", "name": "Ontario Teachers'", "description": "Ontario Teachers' Pension Plan", "lp_type": "pension", "location": "Toronto, Canada", "total_aum_bn": 250, "is_active": True},
        {"id": "lp-005", "name": "GIC", "description": "Government of Singapore Investment Corporation", "lp_type": "sovereign_wealth", "location": "Singapore", "total_aum_bn": 690, "is_active": True},
    ]

    lps: list[dict[str, Any]] = []
    stats: dict[str, int] = {"total": 0, "pensions": 0, "endowments": 0, "family_offices": 0, "other": 0}

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT lp.id, o.name, o.description, lp.lp_type,
                           CONCAT(o.hq_city, ', ', o.hq_country) as location,
                           lp.total_aum_bn, lp.is_active
                    FROM lp_profiles lp
                    JOIN organizations o ON lp.org_id = o.id
                    WHERE 1=1
                """
                params: list = []

                if q:
                    query += " AND o.name ILIKE %s"
                    params.append(f"%{q}%")

                if type:
                    query += " AND lp.lp_type = %s"
                    params.append(type)

                query += " ORDER BY o.name LIMIT %s OFFSET %s"
                params.extend([per_page, (page - 1) * per_page])

                cur.execute(query, params)
                rows = cur.fetchall()
                lps = [dict(row) for row in rows]

                cur.execute("SELECT COUNT(*) FROM lp_profiles")
                result = cur.fetchone()
                stats["total"] = result["count"] if result else 0

                cur.execute("SELECT COUNT(*) FROM lp_profiles WHERE lp_type = 'pension'")
                result = cur.fetchone()
                stats["pensions"] = result["count"] if result else 0

                cur.execute("SELECT COUNT(*) FROM lp_profiles WHERE lp_type = 'endowment'")
                result = cur.fetchone()
                stats["endowments"] = result["count"] if result else 0

                cur.execute("SELECT COUNT(*) FROM lp_profiles WHERE lp_type = 'family_office'")
                result = cur.fetchone()
                stats["family_offices"] = result["count"] if result else 0

                cur.execute("SELECT COUNT(*) FROM lp_profiles WHERE lp_type NOT IN ('pension', 'endowment', 'family_office')")
                result = cur.fetchone()
                stats["other"] = result["count"] if result else 0

        except Exception as e:
            logger.warning(f"Failed to fetch LPs from database: {e}")
            lps = mock_lps
            stats = {"total": 5, "pensions": 2, "endowments": 1, "family_offices": 1, "other": 1}
        finally:
            conn.close()
    else:
        lps = mock_lps
        stats = {"total": 5, "pensions": 2, "endowments": 1, "family_offices": 1, "other": 1}

        if q:
            lps = [lp for lp in lps if q.lower() in lp["name"].lower()]
        if type:
            lps = [lp for lp in lps if lp["lp_type"] == type]

    total_pages = max(1, (stats["total"] + per_page - 1) // per_page)

    return templates.TemplateResponse(
        request,
        "pages/admin/lps.html",
        {
            "title": "LP Database - LPxGP",
            "user": user,
            "lps": lps,
            "stats": stats,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "search_query": q,
            "filter_type": type,
        },
    )


@router.get("/admin/lps/new", response_class=HTMLResponse, response_model=None)
async def admin_lp_new_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Create new LP page."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not can_manage_data(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    return templates.TemplateResponse(
        request,
        "pages/admin/lp-detail.html",
        {
            "title": "Add New LP - LPxGP",
            "user": user,
            "lp": None,
        },
    )


@router.get("/admin/lps/{lp_id}", response_class=HTMLResponse, response_model=None)
async def admin_lp_detail_page(request: Request, lp_id: str) -> HTMLResponse | RedirectResponse:
    """LP detail/edit page."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not can_manage_data(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    mock_lps = {
        "lp-001": {
            "id": "lp-001", "name": "CalPERS", "description": "California Public Employees' Retirement System",
            "lp_type": "pension", "location": "Sacramento, CA, USA", "total_aum_bn": 450, "pe_allocation": "13%",
            "typical_commitment_min_m": 100, "typical_commitment_max_m": 500,
            "preferred_strategies": ["buyout", "growth_equity", "infrastructure"],
            "preferred_geographies": ["North America", "Europe"],
            "investment_mandate": "CalPERS maintains a diversified private equity portfolio.",
            "is_active": True, "updated_at": "2 weeks ago",
        },
        "lp-002": {
            "id": "lp-002", "name": "Yale Endowment", "description": "Yale University Investments Office",
            "lp_type": "endowment", "location": "New Haven, CT, USA", "total_aum_bn": 41, "pe_allocation": "41%",
            "typical_commitment_min_m": 25, "typical_commitment_max_m": 150,
            "preferred_strategies": ["venture_capital", "buyout"],
            "preferred_geographies": ["Global"],
            "investment_mandate": "Pioneer of the endowment model.",
            "is_active": True, "updated_at": "1 week ago",
        },
    }

    lp = None
    conn = get_db()
    if conn:
        try:
            from uuid import UUID
            UUID(lp_id)

            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT lp.id, o.name, o.description, lp.lp_type,
                           CONCAT(o.hq_city, ', ', o.hq_country) as location,
                           lp.total_aum_bn, lp.typical_commitment_min_m,
                           lp.typical_commitment_max_m, lp.preferred_strategies,
                           lp.preferred_geographies, lp.investment_mandate,
                           lp.is_active, lp.updated_at
                    FROM lp_profiles lp
                    JOIN organizations o ON lp.org_id = o.id
                    WHERE lp.id = %s
                    """,
                    [lp_id],
                )
                row = cur.fetchone()
                if row:
                    lp = dict(row)
        except ValueError:
            lp = mock_lps.get(lp_id)
        except Exception as e:
            logger.warning(f"Failed to fetch LP from database: {e}")
            lp = mock_lps.get(lp_id)
        finally:
            conn.close()
    else:
        lp = mock_lps.get(lp_id)

    if not lp:
        return RedirectResponse(url="/admin/lps", status_code=303)

    return templates.TemplateResponse(
        request,
        "pages/admin/lp-detail.html",
        {
            "title": f"Edit {lp['name']} - LPxGP",
            "user": user,
            "lp": lp,
        },
    )


@router.post("/admin/lps/new", response_class=HTMLResponse, response_model=None)
async def admin_lp_create(request: Request) -> HTMLResponse | RedirectResponse:
    """Create new LP."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not can_manage_data(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    form = await request.form()
    name = str(form.get("name", "")).strip()
    lp_type = str(form.get("lp_type", "")).strip()

    if not name or not lp_type:
        return templates.TemplateResponse(
            request,
            "pages/admin/lp-detail.html",
            {
                "title": "Add New LP - LPxGP",
                "user": user,
                "lp": None,
                "error": "Name and Type are required",
            },
        )

    logger.info(f"Would create LP: {name} ({lp_type})")
    return RedirectResponse(url="/admin/lps", status_code=303)


@router.post("/admin/lps/{lp_id}", response_class=HTMLResponse, response_model=None)
async def admin_lp_update(request: Request, lp_id: str) -> HTMLResponse | RedirectResponse:
    """Update LP."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not can_manage_data(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    form = await request.form()
    name = str(form.get("name", "")).strip()
    lp_type = str(form.get("lp_type", "")).strip()

    if not name or not lp_type:
        return RedirectResponse(url=f"/admin/lps/{lp_id}", status_code=303)

    logger.info(f"Would update LP {lp_id}: {name} ({lp_type})")
    return RedirectResponse(url="/admin/lps", status_code=303)


@router.delete("/admin/lps/{lp_id}", response_model=None)
async def admin_lp_delete(request: Request, lp_id: str) -> JSONResponse | RedirectResponse:
    """Delete LP."""
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(content={"error": "Not authenticated"}, status_code=401)

    if not can_manage_data(user):
        return JSONResponse(content={"error": "Insufficient permissions"}, status_code=403)

    logger.info(f"Would delete LP {lp_id}")
    return JSONResponse(content={"success": True})


# =============================================================================
# Company Management
# =============================================================================


@router.get("/admin/companies", response_class=HTMLResponse, response_model=None)
async def admin_companies_page(
    request: Request,
    page: int = 1,
    q: str | None = None,
    status: str | None = None,
) -> HTMLResponse | RedirectResponse:
    """Companies management page."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not can_manage_data(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    per_page = 25

    mock_companies: list[dict[str, Any]] = [
        {"id": "org-001", "name": "Acme Capital", "initials": "AC", "color": "navy", "type": "Private Equity", "admin_email": "john@acmecapital.com", "user_count": 4, "fund_count": 3, "status": "active", "created_at": "Dec 1, 2024"},
        {"id": "org-002", "name": "Beta Ventures", "initials": "BV", "color": "green", "type": "Venture Capital", "admin_email": None, "user_count": 0, "fund_count": 0, "status": "pending", "created_at": "Dec 18, 2024"},
        {"id": "org-003", "name": "Gamma Partners", "initials": "GP", "color": "purple", "type": "Growth Equity", "admin_email": "alex@gammapartners.com", "user_count": 2, "fund_count": 1, "status": "inactive", "created_at": "Oct 15, 2024"},
        {"id": "org-004", "name": "Delta Capital", "initials": "DC", "color": "blue", "type": "Private Equity", "admin_email": "sarah@deltacap.com", "user_count": 6, "fund_count": 4, "status": "active", "created_at": "Sep 20, 2024"},
    ]

    companies: list[dict[str, Any]] = []
    total_companies = 0

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                query = """
                    SELECT o.id, o.name, o.description,
                           UPPER(LEFT(o.name, 1)) || UPPER(LEFT(SPLIT_PART(o.name, ' ', 2), 1)) as initials,
                           o.created_at
                    FROM organizations o
                    WHERE o.is_gp = TRUE
                """
                params: list = []

                if q:
                    query += " AND o.name ILIKE %s"
                    params.append(f"%{q}%")

                query += " ORDER BY o.name LIMIT %s OFFSET %s"
                params.extend([per_page, (page - 1) * per_page])

                cur.execute(query, params)
                rows = cur.fetchall()
                for row in rows:
                    company = dict(row)
                    company["color"] = "navy"
                    company["type"] = "Private Equity"
                    company["admin_email"] = None
                    company["user_count"] = 0
                    company["fund_count"] = 0
                    company["status"] = "active"
                    company["created_at"] = company["created_at"].strftime("%b %d, %Y") if company.get("created_at") else "Unknown"
                    companies.append(company)

                cur.execute("SELECT COUNT(*) FROM organizations WHERE is_gp = TRUE")
                result = cur.fetchone()
                total_companies = result["count"] if result else 0

        except Exception as e:
            logger.warning(f"Failed to fetch companies from database: {e}")
            companies = mock_companies
            total_companies = len(mock_companies)
        finally:
            conn.close()
    else:
        companies = mock_companies
        total_companies = len(mock_companies)

        if q:
            companies = [c for c in companies if q.lower() in c["name"].lower()]
        if status:
            companies = [c for c in companies if c["status"] == status]
        total_companies = len(companies)

    total_pages = max(1, (total_companies + per_page - 1) // per_page)

    return templates.TemplateResponse(
        request,
        "pages/admin/companies.html",
        {
            "title": "Companies - LPxGP",
            "user": user,
            "companies": companies,
            "total_companies": total_companies,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "search_query": q,
            "filter_status": status,
        },
    )


@router.get("/admin/companies/{org_id}", response_class=HTMLResponse, response_model=None)
async def admin_company_detail_page(request: Request, org_id: str) -> HTMLResponse | RedirectResponse:
    """Company detail page."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not can_manage_data(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    mock_companies: dict[str, dict[str, Any]] = {
        "org-001": {
            "id": "org-001", "name": "Acme Capital", "initials": "AC", "color": "navy",
            "type": "Private Equity - Growth", "location": "San Francisco, CA",
            "website": "acmecapital.com", "status": "active", "created_at": "December 1, 2024",
            "user_count": 4, "fund_count": 3, "match_count": 127,
            "last_login": "2 hours ago", "searches_30d": 127, "pitches_30d": 23,
            "users": [
                {"name": "John Partner", "email": "john@acmecapital.com", "initials": "JP", "color": "navy", "role": "admin", "status": "Active"},
                {"name": "Sarah Johnson", "email": "sarah@acmecapital.com", "initials": "SJ", "color": "green", "role": "member", "status": "Active"},
            ],
            "funds": [
                {"name": "Growth Fund III", "target": 500, "status": "Raising", "matches": 45},
                {"name": "Growth Fund II", "target": 350, "status": "Investing", "matches": 52},
            ],
        },
        "org-002": {
            "id": "org-002", "name": "Beta Ventures", "initials": "BV", "color": "green",
            "type": "Venture Capital", "location": None, "website": None,
            "status": "pending", "created_at": "December 18, 2024",
            "user_count": 0, "fund_count": 0, "match_count": 0,
            "last_login": "Never", "searches_30d": 0, "pitches_30d": 0,
            "users": [], "funds": [],
        },
    }

    company: dict[str, Any] | None = None
    conn = get_db()
    if conn:
        try:
            from uuid import UUID
            UUID(org_id)

            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT o.id, o.name, o.description, o.website,
                           CONCAT(o.hq_city, ', ', o.hq_country) as location,
                           o.created_at
                    FROM organizations o
                    WHERE o.id = %s AND o.is_gp = TRUE
                    """,
                    [org_id],
                )
                row = cur.fetchone()
                if row:
                    company = dict(row)
                    company["initials"] = company["name"][:2].upper() if company["name"] else "??"
                    company["color"] = "navy"
                    company["type"] = "Private Equity"
                    company["status"] = "active"
                    company["created_at"] = company["created_at"].strftime("%B %d, %Y") if company.get("created_at") else "Unknown"
                    company["user_count"] = 0
                    company["fund_count"] = 0
                    company["match_count"] = 0
                    company["last_login"] = "Unknown"
                    company["searches_30d"] = 0
                    company["pitches_30d"] = 0
                    company["users"] = []
                    company["funds"] = []
        except ValueError:
            company = mock_companies.get(org_id)
        except Exception as e:
            logger.warning(f"Failed to fetch company from database: {e}")
            company = mock_companies.get(org_id)
        finally:
            conn.close()
    else:
        company = mock_companies.get(org_id)

    if not company:
        return RedirectResponse(url="/admin/companies", status_code=303)

    return templates.TemplateResponse(
        request,
        "pages/admin/company-detail.html",
        {
            "title": f"{company['name']} - LPxGP",
            "user": user,
            "company": company,
        },
    )


@router.delete("/admin/companies/{org_id}", response_model=None)
async def admin_company_deactivate(request: Request, org_id: str) -> JSONResponse:
    """Deactivate a company."""
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(content={"error": "Not authenticated"}, status_code=401)

    if not can_manage_data(user):
        return JSONResponse(content={"error": "Insufficient permissions"}, status_code=403)

    logger.info(f"Would deactivate company {org_id}")
    return JSONResponse(content={"success": True})


# =============================================================================
# Funds Management (Admin)
# =============================================================================


@router.get("/admin/funds", response_class=HTMLResponse, response_model=None)
async def admin_funds_page(
    request: Request,
    page: int = 1,
    q: str | None = None,
    strategy: str | None = None,
    status: str | None = None,
) -> HTMLResponse | RedirectResponse:
    """Funds management page for admin."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not can_manage_data(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    per_page = 25
    funds: list[dict[str, Any]] = []
    stats = {"total": 0, "active": 0, "fundraising": 0, "total_aum_bn": 0}

    mock_funds: list[dict[str, Any]] = [
        {"id": "fund-001", "name": "Growth Fund III", "org_id": "org-001", "org_name": "Acme Capital", "strategy": "growth_equity", "target_size_mm": 500, "vintage": 2024, "status": "fundraising", "description": "Mid-market growth equity fund"},
        {"id": "fund-002", "name": "Buyout Fund IV", "org_id": "org-001", "org_name": "Acme Capital", "strategy": "buyout", "target_size_mm": 1200, "vintage": 2023, "status": "active", "description": "Large-cap buyout fund"},
        {"id": "fund-003", "name": "Venture Fund II", "org_id": "org-004", "org_name": "Delta Capital", "strategy": "venture_capital", "target_size_mm": 250, "vintage": 2024, "status": "fundraising", "description": "Early-stage tech venture fund"},
        {"id": "fund-004", "name": "Real Estate Fund I", "org_id": "org-003", "org_name": "Gamma Partners", "strategy": "real_estate", "target_size_mm": 800, "vintage": 2022, "status": "closed", "description": "Commercial real estate fund"},
        {"id": "fund-005", "name": "Infrastructure Fund II", "org_id": "org-004", "org_name": "Delta Capital", "strategy": "infrastructure", "target_size_mm": 600, "vintage": 2023, "status": "active", "description": "Renewable infrastructure fund"},
    ]

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                where_clauses = []
                params: list[Any] = []

                if q:
                    where_clauses.append("(f.name ILIKE %s OR o.name ILIKE %s)")
                    params.extend([f"%{q}%", f"%{q}%"])

                if strategy:
                    where_clauses.append("f.strategy = %s")
                    params.append(strategy)

                if status:
                    where_clauses.append("f.status = %s")
                    params.append(status)

                where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

                cur.execute("SELECT COUNT(*) FROM funds")
                row = cur.fetchone()
                stats["total"] = row["count"] if row else 0

                cur.execute("SELECT COUNT(*) FROM funds WHERE status = 'active'")
                row = cur.fetchone()
                stats["active"] = row["count"] if row else 0

                cur.execute("SELECT COUNT(*) FROM funds WHERE status = 'fundraising'")
                row = cur.fetchone()
                stats["fundraising"] = row["count"] if row else 0

                cur.execute("SELECT COALESCE(SUM(target_size_mm), 0) / 1000.0 FROM funds")
                row = cur.fetchone()
                stats["total_aum_bn"] = round(row["?column?"] if row else 0, 1)

                count_sql = f"""
                    SELECT COUNT(*) as total
                    FROM funds f
                    LEFT JOIN organizations o ON o.id = f.org_id
                    {where_sql}
                """
                cur.execute(count_sql, params)
                row = cur.fetchone()
                total_funds = row["total"] if row else 0

                offset = (page - 1) * per_page
                query = f"""
                    SELECT f.id, f.name, f.description, f.strategy, f.target_size_mm,
                           f.vintage, f.status, f.org_id, o.name as org_name
                    FROM funds f
                    LEFT JOIN organizations o ON o.id = f.org_id
                    {where_sql}
                    ORDER BY f.name
                    LIMIT %s OFFSET %s
                """
                params.extend([per_page, offset])
                cur.execute(query, params)
                rows = cur.fetchall()
                funds = [dict(row) for row in rows]

        except Exception as e:
            logger.warning(f"Failed to fetch funds from database: {e}")
            funds = mock_funds
            stats = {"total": len(mock_funds), "active": 2, "fundraising": 2, "total_aum_bn": 3.4}
            total_funds = len(mock_funds)
        finally:
            conn.close()
    else:
        funds = mock_funds
        if q:
            funds = [f for f in funds if q.lower() in f["name"].lower() or q.lower() in (f.get("org_name") or "").lower()]
        if strategy:
            funds = [f for f in funds if f.get("strategy") == strategy]
        if status:
            funds = [f for f in funds if f.get("status") == status]
        total_funds = len(funds)
        stats = {"total": len(mock_funds), "active": 2, "fundraising": 2, "total_aum_bn": 3.4}

    total_pages = max(1, (total_funds + per_page - 1) // per_page)

    return templates.TemplateResponse(
        request,
        "pages/admin/funds.html",
        {
            "title": "Funds - Admin - LPxGP",
            "user": user,
            "funds": funds,
            "stats": stats,
            "page": page,
            "per_page": per_page,
            "total_pages": total_pages,
            "search_query": q,
            "filter_strategy": strategy,
            "filter_status": status,
        },
    )


# =============================================================================
# People Management
# =============================================================================


@router.get("/admin/people", response_class=HTMLResponse, response_model=None)
async def admin_people_page(
    request: Request,
    q: str | None = None,
    role: str | None = None,
    page: int = 1,
    per_page: int = 50,
) -> HTMLResponse | RedirectResponse:
    """Admin people management page."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not can_manage_data(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    people: list[dict[str, Any]] = []
    stats = {"total": 0, "decision_makers": 0, "with_email": 0, "with_linkedin": 0}
    pagination = {"page": page, "per_page": per_page, "total": 0, "total_pages": 1}

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                where_clauses = []
                params: list[Any] = []

                if q:
                    where_clauses.append("(p.full_name ILIKE %s OR p.email ILIKE %s)")
                    params.extend([f"%{q}%", f"%{q}%"])

                if role == "decision_maker":
                    where_clauses.append("cp.is_decision_maker = TRUE")

                where_sql = "WHERE " + " AND ".join(where_clauses) if where_clauses else ""

                cur.execute("SELECT COUNT(*) as total FROM people")
                row = cur.fetchone()
                stats["total"] = row["total"] if row else 0

                cur.execute("SELECT COUNT(*) FROM company_people WHERE is_decision_maker = TRUE")
                row = cur.fetchone()
                stats["decision_makers"] = row["count"] if row else 0

                cur.execute("SELECT COUNT(*) FROM people WHERE email IS NOT NULL AND email != ''")
                row = cur.fetchone()
                stats["with_email"] = row["count"] if row else 0

                cur.execute("SELECT COUNT(*) FROM people WHERE linkedin_url IS NOT NULL")
                row = cur.fetchone()
                stats["with_linkedin"] = row["count"] if row else 0

                count_sql = f"""
                    SELECT COUNT(DISTINCT p.id) as total
                    FROM people p
                    LEFT JOIN company_people cp ON cp.person_id = p.id
                    {where_sql}
                """
                cur.execute(count_sql, params)
                row = cur.fetchone()
                pagination["total"] = row["total"] if row else 0
                pagination["total_pages"] = max(1, (pagination["total"] + per_page - 1) // per_page)

                offset = (page - 1) * per_page
                query = f"""
                    SELECT DISTINCT
                        p.id, p.full_name, p.email, p.linkedin_url,
                        cp.title, cp.is_decision_maker,
                        o.name as company_name
                    FROM people p
                    LEFT JOIN company_people cp ON cp.person_id = p.id
                    LEFT JOIN organizations o ON o.id = cp.org_id
                    {where_sql}
                    ORDER BY p.full_name
                    LIMIT %s OFFSET %s
                """
                cur.execute(query, params + [per_page, offset])
                people = cur.fetchall()
        except Exception as e:
            logger.error(f"Admin people error: {e}")
        finally:
            conn.close()

    return templates.TemplateResponse(
        request,
        "pages/admin/people.html",
        {
            "user": user,
            "people": people,
            "stats": stats,
            "pagination": pagination,
            "search_query": q,
            "filter_role": role,
        },
    )


# =============================================================================
# Data Health Dashboard
# =============================================================================


@router.get("/admin/data-health", response_class=HTMLResponse, response_model=None)
async def admin_data_health_page(request: Request) -> HTMLResponse | RedirectResponse:
    """Data health dashboard showing data quality metrics."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not is_admin(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    # Mock health data
    health = {
        "overall_score": 78,
        "lps": {"score": 82, "total": 150, "with_aum": 85, "with_strategy": 78, "with_location": 92},
        "funds": {"score": 75, "total": 45, "with_size": 80, "with_strategy": 90, "with_vintage": 65},
        "people": {"score": 68, "total": 320, "with_email": 72, "with_title": 85, "with_company": 60},
        "issues": [
            {"title": "Missing AUM data", "description": "23 LPs are missing AUM information", "severity": "high", "count": 23, "url": "/admin/lps?filter=missing_aum"},
            {"title": "Incomplete fund profiles", "description": "12 funds lack vintage year", "severity": "medium", "count": 12, "url": "/admin/funds?filter=incomplete"},
            {"title": "Contacts without company", "description": "45 people are not linked to companies", "severity": "low", "count": 45, "url": "/admin/people?filter=no_company"},
        ],
    }

    return templates.TemplateResponse(
        request,
        "pages/admin/data-health.html",
        {
            "title": "Data Health - Admin - LPxGP",
            "user": user,
            "health": health,
        },
    )


# =============================================================================
# Activity Logs
# =============================================================================


@router.get("/admin/activity", response_class=HTMLResponse, response_model=None)
async def admin_activity_page(
    request: Request,
    page: int = 1,
    q: str | None = None,
    action: str | None = None,
    user_id: str | None = None,
) -> HTMLResponse | RedirectResponse:
    """Activity logs page showing user actions."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not is_admin(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    # Mock activity logs
    logs = [
        {"user_name": "Sarah Chen", "action": "create", "description": "created a new fund 'Growth Fund IV'", "details": "Target size: $500M", "timestamp": "2 minutes ago", "resource_url": "/funds/fund-001"},
        {"user_name": "Mike Johnson", "action": "update", "description": "updated LP profile 'CalPERS'", "details": "Updated AUM to $450B", "timestamp": "15 minutes ago", "resource_url": "/lps/lp-001"},
        {"user_name": "Admin User", "action": "login", "description": "logged in", "details": None, "timestamp": "1 hour ago", "resource_url": None},
        {"user_name": "Emily Davis", "action": "delete", "description": "removed contact 'John Doe'", "details": "From company: Acme Capital", "timestamp": "2 hours ago", "resource_url": None},
        {"user_name": "Sarah Chen", "action": "export", "description": "exported LP database", "details": "150 records", "timestamp": "3 hours ago", "resource_url": None},
    ]

    users = [
        {"id": "user-001", "name": "Sarah Chen"},
        {"id": "user-002", "name": "Mike Johnson"},
        {"id": "user-003", "name": "Emily Davis"},
        {"id": "user-004", "name": "Admin User"},
    ]

    return templates.TemplateResponse(
        request,
        "pages/admin/activity-logs.html",
        {
            "title": "Activity Logs - Admin - LPxGP",
            "user": user,
            "logs": logs,
            "users": users,
            "page": page,
            "total_pages": 3,
            "search_query": q,
            "filter_action": action,
            "filter_user": user_id,
        },
    )


# =============================================================================
# System Settings
# =============================================================================


@router.get("/admin/settings", response_class=HTMLResponse, response_model=None)
async def admin_settings_page(request: Request) -> HTMLResponse | RedirectResponse:
    """System settings page."""
    user = auth.get_current_user(request)
    if not user:
        return RedirectResponse(url="/login", status_code=303)

    if not is_admin(user):
        return RedirectResponse(url="/dashboard", status_code=303)

    # Mock settings
    settings_data = {
        "platform_name": "LPxGP",
        "support_email": "support@lpxgp.com",
        "maintenance_mode": False,
        "pagination_size": 25,
        "auto_dedupe": True,
        "validate_emails": True,
        "notify_new_users": True,
        "notify_data_issues": False,
    }

    return templates.TemplateResponse(
        request,
        "pages/admin/settings.html",
        {
            "title": "Settings - Admin - LPxGP",
            "user": user,
            "settings": settings_data,
        },
    )


# =============================================================================
# People Export
# =============================================================================


@router.get("/api/admin/export/people", response_model=None)
async def export_people_csv(request: Request) -> StreamingResponse | JSONResponse:
    """Export People to CSV file."""
    user = auth.get_current_user(request)
    if not user:
        return JSONResponse(status_code=401, content={"error": "Authentication required"})

    if not can_manage_data(user):
        return JSONResponse(status_code=403, content={"error": "Insufficient permissions"})

    people: list[dict[str, Any]] = []

    conn = get_db()
    if conn:
        try:
            with conn.cursor() as cur:
                cur.execute("""
                    SELECT p.id, p.full_name, p.email, p.linkedin_url,
                           cp.title, cp.is_decision_maker,
                           o.name as company_name
                    FROM people p
                    LEFT JOIN company_people cp ON cp.person_id = p.id
                    LEFT JOIN organizations o ON o.id = cp.org_id
                    ORDER BY p.full_name
                """)
                rows = cur.fetchall()
                people = [dict(row) for row in rows]
        except Exception as e:
            logger.warning(f"Failed to export people: {e}")
        finally:
            conn.close()

    if not people:
        people = [
            {"id": "person-001", "full_name": "John Smith", "email": "john@example.com", "title": "CIO", "company_name": "CalPERS", "is_decision_maker": True},
            {"id": "person-002", "full_name": "Jane Doe", "email": "jane@example.com", "title": "Portfolio Manager", "company_name": "Yale Endowment", "is_decision_maker": True},
        ]

    output = io.StringIO()
    if people:
        fieldnames = list(people[0].keys())
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(people)

    output.seek(0)
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"people_export_{timestamp}.csv"

    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={filename}"},
    )
