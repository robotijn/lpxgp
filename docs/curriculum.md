# Curriculum: Building LPxGP with Claude Code

**For:** Experienced Python developer (20+ years)
**Tech stack:** Python (uv), TypeScript/React, Supabase, Docker
**Pace:** Self-directed, milestone-based
**Package manager:** `uv` (not pip/conda)

---

## Course Overview

Learn Claude Code customization while building LPxGP - a GP-LP intelligence platform.

Each milestone delivers a demoable product AND teaches Claude CLI skills.

---

## Milestone-Module Mapping

| Milestone | Modules | What You Learn | What You Build |
|-----------|---------|----------------|----------------|
| M0 | 1-4 | CLAUDE.md, rules, commands | Searchable LP database |
| M1 | 5-6 | Skills, agents | Semantic search |
| M2 | 7-10 | MCP, Puppeteer, N8N | GP profiles + matching |
| M3 | 11-12 | Claude API basics | AI explanations |
| M4 | 13-14 | Advanced prompting | Pitch generation |
| M5 | 15-16 | Docker, CI/CD | Production deployment |

---

## Milestone 0: Foundation
### "I can search my LP database"

**Duration:** 2-3 weeks

### Module 1: CLAUDE.md Foundation

**Goal:** Create a memory file that teaches Claude about LPxGP.

#### 1.1 What is CLAUDE.md?
Claude reads this file automatically at session start.

**Locations (loaded in order):**
```
./CLAUDE.md                     # Project root (team-shared)
./.claude/CLAUDE.md            # Alternative location
~/.claude/CLAUDE.md            # User-level (all projects)
./CLAUDE.local.md              # Local only (gitignored)
```

#### 1.2 LPxGP CLAUDE.md
```markdown
# LPxGP: GP-LP Intelligence Platform

## Overview
AI-powered platform for GP-LP matching.

## Tech Stack
- Python 3.11+ (uv), FastAPI
- React 18, TypeScript, Tailwind
- Supabase (PostgreSQL + pgvector)

## Commands
- `uv run pytest` - run tests
- `uv run ruff check .` - lint
- `npm run dev` - frontend
```

#### 1.3 File imports with `@`
```markdown
See @docs/milestones.md for roadmap.
See @docs/prd/PRD-v1.md for requirements.
```

#### Exercise 1
Review the existing CLAUDE.md and add your personal preferences to CLAUDE.local.md.

---

### Module 2: Project Rules

**Goal:** Organize rules with path-specific matching.

#### 2.1 Rules directory
```
.claude/rules/
├── python.md      # Python standards
├── testing.md     # pytest conventions
├── api.md         # FastAPI patterns
└── frontend.md    # React/TypeScript
```

#### 2.2 Path-specific rules
```markdown
---
paths: **/*.py
---

# Python Rules
- Type hints on all public functions
- Use Pydantic for request/response models
- Use pathlib.Path over os.path
```

```markdown
---
paths: tests/**/*.py
---

# Test Rules
- Use pytest fixtures
- Naming: test_<what>_<when>_<expected>
- Use factories for test data
```

#### Exercise 2
Create `.claude/rules/python.md` and `.claude/rules/testing.md`.

---

### Module 3: Basic Commands

**Goal:** Create project-specific slash commands.

#### 3.1 Command location
```
.claude/commands/           # Project commands
~/.claude/commands/         # Personal commands
```

#### 3.2 LPxGP commands
```markdown
# .claude/commands/status.md
---
description: Project status overview
---

Show git status, test results, and any TODOs.
```

```markdown
# .claude/commands/test.md
---
description: Run pytest
allowed-tools: Bash, Read
---

Run `uv run pytest -v --tb=short` and summarize results.
```

```markdown
# .claude/commands/db.md
---
description: Database status
allowed-tools: Bash, Read
---

Check Supabase connection and show table row counts.
```

#### Exercise 3
Create `/status`, `/test`, and `/db` commands.

---

### Module 4: Command Arguments

**Goal:** Create commands with dynamic input.

#### 4.1 Variables
| Variable | Example |
|----------|---------|
| `$ARGUMENTS` | All args as string |
| `$1`, `$2` | Positional args |
| `!command` | Shell output |
| `@file` | File contents |

#### 4.2 LPxGP examples
```markdown
# .claude/commands/analyze.md
---
description: Analyze a file
argument-hint: <file> [focus]
---

Analyze @$1 for code quality.
Focus: $2
```

