# Implementation Plan: Project Consistency Fixes

Based on 4 rounds of analysis documented in `docs/CONSISTENCY-REVIEW.md`.

---

## Phase 1: Critical Fixes (CLAUDE.md + milestones.md)

These are entry-point documents that set expectations.

### 1.1 Update CLAUDE.md Tech Stack

Add to tech stack table after "Deployment | Railway":
```markdown
| **Agent Framework** | LangGraph (state machines for multi-agent debates) |
| **Agent Monitoring** | Langfuse (open source, prompt versioning) |
```

### 1.2 Update CLAUDE.md Project Documents

Add to the "Project Documents" section:
```markdown
- docs/architecture/ - Agent implementation details (LangGraph + Langfuse)
  - agents-implementation.md - State machines, base classes
  - agent-prompts.md - Versioned prompts for 12 agents
  - batch-processing.md - Scheduler and cache
  - monitoring-observability.md - Langfuse integration
```

### 1.3 Update CLAUDE.md Environment Variables

Add to "Common env vars needed":
```markdown
- `LANGFUSE_PUBLIC_KEY` - For agent monitoring (M3+)
- `LANGFUSE_SECRET_KEY` - For agent monitoring (M3+)
```

### 1.4 Rewrite milestones.md M3 Section

Current M3 says "Fund profile CRUD, Matching algorithm". Replace with:
```markdown
## M3: GP Profiles + Matching + Agent Architecture
### "See matching LPs for my fund"

**What we build:**
- Fund profile CRUD
- Deck upload + LLM extraction
- **Multi-agent debate system (4 debate types, 12 agents):**
  - Constraint Interpretation (Broad/Narrow/Synthesizer)
  - Research Enrichment (Generator/Critic/Synthesizer)
  - Match Scoring Bull/Bear (Bull/Bear/Synthesizer)
  - Batch processing for exhaustive debates
- Match results UI with score breakdown

**Agent Architecture:**
- LangGraph for orchestration
- Langfuse for monitoring and prompt versioning
- Batch jobs run nightly; results cached for months
- See `docs/architecture/` for implementation details
```

### 1.5 Expand milestones.md M4 Section

Add to M4 deliverables:
```markdown
- Learning Agent (cross-company intelligence)
- Explanation Agent (interaction learning)
- Pitch Generator/Critic/Synthesizer debate
```

---

## Phase 2: PRD Fixes

### 2.1 Expand Section 5.2 Feature Priority List

Add missing feature categories:

```markdown
Authentication (from Section 5.3):
├── F-AUTH-01: User Login [P0]
├── F-AUTH-02: Multi-tenancy [P0]
├── F-AUTH-03: Role-Based Access [P0]
└── F-AUTH-04: Invitation System [P0]

Agentic Architecture (from Section 5.6.2-5.6.3):
├── F-AGENT-01: Research Agent [P0] (M3)
├── F-AGENT-02: LLM-Interpreted Constraints [P0] (M3)
├── F-AGENT-03: Learning Agent [P0] (M3)
├── F-AGENT-04: Explanation Agent [P0] (M4)
├── F-MATCH-05: Match Feedback [P1]
├── F-MATCH-06: LP-Side Matching [P0] (M3)
└── F-MATCH-07: Enhanced Match Explanations [P0] (M4)

User Interface (from Section 5.8):
├── F-UI-01: Dashboard [P0]
├── F-UI-02: Fund Profile Form [P0]
├── F-UI-03: LP Search Interface [P0]
├── F-UI-04: Match Results View [P0]
└── F-UI-05: Admin Interface [P0]

Human-in-the-Loop (from Section 5.9):
├── F-HITL-01: Outreach Email Review [P0]
├── F-HITL-02: Match Selection [P0]
├── F-HITL-03: Fund Profile Confirmation [P0]
├── F-HITL-04: Data Import Preview [P0]
└── F-HITL-05: LP Data Corrections [P1]
```

### 2.2 Add Batch vs Real-Time Clarification

