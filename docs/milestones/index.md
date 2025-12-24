# LPxGP Milestone Roadmap

**Philosophy:** Each milestone is independently valuable, demoable, and **live on lpxgp.com**.

**See CLAUDE.md for tech stack**

---

## Overview

| Milestone | Focus | Demo Statement |
|-----------|-------|----------------|
| [M0](m0-setup.md) | Setup | "Data imported, schema ready" |
| [M1](m1-auth-search.md) | Foundation | "Can search LPs, site is live" |
| [M1b](m1b-ir-core.md) | **IR Core** | "IR team can look up contacts and log interactions" |
| [M2](m2-semantic.md) | Semantic | "Natural language search works" |
| [M3](m3-matching.md) | Matching | "42 agents find and score LP matches" |
| [M4](m4-pitch.md) | Content | "AI generates pitches and explanations" |
| [M5](m5-operations.md) | Operations | "GPs can track outreach, admins can manage" |
| [M6](m6-data-quality.md) | Data Quality | "Analysts curate data, health dashboards work" |
| [M7](m7-bidirectional.md) | Bidirectional | "LPs can discover and track funds" |
| [M8](m8-integrations.md) | Integrations | "Email, calendar, CRM connected" |
| [M9](m9-ir-events.md) | IR Advanced | "Entity Resolution, briefing books, MDM" |

**Post-MVP:** Learned ensemble weights, advanced automation, data enrichment APIs

---

## Guiding Principles

1. **Business Value First** - Each milestone delivers usable functionality
2. **IR Team First** - Internal adoption drives product quality and sales
3. **Core Before Connections** - Build solid matching before external integrations
4. **GP First, LP Second** - Prove value for GPs before expanding to LPs
5. **Data Quality is Foundational** - Good data = good matches

---

## Milestone Dependencies

```
M0 (Setup)
 |
 +-- M1 (Auth + Search)
      |
      +-- M1b (IR Core) ← IR team starts using immediately!
      |    |
      |    +-- M2 (Semantic Search)
      |         |
      |         +-- M3 (42-Agent Matching) → enhances IR with AI insights
      |              |
      |              +-- M4 (Pitch Generation) → adds briefing books
      |              |    |
      |              |    +-- M5 (Shortlist + Pipeline + Admin)
      |              |         |
      |              |         +-- M6 (Data Quality + Analyst)
      |              |         |
      |              |         +-- M7 (Bidirectional LP->GP)
      |              |         |    |
      |              |         |    +-- M8 (External Integrations)
      |              |         |
      |              |         +-- M9 (IR Advanced: Entity Resolution, MDM)
      |              |
      |              +-- (M6 can run in parallel with M4-M5)
      |
      +-- IR team provides feedback throughout → improves all milestones
```

---

## Timeline Guidance (No Dates, Just Sequence)

**Phase 1: Foundation** (M0 -> M1)
- Setup, auth, basic search
- Get live on lpxgp.com

**Phase 1b: IR Adoption** (M1b)
- IR team starts using immediately
- Contact lookup, event management, touchpoint logging
- Generates real usage data and feedback

**Phase 2: Intelligence** (M2 -> M3 -> M4)
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

**Phase 6: Relationship Intelligence** (M9)
- IR team features
- Event management
- Entity Resolution / MDM
- This enables internal IR use + showcases value to GPs/LPs

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
| IR & Events in M9 | Internal tool + sales showcase |
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

## Getting Started

**Next:** Start [M0: Setup + Data Import](m0-setup.md)

You need to:
1. Create Supabase project
2. Provide LP/GP data files
3. Create Railway account (for M1 deployment)

Say "start M0" when ready.
