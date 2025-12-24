# Technical Requirements Document (TRD)

## LPxGP: GP-LP Intelligence Platform

**Version:** 1.0.0
**Last Updated:** 2025-01-15
**Status:** Active

---

## Purpose

This document describes **HOW** we build LPxGP. For **WHAT** we build, see the [Product Requirements Document (PRD)](../prd/index.md).

| Document | Focus |
|----------|-------|
| **PRD** | Features, user stories, acceptance criteria |
| **TRD** | Architecture, implementation, technical decisions |

---

## System Architecture Overview

```
                                    ┌─────────────────────────────────────┐
                                    │           INTERNET                  │
                                    └─────────────────┬───────────────────┘
                                                      │
                    ┌─────────────────────────────────┼─────────────────────────────────┐
                    │                                 │                                 │
                    ▼                                 ▼                                 ▼
        ┌───────────────────┐             ┌───────────────────┐             ┌───────────────────┐
        │   Browser/HTMX    │             │   Mobile (PWA)    │             │   API Clients     │
        │                   │             │                   │             │                   │
        │   Tailwind CSS    │             │   Future          │             │   Integrations    │
        └─────────┬─────────┘             └─────────┬─────────┘             └─────────┬─────────┘
                  │                                 │                                 │
                  └─────────────────────────────────┼─────────────────────────────────┘
                                                    │
                                    ┌───────────────▼───────────────┐
                                    │        RAILWAY CLOUD          │
                                    │                               │
                                    │   ┌───────────────────────┐   │
                                    │   │   FastAPI + Jinja2    │   │
                                    │   │   (Python 3.11+)      │   │
                                    │   └───────────┬───────────┘   │
                                    │               │               │
                                    │   ┌───────────▼───────────┐   │
                                    │   │   LangGraph Agents    │   │
                                    │   │   (42 Agents)         │   │
                                    │   └───────────┬───────────┘   │
                                    │               │               │
                                    └───────────────┼───────────────┘
                                                    │
            ┌───────────────────────────────────────┼───────────────────────────────────────┐
            │                                       │                                       │
            ▼                                       ▼                                       ▼
┌───────────────────────┐             ┌───────────────────────┐             ┌───────────────────────┐
│   SUPABASE CLOUD      │             │   EXTERNAL SERVICES   │             │   DATA SOURCES        │
│                       │             │                       │             │                       │
│  ┌─────────────────┐  │             │  ┌─────────────────┐  │             │  ┌─────────────────┐  │
│  │  Market DB      │  │             │  │   OpenRouter    │  │             │  │   CSV Import    │  │
│  │  (LP/GP Data)   │  │             │  │   (LLMs)        │  │             │  │   (Bulk data)   │  │
│  ├─────────────────┤  │             │  ├─────────────────┤  │             │  ├─────────────────┤  │
│  │  Client DB      │  │             │  │   Voyage AI     │  │             │  │   API Feeds     │  │
│  │  (Tenant Data)  │  │             │  │   (Embeddings)  │  │             │  │   (Preqin, etc) │  │
│  ├─────────────────┤  │             │  ├─────────────────┤  │             │  ├─────────────────┤  │
│  │  pgvector       │  │             │  │   Langfuse      │  │             │  │   Scraping      │  │
│  │  (Embeddings)   │  │             │  │   (Monitoring)  │  │             │  │   (LinkedIn)    │  │
│  ├─────────────────┤  │             │  ├─────────────────┤  │             │  └─────────────────┘  │
│  │  Supabase Auth  │  │             │  │   Calendar/     │  │             │                       │
│  │  (JWT/OAuth)    │  │             │  │   Email APIs    │  │             │                       │
│  └─────────────────┘  │             │  └─────────────────┘  │             │                       │
│                       │             │                       │             │                       │
└───────────────────────┘             └───────────────────────┘             └───────────────────────┘
```

---

## Technology Stack

| Layer | Technology | Purpose |
|-------|------------|---------|
| **Frontend** | Jinja2 + HTMX + Tailwind CSS (CDN) | Server-side rendering with dynamic updates |
| **Backend** | FastAPI (Python 3.11+) | Async API, WebSocket support |
| **Database** | Supabase (PostgreSQL 15) | Managed PostgreSQL with extensions |
| **Vector Store** | pgvector | Semantic search for thesis matching |
| **Authentication** | Supabase Auth | JWT tokens, OAuth providers |
| **LLM Provider** | OpenRouter | Multi-model access (Claude, GPT, open models) |
| **Embeddings** | Voyage AI | High-quality financial domain embeddings |
| **Agent Framework** | LangGraph | State machines for multi-agent orchestration |
| **Agent Monitoring** | Langfuse | Open-source observability, prompt versioning |
| **Deployment** | Railway | Auto-deploy from GitHub, cron jobs |
| **CI/CD** | GitHub Actions | Tests, linting, deployment |

---

## TRD Sections

### Core Architecture

