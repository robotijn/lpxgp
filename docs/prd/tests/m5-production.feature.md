# Milestone 5: Production Tests
## "Production-ready with admin"

> **Super Admin = LPxGP Platform Team**
> Only Super Admins can create companies and invite the first user.
> This is the controlled onboarding flow for new GP firms.

---

## F-AUTH-04: Super Admin Panel [P0]

```gherkin
Feature: Super Admin Panel
  As a super admin (LPxGP team member)
  I want to manage companies and platform
  So that I can onboard and support GP firms

  # =============================================
  # Sub-feature: Company Onboarding (Core Flow)
  # =============================================

  Scenario: Complete company onboarding flow
    Given I am a super admin
    # Step 1: Create company
    When I go to Admin > Companies
    And I click "Add Company"
    Then I see company creation form

    # Step 2: Enter company details
    When I enter:
      | Field | Value |
      | Company Name | Acme Capital |
      | Admin Email | partner@acme.com |
      | Plan | Standard |
    And I click "Create & Send Invitation"
    Then company "Acme Capital" is created
    And company status is "Pending" (no users yet)
    And invitation is created for "partner@acme.com"
    And invitation email is sent
    And I see confirmation "Company created. Invitation sent to partner@acme.com"

    # Step 3: Verify in company list
    When I view the companies list
    Then I see "Acme Capital" with:
      | Status | Pending |
      | Users | 0 |
      | Admin Invited | partner@acme.com |

  Scenario: Company becomes active when admin accepts
    Given I created company "Acme Capital"
    And "partner@acme.com" received invitation
    When the admin accepts the invitation
    Then company status changes to "Active"
    And user count shows "1"
    And "partner@acme.com" is shown as Admin

  # Sub-feature: Company Management
  Scenario: View all companies
    Given I am a super admin
    When I go to Admin > Companies
    Then I see all companies with:
      | Company | Status | Users | Funds | Created |
      | Acme Capital | Active | 5 | 3 | 2024-01-15 |
      | Beta Ventures | Active | 8 | 5 | 2024-02-20 |
      | New Firm | Pending | 0 | 0 | 2024-03-01 |

  Scenario: Filter companies by status
    Given I am viewing companies
    When I filter by status "Pending"
    Then I only see companies awaiting admin acceptance

  Scenario: Search companies
    Given I am viewing companies
    When I search for "Acme"
    Then I see "Acme Capital" in results
    And other companies are hidden

  Scenario: View company details
    Given I am a super admin
    When I click on "Acme Capital"
    Then I see company detail page with:
      | Section | Content |
      | Overview | Name, status, created date |
      | Users | List of all users with roles |
      | Funds | List of all funds |
      | Activity | Recent activity log |
      | Settings | Plan, limits, features |

  Scenario: Edit company settings
    Given I am viewing company "Acme Capital"
    When I click "Edit Settings"
    Then I can edit:
      | Company name |
      | Plan/tier |
      | User limit |
      | Feature flags |
    When I save changes
    Then settings are updated
    And change is logged in activity

  Scenario: Deactivate company
    Given company "Defunct Corp" should be deactivated
    When I click "Deactivate Company"
    Then I see confirmation dialog with warnings
    When I confirm with reason "Contract ended"
    Then company status is "Deactivated"
    And all users cannot login
    And data is preserved (not deleted)
    And I can reactivate later

  Scenario: Reactivate company
    Given company "Defunct Corp" is deactivated
    When I click "Reactivate"
    Then company status is "Active"
    And users can login again

  # --- NEGATIVE TESTS: Company Creation ---
  Scenario: Create company with empty name
    Given I am creating a new company
    When I leave company name empty
    And I click "Create"
    Then I see "Company name is required"
    And company is not created

  Scenario: Create company with duplicate name
    Given "Acme Capital" already exists
    When I try to create company "Acme Capital"
    Then I see "A company with this name already exists"
    And company is not created

  Scenario: Create company with invalid admin email
    Given I am creating a new company
    When I enter admin email "not-an-email"
    Then I see "Please enter a valid email"
    And company is not created

  Scenario: Create company with existing user email
    Given "existing@other.com" is already a user
    When I create company with admin email "existing@other.com"
    Then I see "This email is already registered"
    And company is not created

  Scenario: Resend company admin invitation
    Given company "New Firm" has pending invitation
    When I click "Resend Invitation"
    Then new invitation email is sent
    And old invitation is expired
    And I see confirmation

  Scenario: Cancel company invitation
    Given company "New Firm" has pending invitation
    When I click "Cancel Invitation"
    Then invitation is cancelled
    And I can send a new invitation to different email

  # Sub-feature: User Management
  Scenario: View company users
    When I select "Acme Capital"
    And I click "Users"
    Then I see all users in that company
    And I see their roles and status

  Scenario: Add user to company
    When I click "Add User"
    And I enter email "new@acme.com"
    And I select role "Member"
    Then user is added
    And invitation email is sent

  Scenario: Change user role
    When I find a user
    And I change role from "Member" to "Admin"
    Then role is updated
    And user has new permissions

  Scenario: Deactivate user
    When I click "Deactivate" on a user
    Then user cannot login
    And data is preserved
    And user can be reactivated

  # Sub-feature: LP Database Management
  # Note: LP contacts are now stored in global "people" table with "employment" records.
  # Admins manage people separately from LP organizations.

  Scenario: Browse all LPs
    When I go to Admin > LPs
    Then I see all LPs in the database
    And I can search and filter
    And I can see data quality scores
    And I can see how many contacts (people) are linked

  Scenario: Edit LP data
    When I find an LP
    And I click "Edit"
    Then I can modify any field
    And changes are logged

  Scenario: Delete LP
    When I click "Delete" on an LP
    Then I see confirmation dialog
    When I confirm
    Then LP is deleted
    And related matches are updated
    And employment records for this LP are ended (people preserved)

  # Sub-feature: People (Global Contact Database)
  Scenario: Browse all people
    When I go to Admin > People
    Then I see all people in the global database
    And I can filter by current org type (LP/GP)
    And I can search by name or email
    And I can see employment history summary

  Scenario: View person detail
    When I click on person "John Smith"
    Then I see their profile with:
      | Section | Content |
      | Contact Info | Name, email, phone, LinkedIn |
      | Current Role | Title at current org |
      | Employment History | All past positions with dates |
      | Focus Areas | Expertise and specializations |

  Scenario: Edit person details
    When I click "Edit" on a person
    Then I can modify contact info
    And I can update their current role
    And I can add/edit employment history
    And changes are tracked in audit log

  Scenario: Manage employment history
    Given person "John Smith" is at "CalPERS"
    When I add new employment:
      | Field | Value |
      | Org | Yale Endowment |
      | Org Type | lp |
      | Title | CIO |
      | Start Date | 2024-01-15 |
    And I end their CalPERS employment
    Then John Smith's current org is "Yale Endowment"
    And CalPERS employment shows end date
    And all history is preserved

  Scenario: Merge duplicate people
    Given two person records with same email
    When I click "Merge"
    Then I select which record is primary
    And employment histories are combined
    And duplicate is marked as merged
    And references are updated

  # Sub-feature: Data Import
  Scenario: Trigger data import
    When I go to Admin > Import
    Then I can upload LP data file
    And I can map columns
    And I can preview and approve import

  # Sub-feature: Platform Analytics
  Scenario: View platform stats
    When I go to Admin > Analytics
    Then I see:
      | Metric | Value |
      | Total Companies | 25 |
      | Total Users | 150 |
      | Total Funds | 45 |
      | Total LPs | 5,000 |
      | Matches Generated | 12,000 |
      | Pitches Created | 3,500 |

  # Sub-feature: Access Control
  Scenario: Non-admin cannot access
    Given I am a regular user (not super admin)
    When I try to access /admin
    Then I see 403 Forbidden
    And I am redirected to dashboard

  # NEGATIVE TESTS: Admin Access Denied
  Scenario: Company admin cannot access super admin panel
    Given I am a company admin (not super admin)
    When I try to access /admin/companies
    Then I see 403 Forbidden
    And access attempt is logged

  Scenario: Deactivated admin cannot access admin panel
    Given I was a super admin but am now deactivated
    When I try to access /admin
    Then I see 401 Unauthorized
    And I am redirected to login

  Scenario: Expired session cannot access admin
    Given my session has expired
    When I try to access /admin
    Then I see 401 Unauthorized
    And I am redirected to login with return URL preserved

  Scenario: Admin access via direct URL manipulation
    Given I am a regular user
    When I try to access /admin/users/123/edit by typing URL directly
    Then I see 403 Forbidden
    And no user data is returned in response

  # NEGATIVE TESTS: Invalid Company Operations
  Scenario: Create company with duplicate name
    Given company "Acme Capital" already exists
    When I try to create company with name "Acme Capital"
    Then I see error "Company name already exists"
    And no company is created

  Scenario: Create company with invalid email
    When I try to create company with admin email "not-an-email"
    Then I see validation error "Invalid email format"
    And no company is created

  Scenario: Create company with empty name
    When I try to create company with empty name
    Then I see validation error "Company name is required"
    And form is not submitted

  Scenario: Create company with excessively long name
    When I try to create company with name of 500 characters
    Then I see validation error "Company name must be under 255 characters"
    And no company is created

  Scenario: Edit non-existent company
    When I try to access /admin/companies/99999/edit
    Then I see 404 Not Found
    And error is logged

  Scenario: Delete company with active users
    Given company "Acme Capital" has 5 active users
    When I try to delete "Acme Capital" without deactivating users first
    Then I see error "Cannot delete company with active users"
    And company is not deleted
    And I see option to "Deactivate all users first"

  # NEGATIVE TESTS: Invalid User Operations
  Scenario: Add user with duplicate email
    Given user "john@acme.com" already exists
    When I try to add user with email "john@acme.com"
    Then I see error "User with this email already exists"
    And no duplicate user is created

  Scenario: Add user with invalid email domain
    Given company has email domain restriction "@acme.com"
    When I try to add user with email "user@gmail.com"
    Then I see warning "Email domain does not match company domain"
    And I must confirm to proceed

  Scenario: Change role of last admin to member
    Given company has only one admin
    When I try to change that admin's role to "Member"
    Then I see error "Cannot remove last admin from company"
    And role is not changed

  Scenario: Deactivate yourself
    Given I am the logged-in admin
    When I try to deactivate my own account
    Then I see error "Cannot deactivate your own account"
    And my account remains active

  Scenario: Assign non-existent role
    When I try to assign role "SuperMegaAdmin" via API manipulation
    Then I see 400 Bad Request
    And error "Invalid role" is returned
    And attempt is logged as suspicious activity

  # NEGATIVE TESTS: LP Database Edge Cases
  Scenario: Edit LP with concurrent modification
    Given another admin is editing LP "CalPERS"
    When I try to save my changes to LP "CalPERS"
    Then I see error "LP was modified by another user"
    And I see option to refresh and review changes
    And my changes are not lost (shown in diff view)

  Scenario: Delete LP referenced by active matches
    Given LP "CalPERS" has 50 active matches
    When I try to delete LP "CalPERS"
    Then I see warning "LP has 50 active matches"
    And I must confirm deletion
    And matches are updated to show "LP no longer available"

  Scenario: Edit LP with invalid AUM format
    When I try to set LP AUM to "lots of money"
    Then I see validation error "AUM must be a number"
    And changes are not saved

  Scenario: Edit LP with negative AUM
    When I try to set LP AUM to -5000000000
    Then I see validation error "AUM cannot be negative"
    And changes are not saved
```

