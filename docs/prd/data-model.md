# Data Architecture

[← Back to Index](index.md)

---

## 6.1 Entity Relationship Diagram

```
                           ┌─────────────────────────────────────────┐
                           │              organizations              │
                           │  (id, name, is_gp, is_lp, website...)  │
                           │  CONSTRAINT: at least one role TRUE    │
                           └──────────────┬──────────────────────────┘
                                          │
              ┌───────────────────────────┼───────────────────────────┐
              │                           │                           │
              ▼                           │                           ▼
┌─────────────────────────┐               │               ┌─────────────────────────┐
│      gp_profiles        │               │               │      lp_profiles        │
│  (1:1 extension)        │               │               │  (1:1 extension)        │
│                         │               │               │                         │
│  org_id FK → orgs       │               │               │  org_id FK → orgs       │
│  investment_philosophy  │               │               │  lp_type, total_aum     │
│  notable_exits          │               │               │  mandate, check_size    │
│  thesis_embedding       │               │               │  mandate_embedding      │
└───────────┬─────────────┘               │               └───────────┬─────────────┘
            │                             │                           │
            │ 1:N                         │                           │
            ▼                             │                           │
┌─────────────────────────┐               │                           │
│         funds           │               │                           │
│  (org_id FK → gp org)   │               │                           │
│  name, strategy, size   │               │                           │
│  thesis_embedding       │               │                           │
└───────────┬─────────────┘               │                           │
            │                             │                           │
            │                             │                           │
            │     ┌───────────────────────┼───────────────────────────┘
            │     │                       │
            │     │                       ▼
            │     │           ┌─────────────────────────┐
            │     │           │        people           │
            │     │           │  (name, email, bio)     │
            │     │           │  employment_status      │
            │     │           │  auth_user_id (login)   │
            │     │           └───────────┬─────────────┘
            │     │                       │
            │     │                       │ M:N via employment
            │     │                       │
            │     │           ┌───────────┴─────────────┐
            │     │           │       employment        │
            │     │           │  (person_id, org_id)    │
            │     │           │  title, is_current      │
            │     │           │  confidence level       │
            │     │           └─────────────────────────┘
            │     │
            │     │
            ▼     ▼
┌─────────────────────────────────────────────────────────────────────┐
│                         RELATIONSHIP TABLES                          │
├─────────────────────────────────────────────────────────────────────┤
│                                                                      │
│  ┌─────────────────────┐    ┌─────────────────────┐                 │
│  │    investments      │    │  fund_lp_matches    │                 │
│  │ (FACTS - LP→Fund)   │    │ (AI RECOMMENDATIONS)│                 │
│  │                     │    │                     │                 │
│  │ - lp_org_id FK      │    │ - fund_id FK        │                 │
│  │ - fund_id FK        │    │ - lp_org_id FK      │                 │
│  │ - commitment_mm     │    │ - score             │                 │
│  │ - commitment_date   │    │ - explanation       │                 │
│  │ - source            │    │ - talking_points    │                 │
│  └─────────────────────┘    └─────────────────────┘                 │
│                                                                      │
│  ┌─────────────────────────────────────────────────┐                │
│  │               fund_lp_status                     │                │
│  │          (USER-EXPRESSED INTEREST)               │                │
│  │                                                  │                │
│  │ - fund_id FK                                     │                │
│  │ - lp_org_id FK                                   │                │
│  │ - gp_interest ('interested'/'not_interested')   │                │
│  │ - gp_interest_reason                            │                │
│  │ - lp_interest ('interested'/'not_interested')   │                │
│  │ - lp_interest_reason                            │                │
│  │ - pipeline_stage (derived state)                │                │
│  └─────────────────────────────────────────────────┘                │
│                                                                      │
└─────────────────────────────────────────────────────────────────────┘
```

**Key Design Decisions:**

