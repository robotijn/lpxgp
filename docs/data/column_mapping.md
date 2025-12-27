# Data Column Mapping Analysis

## Executive Summary

We have **rich fund data** (1,773 funds with detailed strategies, sectors, geography) but **sparse LP preference data** (only behavioral metrics, no explicit preferences in CSVs).

**Key insight:** The `form_questions.csv` shows the SCHEMA of LP preferences that exist in Metabase, but those values aren't in our CSV exports. We need to either:
1. Export `organisme_form_values` from Metabase to get actual LP preferences
2. Use behavioral data (solicitations accepted/declined) for collaborative filtering

---

## Source Files Overview

| File | Rows | Purpose | Matching Utility |
|------|------|---------|-----------------|
| global_funds.csv | 1,773 | Fund attributes | **HIGH** - rich matching criteria |
| lp_matchmaking.csv | 1,757 | LP basic info + behavior | **MEDIUM** - behavioral signals only |
| companies_crm.csv | 30,339 | Organization master | **LOW** - just names/countries |
| contacts.csv | 5,880 | Contact details | **LOW** - for outreach, not matching |
| parent_companies.csv | 28,426 | Corporate hierarchy | **LOW** - deduplication aid |
| form_questions.csv | 444 | LP preference schema | **SCHEMA ONLY** - no actual values |

---

## Detailed Column Mapping

### 1. FUND DATA (global_funds.csv) → funds table

```
SOURCE COLUMN              → TARGET COLUMN         NOTES
─────────────────────────────────────────────────────────────────
fund_id                    → external_id           Primary key mapping
fund_manager_org_id        → org_id (via lookup)   FK to organizations
fund_manager_name          → (denormalized)        For display only
fund_name                  → name                  Required
fund_status                → status                Map: "Open for investment" → "raising"
fund_generation_number     → fund_number           Roman numeral conversion?
fund_size_category_EM      → target_size_mm        Parse: "Micro (0-€100m)" → 50
description                → investment_thesis     Rich text, use for embeddings

── STRATEGY (Multi-select arrays) ──
private_equity_strategies  → strategy_tags[]       Split by comma
vc_strategies              → strategy_tags[]       Merge into same array
private_debt_strategies    → strategy_tags[]
real_assets_strategies     → strategy_tags[]
other_strategies           → strategy_tags[]

── FOCUS AREAS ──
sectors                    → sector_focus[]        Comma-separated → array
technologies               → sector_focus[]        Merge with sectors?
geographic_focus           → geographic_focus[]    Multi-value
geographic_scopes          → (derived)             Global/Regional/National

── TERMS ──
investment_minimum         → check_size_min_mm     Parse: "€1m" → 1.0
investment_term_duration   → (new field?)          "7-10 years"
fund_domiciliation         → domicile              Luxembourg, Cayman, etc.

── OTHER ──
esg_approach               → esg_policy (bool)     Contains text → true
estimated_date_of_1st_close→ (new field?)          Timing relevance
teaser_document_urls       → pitch_deck_url        First URL if multiple
contacts                   → (junction table)      Parse "id:name" format
```

### 2. LP DATA (lp_matchmaking.csv) → lp_profiles table

```
SOURCE COLUMN              → TARGET COLUMN         NOTES
─────────────────────────────────────────────────────────────────
organization_id            → external_id           Primary key mapping
organization_name          → org.name              Via organizations table
country_name               → org.hq_country        Via organizations table
lp_user_id                 → (people link)         Contact person
first_name + last_name     → people.full_name      Contact person
email                      → people.email
title                      → people.title          Mr/Ms/etc.

── BEHAVIORAL SIGNALS (gold!) ──
solicitations_received     → (analytics)           Total GP approaches
solicitations_accepted     → acceptance_rate       CALCULATE: accepted/received
solicitations_declined     → (analytics)           Rejection patterns
lastlogin_at               → engagement_score      Recent = higher score
lastactivity_at            → engagement_score

── MISSING (need from Metabase) ──
(none)                     → strategy_interests[]  From organisme_form_values
(none)                     → sector_interests[]    From organisme_form_values
(none)                     → geography_interests[] From organisme_form_values
(none)                     → check_size_range      From organisme_form_values
(none)                     → fund_size_preference  From organisme_form_values
```

### 3. LP PREFERENCE SCHEMA (form_questions.csv)

This file shows what preferences LPs CAN provide. Key matching dimensions:

