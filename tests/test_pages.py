"""Tests for page-related routes and functionality.

IMPORTANT: Tests are the source of truth. Do NOT modify tests to make them pass.
If a test fails, fix the APPLICATION, not the test.

Based on BDD Gherkin specs from docs/prd/tests/*.feature.md

Test Categories:
- Home page tests
- Login page tests
- Dashboard tests
- 404 error handling
- Authentication redirects
- Logout functionality
"""

import pytest

# =============================================================================
# HOME PAGE TESTS
# =============================================================================


class TestHomeRoute:
    """Test home page."""

    def test_home_returns_200(self, client):
        """Home page should return 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_home_returns_html(self, client):
        """Home page should return HTML."""
        response = client.get("/")
        assert "text/html" in response.headers["content-type"]

    def test_home_contains_title(self, client):
        """Home page should contain LPxGP title."""
        response = client.get("/")
        assert "LPxGP" in response.text


class TestHomePageComprehensive:
    """Comprehensive home page tests.

    Gherkin Reference: E2E User Journeys
    """

    def test_home_has_navigation(self, client):
        """Home page should have navigation elements."""
        response = client.get("/")

        # Navigation should exist
        assert "<nav" in response.text.lower() or "nav" in response.text

    def test_home_has_main_content(self, client):
        """Home page should have main content area."""
        response = client.get("/")

        assert "LPxGP" in response.text

    def test_home_charset_utf8(self, client):
        """Home page should specify UTF-8 charset for international content.

        Gherkin: Handle unicode in LP name
        """
        response = client.get("/")

        # Check content-type header or meta tag
        content_type = response.headers.get("content-type", "")
        assert "utf-8" in content_type.lower() or "charset" in response.text.lower()

    def test_home_no_server_errors_in_html(self, client):
        """Home page HTML should not contain error traces.

        Edge case: Ensure no debug info leaks to production
        """
        response = client.get("/")
        html = response.text.lower()

        error_patterns = [
            "traceback",
            "exception",
            "error occurred",
            "internal server error",
        ]

        for pattern in error_patterns:
            assert pattern not in html, f"Home page should not contain '{pattern}'"


# =============================================================================
# 404 ERROR HANDLING TESTS
# =============================================================================


class Test404Handler:
    """Test 404 error handling."""

    def test_nonexistent_page_returns_404(self, client):
        """Non-existent page should return 404."""
        response = client.get("/nonexistent-page")
        assert response.status_code == 404

    def test_api_404_returns_json(self, client):
        """API 404 should return JSON."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        assert "application/json" in response.headers["content-type"]


class Test404HandlerComprehensive:
    """Comprehensive 404 error handling tests.

    Gherkin Reference: M1 Auth - Access protected page scenarios
    """

    def test_404_page_content(self, client):
        """404 page should show user-friendly error message."""
        response = client.get("/nonexistent-page")

        # Should show some error indication
        assert response.status_code == 404

    def test_404_no_stack_trace(self, client):
        """404 page should not expose stack traces.

        Security: Error pages should not leak implementation details
        """
        response = client.get("/nonexistent-page")
        text = response.text.lower()

        assert "traceback" not in text
        assert "file " not in text or "line " not in text

    def test_api_404_json_structure(self, client):
        """API 404 should return proper JSON structure.

        Gherkin: API errors return JSON format
        """
        response = client.get("/api/nonexistent")
        data = response.json()

        assert "error" in data or "detail" in data

    def test_api_404_includes_path(self, client):
        """API 404 should include the requested path for debugging."""
        response = client.get("/api/nonexistent-endpoint")
        data = response.json()

        # Should include some path information
        response_text = str(data)
        # Either in 'path' field or somewhere in response
        assert "path" in data or "nonexistent" in response_text.lower()

    def test_404_different_paths(self, client):
        """404 should work for various non-existent paths.

        Edge case: Test multiple path patterns
        """
        paths = [
            "/does-not-exist",
            "/page/123/edit",
            "/api/v2/users",
            "/deeply/nested/path/that/does/not/exist",
        ]

        for path in paths:
            response = client.get(path)
            assert response.status_code == 404, f"Path '{path}' should return 404"


# =============================================================================
# LOGIN PAGE TESTS
# =============================================================================


class TestLoginRoute:
    """Test login page."""

    def test_login_returns_200(self, client):
        """Login page should return 200 OK."""
        response = client.get("/login")
        assert response.status_code == 200

    def test_login_contains_form(self, client):
        """Login page should contain a login form."""
        response = client.get("/login")
        assert "email" in response.text
        assert "password" in response.text


