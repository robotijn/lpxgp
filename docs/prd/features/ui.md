# User Interface

[← Back to Features Index](index.md)

---

## F-UI-01: Dashboard [P0]

**Description:** User home screen with key information

**Requirements:**
- Company name in header with settings link
- Fund cards showing: name, status, size, key stats
- "New Fund" button (Admin/Member only)
- Recent activity feed (last 10 items)
- Quick action buttons: Search LPs, View Matches, Outreach Hub

### First-Time Welcome (Company Admin)
When a Company Admin logs in for the first time (no funds exist):
- Welcome message with company name
- Two prominent options:
  - "Create Your First Fund" (primary)
  - "Invite Team Members" (secondary)
- Quick tip explaining the platform workflow

### First-Time Welcome (Team Member)
When a team member logs in for the first time:
- Welcome message
- If company has funds → show dashboard with funds
- If no funds exist → message "Your admin is setting up the first fund"

### Dashboard Layout
```
┌─────────────────────────────────────────────────────────────────┐
│  [Company Name]                                [⚙️ Settings]    │
├─────────────────────────────────────────────────────────────────┤
│  YOUR FUNDS                                                     │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │ Fund Name          │  │ Fund Name          │  [+ New Fund]  │
│  │ Status · $XXM      │  │ Status · $XXM      │                │
│  │ XX matches         │  │ Closed             │                │
│  │ XX contacted       │  │                    │                │
│  │ [View Matches →]   │  │ [View Details →]   │                │
│  └────────────────────┘  └────────────────────┘                │
│                                                                 │
│  RECENT ACTIVITY                                                │
│  • [User] [action] [target] · [time ago]                       │
│  • ...                                                          │
│                                                                 │
│  QUICK ACTIONS                                                  │
│  [🔍 Search LPs]   [📊 View Matches]   [📧 Outreach Hub]       │
└─────────────────────────────────────────────────────────────────┘
```

**BDD Tests (must pass):**

| Test File | Key Scenarios |
|-----------|---------------|
| `m1-auth-search.feature.md` | Login with valid credentials, Session persists on refresh |
| `e2e-journeys.feature.md` | Complete company onboarding, Complete onboarding from invitation |
| `m3-matching.feature.md` | View matches page, View match detail, Save match to shortlist |

---

## F-UI-02: Fund Profile Form [P0]

**Description:** Multi-step form for fund creation

**Requirements:**
- Wizard-style flow (5 steps)
- Progress indicator
- Validation feedback (inline)
- File upload integration
- Save & continue later

**BDD Tests (must pass):**

| Test File | Key Scenarios |
|-----------|---------------|
| `m3-matching.feature.md` | Enter fund basics, Define investment strategy, Set investment parameters |
| `m3-matching.feature.md` | Save as draft, Publish fund, Attempt to publish without required fields |
| `e2e-journeys.feature.md` | Missing required fields on confirm, Invalid fund size format |

---

## F-UI-03: LP Search Interface [P0]

**Description:** Powerful LP discovery interface

**Requirements:**
- Filter sidebar (collapsible)
- Results list with key info (cards)
- Quick view modal / detail page
- Bulk actions (add to list, export)
- Sort by relevance, AUM, name

**BDD Tests (must pass):**

| Test File | Key Scenarios |
|-----------|---------------|
| `m2-semantic.feature.md` | Search by LP name, Search by strategy, Filter by LP type |
| `m2-semantic.feature.md` | Semantic search by thesis, Combine text and filters |
| `e2e-journeys.feature.md` | Research LPs before fund launch, Search with no results |

---

## F-UI-04: Match Results View [P0]

**Description:** Display matching LPs with context

**Requirements:**
- Ranked list with scores (visual bar)
- Score breakdown on hover/expand
- AI explanation panel (expandable)
- Actions per match (generate pitch, save, dismiss)
- Filter matches by score threshold

**BDD Tests (must pass):**

| Test File | Key Scenarios |
|-----------|---------------|
| `m3-matching.feature.md` | View matches page, View match detail, Match score breakdown |
| `m3-matching.feature.md` | F-DEBATE: Bull/Bear core debate flow, Disagreement resolution |
| `m4-pitch.feature.md` | Generate executive summary, Summary content |

---

## F-UI-05: Admin Interface [P0]

**Description:** Platform administration UI

**Requirements:**
- User management CRUD table
- Company management
- LP data management (browse, edit, delete)
- Import wizard
- Data enrichment job status
- System health dashboard

**BDD Tests (must pass):**

| Test File | Key Scenarios |
|-----------|---------------|
| `m1-auth-search.feature.md` | User belongs to one company, Cannot see other company's funds |
| `m0-foundation.feature.md` | Store LP organization details, Reject LP without name |
| `m5-production.feature.md` | Health check endpoint, System health dashboard |

---

[Next: Human-in-the-Loop →](hitl.md)
