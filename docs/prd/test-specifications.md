# Test Specifications

**Format:** Gherkin/BDD (natural language)
**Purpose:** Communicate requirements with product owner, generate automated tests later
**Total:** ~15,000 lines of test specifications across 7 files

## Test Coverage Summary

| Category | Line Count | Key Features |
|----------|------------|--------------|
| Foundation (M0) | ~1,700 | Data import, validation, cleaning |
| Auth & Search (M1) | ~1,800 | Login, RLS, full-text search |
| Semantic Search (M2) | ~1,400 | Embeddings, similarity, filters |
| Matching + Agents (M3) | ~3,400 | Fund CRUD, debates, scoring |
| Pitch + Learning (M4) | ~2,400 | Summaries, emails, feedback |
| Production (M5) | ~1,900 | Admin, health, monitoring |
| E2E Journeys | ~2,200 | Complete user flows |

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
| F-MATCH-06 | LP-Side Matching (Bidirectional) | M3 |
| F-MATCH-07 | Enhanced Match Explanations with Learning | M4 |

## User Journeys

| Journey | File |
|---------|------|
| Complete E2E flows | [e2e-journeys.feature.md](tests/e2e-journeys.feature.md) |

## Overview

See [tests/index.md](tests/index.md) for:
- Feature coverage matrix
- Priority mapping
- How to read the specs
