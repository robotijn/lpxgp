# M3: GP Profiles + 42-Agent Matching

**"42 agents find and score LP matches"**

The core intelligence milestone - GPs create fund profiles and receive AI-scored LP recommendations through a multi-agent debate system.

---

## Business Value

**Why this matters to customers:**

This is the heart of LPxGP's value proposition:

- **Expert-Level Analysis:** 42 specialized AI agents debate each match, providing depth no human team could match at scale
- **Transparent Scoring:** Bull/Bear breakdowns show exactly why an LP is recommended (or not)
- **Time to Value:** Upload a deck, confirm details, get ranked matches - minutes instead of weeks of research
- **Confidence in Decisions:** Multi-perspective debate reduces blind spots and confirmation bias
- **Scalable Intelligence:** The same quality of analysis whether you're evaluating 10 or 1,000 LPs

After M3, GPs have actionable intelligence on which LPs to pursue - the core product promise.

---

## What We Build

- Fund profile CRUD (GP creates fund)
- Deck upload + LLM extraction
- **Full 42-agent system:**
  - 14 Debate Teams × 3 agents each (Bull/Bear/Synthesizer pattern)
  - Categories: Constraint Interpretation (3), Research (3), Match Scoring (4), Content Generation (4)
- Batch processing for top N matches
- Match results UI with score breakdown

---

## Agent Architecture

```
Stage 1: Fast Filter (hard constraints + soft scores)
    |
    v
Stage 2: Deep Analysis (42 agents on top 50)
    |
    v
Cached Results (ready for GP to view)
```

---

## 14 Debate Teams (42 Agents)

**Constraint Interpretation (3 teams = 9 agents):**
1. LP Mandate Interpretation (Broad Interpreter + Narrow Interpreter + Synthesizer)
2. GP Strategy Interpretation (Thesis Expander + Thesis Refiner + Synthesizer)
3. Regulatory Compliance (Permissive Interpreter + Conservative Interpreter + Synthesizer)

**Research & Enrichment (3 teams = 9 agents):**
4. LP Research (Research Generator + Research Critic + Quality Synthesizer)
5. GP Research (Track Record Researcher + Validator + Synthesizer)
6. Market Intelligence (Trend Analyzer + Trend Skeptic + Market Synthesizer)

**Match Scoring (4 teams = 12 agents):**
7. Strategy Alignment (Strategy Bull + Strategy Bear + Synthesizer)
8. Timing Analysis (Timing Optimist + Timing Skeptic + Synthesizer)
9. Relationship Potential (Relationship Builder + Barrier Finder + Synthesizer)
10. Overall Match (Match Bull + Match Bear + Match Synthesizer)

**Content Generation (4 teams = 12 agents):**
11. Email Pitch (Email Generator + Email Critic + Synthesizer)
12. Executive Summary (Summary Generator + Summary Critic + Synthesizer)
13. Meeting Prep (Prep Generator + Prep Critic + Synthesizer)
14. Follow-up Content (Followup Generator + Followup Critic + Synthesizer)

---

## Fund Onboarding Flow

1. Deck upload -> LLM extraction
2. GP confirms extracted data
3. Questionnaire for gaps
4. Save fund profile

---

## Agent Implementation

- LangGraph for state machine orchestration
- Langfuse for monitoring and prompt versioning
- See `docs/architecture/` for details

---

## Deliverables

- [ ] API: CRUD /api/v1/funds
- [ ] API: Deck upload + LLM extraction
- [ ] Fund onboarding wizard (deck -> confirm -> questionnaire)
- [ ] LangGraph state machines for all 14 debate teams
- [ ] Manager layer synthesis
- [ ] Langfuse monitoring setup
- [ ] Batch job queue for match generation
- [ ] UI: Match results with score breakdown
- [ ] UI: Debate confidence visualization

---

## CLI Learning

- Module 7b: LangGraph state machines
- Module 7c: Langfuse monitoring
- Module 8: MCP fundamentals

---

## Exit Criteria

- [ ] Create fund -> see matches with scores
- [ ] Hover score -> see Bull/Bear breakdown
- [ ] Agent traces visible in Langfuse
- [ ] Live on lpxgp.com

---

## Demo

```
1. Create fund: "$200M Growth, Tech, US"
2. Click "Find Matches"
3. See ranked LPs with scores + confidence
4. Hover -> see Bull/Bear breakdown
5. (Admin) Show Langfuse trace of debate
```

---

[<- Previous: M2 Semantic Search](m2-semantic.md) | [Index](index.md) | [Next: M4 Pitch Generation](m4-pitch.md) ->
