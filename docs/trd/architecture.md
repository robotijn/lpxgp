# System Architecture

[Back to TRD Index](index.md)

---

## Overview

This document describes the core system architecture for LPxGP, including the two-database model, API layer design, authentication, and multi-tenancy approach.

---

## Two-Database Model

LPxGP uses a logical separation between **Market Data** and **Client Data** within a single Supabase instance.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         SUPABASE (Single Instance)                          │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────┐  ┌───────────────────────────────────┐
│  │         MARKET DATABASE           │  │         CLIENT DATABASE           │
│  │         (Shared Schema)           │  │         (Tenant Schema)           │
│  ├───────────────────────────────────┤  ├───────────────────────────────────┤
│  │                                   │  │                                   │
│  │  Organizations (GP/LP firms)      │  │  Companies (GP tenants)           │
│  │  People (Contacts)                │  │  Users (Team members)             │
│  │  Funds (Historical)               │  │  Funds (Active, tenant-owned)     │
│  │  LP Profiles (Market data)        │  │  Matches (Per-tenant results)     │
│  │  GP Profiles (Market data)        │  │  Pitches (Generated content)      │
│  │  Investments (Historical)         │  │  Touchpoints (Interactions)       │
│  │  Events (Industry events)         │  │  Tasks (Follow-ups)               │
│  │  Employment (Career history)      │  │  Notes (Internal notes)           │
│  │                                   │  │  Invitations (User onboarding)    │
│  │  Source: External data feeds      │  │                                   │
│  │  Access: Read-only for clients    │  │  Source: Client input             │
│  │                                   │  │  Access: RLS per company          │
│  │                                   │  │                                   │
│  └───────────────────────────────────┘  └───────────────────────────────────┘
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────────┐
│  │                         SHARED INFRASTRUCTURE                             │
│  ├───────────────────────────────────────────────────────────────────────────┤
│  │  pgvector (Embeddings)  │  Supabase Auth  │  Supabase Storage (Decks)    │
│  └───────────────────────────────────────────────────────────────────────────┘
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Rationale

| Approach | Pros | Cons |
|----------|------|------|
| **Single DB, logical separation** | Simpler ops, easier joins | Careful RLS design needed |
| Separate DB instances | Strong isolation | Complex ops, no cross-DB joins |
| Schema-per-tenant | Moderate isolation | Migration complexity |

**Decision:** Logical separation with RLS. Single Supabase instance keeps operations simple while RLS provides security.

---

## Database Schema

### Market Data Tables

