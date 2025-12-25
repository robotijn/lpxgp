"""LPxGP FastAPI Application.

AI-powered platform helping GPs find and engage LPs.
"""

from contextlib import asynccontextmanager
from pathlib import Path
from typing import Optional
from uuid import UUID
import httpx

import psycopg
from psycopg.rows import dict_row
from fastapi import FastAPI, Request, Query, Form
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates

from src.config import get_settings, validate_settings_on_startup
from src.logging_config import get_logger


def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID.

    Used to validate user input before database queries to prevent
    crashes and potential injection attacks.
    """
    if not value:
        return False
    try:
        UUID(value)
        return True
    except (ValueError, AttributeError):
        return False


def get_db() -> Optional[psycopg.Connection]:
    """Get database connection if configured.

    Returns a psycopg connection with dict_row factory for easy data access.
    Caller is responsible for closing the connection.
    """
    settings = get_settings()
    if settings.database_configured:
        return psycopg.connect(settings.database_url, row_factory=dict_row)
    return None

# -----------------------------------------------------------------------------
# Application Setup
# -----------------------------------------------------------------------------

logger = get_logger(__name__)

# Paths
BASE_DIR = Path(__file__).parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan handler."""
    # Startup
    logger.info("Starting LPxGP application")
    try:
        validate_settings_on_startup()
        logger.info("Configuration validated")
    except Exception as e:
        logger.error(f"Configuration validation failed: {e}")
        raise

    yield

    # Shutdown
    logger.info("Shutting down LPxGP application")


# Create FastAPI app
app = FastAPI(
    title="LPxGP",
    description="AI-powered platform helping GPs find and engage LPs",
    version="0.1.0",
    lifespan=lifespan,
)

# Mount static files
app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")

# Templates
templates = Jinja2Templates(directory=str(TEMPLATES_DIR))


# -----------------------------------------------------------------------------
# Health & Status Endpoints
# -----------------------------------------------------------------------------

@app.api_route("/health", methods=["GET", "HEAD"], response_class=JSONResponse)
async def health_check():
    """Health check endpoint for load balancers and monitoring.

    Supports both GET and HEAD methods for efficient health checking.
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
    }


@app.get("/api/status", response_class=JSONResponse)
async def api_status():
    """API status with configuration info (non-sensitive)."""
    settings = get_settings()
    return {
        "status": "ok",
        "environment": settings.environment,
        "features": {
            "semantic_search": settings.enable_semantic_search,
            "agent_matching": settings.enable_agent_matching,
        },
    }


# -----------------------------------------------------------------------------
# Page Routes
# -----------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Home page."""
    return templates.TemplateResponse(
        request,
        "pages/home.html",
        {"title": "LPxGP - GP-LP Intelligence Platform"},
    )


@app.get("/login", response_class=HTMLResponse)
async def login_page(request: Request):
    """Login page."""
    return templates.TemplateResponse(
        request,
        "pages/login.html",
        {"title": "Login - LPxGP"},
    )