| Document | Description |
|----------|-------------|
| [architecture.md](architecture.md) | Two-database model, API design, auth, multi-tenancy |
| [agents.md](agents.md) | 42-agent system, LangGraph state machines, debate patterns |
| [data-pipeline.md](data-pipeline.md) | Entity Resolution, import adapters, Golden Records |

### Integration & Operations

| Document | Description |
|----------|-------------|
| [integrations.md](integrations.md) | Calendar, email, CRM sync patterns |
| [infrastructure.md](infrastructure.md) | Railway deployment, CI/CD, monitoring |

---

## Key Technical Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| **Single codebase** | Monolith | Simpler deployment, faster iteration |
| **Server-side rendering** | Jinja2 + HTMX | No SPA complexity, SEO-friendly |
| **No ORMs** | supabase-py direct | Simpler, direct SQL when needed |
| **Two-database model** | Market + Client DBs | Separate shared data from tenant data |
| **Entity Resolution** | Ensemble ML + LLM | Avoid pure Bayesian priors, ground in data |
| **Agent architecture** | LangGraph | Better state management than CrewAI |
| **Observability** | Langfuse | Open source, self-hostable, full tracing |

---

## Data Flow Overview

```
┌──────────────────────────────────────────────────────────────────────────────┐
│                            DATA FLOW                                          │
├──────────────────────────────────────────────────────────────────────────────┤
│                                                                               │
│  INGESTION                    PROCESSING                    SERVING           │
│                                                                               │
│  ┌─────────┐     ┌─────────────────────────────┐     ┌─────────────────┐    │
│  │  CSV    │────▶│                             │────▶│  REST API       │    │
│  │  Files  │     │                             │     │  /api/v1/*      │    │
│  └─────────┘     │     ENTITY RESOLUTION       │     └─────────────────┘    │
│                  │                             │                             │
│  ┌─────────┐     │  ┌─────────────────────┐   │     ┌─────────────────┐    │
│  │  APIs   │────▶│  │  Blocking           │   │────▶│  HTMX Views     │    │
│  │  Feeds  │     │  │  (Phonetic + ANN)   │   │     │  (Real-time)    │    │
│  └─────────┘     │  └──────────┬──────────┘   │     └─────────────────┘    │
│                  │             │               │                             │
│  ┌─────────┐     │  ┌──────────▼──────────┐   │     ┌─────────────────┐    │
│  │  Manual │────▶│  │  ML Ensemble        │   │────▶│  Agent Debates  │    │
│  │  Entry  │     │  │  (LogReg+GBM+RF+SVM)│   │     │  (LangGraph)    │    │
│  └─────────┘     │  └──────────┬──────────┘   │     └─────────────────┘    │
│                  │             │               │                             │
│                  │  ┌──────────▼──────────┐   │     ┌─────────────────┐    │
│                  │  │  LLM Tiebreaker     │   │────▶│  Cached Results │    │
│                  │  │  (Uncertain only)   │   │     │  (Months valid) │    │
│                  │  └──────────┬──────────┘   │     └─────────────────┘    │
│                  │             │               │                             │
│                  │  ┌──────────▼──────────┐   │                             │
│                  │  │  Golden Records     │   │                             │
│                  │  │  (Merged entities)  │   │                             │
│                  │  └─────────────────────┘   │                             │
│                  │                             │                             │
│                  └─────────────────────────────┘                             │
│                                                                               │
└──────────────────────────────────────────────────────────────────────────────┘
```

---

## Security Architecture

### Authentication Flow

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│   Browser    │────▶│   FastAPI    │────▶│   Supabase   │
│              │◀────│              │◀────│   Auth       │
└──────────────┘     └──────────────┘     └──────────────┘
       │                    │                    │
       │ 1. Login form      │ 2. Validate        │
       │────────────────────▶────────────────────▶
       │                    │                    │
       │ 4. JWT Cookie      │ 3. JWT Token       │
       │◀────────────────────◀────────────────────
       │                    │                    │
       │ 5. API Request     │ 6. Verify JWT      │
       │  (with cookie)     │  (extract claims)  │
       │────────────────────▶                    │
       │                    │                    │
       │ 8. Response        │ 7. RLS Query       │
       │◀────────────────────◀────────────────────
```

### Multi-Tenancy (Row-Level Security)

```sql
-- Example RLS policy
CREATE POLICY "Users see own company data"
ON funds FOR SELECT
USING (company_id = auth.jwt() ->> 'company_id');

-- Admin override
CREATE POLICY "Admins see all"
ON funds FOR SELECT
USING (auth.jwt() ->> 'role' = 'admin');
```

---

## Related Documents

- [PRD - Product Requirements](../prd/index.md) - What we build
- [Milestones](../milestones.md) - Development roadmap
- [Test Specifications](../prd/test-specifications.md) - BDD test cases
- [M1b: IR Core](../milestones/m1b-ir-core.md) - IR team integration features
- [M9: IR Advanced](../milestones/m9-ir-events.md) - Events and advanced IR

---

## Changelog

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2025-01-15 | Initial TRD structure |