```sql
-- Core organization entity (GP or LP)
CREATE TABLE organizations (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    legal_name TEXT,
    short_name TEXT,
    website TEXT,
    linkedin_url TEXT,
    logo_url TEXT,
    description TEXT,
    hq_city TEXT,
    hq_country TEXT,
    hq_timezone TEXT,
    founded_year INTEGER,
    employee_count INTEGER,
    is_gp BOOLEAN DEFAULT FALSE,
    is_lp BOOLEAN DEFAULT FALSE,
    is_active BOOLEAN DEFAULT TRUE,
    tier TEXT CHECK (tier IN ('tier1', 'tier2', 'tier3', 'untiered')),
    tags TEXT[],
    data_quality_score DECIMAL(3,2),
    last_verified TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- GP-specific profile data
CREATE TABLE gp_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    firm_type TEXT CHECK (firm_type IN (
        'buyout', 'growth', 'venture', 'real_estate',
        'infrastructure', 'credit', 'secondaries',
        'fund_of_funds', 'multi_strategy'
    )),
    primary_strategy TEXT,
    secondary_strategies TEXT[],
    geographic_focus TEXT[],
    sector_focus TEXT[],
    investment_thesis TEXT,
    thesis_embedding VECTOR(1024),
    total_aum_bn DECIMAL(10,2),
    funds_raised INTEGER,
    currently_raising BOOLEAN DEFAULT FALSE,
    current_fund_target_mm DECIMAL(10,2),
    UNIQUE(org_id)
);

-- LP-specific profile data
CREATE TABLE lp_profiles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    lp_type TEXT CHECK (lp_type IN (
        'public_pension', 'corporate_pension', 'endowment',
        'foundation', 'family_office', 'sovereign_wealth',
        'insurance', 'fund_of_funds', 'bank', 'ria', 'other'
    )),
    total_aum_bn DECIMAL(10,2),
    pe_allocation_pct DECIMAL(5,2),
    strategies TEXT[],
    geographic_preferences TEXT[],
    check_size_min_mm DECIMAL(10,2),
    check_size_max_mm DECIMAL(10,2),
    fund_size_min_mm DECIMAL(10,2),
    fund_size_max_mm DECIMAL(10,2),
    min_track_record_years INTEGER,
    esg_required BOOLEAN DEFAULT FALSE,
    emerging_manager_program BOOLEAN DEFAULT FALSE,
    mandate_description TEXT,
    mandate_embedding VECTOR(1024),
    actively_looking BOOLEAN DEFAULT FALSE,
    UNIQUE(org_id)
);

-- People (contacts at organizations)
CREATE TABLE people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    first_name TEXT,
    last_name TEXT,
    preferred_name TEXT,
    email TEXT,
    phone TEXT,
    linkedin_url TEXT,
    photo_url TEXT,
    current_title TEXT,
    current_org_id UUID REFERENCES organizations(id),
    seniority_level TEXT CHECK (seniority_level IN (
        'c_suite', 'partner', 'director', 'vp', 'manager', 'analyst', 'other'
    )),
    is_decision_maker BOOLEAN DEFAULT FALSE,
    bio TEXT,
    location_city TEXT,
    timezone TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Funds (historical and active)
CREATE TABLE funds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID REFERENCES organizations(id) ON DELETE CASCADE,
    name TEXT NOT NULL,
    fund_number INTEGER,
    status TEXT CHECK (status IN (
        'pre_marketing', 'raising', 'first_close',
        'final_close', 'closed', 'investing', 'harvesting'
    )),
    vintage_year INTEGER,
    target_size_mm DECIMAL(10,2),
    current_size_mm DECIMAL(10,2),
    strategy TEXT,
    geographic_focus TEXT[],
    sector_focus TEXT[],
    investment_thesis TEXT,
    thesis_embedding VECTOR(1024),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- LP Investments (commitments)
CREATE TABLE investments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lp_org_id UUID REFERENCES organizations(id),
    fund_id UUID REFERENCES funds(id),
    commitment_mm DECIMAL(10,2),
    commitment_date DATE,
    source TEXT,
    confidence TEXT CHECK (confidence IN ('confirmed', 'likely', 'rumored')),
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

### Client Data Tables

```sql
-- GP companies (tenants)
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    org_id UUID REFERENCES organizations(id),  -- Link to market data
    subscription_tier TEXT DEFAULT 'basic',
    settings JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Users (team members)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    auth_id UUID UNIQUE NOT NULL,  -- Supabase auth.users.id
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    email TEXT NOT NULL,
    full_name TEXT,
    role TEXT CHECK (role IN ('admin', 'user', 'viewer')) DEFAULT 'user',
    is_active BOOLEAN DEFAULT TRUE,
    last_login TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Matches (per-tenant, cached debate results)
CREATE TABLE matches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    fund_id UUID REFERENCES funds(id),
    lp_org_id UUID REFERENCES organizations(id),
    score DECIMAL(5,2),
    confidence DECIMAL(3,2),
    recommendation TEXT CHECK (recommendation IN (
        'strong_pursue', 'pursue', 'investigate', 'cautious', 'avoid'
    )),
    talking_points TEXT[],
    concerns TEXT[],
    debate_id UUID,  -- Reference to agent debate
    status TEXT DEFAULT 'active',
    user_feedback TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    expires_at TIMESTAMPTZ
);

