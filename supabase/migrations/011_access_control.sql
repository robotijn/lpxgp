-- Migration: 011_access_control.sql
-- Description: Access control enhancements - impersonation, role management, onboarding tracking

-- =============================================================================
-- 1. IMPERSONATION LOGS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS impersonation_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    admin_user_id UUID NOT NULL REFERENCES people(id) ON DELETE SET NULL,
    target_user_id UUID NOT NULL REFERENCES people(id) ON DELETE SET NULL,
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    ended_at TIMESTAMPTZ,
    reason TEXT,
    actions_count INTEGER DEFAULT 0,
    write_mode_enabled BOOLEAN DEFAULT FALSE,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Index for querying by admin or target
CREATE INDEX idx_impersonation_logs_admin ON impersonation_logs(admin_user_id);
CREATE INDEX idx_impersonation_logs_target ON impersonation_logs(target_user_id);
CREATE INDEX idx_impersonation_logs_started ON impersonation_logs(started_at DESC);

-- Comment for documentation
COMMENT ON TABLE impersonation_logs IS 'Audit trail for admin/FA impersonation sessions. Retention: 2 years minimum.';
COMMENT ON COLUMN impersonation_logs.write_mode_enabled IS 'TRUE only for Super Admin. FA impersonation is always view-only.';

-- =============================================================================
-- 2. LOGIN ATTEMPTS TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS login_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email TEXT NOT NULL,
    ip_address INET,
    user_agent TEXT,
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    success BOOLEAN NOT NULL DEFAULT FALSE
);

-- Index for rate limiting and lockout queries
CREATE INDEX idx_login_attempts_email ON login_attempts(email, attempted_at DESC);
CREATE INDEX idx_login_attempts_ip ON login_attempts(ip_address, attempted_at DESC);

-- Cleanup old entries (90 day retention)
CREATE OR REPLACE FUNCTION cleanup_old_login_attempts()
RETURNS void AS $$
BEGIN
    DELETE FROM login_attempts WHERE attempted_at < NOW() - INTERVAL '90 days';
END;
$$ LANGUAGE plpgsql;

COMMENT ON TABLE login_attempts IS 'Failed login tracking for account lockout. Retention: 90 days.';

-- =============================================================================
-- 3. ROLE CHANGE AUDIT TABLE
-- =============================================================================

CREATE TABLE IF NOT EXISTS role_change_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES people(id) ON DELETE SET NULL,
    changed_by UUID NOT NULL REFERENCES people(id) ON DELETE SET NULL,
    old_role TEXT NOT NULL,
    new_role TEXT NOT NULL,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    reason TEXT
);

CREATE INDEX idx_role_change_audit_user ON role_change_audit(user_id, changed_at DESC);
CREATE INDEX idx_role_change_audit_changed_by ON role_change_audit(changed_by, changed_at DESC);

COMMENT ON TABLE role_change_audit IS 'Tracks all user role modifications for compliance.';

-- =============================================================================
-- 4. ENTITY CHANGE AUDIT TABLE (FA Operations)
-- =============================================================================

CREATE TABLE IF NOT EXISTS entity_change_audit (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL CHECK (entity_type IN ('gp', 'lp', 'person', 'user', 'fund')),
    entity_id UUID NOT NULL,
    operation TEXT NOT NULL CHECK (operation IN ('create', 'update', 'delete', 'merge')),
    changed_by UUID NOT NULL REFERENCES people(id) ON DELETE SET NULL,
    old_data JSONB,
    new_data JSONB,
    changed_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX idx_entity_change_audit_entity ON entity_change_audit(entity_type, entity_id, changed_at DESC);
CREATE INDEX idx_entity_change_audit_changed_by ON entity_change_audit(changed_by, changed_at DESC);

COMMENT ON TABLE entity_change_audit IS 'Tracks all GP/LP/People/User changes made by FA/SA.';

-- =============================================================================
-- 5. UPDATE PEOPLE TABLE FOR FUND_ADMIN ROLE
-- =============================================================================

-- Update role constraint to include fund_admin
ALTER TABLE people DROP CONSTRAINT IF EXISTS people_role_check;
ALTER TABLE people ADD CONSTRAINT people_role_check
    CHECK (role IN ('viewer', 'member', 'admin', 'fund_admin'));

-- Add needs_password_change for direct user creation
ALTER TABLE people ADD COLUMN IF NOT EXISTS needs_password_change BOOLEAN DEFAULT FALSE;

COMMENT ON COLUMN people.needs_password_change IS 'TRUE when user was created directly by FA and must change password on first login.';

-- =============================================================================
-- 6. ONBOARDING TRACKING ON ORGANIZATIONS
-- =============================================================================

ALTER TABLE organizations ADD COLUMN IF NOT EXISTS onboarded_by UUID REFERENCES people(id);
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS onboarded_at TIMESTAMPTZ;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS onboarding_method TEXT
    CHECK (onboarding_method IN ('database_only', 'invite_admin', 'create_directly'));

COMMENT ON COLUMN organizations.onboarded_by IS 'FA/SA who onboarded this organization.';
COMMENT ON COLUMN organizations.onboarding_method IS 'How the organization was onboarded.';

-- =============================================================================
-- 7. HELPER FUNCTIONS FOR RLS
-- =============================================================================

-- Check if user is a Fund Admin
CREATE OR REPLACE FUNCTION is_fund_admin()
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM people
        WHERE id = auth.uid()
        AND role = 'fund_admin'
    );
