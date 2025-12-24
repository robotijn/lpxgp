# Security Test Specifications

[← Back to Test Index](../test-specifications.md)

---

## Overview

These test specifications cover security controls implemented in the security remediation phases. Each scenario should be tested during development and in CI/CD.

---

## 1. Authentication & Account Lockout

### Feature: Account Lockout Protection

```gherkin
Feature: Account lockout after failed login attempts
  As a security measure
  The system should lock accounts after repeated failed logins
  To prevent brute force attacks

  Background:
    Given a valid user account "user@example.com"

  Scenario: Successful login resets failure count
    Given the user has 3 failed login attempts
    When they login with correct credentials
    Then they should be authenticated
    And the failure count should reset to 0

  Scenario: Account locks after 5 failed attempts
    Given the user has 4 failed login attempts
    When they attempt login with wrong password
    Then they should see "Account temporarily locked"
    And the lockout duration should be 30 minutes

  Scenario: Locked account cannot login with correct password
    Given the user account is locked
    When they attempt login with correct password
    Then they should see "Account temporarily locked"
    And they should see the remaining lockout time

  Scenario: Lockout expires after duration
    Given the user account was locked 31 minutes ago
    When they attempt login with correct password
    Then they should be authenticated

  Scenario: IP-based rate limiting
    Given 5 failed login attempts from IP "192.168.1.100"
    When another login attempt comes from that IP
    Then the request should be rate limited (429)
    And the response should include Retry-After header
```

---

## 2. CSRF Protection

### Feature: Cross-Site Request Forgery Prevention

```gherkin
Feature: CSRF token validation
  As a security measure
  State-changing requests require valid CSRF tokens
  To prevent cross-site request forgery attacks

  Background:
    Given an authenticated user session
    And a valid CSRF token in the cookie

  Scenario: Request without CSRF token is rejected
    When a POST request is made without X-CSRF-Token header
    Then the response should be 403 Forbidden
    And the error should be "CSRF validation failed"

  Scenario: Request with invalid CSRF token is rejected
    When a POST request is made with an invalid CSRF token
    Then the response should be 403 Forbidden

  Scenario: Request with valid CSRF token succeeds
    When a POST request is made with the valid CSRF token
    Then the request should proceed normally

  Scenario: CSRF token in form field works
    When a POST with content-type form-urlencoded
    And the csrf_token field matches the cookie
    Then the request should proceed normally

  Scenario: GET requests don't require CSRF token
    When a GET request is made without CSRF token
    Then the request should succeed

  Scenario: Webhook endpoints are exempt from CSRF
    When a POST to /api/webhooks/stripe is made without CSRF
    Then the request should proceed (validated by signature)
```

---

## 3. Rate Limiting

### Feature: Rate Limit Enforcement

```gherkin
Feature: API rate limiting
  As a platform operator
  I want to enforce rate limits per endpoint
  To prevent abuse and ensure fair usage

  Scenario: Match generation rate limit (10/min per org)
    Given an authenticated user from org "acme-capital"
    When they make 11 requests to POST /matches/generate in 1 minute
    Then the 11th request should return 429
    And the response should include rate limit headers
    And retry-after should be approximately 60 seconds

  Scenario: LP search rate limit (100/min per user)
    Given an authenticated user "analyst@acme.com"
    When they make 101 search requests in 1 minute
    Then the 101st request should return 429

  Scenario: Rate limits are scoped correctly
    Given user A from org "acme" at their rate limit
    And user B from org "beta" making first request
    Then user B's request should succeed

  Scenario: Rate limit headers are informative
    When a rate-limited request is made
    Then response should include X-RateLimit-Limit
    And response should include X-RateLimit-Remaining
    And response should include X-RateLimit-Reset
```

---

## 4. Row-Level Security (RLS)

### Feature: Organization Data Isolation

```gherkin
Feature: RLS prevents cross-org data access
  As a multi-tenant platform
  Users should only see their own organization's data
  Unless they have privileged access

  Background:
    Given org "acme-capital" with user "alice@acme.com"
    And org "beta-ventures" with user "bob@beta.com"
    And a match record belonging to "acme-capital"

  Scenario: User cannot see other org's matches
    Given I am logged in as "bob@beta.com"
    When I request GET /matches
    Then the acme-capital match should not be in the response

  Scenario: User cannot access other org's match by ID
    Given I am logged in as "bob@beta.com"
    And I know the UUID of acme-capital's match
    When I request GET /matches/{acme-match-id}
    Then the response should be 404 Not Found

  Scenario: Fund Admin can see all matches
    Given I am logged in as a Fund Admin
    When I request GET /matches with org filter
    Then I should see matches from all organizations

  Scenario: User cannot update other org's data
    Given I am logged in as "bob@beta.com"
    When I try to PATCH /matches/{acme-match-id}
    Then the response should be 404 or 403

  Scenario: Single employment enforcement
    Given user "charlie@company.com" works at "acme-capital"
    When an admin tries to add them to "beta-ventures"
    Then the operation should fail
    With error "User already has current employment"
```

### Feature: LP Profile Access Control

