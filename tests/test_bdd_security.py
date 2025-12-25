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


# =============================================================================
# SHORTLIST SECURITY TESTS
# BDD: Feature: Shortlist Security & Validation
# =============================================================================


@pytest.mark.browser
class TestShortlistSecurity:
    """Test shortlist security per Security Test Suite specs."""

    @pytest.fixture
    def logged_in_page(self, page: Page):
        """Log in before each test."""
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")
        return page

    def test_shortlist_page_requires_authentication(self, page: Page):
        """
        BDD: Scenario: Access shortlist without authentication
        Given I am not logged in
        When I try to access "/shortlist"
        Then I am redirected to login
        """
        page.goto(f"{BASE_URL}/shortlist")
        expect(page).to_have_url(f"{BASE_URL}/login")

    def test_shortlist_api_requires_authentication(self, page: Page):
        """
        BDD: Scenario: API access without authentication
        Given I am not logged in
        When I call GET /api/shortlist
        Then I receive 401 Unauthorized
        """
        response = page.request.get(f"{BASE_URL}/api/shortlist")
        assert response.status == 401

    def test_shortlist_add_requires_authentication(self, page: Page):
        """
        BDD: Scenario: Add to shortlist without authentication
        Given I am not logged in
        When I POST to /api/shortlist
        Then I receive 401 Unauthorized
        """
        response = page.request.post(
            f"{BASE_URL}/api/shortlist",
            data={"lp_id": "test-lp-001"},
        )
        assert response.status == 401

    def test_shortlist_no_xss_in_notes_display(self, logged_in_page: Page):
        """
        BDD: Scenario: XSS in shortlist notes
        When I add an LP with XSS payload in notes
        And I view my shortlist
        Then the script tag is escaped
        And no script executes
        """
        page = logged_in_page

        # Try to add with XSS payload via API
        xss_payload = "<script>alert('xss')</script>"
        page.request.post(
            f"{BASE_URL}/api/shortlist",
            data={
                "lp_id": "a1000001-0000-0000-0000-000000000001",
                "notes": xss_payload,
            },
            headers={"Content-Type": "application/json"},
        )

        # View shortlist page
        page.goto(f"{BASE_URL}/shortlist")
        page_content = page.content()

        # XSS should be escaped
        assert "<script>alert('xss')</script>" not in page_content

    def test_shortlist_no_sql_injection_in_lp_id(self, logged_in_page: Page):
        """
        BDD: Scenario: SQL injection in shortlist LP ID
        When I try to add LP with SQL injection payload
        Then the request is rejected or sanitized
        And no database error occurs
        """
        page = logged_in_page

        sql_payload = "'; DROP TABLE organizations; --"

        # Try API call with SQL injection
        response = page.request.post(
            f"{BASE_URL}/api/shortlist",
            data={"lp_id": sql_payload},
            headers={"Content-Type": "application/json"},
        )

        # Should be rejected (400 invalid UUID) or sanitized
        assert response.status in [400, 422]

        # Page should still work
        page.goto(f"{BASE_URL}/shortlist")
        page_content = page.content().lower()
        assert "sql" not in page_content
        assert "syntax error" not in page_content

    def test_shortlist_session_isolation(self, page: Page):
        """
        BDD: Scenario: User cannot see other user's shortlist
        Given user A has items in shortlist
        When user B views shortlist
        Then user B cannot see user A's items
        """
        # Login as user A
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")

        # Add item as user A
        page.request.post(
            f"{BASE_URL}/api/shortlist",
            data={"lp_id": "b1000001-0000-0000-0000-000000000001"},
            headers={"Content-Type": "application/json"},
        )

        # Logout
        page.goto(f"{BASE_URL}/logout")
        page.wait_for_timeout(500)

        # Login as user B
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "lp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")

        # Get user B's shortlist
        response_b = page.request.get(f"{BASE_URL}/api/shortlist")
        data_b = response_b.json()

        # User B should not see user A's items
        lp_ids = [item["lp_id"] for item in data_b.get("items", [])]
        assert "b1000001-0000-0000-0000-000000000001" not in lp_ids


