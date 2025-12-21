# Test Specifications

**Format:** Gherkin/BDD (natural language)
**Purpose:** Communicate requirements with product owner, generate automated tests later
**Total:** ~15,200 lines of test specifications across 7 files (~1,682 scenarios)

## Test Coverage Summary

| Category | Line Count | Scenarios | Key Features |
|----------|------------|-----------|--------------|
| Foundation (M0) | ~1,700 | 183 | Data import, validation, cleaning |
| Auth & Search (M1) | ~1,800 | 249 | Login, RLS, full-text search |
| Semantic Search (M2) | ~1,400 | 157 | Embeddings, similarity, filters |
| Matching + Agents (M3) | ~3,800 | 418 | Fund CRUD, debates, observability, batch |
| Pitch + Learning (M4) | ~2,400 | 271 | Summaries, emails, feedback |
| Production (M5) | ~1,900 | 230 | Admin, health, monitoring |
| E2E Journeys | ~2,200 | 174 | Complete user flows |
| **Total** | **~15,200** | **~1,682** | **All features covered** |

## Test Files by Milestone

| Milestone | Description | File |
|-----------|-------------|------|
| M0 | Foundation - Data import & cleaning | [m0-foundation.feature.md](tests/m0-foundation.feature.md) |
| M1 | Auth + Full-Text Search | [m1-auth-search.feature.md](tests/m1-auth-search.feature.md) |
| M2 | Semantic Search | [m2-semantic.feature.md](tests/m2-semantic.feature.md) |
| M3 | Fund Profile + Matching + Agentic Architecture | [m3-matching.feature.md](tests/m3-matching.feature.md) |
| M4 | Pitch Generation + Interaction Learning | [m4-pitch.feature.md](tests/m4-pitch.feature.md) |
| M5 | Production | [m5-production.feature.md](tests/m5-production.feature.md) |

## Agentic Architecture Features

The following agent-based features are tested within M3 and M4:

| Feature | Description | Milestone |
|---------|-------------|-----------|
| F-AGENT-01 | Research Agent (Data Enrichment) | M3 |
| F-AGENT-02 | LLM-Interpreted Constraints | M3 |
| F-AGENT-03 | Learning Agent (Cross-Company Intelligence) | M3 |
| F-AGENT-04 | Explanation Agent (Interaction Learning) | M4 |
| F-MATCH-06 | LP-Side Matching (Bidirectional) | Post-MVP |
| F-MATCH-07 | Enhanced Match Explanations with Learning | M4 |
| F-DEBATE | Multi-Agent Debate System (Bull/Bear/Synthesizer) | M3 |
| F-OBSERVE | Agent Observability with Langfuse | M3 |
| F-PROMPT-VERSION | Prompt Versioning and A/B Testing | M3 |
| F-BATCH-MODE | Real-Time vs Batch Processing | M3 |
| F-PITCH-CRITIC | Pitch Quality Assurance | M4 |

## User Journeys

| Journey | File |
|---------|------|
| Complete E2E flows | [e2e-journeys.feature.md](tests/e2e-journeys.feature.md) |

## Overview

See [tests/index.md](tests/index.md) for:
- Feature coverage matrix
- Priority mapping
- How to read the specs
