# Milestone 1: Auth + Search Tests
## "Search LPs on lpxgp.com"

---

## F-AUTH-01: User Authentication [P0]

```gherkin
Feature: User Authentication
  As a user
  I want to register and login securely
  So that I can access the platform

  # Sub-feature: Registration
  Scenario: Register with valid credentials
    Given I am on the registration page
    When I enter email "gp@venture.com"
    And I enter password "SecurePass123!"
    And I enter name "Jane Smith"
    And I click "Register"
    Then I see "Check your email to verify"
    And a verification email is sent

  Scenario: Email validation
    When I try to register with "not-an-email"
    Then I see "Please enter a valid email"

  Scenario: Password strength requirements
    When I try to register with password "weak"
    Then I see "Password must be at least 8 characters"
    And "Include uppercase, lowercase, and numbers"

  Scenario: Duplicate email prevention
    Given "existing@venture.com" is already registered
    When I try to register with "existing@venture.com"
    Then I see "This email is already registered"

  # Sub-feature: Email Verification
  Scenario: Verify email successfully
    Given I registered with "new@venture.com"
    And I received a verification email
    When I click the verification link
    Then my account is verified
    And I am redirected to login

  Scenario: Expired verification link
    Given my verification link expired (24 hours)
    When I click the link
    Then I see "Link expired, request a new one"
    And I can request a new verification email

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
```
