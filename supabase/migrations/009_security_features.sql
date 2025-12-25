-- ============================================================================
-- Migration 009: Security Features
-- Purpose: Support CSRF, rate limiting tracking, and account lockout
-- ============================================================================

-- ============================================================================
-- 0. Helper Functions (needed for RLS policies below)
-- ============================================================================

-- Get user's effective role (accounts for super_admin flag)
CREATE OR REPLACE FUNCTION get_user_org_role()
RETURNS TEXT AS $$
    SELECT CASE
        WHEN (SELECT is_super_admin FROM people WHERE auth_user_id = auth.uid()) THEN 'super_admin'
        ELSE (SELECT role FROM people WHERE auth_user_id = auth.uid())
    END
$$ LANGUAGE sql SECURITY DEFINER;

COMMENT ON FUNCTION get_user_org_role IS 'Get user effective role (super_admin if is_super_admin flag set, otherwise role field)';

-- ============================================================================
-- 1. Login Attempts Table (Account Lockout)
-- ============================================================================

-- Track login attempts for brute force protection
CREATE TABLE IF NOT EXISTS login_attempts (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identifiers
    email TEXT NOT NULL,
    ip_address INET NOT NULL,

    -- Attempt details
    attempted_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    success BOOLEAN NOT NULL DEFAULT FALSE,

    -- Optional: user agent for forensics
    user_agent TEXT,

    -- Indexes for fast lookups
    CONSTRAINT login_attempts_email_lower CHECK (email = LOWER(email))
);

-- Index for checking lockouts (recent failed attempts by email)
CREATE INDEX idx_login_attempts_email_recent
    ON login_attempts (email, attempted_at DESC)
    WHERE success = FALSE;

-- Index for IP-based rate limiting
CREATE INDEX idx_login_attempts_ip_recent
    ON login_attempts (ip_address, attempted_at DESC);

-- Cleanup old attempts (keep 90 days for audit)
-- This can be run via a scheduled job
CREATE OR REPLACE FUNCTION cleanup_old_login_attempts()
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM login_attempts
    WHERE attempted_at < NOW() - INTERVAL '90 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;

COMMENT ON TABLE login_attempts IS 'Track login attempts for brute force protection and audit';
COMMENT ON FUNCTION cleanup_old_login_attempts IS 'Remove login attempts older than 90 days';


-- ============================================================================
-- 2. Rate Limit Tracking (Optional - for distributed rate limiting)
-- ============================================================================

-- Note: slowapi uses in-memory storage by default.
-- For distributed deployments, you might want to track in Redis or DB.
-- This table is optional and can be used for audit/analytics.

CREATE TABLE IF NOT EXISTS rate_limit_events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identifiers
    key TEXT NOT NULL,  -- user ID, org ID, or IP
    endpoint TEXT NOT NULL,

    -- Event details
    occurred_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    was_limited BOOLEAN NOT NULL DEFAULT FALSE,

    -- For analytics
    requests_in_window INTEGER
);

-- Index for recent events
CREATE INDEX idx_rate_limit_events_recent
    ON rate_limit_events (key, endpoint, occurred_at DESC);

-- Auto-cleanup (keep 7 days)
CREATE OR REPLACE FUNCTION cleanup_old_rate_limit_events()
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    deleted_count INTEGER;
BEGIN
    DELETE FROM rate_limit_events
    WHERE occurred_at < NOW() - INTERVAL '7 days';

    GET DIAGNOSTICS deleted_count = ROW_COUNT;
    RETURN deleted_count;
END;
$$;

COMMENT ON TABLE rate_limit_events IS 'Optional: Track rate limit events for analytics';


-- ============================================================================
-- 3. Session Management Enhancements
-- ============================================================================

-- Track active sessions for the session timeout feature
-- Supabase Auth handles sessions, but we may want additional tracking

CREATE TABLE IF NOT EXISTS user_sessions (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- User reference
    user_id UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,

    -- Session details
    started_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    last_activity_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    expires_at TIMESTAMPTZ NOT NULL,

    -- Device/location info (for security display)
    ip_address INET,
    user_agent TEXT,

    -- Status
    is_active BOOLEAN NOT NULL DEFAULT TRUE,
    ended_at TIMESTAMPTZ,
    end_reason TEXT,  -- 'logout', 'timeout', 'revoked'

    CONSTRAINT valid_session_dates CHECK (expires_at > started_at)
);