Add to Section 5.6.3 after the debate descriptions:
```markdown
#### When Debates Run

| Trigger | Processing | User Experience |
|---------|------------|-----------------|
| New fund created | Immediate (simplified) | See matches in ~30 seconds |
| New LP added | Queued for batch | Available next morning |
| Nightly batch | Full debate cycle | Comprehensive cached results |
| User requests refresh | Queued for batch | "Refreshing..." message |

**Note:** The nightly batch runs exhaustive multi-round debates. Real-time requests use cached results or simplified single-pass scoring.
```

---

## Phase 3: Curriculum Updates

### 3.1 Add Agent Architecture Modules

Insert after Module 7 (Agents):
```markdown
### Module 7b: LangGraph State Machines (M3)

**Goal:** Understand multi-agent orchestration with LangGraph.

#### 7b.1 State Machine Basics
- States, nodes, edges
- Conditional routing
- Checkpointing and persistence

#### 7b.2 Debate Pattern
- Bull/Bear/Synthesizer pattern
- Regeneration on disagreement
- Escalation to human review

### Module 7c: Langfuse Monitoring (M3)

**Goal:** Set up agent observability and prompt versioning.

#### 7c.1 Tracing Setup
- Configure Langfuse client
- Trace decorators
- Span hierarchy

#### 7c.2 Prompt Management
- Version control for prompts
- A/B testing
- Evaluation datasets
```

### 3.2 Update Module Mapping Table

```markdown
| M3 | 7b, 7c, 8 | LangGraph, Langfuse, MCP | GP profiles + agent matching |
| M4 | 9-10 | OpenRouter API, prompting, learning agents | AI explanations + pitch |
```

---

## Phase 4: Test Specification Updates

### 4.1 Add Architecture Section to m3-matching.feature.md

Ensure F-AGENT tests are clearly marked:
```gherkin
# Architecture: Multi-Agent Debates
# These tests verify the Bull/Bear/Synthesizer debate pattern

Feature: F-DEBATE Multi-Agent Match Scoring
  As the matching system
  I want to use adversarial debate for match scoring
  So that scores reflect multiple perspectives
```

### 4.2 Update test-specifications.md Index

Add a section explaining test organization:
```markdown
## Test Organization

| Category | Files | Line Count |
|----------|-------|------------|
| Foundation | m0-foundation | ~1,700 |
| Auth & Search | m1-auth-search | ~1,800 |
| Semantic Search | m2-semantic | ~1,400 |
| Matching + Agents | m3-matching | ~3,400 |
| Pitch + Learning | m4-pitch | ~2,400 |
| Production | m5-production | ~1,900 |
| E2E Journeys | e2e-journeys | ~2,200 |
| **Total** | **7 files** | **~15,000 lines** |
```

---

## Phase 5: Minor Fixes

### 5.1 Fix CLAUDE.md "27 mockups" (Actually 30)

Line 133 says "27 UI screen mockups" but there are 30 templates.

### 5.2 Reference UX Storylines

Add to CLAUDE.md Project Documents:
```markdown
- docs/product-doc/content/ux-storylines.md - User journey narratives
```

### 5.3 Standardize Terminology

Replace "agentic architecture" with "multi-agent debate architecture" for consistency:
- PRD Section 5.6.2 header
- test-specifications.md header

---

## Implementation Order

1. **CLAUDE.md** - Entry point, fixes expectations (15 min)
2. **milestones.md** - Second entry point (20 min)
3. **PRD Section 5.2** - Complete feature list (30 min)
4. **curriculum.md** - Add agent modules (45 min)
5. **test-specifications.md** - Better organization (15 min)
6. **Minor fixes** - Counts, references (10 min)
7. **Regenerate PDF** - With updated content (5 min)
8. **Commit and push** (5 min)

---

## Verification Checklist

After all fixes:
- [ ] CLAUDE.md mentions LangGraph and Langfuse
- [ ] CLAUDE.md references architecture docs
- [ ] CLAUDE.md has Langfuse env vars
- [ ] milestones.md M3 mentions multi-agent debates
- [ ] PRD Section 5.2 has ALL feature IDs
- [ ] curriculum.md has LangGraph/Langfuse modules
- [ ] Mockup count is correct (30)
- [ ] UX storylines referenced
- [ ] Terminology consistent
- [ ] PDF regenerated