| Decision | Rationale |
|----------|-----------|
| **Boolean role flags** (`is_gp`, `is_lp`) | Organizations can be BOTH (e.g., Blackstone, KKR invest in other funds) |
| **Separate profile tables** | No NULL pollution - GPs don't have 30+ empty LP fields |
| **No `primary_org_id`** | Derive current employer from `employment WHERE is_current = TRUE` |
| **Employment status on people** | Handle "unknown" employment explicitly |
| **Employment confidence** | Track data quality: 'confirmed', 'likely', 'inferred' |
| **Separate investments table** | Facts (historical investments) vs recommendations (AI matches) |
| **Bidirectional interest tracking** | GP and LP can independently express interest/rejection |
| **Pipeline stage** | Computed from (gp_interest, lp_interest, investment existence) |

---

## 6.2 Core Tables

> **Note:** Full SQL is in `supabase/migrations/`. This section documents the design.

### Organizations
Base table for all organizations. Can be GP, LP, or BOTH.

**Key fields:**
- `id` - UUID primary key
- `name` - Organization name
- `website`, `hq_city`, `hq_country` - Basic info
- `is_gp`, `is_lp` - Role flags (at least one must be TRUE)
- `created_at`, `updated_at` - Timestamps

### GP Profiles (1:1 Extension)
GP-specific fields. Only exists for organizations where `is_gp = TRUE`.

**Key fields:**
- `org_id` FK → organizations
- `investment_philosophy`, `team_size`, `years_investing`
- `notable_exits` (JSONB)
- `thesis_embedding` (VECTOR 1024)

### LP Profiles (1:1 Extension)
LP-specific fields. Only exists for organizations where `is_lp = TRUE`.

**Key fields:**
- `org_id` FK → organizations
- `lp_type` - pension, endowment, family_office, etc.
- `total_aum_bn`, `pe_allocation_pct`
- `strategies`, `geographic_preferences`, `sector_preferences` (arrays)
- `check_size_min_mm`, `check_size_max_mm`
- `mandate_description`, `mandate_embedding` (VECTOR 1024)
- `llm_summary`, `summary_embedding` - For sparse data
- `data_quality_score`, `last_verified`

### People
All professionals in the industry. Platform users have `auth_user_id` set.

**Key fields:**
- `full_name`, `email`, `phone`, `linkedin_url`
- `bio`, `notes`, `is_decision_maker`
- `auth_user_id` FK → auth.users (NULL = cannot login)
- `role` - admin, member, viewer
- `is_super_admin` - Platform-level admin
- `employment_status` - employed, unknown, unemployed, retired

> **Note:** Current employer derived from `employment WHERE is_current = TRUE`

### Employment
Links people to organizations over time. Supports multiple concurrent jobs.

**Key fields:**
- `person_id` FK → people
- `org_id` FK → organizations
- `title`, `department`
- `start_date`, `end_date`, `is_current`
- `confidence` - confirmed, likely, inferred
- `source` - linkedin, manual, import

### Invitations
Tracks pending user invitations.

**Key fields:**
- `email`, `org_id`, `role`
- `token` - Secure invitation token
- `status` - pending, accepted, expired, cancelled
- `expires_at`, `accepted_at`

### Funds
Fund profiles created by GPs.

**Key fields:**
- `org_id` FK → organizations (GP)
- `name`, `fund_number`, `status` (draft, active, closed)
- `vintage_year`, `target_size_mm`, `current_aum_mm`
- `strategy`, `sub_strategy`, `geographic_focus`, `sector_focus`
- `check_size_min_mm`, `check_size_max_mm`
- `track_record` (JSONB), `notable_exits` (JSONB)
- `management_fee_pct`, `carried_interest_pct`, etc.
- `pitch_deck_url`, `pitch_deck_text`
- `investment_thesis`, `thesis_embedding` (VECTOR 1024)

### Fund Team
Links people to funds they work on.

**Key fields:**
- `fund_id` FK → funds
- `person_id` FK → people
- `role` - Partner, Principal, Analyst
- `is_key_person`, `allocation_pct`

