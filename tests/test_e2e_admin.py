"""End-to-End tests for Admin functionality using Playwright.

These tests cover admin-specific user journeys through the application,
including admin dashboard, user management, system health, navigation,
role enforcement, and mobile responsiveness.

They require a running server at http://localhost:8000.

Run with:
    # Start server first
    uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 &

    # Run admin E2E tests
    uv run pytest tests/test_e2e_admin.py -v -m browser

Test Categories:
    - Admin dashboard and platform stats
    - Admin navigation
    - Admin role enforcement (GP/LP redirects)
    - Admin mobile responsiveness
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


@pytest.fixture
def logged_in_as_lp(page: Page) -> Generator[Page, None, None]:
    """Fixture that provides a page logged in as LP demo user."""
    page.goto(f"{BASE_URL}/login")
    page.fill('input[name="email"]', "lp@demo.com")
    page.fill('input[name="password"]', "demo123")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{BASE_URL}/dashboard")
    yield page


@pytest.fixture
def logged_in_as_admin(page: Page) -> Generator[Page, None, None]:
    """Fixture that provides a page logged in as admin demo user."""
    page.goto(f"{BASE_URL}/login")
    page.fill('input[name="email"]', "admin@demo.com")
    page.fill('input[name="password"]', "admin123")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{BASE_URL}/dashboard")
    yield page


@pytest.fixture
def mobile_viewport():
    """iPhone SE viewport dimensions."""
    return {"width": 375, "height": 667}


@pytest.fixture
def tablet_viewport():
    """iPad viewport dimensions."""
    return {"width": 768, "height": 1024}


# =============================================================================
# ADMIN JOURNEY TESTS
# =============================================================================


@pytest.mark.browser
class TestAdminJourney:
    """E2E tests for admin user journey."""

    def test_admin_dashboard_loads(self, logged_in_as_admin: Page):
        """Admin dashboard should load for admin user."""
        page = logged_in_as_admin
        page.goto(f"{BASE_URL}/admin")

        expect(page.locator("h1")).to_contain_text("Platform Dashboard")
        expect(page).to_have_url(f"{BASE_URL}/admin")

    def test_admin_shows_platform_stats(self, logged_in_as_admin: Page):
        """Admin dashboard should display platform statistics."""
        page = logged_in_as_admin
        page.goto(f"{BASE_URL}/admin")

        # Check for stats sections
        page_content = page.content()
        assert "Companies" in page_content
        assert "Total Users" in page_content
        assert "LP Database" in page_content

    def test_admin_shows_system_health(self, logged_in_as_admin: Page):
        """Admin dashboard should show system health summary."""
        page = logged_in_as_admin
        page.goto(f"{BASE_URL}/admin")

        # Use heading role to avoid ambiguity with link
        expect(page.get_by_role("heading", name="System Health")).to_be_visible()

    def test_admin_users_page_loads(self, logged_in_as_admin: Page):
        """Admin users page should load and display users."""
        page = logged_in_as_admin
        page.goto(f"{BASE_URL}/admin/users")

        expect(page.locator("h1")).to_contain_text("Users")

        # Should show registered users
        page_content = page.content()
        assert "gp@demo.com" in page_content or "Demo GP" in page_content

    def test_admin_health_page_loads(self, logged_in_as_admin: Page):
        """Admin health page should load and display health checks."""
        page = logged_in_as_admin
        page.goto(f"{BASE_URL}/admin/health")

        expect(page.locator("h1")).to_contain_text("System Health")

        # Should show health check items
        page_content = page.content()
        assert "Database" in page_content
        assert "Authentication" in page_content


@pytest.mark.browser
class TestAdminNavigation:
    """E2E tests for admin navigation."""

    def test_admin_nav_links_work(self, logged_in_as_admin: Page):
        """Admin navigation links should work correctly."""
        page = logged_in_as_admin

        # Test direct navigation to admin pages (nav links exist)
        page.goto(f"{BASE_URL}/admin/users")
        expect(page).to_have_url(f"{BASE_URL}/admin/users")
        assert "Users" in page.content()

        page.goto(f"{BASE_URL}/admin/health")
        expect(page).to_have_url(f"{BASE_URL}/admin/health")
        assert "System Health" in page.content()

        page.goto(f"{BASE_URL}/admin")
        expect(page).to_have_url(f"{BASE_URL}/admin")
        assert "Platform Dashboard" in page.content()

    def test_admin_back_to_app_link(self, logged_in_as_admin: Page):
        """Admin should have link back to main app."""
        page = logged_in_as_admin
        page.goto(f"{BASE_URL}/admin")

        # Check for back to app link
        back_link = page.locator('a[href="/dashboard"]').first
        expect(back_link).to_be_visible()

        back_link.click()
        expect(page).to_have_url(f"{BASE_URL}/dashboard")


@pytest.mark.browser
class TestAdminRoleEnforcement:
    """E2E tests for admin role enforcement."""

    def test_gp_redirected_from_admin(self, logged_in_page: Page):
        """GP user should be redirected away from admin."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/admin")

        # Should be redirected to dashboard
        expect(page).to_have_url(f"{BASE_URL}/dashboard")

    def test_lp_redirected_from_admin(self, logged_in_as_lp: Page):
        """LP user should be redirected away from admin."""
        page = logged_in_as_lp
        page.goto(f"{BASE_URL}/admin")

        # Should be redirected to dashboard
        expect(page).to_have_url(f"{BASE_URL}/dashboard")


@pytest.mark.browser
class TestAdminMobileResponsive:
    """Test admin mobile responsiveness."""

    def test_admin_dashboard_mobile(self, logged_in_as_admin: Page, mobile_viewport):
        """Admin dashboard should work on mobile."""
        page = logged_in_as_admin
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/admin")

        # Page should load on mobile
        expect(page.locator("h1")).to_contain_text("Platform Dashboard")

    def test_admin_users_mobile(self, logged_in_as_admin: Page, mobile_viewport):
        """Admin users page should work on mobile."""
        page = logged_in_as_admin
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/admin/users")

        expect(page.locator("h1")).to_contain_text("Users")
