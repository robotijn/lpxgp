# M9: IR Advanced - Entity Resolution & Intelligence

**"Clean data, AI-powered briefing books, relationship scoring"**

> **Note:** Basic IR features (contact lookup, events, touchpoints) are in [M1b: IR Core](m1b-ir-core.md). This milestone adds advanced features that require AI and data quality infrastructure.

---

## Business Value

> **Why this matters:** After M1b gives IR the basics, M9 makes them superhuman. AI generates briefing books, Entity Resolution cleans messy data, and relationship scoring prioritizes who to focus on.

**Revenue Impact:**
- Clean data → better AI matching → more value for GPs/LPs
- Briefing books → IR is always prepared → better event outcomes
- Import adapters → onboard new clients' data easily

**Competitive Advantage:**
- Entity Resolution is hard - competitors don't have it
- AI briefing books save hours of prep time
- Relationship scoring surfaces hidden opportunities

---

## What We Build (Beyond M1b)

### 1. Entity Resolution / MDM
- Multi-source data import (CSV, Salesforce, HubSpot)
- Duplicate detection with ML + LLM
- Golden record creation
- Human review queue for uncertain matches
- Monthly model retrain with caching

### 2. AI-Powered Briefing Books
- Auto-generated before events
- Per-attendee profile cards
- Talking points from touchpoint history
- Relationship scoring (cold → warm → hot)
- Topics to avoid (from notes)

### 3. Relationship Intelligence
- Relationship strength scoring (1-5)
- Activity decay (stale relationships flagged)
- Priority queue based on scoring
- "Last touched X days ago" alerts

### 4. Data Import Adapters
- CSV bulk import
- Salesforce sync
- HubSpot sync
- Excel file processing
- Deduplication on import

### 5. Advanced IR Analytics
- Event ROI tracking
- Relationship progression over time
- Team activity metrics
- Data quality dashboard

---

## New Database Entities

**New in M9** (not in M1b):

| Entity | Purpose |
|--------|---------|
| `data_imports` | Raw imported data batches |
| `entity_matches` | ER match results + confidence scores |
| `field_provenance` | Source tracking per field for golden records |
| `relationship_scores` | Computed relationship strength (1-5) |
| `briefing_books` | Generated briefing book cache |

**Enhanced from M1b:**

| Entity | M9 Enhancement |
|--------|----------------|
| `people` | + golden_record_id, + data_quality_score |
| `touchpoints` | + ai_sentiment, + ai_topics |
| `events` | + roi_metrics, + briefing_book_id |

---

## Deliverables

> **Note:** Basic CRUD for events, touchpoints, tasks is in M1b. M9 adds advanced features.

### API Endpoints (M9-Specific)
- [ ] POST: `/api/v1/data-imports` - bulk import with ER
- [ ] GET: `/api/v1/data-imports/{id}/matches` - review ER results
- [ ] POST: `/api/v1/entity-matches/{id}/resolve` - approve/reject match
- [ ] GET: `/api/v1/events/{id}/briefing-book` - AI-generated briefing
- [ ] GET: `/api/v1/people/{id}/relationship-score` - computed score
- [ ] GET: `/api/v1/ir/priority-queue` - ranked relationships
- [ ] GET: `/api/v1/ir/analytics/event-roi` - ROI metrics

### UI Screens (M9-Specific)
- [ ] Data import wizard (CSV, Salesforce, HubSpot)
- [ ] Human review queue for ER matches
- [ ] AI briefing book viewer
- [ ] Relationship score dashboard
- [ ] Priority queue (ranked by score + staleness)
- [ ] Event ROI analytics
- [ ] Data quality dashboard

### Backend Services
- [ ] Entity Resolution pipeline (ML + LLM)
- [ ] Import adapters (CSV, Salesforce, HubSpot)
- [ ] Golden Record merger
- [ ] Relationship scoring engine
- [ ] Briefing book generator (LLM)
- [ ] Monthly model retrain job
- [ ] Classification cache

---

## User Stories

> **Note:** Basic user stories (contact lookup, event management, touchpoint logging) are in M1b.

### IR Team Member
```
As an IR team member,
I want an AI-generated briefing book before each event
So that I know who to prioritize meeting and what to discuss.
```

