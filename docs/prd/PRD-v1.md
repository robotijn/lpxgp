# Product Requirements Document (PRD)
# LPxGP: GP-LP Intelligence Platform

**Version:** 1.2
**Last Updated:** 2024-12-20
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
| AI/LLM | **Claude API** | Superior document analysis and reasoning |
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
└── F-LP-06: LP Data Enrichment [P0]

Priority B (Second): Matching Engine
├── F-MATCH-01: Hard Filter Matching [P0]
├── F-MATCH-02: Soft Scoring [P0]
├── F-MATCH-03: Semantic Matching [P0]
└── F-MATCH-04: Match Explanations [P0]

Priority C (Third): Pitch Generation
├── F-PITCH-01: LP-Specific Executive Summary [P0]
└── F-PITCH-02: Outreach Email Draft [P0]
```

---

### 5.3 Authentication & Authorization

#### F-AUTH-01: User Authentication [P0]
**Description:** Users can register and login securely
**Requirements:**
- Email/password authentication via Supabase Auth
- Email verification
- Password reset flow
- Session management with JWT

**Test Cases:** See TEST-AUTH-01 in Testing Strategy

#### F-AUTH-02: Multi-tenancy [P0]
**Description:** Users belong to companies, data is isolated
**Requirements:**
- User belongs to exactly one company
- Users only see their company's data
- Row-level security in database
- Company-level settings

**Test Cases:** See TEST-AUTH-02 in Testing Strategy

#### F-AUTH-03: Role-Based Access Control [P0]
**Description:** Different permission levels within a company
**Requirements:**
- Roles: Admin, Member, Viewer
- Admin: manage users, settings, all data
- Member: create/edit/delete own data, view shared
- Viewer: read-only access

**Test Cases:** See TEST-AUTH-03 in Testing Strategy

#### F-AUTH-04: Admin Panel [P0]
**Description:** Super-admin interface for platform management
**Requirements:**
- Create/manage companies
- Create/manage users
- View platform analytics
- Manage LP database (global)
- Trigger data enrichment jobs

**Test Cases:** See TEST-AUTH-04 in Testing Strategy

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
2. LLM (Claude) extracts fund information (strategy, size, team, track record, etc.)
3. System displays extracted fields for GP review and confirmation
4. Interactive questionnaire prompts GP for any missing required fields
5. GP reviews complete profile and approves before saving
6. Profile saved with confirmation status

**Test Cases:** See TEST-GP-02 in Testing Strategy

#### F-GP-03: AI Profile Extraction [P1]
**Description:** Auto-populate profile from uploaded deck
**Requirements:**
- Parse PDF/PPTX content
- Use Claude to extract structured data
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
- Claude-generated explanation (2-3 paragraphs)
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
- Fund profile status summary
- Recent matches (last 10)
- Pending actions count
- Quick stats (total matches, pitches generated)
- Quick actions (new fund, find LPs)

**Test Cases:** See TEST-UI-01 in Testing Strategy

#### F-UI-02: Fund Profile Form [P0]
**Description:** Multi-step form for fund creation
**Requirements:**
- Wizard-style flow (5 steps)
- Progress indicator
- Validation feedback (inline)
- File upload integration
- Save & continue later

**Test Cases:** See TEST-UI-02 in Testing Strategy

#### F-UI-03: LP Search Interface [P0]
**Description:** Powerful LP discovery interface
**Requirements:**
- Filter sidebar (collapsible)
- Results list with key info (cards)
- Quick view modal / detail page
- Bulk actions (add to list, export)
- Sort by relevance, AUM, name

**Test Cases:** See TEST-UI-03 in Testing Strategy

#### F-UI-04: Match Results View [P0]
**Description:** Display matching LPs with context
**Requirements:**
- Ranked list with scores (visual bar)
- Score breakdown on hover/expand
- AI explanation panel (expandable)
- Actions per match (generate pitch, save, dismiss)
- Filter matches by score threshold

**Test Cases:** See TEST-UI-04 in Testing Strategy

#### F-UI-05: Admin Interface [P0]
**Description:** Platform administration UI
**Requirements:**
- User management CRUD table
- Company management
- LP data management (browse, edit, delete)
- Import wizard
- Data enrichment job status
- System health dashboard

**Test Cases:** See TEST-UI-05 in Testing Strategy

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

#### F-HITL-02: Match Selection [P0]
**Description:** GP explicitly approves matches for outreach
**Requirements:**
- Matches shown as recommendations, not actions
- GP must explicitly add LP to shortlist
- Shortlist is separate from match results
- Bulk add to shortlist supported
- Clear distinction between "matched" and "shortlisted"

#### F-HITL-03: Fund Profile Confirmation [P0]
**Description:** GP confirms AI-extracted fund information
**Requirements:**
- AI extraction shows confidence scores per field
- GP reviews each extracted field
- Required fields highlighted if missing
- GP must explicitly approve profile before saving
- Audit trail of what was AI-extracted vs manually entered

#### F-HITL-04: Data Import Preview [P0]
**Description:** Preview and approve data before committing
**Requirements:**
- Show preview of first N rows after mapping
- Highlight validation errors and warnings
- Show duplicate detection results
- Require explicit "Confirm Import" action
- Rollback option within 24 hours

#### F-HITL-05: LP Data Corrections [P1]
**Description:** GPs can flag outdated or incorrect LP information
**Requirements:**
- "Flag as outdated" button on LP profiles
- Optional correction suggestion field
- Flagged records queued for admin review
- Track flag history per LP
- Notify admin of new flags

---

## 6. Data Architecture

### 6.1 Entity Relationship Diagram

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Company   │────<│    User     │     │    Role     │
└─────────────┘     └─────────────┘     └─────────────┘
      │                   │
      │                   │ creates/owns
      │                   ▼
      │             ┌─────────────┐
      └────────────>│    Fund     │
                    └─────────────┘
                          │
                          │ matches with
                          ▼
                    ┌─────────────┐     ┌─────────────┐
                    │   Match     │────>│     LP      │
                    └─────────────┘     └─────────────┘
                          │                   │
                          │                   │
                          ▼                   ▼
                    ┌─────────────┐     ┌─────────────┐
                    │   Pitch     │     │  Contact    │
                    └─────────────┘     └─────────────┘
                                              │
                                              ▼
                                        ┌─────────────┐
                                        │ Enrichment  │
                                        │    Log      │
                                        └─────────────┘
```

