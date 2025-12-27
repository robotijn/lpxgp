-- LPxGP External Sync Schema Migration
-- Adds external_id tracking for syncing with Metabase/IPEM data source

--------------------------------------------------------------------------------
-- Organizations: External ID tracking
--------------------------------------------------------------------------------
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS external_source TEXT DEFAULT 'ipem';
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS parent_org_id UUID REFERENCES organizations(id);

-- Drop constraint if exists (for re-running migration)
ALTER TABLE organizations DROP CONSTRAINT IF EXISTS at_least_one_role;

-- Make roles optional during import (can be set later)
ALTER TABLE organizations ADD CONSTRAINT at_least_one_role
    CHECK (is_gp OR is_lp OR external_id IS NOT NULL);

CREATE UNIQUE INDEX IF NOT EXISTS idx_org_external
    ON organizations(external_source, external_id)
    WHERE external_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_org_parent ON organizations(parent_org_id);

--------------------------------------------------------------------------------
-- People: External ID tracking + certification status
--------------------------------------------------------------------------------
ALTER TABLE people ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE people ADD COLUMN IF NOT EXISTS external_source TEXT DEFAULT 'ipem';
ALTER TABLE people ADD COLUMN IF NOT EXISTS certification_status TEXT;
ALTER TABLE people ADD COLUMN IF NOT EXISTS email_valid BOOLEAN;

CREATE UNIQUE INDEX IF NOT EXISTS idx_people_external
    ON people(external_source, external_id)
    WHERE external_id IS NOT NULL;

--------------------------------------------------------------------------------
-- Funds: External ID tracking
--------------------------------------------------------------------------------
ALTER TABLE funds ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE funds ADD COLUMN IF NOT EXISTS external_source TEXT DEFAULT 'ipem';

CREATE UNIQUE INDEX IF NOT EXISTS idx_funds_external
    ON funds(external_source, external_id)
    WHERE external_id IS NOT NULL;

--------------------------------------------------------------------------------
-- LP Profiles: Additional fields from IPEM
--------------------------------------------------------------------------------
ALTER TABLE lp_profiles ADD COLUMN IF NOT EXISTS solicitations_received INTEGER DEFAULT 0;
ALTER TABLE lp_profiles ADD COLUMN IF NOT EXISTS solicitations_accepted INTEGER DEFAULT 0;

--------------------------------------------------------------------------------
-- Sync Log: Audit trail for data imports
--------------------------------------------------------------------------------
CREATE TABLE IF NOT EXISTS sync_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    sync_date       TIMESTAMPTZ DEFAULT NOW(),
    source          TEXT NOT NULL,
    table_name      TEXT NOT NULL,
    records_created INTEGER DEFAULT 0,
    records_updated INTEGER DEFAULT 0,
    records_deleted INTEGER DEFAULT 0,
    records_skipped INTEGER DEFAULT 0,
    errors          JSONB DEFAULT '[]',
    duration_ms     INTEGER,
    metadata        JSONB DEFAULT '{}'
);

CREATE INDEX IF NOT EXISTS idx_sync_log_date ON sync_log(sync_date DESC);
CREATE INDEX IF NOT EXISTS idx_sync_log_source ON sync_log(source, table_name);

--------------------------------------------------------------------------------
-- Comments for documentation
--------------------------------------------------------------------------------
COMMENT ON COLUMN organizations.external_id IS 'ID from external source (e.g., IPEM Organization ID)';
COMMENT ON COLUMN organizations.external_source IS 'External data source identifier (ipem, preqin, etc.)';
COMMENT ON COLUMN organizations.parent_org_id IS 'Parent organization for hierarchical structures';

COMMENT ON COLUMN people.external_id IS 'ID from external source (e.g., IPEM Contact ID)';
COMMENT ON COLUMN people.certification_status IS 'IPEM certification: Certified, Waiting, etc.';
COMMENT ON COLUMN people.email_valid IS 'Email validation result from source';

COMMENT ON COLUMN funds.external_id IS 'ID from external source (e.g., IPEM Fund ID)';

COMMENT ON TABLE sync_log IS 'Audit trail for data imports and syncs';
