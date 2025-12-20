# Screen Inventory

Complete UI screen definitions for LPxGP platform.

---

## Screen Categories

| Category | Count | Description |
|----------|-------|-------------|
| Public | 4 | Unauthenticated pages (login, invites, password reset) |
| GP User | 14 | Main application screens for GP users |
| Super Admin | 10 | Platform administration screens |

**Total: 28 screens**

---

## Public Screens (Unauthenticated)

### Login
**Route:** `/login`

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│                    LPxGP                            │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ Email                                         │  │
│  │ [_______________________________________]     │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ Password                                      │  │
│  │ [_______________________________________]     │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  [          Sign In          ]                      │
│                                                     │
│  Forgot password?                                   │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Notes:**
- NO "Sign Up" or "Get Started" button (invite-only platform)
- "Forgot password?" links to password reset flow
- Error states: Invalid credentials, Account locked, Account deactivated

---

### Accept Invitation
**Route:** `/invite/[token]`

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│           Welcome to LPxGP                          │
│                                                     │
│  You've been invited to join:                       │
│  ┌───────────────────────────────────────────────┐  │
│  │  Acme Capital                                 │  │
│  │  Role: Admin                                  │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  Email: partner@acme.com (cannot change)            │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ Full Name                                     │  │
│  │ [_______________________________________]     │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ Create Password                               │  │
│  │ [_______________________________________]     │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ Confirm Password                              │  │
│  │ [_______________________________________]     │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  [       Complete Setup       ]                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

**Notes:**
- Shows company name and role from invitation
- Email is pre-filled and read-only
- Password requirements shown inline
- Error states: Invalid token, Expired token, Already accepted

---

### Forgot Password
**Route:** `/forgot-password`

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│              Reset Password                         │
│                                                     │
│  Enter your email to receive a reset link.          │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ Email                                         │  │
│  │ [_______________________________________]     │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  [       Send Reset Link       ]                    │
│                                                     │
│  Back to login                                      │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

### Reset Password
**Route:** `/reset-password/[token]`

```
┌─────────────────────────────────────────────────────┐
│                                                     │
│            Create New Password                      │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ New Password                                  │  │
│  │ [_______________________________________]     │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  ┌───────────────────────────────────────────────┐  │
│  │ Confirm Password                              │  │
│  │ [_______________________________________]     │  │
│  └───────────────────────────────────────────────┘  │
│                                                     │
│  [       Reset Password       ]                     │
│                                                     │
└─────────────────────────────────────────────────────┘
```

---

## GP User Screens

### Dashboard (First-time vs Returning)

#### First-time Welcome
**Route:** `/dashboard` (shown when `first_login_at` is NULL)

```
┌─────────────────────────────────────────────────────────────────┐
│  LPxGP                                           [Settings]     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│         Welcome to LPxGP, John!                                 │
│                                                                 │
│         You're the admin of Acme Capital.                       │
│                                                                 │
│         What would you like to do first?                        │
│                                                                 │
│  ┌────────────────────────┐    ┌────────────────────────┐       │
│  │                        │    │                        │       │
│  │  Create Your           │    │  Invite Team           │       │
│  │  First Fund            │    │  Members               │       │
│  │                        │    │                        │       │
│  │  Upload your pitch     │    │  Add colleagues to     │       │
│  │  deck and let AI       │    │  help with research    │       │
│  │  extract details       │    │  and outreach          │       │
│  │                        │    │                        │       │
│  │  [Get Started ->]      │    │  [Invite ->]           │       │
│  │                        │    │                        │       │
│  └────────────────────────┘    └────────────────────────┘       │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  Quick tip: Start by creating your fund profile.               │
│  Our AI will help extract details from your pitch deck.        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

**Notes:**
- Only shown to Company Admins on first login
- Team Members see regular dashboard (not welcome screen)
- Sets `first_login_at` after first navigation away

---

#### Returning User Dashboard
**Route:** `/dashboard`

```
┌─────────────────────────────────────────────────────────────────┐
│  Acme Capital                                    [Settings]     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  YOUR FUNDS                                                     │
│  ┌──────────────────────┐  ┌──────────────────────┐            │
│  │ Growth Fund III      │  │ Growth Fund II       │  [+ New]   │
│  │                      │  │                      │            │
│  │ Raising - $500M      │  │ Investing - $350M    │            │
│  │ ─────────────────    │  │ ─────────────────    │            │
│  │ 45 matches           │  │ Closed               │            │
│  │ 12 contacted         │  │                      │            │
│  │ 3 meetings           │  │                      │            │
│  │                      │  │                      │            │
│  │ [View Matches ->]    │  │ [View Details ->]    │            │
│  └──────────────────────┘  └──────────────────────┘            │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  RECENT ACTIVITY                                                │
│  - You generated pitch for CalPERS - 2 hours ago               │
│  - Jane added Harvard Endowment to shortlist - yesterday       │
│  - Match score updated for 12 LPs - 2 days ago                 │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  QUICK ACTIONS                                                  │
│  [Search LPs]   [View All Matches]   [Outreach Hub]            │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Fund List
**Route:** `/funds`

