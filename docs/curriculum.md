# Curriculum: Building LPxGP with Claude Code

Learn Claude Code customization while building LPxGP.

**For:** Experienced Python developer | **Pace:** Self-directed, milestone-based

See CLAUDE.md for tech stack and commands.

---

## Milestone-Module Mapping

| Milestone | Modules | What You Learn | What You Build |
|-----------|---------|----------------|----------------|
| M0 | 1, 2, 2b | CLAUDE.md, commands, data cleaning | Data imported + clean (local) |
| M1 | 3-5 | Rules, CI/CD, HTMX | LP search live on lpxgp.com |
| M2 | 6-7 | Skills, simple agents | Semantic search |
| M3 | 7b, 7c, 8 | LangGraph, Langfuse, MCP | GP profiles + multi-agent matching |
| M4 | 9-10 | OpenRouter API, prompting, learning agents | AI explanations + pitch |
| M5 | 11 | Production monitoring | Admin + polish |

---

## Milestone 0: Foundation
### "Data is imported and clean"

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

#### 1.2 Key sections
A good CLAUDE.md includes: project overview, tech stack, common commands, code standards, and current status.

See the actual CLAUDE.md in this repo for a complete example.

#### 1.3 File references
Use plain paths (not `@` imports) to avoid auto-loading large files:
```markdown
See docs/milestones.md for roadmap.
```

#### Exercise 1
Review the existing CLAUDE.md and add your personal preferences to CLAUDE.local.md.

---

### Module 2: Basic Commands

**Goal:** Create project-specific slash commands.

#### 2.1 Command location
```
.claude/commands/           # Project commands
~/.claude/commands/         # Personal commands
```

#### 2.2 LPxGP commands
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
# .claude/commands/dev.md
---
description: Start development server
allowed-tools: Bash
---

Start the FastAPI server with `uv run uvicorn src.main:app --reload`.
```

#### Exercise 2
Create `/status`, `/test`, and `/dev` commands.

---

### Module 2b: Data Cleaning with CLI

**Goal:** Use Claude CLI to clean your LP/GP data (free, no API cost).

#### 2b.1 The approach
```
You: "I have a messy CSV with 10k LPs. Help me clean it."
Claude CLI: Reads file, writes Python script, you run it locally.
Cost: $0 (your subscription)
```

#### 2b.2 Cleaning workflow
1. Load CSV into conversation: `data/raw_lps.csv`
2. Claude analyzes issues (missing fields, inconsistent naming)
3. Claude writes `clean_lps.py` script
4. You run: `uv run python clean_lps.py`
5. Iterate until clean
6. Import to Supabase

#### Exercise 2b
Clean your LP data using Claude CLI. Target: data quality score > 0.7.

---

Design for future data sources. See PRD Section 6 for schema details.

---

**M0 Deliverables:** See milestones.md

---

## Milestone 1: Auth + Search + Deploy
### "Search LPs on lpxgp.com"

### Module 3: Project Rules

**Goal:** Organize rules with path-specific matching.

#### 3.1 Rules directory
```
.claude/rules/
├── python.md      # Python standards
├── testing.md     # pytest conventions
├── api.md         # FastAPI patterns
└── templates.md   # Jinja2/HTMX patterns
```

#### 3.2 Path-specific rules
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
paths: **/templates/**/*.html
---

# Template Rules
- Use HTMX attributes for dynamic behavior
- Include hx-indicator for loading states
- Use Tailwind utility classes
```

#### Exercise 3
Create `.claude/rules/python.md` and `.claude/rules/templates.md`.

---

### Module 4: GitHub Actions CI/CD

**Goal:** Automate testing and deployment.

#### 4.1 GitHub Actions workflow
```yaml
# .github/workflows/deploy.yml
name: Deploy
on:
  push:
    branches: [main]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: astral-sh/setup-uv@v4
      - run: uv sync
      - run: uv run pytest
  deploy:
    needs: test
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: railwayapp/railway-deploy@v1
        with:
          railway_token: ${{ secrets.RAILWAY_TOKEN }}
```

#### 4.2 Railway setup
1. Create Railway account
2. Connect GitHub repo
3. Add environment variables (Supabase URL, API keys)
4. Connect domain lpxgp.com

#### Exercise 4
Set up GitHub Actions to run tests and deploy to Railway.

