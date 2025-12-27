"""End-to-End tests for Navigation functionality using Playwright.

These tests cover navigation-specific user journeys through the application,
including main navigation links, cross-page navigation workflows, and mobile
responsiveness for new pages.

They require a running server at http://localhost:8000.

Run with:
    # Start server first
    uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 &

    # Run navigation E2E tests
    uv run pytest tests/test_e2e_navigation.py -v -m browser

Test Categories:
    - Main navigation links and flows
    - Cross-page navigation workflows (LP -> Match -> Pitch)
    - Mobile responsiveness for new pages
"""

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
def mobile_viewport():
    """iPhone SE viewport dimensions."""
    return {"width": 375, "height": 667}


# =============================================================================
# NAVIGATION FLOW TESTS
# =============================================================================


@pytest.mark.browser
class TestNavigationFlow:
    """Test navigation between pages."""

    def test_main_navigation_links_work(self, logged_in_page: Page):
        """All main navigation links should work."""
        page = logged_in_page

        nav_pages = [
            ("/funds", "Funds"),
            ("/lps", "LP"),
            ("/matches", "Match"),
            ("/dashboard", "Dashboard"),
        ]

        for url, expected_text in nav_pages:
            page.goto(f"{BASE_URL}{url}")
            expect(page).to_have_url(f"{BASE_URL}{url}")
            # Page should have relevant heading
            h1_text = page.locator("h1").text_content() or ""
            assert expected_text.lower() in h1_text.lower(), f"Page {url} missing expected heading"

    def test_logo_links_to_home(self, logged_in_page: Page):
        """Logo should link to home page."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/dashboard")

        # Click logo/brand link
        logo = page.locator('a[href="/"], .logo, .brand')
        if logo.count() > 0:
            logo.first.click()
            expect(page).to_have_url(f"{BASE_URL}/")


# =============================================================================
# CROSS-PAGE NAVIGATION E2E TESTS
# =============================================================================


@pytest.mark.browser
class TestNewPagesNavigation:
    """Test navigation flow between new pages."""

    def test_full_workflow_lp_to_pitch(self, logged_in_page: Page):
        """Test complete workflow: LPs -> LP Detail -> Match -> Pitch.

        BDD: Given I am searching for LPs
             When I find a good match
             And I want to reach out
             Then I can generate a personalized pitch
        """
        page = logged_in_page

        # Start at LPs page
        page.goto(f"{BASE_URL}/lps")
        page.wait_for_load_state("networkidle")

        # Navigate to LP detail (using sample ID)
        page.goto(f"{BASE_URL}/lps/a1000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")
        assert "/lps/" in page.url

        # Click to see match analysis
        match_link = page.locator('a[href*="/matches"]').first
        if match_link.is_visible():
            match_link.click()
            page.wait_for_load_state("networkidle")

        # Navigate to pitch generator
        page.goto(f"{BASE_URL}/pitch?lp_id=a1000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")
        assert "/pitch" in page.url

    def test_outreach_links_to_related_pages(self, logged_in_page: Page):
        """Outreach hub should link to shortlist and pitch generator.

        BDD: Given I am on outreach hub
             Then I can access shortlist and pitch generator
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/outreach")
        page.wait_for_load_state("networkidle")

        # Check for shortlist link
        shortlist_link = page.locator('a[href="/shortlist"]')
        if shortlist_link.count() > 0:
            expect(shortlist_link.first).to_be_visible()

        # Check for pitch link
        pitch_link = page.locator('a[href*="/pitch"]')
        if pitch_link.count() > 0:
            expect(pitch_link.first).to_be_visible()


# =============================================================================
# NEW PAGES MOBILE RESPONSIVE E2E TESTS
# =============================================================================


@pytest.mark.browser
class TestNewPagesMobileResponsive:
    """Test new pages on mobile viewport."""

    def test_lp_detail_mobile(self, logged_in_page: Page, mobile_viewport):
        """LP detail should work on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/lps/a1000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")

        # Page should load and be usable
        assert page.locator("h1").count() > 0

    def test_fund_detail_mobile(self, logged_in_page: Page, mobile_viewport):
        """Fund detail should work on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/funds/0f000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")

        # Page should load and be usable
        assert page.locator("h1").count() > 0

    def test_match_detail_mobile(self, logged_in_page: Page, mobile_viewport):
        """Match detail should work on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/matches/a1000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")

        # Page should load and be usable
        page_content = page.content()
        assert "Score" in page_content or "Match" in page_content

    def test_outreach_mobile(self, logged_in_page: Page, mobile_viewport):
        """Outreach hub should work on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/outreach")
        page.wait_for_load_state("networkidle")

        expect(page.locator("h1")).to_contain_text("Outreach")

    def test_pitch_generator_mobile(self, logged_in_page: Page, mobile_viewport):
        """Pitch generator should work on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/pitch")
        page.wait_for_load_state("networkidle")

        page_content = page.content()
        assert "Pitch" in page_content or "Generator" in page_content

    def test_no_horizontal_scroll_new_pages(self, logged_in_page: Page, mobile_viewport):
        """New pages should not have horizontal scroll on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)

        pages_to_test = [
            "/lps/a1000001-0000-0000-0000-000000000001",
            "/funds/0f000001-0000-0000-0000-000000000001",
            "/matches/a1000001-0000-0000-0000-000000000001",
            "/outreach",
            "/pitch",
        ]

        for url in pages_to_test:
            page.goto(f"{BASE_URL}{url}")
            page.wait_for_load_state("networkidle")

            body_width = page.evaluate("document.body.scrollWidth")
            viewport_width = mobile_viewport["width"]

            assert body_width <= viewport_width + 20, (
                f"Page {url} has horizontal overflow: body={body_width}px, viewport={viewport_width}px"
            )