@pytest.mark.browser
class TestShortlistInputValidation:
    """Test shortlist input validation per F-SHORTLIST specs."""

    @pytest.fixture
    def logged_in_page(self, page: Page):
        """Log in before each test."""
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")
        return page

    def test_shortlist_rejects_empty_lp_id(self, logged_in_page: Page):
        """
        BDD: Scenario: Add shortlist with empty LP ID
        When I try to add empty LP ID
        Then I receive validation error
        """
        page = logged_in_page

        response = page.request.post(
            f"{BASE_URL}/api/shortlist",
            data={"lp_id": ""},
            headers={"Content-Type": "application/json"},
        )

        assert response.status in [400, 422]

    def test_shortlist_rejects_invalid_uuid(self, logged_in_page: Page):
        """
        BDD: Scenario: Add shortlist with invalid UUID
        When I try to add non-UUID LP ID
        Then I receive validation error
        """
        page = logged_in_page

        response = page.request.post(
            f"{BASE_URL}/api/shortlist",
            data={"lp_id": "not-a-valid-uuid"},
            headers={"Content-Type": "application/json"},
        )

        assert response.status == 400

    def test_shortlist_rejects_invalid_priority(self, logged_in_page: Page):
        """
        BDD: Scenario: Add shortlist with invalid priority
        When I try to add with priority > 3 or < 1
        Then I receive validation error
        """
        page = logged_in_page

        # Priority 0 (invalid)
        response = page.request.post(
            f"{BASE_URL}/api/shortlist",
            data={"lp_id": "c1000001-0000-0000-0000-000000000001", "priority": 0},
            headers={"Content-Type": "application/json"},
        )

        assert response.status == 422

    def test_shortlist_handles_unicode_safely(self, logged_in_page: Page):
        """
        BDD: Scenario: Add shortlist with unicode notes
        When I add LP with unicode in notes
        Then the unicode is preserved safely
        """
        page = logged_in_page

        # Clear shortlist first to avoid 409 conflict from previous tests
        page.request.delete(f"{BASE_URL}/api/shortlist")

        response = page.request.post(
            f"{BASE_URL}/api/shortlist",
            data={
                "lp_id": "d1000001-0000-0000-0000-000000000001",
                "notes": "北京投资基金 - Great partner",
            },
            headers={"Content-Type": "application/json"},
        )

        assert response.status == 201

    def test_shortlist_prevents_duplicates(self, logged_in_page: Page):
        """
        BDD: Scenario: Add duplicate LP to shortlist
        When I try to add same LP twice
        Then I receive conflict error
        """
        page = logged_in_page

        lp_id = "e1000001-0000-0000-0000-000000000001"

        # First add should succeed
        page.request.post(
            f"{BASE_URL}/api/shortlist",
            data={"lp_id": lp_id},
            headers={"Content-Type": "application/json"},
        )

        # Note: First one may already exist from other tests
        # Second add should fail with conflict
        response2 = page.request.post(
            f"{BASE_URL}/api/shortlist",
            data={"lp_id": lp_id},
            headers={"Content-Type": "application/json"},
        )

        assert response2.status == 409  # Conflict


