-- LPxGP Funds Schema Migration
-- Funds, Fund Team

--------------------------------------------------------------------------------
-- Funds (GP Profiles)
--------------------------------------------------------------------------------
CREATE TABLE funds (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    created_by          UUID REFERENCES people(id),

    -- Basics
    name                TEXT NOT NULL,
    fund_number         INTEGER,
    status              TEXT CHECK (status IN ('draft', 'raising', 'closed', 'invested', 'harvesting')) DEFAULT 'draft',
    vintage_year        INTEGER,
    target_size_mm      DECIMAL(12,2),
    current_size_mm     DECIMAL(12,2),
    hard_cap_mm         DECIMAL(12,2),
    first_close_date    DATE,
    final_close_target  DATE,

    -- Strategy
    strategy            TEXT,
    sub_strategy        TEXT,
    geographic_focus    TEXT[] DEFAULT '{}',
    sector_focus        TEXT[] DEFAULT '{}',

    -- Investment Parameters
    check_size_min_mm   DECIMAL(12,2),
    check_size_max_mm   DECIMAL(12,2),
    target_companies    INTEGER,
    holding_period_years INTEGER,

    -- Track Record (JSONB for flexibility)
    track_record        JSONB DEFAULT '[]',
    notable_exits       JSONB DEFAULT '[]',
    total_invested_mm   DECIMAL(12,2),
    realized_proceeds_mm DECIMAL(12,2),

    -- Team (see fund_team table for actual team members)
    team_size           INTEGER,
    years_investing     INTEGER,
    spun_out_from       TEXT,

    -- Terms
    management_fee_pct  DECIMAL(4,2),
    carried_interest_pct DECIMAL(4,2),
    hurdle_rate_pct     DECIMAL(4,2),
    gp_commitment_pct   DECIMAL(4,2),
    fund_term_years     INTEGER,

    -- ESG
    esg_policy          BOOLEAN DEFAULT FALSE,
    impact_focus        BOOLEAN DEFAULT FALSE,
    esg_certifications  TEXT[] DEFAULT '{}',

    -- Documents
    pitch_deck_url      TEXT,
    pitch_deck_text     TEXT,

    -- Investment Thesis (for semantic search)
    investment_thesis   TEXT,
    thesis_embedding    VECTOR(1024),

    -- Audit Trail
    updated_by          UUID REFERENCES people(id),
    data_source         TEXT DEFAULT 'manual',
    last_verified       TIMESTAMPTZ,

    -- Metadata
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_funds_org ON funds(org_id);
CREATE INDEX idx_funds_status ON funds(status);
CREATE INDEX idx_funds_strategy ON funds(strategy);
CREATE INDEX idx_funds_thesis_embedding ON funds USING ivfflat (thesis_embedding vector_cosine_ops);

--------------------------------------------------------------------------------
-- Fund Team (GP Professionals on a Fund)
-- Links people to funds they work on.
--------------------------------------------------------------------------------
CREATE TABLE fund_team (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fund_id         UUID REFERENCES funds(id) ON DELETE CASCADE NOT NULL,
    person_id       UUID REFERENCES people(id) NOT NULL,
    role            TEXT,                       -- "Partner", "Principal", "Analyst"
    is_key_person   BOOLEAN DEFAULT FALSE,      -- regulatory "key person"
    allocation_pct  DECIMAL(5,2),               -- % of time on this fund
    created_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(fund_id, person_id)
);

CREATE INDEX idx_fund_team_fund ON fund_team(fund_id);
CREATE INDEX idx_fund_team_person ON fund_team(person_id);

--------------------------------------------------------------------------------
-- Updated_at trigger
--------------------------------------------------------------------------------
CREATE TRIGGER update_funds_updated_at BEFORE UPDATE ON funds
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
