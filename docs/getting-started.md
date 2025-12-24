# Getting Started with LPxGP

This guide walks you through setting up your local development environment for LPxGP.

## Prerequisites

Before you begin, ensure you have:

- **Python 3.11+** - Check with `python3 --version`
- **uv** - Python package manager ([install](https://github.com/astral-sh/uv))
- **Git** - Version control
- **Supabase account** - Free tier works ([supabase.com](https://supabase.com))
- **GitHub account** - For repository access

## Quick Start

### 1. Clone the Repository

```bash
git clone https://github.com/robotijn/lpxgp.git
cd lpxgp
```

### 2. Install Dependencies

```bash
uv sync
```

This installs all Python packages defined in `pyproject.toml`.

### 3. Set Up Supabase

1. Create a new project at [supabase.com](https://supabase.com)
2. Wait for the project to initialize
3. Go to **Settings > Database** and enable the `pgvector` extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS vector;
   ```
4. Copy your API keys from **Settings > API**:
   - Project URL
   - `anon` public key
   - `service_role` secret key

### 4. Configure Environment

```bash
cp .env.example .env
```

Edit `.env` and fill in your Supabase credentials:

```bash
SUPABASE_URL=https://your-project-id.supabase.co
SUPABASE_ANON_KEY=your-anon-key
SUPABASE_SERVICE_KEY=your-service-role-key
```

### 5. Run Database Migrations

Once migrations are created (M0), run them:

```bash
# Using Supabase CLI (recommended)
supabase db push

# Or manually in Supabase SQL Editor
# Copy contents of supabase/migrations/*.sql
```

### 6. Start the Development Server

```bash
uv run uvicorn src.main:app --reload
```

The app will be available at [http://localhost:8000](http://localhost:8000).

### 7. Run Tests

```bash
uv run pytest
```

For verbose output:

```bash
uv run pytest -v
```

## Project Structure

```
lpxgp/
├── CLAUDE.md           # Project context for Claude Code
├── pyproject.toml      # Python dependencies
├── .env.example        # Environment template
├── src/
│   ├── main.py         # FastAPI application
│   ├── config.py       # Settings management
│   ├── templates/      # Jinja2 HTML templates
│   └── static/         # Static assets
├── tests/
│   └── conftest.py     # Test fixtures
├── supabase/
│   └── migrations/     # Database migrations
└── docs/
    ├── getting-started.md  # This file
    ├── milestones.md       # Roadmap
    └── prd/                # Product requirements
```

## Common Tasks

### Adding Dependencies

```bash
uv add package-name
```

### Linting

```bash
uv run ruff check .
uv run ruff check . --fix  # Auto-fix issues
```

### Format Code

```bash
uv run ruff format .
```

## Milestone Checklist

### M0: Foundation
- [ ] Supabase project created
- [ ] Database migrations applied
- [ ] LP CRUD operations working
- [ ] CSV import functional
- [ ] Basic search implemented
- [ ] Deployed to Railway

### M1: Auth + Search
- [ ] Supabase Auth configured
- [ ] Invite-only registration working
- [ ] Advanced search filters
- [ ] Company/user management

### M2: Semantic Search
- [ ] Voyage AI integration
- [ ] Embeddings generated
- [ ] Vector similarity search
- [ ] Hybrid ranking

See [milestones.md](milestones.md) for the complete roadmap.

## Troubleshooting

### `uv` command not found

Install uv:
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

### Supabase connection errors

1. Check your `.env` file has correct credentials
2. Verify the Supabase project is active
3. Check if your IP is allowed (Settings > Database > Network)

### Import errors

Run `uv sync` to ensure all dependencies are installed.

### Tests failing

1. Ensure test database is configured
2. Check for missing environment variables
3. Run with verbose: `uv run pytest -v --tb=long`

## Getting Help

- **Documentation:** See `/docs` folder
- **Issues:** [GitHub Issues](https://github.com/robotijn/lpxgp/issues)
- **PRD:** [docs/prd/index.md](prd/index.md)

## Next Steps

1. Read the [PRD](prd/index.md) to understand the product
2. Review [milestones.md](milestones.md) for the roadmap
3. Check [test-specifications.md](prd/test-specifications.md) for BDD tests
4. Start implementing M0 features using TDD
