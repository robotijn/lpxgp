"""End-to-End tests using Playwright.

These tests cover complete user journeys through the application.
They require a running server at http://localhost:8000.

Run with:
    # Start server first
    uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 &

    # Run E2E tests (browser tests only)
    uv run pytest tests/test_e2e.py -v -m browser

Test Categories:
    - Authentication journeys (register, login, logout, session)
    - Fund management (CRUD operations)
    - LP management (CRUD, search, filter)
    - Matching workflow (generate, view details)
    - Navigation and redirects
    - Mobile/responsive behavior

Performance Notes:
    - Uses session-scoped login fixtures (gp_page, lp_page, admin_page) to reuse auth
    - Avoids networkidle waits in favor of element-specific waits
    - Tests login/logout flows use fresh pages to test actual auth behavior

Note: Test classes have been extracted to separate files:
    - test_e2e_auth.py - Authentication and session tests
    - test_e2e_funds.py - Fund management tests
    - test_e2e_lps.py - LP management tests
    - test_e2e_gps.py - GP database tests
    - test_e2e_admin.py - Admin functionality tests
    - test_e2e_shortlist.py - Shortlist tests
    - test_e2e_crm.py - CRM integration tests
    - test_e2e_matches.py - Matching workflow tests
    - test_e2e_navigation.py - Navigation tests
    - test_e2e_settings.py - Dashboard and settings tests
    - test_e2e_quality.py - Mobile, error handling, accessibility tests
    - test_e2e_outreach.py - Outreach and pitch tests
    - test_e2e_ai_search.py - AI-powered search tests
    - test_e2e_api.py - REST API and RLS tests
"""

from collections.abc import Generator

import pytest
from playwright.sync_api import Page

# Base URL for the running server
BASE_URL = "http://localhost:8000"


# =============================================================================
# FIXTURES
# =============================================================================

# Legacy fixtures that perform fresh login per test - kept for auth tests that
# need to test actual login/logout behavior
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