```
┌─────────────────────────────────────────────────────────────────┐
│  Funds                                           [+ New Fund]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────┬────────────┬──────────┬─────────┬─────────┐        │
│  │ Name   │ Status     │ Size     │ Matches │ Actions │        │
│  ├────────┼────────────┼──────────┼─────────┼─────────┤        │
│  │ Fund 3 │ Raising    │ $500M    │ 45      │ [...]   │        │
│  │ Fund 2 │ Investing  │ $350M    │ -       │ [...]   │        │
│  │ Fund 1 │ Harvesting │ $200M    │ -       │ [...]   │        │
│  └────────┴────────────┴──────────┴─────────┴─────────┘        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Fund Detail
**Route:** `/funds/[id]`

```
┌─────────────────────────────────────────────────────────────────┐
│  <- Funds    Growth Fund III                     [Edit] [...]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  OVERVIEW                          STATS                        │
│  ┌─────────────────────┐          ┌─────────────────────┐      │
│  │ Status: Raising     │          │ Matches: 45         │      │
│  │ Target: $500M       │          │ Shortlisted: 12     │      │
│  │ Vintage: 2024       │          │ Contacted: 8        │      │
│  │ Strategy: PE Growth │          │ Meetings: 3         │      │
│  └─────────────────────┘          └─────────────────────┘      │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  [View Matches]   [Generate Matches]   [View Shortlist]         │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  INVESTMENT THESIS                                              │
│  "We invest in growth-stage technology companies..."            │
│                                                                 │
│  TEAM (from fund_team)                                          │
│  - John Smith, Managing Partner (Key Person)                    │
│  - Jane Doe, Partner (Key Person)                               │
│  - Bob Wilson, Principal                                        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Fund Create/Edit
**Route:** `/funds/new` or `/funds/[id]/edit`