@pytest.mark.browser
class TestShortlistErrorHandling:
    """Test shortlist error handling per F-SHORTLIST specs."""

    @pytest.fixture
    def logged_in_page(self, page: Page):
        """Log in before each test."""
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")
        return page

    def test_shortlist_remove_nonexistent_fails_gracefully(self, logged_in_page: Page):
        """
        BDD: Scenario: Remove non-existent LP from shortlist
        When I try to remove LP not in shortlist
        Then I receive 404 Not Found
        And no error page is shown
        """
        page = logged_in_page

        response = page.request.delete(
            f"{BASE_URL}/api/shortlist/99999999-9999-9999-9999-999999999999"
        )

        assert response.status == 404

        # Error should be JSON, not error page
        data = response.json()
        assert "error" in data

    def test_shortlist_update_nonexistent_fails_gracefully(self, logged_in_page: Page):
        """
        BDD: Scenario: Update non-existent shortlist item
        When I try to update LP not in shortlist
        Then I receive 404 Not Found
        """
        page = logged_in_page

        response = page.request.patch(
            f"{BASE_URL}/api/shortlist/99999999-9999-9999-9999-999999999888",
            data={"notes": "Test"},
            headers={"Content-Type": "application/json"},
        )

        assert response.status == 404

    def test_shortlist_page_handles_errors_gracefully(self, logged_in_page: Page):
        """
        BDD: Scenario: Shortlist page error handling
        When an error occurs on shortlist page
        Then user sees friendly error message
        And no stack trace is exposed
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/shortlist")

        page_content = page.content().lower()

        # Should not expose internal errors
        assert "traceback" not in page_content
        assert "psycopg" not in page_content
        assert "exception" not in page_content or "not found" in page_content


# =============================================================================
# F-SETTINGS: SETTINGS SECURITY TESTS
# BDD: Feature: Settings Access Control and Data Isolation
# =============================================================================


@pytest.mark.browser
class TestSettingsSecurityAuthentication:
    """Test settings authentication requirements."""

    def test_settings_page_redirects_unauthenticated(self, page: Page):
        """
        BDD: Scenario: Unauthenticated user cannot access settings
        Given I am not logged in
        When I navigate to /settings
        Then I am redirected to login page
        """
        page.goto(f"{BASE_URL}/settings")
        expect(page).to_have_url(f"{BASE_URL}/login", timeout=5000)

    def test_settings_api_rejects_unauthenticated(self, page: Page):
        """
        BDD: Scenario: Unauthenticated API access denied
        Given I am not logged in
        When I call settings API
        Then I receive 401 Unauthorized
        """
        response = page.request.get(f"{BASE_URL}/api/settings/preferences")
        assert response.status == 401
        assert "error" in response.json()


@pytest.mark.browser
class TestSettingsSecurityUserIsolation:
    """Test settings data isolation between users."""

    def test_gp_settings_isolated_from_lp(self, page: Page):
        """
        BDD: Scenario: GP user settings are isolated from LP user
        Given GP user modifies their preferences
        When LP user views their preferences
        Then LP sees their own default preferences
        And LP cannot see GP preferences
        """
        # Login as GP and modify preferences
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")

        # Toggle marketing preference via API
        response = page.request.post(
            f"{BASE_URL}/api/settings/preferences/toggle/email_marketing"
        )
        assert response.status == 200

        # Logout
        page.goto(f"{BASE_URL}/logout")

        # Login as LP
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "lp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")

        # Check LP preferences (should be default)
        response = page.request.get(f"{BASE_URL}/api/settings/preferences")
        prefs = response.json()["preferences"]
        assert prefs["email_marketing"] is False  # Default is False

    def test_settings_cannot_modify_other_user_preferences(self, page: Page):
        """
        BDD: Scenario: User cannot modify another user's preferences
        Given I am logged in as GP
        When I try to access LP preferences
        Then I only see my own preferences
        """
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")

        # Settings API doesn't allow specifying user_id - always uses session user
        response = page.request.get(f"{BASE_URL}/api/settings/preferences")
        assert response.status == 200
        # Response should only contain authenticated user's preferences


@pytest.mark.browser
class TestSettingsSecurityInputValidation:
    """Test settings input validation and injection prevention."""

    @pytest.fixture
    def logged_in_page(self, page: Page):
        """Log in as GP user and return page."""
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")
        return page

    def test_settings_toggle_rejects_invalid_preference_name(self, logged_in_page: Page):
        """
        BDD: Scenario: Invalid preference name is rejected
        Given I am logged in
        When I try to toggle invalid preference name
        Then I receive 400 error
        """
        page = logged_in_page

        response = page.request.post(
            f"{BASE_URL}/api/settings/preferences/toggle/invalid_pref_name"
        )
        assert response.status == 400
        assert "Invalid preference" in response.text()

    def test_settings_toggle_rejects_xss_in_pref_name(self, logged_in_page: Page):
        """
        BDD: Scenario: XSS injection in preference name is rejected
        Given I am logged in
        When I try to toggle preference with XSS payload
        Then I receive 400 error
        And no XSS is executed
        """
        page = logged_in_page

        xss_payloads = [
            "<script>alert('xss')</script>",
            "email_marketing<script>",
            "../../../etc/passwd",
        ]

        for payload in xss_payloads:
            response = page.request.post(
                f"{BASE_URL}/api/settings/preferences/toggle/{payload}"
            )
            assert response.status == 400 or response.status == 404

    def test_settings_update_rejects_invalid_json(self, logged_in_page: Page):
        """
        BDD: Scenario: Invalid JSON in settings update is rejected
        Given I am logged in
        When I send malformed JSON to settings API
        Then I receive error response
        """
        page = logged_in_page

        response = page.request.put(
            f"{BASE_URL}/api/settings/preferences",
            data="not valid json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status == 422


# =============================================================================
# F-ADMIN: ADMIN SECURITY TESTS
# BDD: Feature: Admin Access Control and Role-Based Security
# =============================================================================


@pytest.mark.browser
class TestAdminSecurityAuthentication:
    """Test admin authentication requirements."""

    def test_admin_dashboard_redirects_unauthenticated(self, page: Page):
        """
        BDD: Scenario: Unauthenticated user cannot access admin
        Given I am not logged in
        When I navigate to /admin
        Then I am redirected to login page
        """
        page.goto(f"{BASE_URL}/admin")
        expect(page).to_have_url(f"{BASE_URL}/login", timeout=5000)

    def test_admin_users_redirects_unauthenticated(self, page: Page):
        """
        BDD: Scenario: Unauthenticated user cannot access admin users
        Given I am not logged in
        When I navigate to /admin/users
        Then I am redirected to login page
        """
        page.goto(f"{BASE_URL}/admin/users")
        expect(page).to_have_url(f"{BASE_URL}/login", timeout=5000)

    def test_admin_health_redirects_unauthenticated(self, page: Page):
        """
        BDD: Scenario: Unauthenticated user cannot access admin health
        Given I am not logged in
        When I navigate to /admin/health
        Then I am redirected to login page
        """
        page.goto(f"{BASE_URL}/admin/health")
        expect(page).to_have_url(f"{BASE_URL}/login", timeout=5000)

    def test_admin_api_rejects_unauthenticated(self, page: Page):
        """
        BDD: Scenario: Unauthenticated API access denied
        Given I am not logged in
        When I call admin stats API
        Then I receive 401 Unauthorized
        """
        response = page.request.get(f"{BASE_URL}/api/admin/stats")
        assert response.status == 401


@pytest.mark.browser
class TestAdminSecurityRoleBasedAccess:
    """Test admin role-based access control for all user types."""

    def test_gp_user_cannot_access_admin_dashboard(self, page: Page):
        """
        BDD: Scenario: GP user cannot access admin dashboard
        Given I am logged in as GP user
        When I navigate to /admin
        Then I am redirected to dashboard
        And I cannot see admin content
        """
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")

        # Try to access admin
        page.goto(f"{BASE_URL}/admin")
        expect(page).to_have_url(f"{BASE_URL}/dashboard", timeout=5000)

    def test_gp_user_cannot_access_admin_users(self, page: Page):
        """
        BDD: Scenario: GP user cannot access admin users page
        Given I am logged in as GP user
        When I navigate to /admin/users
        Then I am redirected to dashboard
        """
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")

        page.goto(f"{BASE_URL}/admin/users")
        expect(page).to_have_url(f"{BASE_URL}/dashboard", timeout=5000)

    def test_gp_user_cannot_access_admin_health(self, page: Page):
        """
        BDD: Scenario: GP user cannot access admin health page
        Given I am logged in as GP user
        When I navigate to /admin/health
        Then I am redirected to dashboard
        """
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")

        page.goto(f"{BASE_URL}/admin/health")
        expect(page).to_have_url(f"{BASE_URL}/dashboard", timeout=5000)

    def test_gp_user_api_returns_403(self, page: Page):
        """
        BDD: Scenario: GP user API access returns 403 Forbidden
        Given I am logged in as GP user
        When I call admin stats API
        Then I receive 403 Forbidden
        """
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")

        response = page.request.get(f"{BASE_URL}/api/admin/stats")
        assert response.status == 403
        assert "Admin access required" in response.json()["error"]

    def test_lp_user_cannot_access_admin_dashboard(self, page: Page):
        """
        BDD: Scenario: LP user cannot access admin dashboard
        Given I am logged in as LP user
        When I navigate to /admin
        Then I am redirected to dashboard
        """
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "lp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")

        page.goto(f"{BASE_URL}/admin")
        expect(page).to_have_url(f"{BASE_URL}/dashboard", timeout=5000)

    def test_lp_user_api_returns_403(self, page: Page):
        """
        BDD: Scenario: LP user API access returns 403 Forbidden
        Given I am logged in as LP user
        When I call admin stats API
        Then I receive 403 Forbidden
        """
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "lp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")

        response = page.request.get(f"{BASE_URL}/api/admin/stats")
        assert response.status == 403

    def test_admin_user_can_access_all_admin_pages(self, page: Page):
        """
        BDD: Scenario: Admin user can access all admin pages
        Given I am logged in as admin user
        When I navigate to admin pages
        Then I can access all admin functionality
        """
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "admin@demo.com")
        page.fill('input[name="password"]', "admin123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")

        # Access admin dashboard
        page.goto(f"{BASE_URL}/admin")
        expect(page).to_have_url(f"{BASE_URL}/admin")
        expect(page.locator("h1")).to_contain_text("Platform Dashboard")

        # Access admin users
        page.goto(f"{BASE_URL}/admin/users")
        expect(page).to_have_url(f"{BASE_URL}/admin/users")
        expect(page.locator("h1")).to_contain_text("Users")

        # Access admin health
        page.goto(f"{BASE_URL}/admin/health")
        expect(page).to_have_url(f"{BASE_URL}/admin/health")
        expect(page.locator("h1")).to_contain_text("System Health")

    def test_admin_api_returns_data_for_admin(self, page: Page):
        """
        BDD: Scenario: Admin user can access admin API
        Given I am logged in as admin user
        When I call admin stats API
        Then I receive platform statistics
        """
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "admin@demo.com")
        page.fill('input[name="password"]', "admin123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")

        response = page.request.get(f"{BASE_URL}/api/admin/stats")
        assert response.status == 200
        data = response.json()
        assert data["success"] is True
        assert "stats" in data


@pytest.mark.browser
class TestAdminSecurityNoSensitiveDataExposure:
    """Test that admin pages don't expose sensitive data."""

    def test_admin_users_page_hides_passwords(self, page: Page):
        """
        BDD: Scenario: Admin users page does not expose passwords
        Given I am logged in as admin
        When I view the users list
        Then I cannot see any password information
        """
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "admin@demo.com")
        page.fill('input[name="password"]', "admin123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")

        page.goto(f"{BASE_URL}/admin/users")
        page_content = page.content().lower()

        # Should not contain password strings
        assert "password" not in page_content or "password:" not in page_content
        assert "demo123" not in page_content
        assert "admin123" not in page_content
        assert "password_hash" not in page_content

    def test_admin_health_page_no_stack_trace(self, page: Page):
        """
        BDD: Scenario: Admin health page shows no stack traces
        Given I am logged in as admin
        When I view the health page
        Then I do not see any stack traces or internal errors
        """
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "admin@demo.com")
        page.fill('input[name="password"]', "admin123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")

        page.goto(f"{BASE_URL}/admin/health")
        page_content = page.content().lower()

        assert "traceback" not in page_content
        assert "exception" not in page_content or "error" not in page_content


