# Technical Architecture

[← Back to Index](index.md)

---

## 8.1 System Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                              Internet                                │
└───────────────────────────────┬─────────────────────────────────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Supabase Cloud      │
                    │   - Auth              │
                    │   - PostgreSQL        │
                    │   - pgvector          │
                    │   - Storage           │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │   Python App          │
                    │   (Railway)           │
                    │                       │
                    │   FastAPI + Jinja2    │
                    │   + HTMX + Tailwind   │
                    └───────────┬───────────┘
                                │
                    ┌───────────┼───────────┐
                    │                       │
            ┌───────▼───────┐       ┌───────▼───────┐
            │   OpenRouter  │       │   Voyage AI   │
            │    (LLMs)     │       │  (Embeddings) │
            └───────────────┘       └───────────────┘

Future (API integrations):
┌───────────────────┐
│  External APIs    │
│  (Preqin, etc.)   │
└───────────────────┘
```

---

## 8.2 Technology Stack

| Layer | Technology | Rationale |
|-------|------------|-----------|
| **App Framework** | FastAPI (Python 3.11+) | Async, fast, great for AI integration |
| **Templating** | Jinja2 | Server-side rendering, Python native |
| **Interactivity** | HTMX (via CDN) | Hypermedia-driven, no JS framework needed |
| **Styling** | Tailwind CSS (via CDN) | Utility-first, rapid development |
| **Database** | Supabase (PostgreSQL) | Managed, reliable backups, built-in auth |
| **ORM** | supabase-py | No SQLAlchemy, direct Supabase client |
| **Vector DB** | pgvector (Supabase) | Integrated, no separate service |
| **Auth** | Supabase Auth | Built-in, handles JWT, supports OAuth |
| **Embeddings** | Voyage AI (M2+ only) | Best quality for financial domain |
| **AI/LLM** | OpenRouter (multi-model) | Multi-model access, cost flexibility with free models |
| **File Storage** | Supabase Storage | Integrated, S3-compatible |
| **PDF Parsing** | PyMuPDF + pdfplumber | Best Python PDF libraries |
| **PPTX Parsing** | python-pptx | Read/write PowerPoint |
| **CI/CD** | GitHub Actions | Integrated with repo, runs tests |
| **Hosting** | Railway | Auto-deploys from GitHub, no Docker needed |
| **Data Enrichment** | API integrations (future) | Preqin, PitchBook for institutional LP data |
| **Agent Framework** | LangGraph | State machines for multi-agent debates |
| **Agent Monitoring** | Langfuse (open source) | Self-hostable observability, prompt versioning |

---

## 8.3 Agent Implementation

The multi-agent debate architecture is implemented using LangGraph for orchestration and Langfuse for monitoring. Full implementation specifications are in:

| Document | Location | Contents |
|----------|----------|----------|
| **Agent Implementation** | `docs/architecture/agents-implementation.md` | LangGraph state machines, base agent classes, project structure |
| **Agent Prompts** | `docs/architecture/agent-prompts.md` | Complete versioned prompts for all 12 agents |
| **Batch Processing** | `docs/architecture/batch-processing.md` | Scheduler, processor, cache management |
| **Monitoring & Observability** | `docs/architecture/monitoring-observability.md` | Langfuse integration, evaluation, A/B testing |

**Framework Selection Rationale:**

| Requirement | Solution |
|-------------|----------|
| Full agent inspection | Langfuse traces every debate with full conversation history |
| Prompt versioning | Langfuse Prompt Registry with semantic versioning |
| A/B testing | Langfuse supports traffic splitting between prompt versions |
| Self-hosting | Langfuse is MIT licensed and can be deployed on Railway |
| State machine orchestration | LangGraph handles debate cycles and regeneration |

---

## 8.4 API Design

```
/api/v1/
├── /auth
│   ├── POST   /login              # Login with email/password
│   ├── POST   /logout             # Logout (invalidate session)
│   ├── POST   /refresh            # Refresh JWT token
│   ├── POST   /reset-password     # Request password reset email
│   ├── POST   /reset-password/confirm  # Set new password with token
│   │
│   │ # Invitation flow (no public registration)
│   ├── GET    /invite/{token}     # Validate invitation token
│   └── POST   /invite/{token}/accept  # Accept invite
│
├── /invitations (admin endpoints)
│   ├── GET    /                   # List pending invitations
│   ├── POST   /                   # Create invitation
│   ├── DELETE /{id}               # Cancel invitation
│   └── POST   /{id}/resend        # Resend invitation email
│
├── /users
│   ├── GET    /me                 # Get current user profile
│   ├── PATCH  /me                 # Update current user profile
│   ├── GET    /                   # List company users (admin)
│   ├── PATCH  /{id}               # Update user role (admin)
│   └── DELETE /{id}               # Deactivate user (admin)
│
├── /companies
│   ├── GET    /me                 # Get current company
│   ├── PATCH  /me                 # Update company (admin)
│   └── GET    /                   # List all companies (super admin)
│
├── /funds
│   ├── GET    /                   # List company funds
│   ├── POST   /                   # Create fund
│   ├── GET    /{id}               # Get fund details
│   ├── PATCH  /{id}               # Update fund
│   ├── DELETE /{id}               # Delete fund
│   ├── POST   /{id}/upload-deck   # Upload pitch deck
│   ├── POST   /{id}/extract       # Extract profile from deck (AI)
│   └── POST   /{id}/generate-embedding  # Generate thesis embedding
│
├── /lps
│   ├── GET    /                   # List LPs (with filters)
│   ├── GET    /{id}               # Get LP details
│   ├── POST   /search             # Advanced search
│   ├── POST   /semantic-search    # Natural language search
│   ├── GET    /{id}/contacts      # Get LP contacts
│   ├── GET    /{id}/commitments   # Get LP commitments
│   │
│   │ # Admin only
│   ├── POST   /                   # Create LP
│   ├── PATCH  /{id}               # Update LP
│   ├── DELETE /{id}               # Delete LP
│   ├── POST   /import             # Bulk import
│   └── POST   /enrich             # Trigger enrichment
│
├── /matches
│   ├── POST   /generate           # Generate matches for fund
│   ├── GET    /                   # List matches for fund
│   ├── GET    /{id}               # Get match details
│   ├── PATCH  /{id}               # Update match (status, feedback)
│   ├── POST   /{id}/explain       # Regenerate explanation
│   └── DELETE /{id}               # Dismiss match
│
├── /pitches
│   ├── POST   /summary            # Generate LP-specific summary
│   ├── POST   /email              # Generate outreach email
│   ├── GET    /                   # List generated pitches
│   └── GET    /{id}               # Get pitch content
│
└── /admin
    ├── GET    /stats              # Platform statistics
    ├── GET    /import-jobs        # List import jobs
    ├── GET    /import-jobs/{id}   # Get job status
    ├── POST   /import-jobs/{id}/retry  # Retry failed job
    ├── GET    /enrichment-queue   # View enrichment queue
    └── POST   /enrichment/run     # Trigger enrichment batch
```

---

[Next: Roadmap →](roadmap.md)
