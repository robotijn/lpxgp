# UX Storylines

This document describes the user experience flows through the LPxGP platform, connecting screens with user goals and tested behaviors.

---

## Journey 1: Platform Onboarding (Super Admin)

**Actor:** Sarah, LPxGP Super Admin
**Goal:** Onboard a new GP firm to the platform

### Flow

```
admin-dashboard.html → admin-companies.html → [Create Company Form] → admin-company-detail.html → [Invite Admin]
```

### Story

Sarah receives a request from Acme Capital to join LPxGP. She:

1. **Admin Dashboard** - Reviews platform health and sees the "Add Company" action
2. **Companies List** - Clicks "Add Company" to create Acme Capital
3. **Company Detail** - Configures company settings and invites John (Partner) as company admin
4. **Verification** - John receives invitation email

### Tested Behaviors (BDD References)

| Screen | Positive Tests | Negative Tests |
|--------|---------------|----------------|
| admin-companies | F-AUTH-04: Company creation, listing, filtering | Duplicate company name rejected |
| admin-company-detail | F-AUTH-04: User invitation, role assignment | Invalid email format rejected |

---

## Journey 2: New User Onboarding (GP Admin)

**Actor:** John, Partner at Acme Capital
**Goal:** Accept invitation and set up account

### Flow

```
[Email] → accept-invitation.html → [Set Password] → login.html → dashboard.html
```

### Story

John receives an invitation email from LPxGP. He:

1. **Accept Invitation** - Clicks link in email, sees pre-filled email
2. **Set Password** - Creates secure password meeting requirements
3. **Login** - Signs in with new credentials
4. **Dashboard** - Lands on empty dashboard, ready to create first fund

### Tested Behaviors (BDD References)

| Screen | Positive Tests | Negative Tests |
|--------|---------------|----------------|
| accept-invitation | F-AUTH-05: Invitation acceptance, password creation | Expired invitation rejected, weak password rejected |
| login | F-AUTH-01: Successful login, session creation | Invalid credentials rejected, account lockout after 5 failures |
| dashboard | F-UI-01: First-time user experience | N/A |

---

## Journey 3: Fund Creation (GP Admin)

**Actor:** John, Partner at Acme Capital
**Goal:** Create fund profile for Growth Fund III

### Flow

```
dashboard.html → fund-create.html → [Upload Deck] → [AI Extraction] → fund-detail.html
```

### Story

John wants to create a profile for his new fund. He:

1. **Dashboard** - Clicks "+ New Fund" button
2. **Fund Create** - Uploads pitch deck PDF
3. **AI Extraction** - Reviews AI-extracted information (strategy, size, thesis)
4. **Confirmation** - Confirms or edits each field, especially low-confidence items
5. **Fund Detail** - Views completed fund profile

### Tested Behaviors (BDD References)

| Screen | Positive Tests | Negative Tests |
|--------|---------------|----------------|
| fund-create | F-GP-01: Basic info, strategy, parameters | Missing required fields blocked |
| fund-create | F-GP-02: Deck upload (PDF, PPTX) | Corrupt file rejected, oversized file rejected |
| fund-create | F-GP-03: AI extraction with confidence scores | API timeout graceful handling |
| fund-detail | F-GP-04: Profile editing, version history | Concurrent edit conflict detection |

---

## Journey 4: LP Research (GP User)

**Actor:** Maria, Associate at Acme Capital
**Goal:** Find LPs that match Growth Fund III criteria

### Flow

```
dashboard.html → lp-search.html → [Apply Filters] → lp-detail.html → [Add to Shortlist]
```

### Story

Maria needs to research potential LP targets. She:

1. **Dashboard** - Navigates to Search
2. **LP Search** - Applies filters: Strategy = "Growth Equity", Check Size > $10M, Geography = "North America"
3. **Results** - Reviews 45 matching LPs with relevance scores
4. **LP Detail** - Clicks on CalPERS to view full profile, mandate, and contacts
5. **Shortlist** - Adds CalPERS to shortlist for Growth Fund III

### Tested Behaviors (BDD References)

