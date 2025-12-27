# LPxGP: GP-LP Intelligence Platform

An AI-powered platform helping investment fund managers (GPs) find and engage the right institutional investors (LPs).

**Domain:** lpxgp.com

## Project Documents

**Source of truth (MD files we work with):**
- docs/milestones.md - Milestone roadmap (start here!)
- docs/prd/ - Product Requirements Document (modular):
  - index.md - PRD table of contents
  - overview.md - Product overview and goals
  - data-model.md - Database schema and relationships
  - screens.md - UI specifications and mockups
  - user-stories.md - User stories by persona
  - features/ - Detailed feature specifications
- docs/prd/test-specifications.md - Test specifications (TDD)
- docs/curriculum.md - Learning curriculum (Claude Code + LPxGP)
- docs/architecture/ - Agent implementation details (M3+)
- docs/product-doc/content/ux-storylines.md - User journey narratives

**Derived (for human/business communication only):**
- docs/LPxGP-Product-Document.pdf - PDF with screenshots

**Note:** Read these files on demand rather than auto-loading (to save context).

## Claude Preferences

- **Progress updates:** Give frequent updates during long operations
- **Deep thinking:** Always use Opus, don't switch to faster models
- **Parallel execution:** Always run independent tool calls in parallel
- **Use subagents:** Always use Task tool with subagents for parallel work when possible
- **Plan mode:** Use plan mode proactively for complex tasks - do NOT ask for permission
- **Quality focus:** After completing work, proactively check for inconsistencies, missing tests, and improvements

## Testing Guidelines

**CRITICAL: Tests are the source of truth.**
- Do NOT remove tests or adapt tests to make them pass without asking the user first
- If a test fails, fix the APPLICATION, not the test
- Be rigorous with testing: ruff, unit testing, E2E testing
- Always use deep thinking (ultrathink) to create new tests and find edge cases
- Run the full test suite before considering work complete
- Never skip browser/E2E tests - they catch real issues that unit tests miss

## Compact Preferences

When compacting conversations, always preserve:
- Current milestone status and what was accomplished
- File paths modified in the session (with line numbers if relevant)
- Key architectural decisions made
- Error messages encountered and their solutions
- Pending tasks and next steps from the plan files
- Any user preferences or constraints mentioned

Focus summary on: what changed, why, and what's next.

## Tech Stack

| Layer | Technology |
|-------|------------|
| **Backend** | Python 3.12 (uv), FastAPI |
| **Frontend** | Jinja2 templates + HTMX + Tailwind CSS (CDN, no npm build) |
| **Database** | Supabase Cloud (PostgreSQL + pgvector + Auth) |
| **AI/LLM** | OpenRouter (Claude 3.5 Sonnet) + Ollama fallback for local dev |
| **Document Parsing** | pdfplumber (PDF), python-pptx (PowerPoint) |
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

