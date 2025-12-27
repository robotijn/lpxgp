-- ============================================================================
-- Migration 015: Expand schema for ETL data ingestion
--
-- IMPORTANT: This migration adds RAW/ORIGINAL data columns only.
-- Normalized AI data goes in fund_ai_profiles / lp_ai_profiles (migration 016)
-- ============================================================================

--------------------------------------------------------------------------------
-- Organizations: External IDs + Hierarchy + LinkedIn (original data)
--------------------------------------------------------------------------------
ALTER TABLE organizations
    ADD COLUMN IF NOT EXISTS linkedin_url TEXT,
    ADD COLUMN IF NOT EXISTS preqin_id TEXT,
    ADD COLUMN IF NOT EXISTS parent_org_id UUID REFERENCES organizations(id),
    ADD COLUMN IF NOT EXISTS org_level TEXT CHECK (org_level IN ('parent', 'subsidiary', 'division', 'standalone')) DEFAULT 'standalone';

CREATE INDEX IF NOT EXISTS idx_organizations_parent ON organizations(parent_org_id);
CREATE INDEX IF NOT EXISTS idx_organizations_preqin ON organizations(preqin_id) WHERE preqin_id IS NOT NULL;

--------------------------------------------------------------------------------
-- People: External sync + data quality fields (original data)
--------------------------------------------------------------------------------
ALTER TABLE people
    ADD COLUMN IF NOT EXISTS title TEXT,  -- Mr/Ms/Dr/Prof (original)
    ADD COLUMN IF NOT EXISTS mobile TEXT,
    ADD COLUMN IF NOT EXISTS email_valid BOOLEAN,
    ADD COLUMN IF NOT EXISTS certification_status TEXT,
    ADD COLUMN IF NOT EXISTS data_source TEXT DEFAULT 'manual',
    ADD COLUMN IF NOT EXISTS external_id TEXT,
    ADD COLUMN IF NOT EXISTS external_source TEXT;

ALTER TABLE people
    ADD CONSTRAINT people_external_unique_v2
    UNIQUE (external_source, external_id);

--------------------------------------------------------------------------------
-- Funds: Additional RAW fields (client sees these, NOT normalized)
--------------------------------------------------------------------------------
ALTER TABLE funds
    -- Original text values from source (for display)
    ADD COLUMN IF NOT EXISTS strategies_raw TEXT,      -- "Development / Minority, Seed / early stage"
    ADD COLUMN IF NOT EXISTS fund_size_raw TEXT,       -- "Small (€100m-€500m)"
    ADD COLUMN IF NOT EXISTS geographic_scope_raw TEXT, -- "Global", "Pan-European"
    ADD COLUMN IF NOT EXISTS domicile TEXT,            -- "Luxembourg", "Cayman Islands"
    ADD COLUMN IF NOT EXISTS first_close_target DATE,
    ADD COLUMN IF NOT EXISTS fee_details TEXT,
    ADD COLUMN IF NOT EXISTS non_accredited_ok BOOLEAN DEFAULT FALSE;

--------------------------------------------------------------------------------
-- LP Profiles: Behavioral metrics (original numbers, for display)
--------------------------------------------------------------------------------
ALTER TABLE lp_profiles
    ADD COLUMN IF NOT EXISTS solicitations_received INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS solicitations_accepted INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS solicitations_declined INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS event_participation JSONB DEFAULT '[]';

CREATE INDEX IF NOT EXISTS idx_lp_profiles_activity ON lp_profiles(last_activity_at DESC) WHERE last_activity_at IS NOT NULL;

--------------------------------------------------------------------------------
-- Comments: Clarify these are ORIGINAL values
--------------------------------------------------------------------------------
COMMENT ON COLUMN organizations.linkedin_url IS 'LinkedIn company page URL (original)';
COMMENT ON COLUMN organizations.preqin_id IS 'Preqin database identifier (original)';

COMMENT ON COLUMN people.title IS 'Salutation: Mr/Ms/Dr/Prof (original from source)';
COMMENT ON COLUMN people.certification_status IS 'IPEM certification status (original)';

COMMENT ON COLUMN funds.strategies_raw IS 'Original strategy text for display: "Development / Minority"';
COMMENT ON COLUMN funds.fund_size_raw IS 'Original size text for display: "Small (€100m-€500m)"';
COMMENT ON COLUMN funds.geographic_scope_raw IS 'Original scope for display: "Global", "Pan-European"';

COMMENT ON COLUMN lp_profiles.solicitations_received IS 'Original count: total GP approaches';
COMMENT ON COLUMN lp_profiles.solicitations_accepted IS 'Original count: accepted meetings';
COMMENT ON COLUMN lp_profiles.solicitations_declined IS 'Original count: declined approaches';