| Screen | Positive Tests | Negative Tests |
|--------|---------------|----------------|
| lp-search | F-LP-02: Type, strategy, geography, check size filters | No results handling |
| lp-search | F-LP-03: Semantic search with natural language | Empty query handling, special characters |
| lp-search | F-UI-03: HTMX updates, pagination, sorting | Performance < 500ms |
| lp-detail | F-LP-01: Full LP profile with contacts | Missing data graceful display |

---

## Journey 5: AI Matching (GP User)

**Actor:** Maria, Associate at Acme Capital
**Goal:** Get AI-ranked LP matches for Growth Fund III

### Flow

```
fund-detail.html → matches.html → match-detail.html → [Review Insights]
```

### Story

Maria wants to see AI-recommended matches. She:

1. **Fund Detail** - Clicks "View Matches" for Growth Fund III
2. **Matches** - Sees 45 LPs ranked by fit score (0-100)
3. **Match Detail** - Clicks on CalPERS (score: 87) to see breakdown
4. **Insights** - Reviews AI-generated talking points and potential concerns

### Tested Behaviors (BDD References)

| Screen | Positive Tests | Negative Tests |
|--------|---------------|----------------|
| matches | F-MATCH-01: Hard filter matching (strategy, geography, size) | No matches handling |
| matches | F-MATCH-02: Soft scoring with breakdown | Minimum threshold filtering |
| matches | F-UI-04: Visual score bars, color coding | Loading states |
| match-detail | F-MATCH-03: Semantic similarity calculation | Missing mandate handling |
| match-detail | F-MATCH-04: AI explanations, talking points | API timeout fallback |

---

## Journey 6: Pitch Generation (GP User)

**Actor:** Maria, Associate at Acme Capital
**Goal:** Create personalized outreach for CalPERS

### Flow

```
match-detail.html → pitch-generator.html → [Generate] → [Review & Edit] → [Copy to Clipboard]
```

### Story

Maria wants to draft outreach for CalPERS. She:

1. **Match Detail** - Clicks "Generate Pitch"
2. **Pitch Generator** - Selects output type: "Outreach Email"
3. **Generation** - AI generates personalized email referencing CalPERS's recent allocations
4. **Review** - Edits subject line and call-to-action
5. **Copy** - Copies to clipboard for use in email client

### Tested Behaviors (BDD References)

| Screen | Positive Tests | Negative Tests |
|--------|---------------|----------------|
| pitch-generator | F-PITCH-01: Executive summary generation | API rate limiting handled |
| pitch-generator | F-PITCH-02: Email draft with tone options | Missing LP data degradation |
| pitch-generator | F-HITL-01: No auto-send, review required | Clipboard permission issues |

---

## Journey 7: Outreach Management (GP User)

**Actor:** John, Partner at Acme Capital
**Goal:** Track LP outreach progress

### Flow

```
dashboard.html → shortlist.html → outreach-hub.html → [Update Status]
```

### Story

John wants to review and track outreach. He:

1. **Dashboard** - Sees 34 LPs in shortlist, 8 meetings scheduled
2. **Shortlist** - Reviews LPs ready for outreach
3. **Outreach Hub** - Updates status for CalPERS: "Email Sent" → "Meeting Scheduled"
4. **Pipeline** - Views funnel analytics

### Tested Behaviors (BDD References)

| Screen | Positive Tests | Negative Tests |
|--------|---------------|----------------|
| shortlist | F-HITL-02: Shortlist management | Empty shortlist handling |
| outreach-hub | Activity tracking, status updates | N/A |

---

## Journey 8: Team Management (GP Admin)

**Actor:** John, Partner at Acme Capital
**Goal:** Invite Maria as team member

### Flow

```
settings-profile.html → settings-team.html → [Invite Member] → [Email Sent]
```

### Story

John wants to add Maria to the team. He:

1. **Settings - Profile** - Navigates to Settings
2. **Settings - Team** - Clicks "Invite Member"
3. **Invite** - Enters Maria's email, assigns "Member" role
4. **Confirmation** - Maria receives invitation email

### Tested Behaviors (BDD References)

| Screen | Positive Tests | Negative Tests |
|--------|---------------|----------------|
| settings-team | F-AUTH-05: Team invitation | Duplicate email rejected |
| settings-team | F-AUTH-03: Role assignment (Admin, Member) | Role escalation prevented |