---

## F-UI-05: Admin Interface [P0]

```gherkin
Feature: Admin Interface
  As an admin
  I want a comprehensive admin UI
  So that I can manage the platform effectively

  # Sub-feature: Dashboard
  Scenario: Admin dashboard overview
    When I login as super admin
    And I go to Admin
    Then I see dashboard with:
      | Companies summary |
      | Users summary |
      | LP database stats |
      | Recent activity |
      | System health |

  # Sub-feature: User Management UI
  Scenario: User management table
    When I view user management
    Then I see a table with:
      | Column | Sortable | Filterable |
      | Name | Yes | Yes |
      | Email | Yes | Yes |
      | Company | Yes | Yes |
      | Role | Yes | Yes |
      | Status | Yes | Yes |
      | Last Login | Yes | No |

  Scenario: Inline actions
    When I hover over a user row
    Then I see action buttons:
      | "Edit" | "Reset Password" | "Deactivate" |

  # Sub-feature: LP Management UI
  Scenario: LP browser
    When I view LP management
    Then I see LPs in a data grid
    And I can search by name
    And I can filter by type, quality score
    And I can sort by any column

  Scenario: LP edit form
    When I click edit on an LP
    Then I see a comprehensive form
    And all fields are editable
    And validation runs on save

  # Sub-feature: Import Wizard UI
  Scenario: Step-by-step import wizard
    When I start an import
    Then I see wizard steps:
      | 1. Upload File |
      | 2. Map Columns |
      | 3. Preview Data |
      | 4. Validate |
      | 5. Approve & Import |

  # Sub-feature: Data Quality Dashboard
  Scenario: View data quality stats
    When I go to Admin > Data Quality
    Then I see:
      | Metric | Value |
      | Average Quality Score | 72% |
      | LPs Needing Review | 45 |
      | Unverified LPs | 120 |
      | Recently Updated | 50 |

  Scenario: Review queue
    When I click "LPs Needing Review"
    Then I see list of low-quality LPs
    And I can fix or delete each one

  # Sub-feature: System Health
  Scenario: View system health
    When I view system health
    Then I see:
      | Service | Status |
      | Database | Healthy |
      | Supabase Auth | Healthy |
      | OpenRouter API | Healthy |
      | Voyage AI | Healthy |

  # NEGATIVE TESTS: Admin Interface Errors
  Scenario: Dashboard fails to load due to database error
    Given database connection is temporarily unavailable
    When I try to load admin dashboard
    Then I see graceful error message "Unable to load dashboard data"
    And I see "Retry" button
    And partial data that was cached is shown

  Scenario: User table with no users
    Given company has no users (edge case from data migration)
    When I view user management for that company
    Then I see empty state "No users found"
    And I see "Add first user" button

  Scenario: LP browser with zero results
    When I search for "XYZ123NonExistentLP"
    Then I see empty state "No LPs match your search"
    And I see suggestion to adjust filters

  Scenario: LP edit form loses connection mid-save
    Given I am editing LP data
    When network connection is lost during save
    Then I see error "Save failed - please check your connection"
    And my changes are preserved in the form
    And I can retry saving

  Scenario: System health shows degraded service
    Given OpenRouter API is responding slowly
    When I view system health
    Then I see:
      | Service | Status |
      | OpenRouter API | Degraded (2.5s response) |
    And I see warning indicator
    And I see "Last checked: 30 seconds ago"

  Scenario: System health shows service failure
    Given Voyage AI is completely unavailable
    When I view system health
    Then I see:
      | Service | Status |
      | Voyage AI | Down |
    And I see red alert indicator
    And I see "Semantic search is unavailable"
```