**M3+ Agent Architecture:**
```
┌─────────────────────────────────────────────────────────────┐
│                    Async Job Queue                          │
│  (Fund created → Match job queued → Results cached)         │
└─────────────────────────────────────────────────────────────┘
                              │
                              ▼
┌─────────────────────────────────────────────────────────────┐
│                    LangGraph State Machine                  │
│  ┌─────────────┐   ┌─────────────┐   ┌─────────────┐       │
│  │ Bull Agent  │──▶│ Bear Agent  │──▶│ Synthesizer │       │
│  │ (optimist)  │   │ (skeptic)   │   │ (consensus) │       │
│  └─────────────┘   └─────────────┘   └─────────────┘       │
└─────────────────────────────────────────────────────────────┘
                              │
              ┌───────────────┼───────────────┐
              ▼               ▼               ▼
       ┌──────────┐    ┌──────────┐    ┌──────────┐
       │OpenRouter│    │ Langfuse │    │  Cache   │
       │  (LLM)   │    │(Monitor) │    │(Results) │
       └──────────┘    └──────────┘    └──────────┘
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

### Data Safety (CRITICAL)
- **NEVER write, modify, or delete source data** in /docs/data/, Metabase, or Google Sheets
- These contain real production data - treat as READ-ONLY
- **Always make copies** to work with locally or in our own Supabase database
- When ingesting data: copy first, then transform the copy

## Project Structure

```
lpxgp/                    # Git repo
├── CLAUDE.md
├── pyproject.toml
├── src/
│   ├── main.py           # FastAPI app entry point
│   ├── config.py         # Settings (env vars)
│   ├── auth.py           # Authentication utilities
│   ├── database.py       # Supabase connection
│   ├── matching.py       # LP-Fund matching algorithm
│   ├── pitch_deck_analyzer.py  # LLM pitch deck extraction
│   ├── document_parser.py      # PDF/PPTX text extraction
│   ├── file_upload.py    # Upload validation & storage
│   ├── shortlists.py     # Shortlist management
│   ├── search.py         # Full-text search utilities
│   ├── routers/          # API route modules
│   │   ├── funds.py      # Fund CRUD + pitch deck upload
│   │   ├── lps.py        # LP search & recommendations
│   │   ├── matches.py    # Match scoring endpoints
│   │   ├── pipeline.py   # Outreach pipeline tracking
│   │   ├── shortlist.py  # Shortlist management
│   │   ├── pitch.py      # Pitch generation
│   │   ├── admin.py      # Admin dashboard
│   │   ├── lp_portal.py  # LP-side features
│   │   └── ...           # auth, health, settings, etc.
│   ├── models/           # Pydantic models
│   │   ├── funds.py, lps.py, matching.py, pitch.py, ...
│   ├── middleware/       # Request middleware
│   │   ├── rate_limit.py, csrf.py, error_handler.py
│   ├── templates/
│   │   ├── base.html     # Layout with CDN links
│   │   ├── pages/        # Full page templates
│   │   └── partials/     # HTMX partial templates
│   └── static/           # Images only (CSS/JS via CDN)
├── tests/
│   ├── test_main.py      # Core API tests
│   ├── test_matching.py  # Matching algorithm tests
│   ├── test_pitch_deck_*.py  # Pitch deck upload & analysis
│   ├── test_e2e_*.py     # Playwright browser tests
│   └── ...               # ~20 test files, 1400+ tests
├── supabase/
│   └── migrations/
├── uploads/
│   └── pitch_decks/      # Uploaded pitch deck files
└── docs/
```

## Milestones

After M1, every push auto-deploys to lpxgp.com.

**See docs/milestones.md for the full roadmap.**

## Current Status

**Phase:** M5-M7 Features - GP operations + LP Portal + Mutual Interest
**Live at:** lpxgp.com (auto-deploys from main)

**Completed:**
- M0: Project setup, Supabase schema, data import
- M1: Auth (Supabase), LP search, GP dashboard, CI/CD
- M2: Full-text search with filters
- M3 (partial): Fund profiles, pitch deck upload with LLM extraction
- M5 (partial): Shortlist, pipeline tracking (Kanban), admin dashboard
- M7 (partial): LP portal, mutual interest detection

**In Progress:**
- Enhanced matching with pitch deck extracted data
- LP mandate profiles and fund recommendations

**Test Coverage:** 1400+ tests (unit + Playwright E2E)

## Key Concepts

### GP (General Partner)
Fund managers who invest capital. They create fund profiles and seek LP investors.

### LP (Limited Partner)
Institutional investors who provide capital (pensions, endowments, family offices).

### Matching Algorithm
Scores LP-Fund compatibility in two stages:
1. **Hard Filters** (pass/fail):
   - Strategy alignment (e.g., PE fund won't match VC-only LP)
   - Geography overlap
   - Fund size within LP's check range
2. **Soft Scoring** (0-100):
   - Strategy depth match
   - Geographic preference overlap
   - Size fit (centered on LP's sweet spot)
   - Enhanced scoring from pitch deck extracted data (+25 max bonus)

### Pitch Deck Analysis
LLM-powered extraction from uploaded PDFs/PPTs (via OpenRouter or Ollama):
- **Strategy details:** Primary strategy, sub-strategies, investment style
- **Track record:** IRR, MOIC, prior funds, portfolio companies
- **Team details:** Partners, experience years, operator background
- **ESG details:** ESG policy, PRI signatory status
- **Fund terms:** Target size, management fee, carry
- Used to enhance matching scores and generate insights

### Mutual Interest Detection
Bidirectional matching when both GP and LP show interest:
- GP shortlists LP → LP watchlists GP's fund = **Mutual Interest**
- Highlighted in both dashboards
- Higher priority in recommendations

### Pipeline Tracking
Kanban-style outreach stages:
```
identified → shortlisted → researching → contacted →
awaiting_response → responded → meeting_scheduled →
meeting_completed → dd_in_progress → committed/passed
```

### Pitch Generation
LLM-generated content (via OpenRouter):
- LP-specific executive summaries
- Personalized outreach emails
- Talking points and concerns

## Testing Approach

**CRITICAL: ALWAYS RUN ALL TESTS - NEVER SKIP ANY**

When running tests, always run the full test suite including browser tests:
```bash
uv run pytest tests/ -v --tb=short
```

Do NOT skip browser tests (Playwright) - they catch real issues that unit tests miss.

TDD workflow:
1. Write test first (see docs/prd/test-specifications.md)
2. Run `uv run pytest` - should fail
3. Implement minimum code to pass
4. Refactor while green
5. Run ALL tests before considering work complete

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
