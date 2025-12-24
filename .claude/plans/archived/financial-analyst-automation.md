# Financial Analyst Automation Plan

## Overview

Automate the Financial Analyst (FA) role to reduce manual research costs while maximizing data quality for LP-Fund matching. The system uses AI agents to research entities from multiple sources, with configurable trust levels that allow bulk approval of high-confidence data.

**New Agent Count: 42 total** (36 existing + 6 new research agents)

---

## Role Rename Recommendation

**Current:** Financial Analyst
**Proposed:** **Data Scout** or **Market Intel**

Rationale: "Financial Analyst" is generic and long. "Data Scout" captures the research/hunting nature of the work. "Market Intel" emphasizes the intelligence-gathering aspect.

---

## Architecture Summary

```
┌─────────────────────────────────────────────────────────────────────┐
│                     TRIGGERS                                        │
│  Scheduled (2AM) │ GP Request │ Quality Alert │ Match Computed      │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                   PRIORITY QUEUE                                    │
│  Score = (Business Impact × 40%) + (Staleness × 25%)               │
│        + (Field Completeness × 20%) + (GP Interest × 15%)          │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│               RESEARCH COORDINATOR AGENT (Manager)                  │
│  - Dispatches scouts to relevant sources                           │
│  - Aggregates findings from all scouts                             │
│  - Resolves conflicts using trust scores                           │
│  - Makes final recommendation (auto-approve or human review)       │
│                                                                     │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐ ┌────────────┐│
│  │ Perplexity   │ │  LinkedIn    │ │ Regulatory   │ │ Web Fetch  ││
│  │ Scout        │ │  Scout       │ │ Scout        │ │ Scout      ││
│  │ (20/min)     │ │ (5/min)      │ │ (30/min)     │ │ (10/min)   ││
│  └──────┬───────┘ └──────┬───────┘ └──────┬───────┘ └─────┬──────┘│
│         └────────────────┴─────────────────┴───────────────┘       │
│                                    │                                │
│                                    ▼                                │
│            ┌───────────────────────────────────────────┐           │
│            │  COORDINATOR CONFLICT RESOLUTION          │           │
│            │  1. Compare values across scouts          │           │
│            │  2. Weight by source_trust × confidence   │           │
│            │  3. If delta < 10%: pick highest score    │           │
│            │  4. If delta >= 10%: flag for human       │           │
│            │  5. If 2+ scouts agree: boost confidence  │           │
│            └───────────────────────────────────────────┘           │
└────────────────────────────┬────────────────────────────────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 SOURCE TRUST SYSTEM                                 │
│                                                                     │
│  Auto-approve if: source_trust × field_confidence > threshold      │
│                                                                     │
│  Source Defaults:       Field Confidence (examples):                │
│  - SEC Filings: 0.95    - SEC → AUM: 0.98                          │
│  - PitchBook: 0.90      - LinkedIn → Contacts: 0.95                │
│  - LinkedIn: 0.70       - LinkedIn → AUM: 0.30 (unreliable)        │
│  - Perplexity: 0.65     - Perplexity → Mandate: 0.65               │
│  - News: 0.55                                                       │
│                                                                     │
│  FA can override trust per source and per field                    │
└────────────────────────────┬────────────────────────────────────────┘
                             │
              ┌──────────────┴──────────────┐
              │                             │
         AUTO-APPROVE                  HUMAN REVIEW
         (High confidence,             (Low confidence,
          trusted source)              critical fields,
              │                         conflicts)
              │                             │
              └──────────────┬──────────────┘
                             │
                             ▼
┌─────────────────────────────────────────────────────────────────────┐
│                 STAGING → PRODUCTION                                │
│  - Commit approved changes to entity profiles                      │
│  - Invalidate affected match caches                                │
│  - Recalculate data quality scores                                 │
└─────────────────────────────────────────────────────────────────────┘
```

---

## 1. Source Trust System

### Database Schema

