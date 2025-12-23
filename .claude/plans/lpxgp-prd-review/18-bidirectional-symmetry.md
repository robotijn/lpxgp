## 18. Full Bidirectional Feature Symmetry

### Principle

**Whatever a GP can do with LPs, an LP should be able to do with GPs.**

This section documents the complete feature mapping between GP→LP and LP→GP directions.

---

### 18.1 Feature Symmetry Matrix

| GP Feature | LP Equivalent | Status |
|------------|---------------|--------|
| GP Dashboard | LP Dashboard | Mockup exists |
| Fund Profile | Mandate Profile | Mockup exists |
| LP Recommendations | GP/Fund Recommendations | Planned (M5) |
| LP Shortlist | Fund Watchlist | Mockup exists |
| Pitch Generation | Meeting Request Generation | NEW |
| Outreach Pipeline | Inbound Interest Pipeline | NEW |
| Email Sync | Email Sync | Same feature |
| Calendar Integration | Calendar Integration | Same feature |
| GP Health Dashboard | LP Health Dashboard | Section 17 |
| Team Management | Team Management | Same feature |

---

### 18.2 Dashboard Symmetry

#### GP Dashboard
```
┌─────────────────────────────────────────────────────────────────┐
│ GP Dashboard                                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ YOUR FUNDS                              ACTIVE OUTREACH          │
│ ┌───────────────────────┐              ┌───────────────────────┐│
│ │ Growth Fund III       │              │ To Contact: 12        ││
│ │ $500M target          │              │ Awaiting Reply: 8     ││
│ │ 47 LP matches         │              │ Meetings Set: 3       ││
│ └───────────────────────┘              │ In DD: 2              ││
│                                        └───────────────────────┘│
│                                                                  │
│ TOP LP RECOMMENDATIONS                                           │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1. CalPERS        Score: 92   [View] [Add to Shortlist]     │ │
│ │ 2. Yale Endow.    Score: 88   [View] [Add to Shortlist]     │ │
│ │ 3. Ontario Teach. Score: 85   [View] [Add to Shortlist]     │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

#### LP Dashboard (Mirror)
```
┌─────────────────────────────────────────────────────────────────┐
│ LP Dashboard                                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ YOUR MANDATES                           INBOUND INTEREST         │
│ ┌───────────────────────┐              ┌───────────────────────┐│
│ │ PE Allocation 2025    │              │ New Requests: 15      ││
│ │ $200M to deploy       │              │ Under Review: 8       ││
│ │ 34 fund matches       │              │ Meetings Set: 4       ││
│ └───────────────────────┘              │ In DD: 2              ││
│                                        └───────────────────────┘│
│                                                                  │
│ TOP FUND RECOMMENDATIONS                                         │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1. Acme Fund III    Score: 94   [View] [Add to Watchlist]   │ │
│ │ 2. Growth Partners  Score: 89   [View] [Add to Watchlist]   │ │
│ │ 3. Venture X        Score: 86   [View] [Add to Watchlist]   │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ GPs REQUESTING MEETINGS                                          │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1. Blue Capital    Fund IV    Requested: Dec 20             │ │
│ │    Match: 87       [Decline] [Schedule Meeting]             │ │
│ │ 2. Peak Ventures   Fund II    Requested: Dec 19             │ │
│ │    Match: 82       [Decline] [Schedule Meeting]             │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 18.3 Profile Symmetry

#### GP: Fund Profile
- Fund name, size, vintage
- Strategy, geography, sectors
- Thesis/approach description
- Track record
- Team members
- Documents (pitch deck, DDQ)

#### LP: Mandate Profile
- Mandate name, allocation amount
- Target strategies, geographies
- Mandate constraints
- Investment criteria
- Decision makers
- Documents (investment policy)

---

### 18.4 Matching Symmetry

#### GP → LP Matching
```
GP Fund Profile
    ↓
Matching Algorithm
    ↓
Ranked LP List (by fit score)
    ↓
GP Reviews & Shortlists
    ↓
GP Initiates Outreach
```

#### LP → GP Matching
```
LP Mandate Profile
    ↓
Matching Algorithm
    ↓
Ranked Fund List (by fit score)
    ↓
LP Reviews & Watchlists
    ↓
LP Requests Meetings OR Accepts GP Requests
```

---

### 18.5 Outreach/Interest Pipeline Symmetry

