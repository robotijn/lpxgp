"""End-to-End authentication tests using Playwright.

These tests cover authentication-related user journeys:
    - Login/logout flows
    - Registration
    - Session management
    - Protected route access

Extracted from test_e2e.py for better test organization.

Run with:
    # Start server first
    uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 &

    # Run auth E2E tests
    uv run pytest tests/test_e2e_auth.py -v -m browser
"""

import re
from collections.abc import Generator

import pytest
from playwright.sync_api import Page, expect

# Base URL for the running server
BASE_URL = "http://localhost:8000"


# =============================================================================
# FIXTURES
# =============================================================================


@pytest.fixture
def logged_in_page(page: Page) -> Generator[Page, None, None]:
    """Fixture that provides a page logged in as GP demo user.

    NOTE: Prefer gp_page fixture for most tests - it's faster because
    it reuses the login session. Use this only for tests that need to
    verify actual login behavior.
    """
    page.goto(f"{BASE_URL}/login")
    page.fill('input[name="email"]', "gp@demo.com")
    page.fill('input[name="password"]', "demo123")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{BASE_URL}/dashboard")
    yield page


# =============================================================================
# AUTHENTICATION JOURNEY TESTS
# =============================================================================


@pytest.mark.browser
class TestAuthenticationJourney:
    """Test complete authentication flows."""

    def test_login_flow_redirects_to_dashboard(self, page: Page):
        """User should be redirected to dashboard after successful login."""
        page.goto(f"{BASE_URL}/login")

        # Fill login form
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")

        # Submit and wait for redirect
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")

        # Verify we're on dashboard
        expect(page).to_have_url(f"{BASE_URL}/dashboard")
        # Dashboard heading
        expect(page.locator("h1")).to_contain_text("Dashboard")

    def test_login_with_invalid_credentials_shows_error(self, page: Page):
        """Invalid credentials should show error message."""
        page.goto(f"{BASE_URL}/login")

        page.fill('input[name="email"]', "wrong@email.com")
        page.fill('input[name="password"]', "wrongpassword")
        page.click('button[type="submit"]')

        # Wait for error to appear (HTMX swaps into #login-error)
        page.wait_for_selector("#login-error .text-red-700", timeout=5000)

        # Should stay on login page and show error
        expect(page).to_have_url(re.compile(r"/login"))
        expect(page.locator("#login-error")).to_contain_text("Invalid")

    def test_logout_flow_redirects_to_home(self, logged_in_page: Page):
        """Logout should clear session and redirect to home."""
        page = logged_in_page

        # Find and click logout
        page.click('a[href="/logout"]')

        # Should be redirected to home
        page.wait_for_load_state("networkidle")
        assert page.url == f"{BASE_URL}/" or page.url == f"{BASE_URL}"

    def test_session_persists_across_pages(self, logged_in_page: Page):
        """Session should persist when navigating between pages."""
        page = logged_in_page

        # Navigate to multiple protected pages
        page.goto(f"{BASE_URL}/funds")
        expect(page).to_have_url(f"{BASE_URL}/funds")

        page.goto(f"{BASE_URL}/lps")
        expect(page).to_have_url(f"{BASE_URL}/lps")

        page.goto(f"{BASE_URL}/matches")
        expect(page).to_have_url(f"{BASE_URL}/matches")

        # Still logged in - dashboard accessible
        page.goto(f"{BASE_URL}/dashboard")
        expect(page).to_have_url(f"{BASE_URL}/dashboard")

    def test_register_new_user_flow(self, page: Page):
        """New user registration should create account and redirect."""
        page.goto(f"{BASE_URL}/register")

        # Generate unique email for this test
        import time
        unique_email = f"test_{int(time.time())}@example.com"

        page.fill('input[name="email"]', unique_email)
        page.fill('input[name="password"]', "testpassword123")
        page.fill('input[name="name"]', "Test User")

        # Select role if dropdown exists
        role_select = page.locator('select[name="role"]')
        if role_select.count() > 0:
            role_select.select_option("gp")

        page.click('button[type="submit"]')

        # Wait for redirect to dashboard
        page.wait_for_function(
            "window.location.pathname === '/dashboard'",
            timeout=10000
        )
        assert "/dashboard" in page.url

    def test_protected_route_redirects_to_login(self, page: Page):
        """Unauthenticated access to protected routes should redirect to login."""
        # Try accessing dashboard without login
        page.goto(f"{BASE_URL}/dashboard")

        # Should be redirected to login
        expect(page).to_have_url(re.compile(r"/login"))


# =============================================================================
# SESSION MANAGEMENT TESTS
# =============================================================================


@pytest.mark.browser
class TestSessionManagementE2E:
    """E2E tests for session management."""

    def test_logout_clears_session(self, page: Page):
        """Logout should clear session and redirect to login."""
        # Login first
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")

        # Verify logged in
        assert "Dashboard" in page.content()

        # Logout
        page.goto(f"{BASE_URL}/logout")
        page.wait_for_load_state("domcontentloaded")

        # Should be redirected to home or login
        assert page.url in [f"{BASE_URL}/", f"{BASE_URL}/login"]

    def test_protected_page_redirects_when_not_logged_in(self, page: Page):
        """Protected pages should redirect to login when not authenticated."""
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("domcontentloaded")

        # Should redirect to login
        assert "/login" in page.url

    def test_session_persists_across_navigation(self, logged_in_page: Page):
        """Session should persist across page navigation."""
        page = logged_in_page

        # Navigate to multiple pages
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("domcontentloaded")
        assert "Dashboard" in page.content()

        page.goto(f"{BASE_URL}/lps")
        page.wait_for_load_state("domcontentloaded")
        assert page.url == f"{BASE_URL}/lps"

        page.goto(f"{BASE_URL}/funds")
        page.wait_for_load_state("domcontentloaded")
        assert page.url == f"{BASE_URL}/funds"
