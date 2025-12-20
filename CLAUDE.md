# LPxGP: GP-LP Intelligence Platform

An AI-powered platform helping investment fund managers (GPs) find and engage the right institutional investors (LPs).

**Domain:** lpxgp.com

## Project Documents

- @docs/milestones.md - Milestone roadmap (start here!)
- @docs/prd/PRD-v1.md - Product Requirements Document
- @docs/prd/test-specifications.md - Test specifications (TDD)
- @docs/curriculum.md - Learning curriculum (Claude Code + LPxGP)

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11+ (uv), FastAPI |
| **Frontend** | Jinja2 templates + HTMX + Tailwind CSS (CDN, no npm build) |
| **Database** | Supabase Cloud (PostgreSQL + pgvector + Auth) |
| **AI/LLM** | Claude API (Anthropic) |
| **Deployment** | Railway (auto-deploys from GitHub) |

**M2+:** Voyage AI for semantic search
**Post-MVP:** N8N + Puppeteer for data enrichment (only if needed)

## Common Commands

```bash
# Development
uv run uvicorn src.main:app --reload   # Start dev server (http://localhost:8000)
uv run pytest                          # Run tests

# Deployment (push to main = auto-deploy to Railway)
git push origin main
```

## Code Standards

### Python
- Type hints on all public functions
- Google-style docstrings
- Use `pathlib.Path` over `os.path`
- Async/await for I/O operations
- Pydantic for all request/response models
- pytest for testing with factories

### Templates (Jinja2 + HTMX)
- Base template with common layout
- HTMX for dynamic updates (no page reloads)
- Tailwind CSS for styling
- Semantic HTML with accessibility in mind

### Database
- Use supabase-py directly (no SQLAlchemy)
- Row-Level Security (RLS) for multi-tenancy
- pgvector for semantic search
- Migrations in `supabase/migrations/`

## Project Structure

```
lpxgp/
├── CLAUDE.md
├── pyproject.toml
├── src/
│   ├── main.py                 # FastAPI app + all routes
│   ├── templates/
│   │   ├── base.html           # Layout with CDN links
│   │   └── pages/
│   └── static/                 # Images only (CSS/JS via CDN)
├── tests/
│   └── test_main.py
├── supabase/
│   └── migrations/
└── docs/
```

## Milestones

| Milestone | Demo | Duration | Live |
|-----------|------|----------|------|
| M0 | "Data is imported and clean" | 1-2 days | Local only |
| M1 | "Search LPs on lpxgp.com" | 2-3 days | Yes |
| M2 | "Natural language search works" | 1-2 days | Auto-deploy |
| M3 | "See matching LPs for my fund" | 2-3 days | Auto-deploy |
| M4 | "AI explains matches + generates pitch" | 1-2 days | Auto-deploy |
| M5 | "Production-ready with admin" | 2-3 days | Auto-deploy |

**Total: ~15 working days** - After M1, every push auto-deploys to lpxgp.com.

See @docs/milestones.md for full roadmap.

## Current Status

**Phase:** Ready for Milestone 0
**Next:** Project structure, Supabase setup, data import

## Key Concepts

### GP (General Partner)
Fund managers who invest capital. They create fund profiles and seek LP investors.

### LP (Limited Partner)
Institutional investors who provide capital (pensions, endowments, family offices).

### Matching
Algorithm that scores LP-Fund compatibility based on:
- Strategy alignment (hard filter)
- Geography overlap (hard filter)
- Fund size fit (soft score)
- Semantic similarity of thesis/mandate (Voyage AI embeddings)

### Pitch Generation
Claude-generated content:
- LP-specific executive summaries
- Personalized outreach emails
- Talking points and concerns

## Testing Approach

TDD workflow:
1. Write test first (see @docs/prd/test-specifications.md)
2. Run `uv run pytest` - should fail
3. Implement minimum code to pass
4. Refactor while green

## Learning Approach

Learn Claude Code features while building LPxGP:
- Modules 1-5: Claude CLI basics (CLAUDE.md, commands, rules, deployment)
- Modules 6-7: Skills and agents
- Modules 8-11: MCP, Claude API, production

See @docs/curriculum.md for the full learning path.
