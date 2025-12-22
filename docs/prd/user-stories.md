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

[Next: Non-Functional Requirements →](nfr.md)
