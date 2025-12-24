# M1b: IR Team Core

**"IR team can look up contacts and log interactions"**

> **Position:** Immediately after M1 (Auth + Search), before M2 (Semantic)

---

## Business Value

> **Why this matters:** The IR team starts using the platform immediately. They become power users before GPs/LPs even see the product. Their daily usage validates the product and generates relationship data.

**Strategic Benefits:**
1. **Internal dogfooding** - IR team finds issues before customers
2. **Relationship data** - Touchpoints create training data for AI
3. **Sales demo material** - IR shows real usage to prospects
4. **Early revenue justification** - Platform is useful before AI features

---

## What We Build

### 1. Contact Quick Lookup
- Search any person/organization
- Mobile-first profile card
- Key facts + recent activity
- Works with basic full-text search (M1)

### 2. Event Management
- Create events (conference, dinner, summit)
- Add/remove attendees
- Basic attendee list view
- Link attendees to existing GP/LP organizations

### 3. Touchpoint Logging
- Log meeting, call, email, event interaction
- Note content + sentiment
- Create follow-up task
- View timeline per contact

### 4. Task Management
- Task list with due dates
- Assign to team members
- Mark complete
- Filter by contact/event

### 5. IR Dashboard
- Today's tasks
- Upcoming events
- Recent touchpoints
- Quick search bar

---

## Why This Can Come Early

| Dependency | Status After M1 |
|------------|-----------------|
| Auth | ✅ Available |
| Basic search | ✅ Available |
| Database | ✅ Available |
| Multi-tenancy (RLS) | ✅ Available |
| Semantic search | ❌ Not needed yet |
| 42-agent matching | ❌ Not needed yet |
| Pitch generation | ❌ Not needed yet |

---

## New Database Tables

```sql
-- Events
CREATE TABLE events (
    id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    name TEXT NOT NULL,
    event_type TEXT, -- conference, dinner, summit, etc.
    start_date DATE,
    end_date DATE,
    city TEXT,
    country TEXT,
    status TEXT DEFAULT 'planning',
    notes TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Event Attendance
CREATE TABLE event_attendance (
    id UUID PRIMARY KEY,
    event_id UUID REFERENCES events(id),
    person_id UUID, -- or company_id
    company_id UUID,
    registration_status TEXT DEFAULT 'registered',
    priority_level TEXT, -- must_meet, should_meet, etc.
    notes TEXT
);

-- Touchpoints (interactions)
CREATE TABLE touchpoints (
    id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    person_id UUID,
    company_id UUID,
    event_id UUID REFERENCES events(id),
    touchpoint_type TEXT NOT NULL, -- meeting, call, email, etc.
    occurred_at TIMESTAMPTZ NOT NULL,
    summary TEXT,
    sentiment TEXT, -- positive, neutral, negative
    follow_up_required BOOLEAN DEFAULT FALSE,
    created_by UUID REFERENCES people(id),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Tasks
CREATE TABLE tasks (
    id UUID PRIMARY KEY,
    org_id UUID REFERENCES organizations(id),
    title TEXT NOT NULL,
    description TEXT,
    person_id UUID,
    company_id UUID,
    event_id UUID,
    touchpoint_id UUID REFERENCES touchpoints(id),
    assigned_to UUID REFERENCES people(id),
    due_date DATE,
    status TEXT DEFAULT 'pending',
    completed_at TIMESTAMPTZ
);
```

---

## Deliverables

### API Endpoints
- [ ] CRUD: `/api/v1/events`
- [ ] CRUD: `/api/v1/events/{id}/attendees`
- [ ] CRUD: `/api/v1/touchpoints`
- [ ] CRUD: `/api/v1/tasks`
- [ ] GET: `/api/v1/contacts/search` (quick lookup)
- [ ] GET: `/api/v1/contacts/{id}/card` (profile card)
- [ ] GET: `/api/v1/contacts/{id}/timeline` (touchpoints)

### UI Screens
- [ ] IR Dashboard (home for IR users)
- [ ] Contact search + profile card
- [ ] Event list and create/edit
- [ ] Attendee management
- [ ] Touchpoint log form
- [ ] Task list
- [ ] Contact timeline

---

## User Stories

```gherkin
As an IR team member,
I want to quickly look up any contact
So that I'm prepared for conversations.
```

```gherkin
As an IR team member,
I want to log a meeting I just had
So that the team knows what was discussed.
```

```gherkin
As an IR team member,
I want to create follow-up tasks
So that nothing falls through the cracks.
```

```gherkin
As an IR team manager,
I want to see upcoming events and who's attending
So that I can prioritize outreach.
```

---

## Exit Criteria

- [ ] IR user can search contacts (people + organizations)
- [ ] IR user can view profile card on mobile
- [ ] IR user can create events and manage attendees
- [ ] IR user can log touchpoints with notes
- [ ] IR user can create and complete tasks
- [ ] IR dashboard shows today's priorities
- [ ] Live on lpxgp.com

---

## Demo Script

```
1. Login as IR team member
2. Quick search: "John Smith"
3. View profile card (mobile-friendly)
4. See: title, company, contact info
5. Create event: "Q1 LP Summit"
6. Add attendees (search + add)
7. After meeting: Log touchpoint
8. Create follow-up task: "Send materials"
9. View IR dashboard - see tasks
10. Complete task
```

---

## What This Enables

After M1b, IR team can:
- ✅ Look up any contact before meetings
- ✅ Track all events they're managing
- ✅ Log every interaction
- ✅ Never forget follow-ups

What IR team can't do yet (needs later milestones):
- ❌ AI-generated briefing books (M3+)
- ❌ Relationship scoring (M3+)
- ❌ Entity Resolution / deduplication (M9)
- ❌ Data import from external sources (M9)

---

## Consequences of Building This Early

**Positive:**
1. IR team starts using platform daily from week 2-3
2. Touchpoint data improves future AI features
3. Event data enables M3 to consider "met at event" signals
4. Platform proves value before complex AI is ready

**Negative:**
1. IR team sees unfinished product (missing AI features)
2. Data might be messy (no Entity Resolution yet)
3. Profile cards are basic (no AI insights)

**Mitigation:**
- Set expectations: "This is the foundation"
- Use data quality flags to track incomplete records
- Add AI features incrementally to same screens

---

## Relationship to Other Milestones

```
M0 (Setup)
 |
 +-- M1 (Auth + Search)
      |
      +-- M1b (IR Core) ← NEW: Insert here
      |
      +-- M2 (Semantic Search)
           |
           +-- M3 (Matching) → enhances IR with AI insights
                |
                +-- M4 (Pitch) → adds briefing book generation
                     |
                     +-- ... M5, M6, M7, M8 ...
                          |
                          +-- M9 (IR Advanced) → Entity Resolution, MDM
```

---

## Does IR Team Need Their Own Interface?

**Yes, partially.** IR has unique screens:

| Screen | IR Only? | Shared With |
|--------|----------|-------------|
| IR Dashboard | Yes | - |
| Event Management | Yes | - |
| Touchpoint Logger | Yes | - |
| Task List | Yes | - |
| Contact Profile Card | Shared | GP, LP |
| Contact Search | Shared | GP, LP |
| Organization Profile | Shared | GP, LP, Admin |

**Implementation:**
- Same codebase, different navigation
- Role-based menu: IR sees IR dashboard, GP sees GP dashboard
- Shared components for profiles, search

---

[← M1: Auth + Search](m1-auth-search.md) | [Index](index.md) | [M2: Semantic Search →](m2-semantic.md)
