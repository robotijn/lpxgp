# AI Matching Implementation Plan

## Summary

Replace mockup match data with real AI-powered matching. The system will:
1. Calculate rule-based compatibility scores between funds and LPs
2. Use Ollama (same as pitch generation) to generate explanations, talking points, and concerns
3. Store results in the existing `fund_lp_matches` table

## Current State

- Matches are **hardcoded** in `supabase/seed.sql` (lines 108-114)
- No dynamic matching algorithm exists
- Pitch generation already uses Ollama successfully (`src/main.py:1118-1131`)
- The `fund_lp_matches` table schema is ready for real data

## Data Model Analysis

### Fund Attributes (for matching)
| Field | Type | Usage |
|-------|------|-------|
| `strategy` | TEXT | Hard filter - must match LP strategies |
| `geographic_focus` | TEXT[] | Overlap scoring with LP preferences |
| `sector_focus` | TEXT[] | Overlap scoring with LP preferences |
| `target_size_mm` | DECIMAL | Must fit LP fund_size range |
| `fund_number` | INT | Check against LP min_fund_number |
| `esg_policy` | BOOL | Required if LP esg_required |
| `investment_thesis` | TEXT | For LLM context |

### LP Profile Attributes (for matching)
| Field | Type | Usage |
|-------|------|-------|
| `strategies` | TEXT[] | Fund strategy must be in this list |
| `geographic_preferences` | TEXT[] | Overlap with fund geographic_focus |
| `sector_preferences` | TEXT[] | Overlap with fund sector_focus |
| `fund_size_min_mm/max_mm` | DECIMAL | Fund target must fit range |
| `check_size_min_mm/max_mm` | DECIMAL | LP check size (informational) |
| `esg_required` | BOOL | Hard filter if TRUE |
| `emerging_manager_ok` | BOOL | Required if fund_number <= 2 |
| `min_fund_number` | INT | Fund must have >= this number |
| `mandate_description` | TEXT | For LLM context |

## Implementation Plan

### Step 1: Create Matching Service Module

Create `src/matching.py` with:

```python
# Scoring functions
def calculate_match_score(fund: dict, lp: dict) -> dict:
    """Returns {score, score_breakdown, passed_hard_filters}"""

# Hard filters (0 or 100):
- strategy_match: fund.strategy IN lp.strategies
- esg_match: NOT lp.esg_required OR fund.esg_policy
- emerging_manager_match: lp.emerging_manager_ok OR fund.fund_number > 2
- fund_size_match: fund.target_size_mm in LP range

# Soft scores (0-100):
- geography_overlap: % of fund.geographic_focus in lp.geographic_preferences
- sector_overlap: % of fund.sector_focus in lp.sector_preferences
- track_record_score: based on fund.fund_number vs lp.min_fund_number

# Final score calculation:
score = weighted_average(soft_scores) if all_hard_filters_passed else 0
```

### Step 2: Add LLM Content Generation

```python
async def generate_match_content(fund: dict, lp: dict, score_breakdown: dict) -> dict:
    """Use Ollama to generate explanation, talking_points, concerns"""

    prompt = f"""Analyze this GP-LP match and provide insights:

    FUND: {fund['name']} by {fund['gp_name']}
    - Strategy: {fund['strategy']}
    - Target: ${fund['target_size_mm']}M
    - Thesis: {fund['investment_thesis']}

    LP: {lp['name']} ({lp['lp_type']})
    - AUM: ${lp['total_aum_bn']}B
    - Strategies: {lp['strategies']}
    - Mandate: {lp['mandate_description']}

    MATCH SCORES: {score_breakdown}

    Provide JSON with:
    - explanation: 1-2 sentence summary of fit quality
    - talking_points: 3 key points for GP to emphasize
    - concerns: 2 potential objections LP might have
    """

    # Call Ollama (reuse existing pattern from pitch generation)
```

### Step 3: Add API Endpoint

Add to `src/main.py`:

```python
@app.post("/api/funds/{fund_id}/generate-matches")
async def generate_matches_for_fund(fund_id: str):
    """Generate AI matches for a fund against all LPs"""

    1. Validate fund_id (UUID)
    2. Fetch fund details
    3. Fetch all LP profiles
    4. For each LP:
       - Calculate score
       - If score > threshold (e.g., 60):
         - Generate LLM content
         - Upsert to fund_lp_matches
    5. Return summary
```

### Step 4: Add UI Trigger Button

In `src/templates/pages/funds.html`, add a "Generate Matches" button on each fund card that calls the new endpoint via HTMX.

### Step 5: Update Seed Data

Remove hardcoded matches from `supabase/seed.sql` and let the system generate them, OR keep them as examples but add a flag to regenerate.

## Files to Modify

| File | Change |
|------|--------|
| `src/matching.py` | NEW - Matching service module |
| `src/main.py` | Add generate-matches endpoint |
| `src/templates/pages/funds.html` | Add "Generate Matches" button |
| `supabase/seed.sql` | Consider removing hardcoded matches |
| `tests/test_main.py` | Add tests for matching logic |

## Scoring Algorithm Details

```
Hard Filters (all must pass):
├── Strategy: fund.strategy ∈ lp.strategies → 100 else 0
├── ESG: ¬lp.esg_required ∨ fund.esg_policy → 100 else 0
├── Emerging: lp.emerging_manager_ok ∨ fund.fund_number > 2 → 100 else 0
└── Fund Size: lp.fund_size_min ≤ fund.target ≤ lp.fund_size_max → 100 else 0

Soft Scores (weighted average):
├── Geography (30%): |fund.geo ∩ lp.geo| / |fund.geo| × 100
├── Sector (30%): |fund.sector ∩ lp.sector| / |fund.sector| × 100
├── Track Record (20%): min(100, fund.fund_number / lp.min_fund_number × 100)
└── Size Fit (20%): how centered fund.target is in LP range

Final Score = IF all_hard_filters THEN soft_weighted_avg ELSE 0
```

## Testing Strategy

1. Unit tests for `calculate_match_score()` with various fund/LP combinations
2. Mock Ollama responses for LLM generation tests
3. Integration test for the full matching endpoint
4. Test that hardcoded seed data matches algorithm output

## Notes

- Ollama model: `deepseek-r1:8b` (same as pitch generation)
- Timeout: 180s for LLM calls (can be slow)
- Batch processing: Generate matches for all LPs in one request
- Future enhancement: Add semantic similarity via thesis/mandate embeddings