### 6.2 Core Tables

#### Companies
```sql
CREATE TABLE companies (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name            TEXT NOT NULL,
    domain          TEXT,
    settings        JSONB DEFAULT '{}',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### Users
```sql
CREATE TABLE users (
    id              UUID PRIMARY KEY REFERENCES auth.users(id),
    company_id      UUID REFERENCES companies(id),
    email           TEXT UNIQUE NOT NULL,
    full_name       TEXT,
    role            TEXT CHECK (role IN ('admin', 'member', 'viewer')) DEFAULT 'member',
    is_super_admin  BOOLEAN DEFAULT FALSE,
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);
```

#### Funds (GP Profiles)
```sql
CREATE TABLE funds (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    company_id          UUID REFERENCES companies(id) NOT NULL,
    created_by          UUID REFERENCES users(id),

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

    -- Team
    team_size           INTEGER,
    key_persons         JSONB DEFAULT '[]',
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
    updated_by          UUID REFERENCES users(id),
    data_source         TEXT DEFAULT 'manual',
    last_verified       TIMESTAMPTZ,
    verification_status TEXT CHECK (verification_status IN ('unverified', 'pending', 'verified', 'outdated')) DEFAULT 'unverified',

    -- Metadata
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_funds_company ON funds(company_id);
CREATE INDEX idx_funds_thesis_embedding ON funds USING ivfflat (thesis_embedding vector_cosine_ops);
```

#### LPs (Investors)
```sql
CREATE TABLE lps (
    id                      UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Organization
    name                    TEXT NOT NULL,
    type                    TEXT,
    sub_type                TEXT,
    total_aum_bn            DECIMAL(12,2),
    pe_allocation_pct       DECIMAL(5,2),
    pe_target_allocation_pct DECIMAL(5,2),
    headquarters_country    TEXT,
    headquarters_city       TEXT,
    website                 TEXT,

    -- Investment Criteria
    strategies              TEXT[] DEFAULT '{}',
    sub_strategies          TEXT[] DEFAULT '{}',
    check_size_min_mm       DECIMAL(12,2),
    check_size_max_mm       DECIMAL(12,2),
    sweet_spot_mm           DECIMAL(12,2),
    geographic_preferences  TEXT[] DEFAULT '{}',
    sector_preferences      TEXT[] DEFAULT '{}',
    fund_size_preference    TEXT,

    -- Requirements
    min_track_record_years  INTEGER,
    min_fund_number         INTEGER,
    min_irr_threshold       DECIMAL(5,2),
    min_fund_size_mm        DECIMAL(12,2),
    max_fund_size_mm        DECIMAL(12,2),
    esg_required            BOOLEAN DEFAULT FALSE,
    dei_requirements        BOOLEAN DEFAULT FALSE,

    -- Behavior
    commitments_per_year    INTEGER,
    avg_commitment_size_mm  DECIMAL(12,2),
    co_investment_interest  BOOLEAN DEFAULT FALSE,
    secondary_activity      BOOLEAN DEFAULT FALSE,
    direct_investment       BOOLEAN DEFAULT FALSE,

    -- Qualitative (for semantic search)
    mandate_description     TEXT,
    investment_process      TEXT,
    notes                   TEXT,

    -- Programs
    emerging_manager_program BOOLEAN DEFAULT FALSE,
    emerging_manager_allocation_mm DECIMAL(12,2),

    -- Vector embedding
    mandate_embedding       VECTOR(1024),

    -- Data Quality & Audit Trail
    created_by              UUID REFERENCES auth.users(id),
    updated_by              UUID REFERENCES auth.users(id),
    data_source             TEXT DEFAULT 'import',
    last_verified           TIMESTAMPTZ,
    verification_status     TEXT CHECK (verification_status IN ('unverified', 'pending', 'verified', 'outdated')) DEFAULT 'unverified',
    data_quality_score      DECIMAL(3,2) DEFAULT 0.0,
    enrichment_status       TEXT CHECK (enrichment_status IN ('pending', 'in_progress', 'completed', 'failed')) DEFAULT 'pending',

    -- Metadata
    created_at              TIMESTAMPTZ DEFAULT NOW(),
    updated_at              TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_lps_type ON lps(type);
CREATE INDEX idx_lps_strategies ON lps USING GIN(strategies);
CREATE INDEX idx_lps_geographic ON lps USING GIN(geographic_preferences);
CREATE INDEX idx_lps_mandate_embedding ON lps USING ivfflat (mandate_embedding vector_cosine_ops);
CREATE INDEX idx_lps_name_trgm ON lps USING GIN(name gin_trgm_ops);
```

#### LP Contacts
```sql
CREATE TABLE lp_contacts (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lp_id           UUID REFERENCES lps(id) ON DELETE CASCADE,

    full_name       TEXT NOT NULL,
    title           TEXT,
    email           TEXT,
    phone           TEXT,
    linkedin_url    TEXT,

    is_decision_maker BOOLEAN DEFAULT FALSE,
    focus_areas     TEXT[] DEFAULT '{}',
    notes           TEXT,

    -- Audit Trail
    created_by      UUID REFERENCES auth.users(id),
    updated_by      UUID REFERENCES auth.users(id),
    data_source     TEXT DEFAULT 'import',
    last_verified   TIMESTAMPTZ,
    verification_status TEXT CHECK (verification_status IN ('unverified', 'pending', 'verified', 'outdated')) DEFAULT 'unverified',

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_lp_contacts_lp ON lp_contacts(lp_id);
```

#### LP Commitments (Historical)
```sql
CREATE TABLE lp_commitments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lp_id           UUID REFERENCES lps(id) ON DELETE CASCADE,

    fund_name       TEXT,
    fund_manager    TEXT,
    commitment_mm   DECIMAL(12,2),
    vintage_year    INTEGER,
    strategy        TEXT,

    source          TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_lp_commitments_lp ON lp_commitments(lp_id);
```

#### Matches
```sql
CREATE TABLE matches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fund_id         UUID REFERENCES funds(id) ON DELETE CASCADE,
    lp_id           UUID REFERENCES lps(id) ON DELETE CASCADE,

    -- Scoring
    total_score     DECIMAL(5,2),
    hard_filter_pass BOOLEAN DEFAULT TRUE,
    score_breakdown JSONB DEFAULT '{}',
    semantic_score  DECIMAL(5,2),

    -- AI Generated
    explanation     TEXT,
    talking_points  TEXT[] DEFAULT '{}',
    concerns        TEXT[] DEFAULT '{}',

    -- Status
    status          TEXT CHECK (status IN ('new', 'viewed', 'contacted', 'dismissed')) DEFAULT 'new',
    user_feedback   TEXT CHECK (user_feedback IN ('positive', 'negative', NULL)),
    feedback_reason TEXT,

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(fund_id, lp_id)
);

CREATE INDEX idx_matches_fund ON matches(fund_id);
CREATE INDEX idx_matches_score ON matches(total_score DESC);
```

#### Generated Pitches
```sql
CREATE TABLE pitches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id        UUID REFERENCES matches(id) ON DELETE CASCADE,

    type            TEXT CHECK (type IN ('email', 'summary', 'addendum')) NOT NULL,
    content         TEXT NOT NULL,
    tone            TEXT,

    created_by      UUID REFERENCES users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_pitches_match ON pitches(match_id);
```

#### Enrichment Log
```sql
CREATE TABLE enrichment_log (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lp_id           UUID REFERENCES lps(id) ON DELETE CASCADE,
    contact_id      UUID REFERENCES lp_contacts(id) ON DELETE CASCADE,

    source          TEXT NOT NULL,
    field_updated   TEXT,
    old_value       TEXT,
    new_value       TEXT,
    confidence      DECIMAL(3,2),

    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_enrichment_lp ON enrichment_log(lp_id);
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
    created_by      UUID REFERENCES users(id),
    approved_by     UUID REFERENCES users(id),
    approved_at     TIMESTAMPTZ,
    data_source     TEXT DEFAULT 'csv_import',

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    completed_at    TIMESTAMPTZ
);
```

---

### 6.3 Row-Level Security (Multi-tenancy)

```sql
-- Enable RLS on all tables
ALTER TABLE companies ENABLE ROW LEVEL SECURITY;
ALTER TABLE users ENABLE ROW LEVEL SECURITY;
ALTER TABLE funds ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE pitches ENABLE ROW LEVEL SECURITY;

-- Users see their own company
CREATE POLICY "Users see own company" ON companies
    FOR SELECT USING (id = (SELECT company_id FROM users WHERE id = auth.uid()));

-- Users see company members
CREATE POLICY "Users see company members" ON users
    FOR SELECT USING (company_id = (SELECT company_id FROM users WHERE id = auth.uid()));

-- Users CRUD their company's funds
CREATE POLICY "Users manage company funds" ON funds
    FOR ALL USING (company_id = (SELECT company_id FROM users WHERE id = auth.uid()));

-- Users see matches for their funds
CREATE POLICY "Users see own matches" ON matches
    FOR ALL USING (fund_id IN (
        SELECT id FROM funds WHERE company_id = (
            SELECT company_id FROM users WHERE id = auth.uid()
        )
    ));

-- LPs are globally readable
CREATE POLICY "LPs readable by authenticated" ON lps
    FOR SELECT USING (auth.role() = 'authenticated');

-- LPs editable by super admins only
CREATE POLICY "LPs editable by admins" ON lps
    FOR INSERT UPDATE DELETE USING (
        EXISTS (SELECT 1 FROM users WHERE id = auth.uid() AND is_super_admin = TRUE)
    );

-- LP contacts follow LP permissions
CREATE POLICY "LP contacts readable" ON lp_contacts
    FOR SELECT USING (auth.role() = 'authenticated');
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
            │   Claude API  │       │   Voyage AI   │
            │   (Analysis)  │       │  (Embeddings) │
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
| **AI/LLM** | Claude API (Anthropic) | Superior document analysis and reasoning |
| **File Storage** | Supabase Storage | Integrated, S3-compatible |
| **PDF Parsing** | PyMuPDF + pdfplumber | Best Python PDF libraries |
| **PPTX Parsing** | python-pptx | Read/write PowerPoint |
| **CI/CD** | GitHub Actions | Integrated with repo, runs tests |
| **Hosting** | Railway | Auto-deploys from GitHub, no Docker needed |
| **Data Enrichment** | API integrations (future) | Preqin, PitchBook for institutional LP data |

### 8.3 API Design

```
/api/v1/
├── /auth
│   ├── POST   /register           # Create new user
│   ├── POST   /login              # Login
│   ├── POST   /logout             # Logout
│   ├── POST   /refresh            # Refresh token
│   ├── POST   /reset-password     # Request password reset
│   └── POST   /verify-email       # Verify email address
│
├── /users
│   ├── GET    /me                 # Get current user
│   ├── PATCH  /me                 # Update current user
│   ├── GET    /                   # List company users (admin)
│   ├── POST   /invite             # Invite user to company (admin)
│   └── DELETE /{id}               # Remove user (admin)
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

## 9. MVP Definition

**See also:** docs/milestones.md for incremental delivery roadmap.

### 9.1 MVP Scope

**M0: Setup + Data Import (1-2 days)**
- Project structure (Python monolith)
- Supabase project + tables
- LP/GP data import and cleaning

**M1: Auth + Search + Deploy (2-3 days)**
- Authentication with Supabase
- Row-Level Security
- LP search with filters (Supabase full-text search, built-in, free)
- HTMX-powered search UI
- Deploy to Railway + CI/CD pipeline

**M2: Semantic Search (1-2 days)**
- Voyage AI integration (semantic search starts here)
- LP embeddings
- Natural language search

**M3: GP Profiles + Matching (2-3 days)**
- Fund profile creation
- Pitch deck upload
- Hard filter + soft scoring
- Semantic matching

**M4: AI Explanations + Pitch (1-2 days)**
- Claude API integration
- Match explanations
- LP-specific summary + email generation

**M5: Production Polish (2-3 days)**
- Admin dashboard
- Error tracking (Sentry)
- Feedback collection
- Performance optimization

### 9.2 Out of Scope for MVP

- OAuth providers (Google, LinkedIn login)
- AI profile extraction from decks
- Match feedback learning loop
- Actual deck modification (PPTX)
- Advanced analytics
- Mobile optimization
- CRM integrations

### 9.3 Milestone-Based Delivery

**See docs/milestones.md for the detailed roadmap.**

Each milestone delivers a demoable product increment:

| Milestone | Demo | Duration |
|-----------|------|----------|
| M0: Setup + Data | "Data is imported and clean" | 1-2 days |
| M1: Auth + Search + Deploy | "Search LPs on lpxgp.com" | 2-3 days |
| M2: Semantic Search | "Natural language search works" | 1-2 days |
| M3: GP Profiles + Matching | "See matching LPs for my fund" | 2-3 days |
| M4: AI + Pitch | "AI explains matches + generates pitch" | 1-2 days |
| M5: Production Polish | "Production-ready with admin" | 2-3 days |

**Key Principles:**
- Every milestone is independently valuable and demoable
- You can stop at any milestone and have a useful product
- Single Python app serves both API and UI (Jinja2 + HTMX)
- Deployment happens in M1; after that, every push auto-deploys

**Architecture:**
```
Railway (Python app) → Supabase (DB + Auth) → Voyage AI (embeddings) → Claude API (analysis)
```

**Future (data enrichment via APIs):**
```
External APIs (Preqin, PitchBook) → Adapter → Human Review → Supabase (store)
```

**Claude CLI vs API:**
| Task | Tool | Cost |
|------|------|------|
| Data cleaning, scripts | CLI | $0 |
| Match explanations | API | ~$0.01/call |
| Pitch generation | API | ~$0.02/call |

---

## 10. User Stories

### 10.1 Authentication

```
US-AUTH-01: User Registration
As a new user, I want to register with my email so I can access the platform.

Acceptance Criteria:
- Email format validated
- Password min 8 chars, 1 number, 1 special
- Verification email sent within 30 seconds
- Cannot login until verified
- Clear error messages for validation failures

Test: TEST-AUTH-01
```

```
US-AUTH-02: User Login
As a registered user, I want to login so I can access my data.

Acceptance Criteria:
- Email/password authentication works
- Invalid credentials show generic error (security)
- Successful login redirects to dashboard
- Session persists across browser refresh (7 days)
- "Remember me" option available

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

Test: TEST-AUTH-03
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

### 11.1 Testing Pyramid

```
                    ┌───────────┐
                    │    E2E    │  Puppeteer (critical flows)
                    │   Tests   │  ~20 tests
                   ─┴───────────┴─
                  ┌───────────────┐
                  │  Integration  │  pytest + httpx
                  │    Tests      │  ~100 tests
                 ─┴───────────────┴─
                ┌───────────────────┐
                │     Unit Tests    │  pytest + Jest
                │                   │  ~300 tests
               ─┴───────────────────┴─
```

### 11.2 Test Files Structure

```
tests/
├── unit/
│   ├── test_cleaning.py        # Data cleaning functions
│   ├── test_scoring.py         # Matching algorithm
│   ├── test_embeddings.py      # Embedding generation
│   └── test_models.py          # Pydantic models
├── integration/
│   ├── test_auth.py            # Auth endpoints
│   ├── test_funds.py           # Fund CRUD
│   ├── test_lps.py             # LP search/CRUD
│   ├── test_matches.py         # Matching endpoints
│   ├── test_pitches.py         # Pitch generation
│   └── test_import.py          # Data import
├── e2e/
│   ├── test_registration.ts    # User signup flow
│   ├── test_fund_creation.ts   # Create fund flow
│   ├── test_lp_search.ts       # Search LPs flow
│   ├── test_matching.ts        # Generate matches flow
│   └── test_pitch_gen.ts       # Generate pitch flow
└── fixtures/
    ├── sample_lps.csv          # Test LP data
    ├── sample_fund.json        # Test fund data
    └── sample_deck.pdf         # Test pitch deck
```

### 11.3 Test Specifications

See separate document: **docs/prd/test-specifications.md**

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

| # | Date | Decision | Options Considered | Rationale |
|---|------|----------|-------------------|-----------|
| 1 | 2024-12-20 | Supabase Cloud | Self-hosted, Cloud | Faster setup, managed backups, reliable |
| 2 | 2024-12-20 | Voyage AI for embeddings | OpenAI, Cohere, Open source | Best quality for financial domain |
| 3 | 2024-12-20 | Priority A→B→C | Various orders | Search is foundation, then matching, then output |
| 4 | 2024-12-20 | PDF supplement approach | Modify PDF, Generate new | Keep original intact, generate addendum |
| 5 | 2024-12-20 | pgvector for vectors | Pinecone, Weaviate | Integrated with Supabase, no extra service |
| 6 | 2024-12-20 | CDN for frontend, supabase-py for database | npm/bundler, SQLAlchemy | Minimize build tools and dependencies for faster iteration |

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

## Document History

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2024-12-20 | Claude | Initial draft |
| 1.1 | 2024-12-20 | Claude | Added data pipeline, enrichment, testing strategy, decisions |
| 1.2 | 2024-12-20 | Claude | Removed web scraping, added human-in-the-loop requirements, updated F-GP-02 flow, added audit trail fields |

---

## Related Documents

- docs/prd/test-specifications.md - Detailed test cases
- docs/curriculum.md - Learning curriculum (to be updated)
