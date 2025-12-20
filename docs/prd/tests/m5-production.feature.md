# Milestone 5: Production Tests
## "Production-ready with admin"

---

## F-AUTH-04: Admin Panel [P0]

```gherkin
Feature: Admin Panel
  As a super admin
  I want to manage the platform
  So that I can support all users

  # Sub-feature: Company Management
  Scenario: View all companies
    Given I am a super admin
    When I go to Admin > Companies
    Then I see all companies with:
      | Company | Users | Funds | Created |
      | Acme Capital | 5 | 3 | 2024-01-15 |
      | Beta Ventures | 8 | 5 | 2024-02-20 |

  Scenario: Create new company
    When I click "Add Company"
    And I enter:
      | Name | New Partners |
      | Admin Email | admin@newpartners.com |
    And I click "Create"
    Then company is created
    And invitation email is sent to admin

  Scenario: Edit company settings
    When I select a company
    Then I can edit company name
    And I can adjust company limits
    And I can enable/disable features

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
  Scenario: Browse all LPs
    When I go to Admin > LPs
    Then I see all LPs in the database
    And I can search and filter
    And I can see data quality scores

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
```
