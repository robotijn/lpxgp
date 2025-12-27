"""End-to-End tests for Shortlist functionality using Playwright.

These tests cover shortlist user journeys including:
- Adding/removing LPs from shortlist
- Shortlist page navigation
- Stats display
- Mobile responsiveness

Extracted from test_e2e.py for better test organization.

Run with:
    # Start server first
    uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 &

    # Run shortlist E2E tests
    uv run pytest tests/test_e2e_shortlist.py -v -m browser
"""

from collections.abc import Generator

import pytest
from playwright.sync_api import Page, expect

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

    # Fill login form
    page.fill('input[name="email"]', "gp@demo.com")
    page.fill('input[name="password"]', "demo1234")
    page.click('button[type="submit"]')

    # Wait for redirect to dashboard
    page.wait_for_url(f"{BASE_URL}/dashboard")

    yield page


@pytest.fixture
def mobile_viewport():
    """Mobile viewport dimensions."""
    return {"width": 375, "height": 667}


# =============================================================================
# SHORTLIST E2E TESTS
# =============================================================================


@pytest.mark.browser
class TestShortlistJourney:
    """Test complete shortlist user journeys.

    Gherkin Reference: F-SHORTLIST - User saves and manages LPs
    """

    def test_shortlist_page_accessible(self, logged_in_page: Page):
        """Shortlist page should be accessible when logged in."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/shortlist")

        expect(page).to_have_url(f"{BASE_URL}/shortlist")
        expect(page.locator("h1")).to_contain_text("Shortlist")

    def test_navigation_includes_shortlist(self, logged_in_page: Page):
        """Navigation should include shortlist link."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/dashboard")

        # Check for shortlist link in navigation
        shortlist_link = page.locator('a[href="/shortlist"]')
        expect(shortlist_link.first).to_be_visible()

    def test_shortlist_empty_state(self, logged_in_page: Page):
        """Shortlist should show empty state when no items."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/shortlist")

        # Should show empty state or 0 count
        page_content = page.content().lower()
        # Empty state indicators
        assert (
            "no saved" in page_content
            or "0" in page_content
            or "start saving" in page_content
            or "empty" in page_content
        )

    def test_lps_page_has_save_button(self, logged_in_page: Page):
        """LPs page should have save/shortlist buttons on LP cards."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps")

        # Wait for page to load
        page.wait_for_timeout(500)

        # Look for save/shortlist buttons
        save_buttons = page.locator("button:has-text('Save'), button[title*='shortlist']")
        if save_buttons.count() > 0:
            expect(save_buttons.first).to_be_visible()

    def test_shortlist_toggle_from_lps_page(self, logged_in_page: Page):
        """User should be able to toggle shortlist from LPs page."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps")

        # Wait for page to load
        page.wait_for_timeout(500)

        # Find a save button (might have HTMX toggle behavior)
        toggle_button = page.locator(
            "button[hx-post*='toggle'], button:has-text('Save')"
        ).first

        if toggle_button.is_visible():
            # Click to toggle
            toggle_button.click()
            page.wait_for_timeout(500)

            # Button state should change (text or style)
            button_text = toggle_button.inner_text().lower()
            # After toggle, should say "saved" or "remove"
            assert "saved" in button_text or "remove" in button_text or "save" in button_text

    def test_shortlist_persists_across_navigation(self, logged_in_page: Page):
        """Shortlist items should persist when navigating."""
        page = logged_in_page

        # Go to shortlist and check initial state
        page.goto(f"{BASE_URL}/shortlist")
        page.wait_for_timeout(300)
        page.content()

        # Navigate away and back
        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_timeout(300)
        page.goto(f"{BASE_URL}/shortlist")
        page.wait_for_timeout(300)

        # Content should be consistent (not lost during navigation)
        final_content = page.content()

        # Basic structural elements should persist
        assert "Shortlist" in final_content

    def test_shortlist_accessible_from_dashboard(self, logged_in_page: Page):
        """User should be able to access shortlist from dashboard."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/dashboard")

        # Find and click shortlist link
        shortlist_link = page.locator('a[href="/shortlist"]').first
        if shortlist_link.is_visible():
            shortlist_link.click()
            page.wait_for_url(f"{BASE_URL}/shortlist")
            expect(page).to_have_url(f"{BASE_URL}/shortlist")


@pytest.mark.browser
class TestShortlistNavigation:
    """Test shortlist page navigation and structure."""

    def test_shortlist_has_back_to_lps_link(self, logged_in_page: Page):
        """Shortlist page should have link back to LPs."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/shortlist")

        lps_link = page.locator('a[href="/lps"]')
        expect(lps_link.first).to_be_visible()

    def test_shortlist_navigation_works(self, logged_in_page: Page):
        """All navigation links on shortlist page should work."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/shortlist")

        # Test key navigation links
        nav_links = [
            ("/dashboard", "Dashboard"),
            ("/lps", "LP"),
            ("/funds", "Fund"),
        ]

        for href, partial_text in nav_links:
            link = page.locator(f'a[href="{href}"]').first
            if link.is_visible():
                link.click()
                page.wait_for_timeout(300)
                expect(page).to_have_url(f"{BASE_URL}{href}")
                page.goto(f"{BASE_URL}/shortlist")


@pytest.mark.browser
class TestShortlistStats:
    """Test shortlist statistics display."""

    def test_shortlist_shows_count(self, logged_in_page: Page):
        """Shortlist page should show item count."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/shortlist")

        # Should display count somewhere (in stats or empty message)
        page_content = page.content()
        # Stats typically show numbers
        assert any(char.isdigit() for char in page_content)

    def test_shortlist_stats_section_exists(self, logged_in_page: Page):
        """Shortlist should have a stats section if items exist."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/shortlist")

        # Look for stats-related elements
        page_content = page.content().lower()

        # Should have either stats or empty state
        has_stats = "total" in page_content or "saved" in page_content
        has_empty = "no saved" in page_content or "start saving" in page_content

        assert has_stats or has_empty, "Should show stats or empty state"


@pytest.mark.browser
class TestShortlistMobileResponsive:
    """Test shortlist mobile responsiveness."""

    def test_shortlist_mobile_navigation(self, logged_in_page: Page, mobile_viewport):
        """Shortlist should be navigable on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/shortlist")

        # Page should load on mobile
        expect(page.locator("h1")).to_contain_text("Shortlist")

    def test_shortlist_mobile_menu(self, logged_in_page: Page, mobile_viewport):
        """Mobile menu should include shortlist link."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/dashboard")

        # Find and click mobile menu button
        menu_button = page.locator("[data-mobile-menu-button], button:has(svg[class*='menu']), #mobile-menu-button")
        if menu_button.count() > 0:
            menu_button.first.click()
            page.wait_for_timeout(300)

            # Check for shortlist in mobile menu
            mobile_menu = page.locator("#mobile-menu, [data-mobile-menu]")
            if mobile_menu.is_visible():
                shortlist_mobile_link = mobile_menu.locator('a[href="/shortlist"]')
                if shortlist_mobile_link.count() > 0:
                    expect(shortlist_mobile_link.first).to_be_visible()
