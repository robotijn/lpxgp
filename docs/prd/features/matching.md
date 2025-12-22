# Matching Engine & Agent Architecture

[← Back to Features Index](index.md)

---

## Core Matching Features

### F-MATCH-01: Hard Filter Matching [P0]

**Description:** Eliminate LPs that don't meet basic criteria

**Requirements:**
- Strategy alignment check
- Geography overlap check
- Fund size within LP's range
- Track record meets minimums
- Configurable filter weights
- Fast elimination (< 100ms for 10k LPs)

**Test Cases:** See TEST-MATCH-01 in Testing Strategy

---

### F-MATCH-02: Soft Scoring [P0]

**Description:** Rank remaining LPs by fit quality

**Requirements:**
- Multi-factor scoring algorithm
- Factors: sector overlap, size fit, track record, ESG alignment
- Configurable weights per factor
- Score breakdown visible to user
- Score range 0-100
- Minimum score threshold (configurable, default 50)

**Test Cases:** See TEST-MATCH-02 in Testing Strategy

---

### F-MATCH-03: Semantic Matching [P0]

**Description:** Match based on investment thesis similarity

**Requirements:**
- Voyage AI embeddings for fund thesis
- Voyage AI embeddings for LP mandate
- Cosine similarity calculation
- Semantic score contributes 30% to total score
- Handle missing mandate text gracefully

**Test Cases:** See TEST-MATCH-03 in Testing Strategy

---

### F-MATCH-04: Match Explanations [P0]

**Description:** Human-readable explanation of why LP matched

**Requirements:**
- AI-generated explanation (2-3 paragraphs)
- Highlight key alignment points
- Note potential concerns or gaps
- Suggest talking points (3-5 bullets)
- Include relevant LP history if available
- Cache explanations for performance

**Test Cases:** See TEST-MATCH-04 in Testing Strategy

---

### F-MATCH-05: Match Feedback [P1]

**Description:** GPs provide feedback on match quality

**Requirements:**
- Thumbs up/down on matches
- "Not relevant" with reason
- "Already in contact" flag
- Use feedback to improve algorithm

---

## AI Matching Architecture

> **Design Principle:** Quality above all else. Cost is not a constraint.
> **Success Metric:** Actual investment commitments, not just high match scores.

### Quality-First Hybrid Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    QUALITY-FIRST MATCHING PIPELINE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STAGE 1: HARD FILTERS (SQL) - Eliminate impossible matches             │
│  ├── Strategy must align                                                │
│  ├── Geography must overlap                                             │
│  ├── Fund size within LP's acceptable range                             │
│  └── Track record meets LP minimums                                     │
│  OUTPUT: ~300-500 candidates from 10,000 LPs                            │
│                                                                          │
│  STAGE 2: MULTI-SIGNAL SCORING (Python + Embeddings)                    │
│  ├── Attribute matching (sector, size, ESG, etc.)                       │
│  ├── Semantic similarity (Voyage AI embeddings)                         │
│  ├── Historical patterns (collaborative signals when available)         │
│  └── Relationship signals (mutual connections, prior contact)           │
│  OUTPUT: Ranked list with preliminary scores                            │
│                                                                          │
│  STAGE 3: LLM DEEP ANALYSIS (Claude via OpenRouter)                     │
│  ├── Analyze EVERY filtered candidate with LLM                          │
│  ├── Structured reasoning about fit quality                             │
│  ├── Identify non-obvious alignment and concerns                        │
│  ├── Generate nuanced scores with confidence levels                     │
│  └── Parallel processing for speed                                      │
│  OUTPUT: LLM-validated scores + detailed reasoning                      │
│                                                                          │
│  STAGE 4: ENSEMBLE RANKING                                              │
│  ├── Combine rule-based score + LLM score + semantic score              │
│  ├── Weight by confidence and data quality                              │
│  └── Surface disagreements as "worth investigating"                     │
│  OUTPUT: Final ranked matches with multi-perspective validation         │
│                                                                          │
│  STAGE 5: EXPLANATION GENERATION                                        │
│  ├── Rich explanations from LLM analysis (already computed)             │
│  ├── Talking points tailored to LP's stated priorities                  │
│  ├── Concerns and how to address them                                   │
│  └── Suggested approach strategy                                        │
│  OUTPUT: Actionable intelligence for GP outreach                        │
│                                                                          │
│  STAGE 6: LEARNING LOOP (Continuous)                                    │
│  ├── Track all outcomes (shortlist, contact, meeting, commitment)       │
│  ├── Retrain ML models monthly on outcomes                              │
│  └── Human-in-loop validation of edge cases                             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

