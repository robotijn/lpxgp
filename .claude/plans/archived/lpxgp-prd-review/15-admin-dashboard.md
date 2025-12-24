## 15. Admin Dashboard Redesign & Two-Database Model

### Overview

Two issues to address:
1. **Admin dashboard restructure** - Better CRUD organization
2. **Two-database model clarification** - Market data vs Client data

---

### 15.1 Two-Database Model

#### The Distinction

| Aspect | Market Database | Client Database |
|--------|-----------------|-----------------|
| **Purpose** | Reference data, intelligence | Our paying customers |
| **Scale** | 100K+ LPs, 50K+ GPs | Hundreds of clients |
| **Data Quality** | Variable, scraped/enriched | High, curated, verified |
| **Updates** | Batch enrichment, external feeds | User-driven, real-time |
| **Users** | Read-only for matching | Active users of LPxGP |
| **Example** | "CalPERS is a pension with $450B AUM" | "CalPERS is our client since 2024, John is their admin" |

#### Conceptual Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     MARKET DATABASE                              │
│                   (Intelligence Layer)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  companies                     people                            │
│  ┌──────────────────────┐     ┌──────────────────────┐          │
│  │ 150,000 records      │     │ 500,000+ contacts    │          │
│  │ - GPs (50K)          │     │ - Names, emails      │          │
│  │ - LPs (100K)         │     │ - Titles, LinkedIn   │          │
│  │ - Type, AUM, etc.    │     │ - Historical roles   │          │
│  └──────────────────────┘     └──────────────────────┘          │
│                                                                  │
│  Sources: Pitchbook, Preqin, scraped data, enrichment APIs      │
│  Purpose: Matching, research, outreach targets                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
                              │
                              │ Link via company_id
                              ▼
┌─────────────────────────────────────────────────────────────────┐
│                     CLIENT DATABASE                              │
│                    (Application Layer)                           │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  clients                       users                             │
│  ┌──────────────────────┐     ┌──────────────────────┐          │
│  │ ~500 records         │     │ ~2,000 users         │          │
│  │ - GP clients (300)   │     │ - Email, password    │          │
│  │ - LP clients (200)   │     │ - Linked to client   │          │
│  │ - Subscription tier  │     │ - Permissions        │          │
│  │ - Billing info       │     │ - Preferences        │          │
│  └──────────────────────┘     └──────────────────────┘          │
│                                                                  │
│  Sources: User signup, sales onboarding                         │
│  Purpose: Auth, billing, user-specific features                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Data Model Clarification

