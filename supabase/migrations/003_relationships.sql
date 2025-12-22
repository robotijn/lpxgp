-- LPxGP Relationships Schema Migration
-- Investments, Fund-LP Matches, Fund-LP Status, Pitches, Outreach

--------------------------------------------------------------------------------
-- Investments (Historical Facts)
-- Tracks historical LP investments in GP funds. These are FACTS, not recommendations.
--------------------------------------------------------------------------------
CREATE TABLE investments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    lp_org_id       UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    fund_id         UUID NOT NULL REFERENCES funds(id) ON DELETE CASCADE,

    commitment_mm   DECIMAL(12,2),
    commitment_date DATE,

    -- Data provenance
    source          TEXT CHECK (source IN ('disclosed', 'public', 'estimated', 'imported')) DEFAULT 'imported',
    confidence      TEXT CHECK (confidence IN ('confirmed', 'likely', 'rumored')) DEFAULT 'confirmed',

    created_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(lp_org_id, fund_id)
);

CREATE INDEX idx_investments_lp ON investments(lp_org_id);
CREATE INDEX idx_investments_fund ON investments(fund_id);

--------------------------------------------------------------------------------
-- Fund-LP Matches (AI Recommendations)
-- System-generated match recommendations between funds and LPs.
--------------------------------------------------------------------------------
CREATE TABLE fund_lp_matches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    fund_id         UUID NOT NULL REFERENCES funds(id) ON DELETE CASCADE,
    lp_org_id       UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Scoring
    score           DECIMAL(5,2) NOT NULL,
    score_breakdown JSONB DEFAULT '{}',

    -- AI-generated content
    explanation     TEXT,
    talking_points  TEXT[] DEFAULT '{}',
    concerns        TEXT[] DEFAULT '{}',

    -- Source
    debate_id       UUID,           -- FK to agent_debates when implemented
    model_version   TEXT,

    -- Validity
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ,    -- Matches can become stale

    UNIQUE(fund_id, lp_org_id)
);

CREATE INDEX idx_fund_lp_matches_fund ON fund_lp_matches(fund_id);
CREATE INDEX idx_fund_lp_matches_lp ON fund_lp_matches(lp_org_id);
CREATE INDEX idx_fund_lp_matches_score ON fund_lp_matches(score DESC);

--------------------------------------------------------------------------------
-- Fund-LP Status (User-Expressed Interest)
-- Tracks GP and LP interest/rejection separately.
--------------------------------------------------------------------------------
CREATE TABLE fund_lp_status (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    fund_id         UUID NOT NULL REFERENCES funds(id) ON DELETE CASCADE,
    lp_org_id       UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- GP side
    gp_interest     TEXT CHECK (gp_interest IN ('interested', 'not_interested', 'pursuing')),
    gp_interest_reason TEXT,
    gp_interest_by  UUID REFERENCES people(id),
    gp_interest_at  TIMESTAMPTZ,

    -- LP side
    lp_interest     TEXT CHECK (lp_interest IN ('interested', 'not_interested', 'reviewing')),
    lp_interest_reason TEXT,
    lp_interest_by  UUID REFERENCES people(id),
    lp_interest_at  TIMESTAMPTZ,

    -- Pipeline stage (can be computed or set manually)
    pipeline_stage  TEXT CHECK (pipeline_stage IN (
        'recommended',      -- System recommended, no action
        'gp_interested',    -- GP marked interest
        'gp_pursuing',      -- GP actively reaching out
        'lp_reviewing',     -- LP is evaluating
        'mutual_interest',  -- Both interested
        'in_diligence',     -- Active DD process
        'gp_passed',        -- GP decided not to pursue
        'lp_passed',        -- LP declined
        'invested'          -- Commitment made
    )) DEFAULT 'recommended',

    -- Notes
    notes           TEXT,

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(fund_id, lp_org_id)
);

CREATE INDEX idx_fund_lp_status_fund ON fund_lp_status(fund_id);
CREATE INDEX idx_fund_lp_status_lp ON fund_lp_status(lp_org_id);
CREATE INDEX idx_fund_lp_status_pipeline ON fund_lp_status(pipeline_stage);
CREATE INDEX idx_fund_lp_status_gp_interest ON fund_lp_status(gp_interest) WHERE gp_interest IS NOT NULL;
CREATE INDEX idx_fund_lp_status_lp_interest ON fund_lp_status(lp_interest) WHERE lp_interest IS NOT NULL;

