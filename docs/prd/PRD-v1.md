# Product Requirements Document (PRD)
# LPxGP: GP-LP Intelligence Platform

**Status:** Approved for MVP Development

---

## Table of Contents

1. [Executive Summary](#1-executive-summary)
2. [Problem Statement](#2-problem-statement)
3. [Solution Overview](#3-solution-overview)
4. [User Personas](#4-user-personas)
5. [Feature Requirements](#5-feature-requirements)
   - 5.9 [Human-in-the-Loop Requirements](#59-human-in-the-loop-requirements)
6. [Data Architecture](#6-data-architecture)
7. [Data Pipeline & Enrichment](#7-data-pipeline--enrichment)
8. [Technical Architecture](#8-technical-architecture)
9. [MVP Definition](#9-mvp-definition)
10. [User Stories](#10-user-stories)
11. [Testing Strategy](#11-testing-strategy)
12. [Non-Functional Requirements](#12-non-functional-requirements)
13. [Decisions Log](#13-decisions-log)
14. [Appendix](#14-appendix)

---

## 1. Executive Summary

### 1.1 Product Vision

**LPxGP** is an AI-powered platform that helps investment fund managers (GPs) identify, qualify, and engage the right institutional investors (LPs) for their fundraising efforts.

### 1.2 Value Proposition

| For GPs | Current State | With LPxGP |
|---------|---------------|----------------|
| Finding LPs | Months of research | Instant AI-matched recommendations |
| Qualification | Guesswork | Data-driven fit scoring |
| Outreach | Generic pitches | Personalized, LP-specific materials |
| Conversion | ~5% response rate | Higher relevance = higher conversion |

### 1.3 Success Metrics

| Metric | Target |
|--------|--------|
| Time to first LP match | < 5 minutes after profile complete |
| Match relevance score | > 80% user satisfaction |
| Outreach material generation | < 2 minutes per LP |
| User activation (complete profile) | > 60% of signups |

### 1.4 Key Decisions (Confirmed)

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Database/Auth | **Supabase Cloud** | Managed, fast setup, reliable backups |
| Vector Search | **pgvector** | Integrated with Supabase PostgreSQL |
| Embeddings | **Voyage AI** | Best quality for financial domain |
| AI/LLM | **OpenRouter** | Multi-model access, cost flexibility with free models |
| MVP Priority | **A→B→C** | Search first, then matching, then pitch gen |

---

## 2. Problem Statement

### 2.1 The Fundraising Challenge

Investment fund managers spend 12-18 months raising capital. The process is:

1. **Inefficient:** GPs contact hundreds of LPs with low conversion
2. **Expensive:** Placement agents charge 1.5-2% of capital raised
3. **Opaque:** GPs don't know LP preferences, mandates, or capacity
4. **Manual:** Customizing pitches for each LP is time-consuming
5. **Relationship-driven:** Cold outreach rarely works without context

### 2.2 Why Existing Solutions Fail

| Solution | Problem |
|----------|---------|
| Placement agents | Expensive, limited capacity, conflicts of interest |
| Data providers (Preqin, PitchBook) | Raw data, no intelligence, no actionability |
| CRM systems | Track relationships, don't find new ones |
| LinkedIn | Noisy, not PE/VC focused, no matching capabilities |

### 2.3 The Data Challenge

Existing LP/GP data is:
- Scattered across CSV files and Metabase databases
- Inconsistently populated (random fields filled/empty)
- Not standardized (different naming conventions)
- Missing enrichment (no recent updates)
- Tens of thousands of records requiring cleaning

**Solution:** AI-powered data pipeline that cleans, normalizes, and enriches using imported data sources.

---

## 3. Solution Overview

### 3.1 Core Capabilities

```
┌─────────────────────────────────────────────────────────────────┐
│                          LPxGP Platform                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────────────────────────────────────────────────────┐  │
│  │                   Data Pipeline                           │  │
│  │  CSV/DB Import → Clean → Normalize → Enrich → Vectorize  │  │
│  └──────────────────────────────────────────────────────────┘  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │   GP Portal  │  │  LP Database │  │   Matching Engine    │  │
│  │              │  │              │  │                      │  │
│  │ - Profile    │  │ - Search     │  │ - Hard filters       │  │
│  │ - Deck upload│  │ - Filters    │  │ - Soft scoring       │  │
│  │ - Matches    │  │ - Semantic   │  │ - Semantic similarity│  │
│  │ - Outreach   │  │   search     │  │ - Explanations       │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────────────┐  │
│  │ Pitch Gen    │  │ Admin Panel  │  │   Data Sources       │  │
│  │              │  │              │  │                      │  │
│  │ - LP-specific│  │ - Users      │  │ - CSV import         │  │
│  │   materials  │  │ - Companies  │  │ - Manual entry       │  │
│  │ - Deck mods  │  │ - Permissions│  │ - API integrations   │  │
│  └──────────────┘  └──────────────┘  └──────────────────────┘  │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 3.2 Key Differentiators

1. **Data Quality First:** AI-powered cleaning and enrichment pipeline
2. **Semantic Matching:** Understanding investment thesis alignment, not just keywords
3. **Actionable Output:** Generate ready-to-use outreach materials
4. **Learning System:** Improves recommendations based on feedback
5. **Multi-tenant:** Companies share LP intelligence across their team

---

## 4. User Personas

### 4.1 Primary: Fund Manager (GP)

**Name:** Sarah Chen
**Title:** Partner, Emerging Growth Capital
**Context:** Raising Fund III, $200M target

**Goals:**
- Find LPs who invest in mid-market growth equity
- Prioritize LPs with emerging manager programs
- Generate personalized outreach efficiently

**Pain Points:**
- Spent 3 months on Fund II targeting wrong LPs
- Placement agent took 2% ($4M) on Fund I
- Can't keep track of which LPs fit which mandate

**Quote:** *"I need to know not just WHO to call, but WHY they'd want to talk to me."*

---

### 4.2 Secondary: Investor Relations (IR)

**Name:** Michael Torres
**Title:** VP Investor Relations, Apex Partners
**Context:** Supporting 4 partners across multiple funds

**Goals:**
- Maintain LP relationship database
- Track outreach across the firm
- Generate materials for partners

**Pain Points:**
- Data scattered across spreadsheets
- Partners duplicate LP outreach
- No visibility into firm-wide LP coverage

---

### 4.3 Admin: Platform Administrator

**Name:** Admin User
**Title:** System Administrator
**Context:** Managing platform users and data

**Goals:**
- Onboard new companies and users
- Manage permissions and access
- Monitor data quality
- Run data enrichment pipelines

---

## 5. Feature Requirements

### 5.1 Priority Definitions

| Priority | Definition | MVP? |
|----------|------------|------|
| **P0** | Must have for launch | Yes |
| **P1** | Important, soon after launch | No |
| **P2** | Nice to have | No |
| **P3** | Future consideration | No |

### 5.2 MVP Feature Priority Order

Based on confirmed priorities:

```
Priority A (First): LP Search & Database
├── F-LP-01: LP Profile Storage [P0]
├── F-LP-02: LP Search & Filter [P0]
├── F-LP-03: Semantic Search [P0]
├── F-LP-04: LP Data Import [P0]
├── F-LP-05: LP Data Cleaning Pipeline [P0]
└── F-LP-06: LP Data Enrichment [P1] (post-MVP)

Priority B (Second): Matching Engine
├── F-MATCH-01: Hard Filter Matching [P0]
├── F-MATCH-02: Soft Scoring [P0]
├── F-MATCH-03: Semantic Matching [P0]
├── F-MATCH-04: Match Explanations [P0]
├── F-MATCH-05: Match Feedback [P1] (post-MVP)
├── F-MATCH-06: LP-Side Matching [Post-MVP] (bidirectional)
└── F-MATCH-07: Enhanced Match Explanations [P0]

Priority C (Third): Pitch Generation
├── F-PITCH-01: LP-Specific Executive Summary [P0]
└── F-PITCH-02: Outreach Email Draft [P0]

Priority D: Authentication & Authorization (Section 5.3)
├── F-AUTH-01: User Login [P0]
├── F-AUTH-02: Multi-tenancy [P0]
├── F-AUTH-03: Role-Based Access [P0]
└── F-AUTH-04: Invitation System [P0]

Priority E: Multi-Agent Architecture (Section 5.6.2-5.6.3)
├── F-AGENT-01: Research Agent (Data Enrichment) [P0] (M3)
├── F-AGENT-02: LLM-Interpreted Constraints [P0] (M3)
├── F-AGENT-03: Learning Agent (Cross-Company) [P0] (M3)
└── F-AGENT-04: Explanation Agent (Interaction Learning) [P0] (M4)

Priority F: User Interface (Section 5.8)
├── F-UI-01: Dashboard [P0]
├── F-UI-02: Fund Profile Form [P0]
├── F-UI-03: LP Search Interface [P0]
├── F-UI-04: Match Results View [P0]
└── F-UI-05: Admin Interface [P0]

Priority G: Human-in-the-Loop (Section 5.9)
├── F-HITL-01: Outreach Email Review [P0]
├── F-HITL-02: Match Selection [P0]
├── F-HITL-03: Fund Profile Confirmation [P0]
├── F-HITL-04: Data Import Preview [P0]
└── F-HITL-05: LP Data Corrections [P1]
```

---

### 5.3 Authentication & Authorization

> **IMPORTANT: Invite-Only Platform**
> LPxGP is a controlled B2B platform. There is NO public registration.
> All users must be invited - either by Super Admin (for company admins)
> or by Company Admin (for team members).

#### F-AUTH-01: User Login [P0]
**Description:** Invited users can login securely
**Requirements:**
- Email/password authentication via Supabase Auth
- Password reset flow for existing users
- Session management with JWT (7-day refresh)
- No public registration - login page only
- Clear error messages (generic for security)

**Test Cases:** See TEST-AUTH-01 in Testing Strategy

#### F-AUTH-02: Multi-tenancy [P0]
**Description:** Users belong to exactly one company, data is isolated
**Requirements:**
- User belongs to exactly one company (no multi-company)
- Users only see their company's data
- Row-level security in database
- Company-level settings
- User cannot switch companies (must create new account)

**Test Cases:** See TEST-AUTH-02 in Testing Strategy

#### F-AUTH-03: Role-Based Access Control [P0]
**Description:** Different permission levels within a company
**Requirements:**
- Roles: Admin, Member, Viewer
- Admin: manage users, invite team, settings, all data
- Member: create/edit/delete own data, view shared
- Viewer: read-only access
- First user in company is automatically Admin

**Test Cases:** See TEST-AUTH-03 in Testing Strategy

#### F-AUTH-04: Super Admin Panel [P0]
**Description:** Platform-level administration for LPxGP team
**Requirements:**
- Create new companies (after sales/vetting process)
- Invite company admin (first user of each company)
- View/manage all companies and users
- View platform analytics
- Manage LP database (global)
- Trigger data enrichment jobs
- System health monitoring

**Access:** Only users with `is_super_admin = true`

**Test Cases:** See TEST-AUTH-04 in Testing Strategy

#### F-AUTH-05: User Invitations [P0]
**Description:** Invite-only access to the platform
**Requirements:**

**Super Admin invites Company Admin:**
1. Super Admin creates company in admin panel
2. Super Admin enters admin email and clicks "Send Invite"
3. System generates invitation with secure token
4. Email sent: "You've been invited to LPxGP as Admin of [Company]"
5. Link expires in 7 days
6. Clicking link → Accept Invite page (set password)
7. User created with Admin role, linked to company

**Company Admin invites Team Member:**
1. Admin goes to Settings > Team > Invite
2. Admin enters email and selects role (Member or Admin)
3. System generates invitation with secure token
4. Email sent: "You've been invited to join [Company] on LPxGP"
5. Link expires in 7 days
6. Clicking link → Accept Invite page (set password)
7. User created with specified role, linked to company

**Invitation Rules:**
- One active invitation per email address
- Expired invitations can be resent
- Accepted invitations are marked used
- Cannot invite email that already has an account
- Invitation includes: token, email, company_id, role, invited_by, expires_at

**Test Cases:** See TEST-AUTH-05 in Testing Strategy

---

### 5.4 GP Profile Management

#### F-GP-01: Fund Profile Creation [P0]
**Description:** GPs can create detailed fund profiles
**Requirements:**
- All fields from data model (see Section 6)
- Save as draft, publish when ready
- Multiple funds per company
- Profile completeness indicator

**Test Cases:** See TEST-GP-01 in Testing Strategy

#### F-GP-02: Pitch Deck Upload [P0]
**Description:** Upload and process fund pitch decks with AI-assisted profile creation
**Requirements:**
- Accept PDF and PPTX formats
- Max file size: 100MB
- Store securely in Supabase Storage

**Flow:**
1. GP uploads PDF/PPT pitch deck
2. LLM extracts fund information (strategy, size, team, track record, etc.)
3. System displays extracted fields for GP review and confirmation
4. Interactive questionnaire prompts GP for any missing required fields
5. GP reviews complete profile and approves before saving
6. Profile saved with confirmation status

**Test Cases:** See TEST-GP-02 in Testing Strategy

#### F-GP-03: AI Profile Extraction [P0]
**Description:** Auto-populate profile from uploaded deck
**Requirements:**
- Parse PDF/PPTX content
- Use LLM to extract structured data
- Present extracted data for user confirmation
- Map to profile fields

#### F-GP-04: Fund Profile Editing [P0]
**Description:** Edit and update fund profiles
**Requirements:**
- Form-based editing
- Version history (audit trail)
- Validation rules
- Auto-save drafts

**Test Cases:** See TEST-GP-04 in Testing Strategy

---

### 5.5 LP Database

#### F-LP-01: LP Profile Storage [P0]
**Description:** Store comprehensive LP profiles
**Requirements:**
- All fields from LP data model (see Section 6)
- Support for multiple contacts per LP
- Historical commitment data
- Notes and custom fields
- Data quality score per record

**Test Cases:** See TEST-LP-01 in Testing Strategy

#### F-LP-02: LP Search & Filter [P0]
**Description:** Find LPs by criteria
**Requirements:**
- Filter by: type, AUM, strategies, geography, ticket size
- Full-text search on text fields
- Save search as preset
- Export search results (CSV)
- Pagination with 50 results per page

**Test Cases:** See TEST-LP-02 in Testing Strategy

#### F-LP-03: Semantic Search [P0]
**Description:** Search LPs by meaning, not just keywords
**Requirements:**
- Vector embeddings via Voyage AI for LP mandates/descriptions
- Natural language queries: "LPs interested in climate tech in Europe"
- Similarity scoring (0-100)
- Combine with traditional filters
- Response time < 500ms

**Test Cases:** See TEST-LP-03 in Testing Strategy

#### F-LP-04: LP Data Import [P0]
**Description:** Bulk import LP data from files
**Requirements:**
- Accept CSV, Excel formats
- Field mapping interface (drag-drop or select)
- Validation and error reporting
- Duplicate detection (by name + location)
- Preview before commit
- Batch size up to 10,000 records

**Test Cases:** See TEST-LP-04 in Testing Strategy

#### F-LP-05: LP Data Cleaning Pipeline [P0]
**Description:** Standardize and normalize imported data
**Requirements:**
- Normalize strategy names to taxonomy
- Standardize geography names to ISO codes
- Parse and validate contact information
- Detect and merge duplicates
- Flag data quality issues
- Manual review queue for low-confidence records
- AI-assisted field extraction from messy data

**Test Cases:** See TEST-LP-05 in Testing Strategy

#### F-LP-06: LP Data Enrichment [P1]
**Description:** Enhance LP data using external sources
**Requirements:**
- Future API integrations (Preqin, PitchBook) for institutional data
- Bulk update support from external data providers
- Human review for enriched data before committing
- Confidence scoring for enriched fields
- Design for extensibility to new data sources

**Test Cases:** See TEST-LP-06 in Testing Strategy

---

### 5.6 Matching Engine

#### F-MATCH-01: Hard Filter Matching [P0]
**Description:** Eliminate LPs that don't meet basic criteria
**Requirements:**
- Strategy alignment check
- Geography overlap check
- Fund size within LP's range
- Track record meets minimums
- Configurable filter weights
- Fast elimination (< 100ms for 10k LPs)

**Test Cases:** See TEST-MATCH-01 in Testing Strategy

#### F-MATCH-02: Soft Scoring [P0]
**Description:** Rank remaining LPs by fit quality
**Requirements:**
- Multi-factor scoring algorithm
- Factors: sector overlap, size fit, track record, ESG alignment
- Configurable weights per factor
- Score breakdown visible to user
- Score range 0-100
- Minimum score threshold (configurable, default 50)

**Test Cases:** See TEST-MATCH-02 in Testing Strategy

#### F-MATCH-03: Semantic Matching [P0]
**Description:** Match based on investment thesis similarity
**Requirements:**
- Voyage AI embeddings for fund thesis
- Voyage AI embeddings for LP mandate
- Cosine similarity calculation
- Semantic score contributes 30% to total score
- Handle missing mandate text gracefully

**Test Cases:** See TEST-MATCH-03 in Testing Strategy

#### F-MATCH-04: Match Explanations [P0]
**Description:** Human-readable explanation of why LP matched
**Requirements:**
- AI-generated explanation (2-3 paragraphs)
- Highlight key alignment points
- Note potential concerns or gaps
- Suggest talking points (3-5 bullets)
- Include relevant LP history if available
- Cache explanations for performance

**Test Cases:** See TEST-MATCH-04 in Testing Strategy

#### F-MATCH-05: Match Feedback [P1]
**Description:** GPs provide feedback on match quality
**Requirements:**
- Thumbs up/down on matches
- "Not relevant" with reason
- "Already in contact" flag
- Use feedback to improve algorithm

---

### 5.6.1 AI Matching Architecture

> **Design Principle:** Quality above all else. Cost is not a constraint.
> **Success Metric:** Actual investment commitments, not just high match scores.

#### Quality-First Hybrid Pipeline

```
┌─────────────────────────────────────────────────────────────────────────┐
│                    QUALITY-FIRST MATCHING PIPELINE                       │
├─────────────────────────────────────────────────────────────────────────┤
│                                                                          │
│  STAGE 1: HARD FILTERS (SQL) - Eliminate impossible matches             │
│  ├── Strategy must align                                                │
│  ├── Geography must overlap                                             │
│  ├── Fund size within LP's acceptable range                             │
│  └── Track record meets LP minimums                                     │
│  OUTPUT: ~300-500 candidates from 10,000 LPs                            │
│                                                                          │
│  STAGE 2: MULTI-SIGNAL SCORING (Python + Embeddings)                    │
│  ├── Attribute matching (sector, size, ESG, etc.)                       │
│  ├── Semantic similarity (Voyage AI embeddings)                         │
│  ├── Historical patterns (collaborative signals when available)         │
│  └── Relationship signals (mutual connections, prior contact)           │
│  OUTPUT: Ranked list with preliminary scores                            │
│                                                                          │
│  STAGE 3: LLM DEEP ANALYSIS (Claude via OpenRouter)                     │
│  ├── Analyze EVERY filtered candidate with LLM                          │
│  ├── Structured reasoning about fit quality                             │
│  ├── Identify non-obvious alignment and concerns                        │
│  ├── Generate nuanced scores with confidence levels                     │
│  └── Parallel processing for speed                                      │
│  OUTPUT: LLM-validated scores + detailed reasoning                      │
│                                                                          │
│  STAGE 4: ENSEMBLE RANKING                                              │
│  ├── Combine rule-based score + LLM score + semantic score              │
│  ├── Weight by confidence and data quality                              │
│  └── Surface disagreements as "worth investigating"                     │
│  OUTPUT: Final ranked matches with multi-perspective validation         │
│                                                                          │
│  STAGE 5: EXPLANATION GENERATION                                        │
│  ├── Rich explanations from LLM analysis (already computed)             │
│  ├── Talking points tailored to LP's stated priorities                  │
│  ├── Concerns and how to address them                                   │
│  └── Suggested approach strategy                                        │
│  OUTPUT: Actionable intelligence for GP outreach                        │
│                                                                          │
│  STAGE 6: LEARNING LOOP (Continuous)                                    │
│  ├── Track all outcomes (shortlist, contact, meeting, commitment)       │
│  ├── Retrain ML models monthly on outcomes                              │
│  ├── A/B test algorithm changes                                         │
│  └── Human-in-loop validation of edge cases                             │
│                                                                          │
└─────────────────────────────────────────────────────────────────────────┘
```

#### Ensemble Scoring Weights

| Component | Weight | Source | Purpose |
|-----------|--------|--------|---------|
| **Rule-Based Score** | 25% | SQL + Python | Hard constraints, business logic |
| **Semantic Score** | 25% | Voyage AI embeddings | Thesis/mandate alignment |
| **LLM Score** | 35% | Claude analysis | Nuanced judgment, non-obvious fit |
| **Collaborative Score** | 15% | Historical patterns | "LPs like this invested in funds like this" |

#### LLM Scoring (Key Innovation)

Since cost is not a constraint, we use LLM for actual scoring, not just explanations:

```python
SCORING_PROMPT = """
You are an expert LP-GP matching analyst with 20 years of PE experience.

Analyze the fit between this Fund and LP. Be rigorous and specific.

## FUND PROFILE
{fund_data}

## LP PROFILE
{lp_data}

## HISTORICAL CONTEXT
- LP's past commitments: {lp_commitments}
- Similar funds LP has backed: {similar_funds}

## YOUR TASK

1. **Fit Analysis** (cite specific data points):
   - Strategy alignment: How well does fund strategy match LP mandate?
   - Size fit: Is fund size in LP's sweet spot or edge?
   - Track record: Does team experience meet LP's requirements?
   - Timing: Is LP likely allocating now?

2. **Non-Obvious Insights**:
   - What makes this match better/worse than surface data suggests?
   - Are there red flags the GP should know about?

3. **Scores** (0-100, with confidence 0-1):
   - overall_score, strategy_fit, size_fit, timing_fit, relationship_potential

4. **Actionable Output**:
   - talking_points: 3-5 specific points for GP to lead with
   - concerns: Issues GP should be prepared to address
   - approach_strategy: Recommended outreach approach
   - decision_maker: Who at the LP should be contacted

Return as JSON.
"""
```

**Why LLM Scoring Works:**
1. **Rich context**: Fund thesis + LP mandate are text-heavy, perfect for LLM reasoning
2. **Nuanced judgment**: "This LP backed similar funds but got burned, might be skeptical"
3. **Non-obvious patterns**: LLM can spot things rule-based systems miss
4. **Explanation built-in**: Reasoning is captured during scoring, not retrofitted

#### Bidirectional Matching

**GP → LP (Primary Flow):**
- GP creates fund, system finds matching LPs
- Ranked by fit quality, LP capacity, relationship ease

**LP → GP (Reverse Flow):**
- LPs can see which funds match their mandate
- Optional: LPs can set preferences to receive fund notifications
- See `lp_match_preferences` and `fund_lp_matches` tables in Section 6
- LP interest tracked in `fund_lp_status` table

#### Learning From Slow Feedback

**Critical Reality:** Investment sector feedback takes 12-18 months (first meeting → commitment).

**Multi-Tier Feedback Strategy:**

| Tier | Signal | Latency | Use For |
|------|--------|---------|---------|
| **1** | Match shortlisted/dismissed | Immediate | Hard filter tuning |
| **1** | Pitch generated | Immediate | Strong interest signal |
| **2** | Response received | Days-Weeks | **Key early predictor** |
| **2** | Meeting scheduled | Weeks | **Strong quality signal** |
| **3** | Due diligence started | 2-6 months | Deal progression |
| **3** | Multiple meetings | 2-6 months | Serious consideration |
| **4** | Commitment made | 6-18 months | **Ground truth** |

**Learning Phases:**

1. **Pre-Training (Day 0):** Use imported `lp_commitments` historical data to bootstrap model
2. **Proxy Metrics (Weeks 1-12):** Learn from shortlist → pitch → email → response → meeting progression
3. **Expert Feedback (Ongoing):** Prompt GPs for match quality ratings after review
4. **Outcome Validation (Month 12+):** Validate proxy model against actual commitment outcomes

#### Score Disagreement Handling

When scoring methods disagree significantly, surface this as valuable information:

```python
if std_dev(rule_score, semantic_score, llm_score, collaborative_score) > 20:
    return {
        'flag': 'scores_disagree',
        'insight': f"Rule-based sees high fit ({rule_score}) but "
                   f"LLM sees concerns ({llm_score}). Worth investigating.",
        'recommendation': 'manual_review'
    }
```

#### What NOT to Use for Core Scoring

| Approach | Why Not |
|----------|---------|
| **Agentic frameworks for batch scoring** | Core scoring is embarrassingly parallel; asyncio + direct API calls is cleaner |
| **Pure collaborative filtering** | Cold start problem severe for new funds |
| **Single-method scoring** | Each method has blind spots; ensemble catches what individuals miss |

---

### 5.6.2 Agentic Architecture

While the core scoring pipeline uses direct LLM calls, three specialized agents handle data enrichment and learning:

#### Research Agent (Data Enrichment)

**Trigger:** `data_quality_score < threshold` OR `last_verified > 6 months` OR user request

**Purpose:** Enrich sparse LP/GP profiles with external data

**Tools:**
- `perplexity_search(query)` - General research, recent news, commitment announcements
- `web_fetch(url)` - Scrape LP websites for mandate details
- `news_api(entity, months)` - Recent fund commitment announcements
- `linkedin_api(person, company)` - Verify/update contact information

**Outputs:**
- Enriched profile fields (AUM, mandate text, contacts)
- LLM-generated summary (inferences from sparse data)
- Interpreted constraints (what mandate IMPLIES - see below)

**Human Review:** All proposed changes go to review queue before commit

**Database:** See `research_jobs` and `lp_interpreted_constraints` tables in Section 6.2

#### LLM Summaries for Sparse Data

When LP data is sparse, the LLM generates a rich summary by reasoning about available signals:

```
Raw data:
  name: "Nordic Pension Fund"
  type: "pension"
  aum: NULL
  mandate: NULL

LLM Summary (generated):
  "Nordic Pension Fund is likely a Scandinavian public pension.
   Nordic pensions typically have: AUM €50-200B, strong ESG requirements,
   preference for Nordic/EU managers, long investment horizons.

   Inferred constraints:
   - Geography: EU preferred, Nordics strongly preferred
   - ESG: Required (high confidence)
   - Check size: €30-100M typical"
```

This summary gets embedded as `summary_embedding` and used in semantic matching.

#### Interpreted Constraints (LLM-Derived Hard Filters)

Mandate text contains implicit constraints that keyword matching misses:

| Mandate Says | System Interprets |
|--------------|-------------------|
| "Invests in biodiversity" | Excludes: weapons, fossil_fuels, pharma, tech_hardware, mining |
| "EU-focused growth equity" | Excludes: funds with geography NOT IN EU |
| "Fund III+ only" | Excludes: Fund I, Fund II managers |
| "ESG-integrated approach" | Requires: esg_policy = TRUE |

These interpreted constraints power the hard filter stage (Stage 1).

#### Explanation Agent (Interaction Learning)

**Trigger:** GP shortlists, dismisses, edits pitch, provides feedback

**Purpose:** Learn GP preferences from interactions to personalize recommendations

**Observes:**
- Which matches GP shortlists vs dismisses (implicit preference)
- How GP edits generated pitches (style preference)
- Explicit feedback ("this talking point was wrong")
- Time patterns (when do they engage?)

**Learns & Updates:**
- GP profile: `pitch_style_preference`, `scoring_weight_overrides`
- LP profile: "GP X found talking point Y ineffective"
- Per-GP customization of ensemble weights

**Example Learnings:**
- "Acme Capital always shortens emails" → Learn concise preference
- "Beta Partners dismisses all ESG LPs" → Reduce ESG weight for this GP
- "This GP prefers detailed track record analysis" → Emphasize historical performance

**Database:** See `gp_learned_preferences` table in Section 6.2

#### Learning Agent (Cross-Company Intelligence)

**Trigger:** Continuous, observes all outcomes across companies

**Purpose:** Aggregate learnings to improve recommendations for everyone

**Observes (Aggregated, Privacy-Safe):**
- Response rates by LP (is this LP "hot" or "cold"?)
- Strategy trends (climate funds getting 2x engagement)
- Timing patterns (Q4 allocation windows)
- Outcome correlations (what predicts commitment?)

**Learns & Updates:**
- Global LP signals: "CalPERS response rate dropped 40% this quarter"
- Market priors: "Pensions prioritizing climate in 2024"
- Model weights: Retrain ensemble on outcome data

**Database:** See `global_learned_signals` table in Section 6.2

**Privacy Boundary:**
| Can Share | Cannot Share |
|-----------|--------------|
| "LP X has 60% response rate" (aggregated) | "Company A contacted LP X" |
| "Strategy Y is trending" | Specific pitch content |
| "Q4 allocation windows are real" | Commitment amounts in negotiation |

---

### 5.6.3 Multi-Agent Debate Architecture

Quality is paramount; cost and latency are not constraints. All critical decisions use **adversarial debate** with multiple agents arguing different perspectives before synthesis.

#### Architecture Overview

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ADVERSARIAL MULTI-AGENT ARCHITECTURE                      │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  DEBATE 1: CONSTRAINT INTERPRETATION (Per LP)                                │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                      │
│  │   Broad     │◀──▶│   Narrow    │───▶│ Constraint  │ → Hard/Soft Filters  │
│  │ Interpreter │    │ Interpreter │    │ Synthesizer │                      │
│  └─────────────┘    └─────────────┘    └─────────────┘                      │
│                                                                              │
│  DEBATE 2: RESEARCH ENRICHMENT (Per Entity)                                  │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                      │
│  │  Research   │───▶│  Research   │───▶│   Quality   │ → Enriched Profile   │
│  │  Generator  │    │   Critic    │    │ Synthesizer │                      │
│  └─────────────┘    └─────────────┘    └─────────────┘                      │
│                                                                              │
│  DEBATE 3: MATCH SCORING (Per Match - Stage 3)                               │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                      │
│  │    Bull     │◀──▶│    Bear     │───▶│   Match     │ → Score + Confidence │
│  │   Agent     │    │   Agent     │    │ Synthesizer │   + Talking Points   │
│  └─────────────┘    └─────────────┘    └─────────────┘                      │
│                                                                              │
│  DEBATE 4: PITCH GENERATION (Per Pitch)                                      │
│  ┌─────────────┐    ┌─────────────┐    ┌─────────────┐                      │
│  │   Pitch     │───▶│   Pitch     │───▶│   Content   │ → Final Pitch        │
│  │  Generator  │    │   Critic    │    │ Synthesizer │                      │
│  └─────────────┘    └─────────────┘    └─────────────┘                      │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

#### Debate 1: Constraint Interpretation

When processing LP mandates, two agents with opposing perspectives interpret the constraints:

| Agent | Role | Perspective |
|-------|------|-------------|
| **Broad Interpreter** | Liberal interpretation | Finds flexibility, edge cases that could qualify |
| **Narrow Interpreter** | Conservative interpretation | Strict reading, identifies implicit exclusions |
| **Constraint Synthesizer** | Final judgment | Determines hard vs soft constraints |

**Example:**
- Mandate: "Invests in biodiversity and climate solutions"
- **Broad**: "Could include clean energy, sustainable agriculture, some tech"
- **Narrow**: "Excludes weapons, fossil fuels, pharma, mining, most tech"
- **Synthesizer**: Hard exclude weapons/fossil fuels (95% confidence), soft prefer ESG (80%)

**Database:** See `lp_interpreted_constraints` table in Section 6.2

#### Debate 2: Research Enrichment

For data enrichment, a generator-critic-synthesizer pattern ensures quality:

| Agent | Role | Focus |
|-------|------|-------|
| **Research Generator** | Enriches profiles | Perplexity, web scraping, news APIs |
| **Research Critic** | Validates quality | Source credibility, consistency, recency |
| **Quality Synthesizer** | Commits validated changes | Confidence calibration, human review flags |

**Validation Criteria:**
- Source credibility score (0-10)
- Data recency (days since publication)
- Consistency with existing data
- Confidence calibration

**Database:** See `research_jobs` and `agent_critiques` tables in Section 6.2

#### Debate 3: Match Scoring (Core)

The most critical debate - adversarial analysis of every match:

| Agent | Role | Argues |
|-------|------|--------|
| **Bull Agent** | Match Advocate | Why this GP-LP match will succeed |
| **Bear Agent** | Match Skeptic | Why this match might fail |
| **Match Synthesizer** | Final Judgment | Weighs evidence, produces score + confidence |

**Bull Agent Focus:**
- Strategy alignment points
- Relationship potential and warm intro paths
- Timing opportunities (LP actively deploying)
- Hidden strengths others might miss

**Bear Agent Focus:**
- Strategy misalignment and red flags
- Timing/capacity concerns
- Track record gaps vs LP requirements
- Relationship barriers

**Synthesizer Output:**
- Final score (0-100) with confidence interval
- Resolved vs unresolved disagreements
- Recommendation: pursue | investigate | deprioritize | avoid
- Talking points (from Bull) and concerns to address (from Bear)

**Database:** See `agent_debates`, `agent_outputs`, `agent_disagreements` tables in Section 6.2

#### Debate 4: Pitch Generation

Generated content goes through quality validation:

| Agent | Role | Checks |
|-------|------|--------|
| **Pitch Generator** | Creates personalized content | Emails, summaries, talking points |
| **Pitch Critic** | Validates quality | Factual accuracy, personalization, tone |
| **Content Synthesizer** | Approves or regenerates | Final quality gate |

**Quality Dimensions:**
- **Factual Accuracy** (0-100): Does every claim match source data?
- **Personalization** (0-100): Specific LP references, not generic?
- **Tone** (0-100): Appropriate for LP type?
- **Structure** (0-100): Clear value proposition, logical flow?

**Quality Tiers:**
- Excellent (85+): Approve immediately
- Good (70-84): Approve with suggestions
- Needs Revision (50-69): Regenerate with feedback
- Reject (<50): Fallback to template, flag for review

#### Disagreement Resolution Protocol

Since quality > latency, we use **exhaustive resolution**:

```
Step 1: Initial Debate
├── Bull and Bear analyze in parallel
├── Calculate disagreement magnitude
└── If disagreement > 20 points → Continue to Step 2

Step 2: Cross-Feedback Regeneration (up to 3 rounds)
├── Bull receives Bear's concerns → Regenerate
├── Bear receives Bull's arguments → Regenerate
├── Re-synthesize
└── If still unresolved → Continue to Step 3

Step 3: Human Escalation
├── Create escalation with full debate transcript
├── Priority based on match value and disagreement
└── Human makes final decision
```

**Escalation Triggers:**
| Trigger | Condition | Action |
|---------|-----------|--------|
| Score Disagreement | Bull - Bear > 30 points | Immediate escalation |
| Confidence Collapse | Synthesizer confidence < 0.5 | Escalation with transcript |
| Deal Breaker | Bear identifies hard exclusion | Escalation with reasoning |
| Data Quality | Critic rejects > 50% of research | Human verification required |
| Factual Error | Pitch critic finds hallucination | Block and regenerate |

**Database:** See `agent_escalations` table in Section 6.2

#### Integration with Matching Pipeline

The debate architecture enhances Stage 3 (LLM Deep Analysis):

```
Stage 1: HARD FILTERS (SQL)
         ├── Uses interpreted constraints from Debate 1
         └── Constraint Synthesizer output drives filtering

Stage 2: MULTI-SIGNAL SCORING (Python + Embeddings)
         └── Unchanged (rule-based + semantic)

Stage 3: LLM DEEP ANALYSIS → ADVERSARIAL DEBATE
         ├── Bull Agent (why match works)
         ├── Bear Agent (why match might fail)
         ├── Up to 3 regeneration rounds
         └── Match Synthesizer (final score)

Stage 4: ENSEMBLE RANKING
         ├── Rule-based (25%) + Semantic (25%) + Debate (35%) + Collaborative (15%)
         └── Uses debate confidence for weighting

Stage 5: EXPLANATION GENERATION
         ├── Directly uses debate outputs (already computed)
         ├── Bull arguments → Talking points
         └── Bear concerns → Issues to address

Stage 6: LEARNING LOOP
         └── Debate outcomes feed Learning Agent
```

#### Batch Processing Model

Debates run **asynchronously as batch jobs**, not in real-time. This enables exhaustive quality without latency constraints:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                         BATCH PROCESSING PIPELINE                            │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  NIGHTLY BATCH JOB (e.g., 2 AM)                                              │
│  ├── Identify new/changed entities since last run                           │
│  │   ├── New funds added                                                    │
│  │   ├── New LPs added                                                      │
│  │   ├── Updated fund profiles                                              │
│  │   └── Updated LP mandates                                                │
│  │                                                                          │
│  ├── Run debates for affected matches only                                  │
│  │   ├── Debate 1: Re-interpret changed LP mandates                         │
│  │   ├── Debate 2: Research enrichment for new entities                     │
│  │   ├── Debate 3: Score new fund-LP combinations                           │
│  │   └── Debate 4: Pre-generate pitches for high-score matches              │
│  │                                                                          │
│  └── Store results in database                                              │
│      ├── Cached for months until entities change                            │
│      └── Served instantly to users from cache                               │
│                                                                              │
│  INCREMENTAL UPDATES                                                         │
│  ├── Only recompute affected matches when data changes                      │
│  ├── Track entity modification timestamps                                   │
│  └── Invalidation triggers: fund_updated, lp_updated, mandate_changed       │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

**Cache Invalidation Rules:**

| Change Type | Recomputation Scope |
|-------------|---------------------|
| New fund added | All LPs scored against new fund |
| New LP added | All funds scored against new LP |
| Fund profile updated | All matches for that fund |
| LP mandate changed | Re-interpret constraints + all matches for that LP |
| Research enrichment | Affected matches only |

**Operational Benefits:**
- **No user-facing latency**: Results pre-computed and served from cache
- **Maximum quality**: Can run exhaustive 3-round debates on every match
- **Cost predictable**: Batch processing = predictable compute costs
- **Human escalations**: Resolved during business hours, results available next batch

**Database:** See `batch_jobs` and `entity_cache` tables in Section 6.2

#### When Debates Run: Quality-First Async Processing

**Design principle:** Quality over speed. Matching takes time but results are cached for instant access.

| Trigger | Processing Mode | User Experience |
|---------|-----------------|-----------------|
| New fund created | Async job queue | "Matching in progress..." → notification when ready |
| GP requests refresh | Async job queue | "Re-analyzing..." → notification when ready |
| New LP added | Async job queue | Existing match caches invalidated, re-processed |
| Subsequent access | Cache hit | Matches load instantly |

**Matching times:** 5 minutes to 24 hours depending on queue depth and LP database size.

**Cache lifecycle:**
- Results cached for months until fund/LP data changes
- Cache invalidation triggers: fund edit, LP data update, manual refresh
- Cached matches load instantly for GP users

---

### 5.7 Pitch Generation

#### F-PITCH-01: LP-Specific Executive Summary [P0]
**Description:** Generate personalized 1-page summary
**Requirements:**
- Tailored to specific LP's interests
- Highlight relevant fund aspects
- Include match rationale
- Professional formatting
- Export as PDF
- Generation time < 10 seconds

**Test Cases:** See TEST-PITCH-01 in Testing Strategy

#### F-PITCH-02: Outreach Email Draft [P0]
**Description:** Generate personalized intro email
**Requirements:**
- Multiple tone options (formal, warm, direct)
- Include specific LP references
- Reference any mutual connections if known
- Editable before sending
- Copy to clipboard option
- Save as template for similar LPs

**Test Cases:** See TEST-PITCH-02 in Testing Strategy

#### F-PITCH-03: Deck Modification Suggestions [P1]
**Description:** Suggest changes to pitch deck for LP
**Requirements:**
- Analyze deck content
- Suggest slide order changes
- Recommend emphasis points
- Generate modification report

#### F-PITCH-04: Supplementary Materials [P1]
**Description:** Generate LP-specific addendum documents
**Requirements:**
- Cover letter
- Custom case study selection
- Relevant track record highlights
- Export as PDF

#### F-PITCH-05: Deck Modification (PPTX) [P2]
**Description:** Actually modify PowerPoint decks
**Requirements:**
- Parse PPTX structure
- Add/modify slides
- Insert LP-specific content
- Maintain formatting

---

### 5.8 User Interface

#### F-UI-01: Dashboard [P0]
**Description:** User home screen with key information
**Requirements:**
- Company name in header with settings link
- Fund cards showing: name, status, size, key stats
- "New Fund" button (Admin/Member only)
- Recent activity feed (last 10 items)
- Quick action buttons: Search LPs, View Matches, Outreach Hub

**First-Time Welcome (Company Admin):**
When a Company Admin logs in for the first time (no funds exist):
- Welcome message with company name
- Two prominent options:
  - "Create Your First Fund" (primary)
  - "Invite Team Members" (secondary)
- Quick tip explaining the platform workflow

**First-Time Welcome (Team Member):**
When a team member logs in for the first time:
- Welcome message
- If company has funds → show dashboard with funds
- If no funds exist → message "Your admin is setting up the first fund"

**Dashboard Layout:**
```
┌─────────────────────────────────────────────────────────────────┐
│  [Company Name]                                [⚙️ Settings]    │
├─────────────────────────────────────────────────────────────────┤
│  YOUR FUNDS                                                     │
│  ┌────────────────────┐  ┌────────────────────┐                │
│  │ Fund Name          │  │ Fund Name          │  [+ New Fund]  │
│  │ Status · $XXM      │  │ Status · $XXM      │                │
│  │ XX matches         │  │ Closed             │                │
│  │ XX contacted       │  │                    │                │
│  │ [View Matches →]   │  │ [View Details →]   │                │
│  └────────────────────┘  └────────────────────┘                │
│                                                                 │
│  RECENT ACTIVITY                                                │
│  • [User] [action] [target] · [time ago]                       │
│  • ...                                                          │
│                                                                 │
│  QUICK ACTIONS                                                  │
│  [🔍 Search LPs]   [📊 View Matches]   [📧 Outreach Hub]       │
└─────────────────────────────────────────────────────────────────┘
```

**BDD Tests (must pass):**

| Test File | Key Scenarios |
|-----------|---------------|
| `m1-auth-search.feature.md` | Login with valid credentials, Session persists on refresh, Session expires after inactivity, Logout |
| `e2e-journeys.feature.md` | Complete company onboarding from sales to first login, Complete onboarding from invitation to first match |
| `m3-matching.feature.md` | View matches page, View match detail, Save match to shortlist |

**First-Time Welcome Tests:**
- `e2e-journeys.feature.md`: Complete onboarding from invitation to first match (validates welcome flow)

#### F-UI-02: Fund Profile Form [P0]
**Description:** Multi-step form for fund creation
**Requirements:**
- Wizard-style flow (5 steps)
- Progress indicator
- Validation feedback (inline)
- File upload integration
- Save & continue later

**BDD Tests (must pass):**

| Test File | Key Scenarios |
|-----------|---------------|
| `m3-matching.feature.md` | Enter fund basics, Define investment strategy, Set investment parameters, Add track record, Enter fund terms, Write investment thesis |
| `m3-matching.feature.md` | Save as draft, Publish fund, Attempt to publish without fund name/target size/strategy |
| `m3-matching.feature.md` | Upload PDF deck, Upload PPTX deck, File size validation, File type validation |
| `e2e-journeys.feature.md` | Missing required fields on confirm, Invalid fund size format, Save draft on browser close |

**Validation Tests:**
- `m3-matching.feature.md`: Negative target size rejected, Zero target size rejected, Check size min exceeds max, Invalid vintage year

**File Upload Tests:**
- `m3-matching.feature.md`: Upload corrupt PDF file, Upload corrupt PPTX file, Upload password-protected PDF, Upload empty PDF

#### F-UI-03: LP Search Interface [P0]
**Description:** Powerful LP discovery interface
**Requirements:**
- Filter sidebar (collapsible)
- Results list with key info (cards)
- Quick view modal / detail page
- Bulk actions (add to list, export)
- Sort by relevance, AUM, name

**BDD Tests (must pass):**

| Test File | Key Scenarios |
|-----------|---------------|
| `m2-semantic.feature.md` | Search by LP name, Search by strategy, Filter by LP type, Filter by AUM range, Filter by geography |
| `m2-semantic.feature.md` | Semantic search by thesis, Combine text and filters, Search results pagination |
| `e2e-journeys.feature.md` | Research LPs before fund launch, Search with no results, Filter combination returns empty |
| `m0-foundation.feature.md` | Store LP organization details, Store LP investment criteria |

**Error Handling Tests:**
- `e2e-journeys.feature.md`: Semantic search service unavailable, Search timeout, Network failure during search
- `e2e-journeys.feature.md`: LP profile not found, LP profile loading error, Incomplete LP data

**Saved Searches:**
- `e2e-journeys.feature.md`: Save search with duplicate name, Save search fails, Load saved search that's now invalid

#### F-UI-04: Match Results View [P0]
**Description:** Display matching LPs with context
**Requirements:**
- Ranked list with scores (visual bar)
- Score breakdown on hover/expand
- AI explanation panel (expandable)
- Actions per match (generate pitch, save, dismiss)
- Filter matches by score threshold

**BDD Tests (must pass):**

| Test File | Key Scenarios |
|-----------|---------------|
| `m3-matching.feature.md` | View matches page, View match detail, Match score breakdown, Save match to shortlist, Dismiss match |
| `m3-matching.feature.md` | F-DEBATE: Bull/Bear core debate flow, Disagreement resolution, Match scoring with confidence |
| `m4-pitch.feature.md` | Generate executive summary, Summary content, Tailored to LP interests, Include match rationale |
| `e2e-journeys.feature.md` | Matching engine timeout, No matches found, Matching engine error |

**Score & Explanation Tests:**
- `m3-matching.feature.md`: Score breakdown visible, AI explanation panel, Score confidence indicator

**Error Handling Tests:**
- `e2e-journeys.feature.md`: Matching engine timeout, No matches found, Matching engine error
- `m4-pitch.feature.md`: Handle API timeout during summary generation, Handle invalid match ID

#### F-UI-05: Admin Interface [P0]
**Description:** Platform administration UI
**Requirements:**
- User management CRUD table
- Company management
- LP data management (browse, edit, delete)
- Import wizard
- Data enrichment job status
- System health dashboard

**BDD Tests (must pass):**

| Test File | Key Scenarios |
|-----------|---------------|
| `m1-auth-search.feature.md` | User belongs to one company, Cannot see other company's funds, RLS bypass attempt via SQL injection |
| `m0-foundation.feature.md` | Store LP organization details, Reject LP without name, Sanitize SQL injection in name, Sanitize XSS in name |
| `m0-foundation.feature.md` | Store person details with employment, Track employment history, Reject invalid email format |
| `m5-production.feature.md` | Health check endpoint, System health dashboard, Admin bulk operations |

**Data Import Tests:**
- `m0-foundation.feature.md`: CSV import validation, Handle malformed CSV, Handle duplicate records

**Security Tests:**
- `m1-auth-search.feature.md`: Direct API access to other company's fund, IDOR attack on match data, Modify other company's fund via API

---

### 5.9 Human-in-the-Loop Requirements

The platform prioritizes human oversight for critical actions. AI assists but humans decide.

#### F-HITL-01: Outreach Email Review [P0]
**Description:** Human reviews and manually sends all outreach
**Requirements:**
- AI generates draft email, displayed for review
- GP can edit email content before proceeding
- "Copy to Clipboard" button (no auto-send)
- GP manually pastes into their email client
- Track that email was copied (not sent)

**BDD Tests:** `m4-pitch.feature.md` - Generate email draft, Email is for review only, Copy email, Edit email, Save email as template

#### F-HITL-02: Match Selection [P0]
**Description:** GP explicitly approves matches for outreach
**Requirements:**
- Matches shown as recommendations, not actions
- GP must explicitly add LP to shortlist
- Shortlist is separate from match results
- Bulk add to shortlist supported
- Clear distinction between "matched" and "shortlisted"

**BDD Tests:** `m3-matching.feature.md` - Save match to shortlist, Dismiss match, Bulk shortlist operations

#### F-HITL-03: Fund Profile Confirmation [P0]
**Description:** GP confirms AI-extracted fund information
**Requirements:**
- AI extraction shows confidence scores per field
- GP reviews each extracted field
- Required fields highlighted if missing
- GP must explicitly approve profile before saving
- Audit trail of what was AI-extracted vs manually entered

**BDD Tests:** `e2e-journeys.feature.md` - AI extraction fails mid-process, Missing required fields on confirm; `m3-matching.feature.md` - Publish fund (requires confirmation)

#### F-HITL-04: Data Import Preview [P0]
**Description:** Preview and approve data before committing
**Requirements:**
- Show preview of first N rows after mapping
- Highlight validation errors and warnings
- Show duplicate detection results
- Require explicit "Confirm Import" action
- Rollback option within 24 hours

**BDD Tests:** `m0-foundation.feature.md` - CSV import validation, Handle malformed CSV, Handle duplicate records; `m5-production.feature.md` - Admin bulk operations, Import rollback

#### F-HITL-05: LP Data Corrections [P1]
**Description:** GPs can flag outdated or incorrect LP information
**Requirements:**
- "Flag as outdated" button on LP profiles
- Optional correction suggestion field
- Flagged records queued for admin review
- Track flag history per LP
- Notify admin of new flags

**BDD Tests:** `m0-foundation.feature.md` - LP data validation, Handle incomplete LP data; `m5-production.feature.md` - Data quality monitoring, Admin review queue

---

## 6. Data Architecture

### 6.1 Entity Relationship Diagram

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

**Key Query Patterns:**

```sql
-- GP Perspective: LPs that invested in my funds
SELECT DISTINCT lp.* FROM investments i
JOIN funds f ON f.id = i.fund_id
JOIN organizations lp ON lp.id = i.lp_org_id
WHERE f.org_id = :my_gp_org_id;

-- GP Perspective: Recommended LPs (not yet acted on)
SELECT m.*, lp.name FROM fund_lp_matches m
JOIN funds f ON f.id = m.fund_id
JOIN organizations lp ON lp.id = m.lp_org_id
LEFT JOIN fund_lp_status s ON s.fund_id = m.fund_id AND s.lp_org_id = m.lp_org_id
WHERE f.org_id = :my_gp_org_id
  AND m.score >= 70
  AND (s.gp_interest IS NULL);

-- GP Perspective: LPs that passed on my funds
SELECT s.*, lp.name, f.name as fund_name FROM fund_lp_status s
JOIN organizations lp ON lp.id = s.lp_org_id
JOIN funds f ON f.id = s.fund_id
WHERE f.org_id = :my_gp_org_id
  AND s.lp_interest = 'not_interested';

-- LP Perspective: GPs I've invested in
SELECT DISTINCT gp.* FROM investments i
JOIN funds f ON f.id = i.fund_id
JOIN organizations gp ON gp.id = f.org_id
WHERE i.lp_org_id = :my_lp_org_id;
```

### 6.2 Core Tables

#### Organizations
Base table for all organizations. Can be GP, LP, or BOTH.
```sql
CREATE TABLE organizations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Core identity
    name            TEXT NOT NULL,
    website         TEXT,
    hq_city         TEXT,
    hq_country      TEXT,
    description     TEXT,

    -- Role flags (can be both!)
    is_gp           BOOLEAN DEFAULT FALSE,
    is_lp           BOOLEAN DEFAULT FALSE,

    -- Timestamps
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    -- Must be at least one role
    CONSTRAINT at_least_one_role CHECK (is_gp OR is_lp)
);

CREATE INDEX idx_organizations_is_gp ON organizations(is_gp) WHERE is_gp = TRUE;
CREATE INDEX idx_organizations_is_lp ON organizations(is_lp) WHERE is_lp = TRUE;
CREATE INDEX idx_organizations_name_trgm ON organizations USING GIN(name gin_trgm_ops);
```

#### GP Profiles (1:1 Extension)
GP-specific fields. Only exists for organizations where `is_gp = TRUE`.
```sql
CREATE TABLE gp_profiles (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id                  UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- GP-specific fields
    investment_philosophy   TEXT,
    team_size               INTEGER,
    years_investing         INTEGER,
    spun_out_from           TEXT,
    notable_exits           JSONB DEFAULT '[]',
    track_record_summary    JSONB DEFAULT '{}',

    -- For semantic search
    thesis_embedding        VECTOR(1024),

    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(org_id)
);

CREATE INDEX idx_gp_profiles_org ON gp_profiles(org_id);
CREATE INDEX idx_gp_profiles_thesis_embedding ON gp_profiles USING ivfflat (thesis_embedding vector_cosine_ops);
```

#### LP Profiles (1:1 Extension)
LP-specific fields. Only exists for organizations where `is_lp = TRUE`.
```sql
CREATE TABLE lp_profiles (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id                  UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- LP type and size
    lp_type                 TEXT CHECK (lp_type IN ('pension', 'endowment', 'foundation',
                                                     'family_office', 'sovereign_wealth',
                                                     'insurance', 'fund_of_funds', 'other')),
    total_aum_bn            DECIMAL(12,2),
    pe_allocation_pct       DECIMAL(5,2),

    -- Investment criteria
    strategies              TEXT[] DEFAULT '{}',
    geographic_preferences  TEXT[] DEFAULT '{}',
    sector_preferences      TEXT[] DEFAULT '{}',
    check_size_min_mm       DECIMAL(12,2),
    check_size_max_mm       DECIMAL(12,2),
    fund_size_min_mm        DECIMAL(12,2),
    fund_size_max_mm        DECIMAL(12,2),
    min_track_record_years  INTEGER,
    min_fund_number         INTEGER,

    -- Requirements
    esg_required            BOOLEAN DEFAULT FALSE,
    emerging_manager_ok     BOOLEAN DEFAULT FALSE,

    -- Mandate (for semantic search)
    mandate_description     TEXT,
    mandate_embedding       VECTOR(1024),

    -- LLM-generated summary for sparse data
    llm_summary             TEXT,
    summary_embedding       VECTOR(1024),
    summary_generated_at    TIMESTAMPTZ,
    summary_sources         JSONB DEFAULT '[]',

    -- Data quality
    data_source             TEXT DEFAULT 'manual',
    data_quality_score      DECIMAL(3,2),
    last_verified           TIMESTAMPTZ,

    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(org_id)
);

CREATE INDEX idx_lp_profiles_org ON lp_profiles(org_id);
CREATE INDEX idx_lp_profiles_strategies ON lp_profiles USING GIN(strategies);
CREATE INDEX idx_lp_profiles_geographic ON lp_profiles USING GIN(geographic_preferences);
CREATE INDEX idx_lp_profiles_mandate_embedding ON lp_profiles USING ivfflat (mandate_embedding vector_cosine_ops);
```

#### People (All Industry Professionals)
All professionals in the industry. Platform users have `auth_user_id` set.
Current employer is derived from `employment WHERE is_current = TRUE`.
```sql
CREATE TABLE people (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    full_name           TEXT NOT NULL,
    email               TEXT UNIQUE,
    phone               TEXT,
    linkedin_url        TEXT,

    -- Profile
    bio                 TEXT,
    notes               TEXT,
    is_decision_maker   BOOLEAN DEFAULT FALSE,

    -- Platform authentication (NULL = cannot login, SET = can login)
    auth_user_id        UUID UNIQUE REFERENCES auth.users(id),
    role                TEXT CHECK (role IN ('admin', 'member', 'viewer')) DEFAULT 'member',
    is_super_admin      BOOLEAN DEFAULT FALSE,
    invited_by          UUID REFERENCES people(id),
    first_login_at      TIMESTAMPTZ,

    -- Employment status (for people with no/unknown employment records)
    employment_status   TEXT CHECK (employment_status IN ('employed', 'unknown', 'unemployed', 'retired')) DEFAULT 'unknown',

    -- Timestamps
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Index for finding platform users (people who can login)
CREATE INDEX idx_people_auth ON people(auth_user_id) WHERE auth_user_id IS NOT NULL;
CREATE INDEX idx_people_email ON people(email);
CREATE INDEX idx_people_name_trgm ON people USING GIN(full_name gin_trgm_ops);
```

> **Note:** There is no `primary_org_id` column. To find someone's current employer:
> ```sql
> SELECT p.*, o.name as current_employer, e.title
> FROM people p
> LEFT JOIN employment e ON e.person_id = p.id AND e.is_current = TRUE
> LEFT JOIN organizations o ON o.id = e.org_id
> WHERE p.id = :person_id;
> ```

#### Employment (Career History)
Links people to organizations over time. Supports multiple concurrent jobs.
```sql
CREATE TABLE employment (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id       UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    org_id          UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Position
    title           TEXT,
    department      TEXT,

    -- Timeline
    start_date      DATE,           -- NULL = unknown start
    end_date        DATE,           -- NULL = current or unknown end
    is_current      BOOLEAN DEFAULT TRUE,

    -- Data quality
    confidence      TEXT CHECK (confidence IN ('confirmed', 'likely', 'inferred')) DEFAULT 'confirmed',
    source          TEXT,           -- 'linkedin', 'manual', 'import', etc.

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_dates CHECK (end_date IS NULL OR start_date IS NULL OR end_date >= start_date)
);

CREATE INDEX idx_employment_person ON employment(person_id);
CREATE INDEX idx_employment_org ON employment(org_id);
CREATE INDEX idx_employment_current ON employment(person_id, is_current) WHERE is_current = TRUE;
```

> **Confidence Levels:**
> - `confirmed`: Verified through LinkedIn, public records, or user confirmation
> - `likely`: Inferred from email domain, conference attendance, etc.
> - `inferred`: Best guess based on limited data

#### Invitations
```sql
CREATE TABLE invitations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email           TEXT NOT NULL,
    org_id          UUID NOT NULL REFERENCES organizations(id),
    role            TEXT CHECK (role IN ('admin', 'member', 'viewer')) NOT NULL,
    token           TEXT UNIQUE NOT NULL,
    invited_by      UUID REFERENCES people(id),

    -- Status tracking
    status          TEXT CHECK (status IN ('pending', 'accepted', 'expired', 'cancelled')) DEFAULT 'pending',
    expires_at      TIMESTAMPTZ NOT NULL,
    accepted_at     TIMESTAMPTZ,

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_invitations_token ON invitations(token);
CREATE INDEX idx_invitations_email ON invitations(email);
CREATE INDEX idx_invitations_org ON invitations(org_id);
```

#### Funds (GP Profiles)
```sql
CREATE TABLE funds (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id              UUID NOT NULL REFERENCES organizations(id),
    created_by          UUID REFERENCES people(id),

    -- Basics
    name                TEXT NOT NULL,
    fund_number         INTEGER,
    status              TEXT CHECK (status IN ('draft', 'active', 'closed')) DEFAULT 'draft',
    vintage_year        INTEGER,
    target_size_mm      DECIMAL(12,2),
    current_aum_mm      DECIMAL(12,2),
    hard_cap_mm         DECIMAL(12,2),
    first_close_date    DATE,
    final_close_target  DATE,

    -- Strategy
    strategy            TEXT,
    sub_strategy        TEXT,
    geographic_focus    TEXT[] DEFAULT '{}',
    sector_focus        TEXT[] DEFAULT '{}',

    -- Investment Parameters
    check_size_min_mm   DECIMAL(12,2),
    check_size_max_mm   DECIMAL(12,2),
    target_companies    INTEGER,
    holding_period_years INTEGER,

    -- Track Record (JSONB for flexibility)
    track_record        JSONB DEFAULT '[]',
    notable_exits       JSONB DEFAULT '[]',
    total_invested_mm   DECIMAL(12,2),
    realized_proceeds_mm DECIMAL(12,2),

    -- Team (see fund_team table for actual team members)
    team_size           INTEGER,
    years_investing     INTEGER,
    spun_out_from       TEXT,

    -- Terms
    management_fee_pct  DECIMAL(4,2),
    carried_interest_pct DECIMAL(4,2),
    hurdle_rate_pct     DECIMAL(4,2),
    gp_commitment_pct   DECIMAL(4,2),
    fund_term_years     INTEGER,

    -- ESG
    esg_policy          BOOLEAN DEFAULT FALSE,
    impact_focus        BOOLEAN DEFAULT FALSE,
    esg_certifications  TEXT[] DEFAULT '{}',

    -- Documents
    pitch_deck_url      TEXT,
    pitch_deck_text     TEXT,

    -- Investment Thesis (for semantic search)
    investment_thesis   TEXT,
    thesis_embedding    VECTOR(1024),

    -- Audit Trail
    updated_by          UUID REFERENCES people(id),
    data_source         TEXT DEFAULT 'manual',
    last_verified       TIMESTAMPTZ,
    verification_status TEXT CHECK (verification_status IN ('unverified', 'pending', 'verified', 'outdated')) DEFAULT 'unverified',

    -- Metadata
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_funds_org ON funds(org_id);
CREATE INDEX idx_funds_thesis_embedding ON funds USING ivfflat (thesis_embedding vector_cosine_ops);
```

#### Fund Team (GP Professionals on a Fund)
Links people to funds they work on.
```sql
CREATE TABLE fund_team (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fund_id         UUID REFERENCES funds(id) ON DELETE CASCADE NOT NULL,
    person_id       UUID REFERENCES people(id) NOT NULL,
    role            TEXT,                       -- "Partner", "Principal", "Analyst"
    is_key_person   BOOLEAN DEFAULT FALSE,      -- regulatory "key person"
    allocation_pct  DECIMAL(5,2),               -- % of time on this fund
    created_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(fund_id, person_id)
);

CREATE INDEX idx_fund_team_fund ON fund_team(fund_id);
CREATE INDEX idx_fund_team_person ON fund_team(person_id);
```

#### Organization Contacts (via People + Employment)

> **Note:** Contacts for both GPs and LPs are stored in the global `people` table with
> employment records linking them to organizations. This enables:
> - Tracking people as they move between organizations
> - Shared contact database across all GP companies
> - Employment history with start/end dates
> - People moving from LP to GP or vice versa
>
> To find contacts for an organization:
> ```sql
> SELECT p.*, e.title, e.department, e.start_date
> FROM people p
> JOIN employment e ON e.person_id = p.id
> WHERE e.org_id = '<org_id>'
>   AND e.is_current = TRUE;
> ```

#### Investments (Historical Facts)
Tracks historical LP investments in GP funds. These are FACTS, not recommendations.
```sql
CREATE TABLE investments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    lp_org_id       UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,
    fund_id         UUID NOT NULL REFERENCES funds(id) ON DELETE CASCADE,

    commitment_mm   DECIMAL(12,2),
    commitment_date DATE,

    -- Data provenance
    source          TEXT CHECK (source IN ('disclosed', 'public', 'estimated', 'imported')) DEFAULT 'imported',
    confidence      TEXT CHECK (confidence IN ('confirmed', 'likely', 'rumored')) DEFAULT 'confirmed',

    created_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(lp_org_id, fund_id)
);

CREATE INDEX idx_investments_lp ON investments(lp_org_id);
CREATE INDEX idx_investments_fund ON investments(fund_id);
```

> **Note:** Investments are linked to specific funds, not just GP organizations.
> To find "LPs that invested in a GP", join through funds:
> ```sql
> SELECT DISTINCT lp.* FROM investments i
> JOIN funds f ON f.id = i.fund_id
> JOIN organizations lp ON lp.id = i.lp_org_id
> WHERE f.org_id = :gp_org_id;
> ```

#### Fund-LP Matches (AI Recommendations)
System-generated match recommendations between funds and LPs.
```sql
CREATE TABLE fund_lp_matches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    fund_id         UUID NOT NULL REFERENCES funds(id) ON DELETE CASCADE,
    lp_org_id       UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Scoring
    score           DECIMAL(5,2) NOT NULL,
    score_breakdown JSONB DEFAULT '{}',

    -- AI-generated content
    explanation     TEXT,
    talking_points  TEXT[] DEFAULT '{}',
    concerns        TEXT[] DEFAULT '{}',

    -- Source
    debate_id       UUID,           -- FK to agent_debates when implemented
    model_version   TEXT,

    -- Validity
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    expires_at      TIMESTAMPTZ,    -- Matches can become stale

    UNIQUE(fund_id, lp_org_id)
);

CREATE INDEX idx_fund_lp_matches_fund ON fund_lp_matches(fund_id);
CREATE INDEX idx_fund_lp_matches_lp ON fund_lp_matches(lp_org_id);
CREATE INDEX idx_fund_lp_matches_score ON fund_lp_matches(score DESC);
```

#### Fund-LP Status (User-Expressed Interest)
Tracks GP and LP interest/rejection separately. Both parties can express interest independently.
```sql
CREATE TABLE fund_lp_status (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    fund_id         UUID NOT NULL REFERENCES funds(id) ON DELETE CASCADE,
    lp_org_id       UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- GP side
    gp_interest     TEXT CHECK (gp_interest IN ('interested', 'not_interested', 'pursuing')),
    gp_interest_reason TEXT,
    gp_interest_by  UUID REFERENCES people(id),
    gp_interest_at  TIMESTAMPTZ,

    -- LP side
    lp_interest     TEXT CHECK (lp_interest IN ('interested', 'not_interested', 'reviewing')),
    lp_interest_reason TEXT,
    lp_interest_by  UUID REFERENCES people(id),
    lp_interest_at  TIMESTAMPTZ,

    -- Pipeline stage (can be computed or set manually)
    pipeline_stage  TEXT CHECK (pipeline_stage IN (
        'recommended',      -- System recommended, no action
        'gp_interested',    -- GP marked interest
        'gp_pursuing',      -- GP actively reaching out
        'lp_reviewing',     -- LP is evaluating
        'mutual_interest',  -- Both interested
        'in_diligence',     -- Active DD process
        'gp_passed',        -- GP decided not to pursue
        'lp_passed',        -- LP declined
        'invested'          -- Commitment made
    )) DEFAULT 'recommended',

    -- Notes
    notes           TEXT,

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(fund_id, lp_org_id)
);

CREATE INDEX idx_fund_lp_status_fund ON fund_lp_status(fund_id);
CREATE INDEX idx_fund_lp_status_lp ON fund_lp_status(lp_org_id);
CREATE INDEX idx_fund_lp_status_pipeline ON fund_lp_status(pipeline_stage);
CREATE INDEX idx_fund_lp_status_gp_interest ON fund_lp_status(gp_interest) WHERE gp_interest IS NOT NULL;
CREATE INDEX idx_fund_lp_status_lp_interest ON fund_lp_status(lp_interest) WHERE lp_interest IS NOT NULL;
```

> **Pipeline Stage Logic:**
> The `pipeline_stage` can be computed from other fields:
> ```python
> def compute_pipeline_stage(gp_interest, lp_interest, has_investment):
>     if has_investment:
>         return 'invested'
>     if gp_interest == 'not_interested':
>         return 'gp_passed'
>     if lp_interest == 'not_interested':
>         return 'lp_passed'
>     if gp_interest == 'interested' and lp_interest == 'interested':
>         return 'mutual_interest'
>     if lp_interest == 'reviewing':
>         return 'lp_reviewing'
>     if gp_interest == 'pursuing':
>         return 'gp_pursuing'
>     if gp_interest == 'interested':
>         return 'gp_interested'
>     return 'recommended'
> ```

#### Outreach Events (Outcome Tracking)
Tracks the full journey from match to commitment for algorithm learning.
```sql
CREATE TABLE outreach_events (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id        UUID NOT NULL REFERENCES fund_lp_matches(id) ON DELETE CASCADE,

    event_type      TEXT NOT NULL CHECK (event_type IN (
        'pitch_generated',
        'email_sent',
        'email_opened',
        'response_received',
        'meeting_scheduled',
        'meeting_held',
        'follow_up_sent',
        'due_diligence_started',
        'term_sheet_received',
        'commitment_made',
        'commitment_declined'
    )),

    event_date      TIMESTAMPTZ NOT NULL,
    notes           TEXT,

    -- For meetings
    meeting_type    TEXT,  -- intro_call, deep_dive, dd_session, closing
    attendees       UUID[],  -- people IDs

    created_by      UUID REFERENCES people(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_outreach_events_match ON outreach_events(match_id);
CREATE INDEX idx_outreach_events_type ON outreach_events(event_type);
CREATE INDEX idx_outreach_events_date ON outreach_events(event_date);
```

#### Match Outcomes (Training Data)
Final outcomes for model training. Critical for learning loop.
```sql
CREATE TABLE match_outcomes (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id            UUID NOT NULL REFERENCES fund_lp_matches(id) UNIQUE,

    -- Outcome
    outcome             TEXT NOT NULL CHECK (outcome IN (
        'committed',
        'declined_after_meeting',
        'declined_before_meeting',
        'no_response',
        'not_contacted',
        'in_progress'
    )),

    -- If committed
    commitment_amount_mm DECIMAL(12,2),
    commitment_date     DATE,

    -- If declined
    decline_reason      TEXT,
    decline_stage       TEXT,  -- At what stage did they decline?

    -- Quality signals
    time_to_first_response INTERVAL,
    time_to_outcome     INTERVAL,
    total_meetings      INTEGER,

    -- For training: snapshot of all scoring inputs at match time
    features_at_match_time JSONB,

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_match_outcomes_outcome ON match_outcomes(outcome);
CREATE INDEX idx_match_outcomes_date ON match_outcomes(commitment_date);
```

#### Relationships (GP-LP Intelligence)
Tracks GP-LP relationships beyond just matches.
```sql
CREATE TABLE relationships (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gp_org_id           UUID NOT NULL REFERENCES organizations(id),
    lp_org_id           UUID NOT NULL REFERENCES organizations(id),

    -- Relationship status
    relationship_type   TEXT CHECK (relationship_type IN (
        'existing_investor',      -- LP has committed to prior fund
        'warm_connection',        -- Met before, have relationship
        'mutual_connection',      -- Know someone who knows them
        'cold'                    -- No prior relationship
    )),

    -- History
    prior_commitments   INTEGER DEFAULT 0,
    total_committed_mm  DECIMAL(12,2),
    last_meeting_date   DATE,
    relationship_strength INTEGER CHECK (relationship_strength BETWEEN 1 AND 5),

    -- Key contacts
    primary_contact_id  UUID REFERENCES people(id),

    notes               TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(gp_org_id, lp_org_id)
);

CREATE INDEX idx_relationships_gp ON relationships(gp_org_id);
CREATE INDEX idx_relationships_lp ON relationships(lp_org_id);
CREATE INDEX idx_relationships_type ON relationships(relationship_type);
```

#### Mutual Connections
People who know both GP and LP contacts.
```sql
CREATE TABLE mutual_connections (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gp_person_id        UUID NOT NULL REFERENCES people(id),
    lp_person_id        UUID NOT NULL REFERENCES people(id),

    connection_type     TEXT,  -- former_colleagues, board_together, etc.
    connection_strength INTEGER CHECK (connection_strength BETWEEN 1 AND 5),

    notes               TEXT,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_mutual_connections_gp ON mutual_connections(gp_person_id);
CREATE INDEX idx_mutual_connections_lp ON mutual_connections(lp_person_id);
```

#### LP Capacity (Timing Intelligence)
Track LP allocation capacity over time for timing predictions.
```sql
CREATE TABLE lp_capacity (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lp_org_id               UUID NOT NULL REFERENCES organizations(id),

    -- Capacity info
    fiscal_year             INTEGER,
    total_pe_allocation_mm  DECIMAL(12,2),
    committed_ytd_mm        DECIMAL(12,2),
    remaining_capacity_mm   DECIMAL(12,2),

    -- Timing
    typical_commitment_quarters TEXT[],  -- ['Q1', 'Q4']
    next_allocation_window  DATE,

    -- Constraints
    at_capacity             BOOLEAN DEFAULT FALSE,
    capacity_notes          TEXT,

    -- Source
    data_source             TEXT,
    verified_date           DATE,

    created_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_lp_capacity_org ON lp_capacity(lp_org_id);
CREATE INDEX idx_lp_capacity_year ON lp_capacity(fiscal_year);
```

#### LP Match Preferences (Bidirectional Matching)
LP-side preferences for receiving fund recommendations.
```sql
CREATE TABLE lp_match_preferences (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lp_org_id               UUID NOT NULL REFERENCES organizations(id),

    -- LP can set active search parameters
    actively_looking        BOOLEAN DEFAULT FALSE,
    allocation_available_mm DECIMAL(12,2),
    target_close_date       DATE,

    -- Notification preferences
    notify_on_new_funds     BOOLEAN DEFAULT TRUE,
    min_match_score         INTEGER DEFAULT 70,

    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_lp_match_preferences_org ON lp_match_preferences(lp_org_id);
CREATE INDEX idx_lp_match_preferences_active ON lp_match_preferences(actively_looking) WHERE actively_looking = TRUE;
```

#### Generated Pitches
```sql
CREATE TABLE pitches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id        UUID NOT NULL REFERENCES fund_lp_matches(id) ON DELETE CASCADE,

    type            TEXT CHECK (type IN ('email', 'summary', 'addendum')) NOT NULL,
    content         TEXT NOT NULL,
    tone            TEXT,

    created_by      UUID REFERENCES people(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pitches_match ON pitches(match_id);
```

#### Enrichment Log
```sql
CREATE TABLE enrichment_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) ON DELETE CASCADE,
    person_id       UUID REFERENCES people(id) ON DELETE SET NULL,

    source          TEXT NOT NULL,
    field_updated   TEXT,
    old_value       TEXT,
    new_value       TEXT,
    confidence      DECIMAL(3,2),

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_enrichment_org ON enrichment_log(org_id);
CREATE INDEX idx_enrichment_person ON enrichment_log(person_id);
```

#### Data Import Jobs
```sql
CREATE TABLE import_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    file_name       TEXT NOT NULL,
    file_url        TEXT,
    status          TEXT CHECK (status IN ('pending', 'preview', 'approved', 'processing', 'completed', 'failed', 'rolled_back')) DEFAULT 'pending',

    total_rows      INTEGER,
    processed_rows  INTEGER DEFAULT 0,
    success_rows    INTEGER DEFAULT 0,
    error_rows      INTEGER DEFAULT 0,

    field_mapping   JSONB,
    errors          JSONB DEFAULT '[]',
    preview_data    JSONB DEFAULT '[]',

    -- Audit Trail
    created_by      UUID REFERENCES people(id),
    approved_by     UUID REFERENCES people(id),
    approved_at     TIMESTAMPTZ,
    data_source     TEXT DEFAULT 'csv_import',

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);
```

#### Research Agent Jobs
```sql
CREATE TABLE research_jobs (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    org_id          UUID REFERENCES organizations(id) ON DELETE CASCADE,
    person_id       UUID REFERENCES people(id) ON DELETE SET NULL,

    job_type        TEXT NOT NULL CHECK (job_type IN ('org_enrichment', 'person_enrichment', 'market_research')),
    status          TEXT CHECK (status IN ('pending', 'in_progress', 'completed', 'failed')) DEFAULT 'pending',

    -- Research parameters
    search_queries  TEXT[],
    sources_to_check TEXT[] DEFAULT ARRAY['perplexity', 'web_search', 'linkedin'],

    -- Results
    findings        JSONB DEFAULT '{}',
    confidence      DECIMAL(3,2),
    sources_used    JSONB DEFAULT '[]',

    -- Audit
    triggered_by    TEXT,  -- 'low_data_quality', 'manual', 'scheduled', 'match_request'
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);

CREATE INDEX idx_research_jobs_org ON research_jobs(org_id);
CREATE INDEX idx_research_jobs_status ON research_jobs(status) WHERE status = 'pending';
```

#### LLM-Interpreted Constraints
```sql
CREATE TABLE lp_interpreted_constraints (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lp_org_id       UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Original mandate text that was interpreted
    source_text     TEXT NOT NULL,

    -- LLM-derived constraints
    hard_include    JSONB DEFAULT '{}',  -- {"strategies": ["buyout"], "geographies": ["EU"]}
    hard_exclude    JSONB DEFAULT '{}',  -- {"sectors": ["weapons", "tobacco"], "geographies": ["Russia"]}
    soft_preferences JSONB DEFAULT '{}', -- {"esg_preference": "strong", "emerging_ok": false}

    -- Interpretation metadata
    llm_reasoning   TEXT,                -- Why the LLM made these interpretations
    confidence      DECIMAL(3,2),
    model_used      TEXT,

    -- Verification
    human_verified  BOOLEAN DEFAULT FALSE,
    verified_by     UUID REFERENCES people(id),
    verified_at     TIMESTAMPTZ,

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_interpreted_constraints_lp ON lp_interpreted_constraints(lp_org_id);
```

#### Explanation Agent Learned Preferences
```sql
CREATE TABLE gp_learned_preferences (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    gp_org_id       UUID NOT NULL REFERENCES organizations(id) ON DELETE CASCADE,

    -- Learned from GP interactions
    preference_type TEXT NOT NULL CHECK (preference_type IN (
        'lp_type_preference',      -- "Prefers family offices over pensions"
        'geography_affinity',      -- "Strong track record with Texas LPs"
        'size_sweet_spot',         -- "Best conversion with $50-100M checks"
        'relationship_style',      -- "Values warm intros over cold outreach"
        'timing_pattern',          -- "Closes better in Q4"
        'objection_pattern'        -- "Often loses on track record concerns"
    )),

    -- The learned insight
    insight         TEXT NOT NULL,
    supporting_data JSONB,           -- Evidence from matches/outcomes

    -- Confidence and validation
    confidence      DECIMAL(3,2),
    observation_count INTEGER DEFAULT 1,
    last_validated  TIMESTAMPTZ,

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_learned_preferences_gp ON gp_learned_preferences(gp_org_id);
CREATE INDEX idx_learned_preferences_type ON gp_learned_preferences(preference_type);
```

#### Learning Agent Global Signals
```sql
CREATE TABLE global_learned_signals (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Aggregated cross-company learning (privacy-safe)
    signal_type     TEXT NOT NULL CHECK (signal_type IN (
        'strategy_trend',          -- "Growth equity seeing 40% more interest this quarter"
        'lp_type_pattern',         -- "Pensions responding faster than usual"
        'geography_shift',         -- "APAC LPs more active in US funds"
        'timing_insight',          -- "Q1 2024 seeing slower close rates"
        'market_condition'         -- "Interest rates affecting LP allocations"
    )),

    -- The signal
    insight         TEXT NOT NULL,
    supporting_metrics JSONB,       -- Aggregated, anonymized stats

    -- Applicability
    applies_to_strategies TEXT[],   -- Which strategies this applies to
    applies_to_geographies TEXT[],  -- Which geographies
    applies_to_lp_types TEXT[],     -- Which LP types

    -- Validity
    confidence      DECIMAL(3,2),
    observation_count INTEGER,
    valid_from      DATE,
    valid_until     DATE,

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_global_signals_type ON global_learned_signals(signal_type);
CREATE INDEX idx_global_signals_validity ON global_learned_signals(valid_until) WHERE valid_until > NOW();
```

#### Agent Debates (Multi-Agent System)
```sql
-- Agent Debate Sessions
CREATE TABLE agent_debates (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    debate_type         TEXT NOT NULL CHECK (debate_type IN (
        'constraint_interpretation',  -- Debate 1: Broad vs Narrow Interpreter
        'research_enrichment',        -- Debate 2: Generator + Critic
        'match_scoring',              -- Debate 3: Bull vs Bear
        'pitch_generation'            -- Debate 4: Generator + Critic
    )),

    -- What entity is being debated
    entity_type         TEXT NOT NULL CHECK (entity_type IN ('lp', 'fund', 'match', 'pitch')),
    entity_id           UUID NOT NULL,

    -- Debate state
    status              TEXT CHECK (status IN ('pending', 'in_progress', 'completed', 'escalated')) DEFAULT 'pending',
    iteration_count     INTEGER DEFAULT 1,      -- How many rounds of debate
    max_iterations      INTEGER DEFAULT 3,      -- Cap on regeneration rounds

    -- Metrics
    total_tokens_used   INTEGER DEFAULT 0,
    total_cost_cents    INTEGER DEFAULT 0,

    -- Timestamps
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ
);

CREATE INDEX idx_agent_debates_status ON agent_debates(status) WHERE status IN ('pending', 'in_progress');
CREATE INDEX idx_agent_debates_entity ON agent_debates(entity_type, entity_id);
CREATE INDEX idx_agent_debates_type ON agent_debates(debate_type);
```

#### Agent Outputs (Individual Agent Responses)
```sql
CREATE TABLE agent_outputs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    debate_id           UUID NOT NULL REFERENCES agent_debates(id) ON DELETE CASCADE,

    -- Which agent and iteration
    agent_role          TEXT NOT NULL CHECK (agent_role IN (
        -- Constraint Interpretation
        'broad_interpreter', 'narrow_interpreter', 'constraint_synthesizer',
        -- Research Enrichment
        'research_generator', 'research_critic', 'quality_synthesizer',
        -- Match Scoring
        'bull_agent', 'bear_agent', 'match_synthesizer',
        -- Pitch Generation
        'pitch_generator', 'pitch_critic', 'content_synthesizer'
    )),
    iteration           INTEGER DEFAULT 1,

    -- Input/Output
    input_prompt        TEXT NOT NULL,
    output_raw          JSONB NOT NULL,         -- Full structured output

    -- Key metrics extracted from output
    primary_score       DECIMAL(5,2),           -- Main score (0-100)
    confidence          DECIMAL(3,2),           -- Confidence (0-1)

    -- Cross-feedback (if this was a regeneration round)
    feedback_received   JSONB,                  -- Feedback from opposing agent
    changes_made        TEXT,                   -- Summary of what changed

    -- Tokens
    tokens_used         INTEGER,
    model_used          TEXT,

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_outputs_debate ON agent_outputs(debate_id);
CREATE INDEX idx_agent_outputs_role ON agent_outputs(agent_role);
```

#### Agent Disagreements (Unresolved Conflicts)
```sql
CREATE TABLE agent_disagreements (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    debate_id           UUID NOT NULL REFERENCES agent_debates(id) ON DELETE CASCADE,

    -- What are they disagreeing about
    topic               TEXT NOT NULL,          -- e.g., "strategy_fit", "timing_appropriateness"
    agent_a_role        TEXT NOT NULL,          -- e.g., "bull_agent"
    agent_a_position    TEXT NOT NULL,          -- What agent A believes
    agent_a_score       DECIMAL(5,2),
    agent_b_role        TEXT NOT NULL,          -- e.g., "bear_agent"
    agent_b_position    TEXT NOT NULL,          -- What agent B believes
    agent_b_score       DECIMAL(5,2),

    -- Magnitude and resolution
    magnitude           DECIMAL(5,2) NOT NULL,  -- Score difference
    resolution_method   TEXT CHECK (resolution_method IN (
        'regeneration',      -- Resolved through cross-feedback
        'synthesizer_decision', -- Synthesizer made judgment call
        'human_decision'     -- Escalated to human
    )),
    resolution_notes    TEXT,

    resolved_at         TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_disagreements_debate ON agent_disagreements(debate_id);
CREATE INDEX idx_agent_disagreements_unresolved ON agent_disagreements(resolved_at) WHERE resolved_at IS NULL;
```

#### Agent Escalations (Human Review Queue)
```sql
CREATE TABLE agent_escalations (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    debate_id           UUID NOT NULL REFERENCES agent_debates(id) ON DELETE CASCADE,

    -- Escalation details
    escalation_type     TEXT NOT NULL CHECK (escalation_type IN (
        'score_disagreement',   -- Bull/Bear disagree by >30 points
        'confidence_collapse',  -- Synthesizer confidence <0.5
        'deal_breaker',         -- Bear identified hard exclusion
        'data_quality',         -- Critic rejected >50% of research
        'factual_error',        -- Pitch critic found hallucination
        'edge_case'             -- Unusual situation needs human judgment
    )),
    priority            TEXT CHECK (priority IN ('low', 'medium', 'high', 'critical')) DEFAULT 'medium',

    -- Context for human reviewer
    summary             TEXT NOT NULL,          -- One-line summary
    debate_transcript   JSONB NOT NULL,         -- Full debate history
    key_disagreement    TEXT,                   -- Main point of contention

    -- Assignment and resolution
    status              TEXT CHECK (status IN ('pending', 'assigned', 'resolved')) DEFAULT 'pending',
    assigned_to         UUID REFERENCES people(id),
    assigned_at         TIMESTAMPTZ,

    -- Resolution
    resolution          TEXT,                   -- Human's decision
    resolution_reasoning TEXT,                  -- Why they decided this way
    resolved_by         UUID REFERENCES people(id),
    resolved_at         TIMESTAMPTZ,

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_escalations_status ON agent_escalations(status) WHERE status IN ('pending', 'assigned');
CREATE INDEX idx_agent_escalations_priority ON agent_escalations(priority, created_at);
CREATE INDEX idx_agent_escalations_assigned ON agent_escalations(assigned_to) WHERE assigned_to IS NOT NULL;
```

#### Agent Critiques (Quality Assessment Records)
```sql
CREATE TABLE agent_critiques (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    debate_id           UUID REFERENCES agent_debates(id) ON DELETE CASCADE,

    -- What was critiqued
    content_type        TEXT NOT NULL CHECK (content_type IN (
        'research_finding',     -- Research Critic output
        'pitch_draft',          -- Pitch Critic output
        'constraint_interpretation', -- Constraint interpretation review
        'match_analysis'        -- Match analysis review
    )),
    content_id          UUID,                   -- FK to the content being critiqued

    -- Quality scores (0-100)
    overall_score       DECIMAL(5,2) NOT NULL,
    dimension_scores    JSONB NOT NULL,         -- {"accuracy": 85, "personalization": 70, ...}

    -- Issues found
    issues_found        JSONB DEFAULT '[]',     -- [{"type": "factual_error", "description": "..."}]
    issue_severity      TEXT CHECK (issue_severity IN ('none', 'minor', 'moderate', 'critical')),

    -- Recommendation
    recommendation      TEXT CHECK (recommendation IN (
        'approve',              -- Quality sufficient
        'approve_with_notes',   -- Minor suggestions
        'regenerate',           -- Needs improvement
        'reject'                -- Cannot be salvaged
    )),
    improvement_notes   TEXT,                   -- What to improve if regenerating

    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_agent_critiques_debate ON agent_critiques(debate_id);
CREATE INDEX idx_agent_critiques_type ON agent_critiques(content_type);
CREATE INDEX idx_agent_critiques_severity ON agent_critiques(issue_severity) WHERE issue_severity = 'critical';
```

#### Batch Jobs (Async Processing)
```sql
CREATE TABLE batch_jobs (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Job type and scope
    job_type            TEXT NOT NULL CHECK (job_type IN (
        'nightly_full',         -- Full nightly recomputation
        'incremental',          -- Only changed entities
        'entity_specific',      -- Specific fund or LP
        'debate_rerun'          -- Re-run specific debates
    )),

    -- Scope
    scope_filter        JSONB DEFAULT '{}',     -- {"fund_ids": [...], "lp_org_ids": [...]}

    -- Status
    status              TEXT CHECK (status IN ('pending', 'running', 'completed', 'failed', 'cancelled')) DEFAULT 'pending',

    -- Progress tracking
    total_items         INTEGER DEFAULT 0,
    processed_items     INTEGER DEFAULT 0,
    failed_items        INTEGER DEFAULT 0,

    -- Error handling
    errors              JSONB DEFAULT '[]',

    -- Metrics
    tokens_used         INTEGER DEFAULT 0,
    cost_cents          INTEGER DEFAULT 0,

    -- Timestamps
    scheduled_for       TIMESTAMPTZ,            -- When to run (for scheduled jobs)
    started_at          TIMESTAMPTZ,
    completed_at        TIMESTAMPTZ,
    created_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_batch_jobs_status ON batch_jobs(status) WHERE status IN ('pending', 'running');
CREATE INDEX idx_batch_jobs_scheduled ON batch_jobs(scheduled_for) WHERE status = 'pending';
```

#### Entity Cache (Precomputed Results)
```sql
CREATE TABLE entity_cache (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- What entity this cache is for
    entity_type         TEXT NOT NULL CHECK (entity_type IN ('lp', 'fund', 'match', 'pitch')),
    entity_id           UUID NOT NULL,

    -- Cache key and value
    cache_key           TEXT NOT NULL,          -- e.g., "debate_result", "enrichment_data"
    cache_value         JSONB NOT NULL,

    -- Source debate (if applicable)
    source_debate_id    UUID REFERENCES agent_debates(id) ON DELETE SET NULL,

    -- Validity
    valid_from          TIMESTAMPTZ DEFAULT NOW(),
    valid_until         TIMESTAMPTZ,            -- NULL = never expires
    invalidated_at      TIMESTAMPTZ,            -- Set when cache is manually invalidated
    invalidation_reason TEXT,

    -- Metadata
    computation_time_ms INTEGER,
    tokens_used         INTEGER,

    created_at          TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(entity_type, entity_id, cache_key)
);

CREATE INDEX idx_entity_cache_lookup ON entity_cache(entity_type, entity_id, cache_key)
    WHERE invalidated_at IS NULL;
CREATE INDEX idx_entity_cache_expired ON entity_cache(valid_until)
    WHERE valid_until IS NOT NULL AND invalidated_at IS NULL;
```

---

### 6.3 Row-Level Security (Multi-tenancy)

```sql
-- Enable RLS on all tables
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE gp_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE lp_profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE people ENABLE ROW LEVEL SECURITY;
ALTER TABLE employment ENABLE ROW LEVEL SECURITY;
ALTER TABLE funds ENABLE ROW LEVEL SECURITY;
ALTER TABLE investments ENABLE ROW LEVEL SECURITY;
ALTER TABLE fund_lp_matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE fund_lp_status ENABLE ROW LEVEL SECURITY;
ALTER TABLE pitches ENABLE ROW LEVEL SECURITY;
ALTER TABLE fund_team ENABLE ROW LEVEL SECURITY;

-- Helper function: Get current user's org_id (derived from employment)
CREATE OR REPLACE FUNCTION current_user_org_id()
RETURNS UUID AS $$
    SELECT e.org_id
    FROM people p
    JOIN employment e ON e.person_id = p.id AND e.is_current = TRUE
    WHERE p.auth_user_id = auth.uid()
    LIMIT 1  -- In case of multiple current jobs, pick one
$$ LANGUAGE sql SECURITY DEFINER;

-- Helper function: Check if current user is super admin
CREATE OR REPLACE FUNCTION is_super_admin()
RETURNS BOOLEAN AS $$
    SELECT COALESCE(
        (SELECT is_super_admin FROM people WHERE auth_user_id = auth.uid()),
        FALSE
    )
$$ LANGUAGE sql SECURITY DEFINER;

-- Helper function: Check if user works at a GP org
CREATE OR REPLACE FUNCTION user_works_at_gp()
RETURNS BOOLEAN AS $$
    SELECT EXISTS (
        SELECT 1 FROM people p
        JOIN employment e ON e.person_id = p.id AND e.is_current = TRUE
        JOIN organizations o ON o.id = e.org_id
        WHERE p.auth_user_id = auth.uid() AND o.is_gp = TRUE
    )
$$ LANGUAGE sql SECURITY DEFINER;

-- Organizations: Users see their own GP org; all LP orgs are readable
CREATE POLICY "Users see own GP org and all LPs" ON organizations
    FOR SELECT USING (
        (is_gp AND id = current_user_org_id())
        OR is_lp
        OR is_super_admin()
    );

-- Organizations: Only super admins can modify
CREATE POLICY "Super admins manage organizations" ON organizations
    FOR INSERT UPDATE DELETE USING (is_super_admin());

-- GP Profiles: Visible to org members, editable by admins
CREATE POLICY "GP profiles visible to org" ON gp_profiles
    FOR SELECT USING (org_id = current_user_org_id() OR is_super_admin());

CREATE POLICY "GP profiles editable by admins" ON gp_profiles
    FOR INSERT UPDATE DELETE USING (
        (org_id = current_user_org_id()
         AND (SELECT role FROM people WHERE auth_user_id = auth.uid()) = 'admin')
        OR is_super_admin()
    );

-- LP Profiles: All LP profiles readable by authenticated users
CREATE POLICY "LP profiles readable" ON lp_profiles
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "LP profiles editable by admins" ON lp_profiles
    FOR INSERT UPDATE DELETE USING (is_super_admin());

-- People: All authenticated users can read (shared contact database)
CREATE POLICY "People readable by authenticated" ON people
    FOR SELECT USING (auth.role() = 'authenticated');

-- People: Super admins can modify all; users can modify their own profile
CREATE POLICY "People editable" ON people
    FOR UPDATE USING (
        auth_user_id = auth.uid()
        OR is_super_admin()
    );

CREATE POLICY "People insertable by admins" ON people
    FOR INSERT WITH CHECK (is_super_admin());

-- Employment: Readable by all authenticated
CREATE POLICY "Employment readable by authenticated" ON employment
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Employment editable by admins" ON employment
    FOR INSERT UPDATE DELETE USING (is_super_admin());

-- Funds: Users manage their org's funds
CREATE POLICY "Users manage own org funds" ON funds
    FOR ALL USING (org_id = current_user_org_id() OR is_super_admin());

-- Investments: Readable by all authenticated (historical data)
CREATE POLICY "Investments readable" ON investments
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Investments editable by admins" ON investments
    FOR INSERT UPDATE DELETE USING (is_super_admin());

-- Fund-LP Matches: GP users see matches for their funds
CREATE POLICY "Users see own matches" ON fund_lp_matches
    FOR SELECT USING (
        fund_id IN (SELECT id FROM funds WHERE org_id = current_user_org_id())
        OR is_super_admin()
    );

CREATE POLICY "System creates matches" ON fund_lp_matches
    FOR INSERT UPDATE DELETE USING (is_super_admin());

-- Fund-LP Status: GP users can update status for their funds
CREATE POLICY "Users see own fund status" ON fund_lp_status
    FOR SELECT USING (
        fund_id IN (SELECT id FROM funds WHERE org_id = current_user_org_id())
        OR is_super_admin()
    );

CREATE POLICY "Users manage own fund status" ON fund_lp_status
    FOR INSERT UPDATE USING (
        fund_id IN (SELECT id FROM funds WHERE org_id = current_user_org_id())
        OR is_super_admin()
    );

-- Pitches: Users see pitches for their matches
CREATE POLICY "Users see own pitches" ON pitches
    FOR ALL USING (
        match_id IN (
            SELECT m.id FROM fund_lp_matches m
            JOIN funds f ON m.fund_id = f.id
            WHERE f.org_id = current_user_org_id()
        )
        OR is_super_admin()
    );

-- Fund team: Visible to org members
CREATE POLICY "Fund team visible to org" ON fund_team
    FOR SELECT USING (
        fund_id IN (SELECT id FROM funds WHERE org_id = current_user_org_id())
        OR is_super_admin()
    );

-- Fund team: Managed by org admins
CREATE POLICY "Fund team managed by admins" ON fund_team
    FOR INSERT UPDATE DELETE USING (
        fund_id IN (SELECT id FROM funds WHERE org_id = current_user_org_id())
        AND (SELECT role FROM people WHERE auth_user_id = auth.uid()) = 'admin'
        OR is_super_admin()
    );
```

---

## 7. Data Pipeline & Enrichment

### 7.1 Data Import Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                     Data Import Pipeline                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  Upload  │───>│  Parse   │───>│  Clean   │───>│  Store   │  │
│  │ CSV/Excel│    │  Detect  │    │ Normalize│    │ Database │  │
│  └──────────┘    │  Types   │    │ Validate │    └──────────┘  │
│                  └──────────┘    └──────────┘                   │
│                                       │                          │
│                                       ▼                          │
│                              ┌──────────────┐                   │
│                              │   Enrich     │                   │
│                              │  (async job) │                   │
│                              └──────────────┘                   │
│                                       │                          │
│                                       ▼                          │
│                              ┌──────────────┐                   │
│                              │  Vectorize   │                   │
│                              │  (Voyage AI) │                   │
│                              └──────────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

### 7.2 Cleaning Rules

#### Strategy Normalization
```python
STRATEGY_MAPPING = {
    # Input variations -> Canonical name
    "pe": "Private Equity",
    "private equity": "Private Equity",
    "buyout": "Private Equity - Buyout",
    "lbo": "Private Equity - Buyout",
    "growth": "Private Equity - Growth",
    "growth equity": "Private Equity - Growth",
    "vc": "Venture Capital",
    "venture": "Venture Capital",
    "venture capital": "Venture Capital",
    "early stage": "Venture Capital - Early Stage",
    "seed": "Venture Capital - Seed",
    "real estate": "Real Estate",
    "re": "Real Estate",
    "infrastructure": "Infrastructure",
    "infra": "Infrastructure",
    "credit": "Private Credit",
    "private credit": "Private Credit",
    "direct lending": "Private Credit - Direct Lending",
    "mezzanine": "Private Credit - Mezzanine",
    "mezz": "Private Credit - Mezzanine",
    # ... more mappings
}
```

#### Geography Normalization
```python
GEOGRAPHY_MAPPING = {
    # Input variations -> ISO code + region
    "us": {"code": "US", "region": "North America"},
    "usa": {"code": "US", "region": "North America"},
    "united states": {"code": "US", "region": "North America"},
    "uk": {"code": "GB", "region": "Europe"},
    "united kingdom": {"code": "GB", "region": "Europe"},
    "germany": {"code": "DE", "region": "Europe"},
    "de": {"code": "DE", "region": "Europe"},
    # ... more mappings
}
```

#### LP Type Normalization
```python
LP_TYPE_MAPPING = {
    "pension": "Public Pension",
    "public pension": "Public Pension",
    "corporate pension": "Corporate Pension",
    "endowment": "Endowment",
    "university endowment": "Endowment",
    "foundation": "Foundation",
    "family office": "Family Office",
    "fo": "Family Office",
    "sfo": "Single Family Office",
    "mfo": "Multi Family Office",
    "fof": "Fund of Funds",
    "fund of funds": "Fund of Funds",
    "swf": "Sovereign Wealth Fund",
    "sovereign wealth": "Sovereign Wealth Fund",
    "insurance": "Insurance Company",
    "insurance company": "Insurance Company",
    # ... more mappings
}
```

### 7.3 Data Sources & Enrichment

**Data Sources (No Web Scraping):**
- **CSV Import:** Bulk upload from spreadsheets (primary source)
- **Manual Entry:** Users add/edit LP records directly
- **Future API Integrations:** Preqin, PitchBook, and other data providers

**Design Principles:**
- No web scraping (no Puppeteer, no automated browsing)
- All data comes from explicit imports or manual entry
- Bulk update support for external data provider feeds
- Human review required before committing enriched data

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Enrichment Flow                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Data Sources:                                                   │
│  ├── CSV/Excel Import (current)                                 │
│  ├── Manual Entry (current)                                     │
│  └── API Integrations (future: Preqin, PitchBook)               │
│                                                                  │
│  Processing Pipeline:                                            │
│                                                                  │
│  1. Import/Update Detection                                     │
│     ├── Parse incoming data                                     │
│     ├── Match against existing records (name + location)        │
│     └── Queue for human review if conflicts detected            │
│                                                                  │
│  2. Human Review (for bulk updates)                             │
│     ├── Show diff between old and new values                    │
│     ├── Allow field-by-field approval                           │
│     └── Require explicit confirmation                           │
│                                                                  │
│  3. Generate Embeddings                                         │
│     ├── Combine: mandate_description + strategies + notes       │
│     ├── Voyage AI: Generate 1024-dim embedding                  │
│     └── Supabase: Store in mandate_embedding column             │
│                                                                  │
│  4. Calculate Data Quality Score                                │
│     ├── Score = weighted sum of field completeness              │
│     ├── Bonus for recent verification                           │
│     └── Supabase: Store in data_quality_score                   │
│                                                                  │
│  5. Update Audit Trail                                          │
│     ├── Record data_source for each field                       │
│     ├── Track last_verified date                                │
│     └── Set verification_status                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Future API Integration Design:**
- Standardized adapter pattern for data providers
- Scheduled sync jobs (configurable frequency)
- Field-level merge rules (e.g., "prefer Preqin for AUM")
- Conflict resolution queue for human review

### 7.4 Data Quality Scoring

```python
def calculate_data_quality_score(lp: LP) -> float:
    """
    Calculate data quality score from 0.0 to 1.0
    """
    weights = {
        # High importance (must have)
        "name": 0.10,
        "type": 0.10,
        "strategies": 0.10,
        "check_size_min_mm": 0.05,
        "check_size_max_mm": 0.05,

        # Medium importance (should have)
        "total_aum_bn": 0.08,
        "geographic_preferences": 0.08,
        "mandate_description": 0.10,
        "website": 0.04,

        # Lower importance (nice to have)
        "sector_preferences": 0.05,
        "min_track_record_years": 0.05,
        "esg_required": 0.03,
        "emerging_manager_program": 0.03,

        # Enrichment bonus
        "has_contacts": 0.07,
        "has_commitments": 0.05,
        "recently_verified": 0.02,
    }

    score = 0.0
    for field, weight in weights.items():
        if field == "has_contacts":
            if lp.contacts and len(lp.contacts) > 0:
                score += weight
        elif field == "has_commitments":
            if lp.commitments and len(lp.commitments) > 0:
                score += weight
        elif field == "recently_verified":
            if lp.last_verified and (now() - lp.last_verified).days < 180:
                score += weight
        elif getattr(lp, field, None):
            score += weight

    return round(score, 2)
```

---

## 8. Technical Architecture

### 8.1 System Architecture

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

### 8.2 Technology Stack

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

### 8.3 Agent Implementation

The multi-agent debate architecture (Section 5.6.3) is implemented using LangGraph for orchestration and Langfuse for monitoring. Full implementation specifications are in:

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

### 8.4 API Design

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
│   └── POST   /invite/{token}/accept  # Accept invite (set password, create account)
│
├── /invitations (admin endpoints)
│   ├── GET    /                   # List pending invitations (company admin)
│   ├── POST   /                   # Create invitation (company admin)
│   ├── DELETE /{id}               # Cancel invitation (company admin)
│   └── POST   /{id}/resend        # Resend invitation email (company admin)
│
├── /users
│   ├── GET    /me                 # Get current user profile
│   ├── PATCH  /me                 # Update current user profile
│   ├── GET    /                   # List company users (company admin)
│   ├── PATCH  /{id}               # Update user role (company admin)
│   └── DELETE /{id}               # Deactivate user (company admin)
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

## 9. MVP Definition & Roadmap

### 9.1 Milestone Overview

| Milestone | Demo Statement | Scope |
|-----------|---------------|-------|
| **M0** | "Data is imported and clean" | Supabase setup, data import, cleaning |
| **M1** | "Search LPs on lpxgp.com" | Auth, RLS, full-text search, Railway deploy |
| **M2** | "Natural language search works" | Voyage AI embeddings, semantic search |
| **M3** | "See matching LPs for my fund" | Fund CRUD, agent debates, Langfuse |
| **M4** | "AI explains matches + generates pitch" | Pitch debate, learning agents, PDF export |
| **M5** | "Production-ready with admin" | Admin dashboard, Sentry, monitoring |

### 9.2 Milestone Details

#### M0: Setup + Data Import
- Project structure (Python monolith)
- Supabase project + tables
- Import existing LP/GP data
- Data cleaning with Claude CLI
- **Exit:** `uv run pytest` passes, localhost:8000/lps shows data

#### M1: Auth + Search + Deploy
- Supabase Auth UI (no custom login forms)
- Row-Level Security (RLS)
- LP full-text search API with filters
- Search UI (Jinja2 + HTMX)
- **Deploy to Railway + CI/CD**
- **Exit:** lpxgp.com live, can register/login/search

#### M2: Semantic Search
- Voyage AI integration
- LP embeddings (pgvector)
- Semantic search endpoint
- Combined filters + semantic
- **Exit:** "climate tech investors" returns relevant results

#### M3: GP Profiles + Matching + Agent Architecture
- Fund profile CRUD with deck upload
- **Multi-agent debate system** (4 debate types, 12 agents)
- LangGraph state machines + Langfuse monitoring
- **Matching Architecture (Quality First):**
  - Initial match: async job queue (5 min to 24 hours)
  - Cached results: load instantly for GP
- **Exit:** Create fund → see matches with score breakdown

#### M4: AI Explanations + Pitch + Learning
- Pitch generation debate (Generator/Critic/Synthesizer)
- Explanation Agent (learns from GP interactions)
- Learning Agent (cross-company intelligence)
- Summary + email generation (human-in-loop)
- PDF export
- **Exit:** Explanations accurate, PDF download works

#### M5: Production Polish
- Admin dashboard (user management, data quality)
- Role-based access (Admin, Member, Viewer)
- Sentry integration
- Performance optimization (< 500ms p95)
- **Exit:** Admin works, no Sentry errors for 24h

### 9.3 Post-MVP Features

**Data Enrichment:**
- Preqin API integration
- Partner data feeds
- Automated enrichment

**LP-Side Matching (Bidirectional):**
- LP users can log in and see matching funds
- LP dashboard with fund recommendations
- LP preference settings

### 9.4 Out of Scope for MVP

- OAuth providers (Google, LinkedIn login)
- AI profile extraction from decks
- Match feedback learning loop
- Actual deck modification (PPTX)
- Advanced analytics
- Mobile optimization
- CRM integrations

---

## 10. User Stories

### 10.1 Authentication

> **Note:** LPxGP is invite-only. There is no self-registration.

```
US-AUTH-01: Accept Invitation
As an invited user, I want to accept my invitation and set up my account.

Acceptance Criteria:
- Invitation link shows company name and my role
- Email field is pre-filled and not editable
- Password must be min 8 chars, 1 uppercase, 1 lowercase, 1 number
- After submission, account is created and I'm logged in
- First-time welcome screen is shown
- Expired invitation shows clear error with "Request new invitation" option

Test: TEST-AUTH-01
```

```
US-AUTH-02: User Login
As an existing user, I want to login so I can access my data.

Acceptance Criteria:
- Email/password authentication works
- Invalid credentials show generic error (security)
- Successful login redirects to dashboard
- First-time users see welcome screen
- Session persists across browser refresh (7 days)
- No "Register" link on login page (invite-only)

Test: TEST-AUTH-02
```

```
US-AUTH-03: Company Isolation
As a user, I should only see data belonging to my company.

Acceptance Criteria:
- User cannot see other companies' funds
- User cannot see other companies' matches
- User cannot see other companies' users
- API returns 404 (not 403) for other company data
- User belongs to exactly one company

Test: TEST-AUTH-03
```

```
US-AUTH-04: Invite Team Member
As a company admin, I want to invite team members so they can use the platform.

Acceptance Criteria:
- Can invite by email address
- Can select role (Member or Admin)
- Invitation email sent within 30 seconds
- Can view pending invitations
- Can resend expired invitations
- Can cancel pending invitations
- Cannot invite email that already has account

Test: TEST-AUTH-04
```

```
US-AUTH-05: Super Admin - Create Company
As a super admin, I want to create companies and invite their first admin.

Acceptance Criteria:
- Can create company with name
- Can enter admin email and send invitation
- Company appears in admin panel
- First user invited automatically gets Admin role
- Can view all companies and their status

Test: TEST-AUTH-05
```

### 10.2 LP Search (Priority A)

```
US-LP-01: Basic LP Search
As a GP, I want to search LPs by criteria so I can find relevant investors.

Acceptance Criteria:
- Filter by: type (multi-select), strategy (multi-select), geography (multi-select)
- Filter by: AUM range (min-max slider)
- Filter by: check size range (min-max slider)
- Results update within 500ms of filter change
- Can combine multiple filters (AND logic)
- Clear all filters button
- Results count shown

Test: TEST-LP-01
```

```
US-LP-02: Semantic LP Search
As a GP, I want to search LPs using natural language so I can describe what I'm looking for.

Acceptance Criteria:
- Free text input field
- Query: "LPs interested in climate tech in Europe" returns relevant results
- Results show relevance score (0-100)
- Can combine semantic search with filters
- Search completes in < 2 seconds

Test: TEST-LP-02
```

```
US-LP-03: View LP Details
As a GP, I want to view LP details so I can understand their preferences.

Acceptance Criteria:
- All LP fields displayed in organized sections
- Contact information shown with LinkedIn links
- Historical commitments listed (if available)
- Data quality indicator shown
- "Last updated" date visible

Test: TEST-LP-03
```

### 10.3 Data Import (Priority A)

```
US-IMPORT-01: CSV Import
As an admin, I want to import LP data from CSV so I can populate the database.

Acceptance Criteria:
- Accept CSV files up to 50MB
- Field mapping interface (source column -> target field)
- Preview first 10 rows before import
- Validation errors shown per row
- Duplicate detection by name + location
- Progress indicator during import
- Summary report after completion

Test: TEST-IMPORT-01
```

```
US-IMPORT-02: Data Cleaning
As an admin, I want imported data to be automatically cleaned so it's usable.

Acceptance Criteria:
- Strategy names normalized to taxonomy
- Geography names standardized
- LP types normalized
- Empty strings converted to NULL
- Whitespace trimmed
- Data quality score calculated

Test: TEST-IMPORT-02
```

```
US-IMPORT-03: Data Enrichment
As an admin, I want LP data enriched from external sources so it's more complete.

Acceptance Criteria:
- Support bulk updates from CSV/Excel
- Future: API integration with data providers (Preqin, PitchBook)
- Enrichment log shows what changed
- Confidence score for enriched fields
- Human review queue before committing changes
- Diff view showing old vs new values

Test: TEST-IMPORT-03
```

### 10.4 Matching (Priority B)

```
US-MATCH-01: Generate Matches
As a GP, I want to generate LP matches for my fund so I can identify targets.

Acceptance Criteria:
- Click button to generate matches
- Loading indicator during generation
- Matches displayed ranked by score (highest first)
- Score shown visually (progress bar + number)
- At least top 50 matches shown
- Generation completes in < 30 seconds

Test: TEST-MATCH-01
```

```
US-MATCH-02: Match Explanation
As a GP, I want to understand why an LP matched so I can tailor my approach.

Acceptance Criteria:
- AI-generated explanation (2-3 paragraphs)
- Key alignment points highlighted (bullets)
- Potential concerns noted (if any)
- Talking points suggested (3-5 bullets)
- Explanation loads in < 5 seconds

Test: TEST-MATCH-02
```

```
US-MATCH-03: Dismiss Match
As a GP, I want to dismiss irrelevant matches so I can focus on good ones.

Acceptance Criteria:
- Dismiss button on each match card
- Optional reason selection (dropdown)
- Dismissed match removed from list
- Can view dismissed matches separately
- Undo dismiss within 10 seconds

Test: TEST-MATCH-03
```

### 10.5 Pitch Generation (Priority C)

```
US-PITCH-01: Generate Summary
As a GP, I want to generate an LP-specific summary so I can send personalized materials.

Acceptance Criteria:
- One click generation from match view
- Summary includes LP-specific talking points
- Professional formatting (headers, bullets)
- Can edit before download
- Export as PDF
- Generation completes in < 10 seconds

Test: TEST-PITCH-01
```

```
US-PITCH-02: Generate Email
As a GP, I want to generate an outreach email so I can contact the LP.

Acceptance Criteria:
- Personalized email generated
- Tone selection (formal, warm, direct)
- Includes specific LP references
- Subject line generated
- Copy to clipboard button
- Edit inline before copying

Test: TEST-PITCH-02
```

---

## 11. Testing Strategy

**See docs/prd/test-specifications.md for detailed test cases.**

TDD approach: Write test first (RED) → Implement (GREEN) → Refactor.

---

## 12. Non-Functional Requirements

### 12.1 Performance

| Metric | Requirement |
|--------|-------------|
| Page load time | < 2 seconds (LCP) |
| Search response | < 500ms |
| Semantic search | < 2 seconds |
| Match generation | < 30 seconds for 100 matches |
| Pitch generation | < 10 seconds |
| Concurrent users | Support 100 simultaneous |
| Database queries | < 100ms for indexed queries |

### 12.2 Security

- All data encrypted at rest (Supabase default)
- All traffic over HTTPS
- JWT tokens with 1 hour expiry
- Refresh tokens with 7 day expiry
- Row-level security enforced
- Input validation on all endpoints
- Rate limiting: 100 req/min per user
- Audit logging for sensitive actions
- No sensitive data in logs

### 12.3 Reliability

- 99.9% uptime target (Supabase SLA)
- Daily automated backups (Supabase)
- Point-in-time recovery (7 days)
- Health check endpoints
- Graceful error handling
- Retry logic for external APIs

### 12.4 Scalability

- Stateless backend (horizontal scaling ready)
- Database connection pooling (Supabase)
- Async operations for AI calls
- Background jobs for enrichment
- Static assets served by FastAPI (Railway handles caching)

---

## 13. Decisions Log

| # | Decision | Options Considered | Rationale |
|---|----------|-------------------|-----------|
| 1 | Supabase Cloud | Self-hosted, Cloud | Faster setup, managed backups, reliable |
| 2 | Voyage AI for embeddings | OpenAI, Cohere, Open source | Best quality for financial domain |
| 3 | Priority A→B→C | Various orders | Search is foundation, then matching, then output |
| 4 | PDF supplement approach | Modify PDF, Generate new | Keep original intact, generate addendum |
| 5 | pgvector for vectors | Pinecone, Weaviate | Integrated with Supabase, no extra service |
| 6 | CDN for frontend, supabase-py for database | npm/bundler, SQLAlchemy | Minimize build tools and dependencies for faster iteration |

---

## 14. Appendix

### 14.1 Glossary

| Term | Definition |
|------|------------|
| **GP** | General Partner - the fund manager who invests capital |
| **LP** | Limited Partner - the investor who provides capital |
| **AUM** | Assets Under Management - total capital managed |
| **DPI** | Distributions to Paid-In - realized returns metric |
| **TVPI** | Total Value to Paid-In - total returns metric |
| **IRR** | Internal Rate of Return - time-weighted return metric |
| **Vintage** | Year the fund started investing |
| **First Close** | Initial capital commitment milestone |
| **Hard Cap** | Maximum fund size |

### 14.2 Strategy Taxonomy

```
Primary Strategies:
├── Private Equity
│   ├── Buyout (Large, Mid, Small)
│   ├── Growth Equity
│   └── Turnaround / Distressed
├── Venture Capital
│   ├── Seed
│   ├── Early Stage
│   ├── Late Stage
│   └── Growth
├── Real Estate
│   ├── Core
│   ├── Value-Add
│   └── Opportunistic
├── Infrastructure
│   ├── Core
│   └── Value-Add
├── Private Credit
│   ├── Direct Lending
│   ├── Mezzanine
│   └── Distressed
├── Secondaries
└── Fund of Funds
```

### 14.3 LP Type Taxonomy

```
LP Types:
├── Public Pension
├── Corporate Pension
├── Endowment
├── Foundation
├── Insurance Company
├── Bank
├── Sovereign Wealth Fund
├── Single Family Office
├── Multi Family Office
├── Fund of Funds
├── Investment Consultant
├── Corporate
└── High Net Worth Individual
```

### 14.4 Geographic Taxonomy

```
Regions:
├── North America
│   ├── United States (US)
│   └── Canada (CA)
├── Europe
│   ├── United Kingdom (GB)
│   ├── Germany (DE)
│   ├── France (FR)
│   ├── Netherlands (NL)
│   ├── Switzerland (CH)
│   ├── Nordics (DK, SE, NO, FI)
│   └── Other Europe
├── Asia Pacific
│   ├── China (CN)
│   ├── Japan (JP)
│   ├── South Korea (KR)
│   ├── Singapore (SG)
│   ├── Hong Kong (HK)
│   ├── Australia (AU)
│   └── Other APAC
├── Middle East
│   ├── UAE (AE)
│   ├── Saudi Arabia (SA)
│   └── Other ME
├── Latin America
│   ├── Brazil (BR)
│   └── Other LATAM
└── Africa
```

---

## Related Documents

- docs/prd/test-specifications.md - Detailed test cases
- docs/curriculum.md - Learning curriculum
