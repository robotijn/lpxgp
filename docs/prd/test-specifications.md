# Test Specifications

**Format:** Gherkin/BDD (natural language)
**Purpose:** Communicate requirements with product owner, generate automated tests later
**Total:** ~16,150 lines of test specifications across 9 files (~1,782 scenarios)

---

## Running Tests Locally

**IMPORTANT:** Never skip tests. All tests must pass before pushing to main.

### Quick Reference

```bash
# Run ALL tests (recommended before pushing)
uv run pytest tests/ -v

# Run only unit tests (fast, no browser needed)
uv run pytest tests/ -v -m "not browser"

# Run only browser tests (requires running server)
uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 &
sleep 3
uv run pytest tests/ -v -m "browser"
kill %1
```

### Full CI Simulation

Run these commands in order to simulate exactly what CI does:

```bash
# 1. Linting (ruff) - must pass
uv run ruff check src/ --select=E,F
uv run ruff check src/ --select=I          # Import sorting

# 2. Type checking (mypy) - should not crash
uv run mypy src/ --ignore-missing-imports

# 3. Code quality checks
uv run ruff check src/ --select=T201 --exclude=src/config.py  # No print statements
uv run ruff check src/ --select=T100                          # No debugger statements

# 4. Unit tests
uv run pytest tests/ -v --tb=short -m "not browser"

# 5. Browser tests (requires Playwright)
uv run playwright install chromium
uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 &
sleep 3
uv run pytest tests/ -v --tb=short -m "browser"
kill %1
```

### Test Files

| File | Purpose | Marker |
|------|---------|--------|
| `tests/test_main.py` | API endpoints, auth, browser UI | `browser` for Playwright tests |
| `tests/test_ci.py` | CI checks as unit tests (linting, types) | none |
| `tests/conftest.py` | Shared fixtures and test data | N/A |

### Pytest Markers

```bash
# List available markers
uv run pytest --markers

# Current markers:
# @pytest.mark.browser - Tests requiring Playwright browser
```

### Common Issues

| Issue | Solution |
|-------|----------|
| `ModuleNotFoundError` | Run `uv sync --all-extras` to install dev dependencies |
| Browser tests fail locally | Start server first: `uv run uvicorn src.main:app &` |
| Playwright not installed | Run `uv run playwright install chromium` |
| Port 8000 in use | Kill existing process: `lsof -ti:8000 \| xargs kill` |

### CI Workflow

The GitHub Actions workflow (`.github/workflows/ci.yml`) runs:

1. **test job** (58s):
   - Install dependencies with `uv sync --all-extras`
   - Run ruff linting
   - Run unit tests (`-m "not browser"`)
   - Install Playwright browsers
   - Start server, run browser tests, stop server

2. **type-check job** (15s):
   - Run mypy type checking

Both jobs must pass for CI to be green.

---

## Test Coverage Summary

| Category | Line Count | Scenarios | Key Features |
|----------|------------|-----------|--------------|
| Foundation (M0) | ~1,700 | 183 | Data import, validation, cleaning |
| Auth & Search (M1) | ~1,800 | 249 | Login, RLS, full-text search |
| **IR Core (M1b)** | ~450 | 48 | Contact lookup, events, touchpoints, tasks |
| Semantic Search (M2) | ~1,400 | 157 | Embeddings, similarity, filters |
| Matching + Agents (M3) | ~3,800 | 418 | Fund CRUD, debates, observability, batch |
| Pitch + Learning (M4) | ~2,400 | 271 | Summaries, emails, feedback |
| Production (M5) | ~1,900 | 230 | Admin, health, monitoring |
| **IR Advanced (M9)** | ~500 | 52 | Entity Resolution, briefing books, scoring |
| E2E Journeys | ~2,200 | 174 | Complete user flows |
| **Total** | **~16,150** | **~1,782** | **All features covered** |

## Test Files by Milestone

| Milestone | Description | File |
|-----------|-------------|------|
| M0 | Foundation - Data import & cleaning | [m0-foundation.feature.md](tests/m0-foundation.feature.md) |
| M1 | Auth + Full-Text Search | [m1-auth-search.feature.md](tests/m1-auth-search.feature.md) |
| **M1b** | **IR Core - Contact lookup, events, touchpoints** | [m1b-ir-core.feature.md](tests/m1b-ir-core.feature.md) |
| M2 | Semantic Search | [m2-semantic.feature.md](tests/m2-semantic.feature.md) |
| M3 | Fund Profile + Matching + Agentic Architecture | [m3-matching.feature.md](tests/m3-matching.feature.md) |
| M4 | Pitch Generation + Interaction Learning | [m4-pitch.feature.md](tests/m4-pitch.feature.md) |
| M5 | Production | [m5-production.feature.md](tests/m5-production.feature.md) |
| **M9** | **IR Advanced - Entity Resolution, briefing books** | [m9-ir-advanced.feature.md](tests/m9-ir-advanced.feature.md) |

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
