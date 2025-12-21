# LPxGP Milestone Roadmap

**Philosophy:** Each milestone is independently valuable, demoable, and **live on lpxgp.com**.

**See CLAUDE.md for tech stack**

---

## Overview

| Milestone | Demo Statement | Live URL |
|-----------|---------------|----------|
| M0 | "Data is imported and clean" | Local only |
| M1 | "Search LPs on lpxgp.com" | Yes |
| M2 | "Natural language search works" | Auto-deploy |
| M3 | "See matching LPs for my fund" | Auto-deploy |
| M4 | "AI explains matches + generates pitch" | Auto-deploy |
| M5 | "Production-ready with admin" | Auto-deploy |

**Post-MVP:** Data integrations (APIs) - only if needed

---

## M0: Setup + Data Import
### "Data is imported and clean"

**What we build:**
- Project structure (Python monolith)
- Supabase project + tables
- Import existing LP/GP data
- Data cleaning with Claude CLI

**Deliverables:**
- [ ] main.py + base.html + Supabase tables
- [ ] Use CDN for HTMX + Tailwind (no build step)
- [ ] LP data imported and cleaned
- [ ] GP data imported

**CLI Learning:**
- Module 1: CLAUDE.md
- Module 2: Commands (`/status`, `/test`)

**Exit Criteria:**
- [ ] `uv run pytest` passes
- [ ] localhost:8000/lps shows data

**Demo:** Local only - show Supabase dashboard with your data

---

## M1: Auth + Search + Deploy
### "Search LPs on lpxgp.com"

