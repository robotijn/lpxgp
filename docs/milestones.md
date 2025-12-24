# LPxGP Milestone Roadmap

**Philosophy:** Each milestone is independently valuable, demoable, and **live on lpxgp.com**.

**See CLAUDE.md for tech stack**

---

## Overview

| Milestone | Focus | Demo Statement |
|-----------|-------|----------------|
| M0 | Setup | "Data imported, schema ready" |
| M1 | Foundation | "Can search LPs, site is live" |
| M2 | Semantic | "Natural language search works" |
| M3 | Matching | "42 agents find and score LP matches" |
| M4 | Content | "AI generates pitches and explanations" |
| M5 | Operations | "GPs can track outreach, admins can manage" |
| M6 | Data Quality | "Analysts curate data, health dashboards work" |
| M7 | Bidirectional | "LPs can discover and track funds" |
| M8 | Integrations | "Email, calendar, CRM connected" |

**Post-MVP:** Learned ensemble weights, advanced automation, data enrichment APIs

---

## Guiding Principles

1. **Business Value First** - Each milestone delivers usable functionality
2. **Core Before Connections** - Build solid matching before external integrations
3. **GP First, LP Second** - Prove value for GPs before expanding to LPs
4. **Data Quality is Foundational** - Good data = good matches

---

## M0: Setup + Data Import
### "Data imported, schema ready"

**What we build:**
- Project structure (Python + FastAPI + HTMX)
- Supabase schema with two-database model
- Import existing LP/GP data into Market DB
- Data cleaning with Claude CLI

**Two-Database Architecture:**
```sql
-- Market Data (Intelligence Layer)
companies (id, name, type, lp_type, aum_usd_mm, strategies, ...)
people (id, full_name, email, linkedin_url, ...)
company_people (company_id, person_id, title, is_decision_maker, ...)

-- Client Data (Application Layer)
clients (id, company_id, client_type, subscription_tier, ...)
users (id, client_id, email, role, ...)
```

**Deliverables:**
- [ ] main.py + base.html + Supabase tables
- [ ] Two-database schema implemented
- [ ] LP market data imported
- [ ] GP market data imported
- [ ] CDN setup (HTMX + Tailwind, no npm)

**CLI Learning:**
- Module 1: CLAUDE.md
- Module 2: Commands (`/status`, `/test`)

**Exit Criteria:**
- [ ] `uv run pytest` passes
- [ ] localhost:8000/health returns 200
- [ ] Market data queryable

**Demo:** Local only - show Supabase dashboard with your data

---

## M1: Auth + Search + Deploy
### "Can search LPs, site is live"

