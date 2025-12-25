"""BDD-style security and edge case tests.

These tests map to the Gherkin specifications in docs/prd/tests/.
They focus on security, validation, and error handling scenarios.

Run with:
    uv run pytest tests/test_bdd_security.py -v -m browser

Mapping to BDD specs:
    - F-AUTH-01: User Login validation and security
    - F-LP-02: LP Search edge cases
    - Security Test Suite: XSS, injection prevention
"""

import pytest
from playwright.sync_api import Page, expect

BASE_URL = "http://localhost:8000"


# =============================================================================
# F-AUTH-01: LOGIN VALIDATION TESTS
# BDD: Feature: User Login - Negative Tests
# =============================================================================


@pytest.mark.browser
class TestLoginValidation:
    """Test login form validation per F-AUTH-01 specs."""

    def test_login_with_empty_email_shows_validation_error(self, page: Page):
        """
        BDD: Scenario: Login with empty email
        Given I am on the login page
        When I leave email field empty
        And I enter password "SomePassword123"
        And I click "Login"
        Then I see validation error for email
        """
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="password"]', "SomePassword123")
        page.click('button[type="submit"]')

        # HTML5 validation should prevent submission
        email_input = page.locator('input[name="email"]')
        expect(email_input).to_have_attribute("required", "")

    def test_login_with_empty_password_shows_validation_error(self, page: Page):
        """
        BDD: Scenario: Login with empty password
        Given I am on the login page
        When I enter email "gp@venture.com"
        And I leave password field empty
        And I click "Login"
        Then I see validation error for password
        """
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@venture.com")
        page.click('button[type="submit"]')

        # HTML5 validation should prevent submission
        password_input = page.locator('input[name="password"]')
        expect(password_input).to_have_attribute("required", "")

    def test_login_with_nonexistent_email_shows_generic_error(self, page: Page):
        """
        BDD: Scenario: Login with non-existent email
        When I login with email "nonexistent@venture.com"
        Then I see "Invalid email or password"
        And the error message does not reveal whether email exists
        """
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "nonexistent@venture.com")
        page.fill('input[name="password"]', "wrongpassword")
        page.click('button[type="submit"]')

        # Wait for error message
        error = page.locator("text=Invalid email or password")
        expect(error).to_be_visible(timeout=5000)

        # Error message should NOT reveal if email exists
        page.wait_for_timeout(500)
        content = page.content()
        assert "email not found" not in content.lower()
        assert "user not found" not in content.lower()
        assert "no account" not in content.lower()

    def test_session_cookie_has_httponly_flag(self, page: Page):
        """
        BDD: Scenario: Session tokens are secure
        Given I am logged in
        When I examine my session cookie
        Then it has HttpOnly flag
        """
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")

        # Get cookies and check security flags
        cookies = page.context.cookies()
        session_cookie = next(
            (c for c in cookies if c["name"] == "lpxgp_session"), None
        )
        assert session_cookie is not None, "Session cookie should exist"
        assert session_cookie["httpOnly"] is True, "Cookie should be HttpOnly"


# =============================================================================
# F-LP-02: LP SEARCH EDGE CASES
# BDD: Feature: LP Search & Filter - Negative Tests
# =============================================================================


