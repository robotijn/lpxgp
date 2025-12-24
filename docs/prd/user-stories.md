# User Stories

[← Back to Index](index.md)

---

## 10.1 Authentication

> **Note:** LPxGP is invite-only. There is no self-registration.

### US-AUTH-01: Accept Invitation
As an invited user, I want to accept my invitation and set up my account.

**Acceptance Criteria:**
- Invitation link shows company name and my role
- Email field is pre-filled and not editable
- Password must be min 8 chars, 1 uppercase, 1 lowercase, 1 number
- After submission, account is created and I'm logged in
- First-time welcome screen is shown
- Expired invitation shows clear error with "Request new invitation" option

**Test:** TEST-AUTH-01

### US-AUTH-02: User Login
As an existing user, I want to login so I can access my data.

**Acceptance Criteria:**
- Email/password authentication works
- Invalid credentials show generic error (security)
- Successful login redirects to dashboard
- First-time users see welcome screen
- Session persists across browser refresh (7 days)
- No "Register" link on login page (invite-only)

**Test:** TEST-AUTH-02

### US-AUTH-03: Company Isolation
As a user, I should only see data belonging to my company.

**Acceptance Criteria:**
- User cannot see other companies' funds
- User cannot see other companies' matches
- User cannot see other companies' users
- API returns 404 (not 403) for other company data
- User belongs to exactly one company

**Test:** TEST-AUTH-03

### US-AUTH-04: Invite Team Member
As a company admin, I want to invite team members so they can use the platform.

**Acceptance Criteria:**
- Can invite by email address
- Can select role (Member or Admin)
- Invitation email sent within 30 seconds
- Can view pending invitations
- Can resend expired invitations
- Can cancel pending invitations
- Cannot invite email that already has account

**Test:** TEST-AUTH-04

### US-AUTH-05: Super Admin - Create Company
As a super admin, I want to create companies and invite their first admin.

**Acceptance Criteria:**
- Can create company with name
- Can enter admin email and send invitation
- Company appears in admin panel
- First user invited automatically gets Admin role
- Can view all companies and their status

**Test:** TEST-AUTH-05

### US-AUTH-06: Impersonate User
As a Super Admin, I want to view the platform as any user so I can provide support and verify their experience.

**Acceptance Criteria:**
- Impersonate button on admin users list triggers view-as mode
- Clear visual banner shows impersonation is active: "[Admin] viewing as [User]"
- I see exactly what the target user sees
- Write operations are blocked unless explicitly enabled (Super Admin only)
- End Session returns me to admin view
- All my actions during impersonation are logged

**Test:** TEST-AUTH-06

### US-AUTH-07: Manage User Roles
As a Super Admin, I want to change user roles so I can grant or revoke access.

**Acceptance Criteria:**
- I can change any user's role from the admin panel
- Role options: Viewer, Member, Admin, Fund Admin
- Changes require confirmation for admin/FA roles
- Cannot remove last admin from an org
- Role change is logged with my ID and timestamp

**Test:** TEST-AUTH-07

### US-AUTH-08: FA Onboard GP (Invite Method)
As a Fund Admin, I want to onboard a new GP by inviting their admin so they can start using the platform.

**Acceptance Criteria:**
- Multi-step wizard collects company info and GP profile
- Select "Invite Admin" method
- Enter admin email address
- Organization created with is_gp=TRUE
- Invitation sent to admin email
- GP admin can accept and set up their account
- I can see onboarding status in my FA dashboard

**Test:** TEST-AUTH-08a

### US-AUTH-09: FA Onboard GP (Direct Creation)
As a Fund Admin, I want to create a GP account directly so I can expedite their onboarding.

**Acceptance Criteria:**
- Multi-step wizard collects company info and user details
- Select "Create User Directly" method
- I set a temporary password for the user
- User receives account creation email
- User must change password on first login
- Organization and employment records created atomically

**Test:** TEST-AUTH-08b

### US-AUTH-10: FA Add LP to Database
As a Fund Admin, I want to add LP organizations to the database so GPs can find them in searches.

**Acceptance Criteria:**
- Multi-step wizard collects LP org and profile info
- Optional: add key contacts (people records)
- LP appears in search results immediately
- Duplicate detection warns if similar LP exists
- I can edit the LP profile after creation

**Test:** TEST-AUTH-09a

### US-AUTH-11: FA Onboard LP with Portal Access
As a Fund Admin, I want to create an LP organization with user access so they can use the LP portal.