@app.get("/matches", response_class=HTMLResponse)
async def matches_page(request: Request, fund_id: Optional[str] = Query(None)):
    """Matches page showing AI-recommended LP matches."""
    # Validate fund_id if provided - ignore invalid UUIDs to prevent crashes
    validated_fund_id = None
    if fund_id and is_valid_uuid(fund_id):
        validated_fund_id = fund_id

    # Default empty state
    empty_response = {
        "title": "Matches - LPxGP",
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
                    (validated_fund_id,)
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


@app.get("/funds", response_class=HTMLResponse)
async def funds_page(request: Request):
    """Funds page listing GP fund profiles."""
    empty_response = {
        "title": "Funds - LPxGP",
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


@app.get("/lps", response_class=HTMLResponse)
async def lps_page(
    request: Request,
    search: Optional[str] = Query(None),
    lp_type: Optional[str] = Query(None),
):
    """LPs page for browsing and searching LP profiles."""
    empty_response = {
        "title": "LPs - LPxGP",
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
            query = """
                SELECT
                    o.id, o.name, o.hq_city, o.hq_country, o.website,
                    lp.lp_type, lp.total_aum_bn, lp.pe_allocation_pct,
                    lp.check_size_min_mm, lp.check_size_max_mm,
                    lp.geographic_preferences, lp.strategies
                FROM organizations o
                JOIN lp_profiles lp ON lp.org_id = o.id
                WHERE 1=1
            """
            params = []

            if search:
                query += " AND (o.name ILIKE %s OR o.hq_city ILIKE %s)"
                params.extend([f"%{search}%", f"%{search}%"])

            if lp_type:
                query += " AND lp.lp_type = %s"
                params.append(lp_type)

            query += " ORDER BY lp.total_aum_bn DESC NULLS LAST LIMIT 100"

            cur.execute(query, params)
            lps = cur.fetchall()

        # Calculate stats
        total_aum = sum(lp["total_aum_bn"] or 0 for lp in lps)

        return templates.TemplateResponse(
            request,
            "pages/lps.html",
            {
                "title": "LPs - LPxGP",
                "lps": lps,
                "total_aum": total_aum,
                "search": search or "",
                "lp_type": lp_type or "",
                "lp_types": lp_types,
            },
        )
    finally:
        conn.close()


# -----------------------------------------------------------------------------
# API Endpoints (HTMX partials)
# -----------------------------------------------------------------------------

@app.get("/api/match/{match_id}/detail", response_class=HTMLResponse)
async def match_detail(request: Request, match_id: str):
    """Get match detail for modal display (HTMX partial)."""
    if not is_valid_uuid(match_id):
        return HTMLResponse(
            content="<p class='text-red-500'>Invalid match ID</p>",
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
            """, (match_id,))
            match = cur.fetchone()

        if not match:
            return HTMLResponse(
                content="<p class='text-navy-500'>Match not found</p>",
                status_code=404
            )

        return templates.TemplateResponse(
            request,
            "partials/match_detail_modal.html",
            {"match": match},
        )
    finally:
        conn.close()


@app.get("/api/lp/{lp_id}/detail", response_class=HTMLResponse)
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


@app.post("/api/funds", response_class=HTMLResponse)
async def create_fund(
    request: Request,
    name: str = Form(...),
    org_id: str = Form(...),
    status: str = Form(default="draft"),
    vintage_year: Optional[int] = Form(default=None),
    target_size_mm: Optional[float] = Form(default=None),
    strategy: Optional[str] = Form(default=None),
    sub_strategy: Optional[str] = Form(default=None),
    geographic_focus: Optional[str] = Form(default=""),
    sector_focus: Optional[str] = Form(default=""),
    check_size_min_mm: Optional[float] = Form(default=None),
    check_size_max_mm: Optional[float] = Form(default=None),
    investment_thesis: Optional[str] = Form(default=None),
    management_fee_pct: Optional[float] = Form(default=None),
    carried_interest_pct: Optional[float] = Form(default=None),
    gp_commitment_pct: Optional[float] = Form(default=None),
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
            fund_id = cur.fetchone()["id"]
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
            content=f"<p class='text-red-500'>Failed to create fund: {str(e)}</p>",
            status_code=500
        )
    finally:
        conn.close()


@app.get("/api/organizations/gp", response_class=JSONResponse)
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


@app.get("/api/funds/{fund_id}/edit", response_class=HTMLResponse)
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


@app.put("/api/funds/{fund_id}", response_class=HTMLResponse)
async def update_fund(
    request: Request,
    fund_id: str,
    name: str = Form(...),
    org_id: str = Form(...),
    status: str = Form(default="draft"),
    vintage_year: Optional[int] = Form(default=None),
    target_size_mm: Optional[float] = Form(default=None),
    strategy: Optional[str] = Form(default=None),
    sub_strategy: Optional[str] = Form(default=None),
    geographic_focus: Optional[str] = Form(default=""),
    sector_focus: Optional[str] = Form(default=""),
    check_size_min_mm: Optional[float] = Form(default=None),
    check_size_max_mm: Optional[float] = Form(default=None),
    investment_thesis: Optional[str] = Form(default=None),
    management_fee_pct: Optional[float] = Form(default=None),
    carried_interest_pct: Optional[float] = Form(default=None),
    gp_commitment_pct: Optional[float] = Form(default=None),
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
            content=f"<p class='text-red-500'>Failed to update fund: {str(e)}</p>",
            status_code=500
        )
    finally:
        conn.close()


@app.post("/api/match/{match_id}/generate-pitch", response_class=HTMLResponse)
async def generate_pitch(
    request: Request,
    match_id: str,
    pitch_type: str = Form(default="email"),
    tone: str = Form(default="professional"),
):
    """Generate an AI pitch for a match (HTMX partial)."""
    if not is_valid_uuid(match_id):
        return HTMLResponse(
            content="<p class='text-red-500'>Invalid match ID</p>",
            status_code=400
        )

    conn = get_db()
    if not conn:
        return HTMLResponse(
            content="<p class='text-navy-500'>Database not configured</p>",
            status_code=503
        )

    try:
        # Fetch match data for pitch generation
        with conn.cursor() as cur:
            cur.execute("""
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
            """, (match_id,))
            match = cur.fetchone()

        if not match:
            return HTMLResponse(
                content="<p class='text-navy-500'>Match not found</p>",
                status_code=404
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
                    }
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
• Target fund size: ${match['target_size_mm']}M
• {talking_points[0] if talking_points else 'Strong alignment with LP mandate'}
• {talking_points[1] if len(talking_points) > 1 else 'Experienced management team'}

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


# -----------------------------------------------------------------------------
# Error Handlers
# -----------------------------------------------------------------------------

@app.exception_handler(404)
async def not_found_handler(request: Request, exc):
    """Custom 404 handler."""
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=404,
            content={"error": "Not found", "path": request.url.path},
        )
    return templates.TemplateResponse(
        request,
        "pages/error.html",
        {"title": "Not Found", "error_code": 404, "error_message": "Page not found"},
        status_code=404,
    )


@app.exception_handler(500)
async def server_error_handler(request: Request, exc):
    """Custom 500 handler."""
    logger.error(f"Server error: {exc}", exc_info=True)
    if request.url.path.startswith("/api/"):
        return JSONResponse(
            status_code=500,
            content={"error": "Internal server error"},
        )
    return templates.TemplateResponse(
        request,
        "pages/error.html",
        {"title": "Error", "error_code": 500, "error_message": "Something went wrong"},
        status_code=500,
    )