```markdown
# .claude/commands/lp.md
---
description: Look up LP by name
argument-hint: <name>
---

Search for LP: $ARGUMENTS
Show their profile and any matches.
```

#### Exercise 4
Create `/analyze` and `/lp` commands.

---

### Module 4b: Data Cleaning with CLI

**Goal:** Use Claude CLI to clean your LP/GP data (free, no API cost).

#### 4b.1 The approach
```
You: "I have a messy CSV with 10k LPs. Help me clean it."
Claude CLI: Reads file, writes Python script, you run it locally.
Cost: $0 (your subscription)
```

#### 4b.2 Cleaning workflow
1. Load CSV into conversation: `@data/raw_lps.csv`
2. Claude analyzes issues (missing fields, inconsistent naming)
3. Claude writes `clean_lps.py` script
4. You run: `uv run python clean_lps.py`
5. Iterate until clean
6. Import to Supabase

#### 4b.3 Normalization functions
```python
# Claude helps you write these
STRATEGY_MAP = {
    "pe": "Private Equity",
    "vc": "Venture Capital",
    "buyout": "Private Equity - Buyout",
}

def normalize_strategy(value: str) -> str:
    return STRATEGY_MAP.get(value.lower().strip(), value)
```

#### Exercise 4b
Clean your LP data using Claude CLI. Target: data quality score > 0.7.

---

### M0 Deliverables Checklist
- [ ] Project structure created
- [ ] Supabase tables + RLS policies
- [ ] LP data imported and cleaned
- [ ] GP data imported
- [ ] Basic search UI with filters
- [ ] LP detail page
- [ ] Commands: `/status`, `/test`, `/db`, `/analyze`

---

## Milestone 1: Smart Search
### "Find LPs using natural language"

**Duration:** 1-2 weeks

### Module 5: Skills

**Goal:** Create capabilities Claude uses automatically.

#### 5.1 Skills vs Commands
| Aspect | Commands | Skills |
|--------|----------|--------|
| Invocation | User types `/command` | Claude decides |
| Structure | Single file | Directory with SKILL.md |

#### 5.2 LPxGP skills
```
.claude/skills/
├── supabase-helper/
│   ├── SKILL.md
│   └── rls-patterns.md
└── voyage-helper/
    ├── SKILL.md
    └── embedding-examples.md
```

#### 5.3 Supabase skill
```yaml
---
name: supabase-helper
description: Supabase specialist for RLS policies, migrations, pgvector queries, and Auth. Use when working with database or authentication.
allowed-tools: Read, Grep, Glob, Edit, Bash
---

# Supabase Helper

## When to Use
- Writing migrations
- Setting up RLS policies
- pgvector similarity queries
- Auth configuration

## RLS Pattern for Multi-tenancy
See [rls-patterns.md](rls-patterns.md)
```

#### Exercise 5
Create `supabase-helper` and `voyage-helper` skills.

---

### Module 6: Custom Agents

**Goal:** Create specialized AI assistants.

#### 6.1 LPxGP agents
```
.claude/agents/
├── pytest-runner.md      # Test specialist
├── api-reviewer.md       # Code reviewer
└── search-debugger.md    # Search quality checker
```

#### 6.2 Pytest runner agent
```markdown
---
name: pytest-runner
description: Runs pytest and fixes failing tests. Use after code changes.
tools: Read, Edit, Bash, Grep, Glob
model: sonnet
---

You are a Python testing specialist for LPxGP.

## Process
1. Run `uv run pytest -v --tb=short`
2. Analyze failures
3. Fix issues (test bug vs code bug)
4. Re-run to verify

## LPxGP Patterns
- Factories in tests/fixtures/factories.py
- Mock external APIs (Claude, Voyage)
- Use httpx for integration tests
```

#### 6.3 Search debugger agent
```markdown
---
name: search-debugger
description: Debug search quality issues. Use when search results seem wrong.
tools: Read, Bash, Grep
model: sonnet
---

You debug LPxGP search quality.

## Process
1. Run the problematic query
2. Check embedding similarity scores
3. Verify LP data quality
4. Suggest improvements
```

#### Exercise 6
Create `pytest-runner` and `search-debugger` agents.

---

### M1 Deliverables Checklist
- [ ] Voyage AI integration
- [ ] Embeddings for all LP mandates
- [ ] Semantic search endpoint
- [ ] Combined filter + semantic search
- [ ] Relevance scores in UI
- [ ] Skills: `supabase-helper`, `voyage-helper`
- [ ] Agents: `pytest-runner`, `search-debugger`

