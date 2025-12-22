-- LPxGP Row-Level Security Policies
-- Multi-tenancy and access control

--------------------------------------------------------------------------------
-- Enable RLS on all tables
--------------------------------------------------------------------------------
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE gp_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE lp_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE people ENABLE ROW LEVEL SECURITY;
ALTER TABLE employment ENABLE ROW LEVEL SECURITY;
ALTER TABLE invitations ENABLE ROW LEVEL SECURITY;
ALTER TABLE funds ENABLE ROW LEVEL SECURITY;
ALTER TABLE fund_team ENABLE ROW LEVEL SECURITY;
ALTER TABLE investments ENABLE ROW LEVEL SECURITY;
ALTER TABLE fund_lp_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE fund_lp_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE pitches ENABLE ROW LEVEL SECURITY;
ALTER TABLE outreach_events ENABLE ROW LEVEL SECURITY;
ALTER TABLE match_outcomes ENABLE ROW LEVEL SECURITY;
ALTER TABLE lp_match_preferences ENABLE ROW LEVEL SECURITY;
ALTER TABLE relationships ENABLE ROW LEVEL SECURITY;
ALTER TABLE mutual_connections ENABLE ROW LEVEL SECURITY;

--------------------------------------------------------------------------------
-- Helper Functions
--------------------------------------------------------------------------------

-- Get current user's primary org_id (derived from employment)
CREATE OR REPLACE FUNCTION current_user_org_id()
RETURNS UUID AS $$
    SELECT e.org_id
    FROM people p
    JOIN employment e ON e.person_id = p.id AND e.is_current = TRUE
    WHERE p.auth_user_id = auth.uid()
    LIMIT 1  -- In case of multiple current jobs, pick one
$$ LANGUAGE sql SECURITY DEFINER;

-- Check if current user is super admin
CREATE OR REPLACE FUNCTION is_super_admin()
RETURNS BOOLEAN AS $$
    SELECT COALESCE(
        (SELECT is_super_admin FROM people WHERE auth_user_id = auth.uid()),
        FALSE
    )
$$ LANGUAGE sql SECURITY DEFINER;

-- Check if user works at a GP org
CREATE OR REPLACE FUNCTION user_works_at_gp()
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM people p
        JOIN employment e ON e.person_id = p.id AND e.is_current = TRUE
        JOIN organizations o ON o.id = e.org_id
        WHERE p.auth_user_id = auth.uid() AND o.is_gp = TRUE
    )
$$ LANGUAGE sql SECURITY DEFINER;

-- Get current user's role at their org
CREATE OR REPLACE FUNCTION current_user_role()
RETURNS TEXT AS $$
    SELECT role FROM people WHERE auth_user_id = auth.uid()
$$ LANGUAGE sql SECURITY DEFINER;

--------------------------------------------------------------------------------
-- Organizations Policies
--------------------------------------------------------------------------------

-- Users see their own GP org and all LP orgs
CREATE POLICY "Users see own GP org and all LPs" ON organizations
    FOR SELECT USING (
        (is_gp AND id = current_user_org_id())
        OR is_lp
        OR is_super_admin()
    );

-- Only super admins can modify organizations
CREATE POLICY "Super admins manage organizations" ON organizations
    FOR INSERT WITH CHECK (is_super_admin());

CREATE POLICY "Super admins update organizations" ON organizations
    FOR UPDATE USING (is_super_admin());

CREATE POLICY "Super admins delete organizations" ON organizations
    FOR DELETE USING (is_super_admin());

--------------------------------------------------------------------------------
-- GP Profiles Policies
--------------------------------------------------------------------------------

-- GP profiles visible to org members
CREATE POLICY "GP profiles visible to org" ON gp_profiles
    FOR SELECT USING (org_id = current_user_org_id() OR is_super_admin());

-- GP profiles editable by org admins
CREATE POLICY "GP profiles editable by admins" ON gp_profiles
    FOR INSERT WITH CHECK (
        (org_id = current_user_org_id() AND current_user_role() = 'admin')
        OR is_super_admin()
    );