```
PREFERENCE KEY                              → MATCHING DIMENSION
─────────────────────────────────────────────────────────────────
lp_strategies_private_equity               → fund.private_equity_strategies
lp_strategies_vc                           → fund.vc_strategies
lp_strategies_private_debt                 → fund.private_debt_strategies
lp_strategies_real_assets                  → fund.real_assets_strategies
sectors_interests_next_12_months           → fund.sectors
technologies_interests_next_12_months      → fund.technologies
new_funds_geographic_scopes_interests      → fund.geographic_scopes
new_funds_market_segments_interests        → fund.fund_size_category_EM
invest_in_funds_domiciled_in               → fund.fund_domiciliation
typical_fund_commitment                    → fund.investment_minimum
primary_fund_allocation_next_12_months     → fund.target size fit
```

---

## Simplified Matching Structure

### Proposed Unified Model

```python
class MatchingProfile:
    """Unified structure for both LPs and Funds"""

    # Identity
    id: str
    name: str
    type: Literal["lp", "fund"]

    # HARD FILTERS (must match)
    strategies: list[str]      # ["buyout", "growth", "venture"]
    geographies: list[str]     # ["europe", "north_america"]
    fund_size_bucket: str      # "micro", "small", "mid", "large", "mega"

    # SOFT SCORES (weighted similarity)
    sectors: list[str]         # ["healthcare", "tech", "consumer"]
    esg_required: bool

    # For embeddings
    description_text: str      # Free text for semantic matching
```

### Strategy Normalization Map

| Source Values | Normalized |
|---------------|------------|
| "Buyout", "buyout-6" | `buyout` |
| "Development / Minority", "development-minority-1" | `growth` |
| "Seed / early stage", "seed-early-stage-1" | `venture_early` |
| "Late stage / growth", "late-stage-growth-1" | `venture_late` |
| "Direct lending", "direct-lending-1" | `credit_direct` |
| "Mezzanine", "mezzanine-2" | `credit_mezz` |
| "Infrastructure", "infrastructure-4" | `infra` |
| "Real estate", "real-estate-4" | `real_estate` |

### Fund Size Normalization

| Source | Normalized | Range (EUR) |
|--------|------------|-------------|
| "Micro (0-€100m)" | `micro` | 0-100M |
| "Small (€100m-€500m)" | `small` | 100-500M |
| "Mid (€500m-€2bn)" | `mid` | 500M-2B |
| "Large (€2bn-€10bn)" | `large` | 2-10B |
| "Mega (>€10bn)" | `mega` | 10B+ |

### Geography Normalization

| Source Patterns | Normalized |
|-----------------|------------|
| "western_europe", "france", "germany" | `europe_west` |
| "central_eastern_europe", "poland" | `europe_east` |
| "north_america", "usa", "canada" | `north_america` |
| "asia_pacific", "china", "japan" | `asia_pac` |
| "Global" | `global` |

---

## Data Gaps Analysis

### What We HAVE (in CSVs)
- Fund attributes: strategy, geography, size, sectors (rich data)
- LP identity: org name, country, contact info
- LP behavior: solicitations received/accepted/declined

### What We're MISSING (need from Metabase)
- LP explicit preferences (from `organisme_form_values` table)
- Match history (from `lp_gp_matches` table)
- Which LPs accepted which specific funds

### Workarounds Without Preferences

1. **Country-based proxy**: LP country → assume regional interest
2. **Behavioral clustering**: LPs who accepted similar funds → similar preferences
3. **Size-based matching**: Large LPs → larger fund commitments
4. **Engagement scoring**: Recent activity → prioritize in recommendations

---

## Recommended ETL Phases

### Phase 1: Current Data (CSV-based)
1. Load organizations (companies_crm.csv)
2. Load funds with normalized attributes (global_funds.csv)
3. Load LP profiles with behavioral metrics (lp_matchmaking.csv)
4. Load contacts/people (contacts.csv)

### Phase 2: Preference Data (requires Metabase access)
1. Export `organisme_form_values` WHERE entity is LP
2. Parse preference keys into normalized arrays
3. Update lp_profiles with preference data

### Phase 3: Match History (requires Metabase access)
1. Export `lp_gp_matches` table
2. Build collaborative filtering model
3. Identify LP preference patterns from behavior

---

## Implementation Priority

| Priority | Task | Impact |
|----------|------|--------|
| **P0** | Normalize fund strategies/geography | Enables basic matching |
| **P0** | Parse fund_size_category | Enables size filtering |
| **P1** | Export LP preferences from Metabase | Enables preference matching |
| **P1** | Calculate LP acceptance rates | Enables behavioral scoring |
| **P2** | Build strategy normalization map | Improves match quality |
| **P2** | Geographic region rollups | Simplifies geo matching |
| **P3** | Collaborative filtering from history | "LPs like you also..." |