#### GP: Outreach Pipeline (Pursuing LPs)
```
Stages:
1. Identified (system recommended)
2. Shortlisted (GP interested)
3. Researching
4. Intro Requested / Cold Outreach Sent
5. Awaiting Response
6. Response Received
7. Meeting Scheduled
8. Meeting Completed
9. DD In Progress
10. Committed / Passed
```

#### LP: Interest Pipeline (Evaluating GPs)
```
Stages:
1. Recommended (system recommended)
2. Watchlisted (LP interested)
3. Reviewing
4. Meeting Requested (by LP)  ←── LP can initiate!
5. OR: Inbound Request (from GP)
6. Meeting Scheduled
7. Meeting Completed
8. DD In Progress
9. Committed / Passed
```

#### LP Interest Pipeline UI
```
┌─────────────────────────────────────────────────────────────────┐
│ LP Interest Pipeline - PE Allocation 2025                       │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Pipeline View | List View | Calendar View                       │
│                                                                  │
│ ┌─────────┬─────────┬─────────┬─────────┬─────────┬─────────┐  │
│ │ Review  │Requested│ Inbound │ Meeting │ DD      │Committed│  │
│ │   (12)  │   (3)   │   (8)   │   (5)   │   (2)   │   (1)   │  │
│ ├─────────┼─────────┼─────────┼─────────┼─────────┼─────────┤  │
│ │         │         │         │         │         │         │  │
│ │Acme III │Peak II  │Blue IV  │Growth   │Venture  │Alpha    │  │
│ │Score:94 │Score:87 │Score:82 │Score:89 │Score:85 │Score:91 │  │
│ │         │         │         │         │         │         │  │
│ │Gamma II │         │Delta III│Summit   │         │         │  │
│ │Score:88 │         │Score:78 │Score:86 │         │         │  │
│ └─────────┴─────────┴─────────┴─────────┴─────────┴─────────┘  │
│                                                                  │
│ Key:                                                             │
│ • Review = LP proactively researching                           │
│ • Requested = LP requested meeting with GP                      │
│ • Inbound = GP requested meeting with LP                        │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 18.6 Content Generation Symmetry

#### GP: Pitch Generation
- Executive summary tailored to LP
- Personalized outreach email
- Talking points for LP's interests
- Objection handling prep

#### LP: Meeting Request Generation
- Interest summary explaining why this fund
- Personalized meeting request email
- Questions to ask the GP
- Evaluation criteria prep

```
┌─────────────────────────────────────────────────────────────────┐
│ Generate Meeting Request - Acme Capital Fund III                │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ Why This Fund Matches Your Mandate                               │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ ✓ Strategy: Growth equity - matches your target allocation  │ │
│ │ ✓ Geography: North America & Europe - within your mandate   │ │
│ │ ✓ Fund Size: $500M - fits your check size ($15-30M)         │ │
│ │ ✓ Track Record: Fund II returned 2.1x - above your hurdle   │ │
│ │ ⚠ Sector: Heavy tech focus - monitor concentration          │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Generated Meeting Request Email                                  │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ To: [john@acmecapital.com]                                  │ │
│ │ Subject: CalPERS Interest in Acme Capital Fund III          │ │
│ │                                                             │ │
│ │ Dear John,                                                  │ │
│ │                                                             │ │
│ │ I'm reaching out from CalPERS' Private Equity team. We've  │ │
│ │ been following Acme Capital's progress and are impressed   │ │
│ │ with Fund II's performance in the growth equity space.     │ │
│ │                                                             │ │
│ │ As we build out our 2025 PE allocation, Fund III appears   │ │
│ │ to align well with our mandate. We'd welcome the           │ │
│ │ opportunity to learn more about your investment thesis     │ │
│ │ and current pipeline.                                      │ │
│ │                                                             │ │
│ │ Would you be available for a 30-minute introductory call   │ │
│ │ in the coming weeks?                                       │ │
│ │                                                             │ │
│ │ Best regards,                                               │ │
│ │ Sarah Chen                                                  │ │
│ │ Director, Private Equity                                    │ │
│ │ CalPERS                                                     │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│ Questions to Prepare                                             │
│ ┌─────────────────────────────────────────────────────────────┐ │
│ │ 1. What's your current deployment pace for Fund III?       │ │
│ │ 2. How does the tech concentration compare to Fund II?     │ │
│ │ 3. What's your approach to ESG in portfolio companies?     │ │
│ │ 4. Co-investment rights and fees?                          │ │
│ └─────────────────────────────────────────────────────────────┘ │
│                                                                  │
│                   [Copy Email] [Send Request] [Save Draft]      │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