```
┌─────────────────────────────────────────────────────────────────┐
│  <- Cancel                              [Save Draft] [Publish]  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌─────────────────────────────────────────────────────────┐   │
│  │ Upload Pitch Deck                                       │   │
│  │ ─────────────────                                       │   │
│  │ [Drop PDF/PPTX here or click to browse]                 │   │
│  │                                                         │   │
│  │ AI will extract fund details automatically              │   │
│  └─────────────────────────────────────────────────────────┘   │
│                                                                 │
│  Or fill in manually:                                           │
│                                                                 │
│  BASIC INFORMATION                                              │
│  Fund Name: [____________________]                              │
│  Fund Number: [___]  Vintage: [____]                           │
│  Target Size: [$________]  Hard Cap: [$________]               │
│                                                                 │
│  STRATEGY                                                       │
│  Strategy: [Private Equity v]                                   │
│  Sub-strategy: [Growth v]                                       │
│  Geography: [x] North America [x] Europe [ ] Asia              │
│  Sectors: [x] Technology [x] Healthcare [ ] Consumer           │
│                                                                 │
│  TEAM                                                           │
│  [+ Add Team Member]                                            │
│  - John Smith, Managing Partner [Key Person] [Remove]           │
│  - Jane Doe, Partner [Key Person] [Remove]                      │
│                                                                 │
│  INVESTMENT THESIS                                              │
│  [                                                     ]        │
│  [                                                     ]        │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### LP Search
**Route:** `/search`

```
┌─────────────────────────────────────────────────────────────────┐
│  Search LPs                                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  [Search by name, mandate, or keyword...____________] [Search]  │
│                                                                 │
│  FILTERS                                                        │
│  Type: [x] Pension [ ] Endowment [ ] Foundation [x] Family     │
│  AUM: [$___] to [$___]                                         │
│  Geography: [Select regions...]                                 │
│  Strategies: [Select strategies...]                             │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  RESULTS (247 LPs)                          [Sort: AUM desc v]  │
│  ┌────────────────┬──────────────┬─────────┬─────────────────┐ │
│  │ Name           │ Type         │ AUM     │ Actions         │ │
│  ├────────────────┼──────────────┼─────────┼─────────────────┤ │
│  │ CalPERS        │ Pension      │ $450B   │ [View] [+List]  │ │
│  │ Yale Endowment │ Endowment    │ $41B    │ [View] [+List]  │ │
│  │ Ford Found.    │ Foundation   │ $16B    │ [View] [+List]  │ │
│  └────────────────┴──────────────┴─────────┴─────────────────┘ │
│                                                                 │
│  [< Prev]  Page 1 of 25  [Next >]                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### LP Detail
**Route:** `/lps/[id]`

```
┌─────────────────────────────────────────────────────────────────┐
│  <- Search    CalPERS                   [+ Add to Shortlist]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  OVERVIEW                                                       │
│  Type: Public Pension          AUM: $450B                       │
│  Location: Sacramento, CA      Website: calpers.ca.gov          │
│                                                                 │
│  INVESTMENT PREFERENCES                                         │
│  Strategies: PE, VC, Real Estate, Infrastructure               │
│  Check Size: $50M - $500M                                       │
│  Geography: Global                                              │
│                                                                 │
│  MANDATE                                                        │
│  "CalPERS invests in private equity to generate..."            │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  KEY CONTACTS (from people + employment)                        │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ John Smith - CIO (Decision Maker)                          ││
│  │ john.smith@calpers.ca.gov                                  ││
│  │ At CalPERS since 2018                                      ││
│  ├────────────────────────────────────────────────────────────┤│
│  │ Jane Doe - Director, Private Equity (Decision Maker)       ││
│  │ jane.doe@calpers.ca.gov                                    ││
│  │ At CalPERS since 2020 (prev: Stanford Endowment)           ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  [Flag as Outdated]  [Suggest Correction]                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Matches
**Route:** `/funds/[id]/matches`

```
┌─────────────────────────────────────────────────────────────────┐
│  <- Fund    Matches for Growth Fund III    [Refresh Matches]   │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  45 matches found                          [Sort: Score desc v] │
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ [1] CalPERS                                     Score: 92  ││
│  │     Pension | $450B | California                           ││
│  │     Key: Strategy match, ESG alignment, size fit           ││
│  │     [View Details]  [+ Shortlist]  [Why this match?]       ││
│  ├────────────────────────────────────────────────────────────┤│
│  │ [2] Yale Endowment                              Score: 88  ││
│  │     Endowment | $41B | Connecticut                         ││
│  │     Key: Strong PE allocation, thesis alignment            ││
│  │     [View Details]  [+ Shortlist]  [Why this match?]       ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  [Bulk Actions: Add Selected to Shortlist]                      │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Match Detail
**Route:** `/funds/[id]/matches/[lp_id]`