-- Index for finding active sessions
CREATE INDEX idx_user_sessions_active
    ON user_sessions (user_id, is_active)
    WHERE is_active = TRUE;

-- Index for cleanup
CREATE INDEX idx_user_sessions_expires
    ON user_sessions (expires_at)
    WHERE is_active = TRUE;

-- Function to end expired sessions
CREATE OR REPLACE FUNCTION end_expired_sessions()
RETURNS INTEGER
LANGUAGE plpgsql
SECURITY DEFINER
AS $$
DECLARE
    ended_count INTEGER;
BEGIN
    UPDATE user_sessions
    SET
        is_active = FALSE,
        ended_at = NOW(),
        end_reason = 'timeout'
    WHERE
        is_active = TRUE
        AND expires_at < NOW();

    GET DIAGNOSTICS ended_count = ROW_COUNT;
    RETURN ended_count;
END;
$$;

COMMENT ON TABLE user_sessions IS 'Track user sessions for timeout and security features';
COMMENT ON FUNCTION end_expired_sessions IS 'Mark expired sessions as inactive';


-- ============================================================================
-- 4. RLS Policies for Security Tables
-- ============================================================================

-- Login attempts: Only FA/Super Admin can view
ALTER TABLE login_attempts ENABLE ROW LEVEL SECURITY;

CREATE POLICY "login_attempts_fa_only" ON login_attempts
    FOR SELECT
    USING (is_privileged_user());

-- No INSERT policy needed - service role inserts directly
-- No UPDATE/DELETE - immutable audit log

-- Rate limit events: Only FA/Super Admin can view
ALTER TABLE rate_limit_events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "rate_limit_events_fa_only" ON rate_limit_events
    FOR SELECT
    USING (is_privileged_user());

-- User sessions: Users can see their own, admins can see org's
ALTER TABLE user_sessions ENABLE ROW LEVEL SECURITY;

CREATE POLICY "user_sessions_own" ON user_sessions
    FOR SELECT
    USING (user_id = auth.uid());

CREATE POLICY "user_sessions_org_admin" ON user_sessions
    FOR SELECT
    USING (
        EXISTS (
            SELECT 1 FROM employment e
            WHERE e.person_id = user_sessions.user_id
            AND e.org_id = current_user_org_id()
            AND e.is_current = TRUE
        )
        AND get_user_org_role() IN ('admin', 'fund_admin', 'super_admin')
    );


-- ============================================================================
-- 5. Helper Views for Security Dashboard
-- ============================================================================

-- View: Recent failed login attempts (for admin dashboard)
CREATE OR REPLACE VIEW v_recent_failed_logins AS
SELECT
    email,
    ip_address,
    COUNT(*) as attempt_count,
    MAX(attempted_at) as last_attempt,
    MIN(attempted_at) as first_attempt
FROM login_attempts
WHERE
    success = FALSE
    AND attempted_at > NOW() - INTERVAL '24 hours'
GROUP BY email, ip_address
HAVING COUNT(*) >= 3
ORDER BY attempt_count DESC, last_attempt DESC;

COMMENT ON VIEW v_recent_failed_logins IS 'Shows IPs/emails with 3+ failed logins in 24h';


-- View: Currently locked accounts
CREATE OR REPLACE VIEW v_locked_accounts AS
SELECT
    email,
    COUNT(*) as failed_attempts,
    MAX(attempted_at) as last_attempt,
    MAX(attempted_at) + INTERVAL '30 minutes' as lockout_expires
FROM login_attempts
WHERE
    success = FALSE
    AND attempted_at > NOW() - INTERVAL '30 minutes'
GROUP BY email
HAVING COUNT(*) >= 5
ORDER BY last_attempt DESC;

COMMENT ON VIEW v_locked_accounts IS 'Shows accounts currently locked out (5+ failures in 30 min)';


-- Grant access to views for privileged users
GRANT SELECT ON v_recent_failed_logins TO authenticated;
GRANT SELECT ON v_locked_accounts TO authenticated;


-- ============================================================================
-- Done
-- ============================================================================

COMMENT ON SCHEMA public IS 'Migration 009: Security features (lockout, rate limiting, sessions)';