```sql
-- Data Sources Registry
CREATE TABLE data_sources (
    id                  UUID PRIMARY KEY,
    name                TEXT NOT NULL UNIQUE,  -- 'linkedin', 'pitchbook', etc.
    display_name        TEXT NOT NULL,
    source_type         TEXT NOT NULL,  -- 'api', 'web', 'regulatory', 'manual'
    default_trust_score DECIMAL(3,2),   -- 0.0 to 1.0
    rate_limit_per_hour INTEGER,
    is_active           BOOLEAN DEFAULT TRUE
);

-- Per-User Trust Overrides (FA can customize)
CREATE TABLE user_source_trust (
    user_id     UUID REFERENCES people(id),
    source_id   UUID REFERENCES data_sources(id),
    trust_score DECIMAL(3,2),
    reason      TEXT,
    UNIQUE(user_id, source_id)
);

-- Field-Source Confidence Matrix
CREATE TABLE field_source_confidence (
    source_id        UUID REFERENCES data_sources(id),
    entity_type      TEXT,  -- 'lp_profile', 'fund', 'person'
    field_name       TEXT,  -- 'total_aum_bn', 'contacts', etc.
    confidence_score DECIMAL(3,2),
    UNIQUE(source_id, entity_type, field_name)
);

-- Auto-Approval Configuration
CREATE TABLE auto_approval_config (
    org_id                       UUID,  -- NULL = global default
    user_id                      UUID,  -- NULL = org or global
    auto_approve_threshold       DECIMAL(3,2) DEFAULT 0.85,
    always_review_fields         JSONB,  -- ["total_aum_bn", "pe_allocation_pct"]
    require_two_source_agreement BOOLEAN DEFAULT TRUE,
    max_value_delta_pct          DECIMAL(5,2) DEFAULT 10.0
);
```

### Default Trust Scores

| Source | Trust | Best For |
|--------|-------|----------|
| SEC Filings | 0.95 | AUM, allocations (public pensions) |
| PitchBook/Preqin | 0.90 | PE/VC data, fund history |
| GP/LP Provided | 0.90 | Their own data |
| Annual Reports | 0.92 | Official financials |
| Company Website | 0.80 | HQ, mandate description |
| LinkedIn | 0.70 | Contacts, titles (NOT for AUM) |
| Perplexity | 0.65 | General research, news |
| News Articles | 0.55 | Recent activity, commitments |

### Auto-Approval Flow

```
1. Calculate: combined_score = source_trust × field_confidence
2. If field in always_review_fields → HUMAN REVIEW
3. If combined_score < threshold (0.85) → HUMAN REVIEW
4. If conflicting values from sources → HUMAN REVIEW
5. If require_two_sources AND only 1 source → HUMAN REVIEW
6. Otherwise → AUTO-APPROVE
```

---

## 2. Priority Queue System

### Priority Score Formula

```python
priority_score = (
    business_impact_score * 0.40 +   # Impact on matching quality
    data_staleness_score * 0.25 +    # How old is the data
    field_completeness_score * 0.20 + # Missing critical fields
    active_interest_score * 0.15     # GP actively pursuing this LP
)
```

### Business Impact Calculation

- Count of matches where this LP appears in top 50
- Average match score (higher = more important to enrich)
- Recent GP views (last 30 days)
- Active shortlist count

### Database Schema

```sql
CREATE TABLE enrichment_queue (
    id                       UUID PRIMARY KEY,
    entity_type              TEXT,  -- 'lp', 'fund', 'person'
    entity_id                UUID,
    priority_score           FLOAT,
    business_impact_score    FLOAT,
    data_staleness_score     FLOAT,
    field_completeness_score FLOAT,
    active_interest_score    FLOAT,
    status                   TEXT DEFAULT 'pending',
    scheduled_for            DATE,
    trigger_source           TEXT,  -- 'scheduled', 'gp_request', etc.
    UNIQUE(entity_type, entity_id, scheduled_for)
);
```

---

## 3. Research Agent Architecture

### New Agents (6 total)

