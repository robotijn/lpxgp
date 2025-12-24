# LPxGP Product Requirements Document

**Status:** Approved for MVP Development

This PRD is split into modular files for easier processing and maintenance.

## Document Structure

| File | Contents |
|------|----------|
| [overview.md](overview.md) | Executive Summary, Problem Statement, Solution Overview, User Personas |
| [features/](features/) | Feature Requirements (modular) |
| [data-model.md](data-model.md) | Data Architecture & Schema Definitions |
| [data-pipeline.md](data-pipeline.md) | Data Pipeline & Enrichment |
| [technical.md](technical.md) | Technical Architecture & API Design |
| [roadmap.md](roadmap.md) | MVP Definition & Milestone Roadmap |
| [user-stories.md](user-stories.md) | User Stories by Category |
| [nfr.md](nfr.md) | Non-Functional Requirements |
| [decisions.md](decisions.md) | Decisions Log |
| [appendix.md](appendix.md) | Glossary & Taxonomies |
| [test-specifications.md](test-specifications.md) | Test Coverage Summary |

## Feature Requirements (Section 5)

| File | Contents |
|------|----------|
| [features/index.md](features/index.md) | Priority Definitions & MVP Feature Order |
| [features/auth.md](features/auth.md) | F-AUTH: Authentication & Authorization |
| [features/gp-profile.md](features/gp-profile.md) | F-GP: GP Profile Management |
| [features/lp-database.md](features/lp-database.md) | F-LP: LP Database |
| [features/matching.md](features/matching.md) | F-MATCH + F-AGENT + F-DEBATE: Matching Engine & Agent Architecture |
| [features/pitch.md](features/pitch.md) | F-PITCH: Pitch Generation |
| [features/ui.md](features/ui.md) | F-UI: User Interface |
| [features/hitl.md](features/hitl.md) | F-HITL: Human-in-the-Loop |

## Quick Links

- **Start here:** [Overview](overview.md) for product vision
- **Implementation:** [Roadmap](roadmap.md) for milestone details
- **Schema:** [Data Model](data-model.md) for database tables
- **Testing:** [Test Specifications](test-specifications.md) for BDD scenarios

## Related Architecture Documents

Located in `docs/architecture/`:
- `agents-implementation.md` - LangGraph state machines, base classes
- `agent-prompts.md` - Versioned prompts for all 42 agents (14 teams)
- `batch-processing.md` - Scheduler, processor, cache
- `monitoring-observability.md` - Langfuse integration