### Ensemble Scoring Weights

| Component | Weight | Source | Purpose |
|-----------|--------|--------|---------|
| **Rule-Based Score** | 25% | SQL + Python | Hard constraints, business logic |
| **Semantic Score** | 25% | Voyage AI embeddings | Thesis/mandate alignment |
| **LLM Score** | 35% | Claude analysis | Nuanced judgment, non-obvious fit |
| **Collaborative Score** | 15% | Historical patterns | "LPs like this invested in funds like this" |

### Bidirectional Matching

**GP → LP (Primary Flow):**
- GP creates fund, system finds matching LPs
- Ranked by fit quality, LP capacity, relationship ease

**LP → GP (Reverse Flow):**
- LPs can see which funds match their mandate
- Optional: LPs can set preferences to receive fund notifications
- See `lp_match_preferences` and `fund_lp_matches` tables in [Data Model](../data-model.md)
- LP interest tracked in `fund_lp_status` table

---

## Agentic Architecture

### Research Agent (F-AGENT-01)

**Trigger:** `data_quality_score < threshold` OR `last_verified > 6 months` OR user request

**Purpose:** Enrich sparse LP/GP profiles with external data

**Tools:**
- `perplexity_search(query)` - General research, recent news
- `web_fetch(url)` - Scrape LP websites for mandate details
- `news_api(entity, months)` - Recent fund commitment announcements

**Outputs:**
- Enriched profile fields (AUM, mandate text, contacts)
- LLM-generated summary (inferences from sparse data)
- Interpreted constraints (what mandate IMPLIES)

**Human Review:** All proposed changes go to review queue before commit

---

### LLM-Interpreted Constraints (F-AGENT-02)

Mandate text contains implicit constraints that keyword matching misses:

| Mandate Says | System Interprets |
|--------------|-------------------|
| "Invests in biodiversity" | Excludes: weapons, fossil_fuels, pharma, tech_hardware, mining |
| "EU-focused growth equity" | Excludes: funds with geography NOT IN EU |
| "Fund III+ only" | Excludes: Fund I, Fund II managers |
| "ESG-integrated approach" | Requires: esg_policy = TRUE |

---

### Learning Agent (F-AGENT-03)

**Trigger:** Continuous, observes all outcomes across companies

**Purpose:** Aggregate learnings to improve recommendations for everyone

**Observes (Aggregated, Privacy-Safe):**
- Response rates by LP (is this LP "hot" or "cold"?)
- Strategy trends (climate funds getting 2x engagement)
- Timing patterns (Q4 allocation windows)
- Outcome correlations (what predicts commitment?)

**Privacy Boundary:**
| Can Share | Cannot Share |
|-----------|--------------|
| "LP X has 60% response rate" (aggregated) | "Company A contacted LP X" |
| "Strategy Y is trending" | Specific pitch content |
| "Q4 allocation windows are real" | Commitment amounts in negotiation |

---

### Explanation Agent (F-AGENT-04)

**Trigger:** GP shortlists, dismisses, edits pitch, provides feedback

**Purpose:** Learn GP preferences from interactions to personalize recommendations

**Observes:**
- Which matches GP shortlists vs dismisses (implicit preference)
- How GP edits generated pitches (style preference)
- Explicit feedback ("this talking point was wrong")