---

## F-HITL-04: Data Import Preview [P0]

```gherkin
Feature: Data Import Preview (Human-in-the-Loop)
  As an admin
  I want to preview imports before committing
  So that I don't accidentally corrupt data

  # Sub-feature: Preview Display
  Scenario: Show preview of import data
    Given I uploaded and mapped a CSV
    When I reach the preview step
    Then I see first 20 rows of data
    And I see how it will look after import
    And I see total count to import

  # Sub-feature: Validation Results
  Scenario: Show validation errors
    Given import has some invalid rows
    When I view preview
    Then I see error summary:
      | Valid Rows | 480 |
      | Errors | 15 |
      | Warnings | 5 |
    And I can see each error with details

  Scenario: Error details
    When I click "View Errors"
    Then I see:
      | Row | Field | Issue |
      | 25 | email | Invalid format |
      | 42 | aum | Not a number |

  # Sub-feature: Duplicate Detection
  Scenario: Show duplicates detected
    Given import has potential duplicates
    When I view preview
    Then I see "10 potential duplicates found"
    And I can review each one
    And I can choose Skip or Merge

  # Sub-feature: Explicit Approval
  Scenario: Require approval to import
    Given I reviewed the preview
    Then I see two buttons:
      | "Approve & Import" |
      | "Cancel" |
    And I must click one to proceed

  Scenario: Approve import
    When I click "Approve & Import"
    Then import job starts
    And I see progress bar
    And data is inserted into database

  Scenario: Cancel import
    When I click "Cancel"
    Then no data is imported
    And I return to import screen

  # Sub-feature: Rollback
  Scenario: Rollback option
    Given I imported data 2 hours ago
    When I go to import history
    Then I see "Rollback" button
    And I can undo the import within 24 hours

  Scenario: Rollback expired
    Given I imported data 30 hours ago
    When I view import history
    Then "Rollback" is disabled
    And I see "Rollback window expired"

  # NEGATIVE TESTS: Data Import Failures
  Scenario: Upload corrupted CSV file
    When I upload a corrupted CSV file
    Then I see error "File could not be parsed"
    And I see suggestions:
      | "Check file encoding (UTF-8 recommended)" |
      | "Ensure proper CSV formatting" |
    And no import is started

  Scenario: Upload empty file
    When I upload an empty CSV file
    Then I see error "File contains no data"
    And I cannot proceed to mapping step

  Scenario: Upload file exceeding size limit
    When I upload a CSV file over 50MB
    Then I see error "File size exceeds limit (50MB max)"
    And upload is rejected before completion

  Scenario: Upload non-CSV file with CSV extension
    When I upload a binary file renamed to .csv
    Then I see error "Invalid file format - not a valid CSV"
    And no import is started

  Scenario: Column mapping with missing required fields
    Given I uploaded a CSV
    When I try to proceed without mapping required "name" field
    Then I see error "Required field 'LP Name' must be mapped"
    And I cannot proceed to preview

  Scenario: Import with all rows failing validation
    Given I uploaded a CSV with 100% invalid data
    When I view preview
    Then I see "All rows failed validation"
    And "Approve & Import" is disabled
    And I see "Fix data and re-upload"

  # NEGATIVE TESTS: Rollback Failures
  Scenario: Rollback when data has been modified
    Given I imported 100 LPs 2 hours ago
    And 5 of those LPs have been edited since import
    When I try to rollback
    Then I see warning "5 records have been modified since import"
    And I can choose:
      | "Rollback all anyway" |
      | "Rollback only unmodified records" |
      | "Cancel rollback" |

  Scenario: Rollback fails mid-operation
    Given I am rolling back an import
    When database connection fails during rollback
    Then I see error "Rollback failed - partial state"
    And I see which records were reverted
    And I see which records still need attention
    And error is logged for admin review

  Scenario: Rollback when LPs have active matches
    Given I imported 100 LPs
    And 20 of those LPs have been used in matches
    When I try to rollback
    Then I see warning "20 LPs have associated matches"
    And I must confirm matches will be marked as invalid
    And I can proceed or cancel

  Scenario: Double rollback attempt
    Given I already rolled back an import
    When I try to rollback the same import again
    Then I see error "Import has already been rolled back"
    And no action is taken

  Scenario: Import fails mid-process
    Given I approved an import of 500 LPs
    And 250 LPs have been inserted
    When database connection fails
    Then import is paused
    And I see "Import failed at row 250"
    And I can "Resume" or "Rollback partial import"
    And data integrity is preserved (transaction)

  Scenario: Import timeout
    Given I approved an import of 10,000 LPs
    When import takes longer than 5 minutes
    Then I see progress indicator
    And I can continue working (import runs in background)
    And I receive notification when complete or failed
```