-- Pitches (generated content)
CREATE TABLE pitches (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    match_id UUID REFERENCES matches(id),
    pitch_type TEXT CHECK (pitch_type IN (
        'email_intro', 'executive_summary', 'meeting_prep', 'follow_up'
    )),
    content JSONB NOT NULL,
    quality_score DECIMAL(5,2),
    status TEXT DEFAULT 'draft',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Touchpoints (interactions)
CREATE TABLE touchpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    person_id UUID REFERENCES people(id),
    org_id UUID REFERENCES organizations(id),
    touchpoint_type TEXT CHECK (touchpoint_type IN (
        'meeting', 'call', 'email', 'event_interaction',
        'linkedin_message', 'coffee', 'dinner', 'other'
    )),
    direction TEXT CHECK (direction IN ('outbound', 'inbound', 'mutual')),
    occurred_at TIMESTAMPTZ NOT NULL,
    summary TEXT,
    key_takeaways TEXT[],
    follow_up_required BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES users(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tasks (follow-ups)
CREATE TABLE tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID REFERENCES companies(id) ON DELETE CASCADE,
    assigned_to UUID REFERENCES users(id),
    person_id UUID REFERENCES people(id),
    org_id UUID REFERENCES organizations(id),
    title TEXT NOT NULL,
    description TEXT,
    due_date DATE,
    priority TEXT CHECK (priority IN ('urgent', 'high', 'normal', 'low')),
    status TEXT CHECK (status IN (
        'pending', 'in_progress', 'completed', 'cancelled'
    )) DEFAULT 'pending',
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

---

## API Layer Design

### API Structure

```
/api/v1/
├── /auth
│   ├── POST   /login              # Login with email/password
│   ├── POST   /logout             # Logout (invalidate session)
│   ├── POST   /refresh            # Refresh JWT token
│   ├── GET    /invite/{token}     # Validate invitation token
│   └── POST   /invite/{token}/accept  # Accept invite, set password
│
├── /users
│   ├── GET    /me                 # Get current user profile
│   ├── PATCH  /me                 # Update current user profile
│   ├── GET    /                   # List company users (admin)
│   └── PATCH  /{id}               # Update user role (admin)
│
├── /funds
│   ├── GET    /                   # List company's active funds
│   ├── POST   /                   # Create fund
│   ├── GET    /{id}               # Get fund details
│   ├── PATCH  /{id}               # Update fund
│   ├── POST   /{id}/upload-deck   # Upload pitch deck
│   └── POST   /{id}/extract       # Extract profile from deck (AI)
│
├── /lps
│   ├── GET    /                   # List LPs (with filters)
│   ├── GET    /{id}               # Get LP details
│   ├── POST   /search             # Advanced search
│   └── POST   /semantic-search    # Natural language search
│
├── /matches
│   ├── POST   /generate           # Generate matches for fund
│   ├── GET    /                   # List matches for fund
│   ├── GET    /{id}               # Get match details
│   ├── PATCH  /{id}               # Update match (feedback)
│   └── POST   /{id}/explain       # Regenerate explanation
│
├── /pitches
│   ├── POST   /                   # Generate pitch for match
│   ├── GET    /{id}               # Get pitch content
│   └── PATCH  /{id}               # Update pitch status
│
├── /touchpoints
│   ├── GET    /                   # List touchpoints (filtered)
│   ├── POST   /                   # Create touchpoint
│   └── PATCH  /{id}               # Update touchpoint
│
├── /tasks
│   ├── GET    /                   # List tasks
│   ├── POST   /                   # Create task
│   ├── PATCH  /{id}               # Update task
│   └── DELETE /{id}               # Delete task
│
└── /admin (super admin only)
    ├── GET    /companies          # List all companies
    ├── GET    /stats              # Platform statistics
    ├── GET    /import-jobs        # List import jobs
    └── POST   /enrichment/run     # Trigger enrichment batch
```

### Request/Response Patterns

```python
# Example: Match generation endpoint
from pydantic import BaseModel
from typing import Optional

class GenerateMatchesRequest(BaseModel):
    fund_id: str
    limit: Optional[int] = 50
    min_score: Optional[float] = 60.0
    strategies: Optional[list[str]] = None
    geographies: Optional[list[str]] = None

class MatchResponse(BaseModel):
    id: str
    lp_name: str
    lp_type: str
    score: float
    confidence: float
    recommendation: str
    talking_points: list[str]
    concerns: list[str]
    created_at: str

class GenerateMatchesResponse(BaseModel):
    matches: list[MatchResponse]
    total: int
    job_id: str  # For async processing
```

---

## Authentication Architecture

### Authentication Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         AUTHENTICATION FLOW                                  │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. INVITATION FLOW (No public registration)                                │
│                                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │ Admin creates│────▶│ Email sent   │────▶│ User clicks  │                │
│  │ invitation   │     │ with token   │     │ link         │                │
│  └──────────────┘     └──────────────┘     └──────┬───────┘                │
│                                                    │                         │
│                                                    ▼                         │
│                                           ┌──────────────┐                  │
│                                           │ Set password │                  │
│                                           │ Accept invite│                  │
│                                           └──────┬───────┘                  │
│                                                  │                          │
│                                                  ▼                          │
│                                           ┌──────────────┐                  │
│                                           │ User created │                  │
│                                           │ in Supabase  │                  │
│                                           └──────────────┘                  │
│                                                                              │
│  2. LOGIN FLOW                                                               │
│                                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │ User submits │────▶│ FastAPI      │────▶│ Supabase     │                │
│  │ credentials  │     │ validates    │     │ Auth         │                │
│  └──────────────┘     └──────┬───────┘     └──────┬───────┘                │
│                              │                     │                         │
│                              │◀────────────────────│ JWT Token              │
│                              │                                               │
│                              ▼                                               │
│                       ┌──────────────┐                                      │
│                       │ Set HTTP-only│                                      │
│                       │ cookie       │                                      │
│                       └──────────────┘                                      │
│                                                                              │
│  3. AUTHENTICATED REQUESTS                                                   │
│                                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │ Request with │────▶│ Verify JWT   │────▶│ Extract      │                │
│  │ cookie       │     │ signature    │     │ user_id,     │                │
│  └──────────────┘     └──────────────┘     │ company_id   │                │
│                                             └──────┬───────┘                │
│                                                    │                         │
│                                                    ▼                         │
│                                             ┌──────────────┐                │
│                                             │ RLS enforces │                │
│                                             │ data access  │                │
│                                             └──────────────┘                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### JWT Claims Structure

```python
# JWT token payload
{
    "sub": "user-uuid",           # User ID
    "email": "user@company.com",
    "role": "user",               # user, admin, super_admin
    "company_id": "company-uuid", # Tenant ID
    "company_name": "Acme Capital",
    "iat": 1704067200,            # Issued at
    "exp": 1704153600             # Expires (24h)
}
```

### FastAPI Middleware

```python
from fastapi import Request, HTTPException
from supabase import create_client

async def auth_middleware(request: Request, call_next):
    # Skip auth for public routes
    if request.url.path in PUBLIC_ROUTES:
        return await call_next(request)

    # Get token from cookie
    token = request.cookies.get("access_token")
    if not token:
        raise HTTPException(status_code=401, detail="Not authenticated")

    # Verify with Supabase
    try:
        user = supabase.auth.get_user(token)
        request.state.user = user
        request.state.company_id = user.user_metadata.get("company_id")
    except Exception:
        raise HTTPException(status_code=401, detail="Invalid token")

    return await call_next(request)
```

---

## Multi-Tenancy with Row-Level Security

### RLS Philosophy

LPxGP uses a **restrictive RLS model** - by default, users see only their own organization's data. Cross-org visibility is explicitly granted to privileged roles only.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         ROLE HIERARCHY                                       │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  SUPER ADMIN ──────────────────────────────────────────────────────────────▶│ Full access
│       │                                                                      │
│       ▼                                                                      │
│  FUND ADMIN (FA) ──────────────────────────────────────────────────────────▶│ Cross-org read, privileged ops
│       │                                                                      │
│       ▼                                                                      │
│  ADMIN ────────────────────────────────────────────────────────────────────▶│ Own org admin + user mgmt
│       │                                                                      │
│       ▼                                                                      │
│  MEMBER ───────────────────────────────────────────────────────────────────▶│ Own org read/write
│       │                                                                      │
│       ▼                                                                      │
│  VIEWER ───────────────────────────────────────────────────────────────────▶│ Own org read-only
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

| Data Type | Viewer | Member | Admin | FA | Super |
|-----------|--------|--------|-------|----|-------|
| LP profiles (market) | Read | Read | Read | Full | Full |
| Own org data | Read | R/W | Full | Full | Full |
| Other org data | - | - | - | Read | Full |
| Audit logs | - | - | - | Read | Full |
| System config | - | - | - | - | Full |

### Key Design Decisions

1. **Single Employment**: Users can only belong to one organization at a time (`is_current=TRUE` enforced by trigger)
2. **Org-Scoped Access**: Helper function `current_user_org_id()` returns user's current org, used in all RLS policies
3. **Privileged Bypass**: `is_privileged_user()` returns TRUE for FA/Super Admin roles for cross-org operations
4. **Audit Logging**: `audit_logs` table tracks access to sensitive data (LP profiles, matches)

### RLS Policy Design

```sql
-- Helper functions for RLS policies
CREATE FUNCTION current_user_org_id() RETURNS UUID AS $$
    SELECT e.org_id FROM employment e
    WHERE e.person_id = auth.uid()
    AND e.is_current = TRUE
    ORDER BY e.started_at DESC
    LIMIT 1;
$$ LANGUAGE SQL SECURITY DEFINER STABLE;

CREATE FUNCTION is_privileged_user() RETURNS BOOLEAN AS $$
    SELECT get_user_org_role() IN ('fund_admin', 'super_admin');
$$ LANGUAGE SQL SECURITY DEFINER STABLE;

-- Enable RLS on tenant tables
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE pitches ENABLE ROW LEVEL SECURITY;
ALTER TABLE touchpoints ENABLE ROW LEVEL SECURITY;
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

-- Standard pattern: org-scoped access with privileged bypass
CREATE POLICY "matches_org_scoped" ON matches FOR ALL
USING (
    org_id = current_user_org_id()
    OR is_privileged_user()
);

-- Similar policies for all tenant tables...
```

### Service Role Access

```python
# For background jobs that need cross-tenant access
from supabase import create_client

# Service role bypasses RLS
service_supabase = create_client(
    SUPABASE_URL,
    SUPABASE_SERVICE_ROLE_KEY  # Service key, not anon key
)

# Use for:
# - Batch processing jobs
# - Admin operations
# - Data imports
```

---

## API Versioning Strategy

```python
# Router versioning
from fastapi import APIRouter

# Current version
v1_router = APIRouter(prefix="/api/v1")

# Future version (when breaking changes needed)
v2_router = APIRouter(prefix="/api/v2")

# Deprecation headers
@v1_router.get("/matches")
async def list_matches():
    response.headers["Deprecation"] = "true"
    response.headers["Sunset"] = "2025-06-01"
    response.headers["Link"] = "</api/v2/matches>; rel=successor"
    return matches
```

---

## Error Handling

```python
from fastapi import HTTPException
from pydantic import BaseModel

class ErrorResponse(BaseModel):
    error: str
    code: str
    details: dict | None = None

# Standard error codes
class ErrorCodes:
    NOT_FOUND = "NOT_FOUND"
    UNAUTHORIZED = "UNAUTHORIZED"
    FORBIDDEN = "FORBIDDEN"
    VALIDATION_ERROR = "VALIDATION_ERROR"
    RATE_LIMITED = "RATE_LIMITED"
    INTERNAL_ERROR = "INTERNAL_ERROR"

# Error handler
@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return JSONResponse(
        status_code=exc.status_code,
        content=ErrorResponse(
            error=exc.detail,
            code=map_status_to_code(exc.status_code),
        ).dict()
    )
```

---

## Rate Limiting

```python
from slowapi import Limiter
from slowapi.util import get_remote_address

limiter = Limiter(key_func=get_remote_address)

# Global rate limits
@app.get("/api/v1/lps")
@limiter.limit("100/minute")
async def list_lps():
    ...

# AI endpoints have stricter limits
@app.post("/api/v1/matches/generate")
@limiter.limit("10/minute")
async def generate_matches():
    ...

# Per-tenant limits (stored in Redis/Supabase)
@app.post("/api/v1/pitches")
@limiter.limit("50/hour", key_func=lambda r: r.state.company_id)
async def generate_pitch():
    ...
```

---

## Impersonation Architecture

Fund Admins and Super Admins can impersonate other users for support and debugging purposes.

### Impersonation Flow

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         IMPERSONATION FLOW                                   │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  1. START IMPERSONATION                                                      │
│                                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │ FA/SA clicks │────▶│ Validate     │────▶│ Create       │                │
│  │ "Impersonate"│     │ permissions  │     │ session log  │                │
│  └──────────────┘     └──────┬───────┘     └──────┬───────┘                │
│                              │                     │                         │
│                    ┌─────────┴─────────┐          │                         │
│                    │ FA: target is GP/LP│          │                         │
│                    │ SA: any non-SA user│          │                         │
│                    └───────────────────┘          │                         │
│                                                   ▼                         │
│                                           ┌──────────────┐                  │
│                                           │ Set session  │                  │
│                                           │ cookies:     │                  │
│                                           │ - admin_id   │                  │
│                                           │ - target_id  │                  │
│                                           │ - read_only  │                  │
│                                           └──────────────┘                  │
│                                                                              │
│  2. DURING IMPERSONATION                                                     │
│                                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │ Request with │────▶│ Check        │────▶│ Apply        │                │
│  │ impersonation│     │ read_only    │     │ target's RLS │                │
│  │ cookies      │     │ flag         │     │ context      │                │
│  └──────────────┘     └──────┬───────┘     └──────────────┘                │
│                              │                                               │
│                    ┌─────────┴─────────┐                                    │
│                    │ FA: always block  │                                    │
│                    │     write ops     │                                    │
│                    │ SA: check flag    │                                    │
│                    └───────────────────┘                                    │
│                                                                              │
│  3. END IMPERSONATION                                                        │
│                                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────┐                │
│  │ Click "End   │────▶│ Log session  │────▶│ Clear        │                │
│  │ Session"     │     │ end time     │     │ cookies      │                │
│  └──────────────┘     └──────────────┘     └──────────────┘                │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Impersonation Session State

```python
# Impersonation context stored in session
{
    "admin_user_id": "admin-uuid",     # Who is impersonating
    "target_user_id": "target-uuid",   # Who is being viewed as
    "started_at": "2025-01-15T10:00:00Z",
    "read_only": True,                  # FA always True, SA configurable
    "reason": "Support ticket #12345"   # Optional
}
```

### Middleware Implementation

```python
async def impersonation_middleware(request: Request, call_next):
    # Check for impersonation cookies
    admin_id = request.cookies.get("impersonate_admin_id")
    target_id = request.cookies.get("impersonate_target_id")

    if admin_id and target_id:
        # Validate admin still has permission
        admin = get_user(admin_id)
        if not admin.role in ("fund_admin", "super_admin"):
            clear_impersonation_cookies(response)
            raise HTTPException(403, "Impersonation session invalid")

        # Set context for RLS
        request.state.effective_user_id = target_id
        request.state.actual_user_id = admin_id
        request.state.is_impersonating = True
        request.state.read_only = request.cookies.get("impersonate_read_only") == "true"

        # Block writes for FA or read-only mode
        if request.method in ("POST", "PUT", "PATCH", "DELETE"):
            if admin.role == "fund_admin" or request.state.read_only:
                raise HTTPException(403, "Write operations not permitted during impersonation")

    return await call_next(request)
```

---

## Billing Integration

LPxGP integrates with Stripe for subscription management and payment processing.

### Billing Architecture

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BILLING ARCHITECTURE                                 │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                          LPxGP Application                            │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │ FA Billing  │  │ GP Billing  │  │ LP Billing  │  │ Webhook     │  │  │
│  │  │ (all orgs)  │  │ (self-serv) │  │ (self-serv) │  │ Handler     │  │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  │  │
│  │         │                │                │                │         │  │
│  │         └────────────────┴────────────────┴────────────────┘         │  │
│  │                                  │                                    │  │
│  └──────────────────────────────────┼────────────────────────────────────┘  │
│                                     │                                        │
│                                     ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         Supabase Database                             │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                   │  │
│  │  │subscriptions│  │ invoices    │  │ payment_    │                   │  │
│  │  │             │  │             │  │ methods     │                   │  │
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                   │  │
│  │         │                │                │                           │  │
│  └─────────┴────────────────┴────────────────┴───────────────────────────┘  │
│                                     │                                        │
│                                     ▼                                        │
│  ┌───────────────────────────────────────────────────────────────────────┐  │
│  │                         Stripe                                        │  │
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  │  │
│  │  │ Customers   │  │Subscriptions│  │ Invoices    │  │ Payment     │  │  │
│  │  │             │  │             │  │             │  │ Methods     │  │  │
│  │  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘  │  │
│  │                                                                       │  │
│  └───────────────────────────────────────────────────────────────────────┘  │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Subscription Plans

| Plan | Price | Features |
|------|-------|----------|
| Free | $0 | Limited LP search, no matches |
| Starter | $99/mo | 1 fund, 50 matches, basic pitch |
| Professional | $299/mo | 3 funds, unlimited matches, full pitch |
| Enterprise | $499/mo | Unlimited funds, priority support, API access |

### Webhook Events

```python
# Stripe webhook handler
@app.post("/webhooks/stripe")
async def stripe_webhook(request: Request):
    payload = await request.body()
    sig = request.headers.get("stripe-signature")

    event = stripe.Webhook.construct_event(payload, sig, WEBHOOK_SECRET)

    if event.type == "invoice.paid":
        # Update invoice status in DB
        await mark_invoice_paid(event.data.object.id)

    elif event.type == "invoice.payment_failed":
        # Mark subscription as past_due
        await mark_subscription_past_due(event.data.object.subscription)

    elif event.type == "customer.subscription.updated":
        # Sync subscription changes
        await sync_subscription(event.data.object)

    elif event.type == "customer.subscription.deleted":
        # Handle cancellation
        await handle_cancellation(event.data.object.id)

    return {"status": "ok"}
```

### Invoice PDF Generation

```python
# Generate invoice PDF for download
@app.get("/api/v1/invoices/{invoice_id}/pdf")
async def download_invoice_pdf(invoice_id: str, user: User = Depends(get_current_user)):
    # Verify user has access to this invoice
    invoice = await get_invoice(invoice_id)
    if invoice.org_id != user.org_id and not is_privileged_user(user):
        raise HTTPException(403, "Access denied")

    # Fetch from Stripe or return cached
    if invoice.pdf_url:
        return RedirectResponse(invoice.pdf_url)

    # Generate PDF from Stripe
    stripe_invoice = stripe.Invoice.retrieve(invoice.stripe_invoice_id)
    return RedirectResponse(stripe_invoice.invoice_pdf)
```

---

## FA API Endpoints

```
/api/v1/fa (Fund Admin only)
├── /dashboard
│   └── GET    /stats              # Platform overview stats
│
├── /gps
│   ├── GET    /                   # List all GP organizations
│   ├── POST   /                   # Create GP (onboard)
│   ├── GET    /{id}               # Get GP details
│   ├── PATCH  /{id}               # Update GP
│   └── DELETE /{id}               # Delete GP
│
├── /lps
│   ├── GET    /                   # List all LP organizations
│   ├── POST   /                   # Create LP (onboard)
│   ├── GET    /{id}               # Get LP details
│   ├── PATCH  /{id}               # Update LP
│   └── DELETE /{id}               # Delete LP
│
├── /people
│   ├── GET    /                   # List all people
│   ├── POST   /                   # Create person
│   ├── GET    /{id}               # Get person details
│   ├── PATCH  /{id}               # Update person
│   ├── DELETE /{id}               # Delete person
│   └── POST   /merge              # Merge duplicate people
│
├── /users
│   ├── GET    /                   # List all users
│   ├── POST   /                   # Create user directly
│   ├── GET    /{id}               # Get user details
│   ├── PATCH  /{id}               # Update user (role: viewer/member only)
│   └── POST   /{id}/deactivate    # Deactivate user
│
├── /billing
│   ├── GET    /                   # List all org subscriptions
│   ├── GET    /{org_id}           # Get org billing details
│   ├── PATCH  /{org_id}           # Update org plan
│   └── GET    /{org_id}/invoices  # List org invoices
│
├── /recommendations
│   ├── GET    /                   # List all recommendations
│   ├── POST   /                   # Add manual recommendation
│   ├── PATCH  /{id}               # Update recommendation
│   └── DELETE /{id}               # Remove recommendation
│
└── /impersonate
    ├── POST   /start              # Start impersonation session
    └── POST   /end                # End impersonation session
```

---

## Related Documents

- [Agents Architecture](agents.md) - Multi-agent debate system
- [Data Pipeline](data-pipeline.md) - Entity Resolution and import
- [Infrastructure](infrastructure.md) - Deployment and operations
