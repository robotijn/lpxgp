-- LPxGP Core Schema Migration
-- Organizations, GP Profiles, LP Profiles, People, Employment

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";
CREATE EXTENSION IF NOT EXISTS "pg_trgm";
CREATE EXTENSION IF NOT EXISTS "vector";

--------------------------------------------------------------------------------
-- Organizations
-- Base table for all organizations. Can be GP, LP, or BOTH.
--------------------------------------------------------------------------------
CREATE TABLE organizations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core identity
    name            TEXT NOT NULL,
    website         TEXT,
    hq_city         TEXT,
    hq_country      TEXT,
    description     TEXT,

    -- Role flags (can be both!)
    is_gp           BOOLEAN DEFAULT FALSE,
    is_lp           BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    -- Must be at least one role
    CONSTRAINT at_least_one_role CHECK (is_gp OR is_lp)
);

CREATE INDEX idx_organizations_is_gp ON organizations(is_gp) WHERE is_gp = TRUE;
CREATE INDEX idx_organizations_is_lp ON organizations(is_lp) WHERE is_lp = TRUE;
CREATE INDEX idx_organizations_name_trgm ON organizations USING GIN(name gin_trgm_ops);

--------------------------------------------------------------------------------
-- GP Profiles (1:1 Extension)
-- GP-specific fields. Only exists for organizations where is_gp = TRUE.
--------------------------------------------------------------------------------
CREATE TABLE gp_profiles (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id                  UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- GP-specific fields
    investment_philosophy   TEXT,
    team_size               INTEGER,
    years_investing         INTEGER,
    spun_out_from           TEXT,
    notable_exits           JSONB DEFAULT '[]',
    track_record_summary    JSONB DEFAULT '{}',

    -- For semantic search
    thesis_embedding        VECTOR(1024),

    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(org_id)
);

CREATE INDEX idx_gp_profiles_org ON gp_profiles(org_id);
CREATE INDEX idx_gp_profiles_thesis_embedding ON gp_profiles USING ivfflat (thesis_embedding vector_cosine_ops);

--------------------------------------------------------------------------------
-- LP Profiles (1:1 Extension)
-- LP-specific fields. Only exists for organizations where is_lp = TRUE.
--------------------------------------------------------------------------------
CREATE TABLE lp_profiles (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id                  UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- LP type and size
    lp_type                 TEXT CHECK (lp_type IN ('pension', 'endowment', 'foundation',
                                                     'family_office', 'sovereign_wealth',
                                                     'insurance', 'fund_of_funds', 'other')),
    total_aum_bn            DECIMAL(12,2),
    pe_allocation_pct       DECIMAL(5,2),

    -- Investment criteria
    strategies              TEXT[] DEFAULT '{}',
    geographic_preferences  TEXT[] DEFAULT '{}',
    sector_preferences      TEXT[] DEFAULT '{}',
    check_size_min_mm       DECIMAL(12,2),
    check_size_max_mm       DECIMAL(12,2),
    fund_size_min_mm        DECIMAL(12,2),
    fund_size_max_mm        DECIMAL(12,2),
    min_track_record_years  INTEGER,
    min_fund_number         INTEGER,

    -- Requirements
    esg_required            BOOLEAN DEFAULT FALSE,
    emerging_manager_ok     BOOLEAN DEFAULT FALSE,

    -- Mandate (for semantic search)
    mandate_description     TEXT,
    mandate_embedding       VECTOR(1024),

    -- LLM-generated summary for sparse data
    llm_summary             TEXT,
    summary_embedding       VECTOR(1024),
    summary_generated_at    TIMESTAMPTZ,
    summary_sources         JSONB DEFAULT '[]',

    -- Data quality
    data_source             TEXT DEFAULT 'manual',
    data_quality_score      DECIMAL(3,2),
    last_verified           TIMESTAMPTZ,

    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(org_id)
);