---

## F-HITL-05: LP Data Corrections [P1]

```gherkin
Feature: LP Data Corrections (Human-in-the-Loop)
  As a GP
  I want to flag incorrect LP data
  So that the database stays accurate

  # Sub-feature: Flag Outdated
  Scenario: Flag LP as outdated
    Given I am viewing an LP profile
    And I know the data is old
    When I click "Flag as Outdated"
    Then a flag is recorded
    And admin is notified

  # Sub-feature: Suggest Correction
  Scenario: Suggest a correction
    Given I am viewing an LP profile
    And I know the correct AUM
    When I click "Suggest Correction"
    And I enter:
      | Field | Current | Suggested |
      | AUM | $10B | $15B |
      | Note | Recent press release |
    Then suggestion is submitted
    And admin can review

  # Sub-feature: Admin Review
  Scenario: Admin reviews flags
    Given there are flagged LPs
    When admin goes to review queue
    Then they see all flagged LPs
    And can approve or reject corrections

  Scenario: Approve correction
    Given a correction was suggested
    When admin approves it
    Then LP data is updated
    And flag is resolved
    And GP is thanked (optional notification)

  Scenario: Reject correction
    When admin rejects with reason
    Then flag is resolved
    And reason is logged

  # Sub-feature: Flag History
  Scenario: View flag history
    Given an LP was flagged multiple times
    When admin views LP's flag history
    Then they see all historical flags
    And can see patterns (frequently flagged)

  # NEGATIVE TESTS: Invalid Corrections
  Scenario: Submit correction with invalid data
    When I suggest AUM correction with value "lots"
    Then I see validation error "AUM must be a valid number"
    And correction is not submitted

  Scenario: Submit correction identical to current value
    Given LP AUM is currently $10B
    When I suggest correction with same value $10B
    Then I see error "Suggested value is same as current value"
    And correction is not submitted

  Scenario: Submit empty correction
    When I submit correction with no changes
    Then I see error "At least one field must be changed"
    And correction is not submitted

  Scenario: Flag spam - excessive flagging by single user
    Given I have flagged 50 LPs in the last hour
    When I try to flag another LP
    Then I see "Flagging limit reached"
    And I am asked to wait before flagging more
    And admin is notified of potential spam

  Scenario: Submit correction for non-existent LP
    Given LP was deleted after I loaded the page
    When I try to submit correction
    Then I see error "LP no longer exists"
    And correction is discarded

  Scenario: Admin approves correction with stale data
    Given correction was submitted for AUM $10B -> $15B
    And another admin already changed AUM to $12B
    When I try to approve the correction
    Then I see warning "LP was modified since correction was submitted"
    And I see current value ($12B) vs suggested ($15B)
    And I can approve, reject, or modify

  Scenario: Submit correction with malicious note
    When I submit correction with note containing script tags
    Then HTML is sanitized in the note
    And correction is saved safely
    And no XSS attack is possible
```