---

### Module 5: HTMX Patterns

**Goal:** Build dynamic UI without JavaScript frameworks.

**Note:** Use `supabase-py` client directly for database access instead of SQLAlchemy - simpler and works seamlessly with Supabase RLS.

#### 5.1 Base template with CDN links
```html
<!-- templates/base.html -->
<!DOCTYPE html>
<html>
<head>
    <script src="https://unpkg.com/htmx.org@1.9.10"></script>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
...
```

#### 5.2 Basic HTMX
```html
<!-- Search form with live results -->
<input type="text"
       name="query"
       hx-get="/lps/search"
       hx-trigger="keyup changed delay:300ms"
       hx-target="#results"
       hx-indicator="#loading">

<div id="loading" class="htmx-indicator">Loading...</div>
<div id="results"></div>
```

#### 5.3 FastAPI + Jinja2 endpoint
```python
@router.get("/lps/search")
async def search_lps(
    request: Request,
    query: str = "",
    type: str | None = None
):
    lps = await lp_service.search(query=query, type=type)
    return templates.TemplateResponse(
        "components/lp_list.html",
        {"request": request, "lps": lps}
    )
```

#### 5.4 Component template
```html
<!-- templates/components/lp_list.html -->
{% for lp in lps %}
<div class="p-4 border rounded hover:bg-gray-50">
    <h3 class="font-bold">{{ lp.name }}</h3>
    <p class="text-gray-600">{{ lp.type }}</p>
    <button hx-get="/lps/{{ lp.id }}"
            hx-target="#modal-content"
            hx-trigger="click">
        View Details
    </button>
</div>
{% endfor %}
```

#### Exercise 5
Build the LP search page with HTMX live filtering.

---

**M1 Deliverables:** See milestones.md

---

## Milestone 2: Semantic Search
### "Natural language search works"

**Note:** This is when Voyage AI gets added to the project. M0 and M1 use only keyword/filter-based search.

### Module 6: Skills

**Goal:** Create capabilities Claude uses automatically.

#### 6.1 Skills vs Commands
| Aspect | Commands | Skills |
|--------|----------|--------|
| Invocation | User types `/command` | Claude decides |
| Structure | Single file | Directory with SKILL.md |

#### 6.2 LPxGP skills
```
.claude/skills/
├── supabase-helper/
│   ├── SKILL.md
│   └── rls-patterns.md
└── voyage-helper/
    ├── SKILL.md
    └── embedding-examples.md
```

#### 6.3 Voyage helper skill
```yaml
---
name: voyage-helper
description: Voyage AI embedding specialist. Helps with vector search, similarity queries, and pgvector operations. Use when working with semantic search or embeddings.
allowed-tools: Read, Grep, Glob, Edit, Bash
---

# Voyage AI Helper

## When to Use
- Generating embeddings for LPs/funds
- Writing pgvector similarity queries
- Debugging search relevance

## Embedding Pattern
See embedding-examples.md for patterns
```

#### Exercise 6
Create `supabase-helper` and `voyage-helper` skills.

---

### Module 7: Custom Agents

**Goal:** Create specialized AI assistants.

#### 7.1 LPxGP agents
```
.claude/agents/
├── pytest-runner.md      # Test specialist
└── search-debugger.md    # Search quality checker
```

#### 7.2 Pytest runner agent
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
- Fixtures in tests/conftest.py
- Mock external APIs (OpenRouter, Voyage)
- Use httpx for integration tests
```

#### Exercise 7
Create `pytest-runner` and `search-debugger` agents.

---

**M2 Deliverables:** See milestones.md

---

## Milestone 3: GP Profiles + Matching + Agent Architecture
### "See matching LPs for my fund"

### Module 7b: LangGraph State Machines

**Goal:** Build multi-agent debate systems with LangGraph.

#### 7b.1 Why LangGraph?
LPxGP uses multi-agent debates for quality matching:
- Bull agent argues FOR a match
- Bear agent argues AGAINST
- Synthesizer resolves disagreements

LangGraph provides:
- State machines for debate cycles
- Conditional routing (regenerate vs complete)
- Persistence (resume interrupted debates)

#### 7b.2 State Definition
```python
from langgraph.graph import StateGraph
from typing import TypedDict

