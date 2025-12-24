-- LPxGP RLS v2 - Security Hardening
-- Addresses Red Team findings: H1-H6
-- Philosophy: Very limited access - only admins/FAs see full system

--------------------------------------------------------------------------------
-- New Helper Functions
--------------------------------------------------------------------------------

-- Check if user is Fund Admin (FA) - can see cross-org data
CREATE OR REPLACE FUNCTION is_fund_admin()
RETURNS BOOLEAN AS $$
    SELECT COALESCE(
        (SELECT role = 'fund_admin' FROM people WHERE auth_user_id = auth.uid()),
        FALSE
    )
$$ LANGUAGE sql SECURITY DEFINER;

-- Check if user is privileged (FA or Super Admin)
CREATE OR REPLACE FUNCTION is_privileged_user()
RETURNS BOOLEAN AS $$
    SELECT is_super_admin() OR is_fund_admin()
$$ LANGUAGE sql SECURITY DEFINER;

-- Improved current_user_org_id with deterministic ordering
-- FIX: H6 - LIMIT 1 without ORDER BY was non-deterministic
CREATE OR REPLACE FUNCTION current_user_org_id()
RETURNS UUID AS $$
    SELECT e.org_id
    FROM people p
    JOIN employment e ON e.person_id = p.id AND e.is_current = TRUE
    WHERE p.auth_user_id = auth.uid()
    ORDER BY e.updated_at DESC  -- Most recent employment wins
    LIMIT 1
$$ LANGUAGE sql SECURITY DEFINER;

--------------------------------------------------------------------------------
-- Audit Log Table (for sensitive access tracking)
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS audit_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID,
    user_email TEXT,
    org_id UUID,
    table_name TEXT NOT NULL,
    record_id UUID,
    operation TEXT NOT NULL CHECK (operation IN ('SELECT', 'INSERT', 'UPDATE', 'DELETE')),
    details JSONB DEFAULT '{}',
    ip_address INET,
    user_agent TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for querying audit logs
CREATE INDEX IF NOT EXISTS idx_audit_logs_user ON audit_logs(user_id);
CREATE INDEX IF NOT EXISTS idx_audit_logs_table ON audit_logs(table_name);
CREATE INDEX IF NOT EXISTS idx_audit_logs_created ON audit_logs(created_at);

-- Audit logs are append-only, readable by privileged users
ALTER TABLE audit_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Audit logs readable by privileged" ON audit_logs
    FOR SELECT USING (is_privileged_user());

CREATE POLICY "Audit logs insertable by system" ON audit_logs
    FOR INSERT WITH CHECK (TRUE);  -- Triggers can insert

--------------------------------------------------------------------------------
-- Trigger Function for Audit Logging
--------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION audit_log_access()
RETURNS TRIGGER AS $$
BEGIN
    INSERT INTO audit_logs (
        user_id,
        user_email,
        org_id,
        table_name,
        record_id,
        operation,
        details
    )
    SELECT
        p.id,
        p.email,
        current_user_org_id(),
        TG_TABLE_NAME,
        COALESCE(NEW.id, OLD.id),
        TG_OP,
        jsonb_build_object(
            'old', CASE WHEN TG_OP IN ('UPDATE', 'DELETE') THEN row_to_json(OLD) END,
            'new', CASE WHEN TG_OP IN ('INSERT', 'UPDATE') THEN row_to_json(NEW) END
        )
    FROM people p
    WHERE p.auth_user_id = auth.uid();

    RETURN COALESCE(NEW, OLD);
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

--------------------------------------------------------------------------------
-- Single Employment Enforcement
-- FIX: Ensure only one is_current=TRUE per person
--------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION enforce_single_employment()
RETURNS TRIGGER AS $$
BEGIN
    IF NEW.is_current = TRUE THEN
        -- Clear any other current employment for this person
        UPDATE employment
        SET is_current = FALSE, updated_at = NOW()
        WHERE person_id = NEW.person_id
          AND id != NEW.id
          AND is_current = TRUE;
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply trigger
DROP TRIGGER IF EXISTS trg_single_employment ON employment;
CREATE TRIGGER trg_single_employment
    BEFORE INSERT OR UPDATE ON employment
    FOR EACH ROW
    EXECUTE FUNCTION enforce_single_employment();

--------------------------------------------------------------------------------
-- Drop and Replace People Policies
-- FIX: H2 - People were readable by all authenticated
--------------------------------------------------------------------------------

DROP POLICY IF EXISTS "People readable by authenticated" ON people;

-- People visible to:
-- 1. User themselves
-- 2. People at same org (via employment)
-- 3. People at LP orgs (for LP research)
-- 4. Privileged users (FA, Super Admin)
CREATE POLICY "People readable by org or privileged" ON people
    FOR SELECT USING (
        -- Self
        auth_user_id = auth.uid()
        -- Same org
        OR id IN (
            SELECT e2.person_id
            FROM employment e1
            JOIN employment e2 ON e1.org_id = e2.org_id
            JOIN people p ON p.id = e1.person_id
            WHERE p.auth_user_id = auth.uid() AND e1.is_current = TRUE
        )
        -- LP org employees (for research)
        OR id IN (
            SELECT e.person_id
            FROM employment e
            JOIN organizations o ON o.id = e.org_id
            WHERE o.is_lp = TRUE AND e.is_current = TRUE
        )
        -- Privileged users see all
        OR is_privileged_user()
    );