```gherkin
Feature: LP profile access is audited
  As sensitive market data
  LP profile access should be controlled and logged

  Scenario: LP profile access is logged
    Given I am logged in as a regular user
    When I view LP profile "calpers"
    Then an audit log entry should be created
    With my user ID and the LP profile ID

  Scenario: Bulk LP access triggers alert
    Given I am logged in as a regular user
    When I view 50+ LP profiles in 10 minutes
    Then the access pattern should be flagged
    For review by a Fund Admin
```

---

## 5. Input Validation

### Feature: SQL Injection Prevention

```gherkin
Feature: SQL injection attacks are prevented
  As a security measure
  All user input should be parameterized
  To prevent SQL injection attacks

  Scenario Outline: SQL injection in search filters
    Given I am authenticated
    When I search LPs with filter "<malicious_input>"
    Then the query should be safely parameterized
    And no SQL error should be exposed
    And the response should be empty or valid data

    Examples:
      | malicious_input |
      | '; DROP TABLE lp_profiles;-- |
      | ' OR '1'='1 |
      | 1; SELECT * FROM users-- |
      | UNION SELECT password FROM users-- |

  Scenario: Error messages don't expose SQL
    Given I am authenticated
    When I submit a malformed query parameter
    Then the error should be generic
    And should not contain SQL syntax
    And should not contain table names
```

### Feature: XSS Prevention

```gherkin
Feature: Cross-site scripting prevention
  As a security measure
  User input and AI-generated content should be sanitized
  To prevent XSS attacks

  Scenario: Script tags in user input are escaped
    Given I am creating a touchpoint
    When I enter "<script>alert('xss')</script>" in the summary
    Then the saved content should have escaped HTML entities
    And when rendered, it should display as text, not execute

  Scenario: AI-generated pitch content is safe
    Given an AI-generated pitch containing HTML
    When the pitch is displayed in the UI
    Then Jinja2 autoescaping should prevent execution
    And the content should be visually correct

  Scenario: SVG-based XSS is prevented
    Given I upload an SVG image
    When the SVG contains embedded JavaScript
    Then the image should be rejected or sanitized
```

---

## 6. Error Handling

### Feature: Error Information Leakage Prevention

```gherkin
Feature: Errors don't expose sensitive information
  As a security measure
  Error messages should be sanitized
  To prevent information disclosure

  Scenario: Database errors are sanitized
    Given a database error occurs
    When the error is returned to the client
    Then it should not contain SQL queries
    And should not contain database connection strings
    And should not contain table/column names
    And should include a request ID for support

  Scenario: Stack traces are not exposed
    Given an unhandled exception occurs
    When the error is returned to the client
    Then it should not contain file paths
    And should not contain stack trace
    And should say "An unexpected error occurred"

  Scenario: Validation errors are safe
    Given I submit invalid data with a password field
    When the validation error is returned
    Then the password value should not be included
    And the field name should be sanitized

  Scenario: Rate limit errors are informative but safe
    Given I am rate limited
    When the 429 error is returned
    Then it should include retry-after
    And should not expose internal rate limit keys
```

---

## 7. File Upload Security

### Feature: Secure File Uploads

```gherkin
Feature: File upload validation
  As a security measure
  File uploads should be strictly validated
  To prevent malicious file attacks

  Scenario: Only allowed extensions accepted
    When I upload a file with extension ".exe"
    Then the upload should be rejected
    With error "File type not allowed"

  Scenario: File size limit enforced
    When I upload a PDF larger than 50MB
    Then the upload should be rejected
    With error "File too large"

  Scenario: MIME type validation
    When I upload a .pdf file that is actually a .exe
    Then the upload should be rejected
    Based on content inspection, not just extension

  Scenario: Uploaded files are stored safely
    When I upload a valid PDF
    Then it should be stored with a random UUID name
    And should not be directly accessible via URL
    And should require authentication to download
```

---

## 8. Session Security

### Feature: Session Management

```gherkin
Feature: Secure session handling
  As a security measure
  Sessions should be properly managed
  To prevent session-based attacks

  Scenario: Session timeout after inactivity
    Given I have been inactive for 60 minutes
    When I make an API request
    Then I should be logged out
    And need to re-authenticate

  Scenario: Session invalidated on logout
    Given I am logged in with a valid session
    When I click logout
    Then my session token should be invalidated
    And using the old token should fail

  Scenario: Concurrent session limit
    Given I am logged in on device A
    When I login on device B
    Then both sessions should be valid (or policy-based limit)
    And I should see my active sessions list

  Scenario: Session cookie is secure
    When I login successfully
    Then the session cookie should have HttpOnly flag
    And should have Secure flag
    And should have SameSite=Strict
```

---

## Test Execution

### Unit Tests
```bash
uv run pytest tests/security/ -v
```

### Integration Tests
```bash
uv run pytest tests/integration/security/ -v
```

### Manual Testing Checklist
- [ ] Attempt login with SQL injection in email field
- [ ] Attempt XSS in touchpoint summary
- [ ] Verify CSRF token is required for POST
- [ ] Verify rate limits with curl loop
- [ ] Verify error messages don't expose internals
- [ ] Verify file upload restrictions
- [ ] Test account lockout with wrong passwords

---

## Related Documents

- [Threat Model](../../security/threat-model.md)
- [Security Findings](../../security/SECURITY-FINDINGS.md)
- [NFR Security Requirements](../nfr.md)