---

## Milestone 2: GP Profiles + Matching
### "See which LPs match my fund"

**Duration:** 2-3 weeks

### Module 7: MCP Fundamentals

**Goal:** Understand Model Context Protocol.

#### 7.1 What is MCP?
Connect Claude to external tools:
- Databases
- APIs
- Browser automation

#### 7.2 Configuration
```json
// ~/.claude/settings.json
{
  "mcpServers": {
    "puppeteer": {
      "command": "npx",
      "args": ["-y", "@anthropic/mcp-server-puppeteer"]
    }
  }
}
```

---

### Module 8: Puppeteer MCP

**Goal:** Browser automation for LP enrichment.

#### 8.1 Capabilities
- Navigate to URLs
- Extract page content
- Take screenshots
- Handle JavaScript-rendered pages

#### 8.2 Enrichment use cases
- Scrape LP website "About" pages
- Extract investment mandates
- Find LinkedIn profiles
- Gather news articles

#### 8.3 Rate limiting
```python
async def enrich_lp(lp_url: str):
    content = await puppeteer.get_page_content(lp_url)
    mandate = await extract_with_claude(content)
    await asyncio.sleep(2)  # Rate limit
    return mandate
```

---

### Module 9: N8N Setup

**Goal:** Workflow orchestration for data pipelines.

#### 9.1 Docker setup
```yaml
services:
  n8n:
    image: n8nio/n8n
    ports:
      - "5678:5678"
    volumes:
      - n8n_data:/home/node/.n8n
```

#### 9.2 LPxGP workflows
- **CSV Import:** Upload → Parse → Clean → Store
- **Nightly Enrichment:** Schedule → Puppeteer → Claude → Supabase
- **Duplicate Detection:** New LP → Search → Flag

---

### Module 10: Matching Engine

**Goal:** Match funds to LPs with scoring.

#### 10.1 Hard filters
```python
def apply_hard_filters(fund: Fund, lps: list[LP]) -> list[LP]:
    return [lp for lp in lps if
        set(fund.strategy) & set(lp.strategies) and
        set(fund.geographic_focus) & set(lp.geographic_preferences) and
        (not lp.max_fund_size_mm or fund.target_size_mm <= lp.max_fund_size_mm)
    ]
```

#### 10.2 Soft scoring
```python
def calculate_score(fund: Fund, lp: LP) -> float:
    score = 0
    score += strategy_fit(fund, lp) * 0.30
    score += size_fit(fund, lp) * 0.20
    score += geography_fit(fund, lp) * 0.20
    score += semantic_similarity(fund, lp) * 0.30
    return score * 100
```

---

### M2 Deliverables Checklist
- [ ] Fund profile creation wizard
- [ ] Pitch deck upload + text extraction
- [ ] Fund thesis embeddings
- [ ] Matching algorithm (hard + soft)
- [ ] Match results page with scores
- [ ] Score breakdown visualization
- [ ] Puppeteer MCP configured
- [ ] N8N running with basic workflow

---

## Milestone 3: AI Explanations
### "Understand WHY an LP matches"

**Duration:** 1-2 weeks

### Module 11: Claude API Integration

**Goal:** Generate match explanations.

#### 11.1 API setup
```python
import anthropic

client = anthropic.Anthropic()

async def generate_explanation(fund: Fund, lp: LP, score: float) -> str:
    response = await client.messages.create(
        model="claude-sonnet-4-20250514",
        max_tokens=1000,
        messages=[{
            "role": "user",
            "content": f"""
            Explain why {lp.name} matches {fund.name}.

            Fund: {fund.strategy}, ${fund.target_size_mm}M
            LP: {lp.type}, invests in {lp.strategies}
            Score: {score}/100

            Provide:
            1. 2-3 paragraph explanation
            2. 3-5 talking points
            3. Any concerns
            """
        }]
    )
    return response.content[0].text
```

#### 11.2 Caching
```python
async def get_explanation(match: Match) -> str:
    if match.explanation:
        return match.explanation  # Cached

    explanation = await generate_explanation(...)
    await db.update(match, explanation=explanation)
    return explanation
```

---

### Module 12: Explanation Quality

**Goal:** Ensure explanations are accurate.

#### 12.1 Principles
- Only reference data you have
- Add citations: "Based on their mandate: [quote]"
- Flag concerns, don't hide them
- Add disclaimer for AI-generated content