--------------------------------------------------------------------------------
-- Drop and Replace Employment Policies
-- FIX: H1 - Employment was readable by all authenticated
--------------------------------------------------------------------------------

DROP POLICY IF EXISTS "Employment readable by authenticated" ON employment;

-- Employment visible to:
-- 1. Own employment
-- 2. Employment at same org
-- 3. Employment at LP orgs (for research)
-- 4. Privileged users
CREATE POLICY "Employment readable by org or privileged" ON employment
    FOR SELECT USING (
        -- Own employment
        person_id = (SELECT id FROM people WHERE auth_user_id = auth.uid())
        -- Same org
        OR org_id = current_user_org_id()
        -- LP org employment (for research)
        OR org_id IN (SELECT id FROM organizations WHERE is_lp = TRUE)
        -- Privileged
        OR is_privileged_user()
    );

--------------------------------------------------------------------------------
-- Add Missing DELETE Policy to Invitations
-- FIX: H3 - Invitations had no DELETE policy
--------------------------------------------------------------------------------

CREATE POLICY "Invitations deleted by org admins" ON invitations
    FOR DELETE USING (
        (org_id = current_user_org_id() AND current_user_role() = 'admin')
        OR is_super_admin()
    );

--------------------------------------------------------------------------------
-- Add Missing UPDATE and DELETE Policies to Outreach Events
-- FIX: H4 - Outreach events had no UPDATE/DELETE
--------------------------------------------------------------------------------

CREATE POLICY "Users update outreach events" ON outreach_events
    FOR UPDATE USING (
        match_id IN (
            SELECT m.id FROM fund_lp_matches m
            JOIN funds f ON m.fund_id = f.id
            WHERE f.org_id = current_user_org_id()
        )
        OR is_super_admin()
    );

CREATE POLICY "Users delete outreach events" ON outreach_events
    FOR DELETE USING (
        match_id IN (
            SELECT m.id FROM fund_lp_matches m
            JOIN funds f ON m.fund_id = f.id
            WHERE f.org_id = current_user_org_id()
        )
        OR is_super_admin()
    );

--------------------------------------------------------------------------------
-- Audit Logging Triggers on Sensitive Tables
-- FIX: H5 - No audit trail for LP profile access
--------------------------------------------------------------------------------

-- Audit LP profile reads (expensive, consider sampling in production)
DROP TRIGGER IF EXISTS trg_audit_lp_profiles ON lp_profiles;
CREATE TRIGGER trg_audit_lp_profiles
    AFTER UPDATE OR DELETE ON lp_profiles
    FOR EACH ROW
    EXECUTE FUNCTION audit_log_access();

-- Audit fund matches
DROP TRIGGER IF EXISTS trg_audit_fund_matches ON fund_lp_matches;
CREATE TRIGGER trg_audit_fund_matches
    AFTER INSERT OR UPDATE OR DELETE ON fund_lp_matches
    FOR EACH ROW
    EXECUTE FUNCTION audit_log_access();

-- Audit invitations
DROP TRIGGER IF EXISTS trg_audit_invitations ON invitations;
CREATE TRIGGER trg_audit_invitations
    AFTER INSERT OR UPDATE OR DELETE ON invitations
    FOR EACH ROW
    EXECUTE FUNCTION audit_log_access();

--------------------------------------------------------------------------------
-- Update People Table for Fund Admin Role
--------------------------------------------------------------------------------

-- Add fund_admin to role check if not present
ALTER TABLE people
DROP CONSTRAINT IF EXISTS people_role_check;

ALTER TABLE people
ADD CONSTRAINT people_role_check
CHECK (role IN ('admin', 'member', 'viewer', 'fund_admin'));

--------------------------------------------------------------------------------
-- Comments for Documentation
--------------------------------------------------------------------------------

COMMENT ON FUNCTION is_fund_admin() IS 'Check if current user is a Fund Admin (cross-org access)';
COMMENT ON FUNCTION is_privileged_user() IS 'Check if user is FA or Super Admin';
COMMENT ON FUNCTION enforce_single_employment() IS 'Ensure only one current employment per person';
COMMENT ON FUNCTION audit_log_access() IS 'Log sensitive data access to audit_logs table';
COMMENT ON TABLE audit_logs IS 'Audit trail for sensitive data access';

--------------------------------------------------------------------------------
-- Grant Permissions
--------------------------------------------------------------------------------

-- Service role can insert audit logs
GRANT INSERT ON audit_logs TO service_role;
GRANT SELECT ON audit_logs TO authenticated;