---

## Performance Tests

```gherkin
Feature: Performance Requirements
  As a platform
  I want fast response times
  So that users have good experience

  # Sub-feature: API Performance
  Scenario: LP search under 500ms
    Given 10,000 LPs in database
    When I search with filters
    Then response time is < 500ms

  Scenario: Semantic search under 2 seconds
    Given 10,000 LPs with embeddings
    When I perform semantic search
    Then response time is < 2 seconds

  Scenario: Match generation under 30 seconds
    Given 1,000 potential LPs
    When I generate matches
    Then completion time is < 30 seconds

  # Sub-feature: Concurrent Users
  Scenario: Handle 100 concurrent users
    Given 100 users are active simultaneously
    When they all perform searches
    Then 99% of requests succeed
    And average response time < 1 second

  # Sub-feature: Page Load
  Scenario: Dashboard loads fast
    When I load the dashboard
    Then page is interactive in < 2 seconds

  Scenario: LP list loads fast
    Given 50 LPs per page
    When I load LP search results
    Then page renders in < 1 second

  # NEGATIVE TESTS: Performance Degradation
  Scenario: System under heavy load
    Given 500 concurrent users (5x normal load)
    When all users perform searches
    Then system remains responsive (degraded but functional)
    And response time < 5 seconds (graceful degradation)
    And no requests timeout completely
    And error rate stays below 5%

  Scenario: Database query timeout
    Given a complex search query
    When query takes longer than 30 seconds
    Then query is cancelled
    And user sees "Search taking too long, please simplify"
    And connection is released back to pool

  Scenario: Memory exhaustion prevention
    Given user requests export of all 50,000 LPs
    When export would exceed memory limit
    Then export is streamed (not loaded to memory)
    Or export is chunked with progress indicator
    And server memory stays within limits

  Scenario: Slow external API (OpenRouter)
    Given OpenRouter is responding slowly (5+ seconds)
    When I request pitch generation
    Then I see "Generation in progress" with spinner
    And I can continue using other features
    And request doesn't block other users

  Scenario: Slow external API (Voyage AI)
    Given Voyage AI is responding slowly (5+ seconds)
    When I perform semantic search
    Then search falls back to keyword search
    And I see "Semantic search unavailable, using keyword search"
    And results are still returned

  Scenario: Connection pool exhaustion
    Given all database connections are in use
    When new request arrives
    Then request waits with timeout
    And if timeout expires, returns 503 Service Unavailable
    And includes Retry-After header

  Scenario: Large result set pagination
    Given search would return 10,000 results
    When I perform search
    Then only first page (50 results) is loaded
    And total count is shown
    And pagination is available
    And response time stays under 1 second

  Scenario: Slow admin dashboard with large dataset
    Given platform has 1,000 companies and 50,000 users
    When admin loads dashboard
    Then dashboard loads with cached summary data
    And detailed data loads progressively
    And page is interactive within 3 seconds
```

---

## Security Tests