--------------------------------------------------------------------------------
-- Generated Pitches
--------------------------------------------------------------------------------
CREATE TABLE pitches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id        UUID NOT NULL REFERENCES fund_lp_matches(id) ON DELETE CASCADE,

    type            TEXT CHECK (type IN ('email', 'summary', 'addendum')) NOT NULL,
    content         TEXT NOT NULL,
    tone            TEXT,

    created_by      UUID REFERENCES people(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pitches_match ON pitches(match_id);

--------------------------------------------------------------------------------
-- Outreach Events (Outcome Tracking)
--------------------------------------------------------------------------------
CREATE TABLE outreach_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id        UUID NOT NULL REFERENCES fund_lp_matches(id) ON DELETE CASCADE,

    event_type      TEXT NOT NULL CHECK (event_type IN (
        'pitch_generated',
        'email_sent',
        'email_opened',
        'response_received',
        'meeting_scheduled',
        'meeting_held',
        'follow_up_sent',
        'due_diligence_started',
        'term_sheet_received',
        'commitment_made',
        'commitment_declined'
    )),

    event_date      TIMESTAMPTZ NOT NULL,
    notes           TEXT,

    -- For meetings
    meeting_type    TEXT,  -- intro_call, deep_dive, dd_session, closing
    attendees       UUID[],  -- people IDs

    created_by      UUID REFERENCES people(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_outreach_events_match ON outreach_events(match_id);
CREATE INDEX idx_outreach_events_type ON outreach_events(event_type);
CREATE INDEX idx_outreach_events_date ON outreach_events(event_date);

--------------------------------------------------------------------------------
-- Match Outcomes (Training Data)
--------------------------------------------------------------------------------
CREATE TABLE match_outcomes (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id            UUID NOT NULL REFERENCES fund_lp_matches(id) UNIQUE,

    -- Outcome
    outcome             TEXT NOT NULL CHECK (outcome IN (
        'committed',
        'declined_after_meeting',
        'declined_before_meeting',
        'no_response',
        'not_contacted',
        'in_progress'
    )),

    -- If committed
    commitment_amount_mm DECIMAL(12,2),
    commitment_date     DATE,

    -- If declined
    decline_reason      TEXT,
    decline_stage       TEXT,

    -- Quality signals
    time_to_first_response INTERVAL,
    time_to_outcome     INTERVAL,
    total_meetings      INTEGER,

    -- For training: snapshot of all scoring inputs at match time
    features_at_match_time JSONB,

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_match_outcomes_outcome ON match_outcomes(outcome);
CREATE INDEX idx_match_outcomes_date ON match_outcomes(commitment_date);

--------------------------------------------------------------------------------
-- LP Match Preferences (Bidirectional Matching)
--------------------------------------------------------------------------------
CREATE TABLE lp_match_preferences (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lp_org_id               UUID NOT NULL REFERENCES organizations(id),

    -- LP can set active search parameters
    actively_looking        BOOLEAN DEFAULT FALSE,
    allocation_available_mm DECIMAL(12,2),
    target_close_date       DATE,

    -- Notification preferences
    notify_on_new_funds     BOOLEAN DEFAULT TRUE,
    min_match_score         INTEGER DEFAULT 70,

    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_lp_match_preferences_org ON lp_match_preferences(lp_org_id);
CREATE INDEX idx_lp_match_preferences_active ON lp_match_preferences(actively_looking) WHERE actively_looking = TRUE;

--------------------------------------------------------------------------------
-- Relationships (GP-LP Intelligence)
--------------------------------------------------------------------------------
CREATE TABLE relationships (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gp_org_id           UUID NOT NULL REFERENCES organizations(id),
    lp_org_id           UUID NOT NULL REFERENCES organizations(id),

    -- Relationship status
    relationship_type   TEXT CHECK (relationship_type IN (
        'existing_investor',
        'warm_connection',
        'mutual_connection',
        'cold'
    )),

    -- History
    prior_commitments   INTEGER DEFAULT 0,
    total_committed_mm  DECIMAL(12,2),
    last_meeting_date   DATE,
    relationship_strength INTEGER CHECK (relationship_strength BETWEEN 1 AND 5),

    -- Key contacts
    primary_contact_id  UUID REFERENCES people(id),

    notes               TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(gp_org_id, lp_org_id)
);

CREATE INDEX idx_relationships_gp ON relationships(gp_org_id);
CREATE INDEX idx_relationships_lp ON relationships(lp_org_id);
CREATE INDEX idx_relationships_type ON relationships(relationship_type);

--------------------------------------------------------------------------------
-- Mutual Connections
--------------------------------------------------------------------------------
CREATE TABLE mutual_connections (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gp_person_id        UUID NOT NULL REFERENCES people(id),
    lp_person_id        UUID NOT NULL REFERENCES people(id),

    connection_type     TEXT,  -- former_colleagues, board_together, etc.
    connection_strength INTEGER CHECK (connection_strength BETWEEN 1 AND 5),

    notes               TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_mutual_connections_gp ON mutual_connections(gp_person_id);
CREATE INDEX idx_mutual_connections_lp ON mutual_connections(lp_person_id);

--------------------------------------------------------------------------------
-- Updated_at triggers
--------------------------------------------------------------------------------
CREATE TRIGGER update_fund_lp_status_updated_at BEFORE UPDATE ON fund_lp_status
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_lp_match_preferences_updated_at BEFORE UPDATE ON lp_match_preferences
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

CREATE TRIGGER update_relationships_updated_at BEFORE UPDATE ON relationships
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
