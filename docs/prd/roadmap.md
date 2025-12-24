# MVP Definition & Roadmap

[← Back to Index](index.md)

---

## 9.1 Milestone Overview

| Milestone | Demo Statement | Scope |
|-----------|---------------|-------|
| **M0** | "Data is imported and clean" | Supabase setup, data import, cleaning |
| **M1** | "Search LPs on lpxgp.com" | Auth, RLS, full-text search, Railway deploy |
| **M2** | "Natural language search works" | Voyage AI embeddings, semantic search |
| **M3** | "See matching LPs for my fund" | Fund CRUD, agent debates, Langfuse |
| **M4** | "AI explains matches + generates pitch" | Pitch debate, learning agents, PDF export |
| **M5** | "Production-ready with admin" | Admin dashboard, Sentry, monitoring |

---

## 9.2 Milestone Details

### M0: Setup + Data Import
- Project structure (Python monolith)
- Supabase project + tables
- Import existing LP/GP data
- Data cleaning with Claude CLI
- **Exit:** `uv run pytest` passes, localhost:8000/lps shows data

### M1: Auth + Search + Deploy
- Supabase Auth UI (no custom login forms)
- Row-Level Security (RLS)
- LP full-text search API with filters
- Search UI (Jinja2 + HTMX)
- **Deploy to Railway + CI/CD**
- **Exit:** lpxgp.com live, can register/login/search

### M2: Semantic Search
- Voyage AI integration
- LP embeddings (pgvector)
- Semantic search endpoint
- Combined filters + semantic
- **Exit:** "climate tech investors" returns relevant results

### M3: GP Profiles + Matching + Agent Architecture
- Fund profile CRUD with deck upload
- **Multi-agent debate system** (14 debate teams, 42 agents)
- LangGraph state machines + Langfuse monitoring
- **Matching Architecture (Quality First):**
  - Initial match: async job queue (5 min to 24 hours)
  - Cached results: load instantly for GP
- **Exit:** Create fund → see matches with score breakdown

### M4: AI Explanations + Pitch + Learning
- Pitch generation debate (Generator/Critic/Synthesizer)
- Explanation Agent (learns from GP interactions)
- Learning Agent (cross-company intelligence)
- Summary + email generation (human-in-loop)
- PDF export
- **Exit:** Explanations accurate, PDF download works

### M5: Production Polish
- Admin dashboard (user management, data quality)
- Role-based access (Admin, Member, Viewer)
- Sentry integration
- Performance optimization (< 500ms p95)
- **Exit:** Admin works, no Sentry errors for 24h

---

## 9.3 Post-MVP Features

> **Note:** Full milestone roadmap is in `docs/milestones.md`. The phases below are:
> - M6: Data Quality + Financial Analyst
> - M7: Bidirectional LP->GP Matching
> - M8: External Integrations

**M6: Data Enrichment & Analyst Tools:**
- Financial Analyst user role
- AI-prioritized work queue
- Document upload + extraction
- Internet research agents
- Data Health dashboard

**M7: LP-Side Matching (Bidirectional):**
- LP client onboarding
- LP mandate profiles
- LP->GP matching (same agents, reversed perspective)
- LP dashboard, watchlist, pipeline
- Meeting request generation
- Mutual interest detection

**M8: Integrations:**
- Email sync (Gmail, Microsoft)
- Calendar sync
- CRM integrations (HubSpot, Salesforce)

---

## 9.4 Out of Scope for MVP

- OAuth providers (Google, LinkedIn login)
- AI profile extraction from decks
- Match feedback learning loop
- Actual deck modification (PPTX)
- Advanced analytics
- Mobile optimization
- CRM integrations

---

[Next: User Stories →](user-stories.md)