```gherkin
Feature: Security Requirements
  As a platform
  I want secure operations
  So that user data is protected

  # Sub-feature: SQL Injection Prevention
  Scenario: Block SQL injection
    When I try malicious input in search:
      | "'; DROP TABLE lps; --" |
      | "1 OR 1=1" |
    Then request is handled safely
    And no data is corrupted
    And I don't see database errors

  # Sub-feature: Authentication Security
  Scenario: Reject expired tokens
    Given my session token expired
    When I try to access protected resources
    Then I get 401 Unauthorized
    And I am redirected to login

  Scenario: Reject invalid tokens
    Given I have a tampered token
    When I try to access protected resources
    Then I get 401 Unauthorized

  # Sub-feature: Rate Limiting
  Scenario: Rate limit API requests
    When I make 150 requests in 1 minute
    Then some requests get 429 Too Many Requests
    And I see "Rate limit exceeded"

  # Sub-feature: Data Isolation
  Scenario: Cannot access other company data
    Given I am from "Company A"
    When I try to access Company B's fund by ID
    Then I get 404 Not Found
    And no data is leaked

  # NEGATIVE TESTS: SQL Injection Attacks
  Scenario: SQL injection in search field
    When I enter "'; DELETE FROM users; --" in search
    Then search returns no results (or empty)
    And no data is deleted
    And attempt is logged as security event

  Scenario: SQL injection in sort parameter
    When I try to sort by "name; DROP TABLE lps"
    Then request is rejected
    And I see 400 Bad Request
    And database is unaffected

  Scenario: SQL injection in filter values
    When I filter by LP type "Pension' OR '1'='1"
    Then filter returns no results (treated as literal)
    And no data leak occurs
    And query is parameterized

  Scenario: SQL injection in import data
    When I import CSV with LP name "'; DROP TABLE--"
    Then LP is created with literal name
    And no SQL is executed
    And import completes successfully

  Scenario: Second-order SQL injection
    Given I created LP with name containing SQL
    When admin searches for that LP
    Then search works safely
    And stored SQL fragment is not executed

  # NEGATIVE TESTS: XSS and Injection Attacks
  Scenario: XSS in LP name
    When I create LP with name "<script>alert('xss')</script>"
    Then name is HTML-escaped when displayed
    And no script executes

  Scenario: XSS in correction notes
    When I submit correction with note containing JavaScript
    Then note is sanitized
    And no XSS is possible in admin view

  Scenario: HTML injection in email fields
    When I register with email containing HTML
    Then email is validated and rejected
    And no HTML injection occurs

  # NEGATIVE TESTS: Authentication Attacks
  Scenario: Brute force login prevention
    When I fail login 5 times in a row
    Then account is temporarily locked
    And I see "Too many attempts, try again in 15 minutes"
    And lockout is logged

  Scenario: Session fixation prevention
    Given I have a session ID
    When I login successfully
    Then a new session ID is generated
    And old session ID is invalidated

  Scenario: Session hijacking prevention
    Given attacker obtains my session token
    When token is used from different IP/User-Agent
    Then session is flagged as suspicious
    And additional verification may be required

  Scenario: Token replay attack
    Given I logged out
    When someone tries to use my old token
    Then token is rejected (revoked on logout)
    And 401 Unauthorized is returned

  Scenario: Password reset token expiration
    Given I requested password reset 25 hours ago
    When I try to use the reset token
    Then token is rejected as expired
    And I must request new reset link

  # NEGATIVE TESTS: Rate Limiting Edge Cases
  Scenario: Rate limit per user not per IP
    Given user A and user B share same IP
    When user A hits rate limit
    Then user B can still make requests
    And rate limiting is per-user

  Scenario: Rate limit reset after window
    Given I hit rate limit at 10:00
    When I wait until 10:01 (window resets)
    Then I can make requests again
    And rate limit counter is reset

  Scenario: Rate limit on expensive operations
    When I try to generate 100 pitches in 1 minute
    Then pitch generation is rate-limited more strictly
    And I see "Limit: 10 pitches per minute"

  Scenario: Rate limit bypass attempt via API
    When I try to manipulate rate limit headers
    Then server ignores client-provided limits
    And server-side tracking is enforced

  Scenario: Distributed rate limiting (multiple instances)
    Given app runs on 3 Railway instances
    When I make requests spread across instances
    Then total rate limit is still enforced
    And Redis/central store tracks request count

  # NEGATIVE TESTS: Authorization Bypass
  Scenario: IDOR - accessing other user's data
    Given I am user 123
    When I try to access /api/users/456/profile
    Then I get 403 Forbidden (or 404)
    And user 456's data is not returned

  Scenario: Privilege escalation via API
    Given I am a regular member
    When I POST to /api/users/me/role with body {"role": "admin"}
    Then request is rejected
    And my role is unchanged
    And attempt is logged

  Scenario: Access admin API endpoints as user
    Given I am a regular user
    When I try to access /api/admin/users
    Then I get 403 Forbidden
    And admin data is not exposed

  Scenario: Modify other company's fund
    Given I am admin of Company A
    When I try to PUT /api/funds/999 (Company B's fund)
    Then I get 404 Not Found (not 403, to avoid enumeration)
    And fund is not modified

  # NEGATIVE TESTS: Input Validation Attacks
  Scenario: Oversized request body
    When I send POST with 100MB body
    Then request is rejected before full upload
    And I see 413 Payload Too Large

  Scenario: Malformed JSON
    When I send {"name": "test with unclosed JSON
    Then I get 400 Bad Request
    And error message doesn't expose internal details

  Scenario: Invalid UTF-8 characters
    When I send request with invalid UTF-8 bytes
    Then request is handled safely
    And either sanitized or rejected with clear error

  Scenario: Path traversal in file upload
    When I upload file named "../../../etc/passwd"
    Then filename is sanitized
    And file is saved safely (no path traversal)

  Scenario: Null byte injection
    When I enter "admin%00.txt" in filename
    Then null byte is removed or request rejected
    And no security bypass occurs
```

