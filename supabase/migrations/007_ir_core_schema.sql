-- LPxGP IR Core Schema (M1b)
-- Events, touchpoints, tasks for IR team

--------------------------------------------------------------------------------
-- Events Table
-- Conferences, dinners, summits managed by IR team
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Event details
    name TEXT NOT NULL,
    event_type TEXT CHECK (event_type IN (
        'conference', 'summit', 'dinner', 'roadshow',
        'webinar', 'meeting', 'call', 'other'
    )),
    description TEXT,

    -- Dates and location
    start_date DATE,
    end_date DATE,
    city TEXT,
    country TEXT,
    venue TEXT,
    is_virtual BOOLEAN DEFAULT FALSE,

    -- Status tracking
    status TEXT DEFAULT 'planning' CHECK (status IN (
        'planning', 'confirmed', 'in_progress', 'completed', 'cancelled'
    )),

    -- IR team notes
    notes TEXT,
    budget_usd DECIMAL(12,2),

    -- M9: Enhanced fields (added later)
    briefing_book_id UUID,  -- Link to generated briefing book
    roi_score DECIMAL(3,2), -- 0.00 - 5.00

    -- Metadata
    created_by UUID REFERENCES people(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_events_org ON events(org_id);
CREATE INDEX IF NOT EXISTS idx_events_start_date ON events(start_date);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);

-- RLS
ALTER TABLE events ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see own org events" ON events
    FOR SELECT USING (org_id = current_user_org_id() OR is_privileged_user());

CREATE POLICY "Users create org events" ON events
    FOR INSERT WITH CHECK (org_id = current_user_org_id() OR is_privileged_user());

CREATE POLICY "Users update org events" ON events
    FOR UPDATE USING (org_id = current_user_org_id() OR is_privileged_user());

CREATE POLICY "Admins delete org events" ON events
    FOR DELETE USING (
        (org_id = current_user_org_id() AND current_user_role() IN ('admin', 'fund_admin'))
        OR is_super_admin()
    );

--------------------------------------------------------------------------------
-- Event Attendance Table
-- Who is attending / attended each event
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS event_attendance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    event_id UUID NOT NULL REFERENCES events(id) ON DELETE CASCADE,

    -- Attendee (either person or company)
    person_id UUID REFERENCES people(id) ON DELETE CASCADE,
    company_id UUID REFERENCES organizations(id) ON DELETE CASCADE,

    -- Registration
    registration_status TEXT DEFAULT 'registered' CHECK (registration_status IN (
        'invited', 'registered', 'confirmed', 'attended', 'no_show', 'cancelled'
    )),

    -- IR priority
    priority_level TEXT CHECK (priority_level IN (
        'must_meet', 'should_meet', 'nice_to_meet', 'avoid'
    )),

    -- Notes
    notes TEXT,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- At least one of person_id or company_id required
    CONSTRAINT attendee_required CHECK (person_id IS NOT NULL OR company_id IS NOT NULL)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_attendance_event ON event_attendance(event_id);
CREATE INDEX IF NOT EXISTS idx_attendance_person ON event_attendance(person_id);
CREATE INDEX IF NOT EXISTS idx_attendance_company ON event_attendance(company_id);
CREATE INDEX IF NOT EXISTS idx_attendance_priority ON event_attendance(priority_level);

-- RLS (inherits from events)
ALTER TABLE event_attendance ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see attendance for own org events" ON event_attendance
    FOR SELECT USING (
        event_id IN (SELECT id FROM events WHERE org_id = current_user_org_id())
        OR is_privileged_user()
    );

CREATE POLICY "Users manage attendance for own org events" ON event_attendance
    FOR INSERT WITH CHECK (
        event_id IN (SELECT id FROM events WHERE org_id = current_user_org_id())
        OR is_privileged_user()
    );

CREATE POLICY "Users update attendance for own org events" ON event_attendance
    FOR UPDATE USING (
        event_id IN (SELECT id FROM events WHERE org_id = current_user_org_id())
        OR is_privileged_user()
    );

CREATE POLICY "Users delete attendance for own org events" ON event_attendance
    FOR DELETE USING (
        event_id IN (SELECT id FROM events WHERE org_id = current_user_org_id())
        OR is_privileged_user()
    );

