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
└── F-MATCH-04: Match Explanations [P0]

Priority C (Third): Pitch Generation
├── F-PITCH-01: LP-Specific Executive Summary [P0]
└── F-PITCH-02: Outreach Email Draft [P0]
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
ORGANIZATIONS (unified: GPs and LPs)
────────────────────────────────────
┌─────────────────────────────────────────────────────────┐
│                     organizations                        │
│  type: 'gp' | 'lp'                                      │
├─────────────────────────────────────────────────────────┤
│  GP organizations (type='gp'):                          │
│  └── own Funds                                          │
│                                                         │
│  LP organizations (type='lp'):                          │
│  └── receive Matches from Funds                         │
│  └── have LP-specific fields (lp_type, preferences)     │
└─────────────────────────────────────────────────────────┘
                         │
                         │ employs
                         ▼
┌─────────────────────────────────────────────────────────┐
│                      people                              │
│  (all industry professionals)                            │
├─────────────────────────────────────────────────────────┤
│  primary_org_id → organizations.id (current employer)   │
│  auth_user_id → auth.users.id (nullable: login access)  │
│                                                         │
│  Employment history tracks moves between organizations  │
└─────────────────────────────────────────────────────────┘

RELATIONSHIPS
─────────────
organizations (type='gp') ──owns──> funds
funds ──matched_with──> organizations (type='lp') via matches
people ──works_at──> organizations via employment
people ──member_of──> funds via fund_team
matches ──generates──> pitches
```

**Key Design Decisions:**
- **Unified organizations:** GPs and LPs are both organizations with a `type` discriminator
- **People work at organizations:** Clean FK to `organizations.id` (no polymorphic relationships)
- **People can move:** Employment history tracks job changes between any organization
- **Platform users are people:** `auth_user_id` field determines who can login (nullable)
- **No separate users table:** Authentication is just a flag on the people table
- **Referential integrity:** All FKs are real constraints, not polymorphic

### 6.2 Core Tables

#### Organizations (Unified GPs and LPs)
Single table for all organizations - both GP firms and LP investors.
```sql
CREATE TABLE organizations (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    type            TEXT NOT NULL CHECK (type IN ('gp', 'lp')),
    name            TEXT NOT NULL,

    -- Common fields
    website         TEXT,
    hq_city         TEXT,
    hq_country      TEXT,
    total_aum_bn    DECIMAL(12,2),
    description     TEXT,
    settings        JSONB DEFAULT '{}',

    -- LP-specific fields (NULL for GPs)
    lp_type         TEXT CHECK (lp_type IN ('pension', 'endowment', 'foundation',
                                            'family_office', 'sovereign_wealth',
                                            'insurance', 'fund_of_funds', 'other')),
    pe_allocation_pct       DECIMAL(5,2),
    pe_target_allocation_pct DECIMAL(5,2),
    strategies              TEXT[] DEFAULT '{}',
    sub_strategies          TEXT[] DEFAULT '{}',
    check_size_min_mm       DECIMAL(12,2),
    check_size_max_mm       DECIMAL(12,2),
    sweet_spot_mm           DECIMAL(12,2),
    geographic_preferences  TEXT[] DEFAULT '{}',
    sector_preferences      TEXT[] DEFAULT '{}',
    fund_size_preference    TEXT,
    min_track_record_years  INTEGER,
    min_fund_number         INTEGER,
    min_irr_threshold       DECIMAL(5,2),
    min_fund_size_mm        DECIMAL(12,2),
    max_fund_size_mm        DECIMAL(12,2),
    esg_required            BOOLEAN DEFAULT FALSE,
    dei_requirements        BOOLEAN DEFAULT FALSE,
    commitments_per_year    INTEGER,
    avg_commitment_size_mm  DECIMAL(12,2),
    co_investment_interest  BOOLEAN DEFAULT FALSE,
    secondary_activity      BOOLEAN DEFAULT FALSE,
    direct_investment       BOOLEAN DEFAULT FALSE,
    mandate_description     TEXT,
    investment_process      TEXT,
    emerging_manager_program BOOLEAN DEFAULT FALSE,
    emerging_manager_allocation_mm DECIMAL(12,2),

    -- Vector embedding for semantic search (LPs only)
    mandate_embedding       VECTOR(1024),

    -- Data quality (primarily for LPs)
    data_source             TEXT DEFAULT 'manual',
    last_verified           TIMESTAMPTZ,
    verification_status     TEXT CHECK (verification_status IN ('unverified', 'pending', 'verified', 'outdated')) DEFAULT 'unverified',
    data_quality_score      DECIMAL(3,2) DEFAULT 0.0,
    enrichment_status       TEXT CHECK (enrichment_status IN ('pending', 'in_progress', 'completed', 'failed')) DEFAULT 'pending',

    -- Audit
    created_by      UUID REFERENCES auth.users(id),
    updated_by      UUID REFERENCES auth.users(id),
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_organizations_type ON organizations(type);
CREATE INDEX idx_organizations_name_trgm ON organizations USING GIN(name gin_trgm_ops);
CREATE INDEX idx_organizations_strategies ON organizations USING GIN(strategies);
CREATE INDEX idx_organizations_geographic ON organizations USING GIN(geographic_preferences);
CREATE INDEX idx_organizations_mandate_embedding ON organizations USING ivfflat (mandate_embedding vector_cosine_ops);
```

#### People (All Industry Professionals)
All professionals in the industry. Platform users have `auth_user_id` set.
```sql
CREATE TABLE people (
    id                  UUID PRIMARY KEY DEFAULT gen_random_uuid(),

    -- Identity
    full_name           TEXT NOT NULL,
    email               TEXT UNIQUE,
    phone               TEXT,
    linkedin_url        TEXT,

    -- Current position (denormalized for convenience)
    primary_org_id      UUID REFERENCES organizations(id),
    current_title       TEXT,

    -- Platform authentication (NULL = cannot login, SET = can login)
    auth_user_id        UUID UNIQUE REFERENCES auth.users(id),
    role                TEXT CHECK (role IN ('admin', 'member', 'viewer')) DEFAULT 'member',
    is_super_admin      BOOLEAN DEFAULT FALSE,
    invited_by          UUID REFERENCES people(id),
    first_login_at      TIMESTAMPTZ,

    -- Attributes
    focus_areas         TEXT[] DEFAULT '{}',
    is_decision_maker   BOOLEAN DEFAULT FALSE,
    bio                 TEXT,
    notes               TEXT,

    -- Data quality
    data_source         TEXT DEFAULT 'import',
    last_verified       TIMESTAMPTZ,
    verification_status TEXT CHECK (verification_status IN ('unverified', 'pending', 'verified', 'outdated')) DEFAULT 'unverified',

    -- Audit
    created_by          UUID REFERENCES auth.users(id),
    updated_by          UUID REFERENCES auth.users(id),
    created_at          TIMESTAMPTZ DEFAULT NOW(),
    updated_at          TIMESTAMPTZ DEFAULT NOW()
);

-- Index for finding platform users (people who can login)
CREATE INDEX idx_people_auth ON people(auth_user_id) WHERE auth_user_id IS NOT NULL;
CREATE INDEX idx_people_email ON people(email);
CREATE INDEX idx_people_org ON people(primary_org_id);
CREATE INDEX idx_people_name_trgm ON people USING GIN(full_name gin_trgm_ops);
```

#### Employment (Career History)
Links people to organizations over time. Clean FK to organizations.id.
```sql
CREATE TABLE employment (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    person_id       UUID NOT NULL REFERENCES people(id) ON DELETE CASCADE,
    org_id          UUID NOT NULL REFERENCES organizations(id),  -- Clean FK!

    -- Role info
    title           TEXT,
    department      TEXT,
    is_current      BOOLEAN DEFAULT TRUE,

    -- Dates
    start_date      DATE,
    end_date        DATE,                       -- NULL if current

    -- Metadata
    source          TEXT DEFAULT 'import',
    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    -- Constraints
    CONSTRAINT valid_dates CHECK (end_date IS NULL OR end_date >= start_date),
    CONSTRAINT current_has_no_end CHECK (NOT is_current OR end_date IS NULL)
);

CREATE INDEX idx_employment_person ON employment(person_id);
CREATE INDEX idx_employment_org ON employment(org_id);
CREATE INDEX idx_employment_current ON employment(is_current) WHERE is_current = TRUE;
```

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

#### LP Commitments (Historical)
Tracks historical LP commitments to GP funds.
```sql
CREATE TABLE lp_commitments (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    lp_org_id       UUID NOT NULL REFERENCES organizations(id),
    gp_org_id       UUID NOT NULL REFERENCES organizations(id),

    fund_name       TEXT,
    commitment_mm   DECIMAL(12,2),
    vintage_year    INTEGER,
    strategy        TEXT,

    source          TEXT,
    created_at      TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_lp_commitments_lp ON lp_commitments(lp_org_id);
CREATE INDEX idx_lp_commitments_gp ON lp_commitments(gp_org_id);
```

#### Matches
Matches between funds and LP organizations.
```sql
CREATE TABLE matches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    fund_id         UUID NOT NULL REFERENCES funds(id) ON DELETE CASCADE,
    lp_org_id       UUID NOT NULL REFERENCES organizations(id),

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
    status          TEXT CHECK (status IN ('new', 'viewed', 'shortlisted', 'contacted', 'dismissed')) DEFAULT 'new',
    user_feedback   TEXT CHECK (user_feedback IN ('positive', 'negative', NULL)),
    feedback_reason TEXT,

    created_at      TIMESTAMPTZ DEFAULT NOW(),
    updated_at      TIMESTAMPTZ DEFAULT NOW(),

    UNIQUE(fund_id, lp_org_id)
);

CREATE INDEX idx_matches_fund ON matches(fund_id);
CREATE INDEX idx_matches_lp ON matches(lp_org_id);
CREATE INDEX idx_matches_score ON matches(total_score DESC);
```

#### Generated Pitches
```sql
CREATE TABLE pitches (
    id              UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    match_id        UUID NOT NULL REFERENCES matches(id) ON DELETE CASCADE,

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

---

### 6.3 Row-Level Security (Multi-tenancy)

```sql
-- Enable RLS on all tables
ALTER TABLE organizations ENABLE ROW LEVEL SECURITY;
ALTER TABLE people ENABLE ROW LEVEL SECURITY;
ALTER TABLE funds ENABLE ROW LEVEL SECURITY;
ALTER TABLE matches ENABLE ROW LEVEL SECURITY;
ALTER TABLE pitches ENABLE ROW LEVEL SECURITY;
ALTER TABLE employment ENABLE ROW LEVEL SECURITY;
ALTER TABLE fund_team ENABLE ROW LEVEL SECURITY;

-- Helper function: Get current user's org_id
CREATE OR REPLACE FUNCTION current_user_org_id()
RETURNS UUID AS $$
    SELECT primary_org_id FROM people WHERE auth_user_id = auth.uid()
$$ LANGUAGE sql SECURITY DEFINER;

-- Helper function: Check if current user is super admin
CREATE OR REPLACE FUNCTION is_super_admin()
RETURNS BOOLEAN AS $$
    SELECT COALESCE(
        (SELECT is_super_admin FROM people WHERE auth_user_id = auth.uid()),
        FALSE
    )
$$ LANGUAGE sql SECURITY DEFINER;

-- Organizations: Users see their own GP org; all LPs are readable
CREATE POLICY "Users see own GP org" ON organizations
    FOR SELECT USING (
        (type = 'gp' AND id = current_user_org_id())
        OR type = 'lp'
        OR is_super_admin()
    );

-- Organizations: Only super admins can modify
CREATE POLICY "Super admins manage organizations" ON organizations
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

-- Funds: Users manage their org's funds
CREATE POLICY "Users manage own org funds" ON funds
    FOR ALL USING (org_id = current_user_org_id() OR is_super_admin());

-- Matches: Users see matches for their funds
CREATE POLICY "Users see own matches" ON matches
    FOR ALL USING (
        fund_id IN (SELECT id FROM funds WHERE org_id = current_user_org_id())
        OR is_super_admin()
    );

-- Pitches: Users see pitches for their matches
CREATE POLICY "Users see own pitches" ON pitches
    FOR ALL USING (
        match_id IN (
            SELECT m.id FROM matches m
            JOIN funds f ON m.fund_id = f.id
            WHERE f.org_id = current_user_org_id()
        )
        OR is_super_admin()
    );

-- Employment: Readable by all authenticated
CREATE POLICY "Employment readable by authenticated" ON employment
    FOR SELECT USING (auth.role() = 'authenticated');

CREATE POLICY "Employment editable by admins" ON employment
    FOR INSERT UPDATE DELETE USING (is_super_admin());

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

### 8.3 API Design

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

## 9. MVP Definition

**See docs/milestones.md for the detailed roadmap.**

### 9.1 Out of Scope for MVP

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