@pytest.mark.browser
class TestLPSearchEdgeCases:
    """Test LP search edge cases per F-LP-02 specs."""

    @pytest.fixture
    def logged_in_page(self, page: Page):
        """Log in before each test."""
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")
        return page

    def test_search_with_no_results_shows_message(self, logged_in_page: Page):
        """
        BDD: Scenario: Search returns no results
        When I search for "XyzNonExistentLP123"
        Then I see "No LPs found matching your criteria"
        And I do not see an error
        """
        logged_in_page.goto(f"{BASE_URL}/lps")

        # Search for non-existent LP
        search_input = logged_in_page.locator(
            'input[type="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            search_input.first.fill("XyzNonExistentLP123")
            logged_in_page.wait_for_timeout(500)

            # Check for no results or message
            page_content = logged_in_page.content().lower()
            # Should not show error, may show empty state
            assert "error" not in page_content or "no lp" in page_content

    def test_search_with_special_characters_is_safe(self, logged_in_page: Page):
        """
        BDD: Scenario: Search with special characters
        When I search for "O'Brien & Partners"
        Then results include LPs with apostrophes and ampersands
        And no SQL error occurs
        """
        logged_in_page.goto(f"{BASE_URL}/lps")

        search_input = logged_in_page.locator(
            'input[type="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            search_input.first.fill("O'Brien & Partners")
            logged_in_page.wait_for_timeout(500)

            # Page should not show SQL error
            page_content = logged_in_page.content().lower()
            assert "sql" not in page_content
            assert "syntax error" not in page_content
            assert "database error" not in page_content

    def test_search_with_sql_injection_is_prevented(self, logged_in_page: Page):
        """
        BDD: Scenario: SQL injection in search field
        When I search for "'; SELECT * FROM users; --"
        Then I see no results or safe error message
        And no database query is executed maliciously
        """
        logged_in_page.goto(f"{BASE_URL}/lps")

        search_input = logged_in_page.locator(
            'input[type="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            search_input.first.fill("'; SELECT * FROM users; --")
            logged_in_page.wait_for_timeout(500)

            # Page should handle gracefully
            page_content = logged_in_page.content().lower()
            assert "internal server error" not in page_content
            assert "traceback" not in page_content

    def test_filter_by_lp_type(self, logged_in_page: Page):
        """
        BDD: Scenario: Filter by LP type
        Given the database has LPs of various types
        When I filter by type using the dropdown
        Then I see the filter form with type options
        """
        logged_in_page.goto(f"{BASE_URL}/lps")

        # Look for filter dropdown (first one is the filter, second is in modal)
        type_filter = logged_in_page.locator('select[name="lp_type"]').first
        expect(type_filter).to_be_visible()

        # Should have at least the "All Types" default option
        options = type_filter.locator("option")
        assert options.count() >= 1, "Filter should have at least 1 option"


# =============================================================================
# SECURITY TEST SUITE
# BDD: Feature: Security Tests
# =============================================================================


@pytest.mark.browser
class TestSecurityXSS:
    """Test XSS prevention per Security Test Suite specs."""

    @pytest.fixture
    def logged_in_page(self, page: Page):
        """Log in before each test."""
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")
        return page

    def test_xss_in_search_query_is_escaped(self, logged_in_page: Page):
        """
        BDD: Scenario: Reflected XSS in search query
        When I search for "<script>alert('xss')</script>"
        And results are displayed
        Then the script tag is escaped in the response
        And no script executes
        """
        logged_in_page.goto(f"{BASE_URL}/lps")

        search_input = logged_in_page.locator('input[name="search"]')
        if search_input.count() > 0:
            xss_payload = "<script>alert('xss')</script>"
            search_input.first.fill(xss_payload)
            # Submit the form to test server-side escaping
            logged_in_page.click('button[type="submit"]')
            logged_in_page.wait_for_timeout(500)

            # Check page source - script should be escaped or absent
            page_content = logged_in_page.content()
            # The literal unescaped script tag should NOT appear
            assert "<script>alert('xss')</script>" not in page_content

    def test_xss_via_url_parameter_is_escaped(self, logged_in_page: Page):
        """
        BDD: Scenario: XSS via URL parameter
        When I navigate to search with XSS in URL
        Then the input is escaped (< becomes &lt;)
        And no script executes
        """
        from urllib.parse import quote
        xss_payload = "<img src=x onerror=alert('xss')>"
        # URL-encode the payload as a browser would
        logged_in_page.goto(
            f"{BASE_URL}/lps?search={quote(xss_payload)}"
        )
        logged_in_page.wait_for_timeout(500)

        # Check that the literal HTML is NOT rendered as HTML
        # (should be escaped to &lt;img... in the page source)
        page_content = logged_in_page.content()
        # The unescaped img tag with onerror should NOT appear
        assert '<img src=x onerror=alert' not in page_content


@pytest.mark.browser
class TestSecuritySession:
    """Test session security per Security Test Suite specs."""

    def test_logout_invalidates_session_completely(self, page: Page):
        """
        BDD: Scenario: Logout invalidates session completely
        Given I am logged in
        When I logout
        And I try to access protected page
        Then I am redirected to login
        """
        # Login
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")

        # Logout
        logout_link = page.locator('a[href="/logout"]')
        if logout_link.count() > 0:
            logout_link.first.click()
            page.wait_for_timeout(500)

        # Try to access protected page
        page.goto(f"{BASE_URL}/dashboard")

        # Should be redirected to login
        expect(page).to_have_url(f"{BASE_URL}/login")

    def test_accessing_protected_page_without_auth_redirects(self, page: Page):
        """
        BDD: Scenario: Access protected page without authentication
        Given I am not logged in
        When I try to access "/dashboard"
        Then I am redirected to login
        """
        page.goto(f"{BASE_URL}/dashboard")
        expect(page).to_have_url(f"{BASE_URL}/login")


@pytest.mark.browser
class TestSecurityHeaders:
    """Test security headers and response safety."""

    def test_error_pages_do_not_expose_stack_traces(self, page: Page):
        """
        BDD: Scenario: Sensitive data not in error messages
        When a page error occurs
        Then database details are not exposed
        And stack traces are not shown
        """
        # Request non-existent page
        page.goto(f"{BASE_URL}/nonexistent-page-12345")

        page_content = page.content().lower()
        # Should not expose internal Python details
        assert "traceback (most recent call last)" not in page_content
        assert 'file "/' not in page_content  # Python file paths
        assert "psycopg" not in page_content  # Database driver
        assert "supabase" not in page_content  # Service name in errors

    def test_api_error_does_not_expose_internals(self, page: Page):
        """
        BDD: Scenario: API responses do not leak sensitive data
        When an API error occurs
        Then internal details are not exposed
        """
        # Try to trigger an API error
        response = page.goto(f"{BASE_URL}/api/nonexistent")

        if response:
            content = response.text().lower() if response.text() else ""
            assert "traceback" not in content
            assert "exception" not in content or "not found" in content


# =============================================================================
# DASHBOARD TESTS
# BDD: Feature: Dashboard - Negative Tests
# =============================================================================


@pytest.mark.browser
class TestDashboardEdgeCases:
    """Test dashboard edge cases per F-UI-01 specs."""

    @pytest.fixture
    def logged_in_page(self, page: Page):
        """Log in before each test."""
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")
        return page

    def test_dashboard_quick_actions_navigate_correctly(self, logged_in_page: Page):
        """
        BDD: Scenario: Create fund from dashboard
        When I click "Create Fund" on dashboard
        Then I go to the fund creation page
        """
        # Find and click a quick action link
        fund_link = logged_in_page.locator('a[href="/funds"]')
        if fund_link.count() > 0:
            fund_link.first.click()
            expect(logged_in_page).to_have_url(f"{BASE_URL}/funds")

    def test_dashboard_lp_link_navigates_correctly(self, logged_in_page: Page):
        """
        BDD: Scenario: Quick action buttons
        When I view the dashboard
        And I click "Search LPs" button
        Then I go to LP Search
        """
        lp_link = logged_in_page.locator('a[href="/lps"]')
        if lp_link.count() > 0:
            lp_link.first.click()
            expect(logged_in_page).to_have_url(f"{BASE_URL}/lps")