--------------------------------------------------------------------------------
-- Touchpoints Table
-- All interactions with contacts (meetings, calls, emails)
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS touchpoints (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Who was contacted
    person_id UUID REFERENCES people(id) ON DELETE SET NULL,
    company_id UUID REFERENCES organizations(id) ON DELETE SET NULL,

    -- Context (optional link to event)
    event_id UUID REFERENCES events(id) ON DELETE SET NULL,

    -- Interaction details
    touchpoint_type TEXT NOT NULL CHECK (touchpoint_type IN (
        'meeting', 'call', 'email', 'event_interaction',
        'video_call', 'linkedin', 'text', 'other'
    )),
    occurred_at TIMESTAMPTZ NOT NULL,
    duration_minutes INTEGER,

    -- Content
    summary TEXT,
    detailed_notes TEXT,

    -- Sentiment tracking
    sentiment TEXT CHECK (sentiment IN ('positive', 'neutral', 'negative', 'mixed')),

    -- Follow-up
    follow_up_required BOOLEAN DEFAULT FALSE,
    follow_up_date DATE,

    -- M9: AI-enhanced fields (populated later)
    ai_sentiment TEXT,           -- AI-analyzed sentiment
    ai_topics JSONB DEFAULT '[]', -- AI-extracted topics
    ai_key_points JSONB DEFAULT '[]', -- AI-extracted key points

    -- Metadata
    created_by UUID REFERENCES people(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- At least one contact required
    CONSTRAINT contact_required CHECK (person_id IS NOT NULL OR company_id IS NOT NULL)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_touchpoints_org ON touchpoints(org_id);
CREATE INDEX IF NOT EXISTS idx_touchpoints_person ON touchpoints(person_id);
CREATE INDEX IF NOT EXISTS idx_touchpoints_company ON touchpoints(company_id);
CREATE INDEX IF NOT EXISTS idx_touchpoints_event ON touchpoints(event_id);
CREATE INDEX IF NOT EXISTS idx_touchpoints_occurred ON touchpoints(occurred_at);
CREATE INDEX IF NOT EXISTS idx_touchpoints_type ON touchpoints(touchpoint_type);
CREATE INDEX IF NOT EXISTS idx_touchpoints_follow_up ON touchpoints(follow_up_required, follow_up_date);

-- RLS
ALTER TABLE touchpoints ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see own org touchpoints" ON touchpoints
    FOR SELECT USING (org_id = current_user_org_id() OR is_privileged_user());

CREATE POLICY "Users create org touchpoints" ON touchpoints
    FOR INSERT WITH CHECK (org_id = current_user_org_id() OR is_privileged_user());

CREATE POLICY "Users update org touchpoints" ON touchpoints
    FOR UPDATE USING (org_id = current_user_org_id() OR is_privileged_user());

CREATE POLICY "Admins delete org touchpoints" ON touchpoints
    FOR DELETE USING (
        (org_id = current_user_org_id() AND current_user_role() IN ('admin', 'fund_admin'))
        OR is_super_admin()
    );

--------------------------------------------------------------------------------
-- Tasks Table
-- Follow-up actions for IR team
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS tasks (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Task details
    title TEXT NOT NULL,
    description TEXT,

    -- Related entities
    person_id UUID REFERENCES people(id) ON DELETE SET NULL,
    company_id UUID REFERENCES organizations(id) ON DELETE SET NULL,
    event_id UUID REFERENCES events(id) ON DELETE SET NULL,
    touchpoint_id UUID REFERENCES touchpoints(id) ON DELETE SET NULL,

    -- Assignment
    assigned_to UUID REFERENCES people(id) ON DELETE SET NULL,
    assigned_by UUID REFERENCES people(id),

    -- Timeline
    due_date DATE,
    reminder_date DATE,

    -- Status
    status TEXT DEFAULT 'pending' CHECK (status IN (
        'pending', 'in_progress', 'completed', 'cancelled', 'deferred'
    )),
    priority TEXT DEFAULT 'medium' CHECK (priority IN (
        'low', 'medium', 'high', 'urgent'
    )),

    -- Completion
    completed_at TIMESTAMPTZ,
    completed_by UUID REFERENCES people(id),
    completion_notes TEXT,

    -- Metadata
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_tasks_org ON tasks(org_id);
CREATE INDEX IF NOT EXISTS idx_tasks_assigned ON tasks(assigned_to);
CREATE INDEX IF NOT EXISTS idx_tasks_due ON tasks(due_date);
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_priority ON tasks(priority);
CREATE INDEX IF NOT EXISTS idx_tasks_person ON tasks(person_id);
CREATE INDEX IF NOT EXISTS idx_tasks_event ON tasks(event_id);

-- RLS
ALTER TABLE tasks ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see own org tasks" ON tasks
    FOR SELECT USING (org_id = current_user_org_id() OR is_privileged_user());

CREATE POLICY "Users create org tasks" ON tasks
    FOR INSERT WITH CHECK (org_id = current_user_org_id() OR is_privileged_user());

CREATE POLICY "Users update own or assigned tasks" ON tasks
    FOR UPDATE USING (
        org_id = current_user_org_id()
        OR assigned_to = (SELECT id FROM people WHERE auth_user_id = auth.uid())
        OR is_privileged_user()
    );

CREATE POLICY "Admins delete org tasks" ON tasks
    FOR DELETE USING (
        (org_id = current_user_org_id() AND current_user_role() IN ('admin', 'fund_admin'))
        OR is_super_admin()
    );

--------------------------------------------------------------------------------
-- IR Notes Table
-- Internal notes visible only to IR team (not shared with contacts)
--------------------------------------------------------------------------------

CREATE TABLE IF NOT EXISTS ir_notes (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Subject of note
    person_id UUID REFERENCES people(id) ON DELETE CASCADE,
    company_id UUID REFERENCES organizations(id) ON DELETE CASCADE,

    -- Content
    note_type TEXT CHECK (note_type IN (
        'general', 'warning', 'opportunity', 'relationship', 'strategy'
    )),
    content TEXT NOT NULL,
    is_sensitive BOOLEAN DEFAULT FALSE,

    -- M9: Topics to avoid (for briefing books)
    is_topic_to_avoid BOOLEAN DEFAULT FALSE,

    -- Metadata
    created_by UUID REFERENCES people(id),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),

    -- At least one subject required
    CONSTRAINT note_subject_required CHECK (person_id IS NOT NULL OR company_id IS NOT NULL)
);

-- Indexes
CREATE INDEX IF NOT EXISTS idx_ir_notes_org ON ir_notes(org_id);
CREATE INDEX IF NOT EXISTS idx_ir_notes_person ON ir_notes(person_id);
CREATE INDEX IF NOT EXISTS idx_ir_notes_company ON ir_notes(company_id);
CREATE INDEX IF NOT EXISTS idx_ir_notes_avoid ON ir_notes(is_topic_to_avoid) WHERE is_topic_to_avoid = TRUE;

-- RLS
ALTER TABLE ir_notes ENABLE ROW LEVEL SECURITY;

CREATE POLICY "Users see own org IR notes" ON ir_notes
    FOR SELECT USING (org_id = current_user_org_id() OR is_privileged_user());

CREATE POLICY "Users create org IR notes" ON ir_notes
    FOR INSERT WITH CHECK (org_id = current_user_org_id() OR is_privileged_user());

CREATE POLICY "Users update org IR notes" ON ir_notes
    FOR UPDATE USING (org_id = current_user_org_id() OR is_privileged_user());

CREATE POLICY "Admins delete org IR notes" ON ir_notes
    FOR DELETE USING (
        (org_id = current_user_org_id() AND current_user_role() IN ('admin', 'fund_admin'))
        OR is_super_admin()
    );

--------------------------------------------------------------------------------
-- Update Triggers for updated_at
--------------------------------------------------------------------------------

CREATE OR REPLACE FUNCTION update_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

-- Apply to all IR tables
DROP TRIGGER IF EXISTS trg_events_updated ON events;
CREATE TRIGGER trg_events_updated
    BEFORE UPDATE ON events
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS trg_attendance_updated ON event_attendance;
CREATE TRIGGER trg_attendance_updated
    BEFORE UPDATE ON event_attendance
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS trg_touchpoints_updated ON touchpoints;
CREATE TRIGGER trg_touchpoints_updated
    BEFORE UPDATE ON touchpoints
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS trg_tasks_updated ON tasks;
CREATE TRIGGER trg_tasks_updated
    BEFORE UPDATE ON tasks
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

DROP TRIGGER IF EXISTS trg_ir_notes_updated ON ir_notes;
CREATE TRIGGER trg_ir_notes_updated
    BEFORE UPDATE ON ir_notes
    FOR EACH ROW EXECUTE FUNCTION update_updated_at();

--------------------------------------------------------------------------------
-- Comments
--------------------------------------------------------------------------------

COMMENT ON TABLE events IS 'IR team managed events (conferences, dinners, etc.)';
COMMENT ON TABLE event_attendance IS 'Who attended or will attend each event';
COMMENT ON TABLE touchpoints IS 'All interactions with contacts';
COMMENT ON TABLE tasks IS 'Follow-up actions for IR team';
COMMENT ON TABLE ir_notes IS 'Internal IR notes (not shared with contacts)';
