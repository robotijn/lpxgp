# LPxGP PRD Review Plan - Index

**Status:** In Progress (Plan Mode)
**Total Sections:** 20

## Quick Navigation

| # | Section | Status |
|---|---------|--------|
| 1 | [Cover Tagline](01-tagline.md) | ✅ Done |
| 2 | [Agent Architecture (36 agents)](02-agent-architecture.md) | ✅ Done |
| 3 | [Documentation Updates](03-documentation-updates.md) | ✅ Done |
| 4-8 | [Agent Prompts (v1.0→v1.2)](04-agent-prompts.md) | ✅ Done |
| 9 | [Data Architecture](09-data-architecture.md) | ✅ Done |
| 10 | [Learned Ensemble Weights](10-ensemble-weights.md) | ✅ Done |
| 11 | [Bidirectional Matching](11-bidirectional-matching.md) | ✅ Done |
| 12 | [Outreach Pipeline](12-outreach-pipeline.md) | ✅ Done |
| 13 | [Team Onboarding](13-team-onboarding.md) | ✅ Done |
| 14 | [Email & Calendar](14-email-calendar.md) | ✅ Done |
| 15 | [Admin Dashboard](15-admin-dashboard.md) | ✅ Done |
| 16 | [Financial Analyst](16-financial-analyst.md) | ✅ Done |
| 17 | [Health Dashboards](17-health-dashboards.md) | ✅ Done |
| 18 | [Bidirectional Symmetry](18-bidirectional-symmetry.md) | ✅ Done |
| 19 | [Revised Milestones](19-milestones.md) | ✅ Done |
| 20 | [Analyst Tooling](20-analyst-tooling.md) | ✅ Done |

## Key Decisions

| Decision | Rationale |
|----------|-----------|
| 36 agents from M3 | Full debate quality from the start |
| GP before LP | Easier to prove value, clearer user story |
| Admin in M5 | Needed for operations, not core product |
| Analyst in M6 | Data quality enables better matching |
| Integrations in M8 | Convenience, not core value |

## Milestone Roadmap

```
M0 → M1 → M2 → M3 → M4 → M5 → M6 → M7 → M8
Setup  Auth  Search Matching Pitch Ops  Data  LP    Integrations
```

## Implementation Priority

1. **Phase 1: Foundation** (M0-M2) - Setup, auth, search
2. **Phase 2: Core Value** (M3-M4) - 36-agent matching, pitch generation
3. **Phase 3: Operations** (M5-M6) - Pipeline, admin, data quality
4. **Phase 4: Expansion** (M7) - LP-side bidirectional matching
5. **Phase 5: Connectivity** (M8) - Email, calendar, CRM integrations

## Files to Update (Summary)

- `docs/prd/PRD-v1.md` - Main PRD
- `docs/milestones.md` - Roadmap
- `docs/prd/data-model.md` - Schema updates
- `docs/architecture/agent-prompts.md` - 36 agent prompts
- `supabase/migrations/` - New tables
- `docs/mockups/` - New admin/analyst screens