---

## Monitoring Tests

```gherkin
Feature: Production Monitoring
  As an operator
  I want monitoring and alerting
  So that I catch issues quickly

  # Sub-feature: Error Tracking
  Scenario: Errors sent to Sentry
    When an unhandled error occurs
    Then it is captured by Sentry
    And includes stack trace
    And includes user context

  Scenario: No errors for 24 hours
    Given production is stable
    When I check Sentry dashboard
    Then I see no new errors in 24 hours

  # Sub-feature: Health Checks
  Scenario: Health endpoint
    When I call /health
    Then I get 200 OK
    And response includes:
      | database: "connected" |
      | auth: "operational" |
      | version: "1.0.0" |

  # Sub-feature: Feedback Collection
  Scenario: Collect match feedback
    Given GPs provide thumbs up/down on matches
    When I view feedback dashboard
    Then I see:
      | Metric | Value |
      | Total Feedback | 500 |
      | Positive | 350 (70%) |
      | Negative | 150 (30%) |

  # NEGATIVE TESTS: Error Tracking Failures
  Scenario: Sentry service unavailable
    Given Sentry is temporarily down
    When an error occurs in production
    Then error is logged locally as fallback
    And application continues to function
    And errors are batched for later submission

  Scenario: Error flood protection
    Given 1000 of the same error occurs per minute
    When Sentry receives these errors
    Then errors are deduplicated/sampled
    And Sentry quota is not exhausted
    And alert is still triggered for new error type

  Scenario: Sensitive data in error context
    When an error includes user password in context
    Then password is scrubbed before sending to Sentry
    And sensitive fields are masked

  Scenario: Error in error handler
    When error tracking code itself fails
    Then original error is not lost
    And fallback logging captures both errors
    And application doesn't crash

  # NEGATIVE TESTS: Health Check Failures
  Scenario: Health check with database down
    Given database is unreachable
    When I call /health
    Then I get 503 Service Unavailable
    And response includes:
      | database: "disconnected" |
      | details: "Connection timeout" |
    And other services still report their status

  Scenario: Health check with partial failure
    Given OpenRouter is down but database is up
    When I call /health
    Then I get 200 OK (degraded)
    And response includes:
      | database: "connected" |
      | openrouter: "unavailable" |
      | status: "degraded" |

  Scenario: Health check timeout
    Given health check takes too long
    When /health doesn't respond in 5 seconds
    Then load balancer marks instance unhealthy
    And traffic is routed to other instances

  Scenario: Deep health check vs shallow health check
    When I call /health
    Then response is fast (< 100ms, shallow check)
    When I call /health?deep=true
    Then response includes actual DB query result
    And response may take longer (< 2 seconds)

  # NEGATIVE TESTS: Logging and Audit
  Scenario: Audit log write failure
    Given audit log storage is full
    When admin performs sensitive action
    Then action is blocked until logging works
    And error is escalated immediately
    And no audit trail gap is allowed

  Scenario: Log retention compliance
    Given logs older than 90 days exist
    When retention policy runs
    Then old logs are archived/deleted
    And compliance requirements are met
    And audit trail for active investigations is preserved

  Scenario: Sensitive data in logs
    When request includes credit card or SSN
    Then these are masked in all logs
    And only last 4 digits are visible if needed
    And PII compliance is maintained
```

---

## E2E: Admin Daily Workflow

```gherkin
Feature: Admin Daily Operations
  As a super admin
  I want to manage the platform
  So that everything runs smoothly

  Scenario: Morning admin routine
    Given I am a super admin

    # Check dashboard
    When I login and view admin dashboard
    Then I see overnight activity:
      | New users | 5 |
      | New funds | 2 |
      | Matches generated | 150 |

    # Check data quality
    When I go to Data Quality
    Then I see 12 LPs flagged for review

    # Review flagged LPs
    When I click first flagged LP
    And I see the issue and correction
    And I approve the correction
    Then LP is updated
    And flag is resolved

    # Process remaining queue
    When I process all 12 flagged items
    Then review queue is empty

    # Check system health
    When I go to System Health
    Then all services show "Healthy"
    And no Sentry errors overnight

    # Review new company request
    When I see a new company application
    And I review their details
    And I approve the company
    Then company is created
    And admin invitation is sent

  # NEGATIVE TESTS: Admin Workflow Errors
  Scenario: Admin dashboard unavailable
    Given I am a super admin
    When I login and dashboard fails to load
    Then I see error "Dashboard temporarily unavailable"
    And I can still navigate to specific admin sections
    And I can access emergency tools

  Scenario: Bulk operation fails partway
    Given I am processing 100 flagged LPs
    When operation fails at item 50
    Then I see "50 of 100 processed before error"
    And I see option to "Resume from item 51"
    And successfully processed items remain processed

  Scenario: Conflicting admin actions
    Given admin A is approving company "NewCo"
    And admin B is rejecting company "NewCo" simultaneously
    When both click submit
    Then first action wins
    And second admin sees "Company status already changed"
    And data integrity is maintained

  Scenario: Admin session timeout during operation
    Given I started a large import job
    When my session times out mid-operation
    Then import continues in background
    And I can re-login and see progress
    And operation is not duplicated

  Scenario: Admin makes destructive mistake
    Given I accidentally deleted wrong LP
    When I realize the mistake within seconds
    Then I can find deleted LP in "Recently Deleted" (soft delete)
    And I can restore it within 30 days
    And all relationships are preserved

  Scenario: System under maintenance
    Given platform is undergoing scheduled maintenance
    When admin tries to make changes
    Then I see "System in maintenance mode"
    And read-only access is available
    And no data modifications are permitted
```