**Acceptance Criteria:**
- Multi-step wizard collects LP info plus admin email
- Select "Invite Admin" or "Create User Directly" method
- Organization created with is_lp=TRUE
- LP profile created with provided details
- Invitation sent or user created directly
- LP admin gains access to LP dashboard features

**Test:** TEST-AUTH-09b

### US-AUTH-12: FA Dashboard
As a Fund Admin, I want a dedicated dashboard so I can manage platform entities and recommendations.

**Acceptance Criteria:**
- Cross-org overview of all GPs and LPs
- View all fund-LP matches across platform
- Add manual recommendations (suggest LP for a fund)
- Override or adjust match scores with notes
- Quick links to impersonate any GP/LP for support
- Recent activity feed (onboardings, recommendations)

**Test:** TEST-AUTH-10

### US-AUTH-13: FA Entity Management
As a Fund Admin, I want to manage all platform entities so I can maintain data quality.

**Acceptance Criteria:**
- Full CRUD on GP organizations and profiles
- Full CRUD on LP organizations and profiles
- Full CRUD on people records with merge capability
- Full CRUD on users with role assignment (Viewer/Member only)
- Cannot assign Admin or Fund Admin roles (Super Admin only)
- All changes logged for audit

**Test:** TEST-AUTH-11

### US-AUTH-14: FA Billing Management
As a Fund Admin, I want to manage billing for all organizations so I can track subscriptions.

**Acceptance Criteria:**
- View/manage billing for all orgs
- Set up billing plans for new orgs
- View all invoices across platform
- Summary of revenue, subscriptions, past due accounts

**Test:** TEST-AUTH-12a

### US-AUTH-15: Self-Service Billing
As a GP or LP admin, I want to manage my organization's billing so I can control our subscription.

**Acceptance Criteria:**
- View current plan and usage metrics
- Update payment method (credit card)
- View invoice history with date, amount, status
- Download invoices as PDF
- Upgrade/downgrade plan
- Manage auto-renewal
- Cancel subscription with confirmation

**Test:** TEST-AUTH-12b

---

## 10.2 LP Search (Priority A)

### US-LP-01: Basic LP Search
As a GP, I want to search LPs by criteria so I can find relevant investors.

**Acceptance Criteria:**
- Filter by: type (multi-select), strategy (multi-select), geography (multi-select)
- Filter by: AUM range (min-max slider)
- Filter by: check size range (min-max slider)
- Results update within 500ms of filter change
- Can combine multiple filters (AND logic)
- Clear all filters button
- Results count shown

**Test:** TEST-LP-01

### US-LP-02: Semantic LP Search
As a GP, I want to search LPs using natural language so I can describe what I'm looking for.

**Acceptance Criteria:**
- Free text input field
- Query: "LPs interested in climate tech in Europe" returns relevant results
- Results show relevance score (0-100)
- Can combine semantic search with filters
- Search completes in < 2 seconds

**Test:** TEST-LP-02

### US-LP-03: View LP Details
As a GP, I want to view LP details so I can understand their preferences.

**Acceptance Criteria:**
- All LP fields displayed in organized sections
- Contact information shown with LinkedIn links
- Historical commitments listed (if available)
- Data quality indicator shown
- "Last updated" date visible

**Test:** TEST-LP-03

---

## 10.3 Data Import (Priority A)

### US-IMPORT-01: CSV Import
As an admin, I want to import LP data from CSV so I can populate the database.

**Acceptance Criteria:**
- Accept CSV files up to 50MB
- Field mapping interface (source column -> target field)
- Preview first 10 rows before import
- Validation errors shown per row
- Duplicate detection by name + location
- Progress indicator during import
- Summary report after completion

**Test:** TEST-IMPORT-01

### US-IMPORT-02: Data Cleaning
As an admin, I want imported data to be automatically cleaned so it's usable.

**Acceptance Criteria:**
- Strategy names normalized to taxonomy
- Geography names standardized
- LP types normalized
- Empty strings converted to NULL
- Whitespace trimmed
- Data quality score calculated

**Test:** TEST-IMPORT-02

### US-IMPORT-03: Data Enrichment
As an admin, I want LP data enriched from external sources so it's more complete.

**Acceptance Criteria:**
- Support bulk updates from CSV/Excel
- Future: API integration with data providers (Preqin, PitchBook)
- Enrichment log shows what changed
- Confidence score for enriched fields
- Human review queue before committing changes
- Diff view showing old vs new values

**Test:** TEST-IMPORT-03