```sql
-- ===============================
-- MARKET DATABASE (Intelligence)
-- ===============================

-- All known companies (GPs and LPs in the market)
CREATE TABLE companies (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    type TEXT NOT NULL CHECK (type IN ('gp', 'lp', 'both')),

    -- Common fields
    website TEXT,
    headquarters_city TEXT,
    headquarters_country TEXT,
    founded_year INTEGER,
    description TEXT,

    -- LP-specific (NULL for pure GPs)
    lp_type TEXT,  -- 'pension', 'endowment', 'family_office', etc.
    aum_usd_mm NUMERIC,
    fiscal_year_end TEXT,
    allocation_pe_pct NUMERIC,

    -- GP-specific (NULL for pure LPs)
    strategies TEXT[],
    flagship_fund_size_mm NUMERIC,
    total_funds_raised_mm NUMERIC,
    vintage_years INTEGER[],

    -- Data quality
    data_source TEXT,  -- 'pitchbook', 'preqin', 'scraped', 'manual'
    data_quality_score NUMERIC,
    last_enriched_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- All known people (contacts at companies)
CREATE TABLE people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    linkedin_url TEXT,

    -- Data quality
    data_source TEXT,
    email_verified BOOLEAN DEFAULT FALSE,

    created_at TIMESTAMP DEFAULT NOW()
);

-- Person-Company relationships (many-to-many, people move jobs)
CREATE TABLE company_people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,

    title TEXT,
    department TEXT,  -- 'investment', 'operations', 'ir', 'legal'
    is_decision_maker BOOLEAN DEFAULT FALSE,

    -- Employment period
    start_date DATE,
    end_date DATE,  -- NULL = current

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(company_id, person_id, COALESCE(end_date, '9999-12-31'))
);

-- ===============================
-- CLIENT DATABASE (Application)
-- ===============================

-- Companies that are our paying clients
CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link to market data
    company_id UUID NOT NULL REFERENCES companies(id),

    -- Client type
    client_type TEXT NOT NULL CHECK (client_type IN ('gp_client', 'lp_client')),

    -- Subscription
    subscription_tier TEXT DEFAULT 'free',  -- 'free', 'starter', 'pro', 'enterprise'
    subscription_status TEXT DEFAULT 'active',  -- 'trial', 'active', 'past_due', 'cancelled'

    -- Dates
    client_since TIMESTAMP NOT NULL DEFAULT NOW(),
    trial_ends_at TIMESTAMP,

    -- Billing (Stripe integration)
    stripe_customer_id TEXT,
    billing_email TEXT,

    -- Account management
    account_manager TEXT,
    onboarding_status TEXT DEFAULT 'pending',

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(company_id)
);

-- Users of our application (employees of clients)
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Link to client
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

    -- Link to market person data (optional)
    person_id UUID REFERENCES people(id),

    -- Auth (Supabase Auth integration)
    supabase_user_id UUID UNIQUE,  -- From Supabase Auth
    email TEXT NOT NULL UNIQUE,

    -- Profile (may differ from people table)
    first_name TEXT,
    last_name TEXT,
    job_title TEXT,
    phone TEXT,
    linkedin_url TEXT,
    photo_url TEXT,
    bio TEXT,

    -- Permissions
    role TEXT DEFAULT 'member',  -- 'admin', 'member', 'viewer'

    -- Status
    is_active BOOLEAN DEFAULT TRUE,
    onboarding_completed_at TIMESTAMP,
    last_login_at TIMESTAMP,

    created_at TIMESTAMP DEFAULT NOW()
);

-- ===============================
-- VIEWS FOR EASY QUERYING
-- ===============================

-- All GP clients with company details
CREATE VIEW gp_clients AS
SELECT
    cl.id as client_id,
    cl.subscription_tier,
    cl.client_since,
    c.id as company_id,
    c.name as company_name,
    c.strategies,
    c.flagship_fund_size_mm,
    COUNT(u.id) as user_count
FROM clients cl
JOIN companies c ON cl.company_id = c.id
LEFT JOIN users u ON cl.id = u.client_id AND u.is_active = TRUE
WHERE cl.client_type = 'gp_client'
GROUP BY cl.id, c.id;

-- All LP clients with company details
CREATE VIEW lp_clients AS
SELECT
    cl.id as client_id,
    cl.subscription_tier,
    cl.client_since,
    c.id as company_id,
    c.name as company_name,
    c.lp_type,
    c.aum_usd_mm,
    COUNT(u.id) as user_count
FROM clients cl
JOIN companies c ON cl.company_id = c.id
LEFT JOIN users u ON cl.id = u.client_id AND u.is_active = TRUE
WHERE cl.client_type = 'lp_client'
GROUP BY cl.id, c.id;

-- All users with their client/company info
CREATE VIEW users_with_context AS
SELECT
    u.*,
    cl.client_type,
    cl.subscription_tier,
    c.name as company_name,
    c.type as company_type
FROM users u
JOIN clients cl ON u.client_id = cl.id
JOIN companies c ON cl.company_id = c.id;
```

#### Key Queries

```sql
-- "Is this company a client?" (fast lookup)
SELECT EXISTS(SELECT 1 FROM clients WHERE company_id = $1);

-- "Get all users at a client"
SELECT u.* FROM users u
JOIN clients cl ON u.client_id = cl.id
WHERE cl.company_id = $1 AND u.is_active = TRUE;

-- "Get market data for a client's company"
SELECT c.* FROM companies c
JOIN clients cl ON c.id = cl.company_id
WHERE cl.id = $1;

-- "Find contacts at an LP (market data)"
SELECT p.*, cp.title, cp.is_decision_maker
FROM people p
JOIN company_people cp ON p.id = cp.person_id
WHERE cp.company_id = $1 AND cp.end_date IS NULL;

-- "Find users at a client (application data)"
SELECT * FROM users
WHERE client_id = $1 AND is_active = TRUE;
```

---