class MatchDebateState(TypedDict):
    fund_data: dict
    lp_data: dict
    bull_output: dict | None
    bear_output: dict | None
    synthesizer_output: dict | None
    iteration: int
    status: str  # pending, complete, escalated
```

#### 7b.3 Graph Construction
```python
def build_match_debate_graph():
    builder = StateGraph(MatchDebateState)
    builder.add_node("bull", bull_node)
    builder.add_node("bear", bear_node)
    builder.add_node("synthesize", synthesizer_node)

    builder.add_edge("bull", "bear")
    builder.add_edge("bear", "synthesize")
    builder.add_conditional_edges(
        "synthesize",
        should_regenerate,
        {"complete": END, "regenerate": "bull", "escalate": "escalate"}
    )
    return builder.compile()
```

See `docs/architecture/agents-implementation.md` for full implementation.

---

### Module 7c: Langfuse Monitoring

**Goal:** Set up agent observability and prompt versioning.

#### 7c.1 Why Langfuse?
- Open source (MIT) - no vendor lock-in
- Self-hostable for sensitive GP/LP data
- Full trace inspection for every debate
- Prompt versioning and A/B testing

#### 7c.2 Tracing Setup
```python
from langfuse import Langfuse
from langfuse.decorators import observe

langfuse = Langfuse()

@observe(name="match_debate")
async def run_match_debate(fund_id: str, lp_id: str):
    # All LLM calls automatically traced
    result = await debate_graph.ainvoke(initial_state)
    return result
```

#### 7c.3 Prompt Management
Store prompts in Langfuse with versioning:
```python
prompt = langfuse.get_prompt("match_bull_agent", version=3)
compiled = prompt.compile(fund_data=fund, lp_data=lp)
```

See `docs/architecture/monitoring-observability.md` for full integration.

---

### Module 8: MCP Fundamentals

**Goal:** Understand Model Context Protocol (for future enrichment).

#### 8.1 What is MCP?
Connect Claude to external tools:
- Databases
- APIs
- Browser automation (UI verification, not scraping)

#### 8.2 Configuration
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

#### 8.3 Puppeteer MCP Use Cases
Puppeteer MCP is for **UI verification and screenshots**, not web scraping.

**Good uses:**
- Screenshot the match results page to verify layout
- Verify responsive design across breakpoints
- Check visual regression after UI changes
- Capture error states for debugging

**Not for:** Scraping competitor sites, data extraction from external pages.

*Note: MCP is for post-MVP enrichment. Focus on matching algorithm first.*

---

### Fund Onboarding Flow

```
1. GP uploads pitch deck (PDF/PPT)
2. LLM extracts: fund name, size, strategy, thesis, team
3. Show extracted info → GP confirms or edits
4. Questionnaire for missing fields
5. GP approves → generate embeddings
```

#### Pitch deck extraction
```python
async def extract_fund_info(file_path: str) -> FundDraft:
    """Extract fund information from pitch deck."""
    text = await extract_text(file_path)  # PDF/PPT to text

    response = await client.chat.completions.create(
        model=settings.OPENROUTER_MODEL,
        messages=[{
            "role": "user",
            "content": f"""
            Extract from this pitch deck:
            - Fund name
            - Target size ($M)
            - Strategy (VC/PE/Growth/etc)
            - Investment thesis
            - Team members and backgrounds

            Return as JSON.

            {text}
            """
        }]
    )
    return FundDraft.model_validate_json(response.choices[0].message.content)
```

#### Confirmation UI
```html
<!-- GP reviews and edits extracted info -->
<form hx-post="/funds/confirm" hx-target="#result">
    <h2>We extracted this from your deck:</h2>

    <label>Fund Name</label>
    <input name="name" value="{{ draft.name }}">

    <label>Target Size ($M)</label>
    <input name="target_size_mm" value="{{ draft.target_size_mm }}">

    <label>Strategy</label>
    <select name="strategy">
        {% for s in strategies %}
        <option {{ 'selected' if s == draft.strategy }}>{{ s }}</option>
        {% endfor %}
    </select>

    <label>Thesis</label>
    <textarea name="thesis">{{ draft.thesis }}</textarea>

    <button type="submit">Confirm & Generate Matches</button>
