# LPxGP

AI-powered platform helping investment fund managers (GPs) find and engage institutional investors (LPs).

**Live at:** [lpxgp.com](https://lpxgp.com)

## Quick Start

```bash
# Install dependencies
uv sync

# Start dev server
uv run uvicorn src.main:app --reload

# Run tests
uv run pytest
```

## Tech Stack

- **Backend:** Python 3.11+, FastAPI
- **Frontend:** Jinja2 + HTMX + Tailwind CSS
- **Database:** Supabase (PostgreSQL + pgvector)
- **Deployment:** Railway (auto-deploys from main)

## Documentation

- [CLAUDE.md](CLAUDE.md) - Project context for Claude Code
- [docs/milestones.md](docs/milestones.md) - Development roadmap
- [docs/prd/PRD-v1.md](docs/prd/PRD-v1.md) - Product requirements

## License

Private - All rights reserved