| Agent | Role | Best For |
|-------|------|----------|
| **Research Coordinator** | Manager | Dispatches scouts, resolves conflicts, makes recommendations |
| **Perplexity Scout** | Researcher | General research, news, AUM updates (20/min) |
| **LinkedIn Scout** | Researcher | Contacts, team info, titles (5/min) |
| **Regulatory Scout** | Researcher | SEC EDGAR, pension CAFRs, 13F (30/min) |
| **Web Fetch Scout** | Researcher | Company websites, mandate text (10/min) |
| **Schema Translator** | Mapper | Transforms raw findings → database schema fields |

### Research Coordinator Agent (Manager)

The Coordinator is the "brain" of the research system:

```python
class ResearchCoordinatorAgent:
    """
    Manager agent that orchestrates research scouts.

    Responsibilities:
    1. Decide which scouts to deploy based on entity type and data gaps
    2. Dispatch scouts in parallel (respecting rate limits)
    3. Aggregate findings from all scouts
    4. Resolve conflicts between scout findings
    5. Calculate final confidence scores
    6. Decide: auto-approve, flag for human, or reject
    """

    async def research(self, entity, data_gaps):
        # 1. Select relevant scouts
        scouts = self.select_scouts(entity.type, data_gaps)

        # 2. Dispatch in parallel
        findings = await asyncio.gather(*[
            scout.research(entity) for scout in scouts
        ])

        # 3. Aggregate and resolve conflicts
        resolved = self.resolve_conflicts(findings)

        # 4. Calculate final recommendation
        return self.make_recommendation(resolved)

    def resolve_conflicts(self, findings):
        """
        Conflict resolution strategy:
        - If values agree (within 10%): use highest confidence source
        - If 2+ scouts agree: boost confidence by 20%
        - If major disagreement (>10%): flag for human review
        - Always prefer regulatory > API > web > search
        """
```

### Schema Translator Agent (Mapper)

Transforms raw text findings into structured database fields:

```python
class SchemaTranslatorAgent:
    """
    Translates raw research findings into database schema format.

    Responsibilities:
    1. Parse unstructured text from scouts
    2. Extract values matching database columns
    3. Normalize formats (currency, percentages, dates)
    4. Validate against field constraints
    5. Handle ambiguous data (flag for review)
    """

    # Field mappings
    FIELD_PATTERNS = {
        "total_aum_bn": {
            "patterns": [r"\$?([\d,.]+)\s*(billion|bn|B)", r"AUM.*\$?([\d,.]+)"],
            "normalize": lambda x: float(x.replace(",", "")) / 1e9 if "million" in x else float(x.replace(",", "")),
            "type": "decimal",
        },
        "strategies": {
            "extract": "classify from text",
            "valid_values": ["Private Equity", "Venture Capital", "Real Estate", ...],
            "type": "array",
        },
        "check_size_min_mm": {
            "patterns": [r"minimum.*\$?([\d,.]+)\s*m", r"check size.*\$?([\d,.]+)"],
            "type": "decimal",
        },
    }

    def translate(self, raw_findings: dict, target_entity: str) -> dict:
        """
        Convert raw findings to database-ready values.

        Returns:
        {
            "total_aum_bn": {"value": 450.0, "confidence": 0.85, "source": "perplexity"},
            "strategies": {"value": ["PE", "VC"], "confidence": 0.70, "source": "website"},
        }
        """
```

### Rate Limiting Strategy

```python
class SourceRateLimiter:
    """Sliding window rate limiter per source."""

    def __init__(self, per_minute: int, per_hour: int):
        self.minute_window = deque()
        self.hour_window = deque()
        self.per_minute = per_minute
        self.per_hour = per_hour

    async def acquire(self):
        # Wait if at minute limit
        # Raise if at hour limit (requeue for later)
        ...

    def get_backoff_seconds(self) -> float:
        # Exponential backoff: base * 2^(failures-1)
        ...
```

### Research Coordinator Flow

