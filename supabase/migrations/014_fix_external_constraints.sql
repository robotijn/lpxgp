-- Fix external sync constraints for upsert compatibility
-- Supabase upsert requires UNIQUE constraints, not partial indexes

--------------------------------------------------------------------------------
-- Organizations: Replace partial index with unique constraint
--------------------------------------------------------------------------------
DROP INDEX IF EXISTS idx_org_external;

-- For upsert to work, we need a proper unique constraint
-- NULL values are considered distinct in PostgreSQL, so this allows multiple NULLs
ALTER TABLE organizations
    ADD CONSTRAINT organizations_external_unique
    UNIQUE (external_source, external_id);

--------------------------------------------------------------------------------
-- People: Replace partial index with unique constraint
--------------------------------------------------------------------------------
DROP INDEX IF EXISTS idx_people_external;

ALTER TABLE people
    ADD CONSTRAINT people_external_unique
    UNIQUE (external_source, external_id);

--------------------------------------------------------------------------------
-- Funds: Replace partial index with unique constraint
--------------------------------------------------------------------------------
DROP INDEX IF EXISTS idx_funds_external;

ALTER TABLE funds
    ADD CONSTRAINT funds_external_unique
    UNIQUE (external_source, external_id);