CREATE INDEX idx_lp_profiles_org ON lp_profiles(org_id);
CREATE INDEX idx_lp_profiles_strategies ON lp_profiles USING GIN(strategies);
CREATE INDEX idx_lp_profiles_geographic ON lp_profiles USING GIN(geographic_preferences);
CREATE INDEX idx_lp_profiles_mandate_embedding ON lp_profiles USING ivfflat (mandate_embedding vector_cosine_ops);

--------------------------------------------------------------------------------
-- People (All Industry Professionals)
-- Current employer is derived from employment WHERE is_current = TRUE.
--------------------------------------------------------------------------------
CREATE TABLE people (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    full_name           TEXT NOT NULL,
    email               TEXT UNIQUE,
    phone               TEXT,
    linkedin_url        TEXT,

    -- Profile
    bio                 TEXT,
    notes               TEXT,
    is_decision_maker   BOOLEAN DEFAULT FALSE,

    -- Platform authentication (NULL = cannot login, SET = can login)
    auth_user_id        UUID UNIQUE REFERENCES auth.users(id),
    role                TEXT CHECK (role IN ('admin', 'member', 'viewer')) DEFAULT 'member',
    is_super_admin      BOOLEAN DEFAULT FALSE,
    invited_by          UUID REFERENCES people(id),
    first_login_at      TIMESTAMPTZ,

    -- Employment status (for people with no/unknown employment records)
    employment_status   TEXT CHECK (employment_status IN ('employed', 'unknown', 'unemployed', 'retired')) DEFAULT 'unknown',

    -- Timestamps
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_people_auth ON people(auth_user_id) WHERE auth_user_id IS NOT NULL;
CREATE INDEX idx_people_email ON people(email);
CREATE INDEX idx_people_name_trgm ON people USING GIN(full_name gin_trgm_ops);

--------------------------------------------------------------------------------
-- Employment (Career History)
-- Links people to organizations over time. Supports multiple concurrent jobs.
--------------------------------------------------------------------------------
CREATE TABLE employment (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id       UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    org_id          UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Position
    title           TEXT,
    department      TEXT,

    -- Timeline
    start_date      DATE,           -- NULL = unknown start
    end_date        DATE,           -- NULL = current or unknown end
    is_current      BOOLEAN DEFAULT TRUE,

    -- Data quality
    confidence      TEXT CHECK (confidence IN ('confirmed', 'likely', 'inferred')) DEFAULT 'confirmed',
    source          TEXT,           -- 'linkedin', 'manual', 'import', etc.

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_dates CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
);

CREATE INDEX idx_employment_person ON employment(person_id);
CREATE INDEX idx_employment_org ON employment(org_id);
CREATE INDEX idx_employment_current ON employment(person_id, is_current) WHERE is_current = TRUE;

--------------------------------------------------------------------------------
-- Invitations
--------------------------------------------------------------------------------
CREATE TABLE invitations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT NOT NULL,
    org_id          UUID NOT NULL REFERENCES organizations(id),
    role            TEXT CHECK (role IN ('admin', 'member', 'viewer')) NOT NULL,
    token           TEXT UNIQUE NOT NULL,
    invited_by      UUID REFERENCES people(id),

    -- Status tracking
    status          TEXT CHECK (status IN ('pending', 'accepted', 'expired', 'cancelled')) DEFAULT 'pending',
    expires_at      TIMESTAMPTZ NOT NULL,
    accepted_at     TIMESTAMPTZ,

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_invitations_token ON invitations(token);
CREATE INDEX idx_invitations_email ON invitations(email);
CREATE INDEX idx_invitations_org ON invitations(org_id);

--------------------------------------------------------------------------------
-- Updated_at trigger function
--------------------------------------------------------------------------------
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply updated_at triggers
CREATE TRIGGER update_organizations_updated_at BEFORE UPDATE ON organizations
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_gp_profiles_updated_at BEFORE UPDATE ON gp_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lp_profiles_updated_at BEFORE UPDATE ON lp_profiles
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_people_updated_at BEFORE UPDATE ON people
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_employment_updated_at BEFORE UPDATE ON employment
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
