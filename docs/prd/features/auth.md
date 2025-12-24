# Authentication & Authorization

[← Back to Features Index](index.md)

---

> **IMPORTANT: Invite-Only Platform**
> LPxGP is a controlled B2B platform. There is NO public registration.
> All users must be invited - either by Super Admin (for company admins)
> or by Company Admin (for team members).

---

## F-AUTH-01: User Login [P0]

**Description:** Invited users can login securely

**Requirements:**
- Email/password authentication via Supabase Auth
- Password reset flow for existing users
- Session management with JWT (7-day refresh)
- No public registration - login page only
- Clear error messages (generic for security)

**Test Cases:** See TEST-AUTH-01 in Testing Strategy

---

## F-AUTH-02: Multi-tenancy [P0]

**Description:** Users belong to exactly one company, data is isolated

**Requirements:**
- User belongs to exactly one company (no multi-company)
- Users only see their company's data
- Row-level security in database
- Company-level settings
- User cannot switch companies (must create new account)

**Test Cases:** See TEST-AUTH-02 in Testing Strategy

---

## F-AUTH-03: Role-Based Access Control [P0]

**Description:** Different permission levels within a company

**Requirements:**
- Roles: Admin, Member, Viewer
- Admin: manage users, invite team, settings, all data
- Member: create/edit/delete own data, view shared
- Viewer: read-only access
- First user in company is automatically Admin

**Test Cases:** See TEST-AUTH-03 in Testing Strategy

---

## F-AUTH-04: Super Admin Panel [P0]

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

---

## F-AUTH-05: User Invitations [P0]

**Description:** Invite-only access to the platform

### Super Admin invites Company Admin:
1. Super Admin creates company in admin panel
2. Super Admin enters admin email and clicks "Send Invite"
3. System generates invitation with secure token
4. Email sent: "You've been invited to LPxGP as Admin of [Company]"
5. Link expires in 7 days
6. Clicking link → Accept Invite page (set password)
7. User created with Admin role, linked to company

### Company Admin invites Team Member:
1. Admin goes to Settings > Team > Invite
2. Admin enters email and selects role (Member or Admin)
3. System generates invitation with secure token
4. Email sent: "You've been invited to join [Company] on LPxGP"
5. Link expires in 7 days
6. Clicking link → Accept Invite page (set password)
7. User created with specified role, linked to company

### Invitation Rules:
- One active invitation per email address
- Expired invitations can be resent
- Accepted invitations are marked used
- Cannot invite email that already has an account
- Invitation includes: token, email, company_id, role, invited_by, expires_at

**Test Cases:** See TEST-AUTH-05 in Testing Strategy

---

## F-AUTH-06: Admin Impersonation [P0]

**Description:** Super Admin and Fund Admin can view the platform as any user for support and debugging

**Requirements:**
- Super Admin can impersonate any non-Super-Admin user
- Fund Admin can impersonate GP and LP users (view-only only)
- During impersonation:
  - User sees the platform exactly as the target user sees it
  - Visual banner at top: "[Admin Name] viewing as [User Name] | VIEW ONLY"
  - FA impersonation is always view-only (no changes allowed)
  - Super Admin can optionally enable write mode for support scenarios
  - All actions logged with both admin and target user IDs
- "End Session" button returns admin to their own context
- Audit log captures: admin_user_id, target_user_id, start_time, end_time, actions_taken

**Access:** Super Admin (any user), Fund Admin (GP/LP users only, view-only)

**Test Cases:** See TEST-AUTH-06 in Testing Strategy

---

## F-AUTH-07: Role Management [P0]

**Description:** Super Admin can assign and change user roles

**Requirements:**
- Role assignment UI in admin-users.html (edit modal or inline dropdown)
- Roles available for assignment:
  - Viewer - Read-only access to own org
  - Member - Read/write access to own org data
  - Admin - Full own org access + user management
  - Fund Admin - Cross-org read, privileged operations
- Super Admin can promote any user to any role (including Fund Admin)
- Super Admin can demote users (with confirmation for admins)
- Role changes are audited with: changed_by, old_role, new_role, timestamp
- Cannot remove last Admin from an org (must have at least one)
- Cannot remove Super Admin flag from self

**Access:** Super Admin only

**Test Cases:** See TEST-AUTH-07 in Testing Strategy

---

## F-AUTH-08: Fund Admin GP Onboarding [P0]

**Description:** Fund Admin can onboard new GP organizations to the platform

**Method A: Database Only**
1. FA clicks "Onboard GP" in FA dashboard
2. Enter company details: Name, website, HQ location, description
3. Enter GP profile: Fund focus, strategies, typical fund size
4. Confirm and create
5. GP organization created with is_gp=TRUE, no users

**Method B: Create GP + Invite Admin**
1. FA clicks "Onboard GP" in FA dashboard
2. Enter company and GP profile details (same as Method A)
3. Select "Invite Admin" method
4. Enter admin email address
5. System creates organization, sends invitation email
6. GP admin accepts invite, sets password, gains Admin role

**Method C: Create GP + Create User Directly**
1. FA clicks "Onboard GP" in FA dashboard
2. Enter company and GP profile details (same as Method A)
3. Select "Create User Directly" method
4. Enter: Full name, email, temporary password
5. System creates organization, creates user with Admin role
6. User receives "Account created" email with login instructions
7. User must change password on first login