---

## Journey 9: Data Quality Management (Super Admin)

**Actor:** Sarah, LPxGP Super Admin
**Goal:** Review and fix LP data quality issues

### Flow

```
admin-dashboard.html → admin-data-quality.html → admin-lp-detail.html → [Fix Issue]
```

### Story

Sarah sees data quality alerts. She:

1. **Admin Dashboard** - Sees 23 LPs flagged for review
2. **Data Quality** - Reviews issues: missing strategy, duplicate entries
3. **LP Detail** - Opens flagged LP to correct data
4. **Resolution** - Updates strategy, marks issue resolved

### Tested Behaviors (BDD References)

| Screen | Positive Tests | Negative Tests |
|--------|---------------|----------------|
| admin-data-quality | F-HITL-05: Flag queue, issue categorization | N/A |
| admin-lp-detail | F-LP-05: Data cleaning, normalization | Concurrent edit conflict |

---

## Journey 10: LP Data Import (Super Admin)

**Actor:** Sarah, LPxGP Super Admin
**Goal:** Import new LP data from CSV

### Flow

```
admin-lps.html → admin-import.html → [Upload] → [Map Fields] → [Preview] → [Commit]
```

### Story

Sarah receives new LP data to import. She:

1. **LPs List** - Clicks "Import" button
2. **Import Wizard - Upload** - Uploads CSV file (500 rows)
3. **Import Wizard - Map Fields** - Maps CSV columns to LPxGP fields
4. **Import Wizard - Preview** - Reviews sample rows, sees 2 duplicates detected
5. **Import Wizard - Commit** - Confirms import, 498 new LPs added

### Tested Behaviors (BDD References)

| Screen | Positive Tests | Negative Tests |
|--------|---------------|----------------|
| admin-import | F-LP-04: File upload, field mapping | Invalid file format rejected |
| admin-import | F-LP-04: Duplicate detection, merge options | Malformed CSV handling |
| admin-import | F-HITL-04: Preview, approval, rollback | Large file (10K+ rows) performance |

---

## Screen-to-Test Mapping Summary

| Screen | Primary Feature | Key BDD Scenarios |
|--------|----------------|-------------------|
| login | F-AUTH-01 | Valid login, invalid credentials, lockout |
| accept-invitation | F-AUTH-05 | Accept flow, expired token, weak password |
| forgot-password | F-AUTH-01 | Reset request, invalid email |
| reset-password | F-AUTH-01 | Password update, token expiry |
| dashboard | F-UI-01 | Stats, funds, activity |
| fund-list | F-GP-01 | List, filter, create action |
| fund-detail | F-GP-01, F-GP-04 | View, edit, version history |
| fund-create | F-GP-01, F-GP-02, F-GP-03 | Create, upload, AI extraction |
| lp-search | F-LP-02, F-LP-03, F-UI-03 | Filter, semantic, HTMX |
| lp-detail | F-LP-01 | Full profile, contacts |
| matches | F-MATCH-01, F-MATCH-02, F-UI-04 | Hard/soft scoring, display |
| match-detail | F-MATCH-03, F-MATCH-04 | Semantic, explanations |
| pitch-generator | F-PITCH-01, F-PITCH-02, F-HITL-01 | Summary, email, review |
| shortlist | F-HITL-02 | Selection, management |
| outreach-hub | Activity tracking | Status updates, pipeline |
| settings-profile | User settings | Profile editing |
| settings-team | F-AUTH-03, F-AUTH-05 | Team invite, roles |
| admin-dashboard | F-AUTH-04 | Platform overview |
| admin-companies | F-AUTH-04 | Company management |
| admin-company-detail | F-AUTH-04 | Company config, users |
| admin-users | F-AUTH-04 | User management |
| admin-people | People database | Contact management |
| admin-lps | F-LP-01, F-AUTH-04 | LP database |
| admin-lp-detail | F-LP-01, F-LP-05 | LP editing, quality |
| admin-data-quality | F-HITL-05 | Quality monitoring |
| admin-import | F-LP-04, F-HITL-04 | Import wizard |
| admin-health | Monitoring | System status |