$$ LANGUAGE SQL SECURITY DEFINER STABLE;

-- Update is_privileged_user to include fund_admin
CREATE OR REPLACE FUNCTION is_privileged_user()
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM people
        WHERE id = auth.uid()
        AND (role = 'fund_admin' OR is_super_admin = TRUE)
    );
$$ LANGUAGE SQL SECURITY DEFINER STABLE;

-- Impersonation context functions
CREATE OR REPLACE FUNCTION current_impersonated_user_id()
RETURNS UUID AS $$
    SELECT current_setting('app.impersonated_user_id', TRUE)::UUID;
$$ LANGUAGE SQL STABLE;

CREATE OR REPLACE FUNCTION is_impersonating()
RETURNS BOOLEAN AS $$
    SELECT current_setting('app.impersonated_user_id', TRUE) IS NOT NULL;
$$ LANGUAGE SQL STABLE;

CREATE OR REPLACE FUNCTION impersonation_is_read_only()
RETURNS BOOLEAN AS $$
    SELECT current_setting('app.impersonation_read_only', TRUE)::BOOLEAN;
$$ LANGUAGE SQL STABLE;

-- =============================================================================
-- 8. RLS POLICIES FOR NEW TABLES
-- =============================================================================

-- Impersonation logs: Super Admin only
ALTER TABLE impersonation_logs ENABLE ROW LEVEL SECURITY;

CREATE POLICY "impersonation_logs_sa_only" ON impersonation_logs
    FOR ALL USING (is_super_admin());

-- Role change audit: Privileged users can read
ALTER TABLE role_change_audit ENABLE ROW LEVEL SECURITY;

CREATE POLICY "role_change_audit_privileged_read" ON role_change_audit
    FOR SELECT USING (is_privileged_user());

CREATE POLICY "role_change_audit_sa_write" ON role_change_audit
    FOR INSERT WITH CHECK (is_super_admin());

-- Entity change audit: Privileged users can read and write
ALTER TABLE entity_change_audit ENABLE ROW LEVEL SECURITY;

CREATE POLICY "entity_change_audit_privileged" ON entity_change_audit
    FOR ALL USING (is_privileged_user());

-- Login attempts: Only via service role
ALTER TABLE login_attempts ENABLE ROW LEVEL SECURITY;

-- No policies = only service role can access

-- =============================================================================
-- 9. UPDATE RLS POLICIES FOR PRIVILEGED ACCESS
-- =============================================================================

-- Organizations: FA can read all, write for onboarding
DROP POLICY IF EXISTS "organizations_user_read" ON organizations;
CREATE POLICY "organizations_privileged_access" ON organizations
    FOR ALL USING (
        org_id = current_user_org_id()
        OR is_privileged_user()
    );

-- People: FA can manage all
DROP POLICY IF EXISTS "people_user_access" ON people;
CREATE POLICY "people_privileged_access" ON people
    FOR ALL USING (
        id = auth.uid()
        OR org_id = current_user_org_id()
        OR is_privileged_user()
    );

-- =============================================================================
-- 10. TRIGGERS FOR AUDIT LOGGING
-- =============================================================================

-- Auto-log role changes
CREATE OR REPLACE FUNCTION log_role_change()
RETURNS TRIGGER AS $$
BEGIN
    IF OLD.role IS DISTINCT FROM NEW.role THEN
        INSERT INTO role_change_audit (user_id, changed_by, old_role, new_role)
        VALUES (NEW.id, auth.uid(), OLD.role, NEW.role);
    END IF;
    RETURN NEW;
END;
$$ LANGUAGE plpgsql SECURITY DEFINER;

DROP TRIGGER IF EXISTS trigger_log_role_change ON people;
CREATE TRIGGER trigger_log_role_change
    AFTER UPDATE ON people
    FOR EACH ROW
    WHEN (OLD.role IS DISTINCT FROM NEW.role)
    EXECUTE FUNCTION log_role_change();

-- =============================================================================
-- GRANTS
-- =============================================================================

-- Grant access to authenticated users
GRANT SELECT ON impersonation_logs TO authenticated;
GRANT SELECT ON role_change_audit TO authenticated;
GRANT SELECT, INSERT ON entity_change_audit TO authenticated;

-- Service role has full access
GRANT ALL ON login_attempts TO service_role;
GRANT ALL ON impersonation_logs TO service_role;
GRANT ALL ON role_change_audit TO service_role;
GRANT ALL ON entity_change_audit TO service_role;