Shows full LP profile plus:
- Score breakdown (all factors)
- AI-generated explanation
- Talking points
- Potential concerns
- [Add to Shortlist] / [Generate Pitch]

---

### Pitch Generator
**Route:** `/funds/[id]/pitch/[lp_id]`

```
┌─────────────────────────────────────────────────────────────────┐
│  Generate Pitch for CalPERS                                     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  OUTPUT TYPE                                                    │
│  (x) Executive Summary    ( ) Outreach Email    ( ) Both       │
│                                                                 │
│  TONE                                                           │
│  ( ) Formal    (x) Professional    ( ) Casual                  │
│                                                                 │
│  EMPHASIS (select up to 3)                                      │
│  [x] Track Record  [x] ESG  [ ] Team  [ ] Sector Expertise     │
│                                                                 │
│  [Generate]                                                     │
│                                                                 │
│  ─────────────────────────────────────────────────────────────  │
│                                                                 │
│  GENERATED CONTENT                                              │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ Executive Summary for CalPERS                              ││
│  │                                                            ││
│  │ Growth Fund III represents an opportunity to...            ││
│  │ [AI-generated content here]                                ││
│  │                                                            ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
│  [Copy to Clipboard]  [Regenerate]  [Edit & Save]              │
│                                                                 │
│  Human review required before use.                              │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Shortlist
**Route:** `/funds/[id]/shortlist`

```
┌─────────────────────────────────────────────────────────────────┐
│  Shortlist for Growth Fund III                                  │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  12 LPs shortlisted                                             │
│                                                                 │
│  ┌────────────────┬──────────┬─────────┬─────────────────────┐ │
│  │ Name           │ Score    │ Status  │ Actions             │ │
│  ├────────────────┼──────────┼─────────┼─────────────────────┤ │
│  │ CalPERS        │ 92       │ New     │ [Pitch] [Contact]   │ │
│  │ Yale Endowment │ 88       │ Contact │ [Pitch] [Contact]   │ │
│  │ Harvard Mgmt   │ 85       │ Meeting │ [Pitch] [Notes]     │ │
│  └────────────────┴──────────┴─────────┴─────────────────────┘ │
│                                                                 │
│  [Export CSV]  [Bulk Generate Pitches]                          │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Outreach Hub
**Route:** `/outreach`

Tracks LP engagement status across all funds:
- Columns: LP, Fund, Status, Last Contact, Next Step
- Status flow: New -> Contacted -> Responded -> Meeting -> Committed/Declined
- Notes and activity log per LP

---

### Settings - Profile
**Route:** `/settings/profile`

User's own profile:
- Name, email (read-only)
- Password change
- Notification preferences

---

### Settings - Team (Admin only)
**Route:** `/settings/team`

