# LPxGP Milestone Roadmap

**Philosophy:** Each milestone is independently valuable, demoable, and **live on lpxgp.com**.

**Total timeline:** ~15 working days | See CLAUDE.md for tech stack

---

## Tech Principles
- CDN for frontend libs (no npm build for MVP)
- supabase-py client (no SQLAlchemy)
- Supabase Auth UI (no custom login forms)
- Add complexity only when needed
- Human reviews all generated content before use
- No auto-send - copy to clipboard only
- Puppeteer MCP for UI verification/screenshots (not web scraping)

---

## Overview

| Milestone | Demo Statement | Duration | Live URL |
|-----------|---------------|----------|----------|
| M0 | "Data is imported and clean" | 1-2 days | Local only |
| M1 | "Search LPs on lpxgp.com" | 2-3 days | Yes |
| M2 | "Natural language search works" | 1-2 days | Auto-deploy |
| M3 | "See matching LPs for my fund" | 2-3 days | Auto-deploy |
| M4 | "AI explains matches + generates pitch" | 1-2 days | Auto-deploy |
| M5 | "Production-ready with admin" | 2-3 days | Auto-deploy |

**Post-MVP:** Data integrations (APIs) - only if needed

---

## M0: Setup + Data Import
### "Data is imported and clean"

**Duration:** 1-2 days

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

**Duration:** 2-3 days

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
- [ ] UI: Simple dashboard (recent matches, fund status, quick actions)
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

**Duration:** 1-2 days

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

## M3: GP Profiles + Matching
### "See matching LPs for my fund"

**Duration:** 2-3 days

**What we build:**
- Fund profile CRUD
- Deck upload + LLM extraction
- Matching algorithm
- Match results UI

**Fund Onboarding Flow:**
1. Deck upload → LLM extraction
2. GP confirms extracted data
3. Questionnaire for gaps
4. Save fund profile

**Deliverables:**
- [ ] API: CRUD /api/v1/funds
- [ ] API: Deck upload + LLM extraction
- [ ] API: Generate matches
- [ ] UI: Fund wizard (deck → confirm → questionnaire → save)
- [ ] Score breakdown visualization

**CLI Learning:**
- Module 8: MCP fundamentals

**Exit Criteria:**
- [ ] Create fund → see matches
- [ ] Score breakdown visible
- [ ] Live on lpxgp.com

**Demo:**
```
1. Create fund: "$200M Growth, Tech, US"
2. Click "Find Matches"
3. See ranked LPs with scores
4. Hover → see breakdown
```

---

## M4: AI Explanations + Pitch
### "AI explains matches + generates pitch"

**Duration:** 1-2 days

**What we build:**
- Claude API integration
- Explanation generation
- Summary + email generation (human-in-loop)
- PDF export

**Human-in-Loop Flow:**
- Generate email → GP reviews/edits → copy to clipboard
- No auto-send functionality

**Deliverables:**
- [ ] API: Get explanation
- [ ] API: Generate summary/email draft
- [ ] UI: Explanation panel
- [ ] UI: Email editor with copy to clipboard
- [ ] UI: PDF export
- [ ] Explanation caching

**CLI Learning:**
- Module 9: Claude API
- Module 10: Prompt engineering

**Exit Criteria:**
- [ ] Explanations accurate (no hallucinations)
- [ ] PDF download works
- [ ] Live on lpxgp.com

**Demo:**
```
1. View match → "Why this LP?"
2. See explanation + talking points
3. Generate email → copy
4. Generate summary → download PDF
```

---

## M5: Production Polish
### "Production-ready with admin"

**Duration:** 2-3 days

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

## Timeline

```
Day 1-2:    M0 - Setup + Data (local)
Day 3-5:    M1 - Auth + Search + DEPLOY TO LPXGP.COM
Day 6-7:    M2 - Semantic Search (auto-deploys)
Day 8-10:   M3 - Matching (auto-deploys)
Day 11-12:  M4 - AI + Pitch (auto-deploys)
Day 13-15:  M5 - Polish (auto-deploys)
```

**Total: ~15 working days**

After M1, every push to main auto-deploys to lpxgp.com.

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
