## 9. Data Architecture Optimization

### Current Problem
- No GP database structure defined
- No way to distinguish clients (paying users) from market data
- Person/contact relationships unclear

### Proposed Architecture

#### Option A: Client Flag Approach (Simple)
Add `is_client` boolean to existing tables.

```sql
companies (
    id, name, type, ...,
    is_client BOOLEAN DEFAULT FALSE,  -- Are they paying us?
    client_since TIMESTAMP,
    subscription_tier TEXT  -- 'free', 'basic', 'pro', 'enterprise'
)
```
**Pros:** Simple, no joins needed
**Cons:** Client-specific fields pollute the market data table

#### Option B: Separate Client Table (Recommended)
Keep market data clean, link clients separately.

```sql
-- Market data (everyone we know about)
companies (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    type TEXT NOT NULL,  -- 'gp' | 'lp' | 'both'
    ...market data fields...
)

-- Client relationship (our customers)
clients (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    client_type TEXT NOT NULL,  -- 'gp_client' | 'lp_client'
    subscription_tier TEXT,
    client_since TIMESTAMP,
    billing_contact_id UUID REFERENCES people(id),
    account_manager TEXT,
    created_at TIMESTAMP DEFAULT NOW()
)

-- People (contacts at any company)
people (
    id UUID PRIMARY KEY,
    name TEXT NOT NULL,
    email TEXT,
    linkedin_url TEXT,
    title TEXT,
    is_decision_maker BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMP DEFAULT NOW()
)

-- Person-Company relationship (many-to-many, people move jobs)
company_people (
    id UUID PRIMARY KEY,
    company_id UUID REFERENCES companies(id),
    person_id UUID REFERENCES people(id),
    role TEXT,  -- 'partner', 'associate', 'cio', 'analyst'
    is_primary_contact BOOLEAN DEFAULT FALSE,
    start_date DATE,
    end_date DATE,  -- NULL if current
    UNIQUE(company_id, person_id, start_date)
)
```

**Pros:**
- Clean separation of market data vs client data
- People can move between companies (tracked)
- Easy to query "all our GP clients" or "all our LP clients"
- Client-specific fields don't pollute market data

**Cons:**
- Extra join needed for client checks
- Slightly more complex

#### Option C: Hybrid with Materialized View
Best of both worlds—separate tables but fast lookups.

```sql
-- Same tables as Option B, plus:

-- Materialized view for fast "is this a client?" lookups
CREATE MATERIALIZED VIEW client_companies AS
SELECT
    c.id,
    c.name,
    c.type,
    cl.client_type,
    cl.subscription_tier,
    cl.client_since
FROM companies c
JOIN clients cl ON c.id = cl.company_id;

-- Index for fast lookups
CREATE INDEX idx_client_companies_id ON client_companies(id);

-- Refresh periodically (clients don't change often)
-- REFRESH MATERIALIZED VIEW client_companies;
```

### Recommended: Option B + Quick Lookup Index

```sql
-- Core tables
companies (id, name, type, ...)
clients (id, company_id, client_type, subscription_tier, ...)
people (id, name, email, ...)
company_people (company_id, person_id, role, is_current, ...)

-- Quick lookup: index on clients.company_id
CREATE INDEX idx_clients_company ON clients(company_id);

-- Quick check function
CREATE FUNCTION is_client(company_uuid UUID)
RETURNS BOOLEAN AS $$
    SELECT EXISTS(SELECT 1 FROM clients WHERE company_id = company_uuid);
$$ LANGUAGE SQL STABLE;
```

### Full Schema for GP/LP + Clients