CREATE POLICY "GP profiles updateable by admins" ON gp_profiles
    FOR UPDATE USING (
        (org_id = current_user_org_id() AND current_user_role() = 'admin')
        OR is_super_admin()
    );

CREATE POLICY "GP profiles deleteable by admins" ON gp_profiles
    FOR DELETE USING (
        (org_id = current_user_org_id() AND current_user_role() = 'admin')
        OR is_super_admin()
    );

--------------------------------------------------------------------------------
-- LP Profiles Policies
--------------------------------------------------------------------------------

-- All LP profiles readable by authenticated users
CREATE POLICY "LP profiles readable" ON lp_profiles
    FOR SELECT USING (auth.role() = 'authenticated');

-- Only super admins can modify LP profiles
CREATE POLICY "LP profiles insertable by admins" ON lp_profiles
    FOR INSERT WITH CHECK (is_super_admin());

CREATE POLICY "LP profiles updateable by admins" ON lp_profiles
    FOR UPDATE USING (is_super_admin());

CREATE POLICY "LP profiles deleteable by admins" ON lp_profiles
    FOR DELETE USING (is_super_admin());

--------------------------------------------------------------------------------
-- People Policies
--------------------------------------------------------------------------------

-- All authenticated users can read people (shared contact database)
CREATE POLICY "People readable by authenticated" ON people
    FOR SELECT USING (auth.role() = 'authenticated');

-- Users can update their own profile, super admins can update anyone
CREATE POLICY "People editable" ON people
    FOR UPDATE USING (
        auth_user_id = auth.uid()
        OR is_super_admin()
    );

-- Only super admins can insert new people
CREATE POLICY "People insertable by admins" ON people
    FOR INSERT WITH CHECK (is_super_admin());

-- Only super admins can delete people
CREATE POLICY "People deleteable by admins" ON people
    FOR DELETE USING (is_super_admin());

--------------------------------------------------------------------------------
-- Employment Policies
--------------------------------------------------------------------------------

-- Readable by all authenticated
CREATE POLICY "Employment readable by authenticated" ON employment
    FOR SELECT USING (auth.role() = 'authenticated');

-- Editable by super admins
CREATE POLICY "Employment insertable by admins" ON employment
    FOR INSERT WITH CHECK (is_super_admin());

CREATE POLICY "Employment updateable by admins" ON employment
    FOR UPDATE USING (is_super_admin());

CREATE POLICY "Employment deleteable by admins" ON employment
    FOR DELETE USING (is_super_admin());

--------------------------------------------------------------------------------
-- Invitations Policies
--------------------------------------------------------------------------------

-- Visible to org admins
CREATE POLICY "Invitations visible to org admins" ON invitations
    FOR SELECT USING (
        (org_id = current_user_org_id() AND current_user_role() = 'admin')
        OR is_super_admin()
    );

-- Org admins can create invitations
CREATE POLICY "Invitations created by org admins" ON invitations
    FOR INSERT WITH CHECK (
        (org_id = current_user_org_id() AND current_user_role() = 'admin')
        OR is_super_admin()
    );

-- Org admins can update invitations
CREATE POLICY "Invitations updated by org admins" ON invitations
    FOR UPDATE USING (
        (org_id = current_user_org_id() AND current_user_role() = 'admin')
        OR is_super_admin()
    );

--------------------------------------------------------------------------------
-- Funds Policies
--------------------------------------------------------------------------------

-- Users manage their org's funds
CREATE POLICY "Users see own org funds" ON funds
    FOR SELECT USING (org_id = current_user_org_id() OR is_super_admin());

CREATE POLICY "Users create org funds" ON funds
    FOR INSERT WITH CHECK (org_id = current_user_org_id() OR is_super_admin());

CREATE POLICY "Users update org funds" ON funds
    FOR UPDATE USING (org_id = current_user_org_id() OR is_super_admin());