**What we build:**
- Supabase Auth UI (don't build custom login forms)
- Row-Level Security (multi-tenant)
- LP full-text search (no embeddings yet)
- Basic GP dashboard
- **Deploy to Railway**
- **CI/CD pipeline (GitHub Actions)**

**Deliverables:**
- [ ] Auth: Supabase Auth UI (register, login, logout)
- [ ] RLS policies for multi-tenancy
- [ ] API: GET /api/v1/lps with filters
- [ ] UI: Login + LP search page
- [ ] UI: Simple GP dashboard
- [ ] **GitHub Actions: test -> deploy to Railway**
- [ ] **Live at lpxgp.com**

**CLI Learning:**
- Module 3: Project rules
- Module 4: GitHub Actions CI/CD
- Module 5: HTMX patterns

**Exit Criteria:**
- [ ] lpxgp.com shows login page
- [ ] Can register, login, search LPs
- [ ] Push to main -> auto deploys
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

**What we build:**
- Voyage AI embeddings for LPs
- Semantic search endpoint
- Combined filters + semantic ranking

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

## M3: GP Profiles + 42-Agent Matching
### "42 agents find and score LP matches"

**What we build:**
- Fund profile CRUD (GP creates fund)
- Deck upload + LLM extraction
- **Full 42-agent system:**
  - 14 Debate Teams × 3 agents each (Bull/Bear/Synthesizer pattern)
  - Categories: Constraint Interpretation (3), Research (3), Match Scoring (4), Content Generation (4)
- Batch processing for top N matches
- Match results UI with score breakdown

**Agent Architecture:**
```
Stage 1: Fast Filter (hard constraints + soft scores)
    |
    v
Stage 2: Deep Analysis (42 agents on top 50)
    |
    v
Cached Results (ready for GP to view)
```

**14 Debate Teams (42 Agents):**

*Constraint Interpretation (3 teams = 9 agents):*
1. LP Mandate Interpretation (Broad + Narrow + Synthesizer)
2. GP Strategy Interpretation (Expander + Refiner + Synthesizer)
3. Regulatory Compliance (Permissive + Conservative + Synthesizer)

*Research & Enrichment (3 teams = 9 agents):*
4. LP Research (Generator + Critic + Synthesizer)
5. GP Research (Researcher + Validator + Synthesizer)
6. Market Intelligence (Analyzer + Skeptic + Synthesizer)

*Match Scoring (4 teams = 12 agents):*
7. Strategy Alignment (Bull + Bear + Synthesizer)
8. Timing Analysis (Optimist + Skeptic + Synthesizer)
9. Relationship Potential (Builder + Barrier Finder + Synthesizer)
10. Overall Match (Bull + Bear + Synthesizer)

*Content Generation (4 teams = 12 agents):*
11. Email Pitch (Generator + Critic + Synthesizer)
12. Executive Summary (Generator + Critic + Synthesizer)
13. Meeting Prep (Generator + Critic + Synthesizer)
14. Follow-up Content (Generator + Critic + Synthesizer)

**Fund Onboarding Flow:**
1. Deck upload -> LLM extraction
2. GP confirms extracted data
3. Questionnaire for gaps
4. Save fund profile

**Agent Implementation:**
- LangGraph for state machine orchestration
- Langfuse for monitoring and prompt versioning
- See `docs/architecture/` for details

**Deliverables:**
- [ ] API: CRUD /api/v1/funds
- [ ] API: Deck upload + LLM extraction
- [ ] Fund onboarding wizard (deck -> confirm -> questionnaire)
- [ ] LangGraph state machines for all 14 debate teams
- [ ] Manager layer synthesis
- [ ] Langfuse monitoring setup
- [ ] Batch job queue for match generation
- [ ] UI: Match results with score breakdown
- [ ] UI: Debate confidence visualization

**CLI Learning:**
- Module 7b: LangGraph state machines
- Module 7c: Langfuse monitoring
- Module 8: MCP fundamentals

**Exit Criteria:**
- [ ] Create fund -> see matches with scores
- [ ] Hover score -> see Bull/Bear breakdown
- [ ] Agent traces visible in Langfuse
- [ ] Live on lpxgp.com

**Demo:**
```
1. Create fund: "$200M Growth, Tech, US"
2. Click "Find Matches"
3. See ranked LPs with scores + confidence
4. Hover -> see Bull/Bear breakdown
5. (Admin) Show Langfuse trace of debate
```

---

## M4: Pitch Generation + Explanations
### "AI generates pitches and explanations"

**What we build:**
- Pitch generation from debates (uses Pitch debate output)
- LP-specific executive summaries
- Personalized outreach emails (copy to clipboard, no auto-send)
- Human-in-loop review flow
- PDF export

**Human-in-Loop Flow:**
- Generate content -> GP reviews/edits -> copy to clipboard
- No auto-send functionality
- GP feedback improves future explanations

**Deliverables:**
- [ ] API: GET /api/v1/matches/{id}/pitch
- [ ] API: GET /api/v1/matches/{id}/email-draft
- [ ] UI: Pitch panel with talking points
- [ ] UI: Email editor with copy to clipboard
- [ ] UI: PDF export
- [ ] Human review workflow (generate -> review -> copy)

**CLI Learning:**
- Module 9: LLM API (OpenRouter)
- Module 10: Prompt engineering

**Exit Criteria:**
- [ ] View match -> see pitch
- [ ] Generate email -> copy to clipboard
- [ ] Download PDF summary
- [ ] Live on lpxgp.com

**Demo:**
```
1. View match -> "Why this LP?"
2. See explanation + talking points
3. Generate email -> copy
4. Generate summary -> download PDF
```

---

## M5: Shortlist + Pipeline + Admin Foundation
### "GPs can track outreach, admins can manage"

**What we build:**
- GP Shortlist (add/remove LPs)
- Outreach pipeline tracking (manual stage updates)
- Activity logging
- Admin dashboard structure
- Basic team management

**Outreach Pipeline Stages:**
```
identified -> shortlisted -> researching ->
contacted -> awaiting_response -> responded ->
meeting_scheduled -> meeting_completed ->
dd_in_progress -> committed/passed
```

**Admin Dashboard Structure:**
```
Admin
+-- Overview (stats)
+-- CLIENTS
|   +-- GP Clients
|   +-- LP Clients (placeholder)
|   +-- Users
+-- MARKET DATA
|   +-- Companies
|   +-- People
+-- SYSTEM
    +-- Health
    +-- Jobs
```

**Deliverables:**
- [ ] API: Shortlist CRUD
- [ ] API: Pipeline stage updates
- [ ] UI: Shortlist page with pipeline columns
- [ ] UI: LP card with activity timeline
- [ ] UI: Manual stage updates (drag-and-drop or buttons)
- [ ] Admin: Dashboard navigation structure
- [ ] Admin: GP Clients list
- [ ] Admin: Users list
- [ ] Admin: Market Companies list
- [ ] Admin: Market People list
- [ ] Team: Invite members, role assignment

**Exit Criteria:**
- [ ] GP can shortlist LPs
- [ ] GP can move LPs through pipeline stages
- [ ] Activity logged on LP card
- [ ] Admin can view clients and users
- [ ] Live on lpxgp.com

**Demo:**
```
1. View LP match -> Add to Shortlist
2. Move LP through pipeline stages
3. See activity timeline
4. Login as admin -> see dashboard
```

---

## M6: Data Quality + Financial Analyst
### "Analysts curate data, health dashboards work"

**What we build:**
- Financial Analyst user role
- Analyst dashboard with AI-prioritized queue
- Document upload + extraction (pitch decks, PDFs)
- Agentic internet research (with human validation)
- Data Health dashboard
- GP Health dashboard (funnel metrics)

**User Roles:**
| Role | Market Data | Client Data | Admin |
|------|-------------|-------------|-------|
| Admin | Full CRUD | Full CRUD | Full access |
| Financial Analyst | Full CRUD | View only | No access |
| GP/LP User | View only | Own client only | No access |

**Financial Analyst Workflow:**
```
1. Check priority queue (AI scores what needs attention)
2. Work on record:
   - View missing fields
   - Accept/reject AI research suggestions
   - Upload document for extraction
   - Manual entry
3. Validate and save
```

**Health Dashboards:**
- **Data Health:** Quality scores, field completeness, freshness, analyst activity
- **GP Health:** Funnel (recommendations -> committed), conversion rates, bottlenecks

**Deliverables:**
- [ ] User role: financial_analyst
- [ ] Analyst dashboard with priority queue
- [ ] AI priority scoring algorithm
- [ ] Document upload endpoint
- [ ] PDF/PPT extraction pipeline
- [ ] Internet research agent (find missing data)
- [ ] Human-in-loop validation UI
- [ ] Data Health dashboard with charts
- [ ] GP Health dashboard with funnel
- [ ] Quality score tracking per company

**Exit Criteria:**
- [ ] Analyst can see prioritized work queue
- [ ] Upload pitch deck -> extract fund info
- [ ] AI suggests data -> analyst validates
- [ ] Data Health shows quality trends
- [ ] GP Health shows conversion funnel
- [ ] Live on lpxgp.com

**Demo:**
```
1. Login as analyst
2. See priority queue with AI scores
3. Upload pitch deck -> review extracted data
4. Accept AI suggestions
5. View Data Health dashboard
```

---

## M7: LP->GP Bidirectional Matching
### "LPs can discover and track funds"

**What we build:**
- LP client onboarding
- LP mandate profiles
- LP->GP matching (same 42 agents, reversed perspective)
- LP dashboard (mirror of GP dashboard)
- LP watchlist (equivalent of GP shortlist)
- LP interest pipeline (evaluating funds)
- Inbound request handling (GP requests meeting)
- Meeting request generation (LP initiates)
- LP Health dashboard
- Mutual interest detection

**Bidirectional Principle:**
> Whatever a GP can do with LPs, an LP should be able to do with GPs.

**LP Feature Symmetry:**
| GP Feature | LP Equivalent |
|------------|---------------|
| Fund Profile | Mandate Profile |
| LP Recommendations | Fund Recommendations |
| Shortlist | Watchlist |
| Outreach Pipeline | Interest Pipeline |
| Pitch Generation | Meeting Request Generation |

**Deliverables:**
- [ ] API: LP mandate CRUD
- [ ] API: Fund recommendations for LP
- [ ] UI: LP dashboard
- [ ] UI: Mandate profile editor
- [ ] UI: Fund recommendations list
- [ ] UI: LP watchlist
- [ ] UI: Interest pipeline (reviewing, requested, inbound, meeting, DD, committed)
- [ ] UI: Meeting request generator
- [ ] UI: Inbound GP requests list
- [ ] LP Health dashboard (funnel from LP perspective)
- [ ] Mutual interest alerts

**Exit Criteria:**
- [ ] LP can create mandate
- [ ] LP sees fund recommendations
- [ ] LP can watchlist and track funds
- [ ] LP can request meetings with GPs
- [ ] LP can accept/decline GP requests
- [ ] Mutual interest detected and shown
- [ ] Live on lpxgp.com

**Demo:**
```
1. Login as LP
2. Create mandate
3. See fund recommendations
4. Add to watchlist
5. Request meeting with GP
6. See "Mutual Interest Detected" alert
```

---

## M8: External Integrations
### "Email, calendar, CRM connected"

**What we build:**
- Email sync (Gmail OAuth, Microsoft Graph)
- Email content analysis for AI learning
- Calendar sync (Google Calendar, Microsoft Outlook)
- Scheduling links (Calendly-style)
- CRM integrations (HubSpot, Salesforce)
- User preferences for automation behavior

**Email Integration:**
- OAuth connection to mailbox
- Sync emails to/from LP contacts
- AI analysis (sentiment, topics, objections)
- Build LP communication profiles
- Stage inference from email content

**Calendar Integration:**
- OAuth connection
- Sync meetings with LPs
- Auto-detect LP meetings
- Display in outreach timeline

**Scheduling Links:**
- GP creates availability slots
- Generate LP-facing booking page
- Auto-create video meeting link
- Auto-update outreach stage on booking

**CRM Integration:**
- HubSpot: Push outreach status as deals
- Salesforce: Push as opportunities
- Bidirectional sync option
- Custom field mapping

**User Preferences:**
- Email sync mode: disabled / log_only / suggest / auto_update
- Stage update confirmation: always / major_only / never
- CRM sync direction: push / pull / bidirectional

**Deliverables:**
- [ ] Gmail OAuth integration
- [ ] Microsoft OAuth integration
- [ ] Email sync service
- [ ] Email analysis pipeline
- [ ] LP communication profiles (aggregated insights)
- [ ] Google Calendar OAuth
- [ ] Microsoft Calendar OAuth
- [ ] Calendar sync service
- [ ] Meeting display in timeline
- [ ] Scheduling link generator
- [ ] LP booking page UI
- [ ] HubSpot integration
- [ ] Salesforce integration
- [ ] User preferences UI
- [ ] Confirmation queue (for suggest mode)

**Exit Criteria:**
- [ ] Connect Gmail -> emails appear in timeline
- [ ] Connect calendar -> meetings appear
- [ ] Generate scheduling link -> LP can book
- [ ] Connect HubSpot -> outreach syncs as deals
- [ ] User can control automation level
- [ ] Live on lpxgp.com

**Demo:**
```
1. Connect Gmail
2. See email thread with LP in timeline
3. Connect calendar
4. Generate scheduling link
5. LP books via link
6. See meeting in calendar + outreach updated
```

---

## Post-MVP Features

**Only after real usage proves need.**

### Learned Ensemble Weights
- Track match outcomes (meeting -> DD -> commitment)
- Train ensemble model on successful matches
- LP-type-specific weight optimization
- Requires 6+ months of outcome data

### Advanced Automation
- Auto-schedule follow-ups
- AI-suggested optimal send times
- Bulk outreach campaigns

### Data Enrichment APIs
- Preqin API integration
- Pitchbook API integration
- Partner data feeds
- Continuous enrichment pipeline

---

## Milestone Dependencies

```
M0 (Setup)
 |
 +-- M1 (Auth + Search)
      |
      +-- M2 (Semantic Search)
           |
           +-- M3 (42-Agent Matching)
                |
                +-- M4 (Pitch Generation)
                |    |
                |    +-- M5 (Shortlist + Pipeline + Admin)
                |         |
                |         +-- M6 (Data Quality + Analyst)
                |         |
                |         +-- M7 (Bidirectional LP->GP)
                |              |
                |              +-- M8 (External Integrations)
                |
                +-- (M6 can run in parallel with M4-M5 if team available)
```

---

## Timeline Guidance (No Dates, Just Sequence)

**Phase 1: Foundation** (M0 -> M1 -> M2)
- Setup, auth, basic search
- Get live on lpxgp.com

**Phase 2: Core Value** (M3 -> M4)
- 42-agent matching
- Pitch generation
- This is the core product value

**Phase 3: Operations** (M5 -> M6)
- Pipeline tracking for GPs
- Admin tools
- Data quality tools
- These make the product usable day-to-day

**Phase 4: Expansion** (M7)
- LP-side features
- Bidirectional matching
- Doubles the addressable market

**Phase 5: Connectivity** (M8)
- External integrations
- These are convenience features, not core value
- Only build when core is proven

---

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| 42 agents from M3 | Full debate quality from the start |
| Manual pipeline first | Prove value before automation complexity |
| GP before LP | Easier to prove value, clearer user story |
| Admin in M5 | Needed for operations, not core product |
| Analyst in M6 | Data quality enables better matching |
| Integrations in M8 | Convenience, not core value |
| No timeline estimates | Focus on what, not when |

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
