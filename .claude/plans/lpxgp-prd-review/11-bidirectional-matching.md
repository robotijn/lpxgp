## 11. Bidirectional Matching Phasing

### Current State
Docs mention bidirectional matching but it's:
- Marked as "Post-MVP" / "optional feature"
- Not clearly phased in milestones
- GP→LP dominates all current specs

### Clarification: Two-Phase Approach

**Phase 1: GP→LP (Current milestones M1-M4)**
- GP creates fund profile
- System finds matching LPs
- All 36 agents optimized for GP perspective
- GP dashboard, pitch generation, outreach tools

**Phase 2: LP→GP (Future milestone, post-M4)**
- LP creates/updates mandate
- System finds matching funds
- Agents adapted for LP perspective
- LP dashboard, fund discovery, meeting requests

### Documentation Updates Needed

#### Files to Update for Phasing Clarity

| File | Current State | Update Needed |
|------|---------------|---------------|
| `milestones.md:290` | "LP-Side Matching (Bidirectional)" buried | Move to explicit "M5: LP→GP Matching" milestone |
| `PRD-v1.md:655` | "Bidirectional Matching" section | Split into Phase 1 / Phase 2 with clear timeline |
| `features/matching.md:148` | Mixed GP/LP in same section | Separate sections for each direction |
| `roadmap.md:77` | "LP-Side Matching" in future | Formalize as M5 with dependencies |
| `test-specifications.md:41` | "F-MATCH-06: LP-Side Matching [Post-MVP]" | Keep but link to M5 |

#### Agent Architecture for Both Directions

Current agents are GP-centric. For LP→GP, we need:

| GP→LP Agent | LP→GP Equivalent | Changes Needed |
|-------------|------------------|----------------|
| Bull Agent (argues for match) | Same, but LP perspective | Different prompt focus |
| Bear Agent (argues against) | Same, but LP perspective | Different concerns |
| Relationship Mapper | Same concept | LP's network, not GP's |
| Timing Optimist | Fund timing analyst | "Is this fund at right stage?" |
| Competitive Intel | Portfolio fit analyst | "Does this fund complement my portfolio?" |
| LP Persona | GP Persona | Profile the GP team |
| Pitch Generator | Meeting Request Generator | LP initiates contact |

#### Data Model Implications

The schema already supports both directions:

```sql
-- Already designed for bidirectional
clients (
    client_type: 'gp_client' | 'lp_client'  -- Both supported
)

-- Interest tracking already bidirectional
entity_interests (
    gp_interest: 'interested' | 'rejected' | null,
    lp_interest: 'interested' | 'rejected' | null,
    -- Pipeline computed from both
)
```

#### UI Screens Already Exist

LP screens are already mocked:
- `lp-dashboard.html` - LP's view of matching funds
- `lp-fund-matches.html` - Ranked funds for LP
- `lp-fund-detail.html` - Detailed fund view for LP
- `lp-profile.html` - LP's own profile management

### Proposed Milestone Structure

```
M1: Foundation (Auth, basic UI)
M2: Semantic Search
M3: GP→LP Matching (36 agents, debate system)
M4: Pitch Generation & Outreach
─────────────────────────────────────
M5: LP→GP Matching (adapt agents for LP perspective)
M6: Bidirectional Marketplace (both active simultaneously)
```

### What to Document Now vs Later

**Document NOW (in current PRD updates):**
- Clear statement: "M1-M4 = GP→LP only"
- Agent architecture designed for future LP→GP
- Data model already bidirectional
- LP screens are placeholders for M5

**Document LATER (when starting M5):**
- Full LP→GP agent prompts
- LP-specific debate flows
- LP dashboard functionality
- LP notification preferences

### Key Message for PRD

Add to Executive Summary or Introduction:

> **Phased Approach to Bidirectional Matching**
>
> LPxGP supports matching in both directions, rolled out in phases:
>
> **Phase 1 (M1-M4):** GP→LP matching. Fund managers find and engage institutional investors.
>
> **Phase 2 (M5+):** LP→GP matching. Institutional investors discover and evaluate funds.
>
> The underlying architecture (data model, agent framework, UI components) is designed from day one to support both directions. Phase 1 focuses on GP workflows while building the foundation for Phase 2.

---

