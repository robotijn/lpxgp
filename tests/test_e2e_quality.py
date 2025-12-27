"""End-to-End tests for Quality Assurance using Playwright.

These tests cover quality-related aspects of the application including:
- Mobile responsiveness
- Accessibility
- Performance
- Error handling
- HTMX interactions

They require a running server at http://localhost:8000.

Run with:
    # Start server first
    uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 &

    # Run quality E2E tests
    uv run pytest tests/test_e2e_quality.py -v -m browser

Test Categories:
    - Mobile journey (responsive behavior)
    - Accessibility (WCAG basics)
    - Performance (load times, console errors)
    - Error handling (404 pages)
    - HTMX interactions (dynamic updates)
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


@pytest.fixture
def tablet_viewport():
    """iPad viewport dimensions."""
    return {"width": 768, "height": 1024}


# =============================================================================
# MOBILE JOURNEY TESTS
# =============================================================================


@pytest.mark.browser
class TestMobileJourney:
    """Test mobile user experience."""

    def test_login_works_on_mobile(self, page: Page, mobile_viewport):
        """Login should work on mobile viewport."""
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/login")

        # Form should be visible and usable
        email_input = page.locator('input[name="email"]')
        expect(email_input).to_be_visible()

        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        with page.expect_navigation():
            page.click('button[type="submit"]')
        page.wait_for_load_state("domcontentloaded")

    def test_navigation_accessible_on_mobile(self, page: Page, mobile_viewport):
        """Navigation should be accessible on mobile."""
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        with page.expect_navigation():
            page.click('button[type="submit"]')
        page.wait_for_load_state("domcontentloaded")

        page.goto(f"{BASE_URL}/funds")

        # Either nav links visible or hamburger menu exists
        nav_visible = page.locator("nav a").first.is_visible()
        hamburger_exists = page.locator(
            "[aria-label*='menu'], #mobile-menu, .hamburger, [aria-label*='Menu']"
        ).count() > 0

        assert nav_visible or hamburger_exists, "Navigation must be accessible on mobile"

    def test_no_horizontal_scroll_on_mobile(self, page: Page, mobile_viewport):
        """Pages should not have horizontal scroll on mobile."""
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        with page.expect_navigation():
            page.click('button[type="submit"]')
        page.wait_for_load_state("domcontentloaded")

        pages_to_test = ["/funds", "/lps", "/matches", "/dashboard"]

        for url in pages_to_test:
            page.goto(f"{BASE_URL}{url}")
            body_width = page.evaluate("document.body.scrollWidth")
            viewport_width = mobile_viewport["width"]

            assert body_width <= viewport_width + 20, (
                f"Page {url} has horizontal overflow: body={body_width}px, viewport={viewport_width}px"
            )


# =============================================================================
# ERROR HANDLING TESTS
# =============================================================================


@pytest.mark.browser
class TestErrorHandling:
    """Test error handling in the browser."""

    def test_404_page_shows_error(self, page: Page):
        """404 page should show user-friendly error."""
        page.goto(f"{BASE_URL}/nonexistent-page-12345")

        # Should show 404 or error message
        content = page.content().lower()
        has_error = (
            "404" in content or
            "not found" in content or
            "error" in content
        )
        assert has_error, "404 page should show error message"

    def test_404_has_navigation_back(self, page: Page):
        """404 page should have way to navigate back."""
        page.goto(f"{BASE_URL}/nonexistent-page-12345")

        # Should have link to home or back button
        home_link = page.locator('a[href="/"]')
        has_navigation = home_link.count() > 0

        assert has_navigation, "404 page should have navigation"


# =============================================================================
# HTMX INTERACTION TESTS
# =============================================================================


@pytest.mark.browser
class TestHTMXInteractions:
    """Test HTMX-powered interactions."""

    def test_htmx_loaded(self, logged_in_page: Page):
        """HTMX should be loaded and available."""
        page = logged_in_page

        htmx_available = page.evaluate("typeof htmx !== 'undefined'")
        assert htmx_available, "HTMX should be loaded"

    def test_form_submission_uses_htmx(self, logged_in_page: Page):
        """Forms should use HTMX for submission."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/funds")

        # Check if forms have hx-* attributes
        html = page.content()
        uses_htmx = "hx-post" in html or "hx-get" in html or "hx-trigger" in html
        assert uses_htmx, "Forms should use HTMX attributes"


# =============================================================================
# ACCESSIBILITY TESTS
# =============================================================================


@pytest.mark.browser
class TestAccessibility:
    """Basic accessibility checks."""

    def test_page_has_title(self, logged_in_page: Page):
        """All pages should have a title."""
        page = logged_in_page

        pages = ["/dashboard", "/funds", "/lps", "/matches", "/settings"]
        for url in pages:
            page.goto(f"{BASE_URL}{url}")
            title = page.title()
            assert title and len(title) > 0, f"Page {url} missing title"

    def test_images_have_alt_text(self, logged_in_page: Page):
        """Images should have alt attributes."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/dashboard")

        images = page.locator("img").all()
        for img in images:
            alt = img.get_attribute("alt")
            # alt can be empty string for decorative images, but should exist
            assert alt is not None, "Images should have alt attribute"

    def test_forms_have_labels(self, page: Page):
        """Form inputs should have associated labels."""
        page.goto(f"{BASE_URL}/login")

        # Check that labels exist for form inputs
        labels = page.locator("label").count()

        # At least some inputs should have labels
        assert labels > 0, "Forms should have labels"

    def test_buttons_are_keyboard_accessible(self, page: Page):
        """Buttons should be keyboard accessible."""
        page.goto(f"{BASE_URL}/login")

        # Tab to submit button
        page.keyboard.press("Tab")
        page.keyboard.press("Tab")
        page.keyboard.press("Tab")

        # Focused element should be a button or input
        focused_tag = page.evaluate("document.activeElement.tagName.toLowerCase()")
        assert focused_tag in ["button", "input", "a"], "Should be able to tab to interactive elements"


# =============================================================================
# PERFORMANCE TESTS
# =============================================================================


@pytest.mark.browser
class TestPerformance:
    """Basic performance checks."""

    def test_pages_load_quickly(self, page: Page):
        """Pages should load within reasonable time."""
        import time

        pages = ["/", "/login", "/register"]

        for url in pages:
            start = time.time()
            page.goto(f"{BASE_URL}{url}")
            duration = time.time() - start

            # Page should load within 3 seconds
            assert duration < 3, f"Page {url} took {duration:.2f}s to load"

    def test_no_console_errors(self, logged_in_page: Page):
        """Pages should not have JavaScript console errors."""
        page = logged_in_page

        errors = []
        page.on("console", lambda msg: errors.append(msg.text) if msg.type == "error" else None)

        page.goto(f"{BASE_URL}/dashboard")
        page.wait_for_timeout(1000)

        # Filter out known acceptable errors
        critical_errors = [e for e in errors if "favicon" not in e.lower()]
        assert len(critical_errors) == 0, f"Console errors: {critical_errors}"
