# LPxGP Milestone Roadmap

**Philosophy:** Each milestone is independently valuable and demoable. Ship early, learn fast.

---

## Overview

| Milestone | Demo Statement | Value Delivered | CLI Skills |
|-----------|---------------|-----------------|------------|
| M0 | "Search my LP database" | Basic utility | CLAUDE.md, commands |
| M1 | "Find LPs with natural language" | Smart discovery | Skills, agents |
| M2 | "See which LPs match my fund" | Targeted outreach | MCP, data pipelines |
| M3 | "Understand WHY an LP matches" | Confidence in outreach | Claude API |
| M4 | "Generate personalized pitch" | Time savings | Advanced prompting |
| M5 | "Live system with automation" | Full product | CI/CD, deployment |

---

## Milestone 0: Foundation
### "I can search my LP database"

**Goal:** Import your existing data, make it searchable. Prove the basic concept works.

**Deliverables:**
- [ ] Project structure (backend + frontend)
- [ ] Supabase setup (tables, auth, RLS)
- [ ] LP data imported and cleaned (CLI-assisted)
- [ ] GP data imported
- [ ] Basic search UI with filters (type, strategy, geography, check size)
- [ ] LP detail page

**Demo:**
```
1. Login to LPxGP
2. Go to LP Search
3. Filter: "Public Pension" + "Private Equity" + "North America"
4. See 47 matching LPs
5. Click one, see full profile
```

**CLI Learning:**
- Module 1: CLAUDE.md for project context
- Module 2: Rules for Python/API standards
- Module 3-4: Commands (`/test`, `/lint`, `/status`)
- Use CLI for data cleaning (one-time, free)

**Duration:** 2-3 weeks

**Exit Criteria:**
- 1000+ LPs searchable
- Filters work correctly
- Can demo to a GP and they say "this is useful"

---

## Milestone 1: Smart Search
### "Find LPs using natural language"

**Goal:** Add semantic search. "LPs interested in climate tech in Europe" just works.

**Deliverables:**
- [ ] Voyage AI integration
- [ ] Generate embeddings for all LP mandates
- [ ] Semantic search endpoint
- [ ] Combined filter + semantic search
- [ ] Search results show relevance score
- [ ] Save search as preset

**Demo:**
```
1. Type: "Family offices interested in early-stage healthcare"
2. See ranked results with similarity scores
3. Results are actually relevant (not just keyword matches)
4. Combine with filter: "+ Check size > $10M"
```

**CLI Learning:**
- Module 5: Skills (create `supabase-helper` skill)
- Module 6: Agents (create `pytest-runner` agent)
- Use agents to help write embedding pipeline

**Duration:** 1-2 weeks

**Exit Criteria:**
- Semantic search returns relevant results
- Tested with 20 real queries, precision > 80%
- Noticeably better than keyword search

---

## Milestone 2: GP Profiles + Matching
### "See which LPs match my fund"

**Goal:** GPs create fund profiles, system recommends matching LPs.

**Deliverables:**
- [ ] Fund profile creation (wizard UI)
- [ ] Pitch deck upload + text extraction
- [ ] Fund thesis embedding generation
- [ ] Matching algorithm (hard filters + soft scoring)
- [ ] Match results page with scores
- [ ] Score breakdown visualization

**Demo:**
```
1. Create fund: "Growth Fund III, $200M, Tech + Healthcare, North America"
2. Upload pitch deck (optional)
3. Click "Find Matching LPs"
4. See 50 ranked matches with scores (87, 82, 79...)
5. Hover score: "Strategy: 30/30, Size: 18/20, Geography: 20/20..."
```

**CLI Learning:**
- Module 7-8: MCP + Puppeteer (enrichment pipeline)
- Module 9: N8N setup for automation
- Build enrichment workflow for missing LP data

**Duration:** 2-3 weeks

**Exit Criteria:**
- Fund creation works end-to-end
- Matching produces sensible rankings
- GP says "these matches make sense"

---

## Milestone 3: AI Explanations
### "Understand WHY an LP matches"

**Goal:** Claude explains each match with talking points and concerns.

