# Test Specifications Index

## Testing Philosophy

### TDD Approach
1. Write test first (RED)
2. Implement minimum code to pass (GREEN)
3. Refactor while keeping tests green (REFACTOR)

### Test Pyramid
```
              ┌─────────┐
              │   E2E   │  Playwright for HTMX pages (~20 tests)
             ─┴─────────┴─
            ┌─────────────┐
            │ Integration │  pytest + httpx (~100 tests)
           ─┴─────────────┴─
          ┌─────────────────┐
          │   Unit Tests    │  pytest (~200 tests)
         ─┴─────────────────┴─
```

### Tools
| Layer | Tool |
|-------|------|
| Unit (Python) | pytest |
| Integration | pytest + httpx |
| E2E | Playwright (server-rendered HTML + HTMX) |

### Stack
- **Frontend:** Jinja2 templates + HTMX + Tailwind CSS (server-rendered)
- **Backend:** FastAPI + supabase-py (no SQLAlchemy)
- **Testing:** pytest for all Python code, Playwright for browser E2E tests

---

## Test Files by Milestone

| Milestone | Description | File |
|-----------|-------------|------|
| M0 | Foundation - Data import & cleaning | [m0-foundation.md](m0-foundation.md) |
| M1 | Auth + Full-Text Search | [m1-auth-search.md](m1-auth-search.md) |
| M2 | Semantic Search | [m2-semantic.md](m2-semantic.md) |
| M3 | Fund Profile + Matching | [m3-matching.md](m3-matching.md) |
| M4 | Pitch Generation | [m4-pitch.md](m4-pitch.md) |
| M5 | Production | [m5-production.md](m5-production.md) |

## Other Files

- [fixtures.md](fixtures.md) - Test fixtures and helpers

---

## Running Tests

```bash
# All tests (unit + integration)
uv run pytest

# By milestone
uv run pytest tests/ -k "M0"
uv run pytest tests/ -k "M1"
uv run pytest tests/ -k "M2"

# By type
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/e2e/  # Playwright browser tests

# E2E tests only (Playwright)
uv run pytest tests/e2e/ --headed  # Run with visible browser
uv run pytest tests/e2e/ --browser=firefox  # Specific browser

# With coverage
uv run pytest --cov=src --cov-report=html

# Performance only
uv run pytest -m benchmark

# Install Playwright browsers (first time setup)
uv run playwright install
```