</form>
```

---

### Matching Algorithm

#### Hard filters
```python
def apply_hard_filters(fund: Fund, lps: list[LP]) -> list[LP]:
    return [lp for lp in lps if
        set(fund.strategy) & set(lp.strategies) and
        set(fund.geographic_focus) & set(lp.geographic_preferences) and
        (not lp.max_fund_size_mm or fund.target_size_mm <= lp.max_fund_size_mm)
    ]
```

#### Soft scoring
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

**M3 Deliverables:** See milestones.md

---

## Milestone 4: AI Explanations + Pitch
### "AI explains matches + generates pitch"

### Module 9: OpenRouter API Integration

**Goal:** Generate match explanations via OpenRouter (access to multiple LLM providers).

#### 9.1 API setup
```python
from openai import AsyncOpenAI
from src.config import settings

# OpenRouter uses OpenAI-compatible API
client = AsyncOpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=settings.OPENROUTER_API_KEY,
)

# Model options:
# Free: "google/gemini-2.0-flash-exp:free", "meta-llama/llama-3.3-70b-instruct:free"
# Paid: "anthropic/claude-sonnet-4", "openai/gpt-4o"

async def generate_explanation(fund: Fund, lp: LP, score: float) -> str:
    response = await client.chat.completions.create(
        model=settings.OPENROUTER_MODEL,  # Configure in .env
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
    return response.choices[0].message.content
```

#### 9.2 Caching
```python
async def get_explanation(match: Match) -> str:
    if match.explanation:
        return match.explanation  # Cached

    explanation = await generate_explanation(...)
    await db.update(match, explanation=explanation)
    return explanation
```

---

### Module 10: Pitch Generation

**Goal:** Generate LP-specific materials as drafts for GP review.

**Important:** All generated content is a **draft**. The GP reviews and edits before use.

#### 10.1 Summary generation
```python
async def generate_summary_draft(match: Match) -> str:
    """Generate draft summary - GP will review before using."""
    prompt = f"""
    Create a 1-page executive summary for {match.fund.name}
    tailored to {match.lp.name}.

    Emphasize aspects relevant to their mandate:
    "{match.lp.mandate_description}"
    """
    return await call_llm(prompt)  # Uses OpenRouter client from Module 9
```

#### 10.2 Email generation
```python
async def generate_email_draft(match: Match, tone: str = "professional") -> EmailDraft:
    """Generate draft email - GP reviews and sends from their own email client."""
    prompt = f"""
    Draft an intro email from {match.fund.name} to {match.lp.name}.
    Tone: {tone}

    Include:
    - Why we're reaching out to them specifically
    - Brief fund overview
    - Clear ask (meeting request)

    Under 200 words.
    """
    content = await call_llm(prompt)
    return EmailDraft(subject=extract_subject(content), body=extract_body(content))
```

#### 10.3 Draft review UI
```html
<!-- GP reviews generated draft -->
<div class="draft-container">
    <h3>Draft Email</h3>
    <p class="notice">Review and edit this draft before copying.</p>

    <textarea id="email-draft" rows="10">{{ draft.body }}</textarea>

    <div class="actions">
        <!-- Copy to clipboard, NOT send -->
        <button onclick="copyToClipboard()">Copy to Clipboard</button>
        <button hx-post="/drafts/{{ draft.id }}/regenerate">Regenerate</button>
    </div>
</div>
```

**Never auto-send.** The GP copies the draft to their email client, reviews it, and sends manually.

---

**M4 Deliverables:** See milestones.md

---

## Milestone 5: Production Polish
### "Production-ready with admin"

### Module 11: Production Monitoring

**Goal:** Admin dashboard and monitoring.

#### 11.1 Admin features
- User management
- Data quality metrics
- Error tracking (Sentry)
- Feedback collection

#### 11.2 Sentry setup
```python
import sentry_sdk
from src.config import settings

sentry_sdk.init(
    dsn=settings.SENTRY_DSN,
    traces_sample_rate=0.1,
)
```

#### 11.3 Feedback loop
```python
@router.post("/matches/{match_id}/feedback")
async def submit_feedback(
    match_id: UUID,
    feedback: Literal["positive", "negative"],
    reason: str | None = None
):
    await match_service.record_feedback(match_id, feedback, reason)
```

---

**M5 Deliverables:** See milestones.md

---

## Getting Started

Say "start M0" to begin. See CLAUDE.md for commands and project structure.