---

## Edge Case Tests

```gherkin
Feature: Edge Cases and Boundary Conditions
  As a system
  I want to handle edge cases gracefully
  So that no scenario causes failure

  # Data Edge Cases
  Scenario: LP with maximum field lengths
    When I create LP with all fields at maximum length
    Then LP is created successfully
    And data is not truncated unexpectedly
    And display handles long text gracefully

  Scenario: LP with minimum/empty optional fields
    When I create LP with only required fields
    Then LP is created successfully
    And optional fields show appropriate defaults/placeholders

  Scenario: LP with Unicode characters
    When I create LP with name "Deutsche Bank AG"
    And headquarters in "Munchen"
    And contact in Japanese characters
    Then all Unicode is stored correctly
    And search works with Unicode
    And display renders correctly

  Scenario: LP with special characters in all fields
    When I create LP with ampersands, quotes, slashes
    Then characters are handled correctly
    And no injection vulnerabilities exist
    And display escapes appropriately

  Scenario: Zero AUM LP
    When I create LP with AUM of $0
    Then LP is created (valid edge case)
    And matching algorithms handle zero gracefully
    And no division by zero errors

  Scenario: Very large AUM
    When I create LP with AUM of $999,999,999,999,999
    Then numeric precision is maintained
    And display formats correctly (abbreviated)
    And calculations don't overflow

  # Timing Edge Cases
  Scenario: Action at exact midnight
    When I submit form at 23:59:59.999
    And server processes at 00:00:00.001
    Then date handling is consistent
    And audit logs show correct timestamps
    And daily counters handle boundary correctly

  Scenario: Leap second handling
    Given system encounters leap second
    When operations occur during leap second
    Then no duplicate timestamps occur
    And audit trail remains consistent

  Scenario: Timezone edge cases
    Given user is in timezone UTC-12
    And server is in UTC
    When user creates record at local midnight
    Then timestamps are stored in UTC
    And displayed back in user's timezone
    And date filters work correctly

  # Concurrent Operation Edge Cases
  Scenario: Two admins edit same LP simultaneously
    Given admin A loads LP profile
    And admin B loads same LP profile
    When both make different changes and save
    Then second save warns of conflict
    And merge resolution is available
    And no data is silently lost

  Scenario: User deleted while viewing their data
    Given admin is viewing user profile
    When another admin deletes that user
    And first admin clicks "Edit"
    Then I see "User no longer exists"
    And graceful error is shown

  Scenario: Company deleted while user logged in
    Given I am logged in as user of Company A
    When admin deletes Company A
    Then my session is invalidated
    And I see "Your company has been deactivated"
    And I am logged out gracefully

  # Empty/Null State Edge Cases
  Scenario: Search with no database records
    Given LP database is empty
    When I perform any search
    Then I see "No LPs in database"
    And I see option to import data
    And no errors occur

  Scenario: Dashboard with zero activity
    Given no activity in last 24 hours
    When admin views dashboard
    Then I see appropriate zero states
    And dashboard renders correctly
    And no "undefined" or NaN values

  Scenario: Analytics with no data
    Given new company with no funds or matches
    When I view analytics
    Then I see "Not enough data for analytics"
    And charts show empty state
    And no calculation errors
```

---

## Error Recovery Tests

```gherkin
Feature: Error Recovery and Resilience
  As a system
  I want to recover from errors gracefully
  So that users can continue working

  Scenario: Database connection recovery
    Given database connection is lost
    When connection is restored
    Then system automatically reconnects
    And pending operations are retried
    And user sees minimal disruption

  Scenario: External API recovery
    Given OpenRouter was unavailable
    When OpenRouter comes back online
    Then pending pitch generations resume
    And users are notified of completion
    And no duplicate generations occur

  Scenario: Partial page load failure
    Given dashboard main content loads
    But analytics widget fails
    When page renders
    Then main content is shown
    And failed widget shows "Unable to load"
    And user can manually refresh widget

  Scenario: Background job recovery
    Given import job was running
    When server restarts unexpectedly
    Then job status shows "Interrupted"
    And I can resume from last checkpoint
    And no data duplication occurs

  Scenario: Transaction rollback on error
    Given I am saving complex multi-table update
    When error occurs in second table update
    Then first table update is rolled back
    And data remains consistent
    And user can retry entire operation

  Scenario: Cache invalidation on error
    Given stale data is cached
    When I detect data inconsistency
    Then cache is invalidated
    And fresh data is fetched
    And user sees correct information
```
