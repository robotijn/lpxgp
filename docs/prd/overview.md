# LPxGP Overview

[← Back to Index](index.md)

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

[Next: Feature Requirements →](features/index.md)