class TestLoginPageComprehensive:
    """Comprehensive login page tests.

    Gherkin Reference: M1 Auth - F-AUTH-01: User Login
    """

    def test_login_has_email_field(self, client):
        """Login page should have email input field.

        Gherkin: When I enter my email and password
        """
        response = client.get("/login")

        # Look for email input
        assert 'type="email"' in response.text or 'name="email"' in response.text

    def test_login_has_password_field(self, client):
        """Login page should have password input field.

        Gherkin: When I enter my email and password
        """
        response = client.get("/login")

        # Look for password input
        assert 'type="password"' in response.text or 'name="password"' in response.text

    def test_login_has_submit_button(self, client):
        """Login page should have a submit button.

        Gherkin: And I click "Login"
        """
        response = client.get("/login")

        # Look for submit button
        assert 'type="submit"' in response.text or "button" in response.text.lower()

    def test_login_form_has_action(self, client):
        """Login form should have a form action or JS handler.

        Gherkin: When I click "Login"
        """
        response = client.get("/login")

        # Should have form element
        assert "<form" in response.text.lower()

    def test_login_page_title(self, client):
        """Login page should have appropriate title."""
        response = client.get("/login")

        assert "Login" in response.text or "login" in response.text.lower()


# =============================================================================
# DASHBOARD TESTS
# =============================================================================


class TestDashboardContent:
    """Test dashboard page content."""

    def test_dashboard_shows_user_name(self, client):
        """Dashboard should display user's name."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/dashboard")
        assert "Demo" in response.text  # First name from "Demo GP User"

    def test_dashboard_shows_stats(self, client):
        """Dashboard should show statistics cards."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/dashboard")
        assert "Total Funds" in response.text
        assert "Total LPs" in response.text
        assert "AI Matches" in response.text

    def test_dashboard_has_quick_actions(self, client):
        """Dashboard should have quick action links."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/dashboard")
        assert "Quick Actions" in response.text
        assert "/funds" in response.text
        assert "/matches" in response.text

    def test_dashboard_has_navigation(self, client):
        """Dashboard should have navigation to other pages."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/dashboard")
        assert 'href="/matches"' in response.text
        assert 'href="/funds"' in response.text
        assert 'href="/lps"' in response.text


# =============================================================================
# LOGOUT TESTS
# =============================================================================


class TestLogoutFunctionality:
    """Test logout endpoint and session invalidation.

    Gherkin Reference: F-AUTH-01 - Session Management - Logout
    """

    def test_logout_redirects_to_home_or_login(self, client):
        """Logout should redirect to home or login page."""
        # First login
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Then logout
        response = client.get("/logout", follow_redirects=False)
        assert response.status_code in [302, 303, 307]
        location = response.headers.get("location", "")
        # Logout can redirect to home (/) or login page
        assert location in ["/", "/login"] or "/login" in location

    def test_logout_clears_session(self, client):
        """After logout, protected pages should redirect to login."""
        # Login
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Verify logged in
        response = client.get("/dashboard")
        assert response.status_code == 200

        # Logout
        client.get("/logout")

        # Try to access protected page
        response = client.get("/dashboard", follow_redirects=False)
        assert response.status_code in [302, 303, 307]
        assert "/login" in response.headers.get("location", "")

    def test_logout_works_when_not_logged_in(self, client):
        """Logout should work gracefully when not logged in."""
        response = client.get("/logout", follow_redirects=False)
        # Should redirect to login without error
        assert response.status_code in [302, 303, 307]


# =============================================================================
# PROTECTED PAGE REDIRECTS
# =============================================================================


class TestProtectedPageRedirects:
    """Test that protected pages redirect unauthenticated users.

    Gherkin Reference: F-AUTH-01 - Session Management - Access Control
    """

    @pytest.mark.parametrize(
        "protected_route",
        [
            "/dashboard",
            "/funds",
            "/lps",
            "/gps",
            "/matches",
            "/shortlist",
            "/settings",
            "/outreach",
            "/pitch",
            "/events",
            "/touchpoints",
            "/tasks",
        ],
    )
    def test_protected_route_redirects_when_unauthenticated(
        self, client, protected_route
    ):
        """Protected routes should redirect to login when not authenticated."""
        response = client.get(protected_route, follow_redirects=False)
        assert response.status_code in [302, 303, 307], (
            f"{protected_route} should redirect unauthenticated users"
        )
        location = response.headers.get("location", "")
        assert "/login" in location, (
            f"{protected_route} should redirect to /login, got: {location}"
        )

    @pytest.mark.parametrize(
        "admin_route",
        [
            "/admin",
            "/admin/users",
            "/admin/health",
            "/admin/lps",
            "/admin/companies",
        ],
    )
    def test_admin_routes_redirect_when_unauthenticated(self, client, admin_route):
        """Admin routes should redirect to login when not authenticated."""
        response = client.get(admin_route, follow_redirects=False)
        assert response.status_code in [302, 303, 307], (
            f"{admin_route} should redirect unauthenticated users"
        )
        location = response.headers.get("location", "")
        assert "/login" in location, (
            f"{admin_route} should redirect to /login, got: {location}"
        )

    def test_protected_page_accessible_after_login(self, client):
        """Protected pages should be accessible after login."""
        # Login
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Access protected page
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert "Dashboard" in response.text

    def test_admin_page_accessible_for_admin(self, client):
        """Admin pages should be accessible for admin users."""
        # Login as admin
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        # Access admin page
        response = client.get("/admin")
        assert response.status_code == 200
        assert "Admin" in response.text