### Investments (Historical Facts)
Tracks historical LP investments in GP funds. These are FACTS, not recommendations.

**Key fields:**
- `lp_org_id` FK → organizations
- `fund_id` FK → funds
- `commitment_mm`, `commitment_date`
- `source` - disclosed, public, estimated, imported
- `confidence` - confirmed, likely, rumored

### Fund-LP Matches (AI Recommendations)
System-generated match recommendations between funds and LPs.

**Key fields:**
- `fund_id` FK → funds
- `lp_org_id` FK → organizations
- `score` (0-100), `score_breakdown` (JSONB)
- `explanation`, `talking_points`, `concerns`
- `debate_id` FK → agent_debates
- `expires_at` - Matches can become stale

### Fund-LP Status (User-Expressed Interest)
Tracks GP and LP interest/rejection separately.

**Key fields:**
- `fund_id`, `lp_org_id`
- `gp_interest` - interested, not_interested, pursuing
- `gp_interest_reason`, `gp_interest_by`, `gp_interest_at`
- `lp_interest` - interested, not_interested, reviewing
- `lp_interest_reason`, `lp_interest_by`, `lp_interest_at`
- `pipeline_stage` - Computed state (see below)

**Pipeline Stages:**
- recommended, gp_interested, gp_pursuing
- lp_reviewing, mutual_interest, in_diligence
- gp_passed, lp_passed, invested

### Outreach Events
Tracks the full journey from match to commitment.

**Event types:** pitch_generated, email_sent, email_opened, response_received, meeting_scheduled, meeting_held, follow_up_sent, due_diligence_started, term_sheet_received, commitment_made, commitment_declined

### Match Outcomes
Final outcomes for model training.

**Outcomes:** committed, declined_after_meeting, declined_before_meeting, no_response, not_contacted, in_progress

### Generated Pitches
**Types:** email, summary, addendum

---

## 6.2 Agent Tables

### Agent Debates
Debate sessions between agents.

**Debate types:**
- constraint_interpretation - Broad vs Narrow Interpreter
- research_enrichment - Generator + Critic
- match_scoring - Bull vs Bear
- pitch_generation - Generator + Critic

### Agent Outputs
Individual agent responses within a debate.

**Agent roles:**
- Constraint: broad_interpreter, narrow_interpreter, constraint_synthesizer
- Research: research_generator, research_critic, quality_synthesizer
- Match: bull_agent, bear_agent, match_synthesizer
- Pitch: pitch_generator, pitch_critic, content_synthesizer

### Agent Disagreements
Records of unresolved conflicts between agents.

### Agent Escalations
Human review queue for debates needing intervention.

**Escalation types:** score_disagreement, confidence_collapse, deal_breaker, data_quality, factual_error, edge_case

### Agent Critiques
Quality assessment records.

### Batch Jobs
Async processing jobs.

**Job types:** nightly_full, incremental, entity_specific, debate_rerun

### Entity Cache
Precomputed results cache.

---

## 6.3 Row-Level Security (Multi-tenancy)

RLS is enabled on all tables. Key policies:

| Table | Read Access | Write Access |
|-------|-------------|--------------|
| organizations | Own GP org + all LPs | Super admin only |
| gp_profiles | Own org | Org admins |
| lp_profiles | All authenticated | Super admin only |
| people | All authenticated | Own profile or super admin |
| employment | All authenticated | Super admin only |
| funds | Own org | Own org |
| investments | All authenticated | Super admin only |
| fund_lp_matches | Own fund matches | Super admin only |
| fund_lp_status | Own fund status | Own org |
| pitches | Own matches | Own org |

**Helper functions:**
- `current_user_org_id()` - Get user's org from employment
- `is_super_admin()` - Check if user is platform admin
- `user_works_at_gp()` - Check if user works at a GP org

---

[Next: Data Pipeline →](data-pipeline.md)
