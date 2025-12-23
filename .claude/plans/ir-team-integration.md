# LPxGP: IR Team Integration Strategy + Color Fix

## Quick Task: Fix Mockup Colors to Match Logo

### Problem
The logo uses **gold** (#d4a84b) but mockups define a separate **teal** accent color (#0ea5e9).
This creates brand inconsistency - links and highlights appear teal instead of gold.

### Solution
Replace all `accent` color usages with `gold` across all 30+ mockup files.

### Files to Modify
All HTML files in `/home/tijn/code/lpxgp/docs/mockups/`:
- index.html (line 98: `from-accent-400 to-accent-600` → `from-gold-400 to-gold-600`)
- dashboard.html (multiple `text-accent`, `hover:text-accent` → `text-gold`, `hover:text-gold-600`)
- All other mockups with similar patterns

### Changes Required
1. **Remove accent color definition** from Tailwind config (or change it to gold)
2. **Replace all usages:**
   - `text-accent` → `text-gold`
   - `hover:text-accent` → `hover:text-gold-600`
   - `hover:text-accent-dark` → `hover:text-gold-700`
   - `from-accent-400 to-accent-600` → `from-gold-400 to-gold-600`
   - `bg-accent-*` → `bg-gold-*`

### Validation
After changes, visually confirm all accent colors match the gold in the logo (`#d4a84b`).

---

## Main Task: IR Team Integration Strategy

### Context

**Dual-use Product Vision:**
- **External:** Sell to GPs (fund managers) and LPs (investors) for matching
- **Internal:** Tool for Investor Relations (IR) team to manage event relationships

**Domain:** Events where GPs and LPs connect in real life

---

## Part 1: Goals & Objectives

### Q1: What is the ultimate goal the IR team wants to achieve with the platform?

**Ultimate Goal: Maximize Event Revenue through Relationship Intelligence**

The IR team's core job is ensuring high-value attendance at events. This means:

1. **Attract the right GPs** - Fund managers who are actively raising
2. **Attract the right LPs** - Investors with capital to deploy
3. **Create valuable connections** - Matches that lead to deals

The platform should help IR:
- **Know who matters** - Prioritize outreach to high-value attendees
- **Know them deeply** - Never be caught uninformed in a conversation
- **Track relationship health** - Know where every relationship stands
- **Predict behavior** - Who's likely to attend, invest, or churn

**Success Metric:** Event attendance quality × conversion to commitments

---

### Q2: What are secondary goals the IR team needs to achieve?

**Secondary Goals (in priority order):**

| Goal | Why It Matters |
|------|----------------|
| **1. Preparation efficiency** | Less time researching = more time selling |
| **2. Relationship continuity** | When IR person changes, knowledge stays |
| **3. Follow-up discipline** | No leads fall through the cracks |
| **4. Event matching** | Right person at right event |
| **5. Upsell opportunities** | Identify who might buy more services |
| **6. Competitive intelligence** | Know what events competitors are hosting |
| **7. Data accuracy** | Trust the information in the system |

---

### Q3: What is the current way the IR team achieves these goals?

**Current State (likely):**

| Task | Current Tool | Pain Points |
|------|-------------|-------------|
| Contact management | Excel/Salesforce | Data decay, no GP/LP intelligence |
| Pre-meeting research | Google, LinkedIn, manual | Time-consuming, not captured |
| Event attendee tracking | Spreadsheets | No relationship context |
| Follow-up reminders | Email calendar | Inconsistent, person-dependent |
| Relationship history | Personal memory/notes | Lost when people leave |
| GP/LP intelligence | External databases (PitchBook, Preqin) | Expensive, not integrated |

**Key Insight:** The IR team is doing the SAME research the platform does for GPs - they just need it from a different angle.

---

## Part 2: Product Design & Journey

### Q4: How do we create a product that blends seamlessly into the IR team journey?

**The IR Daily Workflow:**

```
Morning                    During Day                    End of Day
┌──────────┐              ┌──────────┐                  ┌──────────┐
│ Review   │──────────────│ Meetings │──────────────────│ Update   │
│ Schedule │              │ & Calls  │                  │ Notes    │
└────┬─────┘              └────┬─────┘                  └────┬─────┘
     │                         │                              │
     ▼                         ▼                              ▼
┌──────────┐              ┌──────────┐                  ┌──────────┐
│ Prep for │              │ Quick    │                  │ Schedule │
│ each mtg │              │ Lookup   │                  │ Follow-ups│
└──────────┘              └──────────┘                  └──────────┘
```

**Seamless Integration Points:**

1. **Calendar sync** - Auto-pull meetings, pre-populate research cards
2. **Quick search** - Type name → instant full profile
3. **Meeting mode** - One-click "I'm talking to X now" view
4. **Post-meeting capture** - Fast note entry, next action tagging
5. **Mobile-first** - Works at events on phone/tablet
6. **Offline mode** - Event venues often have poor WiFi

---

### Q5: How can this product enhance the event experience for the IR team?

**Before Event:**
- **Attendee briefing book** - Auto-generated profiles of all registered attendees
- **Priority list** - AI-ranked "must meet" based on relationship stage
- **Talking points** - What to say to each person
- **Warm intro map** - Who can introduce who

**During Event:**
- **Badge scan → profile** - Scan attendee badge, see full profile instantly
- **Note capture** - Voice-to-text quick notes
- **Next action queue** - Queue follow-ups as you talk
- **Real-time alerts** - "John Smith just checked in" (high priority)

**After Event:**
- **Auto follow-up drafts** - Pre-written based on notes
- **Event ROI** - Which conversations led to deals?
- **Relationship movement** - Who moved pipeline stages?

---

### Q6: How can this product enhance the event experience for LPs and GPs?

**For LPs attending:**
- **Curated introductions** - "Based on your mandate, meet these GPs"
- **Meeting scheduler** - Book 1:1s with relevant GPs
- **Post-event summaries** - What you discussed, materials promised
- **Deal flow tracking** - Track funds you're interested in

**For GPs attending:**
- **LP intelligence** - Who's allocating? What do they look for?
- **Meeting prep** - Talking points for each LP
- **Event ROI** - Which event led to commitments?
- **Warm intro requests** - Ask IR for specific introductions

**Key Insight:** The product SERVES the IR team while SHOWCASING value to GPs/LPs → they want to buy it for themselves.

---

## Part 3: Design Philosophy

### Q7: What is the right type of design for this software?

**Design Principles for Financial/Investment Software:**

| Element | Recommendation | Rationale |
|---------|----------------|-----------|
| **Typography** | Sans-serif (Inter, DM Sans) | Modern, readable, professional |
| **Colors** | Navy/dark blue primary, green accents for positive, red for alerts | Trust, money, urgency |
| **Data density** | High, but organized | Users want information, not whitespace |
| **Visual style** | Minimal decoration | Focus on content |
| **Iconography** | Outlined, simple | Professional, not playful |
| **Spacing** | Tight but breathing | Efficiency without overwhelm |

**Reference Products:**
- Bloomberg Terminal (data density)
- Linear (modern SaaS feel)
- Carta (professional finance)
- Notion (organization)

**Key Design Goals:**
1. **Speed** - Information appears instantly
2. **Scannability** - Glance and understand
3. **Density** - Show lots of data without clutter
4. **Trust** - Feel secure and reliable
5. **Professionalism** - Matches the audience's expectations

---

### Q8: How can we demonstrate reliability and privacy through design?

**Trust Signals:**

| Signal | Implementation |
|--------|----------------|
| **Data freshness** | "Last updated 2 hours ago" badges |
| **Source attribution** | "From: LinkedIn" or "From: PitchBook" |
| **Confidence levels** | "Confirmed" vs "Likely" vs "Unverified" |
| **Audit trail** | "Added by John on Dec 1" |
| **Access indicators** | "Visible to: IR Team only" |
| **Encryption badges** | 🔒 icon on sensitive fields |

**Privacy Design:**
- Clear visibility scopes (My notes, Team notes, Company-wide)
- Obvious data sharing indicators
- Easy data export/deletion
- GDPR/compliance badges where relevant

---

### Q9: How can we foster IR team adoption through design?

**Adoption Drivers:**

1. **Zero friction entry** - No training needed to start
2. **Immediate value** - First search shows useful info
3. **Better than alternative** - Faster than googling
4. **Habit hooks** - Daily digest email, meeting reminders
5. **Social proof** - "Sarah updated this profile"
6. **Gamification** (subtle) - Data completeness scores
7. **Mobile excellence** - Works perfectly at events

**Anti-patterns to avoid:**
- Mandatory fields that slow entry
- Complex workflows for simple tasks
- Information scattered across screens
- Slow load times
- Features that require training

---

## Part 4: Minimum Viable Product

### Q10: What is the minimum functionality to replace current IR operations?

**MVP Feature Set:**

| Category | Must Have | Nice to Have |
|----------|-----------|--------------|
| **Search** | Instant GP/LP search by name | Fuzzy matching, filters |
| **Profiles** | View GP/LP full profile | Edit profiles |
| **Notes** | Add meeting notes | Voice-to-text |
| **Events** | List attendees | Badge scan, check-in |
| **Contacts** | View key people | LinkedIn sync |
| **Follow-ups** | Task list | Auto-reminders |
| **Mobile** | Basic mobile view | Native app |

**MVP Definition:**
> "IR can prepare for a meeting in 30 seconds instead of 10 minutes"

---

### Q11: What integrations does this software need?

**Critical Integrations:**

| System | Purpose | Priority |
|--------|---------|----------|
| **Calendar** (Google/Outlook) | Meeting context | P0 |
| **Email** (read-only) | Relationship signals | P1 |
| **LinkedIn** | Profile enrichment | P1 |
| **Event platform** (Eventbrite, Bizzabo) | Attendee sync | P1 |
| **CRM** (Salesforce, HubSpot) | Sync contacts | P2 |
| **PitchBook/Preqin** | LP data enrichment | P2 |
| **Badge scanners** | Event check-in | P2 |

---

## Part 5: Data Architecture

### Q12: What are all the data types we should consider?

**Core Entity Types:**

```
┌─────────────────────────────────────────────────────────────┐
│                     ORGANIZATIONS                           │
│  ┌─────────────┐      ┌─────────────┐                      │
│  │     GP      │      │     LP      │                      │
│  │ (fund mgr)  │      │ (investor)  │                      │
│  └──────┬──────┘      └──────┬──────┘                      │
│         │                    │                              │
│         ▼                    ▼                              │
│  ┌─────────────┐      ┌─────────────┐                      │
│  │   FUNDS     │      │  MANDATES   │                      │
│  └─────────────┘      └─────────────┘                      │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       PEOPLE                                │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐ │
│  │   PERSON    │──────│ EMPLOYMENT  │──────│    ORG      │ │
│  └─────────────┘      └─────────────┘      └─────────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       EVENTS                                │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐ │
│  │   EVENT     │──────│ ATTENDANCE  │──────│   PERSON    │ │
│  └─────────────┘      └─────────────┘      └─────────────┘ │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                    INTERACTIONS                             │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐ │
│  │   MEETING   │      │   EMAIL     │      │    NOTE     │ │
│  └─────────────┘      └─────────────┘      └─────────────┘ │
│         │                    │                    │         │
│         └────────────────────┼────────────────────┘         │
│                              ▼                              │
│                       ┌─────────────┐                       │
│                       │ TOUCHPOINT  │                       │
│                       └─────────────┘                       │
└─────────────────────────────────────────────────────────────┘

┌─────────────────────────────────────────────────────────────┐
│                       PIPELINE                              │
│  ┌─────────────┐      ┌─────────────┐      ┌─────────────┐ │
│  │    DEAL     │      │    TASK     │      │  FOLLOW-UP  │ │
│  └─────────────┘      └─────────────┘      └─────────────┘ │
└─────────────────────────────────────────────────────────────┘
```

**New Entity Types for IR (not in current schema):**

| Entity | Purpose |
|--------|---------|
| **Event** | Conference, summit, dinner |
| **Attendance** | Who's at which event |
| **Touchpoint** | Any interaction (meeting, call, email) |
| **IR Note** | Internal notes not visible to GPs/LPs |
| **Task** | Follow-up actions |
| **Deal** | Event sponsorship, booth sales |

---

### Q13: What are all the data fields per data type?

#### **ORGANIZATIONS (Base)**

| Field | Type | Required | Source | IR Use |
|-------|------|----------|--------|--------|
| `name` | text | ✓ | Manual | Identification |
| `legal_name` | text | | SEC/Manual | Contracts |
| `short_name` | text | | Manual | Quick reference |
| `logo_url` | url | | Manual/Scrape | Visual recognition |
| `website` | url | | Manual | Research |
| `linkedin_url` | url | | Manual | Research |
| `description` | text | | Manual | Context |
| `hq_city` | text | ✓ | Manual | Geography |
| `hq_country` | text | ✓ | Manual | Geography |
| `hq_timezone` | text | | Derived | Scheduling |
| `founded_year` | int | | Manual | History |
| `employee_count` | int | | Manual | Size |
| `is_gp` | bool | ✓ | Manual | Role |
| `is_lp` | bool | ✓ | Manual | Role |
| `is_active` | bool | ✓ | Manual | Filter |
| `tier` | enum | | Manual | Prioritization |
| `tags` | array | | Manual | Segmentation |
| `ir_owner_id` | fk | | Manual | Accountability |
| `notes` | text | | Manual | Context |

---

#### **GP PROFILES**

| Field | Type | Required | Source | IR Use |
|-------|------|----------|--------|--------|
| **Identity** |
| `org_id` | fk | ✓ | System | Link |
| `firm_type` | enum | ✓ | Manual | Classification |
| ↳ `buyout`, `growth`, `venture`, `real_estate`, `infrastructure`, `credit`, `secondaries`, `fund_of_funds`, `multi_strategy` |
| `year_founded` | int | | Manual | Track record |
| `predecessor_firm` | text | | Manual | Pedigree |
| `spin_out_from` | fk | | Manual | Pedigree |
| **Strategy** |
| `primary_strategy` | text | ✓ | Manual | Matching |
| `secondary_strategies` | array | | Manual | Matching |
| `geographic_focus` | array | ✓ | Manual | Matching |
| `sector_focus` | array | | Manual | Matching |
| `investment_thesis` | text | | Manual | Deep understanding |
| `typical_hold_period` | text | | Manual | Strategy context |
| `value_add_approach` | text | | Manual | Differentiation |
| **Team** |
| `team_size` | int | | Manual | Scale |
| `investment_professionals` | int | | Manual | Scale |
| `years_investing_together` | int | | Manual | Stability signal |
| `key_person_names` | array | | Manual | Know the players |
| **Track Record** |
| `total_aum_bn` | decimal | | Manual | Scale |
| `funds_raised` | int | | Manual | Track record |
| `total_capital_raised_bn` | decimal | | Manual | Track record |
| `total_invested_bn` | decimal | | Manual | Track record |
| `realized_proceeds_bn` | decimal | | Manual | Performance |
| `notable_investments` | jsonb | | Manual | Talking points |
| `notable_exits` | jsonb | | Manual | Talking points |
| `gross_irr` | decimal | | Manual | Performance |
| `net_irr` | decimal | | Manual | Performance |
| `moic` | decimal | | Manual | Performance |
| `dpi` | decimal | | Manual | Performance |
| **Current State** |
| `currently_raising` | bool | | Manual | Hot lead signal |
| `current_fund_name` | text | | Manual | Context |
| `current_fund_target_mm` | decimal | | Manual | Sizing |
| `current_fund_raised_mm` | decimal | | Manual | Progress |
| `expected_close_date` | date | | Manual | Timeline |
| `first_close_date` | date | | Manual | Urgency |
| **Relationships** |
| `placement_agent` | text | | Manual | Channel intel |
| `primary_counsel` | text | | Manual | Network |
| `primary_admin` | text | | Manual | Network |
| `anchor_lps` | array | | Manual | Reference LPs |
| **Meta** |
| `data_quality_score` | decimal | | Computed | Prioritize updates |
| `last_verified` | timestamp | | Manual | Freshness |
| `last_researched` | timestamp | | System | Recency |

---

#### **LP PROFILES**

| Field | Type | Required | Source | IR Use |
|-------|------|----------|--------|--------|
| **Identity** |
| `org_id` | fk | ✓ | System | Link |
| `lp_type` | enum | ✓ | Manual | Classification |
| ↳ `public_pension`, `corporate_pension`, `endowment`, `foundation`, `family_office`, `sovereign_wealth`, `insurance`, `fund_of_funds`, `bank`, `ria`, `other` |
| `sub_type` | text | | Manual | Nuance |
| **Size & Allocation** |
| `total_aum_bn` | decimal | | Manual | Scale |
| `pe_allocation_pct` | decimal | | Manual | Opportunity |
| `pe_allocation_bn` | decimal | | Computed | Absolute opportunity |
| `target_pe_allocation_pct` | decimal | | Manual | Direction |
| `annual_commitment_pace_mm` | decimal | | Manual | Pipeline sizing |
| **Mandate - Strategy** |
| `strategies` | array | ✓ | Manual | Matching |
| `strategy_preferences` | jsonb | | Manual | Detailed prefs |
| `avoided_strategies` | array | | Manual | Don't waste time |
| **Mandate - Geography** |
| `geographic_preferences` | array | | Manual | Matching |
| `geographic_restrictions` | array | | Manual | Don't waste time |
| `home_bias` | bool | | Manual | Pattern |
| **Mandate - Size** |
| `check_size_min_mm` | decimal | | Manual | Matching |
| `check_size_max_mm` | decimal | | Manual | Matching |
| `check_size_sweet_spot_mm` | decimal | | Manual | Best fit |
| `fund_size_min_mm` | decimal | | Manual | Matching |
| `fund_size_max_mm` | decimal | | Manual | Matching |
| **Mandate - Requirements** |
| `min_track_record_years` | int | | Manual | Qualifying |
| `min_fund_number` | int | | Manual | Qualifying |
| `requires_reference_lps` | bool | | Manual | Process |
| `esg_required` | bool | | Manual | Filter |
| `esg_standards` | array | | Manual | Detail |
| `dei_requirements` | text | | Manual | Requirements |
| `emerging_manager_program` | bool | | Manual | Opportunity |
| `emerging_manager_allocation_mm` | decimal | | Manual | Size |
| **Investment Process** |
| `decision_timeline_months` | int | | Manual | Expectation setting |
| `typical_dd_items` | array | | Manual | Preparation |
| `requires_onsite_visit` | bool | | Manual | Process |
| `investment_committee_frequency` | text | | Manual | Timing |
| `fiscal_year_end` | text | | Manual | Budget cycle |
| `board_approval_threshold_mm` | decimal | | Manual | Process |
| **Interests** |
| `co_invest_interest` | bool | | Manual | Opportunity |
| `co_invest_min_mm` | decimal | | Manual | Sizing |
| `direct_interest` | bool | | Manual | Opportunity |
| `secondary_interest` | bool | | Manual | Opportunity |
| `gp_stake_interest` | bool | | Manual | Opportunity |
| **Relationship Intelligence** |
| `current_gp_relationships` | int | | Manual | Relationship density |
| `new_relationships_per_year` | int | | Manual | Openness to new |
| `preferred_intro_method` | text | | Manual | Approach |
| `conferences_attended` | array | | Manual | Event targeting |
| **Decision Makers** |
| `primary_contact_id` | fk | | Manual | Key person |
| `decision_maker_ids` | array | | Manual | Who matters |
| `ic_member_ids` | array | | Manual | Full committee |
| **Behavioral** |
| `responsiveness` | enum | | Manual | Expectation |
| ↳ `highly_responsive`, `normal`, `slow`, `unresponsive` |
| `meeting_preference` | enum | | Manual | Logistics |
| ↳ `in_person`, `video`, `phone`, `no_preference` |
| `communication_style` | enum | | Manual | Approach |
| ↳ `formal`, `casual`, `direct`, `relationship_focused` |
| **Meta** |
| `mandate_description` | text | | Manual | Free-form context |
| `last_commitment_date` | date | | Manual | Activity signal |
| `actively_looking` | bool | | Manual | Hot lead |
| `allocation_available_mm` | decimal | | Manual | Opportunity |
| `next_allocation_date` | date | | Manual | Timing |
| `data_quality_score` | decimal | | Computed | Priority |
| `last_verified` | timestamp | | Manual | Freshness |

---

#### **PEOPLE (Contacts)**

| Field | Type | Required | Source | IR Use |
|-------|------|----------|--------|--------|
| **Identity** |
| `id` | uuid | ✓ | System | |
| `full_name` | text | ✓ | Manual | |
| `first_name` | text | | Derived | Personalization |
| `last_name` | text | | Derived | |
| `preferred_name` | text | | Manual | "Call me Bob" |
| `pronouns` | text | | Manual | Respect |
| `photo_url` | url | | LinkedIn | Recognition |
| **Contact** |
| `email` | text | ✓ | Manual | Primary contact |
| `email_secondary` | text | | Manual | Backup |
| `phone` | text | | Manual | |
| `phone_type` | enum | | Manual | Mobile/Office |
| `linkedin_url` | url | | Manual | Research |
| `twitter_url` | url | | Manual | |
| `assistant_name` | text | | Manual | Gatekeeping |
| `assistant_email` | text | | Manual | Scheduling |
| **Professional** |
| `current_title` | text | | Derived | Context |
| `current_org_id` | fk | | Derived | Link |
| `seniority_level` | enum | | Manual | Prioritization |
| ↳ `c_suite`, `partner`, `director`, `vp`, `manager`, `analyst`, `other` |
| `is_decision_maker` | bool | | Manual | Flag |
| `decision_authority_mm` | decimal | | Manual | Threshold |
| `department` | text | | Manual | Context |
| `reports_to_id` | fk | | Manual | Org chart |
| **Background** |
| `bio` | text | | Manual | Context |
| `education` | jsonb | | Manual | Connection points |
| `certifications` | array | | Manual | CFA, etc. |
| `languages` | array | | Manual | Communication |
| `previous_firms` | array | | LinkedIn | Network mapping |
| `years_in_industry` | int | | Manual | Experience |
| **Personal (for rapport)** |
| `location_city` | text | | Manual | Travel planning |
| `timezone` | text | | Derived | Scheduling |
| `birthday_month` | int | | Manual | Touchpoints |
| `interests` | array | | Manual | Small talk |
| `alma_mater` | text | | Manual | Connection |
| `military_service` | bool | | Manual | Connection |
| `board_memberships` | array | | Manual | Network |
| **Relationship** |
| `relationship_owner_id` | fk | | Manual | Accountability |
| `relationship_strength` | int | | Manual | 1-5 score |
| `first_met_date` | date | | Manual | History |
| `first_met_context` | text | | Manual | Story |
| `warm_intro_through` | fk | | Manual | Connection |
| **Preferences** |
| `preferred_contact_method` | enum | | Manual | |
| `best_time_to_call` | text | | Manual | |
| `meeting_preference` | enum | | Manual | |
| `dietary_restrictions` | text | | Manual | Events |
| `travel_preferences` | text | | Manual | Events |
| **Flags** |
| `is_vip` | bool | | Manual | Priority |
| `is_speaker` | bool | | Manual | Content |
| `is_advisory_board` | bool | | Manual | Relationship |
| `do_not_contact` | bool | | Manual | Compliance |
| `do_not_contact_reason` | text | | Manual | |
| **Notes** |
| `internal_notes` | text | | Manual | IR only |
| `talking_points` | array | | Manual | Prep |
| `topics_to_avoid` | array | | Manual | Landmines |
| `last_contacted` | timestamp | | System | Recency |
| `next_action` | text | | Manual | Follow-up |
| `next_action_date` | date | | Manual | Reminder |

---

#### **EMPLOYMENT (Career History)**

| Field | Type | Required | Source | IR Use |
|-------|------|----------|--------|--------|
| `person_id` | fk | ✓ | System | |
| `org_id` | fk | ✓ | System | |
| `title` | text | ✓ | Manual | Context |
| `department` | text | | Manual | |
| `start_date` | date | | Manual | Tenure |
| `end_date` | date | | Manual | |
| `is_current` | bool | ✓ | Manual | |
| `responsibilities` | text | | Manual | |
| `achievements` | text | | Manual | Talking points |
| `left_reason` | text | | Manual | Intel |
| `confidence` | enum | | Manual | Data quality |
| `source` | text | | Manual | |

---

#### **FUNDS (GP Funds)**

| Field | Type | Required | Source | IR Use |
|-------|------|----------|--------|--------|
| **Identity** |
| `org_id` | fk | ✓ | System | |
| `name` | text | ✓ | Manual | |
| `fund_number` | int | | Manual | Fund I, II, etc. |
| `status` | enum | ✓ | Manual | Pipeline stage |
| ↳ `pre_marketing`, `raising`, `first_close`, `final_close`, `closed`, `investing`, `harvesting` |
| `vintage_year` | int | | Manual | |
| **Sizing** |
| `target_size_mm` | decimal | | Manual | Scale |
| `hard_cap_mm` | decimal | | Manual | Maximum |
| `current_size_mm` | decimal | | Manual | Progress |
| `first_close_mm` | decimal | | Manual | Milestone |
| `first_close_date` | date | | Manual | Timeline |
| `final_close_target` | date | | Manual | Urgency |
| **Strategy** |
| `strategy` | text | ✓ | Manual | Matching |
| `sub_strategy` | text | | Manual | |
| `geographic_focus` | array | | Manual | |
| `sector_focus` | array | | Manual | |
| `investment_thesis` | text | | Manual | |
| **Parameters** |
| `check_size_min_mm` | decimal | | Manual | |
| `check_size_max_mm` | decimal | | Manual | |
| `target_companies` | int | | Manual | |
| `target_ownership_pct` | text | | Manual | |
| `holding_period_years` | int | | Manual | |
| **Terms** |
| `management_fee_pct` | decimal | | Manual | |
| `carried_interest_pct` | decimal | | Manual | |
| `hurdle_rate_pct` | decimal | | Manual | |
| `gp_commitment_pct` | decimal | | Manual | |
| `fund_term_years` | int | | Manual | |
| **Track Record** |
| `track_record` | jsonb | | Manual | Performance |
| `prior_fund_irr` | decimal | | Manual | |
| `prior_fund_moic` | decimal | | Manual | |
| **ESG** |
| `esg_policy` | bool | | Manual | |
| `impact_focus` | bool | | Manual | |
| `esg_certifications` | array | | Manual | |
| **Docs** |
| `pitch_deck_url` | url | | Manual | |
| `ppm_url` | url | | Manual | |
| `data_room_url` | url | | Manual | |

---

#### **EVENTS (NEW - for IR)**

| Field | Type | Required | Source | IR Use |
|-------|------|----------|--------|--------|
| **Identity** |
| `id` | uuid | ✓ | System | |
| `name` | text | ✓ | Manual | |
| `short_name` | text | | Manual | |
| `event_type` | enum | ✓ | Manual | Classification |
| ↳ `conference`, `summit`, `dinner`, `roundtable`, `webinar`, `roadshow`, `workshop`, `networking`, `other` |
| `series_id` | fk | | Manual | Annual events |
| `edition` | text | | Manual | "2024", "Q4" |
| **Timing** |
| `start_date` | date | ✓ | Manual | |
| `end_date` | date | ✓ | Manual | |
| `timezone` | text | ✓ | Manual | |
| `registration_deadline` | date | | Manual | |
| `early_bird_deadline` | date | | Manual | |
| **Location** |
| `format` | enum | ✓ | Manual | |
| ↳ `in_person`, `virtual`, `hybrid` |
| `venue_name` | text | | Manual | |
| `venue_address` | text | | Manual | |
| `city` | text | | Manual | |
| `country` | text | | Manual | |
| `virtual_platform` | text | | Manual | Zoom, etc. |
| **Audience** |
| `target_audience` | array | | Manual | |
| `gp_focus` | bool | | Manual | |
| `lp_focus` | bool | | Manual | |
| `strategies_focus` | array | | Manual | |
| `max_attendees` | int | | Manual | |
| `current_registrations` | int | | Computed | |
| **Content** |
| `theme` | text | | Manual | |
| `description` | text | | Manual | |
| `agenda_url` | url | | Manual | |
| `speakers` | array | | Manual | |
| **Commercial** |
| `ticket_price_usd` | decimal | | Manual | |
| `sponsorship_tiers` | jsonb | | Manual | |
| `target_revenue_usd` | decimal | | Manual | |
| `actual_revenue_usd` | decimal | | Computed | |
| **IR Operations** |
| `event_owner_id` | fk | ✓ | Manual | Accountability |
| `ir_team_attending` | array | | Manual | |
| `target_gp_count` | int | | Manual | Goals |
| `target_lp_count` | int | | Manual | Goals |
| `notes` | text | | Manual | |
| **Status** |
| `status` | enum | ✓ | Manual | |
| ↳ `planning`, `announced`, `registration_open`, `sold_out`, `completed`, `cancelled` |

---

#### **EVENT ATTENDANCE (NEW)**

| Field | Type | Required | Source | IR Use |
|-------|------|----------|--------|--------|
| `event_id` | fk | ✓ | System | |
| `person_id` | fk | ✓ | System | |
| `org_id` | fk | | Derived | |
| **Registration** |
| `registration_date` | timestamp | | System | |
| `registration_status` | enum | ✓ | Manual | |
| ↳ `invited`, `registered`, `confirmed`, `waitlisted`, `cancelled`, `no_show`, `attended` |
| `ticket_type` | text | | Manual | VIP, standard, etc. |
| `invited_by_id` | fk | | Manual | Who invited |
| `registration_source` | text | | Manual | How they found us |
| **Attendance** |
| `checked_in` | bool | | System | |
| `checked_in_at` | timestamp | | System | |
| `badge_id` | text | | System | Scanner integration |
| `sessions_attended` | array | | System | |
| **Engagement** |
| `is_speaker` | bool | | Manual | |
| `is_sponsor` | bool | | Manual | |
| `sponsor_tier` | text | | Manual | |
| `meetings_scheduled` | int | | Computed | |
| `meetings_attended` | int | | Computed | |
| **IR Notes** |
| `priority_level` | enum | | Manual | |
| ↳ `must_meet`, `should_meet`, `nice_to_meet`, `no_priority` |
| `talking_points` | array | | Manual | Prep for this event |
| `goals` | text | | Manual | What do we want |
| `notes` | text | | Manual | Post-event notes |
| `follow_up_required` | bool | | Manual | |
| `follow_up_owner_id` | fk | | Manual | |

---

#### **TOUCHPOINTS (All Interactions - NEW)**

| Field | Type | Required | Source | IR Use |
|-------|------|----------|--------|--------|
| `id` | uuid | ✓ | System | |
| `person_id` | fk | ✓ | System | |
| `org_id` | fk | | Derived | |
| **Type** |
| `touchpoint_type` | enum | ✓ | Manual | Classification |
| ↳ `meeting`, `call`, `email`, `event_interaction`, `linkedin_message`, `text`, `coffee`, `dinner`, `conference_meetup`, `intro_made`, `referral_received`, `other` |
| `direction` | enum | ✓ | Manual | |
| ↳ `outbound`, `inbound`, `mutual` |
| **Timing** |
| `occurred_at` | timestamp | ✓ | Manual | |
| `duration_minutes` | int | | Manual | |
| **Context** |
| `event_id` | fk | | Manual | If at event |
| `location` | text | | Manual | |
| `format` | enum | | Manual | |
| ↳ `in_person`, `video`, `phone`, `async` |
| **Participants** |
| `our_attendees` | array | ✓ | Manual | IR team members |
| `their_attendees` | array | | Manual | Other people |
| **Content** |
| `subject` | text | | Manual | Topic/purpose |
| `summary` | text | | Manual | What happened |
| `key_takeaways` | array | | Manual | Highlights |
| `commitments_made` | array | | Manual | What we promised |
| `commitments_received` | array | | Manual | What they promised |
| **Sentiment** |
| `sentiment` | enum | | Manual | |
| ↳ `very_positive`, `positive`, `neutral`, `negative`, `very_negative` |
| `engagement_level` | enum | | Manual | |
| ↳ `highly_engaged`, `engaged`, `neutral`, `disengaged` |
| **Follow-up** |
| `follow_up_required` | bool | | Manual | |
| `follow_up_by_date` | date | | Manual | |
| `follow_up_owner_id` | fk | | Manual | |
| `follow_up_completed` | bool | | Manual | |
| **Attachments** |
| `attachments` | jsonb | | Manual | Files shared |
| `recording_url` | url | | Manual | If recorded |

---

#### **TASKS (Follow-ups - NEW)**

| Field | Type | Required | Source | IR Use |
|-------|------|----------|--------|--------|
| `id` | uuid | ✓ | System | |
| `title` | text | ✓ | Manual | |
| `description` | text | | Manual | |
| **Association** |
| `person_id` | fk | | Manual | Related contact |
| `org_id` | fk | | Manual | Related org |
| `event_id` | fk | | Manual | Related event |
| `touchpoint_id` | fk | | Manual | Spawned from |
| **Assignment** |
| `assigned_to_id` | fk | ✓ | Manual | |
| `created_by_id` | fk | ✓ | System | |
| **Timing** |
| `due_date` | date | | Manual | |
| `reminder_date` | date | | Manual | |
| `priority` | enum | | Manual | |
| ↳ `urgent`, `high`, `normal`, `low` |
| **Status** |
| `status` | enum | ✓ | Manual | |
| ↳ `pending`, `in_progress`, `completed`, `cancelled`, `deferred` |
| `completed_at` | timestamp | | System | |
| **Notes** |
| `notes` | text | | Manual | |
| `outcome` | text | | Manual | Result |

---

#### **IR NOTES (Internal Only - NEW)**

| Field | Type | Required | Source | IR Use |
|-------|------|----------|--------|--------|
| `id` | uuid | ✓ | System | |
| `entity_type` | enum | ✓ | Manual | |
| ↳ `person`, `organization`, `fund`, `event` |
| `entity_id` | uuid | ✓ | Manual | |
| **Content** |
| `note_type` | enum | | Manual | |
| ↳ `general`, `intel`, `warning`, `opportunity`, `relationship` |
| `content` | text | ✓ | Manual | |
| `is_sensitive` | bool | | Manual | Extra restricted |
| `visibility` | enum | | Manual | |
| ↳ `private`, `team`, `company` |
| **Meta** |
| `created_by_id` | fk | ✓ | System | |
| `created_at` | timestamp | ✓ | System | |
| `updated_at` | timestamp | | System | |
| `pinned` | bool | | Manual | Important |

---

## Part 6: GP & LP Understanding

### Q14: What is the best way to describe a GP and an LP?

**GP Profile Structure:**

```
IDENTITY
├── Organization name
├── Logo, website
├── HQ location
├── Founded year
└── Team size

STRATEGY
├── Investment focus (PE, VC, RE, etc.)
├── Geographic focus
├── Sector focus
├── Check size range
├── Fund size range
└── Investment thesis (free text)

TRACK RECORD
├── Funds raised (history)
├── Notable investments
├── Notable exits
├── Performance (if disclosed)
└── LP base (who invested)

TEAM
├── Key partners
├── Background/pedigree
├── Years together
└── Notable alumni

CURRENT STATE
├── Currently raising?
├── Target fund size
├── Timeline to close
└── Current investors
```

**LP Profile Structure:**

```
IDENTITY
├── Organization name
├── Type (pension, endowment, family office, etc.)
├── HQ location
├── Total AUM
└── PE/VC allocation %

MANDATE
├── Strategies interested in
├── Geographic focus
├── Sector preferences
├── Check size range
├── Fund size preferences
└── Mandate description (free text)

REQUIREMENTS
├── Track record minimums
├── ESG requirements
├── Emerging manager program?
├── Co-invest interest?
└── Direct interest?

DECISION PROCESS
├── Decision makers
├── Investment committee
├── Timeline (typical)
├── Current pipeline
└── Recent commitments

RELATIONSHIP
├── Prior interactions
├── Events attended
├── Warm connections
└── IR owner
```

---

### Q15: How can we understand what a GP and an LP see for their future?

**Future Signals:**

| Entity | Forward-Looking Data |
|--------|---------------------|
| **GP** | Currently raising? Fund target? Timeline? Pipeline deals? |
| **LP** | Actively looking? Allocation available? Target close? |

**Capture Methods:**
1. **Direct entry** - IR asks and records
2. **Public filings** - SEC, pension board minutes
3. **News** - Press releases, interviews
4. **Inference** - Fund I closed 3 years ago → likely raising Fund II

**Data Model:**

```sql
-- GP future state
funds:
  status: 'raising' | 'closed' | 'invested' | 'harvesting'
  target_size_mm: DECIMAL
  final_close_target: DATE
  current_size_mm: DECIMAL  -- how much raised so far

-- LP future state
lp_match_preferences:
  actively_looking: BOOLEAN
  allocation_available_mm: DECIMAL
  target_close_date: DATE
```

---

### Q16: How can we describe what an LP and a GP did in the past?

**Historical Data:**

| Entity | Past Data |
|--------|-----------|
| **GP** | Prior funds raised, investments made, exits achieved |
| **LP** | Prior commitments, funds invested in, co-investments |

**Existing Tables (already in schema):**

```sql
-- GP history
funds: vintage_year, track_record (JSONB), notable_exits (JSONB)

-- LP history
investments: lp_org_id, fund_id, commitment_mm, commitment_date

-- Relationship history
outreach_events: event_type, event_date, notes
```

---

### Q17: What information does the IR team need to appear deeply knowledgeable?

**The "Know Everything" Card:**

```
┌─────────────────────────────────────────────────────────────┐
│ JOHN SMITH                                     CalPERS     │
│ Managing Director, Private Equity              [LP Badge]  │
├─────────────────────────────────────────────────────────────┤
│ QUICK FACTS                                                │
│ • Decision maker for PE allocations up to $500M           │
│ • 15 years at CalPERS, previously at KKR                  │
│ • Stanford MBA, CFA charterholder                         │
│ • Board: Pension Fund Association                         │
├─────────────────────────────────────────────────────────────┤
│ RECENT ACTIVITY                                            │
│ • Oct 2024: Committed $200M to Vista Fund VIII            │
│ • Sep 2024: Met at SuperReturn (we introduced)            │
│ • Aug 2024: Declined Thoma Bravo (concentration)          │
├─────────────────────────────────────────────────────────────┤
│ OUR RELATIONSHIP                                           │
│ • 3 events attended (2023-2024)                           │
│ • Last spoke: Nov 15 (Sarah - follow up on speakers)      │
│ • Sentiment: Warm, engaged                                │
│ • Next action: Invite to Davos dinner                     │
├─────────────────────────────────────────────────────────────┤
│ TALKING POINTS                                             │
│ ✓ "How was Vista closing? Heard they hit $26B"           │
│ ✓ "Still looking at growth equity for Q1?"               │
│ ✓ "Any interest in our Asia GP summit?"                  │
├─────────────────────────────────────────────────────────────┤
│ AVOID                                                      │
│ ✗ Don't mention healthcare - bad experience with ABC      │
│ ✗ Sensitive about CalPERS governance issues               │
└─────────────────────────────────────────────────────────────┘
```

---

### Q18: What is the best way to visualize this for IR during conversations?

**Views by Context:**

| Context | View | Key Info |
|---------|------|----------|
| **Before meeting** | Full profile | Everything above |
| **During meeting** | Quick card | Name, role, last interaction, talking points |
| **At event** | Mobile card | Photo, name, org, "why they matter" |
| **After meeting** | Note entry | Pre-filled with attendees, quick actions |

**Quick Lookup (Mobile-first):**

```
┌────────────────────────┐
│ 🔍 John Sm...          │
├────────────────────────┤
│ 📷 John Smith          │
│ CalPERS • MD, PE       │
│ ────────────────────── │
│ Last: Nov 15 (Sarah)   │
│ 💡 Interested in Asia  │
│ ⚠️ Skip healthcare     │
├────────────────────────┤
│ [View Full] [Add Note] │
└────────────────────────┘
```

---

## Part 7: Data Automation & Trust

### Q19: How can we automate data ingestion while maintaining reliability?

**Source Trust System:**

| Source | Trust Level | Auto-commit? |
|--------|-------------|--------------|
| **User entry** | Confirmed | Yes |
| **CRM sync** | High | Yes |
| **LinkedIn** | Medium | Yes, with freshness decay |
| **News scrape** | Low | Queue for review |
| **AI inference** | Lowest | Always review |

**Data Quality Pipeline:**

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   Ingest    │────▶│  Validate   │────▶│   Store     │
│  (source)   │     │  (trust)    │     │ (w/ source) │
└─────────────┘     └─────────────┘     └─────────────┘
                           │
                    low trust?
                           │
                           ▼
                    ┌─────────────┐
                    │  Human      │
                    │  Review     │
                    └─────────────┘
```

**Provenance Tracking:**

```sql
-- Every field can have metadata
lp_profiles:
  data_source: TEXT
  last_verified: TIMESTAMPTZ
  confidence: ENUM (confirmed, likely, inferred)

-- Detailed source tracking
data_provenance:
  entity_type, entity_id, field_name
  value, source, confidence
  captured_at, captured_by
  supersedes: FK (previous version)
```

---

### Q20: How can this information build better event experiences?

**Pre-Event Intelligence:**

1. **Attendee analysis** - "This event has 40 LPs actively allocating to growth equity"
2. **Match suggestions** - "GP X should meet LP Y (85% match)"
3. **Conflict detection** - "LP A and LP B both invested in same sector - separate tables"
4. **VIP identification** - "These 5 attendees account for 60% of potential capital"

**During Event:**

1. **Real-time check-in alerts** - "High-priority LP just arrived"
2. **Introduction facilitation** - "Sarah, introduce GP X to LP Y at booth 3"
3. **Conversation starters** - Push notification: "LP just closed Fund VIII - congrats!"

**Post-Event:**

1. **Relationship mapping** - "Who met whom based on notes"
2. **Deal tracking** - "3 meetings likely to result in commitments"
3. **Event ROI** - "Event led to $500M in commitments over 6 months"

---

## Part 8: Additional Information Needs

### Q21: What other information besides GP/LP past, present, future is useful?

**Market Intelligence:**
- Fund performance benchmarks
- Sector allocation trends
- Geographic flow patterns
- Competitor event intelligence

**Relationship Intelligence:**
- Warm introduction paths
- Shared connections
- Alumni networks
- Board relationships

**Event Intelligence:**
- Historical attendance patterns
- Event ROI by attendee type
- Optimal event formats
- Speaker effectiveness

**Operational Intelligence:**
- IR team workload
- Follow-up completion rates
- Response time metrics
- Territory coverage gaps

---

## Part 9: Data Integration Architecture (Master Data Management)

### The Problem: Industry Data Mess

The IR team's data exists in multiple fragmented sources:
- Salesforce, HubSpot, or other CRMs
- Excel spreadsheets (definitely)
- Legacy databases
- Email inboxes
- LinkedIn connections
- Event registration systems (Eventbrite, Bizzabo)
- External data providers (PitchBook, Preqin)

**Goal:** Create a single source of truth using entity resolution.

---

### Entity Resolution Library Comparison (Detailed)

Given your requirements (<100K records, human review, skepticism of pure Bayesian, interest in bootstrapping):

| Library | Approach | Precision | Recall | Scalability | Training | Pros | Cons |
|---------|----------|-----------|--------|-------------|----------|------|------|
| **Splink** | Probabilistic (Fellegi-Sunter) | 60-76% | 85-98% | 7M in 2 mins | Unsupervised | Fast, no labels needed | Over-matches, priors not data-grounded |
| **Dedupe** | Active Learning | ~99% | 75-97% | <2M records | Interactive labeling | High precision, learns from humans | Effort to label, memory constraints |
| **RecordLinkage** | Traditional ML (LogReg, SVM, NB) | Tunable | Tunable | Medium | Supervised | Extensible, ensemble-friendly | Needs labels, no blocking built-in |
| **Entity-embed** | Deep Learning + ANN | Variable | ~99% | Very high | Requires training | Great for blocking stage | Needs good initial model |
| **LLM-based** | Semantic reasoning | High | High | Low (cost) | Zero-shot | Understands context | Expensive per-pair |

#### Research Findings on LLM Entity Resolution (2024-2025)

From recent academic research ([Springer 2025](https://link.springer.com/chapter/10.1007/978-3-031-78548-1_21), [arXiv 2024](https://arxiv.org/html/2310.06174v2)):

1. **LMCD Framework**: Graph community detection with LLM edge pruning - retrieves embedding neighbors, then uses LLM to remove false positives
2. **Cost-efficient prompt engineering**: GPT-3.5 achieves good results with structured prompts for unsupervised ER
3. **Selecting strategy** is most cost-effective for LLM-based entity matching
4. **Ensemble + Transformers**: Single-architecture ensembles make LLM ensembles viable

### Recommended Architecture: Hybrid Bootstrapping Pipeline

Based on your preferences (ensemble start → bootstrap to complex → selective LLM):

```
┌─────────────────────────────────────────────────────────────────┐
│                 STAGE 1: BLOCKING                               │
├─────────────────────────────────────────────────────────────────┤
│ Hybrid: Name (metaphone) + Embedding (Voyage AI) + Rules        │
│ Libraries: metaphone, pgvector (ANN), rule-based                │
│ Output: ~5-10x candidate pairs vs brute force                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                 STAGE 2: FEATURE EXTRACTION                     │
├─────────────────────────────────────────────────────────────────┤
│ 20+ features:                                                   │
│ • Name: Levenshtein, Jaro-Winkler, token_sort, metaphone       │
│ • Semantic: Embedding similarity (Voyage AI)                    │
│ • Structural: AUM ratio, strategy overlap, entity type          │
│ • Identifiers: Domain match, LinkedIn, email                    │
│ Library: rapidfuzz, custom feature extractor                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                 STAGE 3: ENSEMBLE CLASSIFIER                    │
├─────────────────────────────────────────────────────────────────┤
│ Bootstrap: Generate heuristic labels from high-confidence rules │
│ Models: LogReg (35%) + GBM (35%) + RF (20%) + SVM (10%)        │
│ Output: P(match) with model agreement score                     │
│ Library: scikit-learn                                           │
│                                                                 │
│ Decision zones:                                                 │
│ • p > 0.8 → MATCH                                              │
│ • p < 0.3 → NON-MATCH                                          │
│ • 0.3 ≤ p ≤ 0.8 → UNCERTAIN (→ LLM or Human)                   │
└────────────────────────────┬────────────────────────────────────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
         ┌────────┐    ┌──────────┐   ┌──────────┐
         │ MATCH  │    │ UNCERTAIN│   │NON-MATCH │
         └────────┘    └────┬─────┘   └──────────┘
                            │
┌───────────────────────────▼─────────────────────────────────────┐
│                 STAGE 4: LLM TIEBREAKER                         │
├─────────────────────────────────────────────────────────────────┤
│ Only for uncertain pairs (~10-20% of candidates)                │
│ Model: Claude Sonnet via OpenRouter                             │
│ Structured output: decision, confidence, evidence_for/against   │
│ Cost: ~$0.003-0.01 per pair                                     │
│                                                                 │
│ Decision: MATCH, NON-MATCH, or → HUMAN QUEUE                    │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                 STAGE 5: HUMAN REVIEW QUEUE                     │
├─────────────────────────────────────────────────────────────────┤
│ Priority-based queue with ML+LLM context                        │
│ IR team validates difficult cases                               │
│ Decisions fed back to training → MODEL IMPROVEMENT              │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                 STAGE 6: CLUSTERING                             │
├─────────────────────────────────────────────────────────────────┤
│ Graph-based transitive closure with conflict detection          │
│ Library: networkx                                               │
│ Large/uncertain clusters → Human review                         │
└────────────────────────────┬────────────────────────────────────┘
                             │
┌────────────────────────────▼────────────────────────────────────┐
│                 STAGE 7: GOLDEN RECORDS                         │
├─────────────────────────────────────────────────────────────────┤
│ Field-by-field merge with source priority tracking              │
│ Priority: Manual > Verified > PitchBook > Imported              │
│ Full provenance audit trail                                     │
└─────────────────────────────────────────────────────────────────┘
```

### Bootstrap Strategy (Zero-Label Start)

```python
# High-confidence heuristic rules for initial labels
def heuristic_label(rec_a, rec_b, features):
    # MATCH rules
    if same_linkedin_url(rec_a, rec_b): return 1
    if same_domain(rec_a, rec_b) and name_sim > 0.9: return 1
    if exact_name_match and same_city: return 1

    # NON-MATCH rules
    if very_different_aum(100x) and different_country: return 0
    if name_sim < 0.3 and no_shared_identifiers: return 0

    return None  # Uncertain - don't use for training
```

### Learning Loop

```
Human Decisions ──────────────────┐
                                  │
                                  ▼
┌────────────────┐          ┌─────────────┐
│ Heuristic      │──Train──▶│  Ensemble   │
│ Labels (v0)    │          │  Model v1   │
└────────────────┘          └──────┬──────┘
                                   │
                                   ▼
                            Classify new pairs
                                   │
                                   ▼
                            Uncertain → LLM/Human
                                   │
                                   ▼
                            Human validates
                                   │
                                   ▼
                            Add to training set
                                   │
                                   ▼
┌────────────────┐          ┌─────────────┐
│ Human Labels   │──Retrain▶│  Ensemble   │
│ + Heuristics   │          │  Model v2   │
└────────────────┘          └─────────────┘
```

### Why This Approach Works for Your Requirements

| Your Requirement | How Addressed |
|-----------------|---------------|
| Skeptical of pure Bayesian | Ensemble starts with data-driven ML, not Fellegi-Sunter priors |
| Interest in bootstrapping | Heuristic labels → train → human feedback → retrain |
| <100K records | Can afford generous blocking and LLM calls |
| Human review handles edge cases | Priority queue with ML/LLM context |
| LLMs with architecture | Selective use (10-20%), structured output, evidence-based |
| Grounded in actual data | Training always from real matches, not assumed distributions |

---

### Refinement: Stacking Meta-Learner (Monthly Retrain)

Rather than fixed weights, use **stacking** where a meta-learner combines base model predictions:

```python
from sklearn.ensemble import StackingClassifier

stacking_classifier = StackingClassifier(
    estimators=[
        ('logreg', LogisticRegression()),
        ('gbm', GradientBoostingClassifier()),
        ('rf', RandomForestClassifier()),
        ('svm', CalibratedClassifierCV(SVC())),
    ],
    final_estimator=LogisticRegression(),  # Meta-learner
    cv=5,
    stack_method='predict_proba'
)

# Monthly retrain schedule
async def monthly_retrain():
    # Fetch all training data (heuristic + human labels)
    training_data = await fetch_all_training_data()

    # Retrain stacking classifier
    stacking_classifier.fit(X_train, y_train)

    # Evaluate on holdout
    cv_score = cross_val_score(stacking_classifier, X, y, cv=5)

    # Save model version
    await save_model_version(stacking_classifier, cv_score)
```

**Why monthly?**
- Accumulates ~50-200 new human labels per month
- Data distribution may shift (new GPs/LPs with different patterns)
- Balances improvement vs. stability

**Monthly Retrain with Caching Strategy:**

```python
from datetime import datetime, timedelta
import hashlib
import pickle

class CachedERClassifier:
    """Entity resolution with monthly retrain and aggressive caching."""

    def __init__(self, cache_dir: str = "/tmp/er_cache"):
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.model = None
        self.model_version = None
        self.classification_cache = {}  # In-memory for hot path

    def _pair_hash(self, rec_a: dict, rec_b: dict) -> str:
        """Deterministic hash for a pair of records."""
        # Sort by ID to ensure (A,B) == (B,A)
        ids = sorted([rec_a.get("id", ""), rec_b.get("id", "")])
        key_fields = ["id", "name", "website", "linkedin_url", "hq_city"]
        data = {
            "a": {k: rec_a.get(k) for k in key_fields},
            "b": {k: rec_b.get(k) for k in key_fields},
        }
        return hashlib.sha256(str(sorted(ids) + [data]).encode()).hexdigest()[:16]

    async def classify(self, rec_a: dict, rec_b: dict) -> dict:
        """Classify with caching - only compute if not cached."""
        pair_hash = self._pair_hash(rec_a, rec_b)

        # Check in-memory cache first (hot path)
        if pair_hash in self.classification_cache:
            return self.classification_cache[pair_hash]

        # Check persistent cache
        cache_file = self.cache_dir / f"{pair_hash}.pkl"
        if cache_file.exists():
            cached = pickle.loads(cache_file.read_bytes())
            # Only use if same model version
            if cached.get("model_version") == self.model_version:
                self.classification_cache[pair_hash] = cached["result"]
                return cached["result"]

        # Compute fresh classification
        result = await self._compute_classification(rec_a, rec_b)

        # Cache it
        self.classification_cache[pair_hash] = result
        cache_file.write_bytes(pickle.dumps({
            "model_version": self.model_version,
            "result": result,
            "computed_at": datetime.utcnow().isoformat(),
        }))

        return result

    async def monthly_retrain(self):
        """Retrain model monthly - invalidates cache for changed predictions."""
        # Fetch training data
        training_data = await fetch_all_training_data()

        # Retrain
        new_model = StackingClassifier(...)
        new_model.fit(X_train, y_train)

        # Evaluate
        cv_score = cross_val_score(new_model, X, y, cv=5)

        # Only deploy if improvement or similar performance
        if cv_score.mean() >= self.current_score - 0.02:  # Allow 2% tolerance
            self.model = new_model
            self.model_version = datetime.utcnow().strftime("%Y%m")
            self.classification_cache.clear()  # Invalidate in-memory cache
            # Persistent cache auto-invalidates via version check

            await save_model_version(new_model, cv_score, self.model_version)
            return {"status": "updated", "score": cv_score.mean()}

        return {"status": "kept_existing", "reason": "new model worse"}

# Scheduler (e.g., via cron or APScheduler)
# Run on 1st of each month at 3am
@scheduler.scheduled_job('cron', day=1, hour=3)
async def scheduled_retrain():
    classifier = get_classifier_instance()
    result = await classifier.monthly_retrain()
    log.info(f"Monthly retrain: {result}")
```

**Cache Benefits:**
- **Hot path:** In-memory dict for frequently accessed pairs
- **Persistent:** Disk cache survives restarts, keyed by pair hash + model version
- **Auto-invalidation:** Model version in cache → stale entries ignored after retrain
- **Deterministic:** Same pair always produces same hash regardless of order

**Note on Convergence:** After initial data ingest, the data won't change dramatically. Monthly retraining serves as a checkpoint, not continuous drift. The cache ensures we don't recompute stable classifications. A few percentage points difference in model confidence won't change classification outcomes significantly.

---

### Refinement: Cold Start Problem (Getting Good Heuristic Labels)

**Challenge:** Need initial training data, but no human labels yet.

**Solution: Multi-tier heuristic rules with confidence gradients**

```python
# Tier 1: VERY HIGH CONFIDENCE (use for training)
# These rules have near-100% precision
tier1_match_rules = [
    # Same unique identifier
    lambda a, b: a.get("linkedin_url") == b.get("linkedin_url") and a.get("linkedin_url"),

    # Exact name + same registered address
    lambda a, b: (
        normalize(a["name"]) == normalize(b["name"])
        and a.get("hq_city") == b.get("hq_city")
        and a.get("hq_country") == b.get("hq_country")
    ),

    # Same SEC CIK number (if available)
    lambda a, b: a.get("sec_cik") == b.get("sec_cik") and a.get("sec_cik"),
]

tier1_non_match_rules = [
    # Different entity types AND different countries
    lambda a, b: (
        a.get("lp_type") != b.get("lp_type")
        and a.get("hq_country") != b.get("hq_country")
        and a.get("lp_type") and b.get("lp_type")
    ),

    # 1000x AUM difference (e.g., $10B vs $10M)
    lambda a, b: (
        a.get("total_aum_bn") and b.get("total_aum_bn")
        and max(a["total_aum_bn"], b["total_aum_bn"]) /
            max(min(a["total_aum_bn"], b["total_aum_bn"]), 0.001) > 1000
    ),

    # Completely different names + no shared identifiers
    lambda a, b: (
        fuzz.ratio(normalize(a["name"]), normalize(b["name"])) < 20
        and not same_domain(a, b)
        and not same_linkedin(a, b)
    ),
]

# Tier 2: HIGH CONFIDENCE (use for training with lower weight)
tier2_match_rules = [
    # Same website domain + name similarity > 0.8
    lambda a, b: (
        same_domain(a.get("website"), b.get("website"))
        and fuzz.token_set_ratio(a["name"], b["name"]) > 80
    ),

    # Phonetic match + same city
    lambda a, b: (
        doublemetaphone(a["name"])[0] == doublemetaphone(b["name"])[0]
        and a.get("hq_city") == b.get("hq_city")
        and doublemetaphone(a["name"])[0]  # Not empty
    ),
]

# Tier 3: MEDIUM CONFIDENCE (validation set, not training)
# Use to evaluate model performance, not to train
tier3_candidates = [
    lambda a, b: (
        fuzz.token_set_ratio(a["name"], b["name"]) > 70
        and same_country(a, b)
    ),
]

def generate_bootstrap_labels(pairs):
    """Generate training labels with confidence tiers."""
    labels = []

    for a, b in pairs:
        # Tier 1 - high confidence, full weight
        for rule in tier1_match_rules:
            if rule(a, b):
                labels.append((a, b, 1, 1.0))  # (a, b, label, weight)
                break
        for rule in tier1_non_match_rules:
            if rule(a, b):
                labels.append((a, b, 0, 1.0))
                break

        # Tier 2 - medium confidence, reduced weight
        for rule in tier2_match_rules:
            if rule(a, b):
                labels.append((a, b, 1, 0.7))
                break

    return labels
```

**Bootstrap Strategy:**
1. Generate candidate pairs via blocking (generous)
2. Apply Tier 1 rules → ~5-10% of pairs get labels
3. Apply Tier 2 rules → another ~10-15%
4. Train initial model on Tier 1+2 (weighted)
5. Evaluate on Tier 3 candidates (don't train)
6. Route uncertain pairs to human → collect real labels
7. After 50+ human labels, retrain with mixed data

**Expected cold-start timeline:**
- Day 1: Heuristic model (70-80% accuracy)
- Week 2: 50+ human labels → improved model
- Month 1: 200+ human labels → stable model
- Ongoing: Monthly retrain with accumulated data

---

### Refinement: Domain-Specific Features for GP/LP

Beyond generic string similarity, add **financial domain features**:

```python
@dataclass
class FinancialFeatures:
    """Domain-specific features for GP/LP entity resolution."""

    # Organization Type Features
    both_gp: float  # 1 if both are GPs
    both_lp: float  # 1 if both are LPs
    type_compatible: float  # 1 if types match or one is GP+LP

    # Investment Strategy Features
    strategy_jaccard: float  # Jaccard similarity of strategy lists
    primary_strategy_match: float  # 1 if primary strategies match
    strategy_embedding_sim: float  # Semantic similarity of strategy descriptions

    # Size & Scale Features
    aum_log_diff: float  # |log(aum_a) - log(aum_b)|, normalized
    aum_same_order: float  # 1 if same order of magnitude (1-10x)
    check_size_overlap: float  # Do check size ranges overlap?

    # Geographic Features
    same_country: float
    same_region: float  # NA, EU, APAC, etc.
    geo_preference_overlap: float  # Jaccard of geographic preferences

    # Track Record Features
    vintage_year_diff: float  # |vintage_a - vintage_b|, normalized
    fund_number_diff: float  # |fund_num_a - fund_num_b|
    both_emerging: float  # Both are emerging managers

    # Relationship Features
    shared_investments: float  # Do they have LPs in common? (GP-GP)
    prior_relationship: float  # 1 if known prior relationship exists

    # Name Pattern Features
    has_fund_number_a: float  # "Fund III", "II", etc.
    has_fund_number_b: float
    fund_number_match: float  # Same fund number in name?
    has_geography_a: float  # "Asia Fund", "Europe Partners"
    has_geography_b: float
    geography_match: float  # Same geography in name?

    # Legal Entity Features
    same_legal_suffix: float  # Both "LLC", both "LP", etc.
    name_without_suffix_sim: float  # Similarity after removing suffixes

class DomainFeatureExtractor:
    """Extract domain-specific features for financial entities."""

    LEGAL_SUFFIXES = [
        " llc", " lp", " llp", " inc", " corp", " ltd",
        " partners", " capital", " management", " advisors",
        " fund", " investments", " asset management"
    ]

    FUND_NUMBER_PATTERN = r'\b(I{1,3}|IV|V|VI{0,3}|[1-9]|1[0-9]|20)\b'

    GEOGRAPHY_KEYWORDS = [
        "asia", "europe", "americas", "global", "us", "china",
        "japan", "india", "latam", "emea", "apac", "mena"
    ]

    def extract(self, rec_a: dict, rec_b: dict) -> FinancialFeatures:
        return FinancialFeatures(
            # Type features
            both_gp=float(rec_a.get("is_gp") and rec_b.get("is_gp")),
            both_lp=float(rec_a.get("is_lp") and rec_b.get("is_lp")),
            type_compatible=self._type_compatible(rec_a, rec_b),

            # Strategy features
            strategy_jaccard=self._jaccard(
                rec_a.get("strategies", []),
                rec_b.get("strategies", [])
            ),
            primary_strategy_match=float(
                rec_a.get("primary_strategy") == rec_b.get("primary_strategy")
                and rec_a.get("primary_strategy")
            ),
            strategy_embedding_sim=self._embedding_sim(
                rec_a.get("thesis_embedding"),
                rec_b.get("thesis_embedding")
            ),

            # Size features
            aum_log_diff=self._aum_log_diff(rec_a, rec_b),
            aum_same_order=self._aum_same_order(rec_a, rec_b),
            check_size_overlap=self._check_size_overlap(rec_a, rec_b),

            # Geographic features
            same_country=float(rec_a.get("hq_country") == rec_b.get("hq_country")),
            same_region=float(self._same_region(rec_a, rec_b)),
            geo_preference_overlap=self._jaccard(
                rec_a.get("geographic_preferences", []),
                rec_b.get("geographic_preferences", [])
            ),

            # Track record features
            vintage_year_diff=self._vintage_diff(rec_a, rec_b),
            fund_number_diff=self._fund_number_diff(rec_a, rec_b),
            both_emerging=float(
                rec_a.get("emerging_manager_ok") and rec_b.get("emerging_manager_ok")
            ),

            # Name pattern features
            has_fund_number_a=float(self._has_fund_number(rec_a.get("name", ""))),
            has_fund_number_b=float(self._has_fund_number(rec_b.get("name", ""))),
            fund_number_match=self._fund_number_match(rec_a, rec_b),
            has_geography_a=float(self._has_geography(rec_a.get("name", ""))),
            has_geography_b=float(self._has_geography(rec_b.get("name", ""))),
            geography_match=self._geography_match(rec_a, rec_b),

            # Legal entity features
            same_legal_suffix=self._same_legal_suffix(rec_a, rec_b),
            name_without_suffix_sim=self._name_without_suffix_sim(rec_a, rec_b),
        )

    def _has_fund_number(self, name: str) -> bool:
        import re
        return bool(re.search(self.FUND_NUMBER_PATTERN, name, re.IGNORECASE))

    def _fund_number_match(self, a: dict, b: dict) -> float:
        import re
        name_a = a.get("name", "")
        name_b = b.get("name", "")

        nums_a = re.findall(self.FUND_NUMBER_PATTERN, name_a, re.IGNORECASE)
        nums_b = re.findall(self.FUND_NUMBER_PATTERN, name_b, re.IGNORECASE)

        if not nums_a or not nums_b:
            return 0.5  # Neutral if no fund numbers

        return float(set(nums_a) == set(nums_b))

    def _aum_log_diff(self, a: dict, b: dict) -> float:
        aum_a = a.get("total_aum_bn") or a.get("target_size_mm", 0) / 1000
        aum_b = b.get("total_aum_bn") or b.get("target_size_mm", 0) / 1000

        if not aum_a or not aum_b:
            return 0.5  # Neutral if missing

        import math
        log_diff = abs(math.log10(max(aum_a, 0.001)) - math.log10(max(aum_b, 0.001)))
        # Normalize: 0 diff = 1.0, 3 orders of magnitude = 0.0
        return max(0.0, 1.0 - log_diff / 3.0)

    def _check_size_overlap(self, a: dict, b: dict) -> float:
        min_a = a.get("check_size_min_mm", 0)
        max_a = a.get("check_size_max_mm", float("inf"))
        min_b = b.get("check_size_min_mm", 0)
        max_b = b.get("check_size_max_mm", float("inf"))

        # Check for overlap
        overlap_start = max(min_a, min_b)
        overlap_end = min(max_a, max_b)

        if overlap_start <= overlap_end:
            # Calculate overlap ratio
            overlap = overlap_end - overlap_start
            range_a = max_a - min_a if max_a != float("inf") else 1000
            range_b = max_b - min_b if max_b != float("inf") else 1000
            avg_range = (range_a + range_b) / 2
            return min(1.0, overlap / avg_range) if avg_range > 0 else 1.0
        return 0.0

    # ... more helper methods
```

---

### Refinement: LLM Strategy (Self-Consistency + Fine-Tuning)

Your preference for both self-consistency (#3) AND fine-tuned classifier (#4) suggests a **two-stage LLM approach**:

```
                 Uncertain Pairs
                       │
                       ▼
        ┌──────────────────────────┐
        │   STAGE A: Fine-tuned    │
        │   Small Model Classifier │
        │   (Cheap, fast, ~80%)    │
        └────────────┬─────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
        ▼            ▼            ▼
    MATCH      UNCERTAIN     NON-MATCH
    (high)     (medium)      (low)
                  │
                  ▼
        ┌──────────────────────────┐
        │  STAGE B: Self-Consistency│
        │  Full Claude Sonnet       │
        │  (3x samples, majority)   │
        └────────────┬─────────────┘
                     │
                     ▼
               Final Decision
```

**Stage A: Fine-tuned Small Model**
```python
# Fine-tune a smaller model (e.g., Mistral-7B or Llama-3-8B) on domain data
# This handles ~70% of uncertain pairs cheaply

class FineTunedERClassifier:
    """Fast, cheap classifier for initial LLM filtering."""

    def __init__(self, model_path: str):
        # Load fine-tuned model (could be via OpenRouter or local)
        self.model = load_model(model_path)

    async def classify(self, pair_context: str) -> tuple[str, float]:
        """Quick classification with confidence."""
        response = await self.model.generate(
            prompt=f"Classify as MATCH or NON_MATCH:\n{pair_context}",
            max_tokens=10,
            temperature=0.0
        )
        # Parse response and confidence
        return parse_classification(response)
```

**Stage B: Self-Consistency with Full Model**
```python
class SelfConsistencyClassifier:
    """High-quality classification for difficult cases."""

    def __init__(self, api_key: str, n_samples: int = 3):
        self.client = OpenRouterClient(api_key)
        self.n_samples = n_samples
        self.model = "anthropic/claude-sonnet-4-20250514"

    async def classify(
        self,
        record_a: dict,
        record_b: dict,
        features: dict
    ) -> dict:
        """Self-consistency via multiple samples + majority vote."""

        prompt = self._build_prompt(record_a, record_b, features)
        samples = []

        # Generate n samples with temperature > 0
        for _ in range(self.n_samples):
            response = await self.client.generate(
                model=self.model,
                messages=[
                    {"role": "system", "content": SYSTEM_PROMPT},
                    {"role": "user", "content": prompt},
                ],
                temperature=0.7,  # Higher temp for diversity
                max_tokens=500,
            )
            samples.append(self._parse_response(response))

        # Majority vote
        decisions = [s["decision"] for s in samples]
        majority_decision = max(set(decisions), key=decisions.count)
        agreement = decisions.count(majority_decision) / len(decisions)

        # Aggregate reasoning
        return {
            "decision": majority_decision,
            "confidence": agreement,
            "samples": samples,
            "reasoning": self._aggregate_reasoning(samples),
            "needs_human": agreement < 0.67,  # No 2/3 majority
        }
```

**Cost Analysis:**
- Fine-tuned small model: ~$0.0001/pair
- Self-consistency (3x Claude Sonnet): ~$0.01/pair
- With routing: Fine-tuned handles 70%, Sonnet handles 30%
- Average cost: 0.7 × $0.0001 + 0.3 × $0.01 = **~$0.003/pair**

### Recommended Libraries

```
# Core
scikit-learn       # Ensemble classifiers (LogReg, GBM, RF, SVM)
rapidfuzz          # String similarity (Levenshtein, token_sort, etc.)
metaphone          # Phonetic matching
networkx           # Graph clustering

# Optional
recordlinkage      # Additional comparison methods, academic toolkit
entity-embed       # If you want deep learning blocking later

# Already in stack
pgvector           # ANN for embedding similarity (via Supabase)
voyage-ai          # Embeddings (already using for semantic search)
openrouter         # LLM API (already using for pitch generation)
```

---

### Data Integration Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     SOURCE SYSTEMS                              │
├──────────┬──────────┬──────────┬──────────┬──────────┬─────────┤
│Salesforce│ HubSpot  │  Excel   │ LinkedIn │Eventbrite│PitchBook│
└────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬─────┴────┬────┘
     │          │          │          │          │          │
     └──────────┴──────────┴────┬─────┴──────────┴──────────┘
                                │
                    ┌───────────▼───────────┐
                    │   STAGING LAYER       │
                    │  (Raw imports with    │
                    │   source metadata)    │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  SPLINK ENTITY        │
                    │  RESOLUTION           │
                    │  ─────────────────    │
                    │  • Match records      │
                    │  • Assign confidence  │
                    │  • Flag for review    │
                    └───────────┬───────────┘
                                │
                    ┌───────────▼───────────┐
                    │  GOLDEN RECORD        │
                    │  CREATION             │
                    │  ─────────────────    │
                    │  • Merge attributes   │
                    │  • Source priority    │
                    │  • Conflict detection │
                    └───────────┬───────────┘
                                │
               ┌────────────────┼────────────────┐
               │                │                │
     ┌─────────▼─────────┐ ┌────▼────┐ ┌────────▼────────┐
     │  MASTER DATA      │ │ REVIEW  │ │ AUDIT TRAIL     │
     │  (Single source   │ │ QUEUE   │ │ (All changes    │
     │   of truth)       │ │(Low conf│ │  with sources)  │
     └───────────────────┘ │matches) │ └─────────────────┘
                           └─────────┘
```

---

### Source Priority Rules

When merging conflicting data from multiple sources:

| Field | Priority Order |
|-------|----------------|
| **Email** | User entry > LinkedIn > CRM > Import |
| **Phone** | User entry > CRM > LinkedIn |
| **Title** | LinkedIn > CRM > User entry |
| **Company** | LinkedIn > CRM > User entry |
| **AUM/Size** | PitchBook > Preqin > Manual > Estimate |
| **Strategy** | User entry > PitchBook > Preqin |
| **Address** | CRM > LinkedIn > User entry |

---

### Database Tables for MDM

```sql
-- Staging table for raw imports
CREATE TABLE data_imports (
    id UUID PRIMARY KEY,
    source TEXT NOT NULL,  -- 'salesforce', 'excel', 'linkedin', etc.
    entity_type TEXT NOT NULL,  -- 'organization', 'person', etc.
    raw_data JSONB NOT NULL,
    normalized_data JSONB,
    import_batch_id UUID,
    imported_at TIMESTAMPTZ DEFAULT NOW(),
    processed BOOLEAN DEFAULT FALSE
);

-- Entity resolution results
CREATE TABLE entity_matches (
    id UUID PRIMARY KEY,
    import_record_id UUID REFERENCES data_imports(id),
    matched_entity_id UUID,  -- FK to organizations/people
    match_confidence DECIMAL(5,4),  -- 0.0000 to 1.0000
    match_reasons JSONB,  -- {"email": 0.99, "name": 0.85, ...}
    status TEXT DEFAULT 'pending',  -- pending, approved, rejected
    reviewed_by UUID,
    reviewed_at TIMESTAMPTZ
);

-- Source provenance for each field
CREATE TABLE field_provenance (
    id UUID PRIMARY KEY,
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    field_name TEXT NOT NULL,
    current_value TEXT,
    source TEXT NOT NULL,
    confidence DECIMAL(3,2),
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    superseded_by UUID  -- FK to newer provenance record
);

-- Review queue for IR team
CREATE TABLE data_review_queue (
    id UUID PRIMARY KEY,
    entity_match_id UUID REFERENCES entity_matches(id),
    priority INT DEFAULT 50,  -- 1-100, higher = more urgent
    review_type TEXT,  -- 'duplicate', 'conflict', 'low_quality'
    context JSONB,  -- Side-by-side comparison data
    assigned_to UUID,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    resolved_at TIMESTAMPTZ
);
```

---

## Summary: Implementation Phases

### Phase 1: Color Fix (Immediate)
- Replace `accent` (teal) with `gold` across all mockups
- Files: 30+ HTML files in `docs/mockups/`
- Estimated changes: ~100 replacements

### Phase 2: Data Model Extension
- Add Events, Attendance, Touchpoints, Tasks, IR Notes tables
- Extend People table with IR-specific fields
- Create MDM staging and provenance tables

### Phase 3: Data Integration Pipeline
- Implement Splink-based entity resolution
- Build import adapters (CSV, Salesforce, HubSpot, Excel)
- Create IR review queue UI for low-confidence matches

### Phase 4: IR User Experience
- Quick profile lookup (mobile-first)
- Meeting prep cards with talking points
- Event briefing books
- Post-meeting note capture

---

## Sources

- [Splink - Probabilistic Record Linkage](https://moj-analytical-services.github.io/splink/)
- [Dedupe - ML-based Entity Resolution](https://github.com/dedupeio/dedupe)
- [Entity Resolution Overview](https://spotintelligence.com/2024/01/22/entity-resolution/)
- [Entity Resolution with Census](https://www.getcensus.com/research-blog-listing/entity-resolution-in-python-with-the-dedupe-package)

---

*Plan last updated: Ready for review*