**Deliverables:**
- [ ] Claude API integration
- [ ] Explanation generation prompt
- [ ] Explanation caching (don't regenerate)
- [ ] Talking points (3-5 bullets)
- [ ] Potential concerns
- [ ] Expandable explanation panel in UI

**Demo:**
```
1. View match: "CalPERS - Score 87"
2. Click "Why this match?"
3. See: "CalPERS has a stated focus on growth equity with
   particular interest in technology. Their recent $50M
   commitment to TechGrowth Partners indicates appetite
   for funds in your size range..."
4. Talking points: "Mention their ESG requirements", "Reference
   their emerging manager program"
```

**CLI Learning:**
- Module 10: Data import refinement
- Module 16: Match explanations (Claude API)
- Learn prompt engineering through iteration

**Duration:** 1-2 weeks

**Exit Criteria:**
- Explanations are accurate (no hallucinations)
- Explanations reference actual LP data
- GP says "this saves me hours of research"

---

## Milestone 4: Pitch Generation
### "Generate personalized outreach"

**Goal:** One-click generation of LP-specific materials.

**Deliverables:**
- [ ] Executive summary generation (1-page, PDF export)
- [ ] Outreach email generation (multiple tones)
- [ ] Edit before export
- [ ] Copy to clipboard
- [ ] Save as template

**Demo:**
```
1. View match with CalPERS
2. Click "Generate Pitch"
3. Choose: "Executive Summary" + "Warm tone email"
4. See generated content, tailored to CalPERS
5. Edit if needed
6. Download PDF / Copy email
```

**CLI Learning:**
- Module 17: Pitch generation
- Advanced prompt engineering
- PDF generation with Python

**Duration:** 1-2 weeks

**Exit Criteria:**
- Generated content is professional quality
- GP would actually send the email (with minor edits)
- Export works (PDF, clipboard)

---

## Milestone 5: Production Polish
### "Live system with real users"

**Goal:** Production-ready with automation and monitoring.

**Deliverables:**
- [ ] Docker deployment
- [ ] CI/CD with GitHub Actions
- [ ] Admin dashboard (user management, data quality)
- [ ] Automated enrichment (N8N + Puppeteer nightly)
- [ ] Error tracking (Sentry)
- [ ] Feedback collection ("Was this match relevant?")
- [ ] Basic analytics

**Demo:**
```
1. Show admin dashboard
2. "Last night's enrichment: 47 LPs updated, 3 failed"
3. "Data quality: 78% average score, 12 LPs need review"
4. "User feedback: 89% of matches marked 'relevant'"
```

**CLI Learning:**
- Module 18-19: Docker, CI/CD, production
- Full deployment pipeline

**Duration:** 2-3 weeks

**Exit Criteria:**
- System runs without manual intervention
- Errors are caught and alerted
- Ready for paying users

---

## Timeline Summary

```
Week 1-3:   M0 - Foundation (search works)
Week 4-5:   M1 - Smart Search (semantic)
Week 6-8:   M2 - Matching (GP profiles, scores)
Week 9-10:  M3 - Explanations (AI insights)
Week 11-12: M4 - Pitch Generation (outreach)
Week 13-15: M5 - Production (deploy, automate)
```

**Total: ~15 weeks** (with buffer for learning and iteration)

---

## Decision Points

After each milestone, ask:

1. **M0 → M1:** Is basic search enough? Or do users need semantic?
2. **M1 → M2:** Should we add more LP data before matching?
3. **M2 → M3:** Are explanations necessary? Or is score enough?
4. **M3 → M4:** Do GPs want generated pitches? Or just insights?
5. **M4 → M5:** Ready for production? Or more polish needed?

You can STOP at any milestone and have a useful product.

---

## What's NOT in Milestones (Future)

- OAuth (Google/LinkedIn login) - use email/password for now
- Mobile optimization
- CRM integrations
- Team collaboration features
- Outreach tracking (sent → response → meeting)
- Billing/payments

These come AFTER you have paying users who ask for them.

---

## Getting Started

**Next action:** Start Milestone 0

```bash
# Create project structure
mkdir -p backend/src/{api,models,services}
mkdir -p frontend/src/{components,pages,hooks}
mkdir -p supabase/migrations
mkdir -p docs/prd

# Initialize Python project
cd backend && uv init

# Initialize React project
cd frontend && npm create vite@latest . -- --template react-ts
```

Say "start M0" when ready.