```python
async def research_entity(entity_type, entity_id, data_gaps):
    # 1. Determine applicable sources
    sources = get_applicable_sources(entity_type, data_gaps)

    # 2. Query each source (respecting rate limits)
    raw_results = {}
    for source in sorted(sources, key=priority):
        await rate_limiters[source].acquire()
        raw_results[source] = await agents[source].research(entity)

    # 3. Run Research Debate (existing pattern)
    validated = await research_debate.run(raw_results)

    # 4. Apply source trust for auto-approval decision
    return await apply_trust_scoring(validated)
```

---

## 4. Nightly Batch Processing

### Schedule

- **2 AM UTC**: Run nightly enrichment batch
- **Process**: Top 200 items by priority, above threshold (30)
- **Output**: Staged results for morning FA review

### Batch Job Flow

```python
async def run_nightly_enrichment():
    # 1. Refresh priority scores for all candidates
    await refresh_priority_queue()

    # 2. Select top N items
    items = await select_batch_items(max=200, min_priority=30)

    # 3. Process each with rate limiting
    for item in items:
        result = await research_coordinator.research_entity(item)
        await stage_for_review(result)

    # 4. Notify FAs of pending reviews
    await notify_fas(pending_count)
```

### Staging Table

```sql
CREATE TABLE enrichment_staging (
    id                  UUID PRIMARY KEY,
    queue_item_id       UUID REFERENCES enrichment_queue(id),
    entity_type         TEXT,
    entity_id           UUID,
    proposed_updates    JSONB,  -- Field → new value
    confidence_scores   JSONB,  -- Field → confidence
    research_sources    JSONB,  -- Which sources were queried
    review_status       TEXT DEFAULT 'pending_review',
    reviewed_by         UUID,
    reviewed_at         TIMESTAMPTZ,
    applied_updates     JSONB   -- What was actually approved
);
```

---

## 5. Caching Strategy

### Field-Specific TTLs

| Field Type | TTL | Example Fields |
|------------|-----|----------------|
| Stable | 365 days | name, website, HQ location |
| Financial | 30 days | AUM, allocation % |
| Strategy | 90 days | strategies, geography, sectors |
| Activity | 14 days | recent commitments |
| Contacts | 7 days | people, email, titles |

### Cache Schema

```sql
CREATE TABLE enrichment_cache (
    entity_type  TEXT,
    entity_id    UUID,
    source       TEXT,
    field_name   TEXT,
    cached_value JSONB,
    confidence   FLOAT,
    cached_at    TIMESTAMPTZ,
    expires_at   TIMESTAMPTZ,
    hit_count    INT DEFAULT 0,
    UNIQUE(entity_type, entity_id, source, field_name)
);
```

---

## 6. FA Dashboard UI/UX

### Screen: Main Dashboard (fa-dashboard.html)

```
┌──────────────────────────────────────────────────────────────┐
│ LPxGP [DATA SCOUT]  Dashboard │ Queue │ Clarify │ Sources │ Metrics │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐  ┌─────────┐
│  │ PENDING │  │NEEDS    │  │REVIEWED │  │  AUTO-  │  │ QUALITY │
│  │   47    │  │CLARIFY  │  │  TODAY  │  │APPROVED │  │  SCORE  │
│  │         │  │   8 ⚠️  │  │   23    │  │   156   │  │   78%   │
│  └─────────┘  └─────────┘  └─────────┘  └─────────┘  └─────────┘
│                                                              │
│  PRIORITY QUEUE                          [Filters] [View]   │
│  ┌──────────────────────────────────────────────────────┐  │
│  │ # │ Entity      │ Type │ Source │ Conf │ Impact │Age │  │
│  ├──────────────────────────────────────────────────────┤  │
│  │ 1 │ CalPERS     │ LP   │Research│ 73%  │ HIGH   │ 2h │  │
│  │ 2 │ Nordic Pen. │ LP   │LinkedIn│ 85%  │ MED    │ 4h │  │
│  │ 3 │ Apex Fund   │ GP   │ Deck   │ 45%  │ HIGH   │ 1d │  │
│  └──────────────────────────────────────────────────────┘  │
│                                                              │
│  [Approve Selected] [Approve All LinkedIn >80%]             │
└──────────────────────────────────────────────────────────────┘
```