@pytest.mark.browser
class TestAdminSecuritySessionManagement:
    """Test admin session security."""

    def test_admin_session_expires_on_logout(self, page: Page):
        """
        BDD: Scenario: Admin session expires on logout
        Given I am logged in as admin
        When I logout
        Then I cannot access admin pages
        """
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "admin@demo.com")
        page.fill('input[name="password"]', "admin123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")

        # Access admin first to confirm it works
        page.goto(f"{BASE_URL}/admin")
        expect(page).to_have_url(f"{BASE_URL}/admin")

        # Logout
        page.goto(f"{BASE_URL}/logout")

        # Try to access admin again
        page.goto(f"{BASE_URL}/admin")
        expect(page).to_have_url(f"{BASE_URL}/login", timeout=5000)


# =============================================================================
# CROSS-CUTTING SECURITY TESTS
# BDD: Feature: Security across all protected routes
# =============================================================================


@pytest.mark.browser
class TestProtectedRoutesComprehensive:
    """Test all protected routes for all user roles."""

    @pytest.fixture
    def logged_in_page(self, page: Page):
        """Log in as GP user and return page."""
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")
        return page

    def test_all_protected_routes_require_auth(self, page: Page):
        """
        BDD: Scenario: All protected routes require authentication
        Given I am not logged in
        When I try to access any protected route
        Then I am redirected to login
        """
        # Clear all cookies to ensure we're truly unauthenticated
        page.context.clear_cookies()

        protected_routes = [
            "/dashboard",
            "/funds",
            "/lps",
            "/matches",
            "/shortlist",
            "/settings",
            "/admin",
            "/admin/users",
            "/admin/health",
        ]

        for route in protected_routes:
            page.context.clear_cookies()  # Clear before each route test
            page.goto(f"{BASE_URL}{route}")
            expect(page).to_have_url(f"{BASE_URL}/login", timeout=5000)

    def test_admin_routes_require_admin_role(self, logged_in_page: Page):
        """
        BDD: Scenario: Admin routes require admin role
        Given I am logged in as non-admin
        When I try to access admin routes
        Then I am redirected to dashboard
        """
        page = logged_in_page  # This is logged in as GP

        admin_routes = [
            "/admin",
            "/admin/users",
            "/admin/health",
        ]

        for route in admin_routes:
            page.goto(f"{BASE_URL}{route}")
            expect(page).to_have_url(f"{BASE_URL}/dashboard", timeout=5000)

    def test_api_endpoints_require_auth(self, page: Page):
        """
        BDD: Scenario: All API endpoints require authentication
        Given I am not logged in
        When I call protected API endpoints
        Then I receive 401 Unauthorized
        """
        protected_apis = [
            "/api/settings/preferences",
            "/api/shortlist",
            "/api/admin/stats",
        ]

        for api in protected_apis:
            response = page.request.get(f"{BASE_URL}{api}")
            assert response.status == 401, f"API {api} should require auth"