CREATE POLICY "Users delete org funds" ON funds
    FOR DELETE USING (
        (org_id = current_user_org_id() AND current_user_role() = 'admin')
        OR is_super_admin()
    );

--------------------------------------------------------------------------------
-- Fund Team Policies
--------------------------------------------------------------------------------

-- Visible to org members
CREATE POLICY "Fund team visible to org" ON fund_team
    FOR SELECT USING (
        fund_id IN (SELECT id FROM funds WHERE org_id = current_user_org_id())
        OR is_super_admin()
    );

-- Managed by org admins
CREATE POLICY "Fund team insertable by admins" ON fund_team
    FOR INSERT WITH CHECK (
        (fund_id IN (SELECT id FROM funds WHERE org_id = current_user_org_id())
         AND current_user_role() = 'admin')
        OR is_super_admin()
    );

CREATE POLICY "Fund team updateable by admins" ON fund_team
    FOR UPDATE USING (
        (fund_id IN (SELECT id FROM funds WHERE org_id = current_user_org_id())
         AND current_user_role() = 'admin')
        OR is_super_admin()
    );

CREATE POLICY "Fund team deleteable by admins" ON fund_team
    FOR DELETE USING (
        (fund_id IN (SELECT id FROM funds WHERE org_id = current_user_org_id())
         AND current_user_role() = 'admin')
        OR is_super_admin()
    );

--------------------------------------------------------------------------------
-- Investments Policies
--------------------------------------------------------------------------------

-- Readable by all authenticated (historical data)
CREATE POLICY "Investments readable" ON investments
    FOR SELECT USING (auth.role() = 'authenticated');

-- Editable by super admins only
CREATE POLICY "Investments insertable by admins" ON investments
    FOR INSERT WITH CHECK (is_super_admin());

CREATE POLICY "Investments updateable by admins" ON investments
    FOR UPDATE USING (is_super_admin());

CREATE POLICY "Investments deleteable by admins" ON investments
    FOR DELETE USING (is_super_admin());

--------------------------------------------------------------------------------
-- Fund-LP Matches Policies
--------------------------------------------------------------------------------

-- GP users see matches for their funds
CREATE POLICY "Users see own matches" ON fund_lp_matches
    FOR SELECT USING (
        fund_id IN (SELECT id FROM funds WHERE org_id = current_user_org_id())
        OR is_super_admin()
    );

-- System (via service role) creates/updates matches
CREATE POLICY "System creates matches" ON fund_lp_matches
    FOR INSERT WITH CHECK (is_super_admin());

CREATE POLICY "System updates matches" ON fund_lp_matches
    FOR UPDATE USING (is_super_admin());

CREATE POLICY "System deletes matches" ON fund_lp_matches
    FOR DELETE USING (is_super_admin());

--------------------------------------------------------------------------------
-- Fund-LP Status Policies
--------------------------------------------------------------------------------

-- GP users see status for their funds
CREATE POLICY "Users see own fund status" ON fund_lp_status
    FOR SELECT USING (
        fund_id IN (SELECT id FROM funds WHERE org_id = current_user_org_id())
        OR is_super_admin()
    );

-- GP users can manage status for their funds
CREATE POLICY "Users create fund status" ON fund_lp_status
    FOR INSERT WITH CHECK (
        fund_id IN (SELECT id FROM funds WHERE org_id = current_user_org_id())
        OR is_super_admin()
    );

CREATE POLICY "Users update fund status" ON fund_lp_status
    FOR UPDATE USING (
        fund_id IN (SELECT id FROM funds WHERE org_id = current_user_org_id())
        OR is_super_admin()
    );

--------------------------------------------------------------------------------
-- Pitches Policies
--------------------------------------------------------------------------------

-- Users see pitches for their matches
CREATE POLICY "Users see own pitches" ON pitches
    FOR SELECT USING (
        match_id IN (
            SELECT m.id FROM fund_lp_matches m
            JOIN funds f ON m.fund_id = f.id
            WHERE f.org_id = current_user_org_id()
        )
        OR is_super_admin()
    );