### Screen: Review Interface (fa-review.html)

```
┌──────────────────────────────────────────────────────────────┐
│ < Back                           Entity: CalPERS             │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  CURRENT DATA              │  PROPOSED CHANGES               │
│  ─────────────────────────────────────────────────────────  │
│  AUM: $400B                │  AUM: $450B      [Perplexity]  │
│    Source: Manual 2023     │    Confidence: 85%  [✓] [✗]   │
│  ─────────────────────────────────────────────────────────  │
│  Contacts:                 │  Contacts:                     │
│  - John Smith, CIO         │  - John Smith, CIO     [same]  │
│                            │  + Sarah Lee, Dir PE   [NEW]   │
│                            │    Source: LinkedIn 92%        │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  [Reject All]  [Approve All]  [Approve Selected]            │
└──────────────────────────────────────────────────────────────┘
```

### Screen: Ambiguous Data Review (fa-clarify.html)

**Purpose:** Dedicated view for data that couldn't be auto-resolved - shows original sources, raw text, and links.

```
┌──────────────────────────────────────────────────────────────┐
│ < Back                     Clarify: CalPERS AUM              │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  CONFLICTING VALUES FOUND                                    │
│  ─────────────────────────────────────────────────────────  │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ SOURCE 1: Perplexity (Confidence: 73%)                  ││
│  │ Value: $556.2 billion                                   ││
│  │                                                          ││
│  │ Original Text:                                           ││
│  │ "CalPERS reported total assets of $556.2 billion as of  ││
│  │  June 2025, making it the largest public pension..."    ││
│  │                                                          ││
│  │ Source: [calpers.ca.gov/newsroom] 🔗                    ││
│  │ Retrieved: Dec 23, 2025                                  ││
│  │                                                  [USE]   ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ SOURCE 2: Annual Report (Confidence: 89%)               ││
│  │ Value: $502.1 billion                                   ││
│  │                                                          ││
│  │ Original Text:                                           ││
│  │ "Total Fund assets: $502.1B (FY 2023-24)"               ││
│  │                                                          ││
│  │ Source: [CAFR 2024 PDF, page 12] 🔗                     ││
│  │ Retrieved: Dec 20, 2025                                  ││
│  │                                                  [USE]   ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  WHY FLAGGED: Values differ by >10% ($54B delta)            │
│                                                              │
│  ┌─────────────────────────────────────────────────────────┐│
│  │ YOUR DECISION:                                           ││
│  │ ○ Use Source 1 ($556.2B - more recent)                  ││
│  │ ○ Use Source 2 ($502.1B - official report)              ││
│  │ ○ Enter custom value: [____________]                    ││
│  │ ○ Skip - need more research                              ││
│  │                                                          ││
│  │ Note (optional): [Fiscal year difference - both valid]  ││
│  └─────────────────────────────────────────────────────────┘│
│                                                              │
│  [Skip]                                         [Confirm]   │
└──────────────────────────────────────────────────────────────┘
```

**Key Features:**
- Shows **original raw text** from each source (not just extracted value)
- **Clickable links** to source documents/URLs
- **Retrieval date** so FA knows how fresh the data is
- **Reason flagged** (conflict, low confidence, ambiguous extraction)
- **Context preservation** - FA can add notes explaining their decision
- **Learning feedback** - decisions improve future auto-resolution

**Data Model Addition:**

```sql
-- Store raw source evidence for FA review
CREATE TABLE research_evidence (
    id              UUID PRIMARY KEY,
    finding_id      UUID REFERENCES field_value_history(id),

    -- Raw source data
    raw_text        TEXT NOT NULL,      -- Original text excerpt
    source_url      TEXT,               -- Link to source
    source_title    TEXT,               -- "CalPERS Annual Report 2024"
    page_number     INT,                -- For PDFs
    screenshot_url  TEXT,               -- Optional screenshot

    -- Extraction context
    extraction_query    TEXT,           -- What we searched for
    extraction_method   TEXT,           -- 'regex', 'llm', 'structured'

    -- Timestamps
    retrieved_at    TIMESTAMPTZ NOT NULL,
    expires_at      TIMESTAMPTZ         -- When this evidence becomes stale
);
```