#### 12.2 Prompt engineering
```python
prompt = f"""
Based ONLY on this data (do not invent facts):

LP Mandate: "{lp.mandate_description}"
LP Check Size: ${lp.check_size_min_mm}M - ${lp.check_size_max_mm}M
LP Strategies: {lp.strategies}

Fund Thesis: "{fund.investment_thesis}"
Fund Size: ${fund.target_size_mm}M

Explain the alignment. Quote the mandate where relevant.
"""
```

---

### M3 Deliverables Checklist
- [ ] Claude API integration
- [ ] Explanation generation
- [ ] Caching layer
- [ ] Talking points extraction
- [ ] Concerns identification
- [ ] Expandable explanation panel in UI

---

## Milestone 4: Pitch Generation
### "Generate personalized outreach"

**Duration:** 1-2 weeks

### Module 13: Summary Generation

**Goal:** LP-specific executive summaries.

#### 13.1 Generation
```python
async def generate_summary(match: Match) -> str:
    prompt = f"""
    Create a 1-page executive summary for {match.fund.name}
    tailored to {match.lp.name}.

    Emphasize aspects relevant to their mandate:
    "{match.lp.mandate_description}"
    """
    return await call_claude(prompt)
```

#### 13.2 PDF export
```python
from weasyprint import HTML

def export_pdf(summary: str, match: Match) -> bytes:
    html = render_template("summary.html", summary=summary, match=match)
    return HTML(string=html).write_pdf()
```

---

### Module 14: Email Generation

**Goal:** Personalized outreach emails.

#### 14.1 Tone options
```python
async def generate_email(match: Match, tone: str = "professional") -> Email:
    prompt = f"""
    Draft an intro email from {match.fund.name} to {match.lp.name}.
    Tone: {tone}

    Include:
    - Why we're reaching out to them specifically
    - Brief fund overview
    - Clear ask (meeting request)

    Under 200 words.
    """
    content = await call_claude(prompt)
    return Email(subject=extract_subject(content), body=extract_body(content))
```

---

### M4 Deliverables Checklist
- [ ] Executive summary generation
- [ ] PDF export
- [ ] Email generation (multiple tones)
- [ ] Edit before export
- [ ] Copy to clipboard
- [ ] Save as template

---

## Milestone 5: Production
### "Live system with automation"

**Duration:** 2-3 weeks

### Module 15: Docker & CI/CD

**Goal:** Containerize and automate deployment.

#### 15.1 Docker Compose
```yaml
version: '3.8'
services:
  backend:
    build: ./backend
    ports: ["8000:8000"]
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - CLAUDE_API_KEY=${CLAUDE_API_KEY}

  frontend:
    build: ./frontend
    ports: ["3000:3000"]

  n8n:
    image: n8nio/n8n
    ports: ["5678:5678"]
```

#### 15.2 GitHub Actions
```yaml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: uv sync && uv run pytest
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - run: railway up
```

---

### Module 16: Production Polish

**Goal:** Monitoring, admin, automation.

#### 16.1 Admin dashboard
- User management
- Data quality metrics
- Enrichment job status
- Error logs

#### 16.2 Automation
- Nightly enrichment (N8N + Puppeteer)
- Stale data alerts
- Backup verification

#### 16.3 Feedback loop
- "Was this match relevant?" Yes/No
- Track: Email sent → Response → Meeting
- Use feedback to improve scoring

---

### M5 Deliverables Checklist
- [ ] Docker deployment
- [ ] CI/CD pipeline
- [ ] Admin dashboard
- [ ] Automated enrichment
- [ ] Error tracking (Sentry)
- [ ] Feedback collection
- [ ] Basic analytics

---

## Quick Reference

### File Locations
| Type | Location |
|------|----------|
| Memory | `./CLAUDE.md` |
| Rules | `.claude/rules/*.md` |
| Commands | `.claude/commands/*.md` |
| Skills | `.claude/skills/*/SKILL.md` |
| Agents | `.claude/agents/*.md` |

### Commands
```bash
uv run pytest                # Run tests
uv run ruff check .          # Lint
npm run dev                  # Frontend
docker-compose up -d         # All services
```

### CLI vs API
| Task | Use |
|------|-----|
| Data cleaning | CLI (free) |
| Writing scripts | CLI (free) |
| Match explanations | API (production) |
| Pitch generation | API (production) |

---

## Getting Started

**Current:** Ready for Milestone 0

Say "start M0" to begin.
