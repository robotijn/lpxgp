# Section 2: Expanded Agent Architecture

## Overview
Expand from 12 to 36 agents (11 debates + manager layer). Deep analysis only runs on **top 50 matches** from Stage 1 fast filtering.

## Pipeline (Batch Pre-computation)

**NOT on-demand** — results are pre-calculated and cached.

```
MONTHLY BATCH JOB (or on fund change):
┌─────────────────────────────────────────────────────────────┐
│  Stage 1: Fast Filter                                       │
│  LPs → Hard filters → Soft scores → Top 50                  │
└─────────────────────────────────────────────────────────────┘
                              ↓
┌─────────────────────────────────────────────────────────────┐
│  Stage 2: Deep Agent Analysis (36 agents)                   │
│  Top 50 → 11 Debate Teams → Manager Layer → Cached Results  │
└─────────────────────────────────────────────────────────────┘
                              ↓
                     Results stored in DB
                     Ready for GP to view
```

## 11 Debate Teams (33 agents)

| # | Debate | Agents | Purpose |
|---|--------|--------|---------|
| 1 | Constraint Interpretation | Broad + Narrow + Synthesizer | LP mandate flexibility |
| 2 | Research Enrichment | Generator + Critic + Synthesizer | Fill data gaps |
| 3 | Match Scoring | Bull + Bear + Synthesizer | Core fit assessment |
| 4 | Pitch Generation | Generator + Critic + Synthesizer | Outreach content |
| 5 | Relationship Intelligence | Mapper + Critic + Synthesizer | Warm intro paths |
| 6 | Timing Analysis | Optimist + Skeptic + Synthesizer | When to approach |
| 7 | Competitive Intelligence | Scout + Critic + Synthesizer | Portfolio conflicts |
| 8 | Objection Handling | Anticipator + Stress-Tester + Synthesizer | Q&A prep |
| 9 | LP Persona | Builder + Validator + Synthesizer | Decision-maker style |
| 10 | Market Context | Analyst + Skeptic + Synthesizer | Macro relevance |
| 11 | Prioritization | Ranker + Challenger + Synthesizer | Success likelihood |

## Manager Layer (3 agents)

- **Strategic Advisor** - Synthesizes all 11 debate outputs
- **Outreach Orchestrator** - Sequences approach strategy
- **Brief Compiler** - Packages GP-ready deliverable

## Architecture Features

**Debate Depth:** CrewAI-style with depth=3 (conflicts resolved through iteration)

**Caching Strategy:**
- LP-level data (Persona, Research) → cached per LP, reused across funds
- Match-level data (Scoring, Pitch) → cached per fund-LP pair
- Market Context → cached with daily TTL
- Relationship data → cached with staleness check

**Confidence Gating:**
- Low confidence → flag for review
- Below threshold → skip to next debate
- Confidence scores flow through pipeline
