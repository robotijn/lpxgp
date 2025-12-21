# LPxGP: GP-LP Intelligence Platform

An AI-powered platform helping investment fund managers (GPs) find and engage the right institutional investors (LPs).

**Domain:** lpxgp.com

## Project Documents

- docs/milestones.md - Milestone roadmap (start here!)
- docs/prd/PRD-v1.md - Product Requirements Document
- docs/prd/test-specifications.md - Test specifications (TDD)
- docs/curriculum.md - Learning curriculum (Claude Code + LPxGP)
- docs/architecture/ - Agent implementation details (M3+):
  - agents-implementation.md - LangGraph state machines, base classes
  - agent-prompts.md - Versioned prompts for 12 agents
  - batch-processing.md - Scheduler, processor, cache
  - monitoring-observability.md - Langfuse integration
- docs/product-doc/content/ux-storylines.md - User journey narratives

Note: Read these files on demand rather than auto-loading (to save context).

## Claude Preferences

- **Progress updates:** Give frequent updates during long operations
- **Deep thinking:** Always use Opus, don't switch to faster models
- **Parallel execution:** Always run independent tool calls in parallel
- **Use subagents:** Always use Task tool with subagents for parallel work when possible
- **Plan mode:** Use plan mode proactively for complex tasks - do NOT ask for permission
- **Quality focus:** After completing work, proactively check for inconsistencies, missing tests, and improvements

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.11+ (uv), FastAPI |
| **Frontend** | Jinja2 templates + HTMX + Tailwind CSS (CDN, no npm build) |
| **Database** | Supabase Cloud (PostgreSQL + pgvector + Auth) |
| **AI/LLM** | OpenRouter (Claude, free models, etc.) |
| **Deployment** | Railway (auto-deploys from GitHub) |
| **Agent Framework** | LangGraph (M3+) - state machines for multi-agent debates |
| **Agent Monitoring** | Langfuse (M3+) - open source observability, prompt versioning |

**M2+:** Voyage AI for semantic search
**Post-MVP:** Data integrations (external APIs, partner feeds)

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   Browser       │────▶│   Railway       │────▶│   Supabase      │
│   (HTMX)        │◀────│   (FastAPI)     │◀────│   (PostgreSQL)  │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┼────────────┐
                    ▼            ▼            ▼
             ┌──────────┐ ┌──────────┐ ┌──────────┐
             │OpenRouter│ │ Voyage   │ │ Supabase │
             │(LLMs)    │ │ AI (M2+) │ │ Auth     │
             └──────────┘ └──────────┘ └──────────┘
```

## Development Tools

| Tool | Purpose |
|------|---------|
| **Puppeteer MCP** | UI screenshots during development (you see what Claude sees) |
| **Playwright** | Automated E2E browser tests in CI/CD (runs headless in GitHub Actions) |

## Common Commands

```bash
# Development
uv run uvicorn src.main:app --reload   # Start dev server (http://localhost:8000)
uv run pytest                          # Run tests
uv run ruff check .                    # Lint code

# Deployment (push to main = auto-deploy to Railway)
git push origin main

# After pushing: Regenerate PDF product document
source /tmp/pdf-env/bin/activate && python docs/product-doc/build_pdf.py
```

**IMPORTANT:** After significant documentation changes, always:
1. Regenerate the PDF: `python docs/product-doc/build_pdf.py`
2. Commit and push the updated PDF
3. GitHub Pages auto-updates from docs/ folder

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

### Human-in-the-Loop (AI Content)
- All generated content (emails, summaries) requires human review before use
- No auto-send functionality - copy to clipboard only
- Fund profiles: GP must confirm AI-extracted information

## Project Structure

```
lpxgp/                    # Git repo
├── CLAUDE.md
├── pyproject.toml
├── src/
│   ├── main.py           # FastAPI app + all routes
│   ├── config.py         # Settings (env vars)
│   ├── templates/
│   │   ├── base.html     # Layout with CDN links
│   │   └── pages/
│   └── static/           # Images only (CSS/JS via CDN)
├── tests/
│   └── test_main.py
├── supabase/
│   └── migrations/
└── docs/
```

## Milestones

After M1, every push auto-deploys to lpxgp.com.

**See docs/milestones.md for the full roadmap.**

## Current Status

**Phase:** Milestone 0 - Documentation complete, ready for implementation
**Next:** Supabase schema setup, data import scripts

**Completed:**
- Full PRD with 50+ feature specifications
- 30 UI screen mockups with working navigation
- BDD test specifications for all milestones
- UX storylines and user journey documentation
- PDF product document for stakeholders

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
LLM-generated content (via OpenRouter):
- LP-specific executive summaries
- Personalized outreach emails
- Talking points and concerns

## Testing Approach

TDD workflow:
1. Write test first (see docs/prd/test-specifications.md)
2. Run `uv run pytest` - should fail
3. Implement minimum code to pass
4. Refactor while green

## Learning Approach

Learn Claude Code features while building LPxGP:
- Modules 1-2b: Foundation (CLAUDE.md, commands, data cleaning)
- Modules 3-5: Auth, CI/CD, HTMX patterns
- Modules 6-7: Skills and agents
- Modules 8-11: MCP, OpenRouter API, production

See docs/curriculum.md for the full learning path.

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `uv run` fails | Run `uv sync` first to install dependencies |
| Supabase connection error | Check SUPABASE_URL and SUPABASE_ANON_KEY env vars |
| Auth redirect fails | Verify callback URL in Supabase dashboard |
| HTMX not loading | Check CDN script tag in base.html |
| Tests fail on CI | Ensure test env vars are set in GitHub secrets |
| Railway deploy fails | Check build logs, verify pyproject.toml is valid |

**Common env vars needed:**
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_ANON_KEY` - Public anon key
- `SUPABASE_SERVICE_KEY` - Service role key (for admin ops)
- `OPENROUTER_API_KEY` - For LLM calls via OpenRouter (M3+)
- `VOYAGE_API_KEY` - For embeddings (M2+)
- `LANGFUSE_PUBLIC_KEY` - For agent monitoring (M3+)
- `LANGFUSE_SECRET_KEY` - For agent monitoring (M3+)