**Learns & Updates:**
- GP profile: `pitch_style_preference`, `scoring_weight_overrides`
- LP profile: "GP X found talking point Y ineffective"
- Per-GP customization of ensemble weights

---

## Multi-Agent Debate Architecture

Quality is paramount; cost and latency are not constraints. All critical decisions use **adversarial debate** with multiple agents arguing different perspectives before synthesis.

### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ADVERSARIAL MULTI-AGENT ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DEBATE 1: CONSTRAINT INTERPRETATION (Per LP)                                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                      │
│  │   Broad     │◀──▶│   Narrow    │───▶│ Constraint  │ → Hard/Soft Filters  │
│  │ Interpreter │    │ Interpreter │    │ Synthesizer │                      │
│  └─────────────┘    └─────────────┘    └─────────────┘                      │
│                                                                              │
│  DEBATE 2: RESEARCH ENRICHMENT (Per Entity)                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                      │
│  │  Research   │───▶│  Research   │───▶│   Quality   │ → Enriched Profile   │
│  │  Generator  │    │   Critic    │    │ Synthesizer │                      │
│  └─────────────┘    └─────────────┘    └─────────────┘                      │
│                                                                              │
│  DEBATE 3: MATCH SCORING (Per Match - Stage 3)                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                      │
│  │    Bull     │◀──▶│    Bear     │───▶│   Match     │ → Score + Confidence │
│  │   Agent     │    │   Agent     │    │ Synthesizer │   + Talking Points   │
│  └─────────────┘    └─────────────┘    └─────────────┘                      │
│                                                                              │
│  DEBATE 4: PITCH GENERATION (Per Pitch)                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                      │
│  │   Pitch     │───▶│   Pitch     │───▶│   Content   │ → Final Pitch        │
│  │  Generator  │    │   Critic    │    │ Synthesizer │                      │
│  └─────────────┘    └─────────────┘    └─────────────┘                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

### Debate 3: Match Scoring (Core)

The most critical debate - adversarial analysis of every match:

| Agent | Role | Argues |
|-------|------|--------|
| **Bull Agent** | Match Advocate | Why this GP-LP match will succeed |
| **Bear Agent** | Match Skeptic | Why this match might fail |
| **Match Synthesizer** | Final Judgment | Weighs evidence, produces score + confidence |

**Synthesizer Output:**
- Final score (0-100) with confidence interval
- Resolved vs unresolved disagreements
- Recommendation: pursue | investigate | deprioritize | avoid
- Talking points (from Bull) and concerns to address (from Bear)

### Disagreement Resolution Protocol

```
Step 1: Initial Debate
├── Bull and Bear analyze in parallel
├── Calculate disagreement magnitude
└── If disagreement > 20 points → Continue to Step 2

Step 2: Cross-Feedback Regeneration (up to 3 rounds)
├── Bull receives Bear's concerns → Regenerate
├── Bear receives Bull's arguments → Regenerate
├── Re-synthesize
└── If still unresolved → Continue to Step 3

Step 3: Human Escalation
├── Create escalation with full debate transcript
├── Priority based on match value and disagreement
└── Human makes final decision
```

---

## Batch Processing Model

Debates run **asynchronously as batch jobs**, not in real-time:

| Trigger | Processing Mode | User Experience |
|---------|-----------------|-----------------|
| New fund created | Async job queue | "Matching in progress..." → notification when ready |
| GP requests refresh | Async job queue | "Re-analyzing..." → notification when ready |
| New LP added | Async job queue | Existing match caches invalidated, re-processed |
| Subsequent access | Cache hit | Matches load instantly |

**Matching times:** 5 minutes to 24 hours depending on queue depth and LP database size.

**Cache lifecycle:**
- Results cached for months until fund/LP data changes
- Cache invalidation triggers: fund edit, LP data update, manual refresh
- Cached matches load instantly for GP users

---

[Next: Pitch Generation →](pitch.md)