```sql
-- ===================
-- MARKET DATA TABLES
-- ===================

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

    -- GP-specific (NULL for pure LPs)
    strategies TEXT[],
    flagship_fund_size_mm NUMERIC,
    total_funds_raised_mm NUMERIC,

    -- Metadata
    data_quality_score NUMERIC,
    last_enriched_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    full_name TEXT NOT NULL,
    email TEXT,
    phone TEXT,
    linkedin_url TEXT,
    created_at TIMESTAMP DEFAULT NOW()
);

CREATE TABLE company_people (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id) ON DELETE CASCADE,
    person_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    title TEXT,
    role_type TEXT,  -- 'partner', 'principal', 'cio', 'analyst', 'ir'
    department TEXT,  -- 'investment', 'operations', 'ir', 'legal'
    is_decision_maker BOOLEAN DEFAULT FALSE,
    is_primary_contact BOOLEAN DEFAULT FALSE,
    start_date DATE,
    end_date DATE,  -- NULL = current
    created_at TIMESTAMP DEFAULT NOW(),
    UNIQUE(company_id, person_id, COALESCE(end_date, '9999-12-31'))
);

-- ===================
-- CLIENT TABLES
-- ===================

CREATE TABLE clients (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id UUID NOT NULL REFERENCES companies(id),

    -- Client classification
    client_type TEXT NOT NULL CHECK (client_type IN ('gp_client', 'lp_client')),
    subscription_tier TEXT DEFAULT 'free',

    -- Dates
    client_since TIMESTAMP NOT NULL DEFAULT NOW(),
    trial_ends_at TIMESTAMP,

    -- Billing
    billing_contact_id UUID REFERENCES people(id),
    stripe_customer_id TEXT,

    -- Account management
    account_manager TEXT,
    onboarding_status TEXT DEFAULT 'pending',

    created_at TIMESTAMP DEFAULT NOW(),

    UNIQUE(company_id)  -- One client record per company
);

-- GP client's funds (if they're a GP client)
CREATE TABLE client_funds (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

    -- Fund details
    fund_name TEXT NOT NULL,
    fund_number INTEGER,  -- Fund I, II, III...
    vintage_year INTEGER,
    target_size_mm NUMERIC,
    hard_cap_mm NUMERIC,
    strategy TEXT,
    geography TEXT[],
    sectors TEXT[],

    -- Fundraising status
    status TEXT DEFAULT 'raising',  -- 'raising', 'final_close', 'deployed'
    first_close_date DATE,
    final_close_target DATE,
    current_commitments_mm NUMERIC,

    -- For matching
    thesis_summary TEXT,
    thesis_embedding VECTOR(1536),

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- LP client's mandates (if they're an LP client)
CREATE TABLE client_mandates (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    client_id UUID NOT NULL REFERENCES clients(id) ON DELETE CASCADE,

    -- Mandate details
    mandate_name TEXT,
    strategies TEXT[],
    geographies TEXT[],
    fund_size_min_mm NUMERIC,
    fund_size_max_mm NUMERIC,
    check_size_min_mm NUMERIC,
    check_size_max_mm NUMERIC,

    -- Preferences
    emerging_managers_ok BOOLEAN DEFAULT FALSE,
    esg_required BOOLEAN DEFAULT FALSE,

    -- For matching
    mandate_text TEXT,
    mandate_embedding VECTOR(1536),

    created_at TIMESTAMP DEFAULT NOW()
);

-- ===================
-- INDEXES
-- ===================

CREATE INDEX idx_companies_type ON companies(type);
CREATE INDEX idx_companies_name ON companies(name);
CREATE INDEX idx_company_people_company ON company_people(company_id);
CREATE INDEX idx_company_people_person ON company_people(person_id);
CREATE INDEX idx_company_people_current ON company_people(company_id) WHERE end_date IS NULL;
CREATE INDEX idx_clients_company ON clients(company_id);
CREATE INDEX idx_clients_type ON clients(client_type);
CREATE INDEX idx_client_funds_client ON client_funds(client_id);

-- ===================
-- HELPER FUNCTIONS
-- ===================

-- Check if company is a client
CREATE FUNCTION is_client(company_uuid UUID)
RETURNS BOOLEAN AS $$
    SELECT EXISTS(SELECT 1 FROM clients WHERE company_id = company_uuid);
$$ LANGUAGE SQL STABLE;

-- Get client type
CREATE FUNCTION get_client_type(company_uuid UUID)
RETURNS TEXT AS $$
    SELECT client_type FROM clients WHERE company_id = company_uuid;
$$ LANGUAGE SQL STABLE;

-- Get current contacts for a company
CREATE FUNCTION get_current_contacts(company_uuid UUID)
RETURNS TABLE (
    person_id UUID,
    full_name TEXT,
    title TEXT,
    email TEXT,
    is_decision_maker BOOLEAN
) AS $$
    SELECT p.id, p.full_name, cp.title, p.email, cp.is_decision_maker
    FROM company_people cp
    JOIN people p ON cp.person_id = p.id
    WHERE cp.company_id = company_uuid AND cp.end_date IS NULL
    ORDER BY cp.is_decision_maker DESC, cp.is_primary_contact DESC;
$$ LANGUAGE SQL STABLE;
```

### Query Examples

```sql
-- All our GP clients with their funds
SELECT c.name, cl.subscription_tier, cf.fund_name, cf.target_size_mm
FROM companies c
JOIN clients cl ON c.id = cl.company_id
LEFT JOIN client_funds cf ON cl.id = cf.client_id
WHERE cl.client_type = 'gp_client';

-- Decision makers at a specific company
SELECT * FROM get_current_contacts('uuid-here');

-- Is this company a client?
SELECT is_client('uuid-here');

-- All LPs in market data (not just clients)
SELECT * FROM companies WHERE type IN ('lp', 'both');

-- GP clients who could match with an LP
SELECT c.name, cf.fund_name, cf.strategy
FROM companies c
JOIN clients cl ON c.id = cl.company_id
JOIN client_funds cf ON cl.id = cf.client_id
WHERE cl.client_type = 'gp_client'
AND cf.status = 'raising'
AND cf.strategy = ANY(ARRAY['buyout', 'growth']);
```

### Migration Path

1. Create new tables (`clients`, `client_funds`, `client_mandates`)
2. Add `type` field to existing `companies` if not present
3. Migrate existing client data to new structure
4. Add helper functions
5. Update application code to use new schema

---

