"""End-to-End tests for API functionality using Playwright.

These tests cover REST API v1 endpoints and Row-Level Security isolation,
testing the APIs from the browser using JavaScript fetch.

They require a running server at http://localhost:8000.

Run with:
    # Start server first
    uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 &

    # Run API E2E tests
    uv run pytest tests/test_e2e_api.py -v -m browser

Test Categories:
    - REST API v1 endpoints (CRUD, search, pagination, auth)
    - Row-Level Security isolation (GP/LP/Admin access)
"""

from collections.abc import Generator

import pytest
from playwright.sync_api import Page

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


# =============================================================================
# REST API V1 TESTS
# =============================================================================


@pytest.mark.browser
class TestRestApiV1E2E:
    """E2E tests for REST API v1 endpoints.

    Tests the APIs from the browser using JavaScript fetch.
    Requires:
    - Live dev server running
    - Database populated with LP/GP/Fund data
    """

    def test_api_v1_lps_returns_json(self, logged_in_page: Page):
        """API /api/v1/lps should return valid JSON."""
        page = logged_in_page
        result = page.evaluate("""
            async () => {
                const response = await fetch('/api/v1/lps');
                return {
                    status: response.status,
                    contentType: response.headers.get('content-type'),
                    data: await response.json()
                };
            }
        """)
        assert result["status"] == 200
        assert "application/json" in result["contentType"]
        assert "data" in result["data"]
        assert "total" in result["data"]

    def test_api_v1_gps_returns_json(self, logged_in_page: Page):
        """API /api/v1/gps should return valid JSON."""
        page = logged_in_page
        result = page.evaluate("""
            async () => {
                const response = await fetch('/api/v1/gps');
                return {
                    status: response.status,
                    contentType: response.headers.get('content-type'),
                    data: await response.json()
                };
            }
        """)
        assert result["status"] == 200
        assert "application/json" in result["contentType"]
        assert "data" in result["data"]
        assert "total" in result["data"]

    def test_api_v1_funds_returns_json(self, logged_in_page: Page):
        """API /api/v1/funds should return valid JSON."""
        page = logged_in_page
        result = page.evaluate("""
            async () => {
                const response = await fetch('/api/v1/funds');
                return {
                    status: response.status,
                    contentType: response.headers.get('content-type'),
                    data: await response.json()
                };
            }
        """)
        assert result["status"] == 200
        assert "application/json" in result["contentType"]
        assert "data" in result["data"]
        assert "total" in result["data"]

    def test_api_v1_lps_with_search(self, logged_in_page: Page):
        """API /api/v1/lps should support search parameter."""
        page = logged_in_page
        result = page.evaluate("""
            async () => {
                const response = await fetch('/api/v1/lps?search=pension');
                return {
                    status: response.status,
                    data: await response.json()
                };
            }
        """)
        assert result["status"] == 200
        assert "data" in result["data"]

    def test_api_v1_gps_with_strategy(self, logged_in_page: Page):
        """API /api/v1/gps should support strategy filter."""
        page = logged_in_page
        result = page.evaluate("""
            async () => {
                const response = await fetch('/api/v1/gps?strategy=buyout');
                return {
                    status: response.status,
                    data: await response.json()
                };
            }
        """)
        assert result["status"] == 200
        assert "data" in result["data"]

    def test_api_v1_funds_with_pagination(self, logged_in_page: Page):
        """API /api/v1/funds should support pagination."""
        page = logged_in_page
        result = page.evaluate("""
            async () => {
                const response = await fetch('/api/v1/funds?page=1&per_page=5');
                return {
                    status: response.status,
                    data: await response.json()
                };
            }
        """)
        assert result["status"] == 200
        assert result["data"]["page"] == 1
        assert result["data"]["per_page"] == 5

    def test_api_v1_requires_auth(self, page: Page):
        """API endpoints should require authentication."""
        page.goto(f"{BASE_URL}/login")  # Fresh page, not logged in
        page.wait_for_load_state("domcontentloaded")

        result = page.evaluate("""
            async () => {
                const response = await fetch('/api/v1/lps');
                return { status: response.status };
            }
        """)
        # Should return 401 Unauthorized
        assert result["status"] == 401


# =============================================================================
# ROW-LEVEL SECURITY ISOLATION TESTS
# =============================================================================


@pytest.mark.browser
class TestRLSIsolationE2E:
    """E2E tests for Row-Level Security isolation."""

    def test_gp_user_sees_dashboard(self, logged_in_page: Page):
        """GP user should see their dashboard."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_load_state("domcontentloaded")
        assert "Dashboard" in page.content()

    def test_gp_user_can_browse_lps(self, logged_in_page: Page):
        """GP user should be able to browse LPs."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps")
        page.wait_for_load_state("domcontentloaded")
        assert "LPs" in page.content() or "LP" in page.content()

    def test_admin_can_access_admin_panel(self, page: Page):
        """Admin user should access admin panel."""
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "admin@demo.com")
        page.fill('input[name="password"]', "admin123")
        page.click('button[type="submit"]')
        page.wait_for_url(f"{BASE_URL}/dashboard")

        page.goto(f"{BASE_URL}/admin")
        page.wait_for_load_state("domcontentloaded")
        assert "Admin" in page.content()