### 15.2 Admin Dashboard Restructure

#### Current State (Problems)

```
Admin Dashboard
├── Companies  ← Confusing: GPs? LPs? Both?
├── Health     ← OK
└── ???        ← Missing: Users, People
```

#### Proposed Structure

```
Admin Dashboard
├── Overview         ← Dashboard home with stats
│
├── CLIENTS          ← Our paying customers
│   ├── GP Clients   ← Companies using LPxGP as GPs
│   ├── LP Clients   ← Companies using LPxGP as LPs
│   └── Users        ← All users across all clients
│
├── MARKET DATA      ← Intelligence database
│   ├── Companies    ← All known GPs and LPs
│   └── People       ← All known contacts
│
└── SYSTEM
    ├── Health       ← System health checks
    ├── Jobs         ← Background job status
    └── Audit Log    ← Admin action history
```

#### Admin Navigation UI

```
┌─────────────────────────────────────────────────────────────────┐
│ 🔧 Admin Dashboard                                              │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ ┌─────────────┐  CLIENTS                                        │
│ │  Overview   │  ─────────────────────────────────────────────  │
│ └─────────────┘  GP Clients (312)  │ LP Clients (187) │ Users   │
│                                                                  │
│                  MARKET DATA                                     │
│                  ─────────────────────────────────────────────  │
│                  Companies (150K) │ People (500K)               │
│                                                                  │
│                  SYSTEM                                          │
│                  ─────────────────────────────────────────────  │
│                  Health │ Jobs │ Audit Log                      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### GP Clients Page

```
┌─────────────────────────────────────────────────────────────────┐
│ Admin > Clients > GP Clients                    [+ Add Client]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ [Search clients...]                    Filter: [All Tiers ▼]    │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Company          │ Tier      │ Users │ Since    │ Status    │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ Acme Capital     │ Enterprise│ 8     │ Jan 2024 │ Active ●  │ │
│ │ Growth Partners  │ Pro       │ 4     │ Mar 2024 │ Active ●  │ │
│ │ Venture Fund X   │ Starter   │ 2     │ Jun 2024 │ Trial 🟡  │ │
│ │ Capital Firm Y   │ Pro       │ 5     │ Dec 2023 │ Active ●  │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Showing 1-20 of 312                              [<] [1] [2] [>]│
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### LP Clients Page (with Users column - was missing!)

```
┌─────────────────────────────────────────────────────────────────┐
│ Admin > Clients > LP Clients                    [+ Add Client]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ [Search clients...]                    Filter: [All Types ▼]    │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Company       │ Type      │ AUM   │ Users │ Since  │ Status │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ CalPERS       │ Pension   │ $450B │ 3     │ Feb 24 │ Active │ │
│ │ Yale Endow.   │ Endowment │ $42B  │ 2     │ Apr 24 │ Active │ │
│ │ Smith Family  │ Fam.Off.  │ $2B   │ 1     │ Jun 24 │ Active │ │
│ │ Ontario Teach │ Pension   │ $250B │ 4     │ Jan 24 │ Active │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                        ▲                        │
│                            Users column was missing!            │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Users Page (All Users Across Clients)

```
┌─────────────────────────────────────────────────────────────────┐
│ Admin > Clients > Users                                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ [Search users...]          Client: [All ▼]   Role: [All ▼]     │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ User              │ Company        │ Type │ Role   │ Status │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ john@acme.com     │ Acme Capital   │ GP   │ Admin  │ Active │ │
│ │ sarah@acme.com    │ Acme Capital   │ GP   │ Member │ Active │ │
│ │ mike@calpers.org  │ CalPERS        │ LP   │ Admin  │ Active │ │
│ │ lisa@calpers.org  │ CalPERS        │ LP   │ Member │ Invited│ │
│ │ bob@growth.com    │ Growth Partners│ GP   │ Admin  │ Active │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Total: 1,847 users across 499 clients                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Market Data: Companies Page