**What we build:**
- Supabase Auth UI (don't build custom login forms)
- Row-Level Security
- LP full-text search API with filters (no embeddings yet)
- Search UI (HTMX)
- **Deploy to Railway**
- **CI/CD pipeline (GitHub Actions)**

**Deliverables:**
- [ ] Auth: Use Supabase Auth UI (register, login, logout)
- [ ] RLS policies configured
- [ ] API: GET /api/v1/lps with filters (full-text search only)
- [ ] UI: Login + LP search page (Jinja2 + HTMX)
- [ ] UI: Simple dashboard (LP count, fund status, quick actions)
- [ ] **GitHub Actions: test → deploy to Railway**
- [ ] **Live at lpxgp.com**

**CLI Learning:**
- Module 3: Project rules
- Module 4: GitHub Actions CI/CD
- Module 5: HTMX patterns

**Exit Criteria:**
- [ ] lpxgp.com shows login page
- [ ] Can register, login, search LPs
- [ ] Push to main → auto deploys
- [ ] All M1 tests pass

**Demo:**
```
1. Open lpxgp.com in browser
2. Register account
3. Search: "Public Pension" + "Private Equity"
4. Show filtered results
```

---

## M2: Semantic Search
### "Natural language search works"

**THIS milestone adds Voyage AI embeddings.** M0-M1 used Supabase full-text search, now we upgrade to semantic.

**What we build:**
- Voyage AI integration
- LP embeddings
- Semantic search endpoint
- Combined filters + semantic

**Deliverables:**
- [ ] Voyage AI configured
- [ ] Embeddings for all LPs
- [ ] API: POST /api/v1/lps/semantic-search
- [ ] UI: Natural language search box
- [ ] Auto-deploys on merge

**CLI Learning:**
- Module 6: Skills (`.claude/skills/`)
- Module 7: Agents (`pytest-runner`)

**Exit Criteria:**
- [ ] "climate tech investors" returns relevant results
- [ ] Semantic search < 2 seconds
- [ ] Live on lpxgp.com after merge

**Demo:**
```
1. Open lpxgp.com
2. Type: "Family offices in healthcare"
3. See ranked results with scores
```

---

## M3: GP Profiles + Matching + Agent Architecture
### "See matching LPs for my fund"

**What we build:**
- Fund profile CRUD
- Deck upload + LLM extraction
- **Multi-agent debate system** (4 debate types, 12 agents):
  - Constraint Interpretation (Broad/Narrow/Synthesizer)
  - Research Enrichment (Generator/Critic/Synthesizer)
  - Match Scoring Bull/Bear (Bull/Bear/Synthesizer)
- Batch processing for exhaustive debates
- Match results UI with score breakdown

**Fund Onboarding Flow:**
1. Deck upload → LLM extraction
2. GP confirms extracted data
3. Questionnaire for gaps
4. Save fund profile

**Agent Architecture:**
- LangGraph for state machine orchestration
- Langfuse for monitoring and prompt versioning
- Batch jobs run nightly; results cached for months
- See `docs/architecture/` for implementation details

**Deliverables:**
- [ ] API: CRUD /api/v1/funds
- [ ] API: Deck upload + LLM extraction
- [ ] API: Generate matches (with agent debates)
- [ ] Agent: Constraint interpretation pipeline
- [ ] Agent: Research enrichment pipeline
- [ ] Agent: Bull/Bear scoring debate
- [ ] Langfuse: Monitoring and tracing setup
- [ ] UI: Fund wizard (deck → confirm → questionnaire → save)
- [ ] Score breakdown visualization

**CLI Learning:**
- Module 7b: LangGraph state machines
- Module 7c: Langfuse monitoring
- Module 8: MCP fundamentals

**Exit Criteria:**
- [ ] Create fund → see matches
- [ ] Score breakdown visible with debate confidence
- [ ] Agent traces visible in Langfuse
- [ ] Live on lpxgp.com

**Demo:**
```
1. Create fund: "$200M Growth, Tech, US"
2. Click "Find Matches"
3. See ranked LPs with scores + confidence
4. Hover → see Bull/Bear breakdown
5. (Admin) Show Langfuse trace of debate
```

---

## M4: AI Explanations + Pitch + Learning
### "AI explains matches + generates pitch"

**What we build:**
- Pitch generation debate (Generator/Critic/Synthesizer)
- Explanation Agent (learns from GP interactions)
- Learning Agent (cross-company intelligence)
- Summary + email generation (human-in-loop)
- PDF export

**Agent Additions:**
- Pitch debate: Generator creates, Critic reviews quality, Synthesizer finalizes
- Explanation Agent: Learns which talking points resonate
- Learning Agent: Aggregates insights across all GPs (anonymized)

**Human-in-Loop Flow:**
- Generate email → GP reviews/edits → copy to clipboard
- No auto-send functionality
- GP feedback improves future explanations

**Deliverables:**
- [ ] Agent: Pitch Generator/Critic/Synthesizer debate
- [ ] Agent: Explanation Agent with interaction learning
- [ ] Agent: Learning Agent (global signals)
- [ ] API: Get explanation (with learned insights)
- [ ] API: Generate summary/email draft
- [ ] UI: Explanation panel with talking points
- [ ] UI: Email editor with copy to clipboard
- [ ] UI: PDF export
- [ ] Explanation caching with learning feedback

**CLI Learning:**
- Module 9: LLM API (OpenRouter)
- Module 10: Prompt engineering

**Exit Criteria:**
- [ ] Explanations accurate (no hallucinations)
- [ ] Pitch debate quality verified
- [ ] PDF download works
- [ ] Feedback loop recording interactions
- [ ] Live on lpxgp.com

**Demo:**
```
1. View match → "Why this LP?"
2. See explanation + learned talking points
3. Generate email → copy
4. (Show: Email was refined by Critic agent)
5. Generate summary → download PDF
```

---

## M5: Production Polish
### "Production-ready with admin"

**What we build:**
- Admin dashboard
- Error tracking (Sentry)
- Feedback collection
- Performance optimization
- Monitoring

**Deliverables:**
- [ ] Admin: User management
- [ ] Admin: Data quality stats
- [ ] Role-based access: Admin, Member, Viewer
- [ ] Sentry integration
- [ ] Feedback: "Was this match relevant?"
- [ ] All endpoints < 500ms p95

**CLI Learning:**
- Module 11: Production monitoring

**Exit Criteria:**
- [ ] Admin dashboard works
- [ ] No Sentry errors for 24h
- [ ] All tests pass, coverage > 80%

**Demo:**
```
1. Login as admin
2. Show user list, data quality
3. Show feedback stats
4. Show error tracking (empty = good)
```

---

## Post-MVP: Enrichment

**Only if needed after real usage.**

- Data integrations (Preqin API, partner feeds)
- Automated enrichment from external APIs

---

## Decision Points

| After | Question |
|-------|----------|
| M0 | Data clean enough? |
| M1 | Site works? Ready for semantic? |
| M2 | Results relevant? |
| M3 | Matches sensible? |
| M4 | Pitches usable? |
| M5 | Ready for real users? |

---

## You vs Claude

| You | Claude |
|-----|--------|
| Provide data files | Write all code |
| Set up Supabase project | Write migrations |
| Create Railway account | Set up CI/CD |
| Configure domain (lpxgp.com) | Integrate APIs |
| Set API keys (env vars) | Write tests |
| Review in browser | Iterate |

---

## Getting Started

**Next:** Start M0

You need to:
1. Create Supabase project
2. Provide LP/GP data files
3. Create Railway account (for M1 deployment)

Say "start M0" when ready.
