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

from pathlib import Path
from typing import Any

from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse
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