**Requirements:**
- Wizard UI with progress indicator
- Validation at each step (email format, uniqueness)
- Cannot create duplicate organization (name + location check)
- Tracks `onboarded_by` and `onboarding_method` on organization
- All onboarding actions logged for audit

**Access:** Fund Admin, Super Admin

**Test Cases:** See TEST-AUTH-08 in Testing Strategy

---

## F-AUTH-09: Fund Admin LP Onboarding [P0]

**Description:** Fund Admin can add LP organizations to the platform

**Method A: Database Only (No Users)**
1. FA clicks "Onboard LP" in FA dashboard
2. Enter organization details: Name, website, type, HQ location
3. Enter LP profile: AUM, strategies, check size range, mandate
4. Optionally add key contacts (name, title, email, is_decision_maker)
5. Confirm and create
6. LP appears in shared database, visible to all GPs for matching

**Method B: Create LP + Invite Admin**
1. Same steps as Method A for organization and profile
2. Select "Invite Admin" method
3. Enter LP admin email address
4. System creates organization (is_lp=TRUE), lp_profile, sends invitation
5. LP admin accepts invite, gains access to LP dashboard (M7 feature)

**Method C: Create LP + Create User Directly**
1. Same steps as Method A for organization and profile
2. Select "Create User Directly" method
3. Enter: Full name, email, temporary password
4. System creates organization, user with Admin role
5. User receives "Account created" email
6. User must change password on first login

**Requirements:**
- Multi-step wizard (6 steps)
- Data quality validation (minimum required fields)
- Duplicate detection (fuzzy match on name + location)
- Same invite/direct patterns as GP onboarding for consistency
- All actions logged for audit

**Access:** Fund Admin, Super Admin

**Test Cases:** See TEST-AUTH-09 in Testing Strategy

---

## F-AUTH-10: Fund Admin Dashboard [P0]

**Description:** Dedicated dashboard for Fund Admins to manage platform entities and recommendations

**Requirements:**
- FA-specific navigation: Dashboard, GPs, LPs, People, Users, Billing, Recommendations
- Overview cards: Total GPs, Total LPs, Total Users, Pending Recommendations
- Recommendations management:
  - View all fund-LP matches across platform
  - Add manual recommendations (suggest LP for a fund)
  - Override or adjust match scores with notes
  - Track recommendation outcomes
- Quick actions: Onboard GP, Onboard LP
- Recent activity feed (onboardings, recommendations, impersonation sessions)
- Cross-org view of all platform data

**Access:** Fund Admin, Super Admin

**Test Cases:** See TEST-AUTH-10 in Testing Strategy

---

## F-AUTH-11: Fund Admin Entity Management [P0]

**Description:** Fund Admin has full CRUD capabilities on all platform entities

**GP Management (fa-gps.html):**
- List all GP organizations with: Name, Website, HQ, User Count, Fund Count, Status
- Actions: View, Edit, Impersonate, Delete
- Search, filter by status
- "Onboard GP" button opens wizard

**LP Management (fa-lps.html):**
- List all LP organizations with: Name, Type, AUM, Quality Score, Contact Count, Status
- Actions: View, Edit, Impersonate (if has users), Delete
- Search, filter by type/quality
- "Onboard LP" button opens wizard

**People Management (fa-people.html):**
- List all people with: Name, Email, Organization, Title, Verified
- Actions: View, Edit, Delete, Merge
- Search, filter by org type
- "Add Person" button
- "Merge Duplicates" workflow for duplicate resolution

**User Management (fa-users.html):**
- List all users with: Name, Email, Organization, Role, Status, Last Active
- Actions: View, Edit Role, Impersonate, Deactivate
- Role dropdown: Viewer, Member only (Admin/FA roles disabled)
- FA CANNOT assign Admin or Fund Admin roles
- Admin/FA users show "Contact Super Admin to modify" tooltip
- "Add User" button (creates user directly, Viewer/Member only)

**Requirements:**
- All changes logged for audit
- FA cannot modify Admin or Fund Admin roles (only Super Admin can)

**Access:** Fund Admin, Super Admin

**Test Cases:** See TEST-AUTH-11 in Testing Strategy

---

## F-AUTH-12: Billing Management [P0]

**Description:** Billing management for platform subscriptions

**FA Billing Dashboard (fa-billing.html):**
- View/manage billing for all organizations
- Table: Organization, Type (GP/LP), Plan, Status, Monthly Fee, Next Invoice
- Actions: View Details, Edit Plan, View Invoices
- Set up billing plans for new orgs
- Summary cards: Total Revenue, Active Subscriptions, Past Due, Upcoming Renewals

**GP Self-Service Billing (settings-billing.html):**
- View current plan and usage metrics
- Update payment method (credit card on file)
- View invoice history with date, amount, status
- **Download invoices as PDF**
- Plan upgrade/downgrade options
- Manage auto-renewal
- Cancel subscription (with confirmation)

**LP Self-Service Billing (lp-settings.html billing tab):**
- Same capabilities as GP billing
- View current plan
- Update payment method
- View invoice history
- **Download invoices as PDF**
- LP-specific plan tiers

**Requirements:**
- Invoices downloadable as PDF
- Payment processing integration (future: Stripe)
- Billing contact email per organization
- Auto-renewal management

**Access:** FA can manage all orgs, GP/LP admins can manage own org billing

**Test Cases:** See TEST-AUTH-12 in Testing Strategy

---

[Next: GP Profile Management →](gp-profile.md)