```
┌─────────────────────────────────────────────────────────────────┐
│  Team Members                                    [+ Invite]     │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  ┌────────────────────────────────────────────────────────────┐│
│  │ John Partner (you)                                         ││
│  │ partner@acme.com - Admin - Active                          ││
│  ├────────────────────────────────────────────────────────────┤│
│  │ Jane Associate                                             ││
│  │ jane@acme.com - Member - Active                            ││
│  │ [Change Role]  [Deactivate]                                ││
│  ├────────────────────────────────────────────────────────────┤│
│  │ Bob Analyst                                                ││
│  │ bob@acme.com - Member - Pending invite                     ││
│  │ [Resend]  [Cancel]                                         ││
│  └────────────────────────────────────────────────────────────┘│
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Settings - Company (Admin only)
**Route:** `/settings/company`

Company settings:
- Company name
- Billing contact (future)
- Data export request

---

## Super Admin Screens

### Admin Dashboard
**Route:** `/admin`

```
┌─────────────────────────────────────────────────────────────────┐
│  Admin Dashboard                                                │
├─────────────────────────────────────────────────────────────────┤
│                                                                 │
│  PLATFORM OVERVIEW                                              │
│  ┌──────────────┐ ┌──────────────┐ ┌──────────────┐            │
│  │ Companies    │ │ Users        │ │ LPs          │            │
│  │     25       │ │    150       │ │   5,000      │            │
│  │ +3 this week │ │ +12 this wk  │ │ +50 this wk  │            │
│  └──────────────┘ └──────────────┘ └──────────────┘            │
│                                                                 │
│  PENDING ACTIONS                                                │
│  - 3 companies awaiting admin acceptance                        │
│  - 12 LPs flagged for review                                    │
│  - 1 import job in progress                                     │
│                                                                 │
│  SYSTEM HEALTH                                                  │
│  Database: Healthy | Auth: Healthy | OpenRouter: Healthy       │
│                                                                 │
│  RECENT ACTIVITY                                                │
│  - New company created: Beta Ventures - 2 hours ago            │
│  - Import completed: 500 LPs - yesterday                       │
│                                                                 │
└─────────────────────────────────────────────────────────────────┘
```

---

### Admin - Companies
**Route:** `/admin/companies`

List of all companies with:
- Name, Status (Pending/Active/Deactivated)
- User count, Fund count
- Created date
- Actions: View, Edit, Deactivate

[+ Add Company] button opens company creation modal.

---

### Admin - Company Detail
**Route:** `/admin/companies/[id]`

Single company view with:
- Company info (name, status, created)
- User list (with invite/deactivate actions)
- Fund list
- Activity log
- Settings (plan, limits)

---

### Admin - Users
**Route:** `/admin/users`

All users across all companies:
- Name, Email, Company, Role, Status, Last Login
- Filter by company, role, status
- Search by name/email

---

### Admin - People (Global Contact Database)
**Route:** `/admin/people`

All people in the platform (LP contacts + GP team members):
- Name, Email, Current Org, Title
- Filter by org type (LP/GP), verification status
- Search by name/email
- [+ Add Person] [Merge Duplicates]

---

### Admin - LPs
**Route:** `/admin/lps`

LP organizations:
- Name, Type, AUM, Quality Score, Contact Count
- Filter by type, quality
- Search
- [+ Add LP] [Import]

---

### Admin - LP Detail/Edit
**Route:** `/admin/lps/[id]`

Full LP editor with all fields editable.
Shows linked people with their employment records.

---

### Admin - Data Quality
**Route:** `/admin/data-quality`

- Quality score distribution
- LPs needing review (flagged by users)
- Unverified LPs
- Duplicate candidates
- Review queue with approve/reject actions

---

### Admin - Import Wizard
**Route:** `/admin/import`

Step-by-step import:
1. Upload CSV/Excel
2. Map columns to fields
3. Preview data
4. Validate (show errors/warnings)
5. Approve and import

---

### Admin - System Health
**Route:** `/admin/health`

Service status dashboard:
- Database connection
- Supabase Auth
- OpenRouter API
- Voyage AI
- Error rates (from Sentry)
- Response times

---

## Navigation Structure

```
GP User:
├── Dashboard
├── Funds
│   ├── Fund List
│   ├── Fund Detail
│   ├── Fund Create/Edit
│   ├── Matches
│   ├── Match Detail
│   └── Shortlist
├── Search (LPs)
│   └── LP Detail
├── Outreach Hub
└── Settings
    ├── Profile
    ├── Team (Admin only)
    └── Company (Admin only)

Super Admin:
├── Admin Dashboard
├── Companies
│   └── Company Detail
├── Users
├── People
├── LPs
│   └── LP Detail/Edit
├── Data Quality
├── Import
└── System Health
```

---

## Responsive Considerations

- All screens must work on desktop (1280px+)
- Dashboard and search should work on tablet (768px+)
- Login/invite screens should work on mobile
- Data tables should use horizontal scroll on smaller screens