```
As an IR team member,
I want to see relationship scores for my contacts
So that I can focus on warming up cold relationships.
```

```
As an IR team member,
I want AI-generated talking points based on history
So that I'm always prepared with relevant conversation starters.
```

### IR Team Manager
```
As an IR team manager,
I want a priority queue ranked by relationship score + staleness
So that I can assign follow-ups to the team strategically.
```

```
As an IR team manager,
I want to track event ROI (contacts → meetings → commitments)
So that I know which events drive actual business outcomes.
```

### Data Admin
```
As a data admin,
I want to import contacts from CSV/Salesforce/HubSpot
So that I can consolidate all relationship data in one place.
```

```
As a data admin,
I want Entity Resolution to flag potential duplicates
So that I can merge records and maintain clean data.
```

---

## Exit Criteria

> **Note:** Basic IR criteria (events, contacts, touchpoints, tasks) are in M1b.

**Entity Resolution:**
- [ ] CSV import creates data_imports batch
- [ ] ER pipeline detects potential duplicates
- [ ] Confidence scores show match quality
- [ ] Human review queue for uncertain matches (50-90% confidence)
- [ ] Golden record merger creates clean master records

**AI Features:**
- [ ] Briefing book auto-generates before events
- [ ] Per-attendee cards show talking points + topics to avoid
- [ ] Relationship scores computed (1-5 scale)
- [ ] Priority queue ranks by score + staleness

**Analytics:**
- [ ] Event ROI dashboard shows meetings → commitments funnel
- [ ] Data quality dashboard shows ER health metrics

**Live on lpxgp.com**

---

## Demo Script

> **Note:** Basic IR demo (contact lookup, events, touchpoints, tasks) is in M1b.

```
M9 Advanced Features Demo:

1. Login as IR team member
2. Open upcoming event: "SuperReturn 2025"
3. Click "Generate Briefing Book" → AI creates it
4. View briefing book:
   - Ranked attendee list (by relationship score)
   - Per-person cards with talking points
   - Topics to avoid (from historical notes)
   - Suggested meeting priority order
5. Check "Relationships" dashboard:
   - See scores (1-5) for all contacts
   - Filter by "stale" (not touched in 30+ days)
   - View priority queue with assignments
6. (Admin) Import CSV with 500 contacts
7. ER pipeline runs:
   - 450 unique records created
   - 35 auto-merged (high confidence)
   - 15 flagged for review
8. Open human review queue
9. See side-by-side comparison
10. Approve/reject suggested merges
11. View data quality dashboard:
    - ER success rate
    - Golden record count
    - Field completeness
```

---

## Technical Notes

### Entity Resolution Architecture
See [TRD: Data Pipeline](../trd/data-pipeline.md) for full details.

```
Source Data → Blocking → Features → Ensemble → LLM → Human Queue → Golden Record
```

### Mobile-First Design
- Profile cards load in <1 second
- Offline mode for poor venue WiFi
- Touch-friendly interaction logging

### Integration with Existing Features
- Event attendees link to existing GP/LP organizations
- Touchpoints visible in match detail pages
- Tasks integrate with outreach pipeline

---

## Dependencies

Requires:
- **M1b (IR Core)** - basic events, touchpoints, tasks tables
- M5 (Shortlist + Pipeline) - for outreach integration
- M6 (Data Quality) - for analyst workflows

Can run in parallel with:
- M7 (Bidirectional) - different user persona
- M8 (Integrations) - can share OAuth patterns for Salesforce/HubSpot

---

## Relationship to Existing Milestones

This milestone **enhances** M1b and other milestones with AI and data quality features:

| From Milestone | M9 Enhancement |
|----------------|----------------|
| M1b: events | + AI briefing books, + ROI analytics |
| M1b: touchpoints | + AI sentiment analysis, + talking point extraction |
| M1b: people | + Entity Resolution, + golden records |
| M1b: tasks | + Priority scoring, + auto-suggestions |
| M5: outreach pipeline | + Relationship score integration |
| M6: data quality | + ER pipeline, + field provenance |

---

[← M8: External Integrations](m8-integrations.md) | [Index](index.md) | Post-MVP →