---

## 10.4 Matching (Priority B)

### US-MATCH-01: Generate Matches
As a GP, I want to generate LP matches for my fund so I can identify targets.

**Acceptance Criteria:**
- Click button to generate matches
- Loading indicator during generation
- Matches displayed ranked by score (highest first)
- Score shown visually (progress bar + number)
- At least top 50 matches shown
- Generation completes in < 30 seconds

**Test:** TEST-MATCH-01

### US-MATCH-02: Match Explanation
As a GP, I want to understand why an LP matched so I can tailor my approach.

**Acceptance Criteria:**
- AI-generated explanation (2-3 paragraphs)
- Key alignment points highlighted (bullets)
- Potential concerns noted (if any)
- Talking points suggested (3-5 bullets)
- Explanation loads in < 5 seconds

**Test:** TEST-MATCH-02

### US-MATCH-03: Dismiss Match
As a GP, I want to dismiss irrelevant matches so I can focus on good ones.

**Acceptance Criteria:**
- Dismiss button on each match card
- Optional reason selection (dropdown)
- Dismissed match removed from list
- Can view dismissed matches separately
- Undo dismiss within 10 seconds

**Test:** TEST-MATCH-03

---

## 10.5 Pitch Generation (Priority C)

### US-PITCH-01: Generate Summary
As a GP, I want to generate an LP-specific summary so I can send personalized materials.

**Acceptance Criteria:**
- One click generation from match view
- Summary includes LP-specific talking points
- Professional formatting (headers, bullets)
- Can edit before download
- Export as PDF
- Generation completes in < 10 seconds

**Test:** TEST-PITCH-01

### US-PITCH-02: Generate Email
As a GP, I want to generate an outreach email so I can contact the LP.

**Acceptance Criteria:**
- Personalized email generated
- Tone selection (formal, warm, direct)
- Includes specific LP references
- Subject line generated
- Copy to clipboard button
- Edit inline before copying

**Test:** TEST-PITCH-02

---

## 10.6 LP Matching (M7)

> **Principle:** Whatever a GP can do with LPs, an LP should be able to do with GPs.

### US-LP-MATCH-01: Create Mandate
As an LP, I want to create investment mandates so the system can match me with relevant funds.

**Acceptance Criteria:**
- Create mandate with: name, strategy, geography, check size range, fund size range
- Mandate can be active or paused
- Multiple mandates supported
- Mandates trigger automatic match generation

**Test:** TEST-LP-MATCH-01

### US-LP-MATCH-02: View Fund Matches
As an LP, I want to see AI-ranked fund recommendations so I can identify opportunities.

**Acceptance Criteria:**
- Matches ranked by score (0-100)
- Filter by mandate
- See match reasons (strategy alignment, track record, size fit)
- Matches update when new funds are added
- Can dismiss irrelevant matches

**Test:** TEST-LP-MATCH-02

### US-LP-MATCH-03: View Match Analysis
As an LP, I want to see Bull vs Bear analysis for a fund match so I can make informed decisions.

**Acceptance Criteria:**
- Bull case: strengths and opportunities
- Bear case: risks and concerns
- Score breakdown by factor
- Suggested due diligence questions
- Analysis generated in < 10 seconds

**Test:** TEST-LP-MATCH-03

### US-LP-MATCH-04: Manage Pipeline
As an LP, I want to track funds through my evaluation process so I can manage my deal flow.

**Acceptance Criteria:**
- Pipeline stages: Initial Review → Due Diligence → IC Approval → Committed
- Add funds from matches or search
- Move funds between stages
- Add notes per fund
- See estimated commitment totals

**Test:** TEST-LP-MATCH-04

### US-LP-MATCH-05: Watchlist
As an LP, I want to watchlist funds for future consideration so I don't lose track of them.

**Acceptance Criteria:**
- Add fund to watchlist from search or matches
- Add notes per watched fund
- See fund status (raising, upcoming)
- Remove from watchlist
- Move to pipeline when ready

**Test:** TEST-LP-MATCH-05

### US-LP-MATCH-06: Mutual Interest Detection
As an LP or GP, I want to know when both parties have expressed interest so we can connect faster.

**Acceptance Criteria:**
- Mutual interest alert shown to both parties
- GP shortlisted LP + LP has GP in pipeline = mutual
- Notification sent to both
- Accelerated path to meeting

**Test:** TEST-LP-MATCH-06

---

[Next: Non-Functional Requirements →](nfr.md)
