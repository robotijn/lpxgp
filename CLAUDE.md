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
| **Frontend** | React 18, TypeScript, Tailwind CSS, shadcn/ui |
| **Database** | Supabase Cloud (PostgreSQL + pgvector + Auth) |
| **Embeddings** | Voyage AI (financial domain) |
| **AI/LLM** | Claude API (Anthropic) |
| **Automation** | N8N (workflow automation) |
| **Scraping** | Puppeteer MCP |
| **Deployment** | Docker, GitHub Actions, Vercel/Railway |

## Common Commands

```bash
# Python backend
uv run pytest                    # Run tests
uv run pytest -v --tb=short      # Verbose tests
uv run ruff check .              # Lint
uv run ruff format .             # Format
uv run python -m backend.main    # Start backend

# Frontend
npm run dev                      # Start dev server
npm run build                    # Production build
npm run test                     # Run tests
npm run lint                     # ESLint

# Docker
docker-compose up -d             # Start all services
docker-compose logs -f           # View logs
docker-compose down              # Stop services
```

## Code Standards

### Python
- Type hints on all public functions
- Google-style docstrings
- Use `pathlib.Path` over `os.path`
- Async/await for I/O operations
- Pydantic for all request/response models
- pytest for testing with factories

### TypeScript/React
- Functional components only
- TanStack Query for server state
- Tailwind CSS for styling
- shadcn/ui component library
- ESLint + Prettier

### Database
- Row-Level Security (RLS) for multi-tenancy
- pgvector for semantic search
- Migrations in `supabase/migrations/`

## Project Structure

```
lpxgp/
├── CLAUDE.md
├── docker-compose.yml
├── backend/
│   ├── pyproject.toml
│   ├── src/
│   │   ├── api/           # FastAPI routes
│   │   ├── models/        # Pydantic models
│   │   ├── services/      # Business logic
│   │   ├── ai/            # Claude/Voyage integrations
│   │   └── cleaning/      # Data normalization
│   └── tests/
│       ├── unit/
│       ├── integration/
│       └── fixtures/
├── frontend/
│   ├── package.json
│   └── src/
│       ├── components/
│       ├── pages/
│       ├── hooks/
│       └── lib/
├── supabase/
│   └── migrations/        # SQL migrations
├── n8n/
│   └── workflows/         # N8N workflow exports
└── docs/
    └── prd/
```

## Milestones

| Milestone | Demo | Duration |
|-----------|------|----------|
| M0 | "Search my LP database" | 2-3 weeks |
| M1 | "Find LPs with natural language" | 1-2 weeks |
| M2 | "See which LPs match my fund" | 2-3 weeks |
| M3 | "Understand WHY an LP matches" | 1-2 weeks |
| M4 | "Generate personalized pitch" | 1-2 weeks |
| M5 | "Live system with automation" | 2-3 weeks |

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
- Modules 1-6: Claude CLI (commands, skills, agents)
- Modules 7-19: Build the application sprint by sprint

See @docs/curriculum.md for the full learning path.
