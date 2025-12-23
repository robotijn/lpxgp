---
description: Load and review a specific PRD review plan section
allowed-tools: Read, Glob
---

Load plan section: $ARGUMENTS (section number 01-20 or "index")

## Plan Sections Available

The PRD review plan is split into sections in `.claude/plans/lpxgp-prd-review/`:

- 00-index.md - Navigation and overview
- 01-tagline.md - Brand messaging
- 02-agent-architecture.md - 36-agent system design
- 03-documentation-updates.md - Doc sync requirements
- 04-agent-prompts.md - Prompt templates (sections 4-8)
- 09-data-architecture.md - Database design
- 10-ensemble-weights.md - Scoring algorithms
- 11-bidirectional-matching.md - Two-way matching
- 12-outreach-pipeline.md - Email/calendar workflow
- 13-team-onboarding.md - User onboarding
- 14-email-calendar.md - Integration specs
- 15-admin-dashboard.md - Admin UI
- 16-financial-analyst.md - Data enrichment role
- 17-health-dashboards.md - System monitoring
- 18-bidirectional-symmetry.md - LP/GP symmetry
- 19-milestones.md - Roadmap updates
- 20-analyst-tooling.md - Research tools

## Actions

1. Read the requested section
2. Summarize key points
3. Identify actionable items
4. Check for dependencies on other sections

## Usage

```
/plan-section index    # Show overview
/plan-section 02       # Load agent architecture section
/plan-section 16       # Load financial analyst section
```