CREATE POLICY "Users create pitches" ON pitches
    FOR INSERT WITH CHECK (
        match_id IN (
            SELECT m.id FROM fund_lp_matches m
            JOIN funds f ON m.fund_id = f.id
            WHERE f.org_id = current_user_org_id()
        )
        OR is_super_admin()
    );

--------------------------------------------------------------------------------
-- Outreach Events Policies
--------------------------------------------------------------------------------

CREATE POLICY "Users see own outreach events" ON outreach_events
    FOR SELECT USING (
        match_id IN (
            SELECT m.id FROM fund_lp_matches m
            JOIN funds f ON m.fund_id = f.id
            WHERE f.org_id = current_user_org_id()
        )
        OR is_super_admin()
    );

CREATE POLICY "Users create outreach events" ON outreach_events
    FOR INSERT WITH CHECK (
        match_id IN (
            SELECT m.id FROM fund_lp_matches m
            JOIN funds f ON m.fund_id = f.id
            WHERE f.org_id = current_user_org_id()
        )
        OR is_super_admin()
    );

--------------------------------------------------------------------------------
-- Match Outcomes Policies
--------------------------------------------------------------------------------

CREATE POLICY "Users see own match outcomes" ON match_outcomes
    FOR SELECT USING (
        match_id IN (
            SELECT m.id FROM fund_lp_matches m
            JOIN funds f ON m.fund_id = f.id
            WHERE f.org_id = current_user_org_id()
        )
        OR is_super_admin()
    );

CREATE POLICY "Users create match outcomes" ON match_outcomes
    FOR INSERT WITH CHECK (
        match_id IN (
            SELECT m.id FROM fund_lp_matches m
            JOIN funds f ON m.fund_id = f.id
            WHERE f.org_id = current_user_org_id()
        )
        OR is_super_admin()
    );

CREATE POLICY "Users update match outcomes" ON match_outcomes
    FOR UPDATE USING (
        match_id IN (
            SELECT m.id FROM fund_lp_matches m
            JOIN funds f ON m.fund_id = f.id
            WHERE f.org_id = current_user_org_id()
        )
        OR is_super_admin()
    );

--------------------------------------------------------------------------------
-- LP Match Preferences Policies
--------------------------------------------------------------------------------

-- Readable by all authenticated
CREATE POLICY "LP preferences readable" ON lp_match_preferences
    FOR SELECT USING (auth.role() = 'authenticated');

-- Editable by super admins
CREATE POLICY "LP preferences insertable by admins" ON lp_match_preferences
    FOR INSERT WITH CHECK (is_super_admin());

CREATE POLICY "LP preferences updateable by admins" ON lp_match_preferences
    FOR UPDATE USING (is_super_admin());

--------------------------------------------------------------------------------
-- Relationships Policies
--------------------------------------------------------------------------------

-- Users see relationships involving their org
CREATE POLICY "Users see own relationships" ON relationships
    FOR SELECT USING (
        gp_org_id = current_user_org_id()
        OR is_super_admin()
    );

CREATE POLICY "Users create relationships" ON relationships
    FOR INSERT WITH CHECK (
        gp_org_id = current_user_org_id()
        OR is_super_admin()
    );

CREATE POLICY "Users update relationships" ON relationships
    FOR UPDATE USING (
        gp_org_id = current_user_org_id()
        OR is_super_admin()
    );

--------------------------------------------------------------------------------
-- Mutual Connections Policies
--------------------------------------------------------------------------------

-- Readable by all authenticated
CREATE POLICY "Mutual connections readable" ON mutual_connections
    FOR SELECT USING (auth.role() = 'authenticated');

-- Editable by super admins
CREATE POLICY "Mutual connections insertable by admins" ON mutual_connections
    FOR INSERT WITH CHECK (is_super_admin());

CREATE POLICY "Mutual connections updateable by admins" ON mutual_connections
    FOR UPDATE USING (is_super_admin());
