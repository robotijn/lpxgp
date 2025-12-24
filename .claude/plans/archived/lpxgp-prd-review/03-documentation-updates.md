## 3. Documentation Updates (36 Agents)

Update all references from "12 agents" to "36 agents" and add new debate descriptions.

### Files to Update

| File | Changes Needed |
|------|----------------|
| `docs/product-doc/build_pdf.py` | Cover stats, tagline (already captured) |
| `docs/prd/PRD-v1.md` | Agent architecture section, debate descriptions |
| `docs/prd/technical.md` | Technical agent specs |
| `docs/prd/roadmap.md` | Milestone scope if agents mentioned |
| `docs/prd/index.md` | Overview if agents mentioned |
| `docs/milestones.md` | Agent-related milestones |
| `docs/architecture/agents-implementation.md` | Add 7 new debate implementations |
| `docs/architecture/agent-prompts.md` | Add 21 new agent prompts + 3 manager prompts |
| `docs/CONSISTENCY-REVIEW.md` | Update consistency notes |

### New Content to Add

**7 New Debates (21 agents):**
1. Relationship Intelligence (Mapper + Critic + Synthesizer)
2. Timing Analysis (Optimist + Skeptic + Synthesizer)
3. Competitive Intelligence (Scout + Critic + Synthesizer)
4. Objection Handling (Anticipator + Stress-Tester + Synthesizer)
5. LP Persona (Builder + Validator + Synthesizer)
6. Market Context (Analyst + Skeptic + Synthesizer)
7. Prioritization (Ranker + Challenger + Synthesizer)

**Manager Layer (3 agents):**
1. Strategic Advisor
2. Outreach Orchestrator
3. Brief Compiler

### PRD Sections to Update/Add
- Agent Architecture Overview (update count, add diagram)
- New debate descriptions with agent roles
- Manager layer description
- Caching strategy
- Batch processing flow
- Learning loop specification
- Confidence gating rules

---