### 18.7 Notification Symmetry

#### GP Notifications
- New LP recommendations
- LP responded to outreach
- Meeting scheduled
- LP started DD
- LP committed

#### LP Notifications
- New fund recommendations
- GP requested meeting
- GP followed up
- Meeting scheduled
- DD materials received
- GP fund closing soon (urgency)

---

### 18.8 Agent Symmetry (36 Agents)

The 36-agent architecture works in both directions with adjusted prompts:

| Debate | GP→LP Focus | LP→GP Focus |
|--------|-------------|-------------|
| Constraint Interpretation | LP mandate flexibility | Fund thesis flexibility |
| Research Enrichment | LP data gaps | GP data gaps |
| Match Scoring | LP fit for fund | Fund fit for mandate |
| Pitch Generation | Pitch to LP | Meeting request to GP |
| Relationship Intelligence | Path to LP | Path to GP |
| Timing Analysis | When to approach LP | When to approach GP |
| Competitive Intelligence | Other GPs pursuing LP | Other LPs in fund |
| Objection Handling | LP concerns | GP concerns |
| Persona Analysis | LP decision-maker style | GP team style |
| Market Context | LP market conditions | GP fundraising conditions |
| Prioritization | Which LPs to pursue | Which funds to prioritize |

---

### 18.9 Data Model Symmetry

#### GP-Centric Tables (Existing)
```sql
client_funds          -- GP's funds
outreach_activities   -- GP → LP tracking
fund_lp_matches       -- GP's view of LP matches
```

#### LP-Centric Tables (New/Enhanced)
```sql
client_mandates       -- LP's mandates
interest_activities   -- LP's tracking of funds
mandate_fund_matches  -- LP's view of fund matches
```

#### Enhanced Interest Activities Table

```sql
CREATE TABLE interest_activities (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- LP mandate
    mandate_id UUID NOT NULL REFERENCES client_mandates(id),

    -- GP fund being evaluated
    fund_id UUID NOT NULL REFERENCES client_funds(id),
    gp_company_id UUID NOT NULL REFERENCES companies(id),

    -- Current status
    stage TEXT NOT NULL DEFAULT 'recommended',
    -- Stages: recommended, watchlisted, reviewing, meeting_requested,
    --         inbound_request, meeting_scheduled, meeting_completed,
    --         dd_in_progress, committed, passed

    -- Who initiated
    initiated_by TEXT,  -- 'lp' | 'gp' | 'system'

    -- Contact tracking
    primary_contact_id UUID REFERENCES people(id),
    last_contact_date TIMESTAMP,
    next_action_date TIMESTAMP,
    next_action_description TEXT,

    -- Match data
    match_score NUMERIC,
    match_reasons JSONB,

    -- Outcome
    commitment_amount_mm NUMERIC,
    passed_reason TEXT,

    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);
```

---

### 18.10 UI Files to Create/Update

| GP Screen | LP Equivalent | File |
|-----------|---------------|------|
| `gp-dashboard.html` | `lp-dashboard.html` | EXISTS |
| `shortlist.html` | `lp-watchlist.html` | NEW |
| `fund-profile.html` | `lp-mandate-profile.html` | NEW |
| `pitch-generator.html` | `lp-meeting-request.html` | NEW |
| `gp-settings.html` | `lp-settings.html` | EXISTS |
| N/A | `lp-inbound-requests.html` | NEW |

---

### 18.11 Implementation Phasing

**Phase 1 (M1-M4): GP→LP**
- GP creates fund, gets LP matches
- GP shortlists and reaches out
- All current milestones

**Phase 2 (M5): LP→GP**
- LP creates mandate, gets fund matches
- LP watchlists and reviews
- LP receives inbound GP requests
- LP initiates meeting requests

**Phase 3 (M6): Full Bidirectional**
- Both sides fully active
- Cross-platform notifications
- Mutual interest detection
- "You both want to meet" alerts

---

### 18.12 Mutual Interest Feature

When both sides express interest:

```
┌─────────────────────────────────────────────────────────────────┐
│ 🎯 Mutual Interest Detected!                                    │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│ CalPERS added Acme Capital Fund III to their watchlist          │
│ while you have CalPERS on your shortlist!                       │
│                                                                  │
│ Both parties interested → Higher success probability            │
│                                                                  │
│ [Schedule Meeting Now]  [View CalPERS Profile]                  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

*Section 18 complete. Full bidirectional feature symmetry documented.*

---

