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

[Next: GP Profile Management →](gp-profile.md)