### Screen: Source Trust Config (fa-sources.html)

```
┌──────────────────────────────────────────────────────────────┐
│ Source Trust Configuration                                   │
├──────────────────────────────────────────────────────────────┤
│                                                              │
│  Auto-Approve Threshold: [====75%====]                      │
│                                                              │
│  SOURCE          │ TRUST │ AUTO │ ACCURACY (30d)            │
│  ────────────────────────────────────────────────────────── │
│  LinkedIn        │ [85%] │ [✓]  │ 94% (156/166)            │
│    Field overrides: Contacts 95%, AUM 30% (never auto)      │
│  ────────────────────────────────────────────────────────── │
│  Perplexity      │ [70%] │ [✓]  │ 82% (89/109)             │
│  ────────────────────────────────────────────────────────── │
│  Research Agent  │ [80%] │ [✓]  │ 93% (234/252)            │
│  ────────────────────────────────────────────────────────── │
│                                                              │
└──────────────────────────────────────────────────────────────┘
```

---

## 7. Update PDF Front Page

Update `docs/product-doc/build_pdf.py` line ~616:

```html
<div class="tagline">
  Powered by 42 AI agents working 24/7—researching, debating,
  and verifying every LP match before it reaches you.
</div>
```

And update stats section:
- "42 AI Agents" (was 36)
- 36 Matching Debate Agents (existing)
- 6 Research Agents (new: 1 Coordinator, 4 Scouts, 1 Translator)

---

## 8. Implementation Phases

### Phase 1: Source Trust System (M4)
- [ ] Create data_sources table with defaults
- [ ] Create user_source_trust table
- [ ] Create field_source_confidence matrix
- [ ] Build trust calculation service
- [ ] FA can configure trust per source

### Phase 2: Priority Queue (M4)
- [ ] Create enrichment_queue table
- [ ] Implement priority calculator
- [ ] Build queue management API
- [ ] FA dashboard with queue view

### Phase 3: Research Agents (M5)
- [ ] Implement Perplexity Agent
- [ ] Implement LinkedIn Agent (API only, no scraping)
- [ ] Implement Regulatory Agent (SEC EDGAR)
- [ ] Implement Web Fetch Agent
- [ ] Rate limiting per source
- [ ] Research Coordinator

### Phase 4: Nightly Batch (M5)
- [ ] Railway cron job setup
- [ ] Batch processor with rate limits
- [ ] Staging table and workflow
- [ ] FA notification system

### Phase 5: FA Dashboard (M6)
- [ ] Main dashboard with queue
- [ ] Review interface (side-by-side)
- [ ] Bulk approval actions
- [ ] Source trust configuration
- [ ] Quality metrics dashboard

### Phase 6: Caching & Optimization (M6)
- [ ] Enrichment cache table
- [ ] Field-specific TTLs
- [ ] Cache invalidation triggers
- [ ] Performance monitoring

---

## Critical Files to Modify

| File | Changes |
|------|---------|
| `supabase/migrations/` | New tables for trust, queue, staging, cache |
| `src/agents/enrichment/` | New module for research agents |
| `src/routes/admin/` | FA dashboard routes |
| `docs/product-doc/templates/` | FA dashboard HTML templates |
| `docs/product-doc/build_pdf.py` | Update agent count to 40 |
| `docs/prd/PRD-v1.md` | Document new architecture |
| `docs/architecture/` | New agent-enrichment.md |

---

## Success Metrics

| Metric | Target |
|--------|--------|
| FA time per entity | < 30 seconds (from 5+ minutes) |
| Auto-approval rate | > 60% of enrichments |
| Data quality score | > 80% average |
| Source accuracy | > 85% per source |
| Nightly throughput | 200 entities/night |
