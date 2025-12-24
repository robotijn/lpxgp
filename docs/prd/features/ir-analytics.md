# IR & Analytics Features

[← Back to Index](index.md)

---

## Overview

Investor Relations (IR) and Analytics features support the IR team's daily operations and provide advanced data management capabilities.

**Milestones:**
- M1b: IR Core (contacts, events, touchpoints, tasks)
- M9: IR Advanced (entity resolution, briefing books, relationship intelligence)

---

## IR Core Features (M1b)

### F-IR-01: Contact Search [P0]

**Description:** Quick lookup of any contact in the database.

**Capabilities:**
- Search by name, organization, or partial match
- Results within 1 second
- Mobile-optimized profile cards
- Shows name, title, organization, relationship history

**Tables:** `people`, `employment`, `organizations`

---

### F-IR-02: Event CRUD [P0]

**Description:** Create, read, update, and delete events (conferences, dinners, meetings).

**Capabilities:**
- Create events with name, type, dates, location
- Edit and delete events
- View upcoming vs past events
- Filter by status

**Tables:** `events`

---

### F-IR-03: Attendee Management [P0]

**Description:** Track who attended which events.

**Capabilities:**
- Add attendees to events
- Track attendance status (confirmed, attended, no-show)
- View attendee lists per event
- View events per contact

**Tables:** `event_attendance`, `people`, `events`

---

### F-IR-04: Log Interactions [P0]

**Description:** Record touchpoints (calls, meetings, emails) with contacts.

**Capabilities:**
- Log interaction type, date, summary
- Link to contacts and organizations
- View interaction history per contact
- Search interactions

**Tables:** `touchpoints`, `people`, `organizations`

---

### F-IR-05: Task CRUD [P0]

**Description:** Create and manage follow-up tasks.

**Capabilities:**
- Create tasks with due date and priority
- Assign to team members
- Link to contacts or events
- Track completion status

**Tables:** `tasks`, `people`

---

### F-IR-06: Dashboard Overview [P0]

**Description:** IR team dashboard with key metrics and upcoming items.

**Capabilities:**
- Upcoming events and meetings
- Outstanding tasks
- Recent interactions
- Quick access to frequent contacts

**Tables:** `events`, `tasks`, `touchpoints`

---

## Entity Resolution Features (M9)

### F-ER-01: Data Import [P1]

**Description:** Import contacts from external sources (CSV, Excel, APIs).

**Capabilities:**
- Upload CSV/Excel files
- Column mapping to database fields
- Progress tracking
- Error handling and reporting

**Tables:** `people`, `employment`, `organizations`

---

### F-ER-02: Human Review Queue [P1]

**Description:** Review uncertain entity matches for data quality.

**Capabilities:**
- Side-by-side record comparison
- Confidence score display
- Merge or keep separate actions
- Edit before merge option
- Queue prioritization

**Tables:** `people` (with merge tracking)

---

### F-ER-03: Golden Record Management [P1]

**Description:** Manage merged records with field provenance.

**Capabilities:**
- Track which source contributed each field
- View merge history
- Undo merges if needed
- Data quality scoring

**Tables:** `people`, audit tables

---

## Briefing Book Features (M9)

### F-BB-01: Briefing Book Generation [P1]

**Description:** AI-generated briefing materials for meetings.

**Capabilities:**
- Generate pre-meeting briefing for any contact
- Include relationship history, recent news, talking points
- PDF export
- Scheduled generation before events

**Tables:** `people`, `touchpoints`, `events`, `organizations`

---

### F-BB-02: Talking Points Generation [P1]

**Description:** AI-suggested talking points based on relationship context.

**Capabilities:**
- Context-aware suggestions
- Based on past interactions and shared connections
- Customizable by meeting type
- Team review before use

**Tables:** `touchpoints`, `mutual_connections`, `relationships`

---

## Relationship Intelligence Features (M9)

### F-RI-01: Relationship Scoring [P1]

**Description:** Algorithmic scoring of relationship strength.

**Capabilities:**
- Score based on recency, frequency, depth of interactions
- Track relationship trends over time
- Identify strengthening/weakening relationships
- Prioritize outreach

**Tables:** `relationships`, `touchpoints`, `people`

---

### F-RI-02: Priority Queue [P1]

**Description:** Prioritized list of contacts needing attention.

**Capabilities:**
- Surface contacts with declining relationship scores
- Upcoming event attendees needing prep
- Overdue follow-ups
- New connections to nurture

**Tables:** `relationships`, `tasks`, `event_attendance`

---

## Advanced Analytics Features (M9)

### F-AA-01: Event ROI Tracking [P2]

**Description:** Track return on investment for events.

**Capabilities:**
- Cost per event
- Leads generated
- Meetings resulted
- Commitments influenced

**Tables:** `events`, `investments`, `touchpoints`

---

### F-AA-02: Data Quality Dashboard [P2]

**Description:** Monitor and improve data quality across the platform.

**Capabilities:**
- Quality scores by entity type
- Stale data identification
- Missing field reports
- Duplicate detection metrics
- Import success rates

**Tables:** All tables (meta-analysis)

---

## Related Documents

- [M1b IR Core Tests](../tests/m1b-ir-core.feature.md)
- [M9 IR Advanced Tests](../tests/m9-ir-advanced.feature.md)
- [Data Model](../data-model.md)

---

[← Back to Index](index.md)