```
┌─────────────────────────────────────────────────────────────────┐
│ Admin > Market Data > Companies              [+ Add] [⬆ Import] │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ [Search companies...]        Type: [All ▼]  Source: [All ▼]    │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Company       │ Type │ AUM/Size   │ Source   │ Quality │ 🔗  │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ CalPERS       │ LP   │ $450B      │ Preqin   │ ●●●●○   │ ✓  │ │
│ │ Blackstone    │ GP   │ $1T AUM    │ Pitchbook│ ●●●●●   │ ✓  │ │
│ │ Yale Endow.   │ LP   │ $42B       │ Manual   │ ●●●●○   │ ✓  │ │
│ │ Unknown Fund  │ GP   │ $50M       │ Scraped  │ ●●○○○   │    │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                        ▲                        │
│                            🔗 = Is also a client               │
│                                                                  │
│ Total: 152,847 companies (51,203 GPs, 101,644 LPs)             │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### Market Data: People Page

```
┌─────────────────────────────────────────────────────────────────┐
│ Admin > Market Data > People                 [+ Add] [⬆ Import] │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ [Search people...]           Company: [All ▼]  Role: [All ▼]   │
│                                                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ Name          │ Company      │ Title     │ Email   │ Source │ │
│ ├─────────────────────────────────────────────────────────────┤ │
│ │ Sarah Chen    │ CalPERS      │ CIO       │ ✓       │ Manual │ │
│ │ John Smith    │ Acme Capital │ Partner   │ ✓       │ LinkedIn│ │
│ │ Mike Johnson  │ Yale Endow.  │ Director  │ ✓       │ Preqin │ │
│ │ Lisa Wong     │ Blackstone   │ Principal │ ?       │ Scraped│ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Total: 523,847 people                                           │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 15.3 Admin CRUD Operations

#### GP Clients CRUD

**Create GP Client:**
1. Search existing company in market data
2. If exists: Link to existing company
3. If not: Create new company record first
4. Set client_type = 'gp_client'
5. Set subscription tier
6. Invite first admin user

**Read GP Client:**
- Show company details (from companies table)
- Show subscription info (from clients table)
- List users (from users table)
- Show funds (from client_funds table)

**Update GP Client:**
- Can update: subscription tier, status, account manager
- Company details edited via Market Data

**Delete GP Client:**
- Soft delete (mark as cancelled)
- Keep company in market data
- Deactivate all users

#### LP Clients CRUD

Same pattern as GP Clients, but:
- client_type = 'lp_client'
- Show mandates instead of funds
- Different LP-specific fields

#### Users CRUD

**Create User:**
1. Select client (GP or LP)
2. Enter email, name
3. Optionally link to existing person in market data
4. Set role (admin/member/viewer)
5. Send invite email

**Read User:**
- Profile info
- Client association
- Activity history
- Preferences

**Update User:**
- Edit profile, role, status
- Reset password
- Enable/disable

**Delete User:**
- Soft delete (deactivate)
- Or hard delete with confirmation

#### Market Companies CRUD

**Create Company:**
- Enter basic info (name, type, location)
- Mark data source as 'manual'
- Low initial data quality score

**Read Company:**
- All market data fields
- Show if this company is also a client
- List all known people

**Update Company:**
- Any field can be edited
- Update timestamp and mark as 'manual' source

**Delete Company:**
- Warn if company is a client (cannot delete)
- Hard delete with confirmation
- Cascade delete company_people records

#### Market People CRUD

**Create Person:**
- Name, email, LinkedIn
- Link to company (current role)

**Read Person:**
- Contact info
- Employment history
- Show if this person is also a user

**Update Person:**
- Edit contact info
- Update company relationship
- Mark previous role as ended

**Delete Person:**
- Warn if person is a user (cannot delete)
- Hard delete with confirmation

---

### 15.4 Files to Update

| File | Changes |
|------|---------|
| `docs/mockups/admin-dashboard.html` | Restructure navigation |
| `docs/mockups/admin-companies.html` | Rename to admin-market-companies.html |
| NEW: `docs/mockups/admin-gp-clients.html` | GP clients list |
| NEW: `docs/mockups/admin-lp-clients.html` | LP clients list (with users column) |
| NEW: `docs/mockups/admin-users.html` | All users list |
| NEW: `docs/mockups/admin-market-people.html` | Market people list |
| `docs/prd/data-model.md` | Clarify two-database model |
| `supabase/migrations/` | New schema with views |

---

*Section 15 complete. Admin dashboard restructure and two-database model clarified.*

---

