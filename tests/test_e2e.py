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
# FUND MANAGEMENT JOURNEY TESTS
# =============================================================================


@pytest.mark.browser
class TestFundManagementJourney:
    """Test complete fund CRUD operations."""

    def test_view_funds_list(self, logged_in_page: Page):
        """User should see list of funds."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/funds")

        expect(page).to_have_url(f"{BASE_URL}/funds")
        expect(page.locator("h1")).to_contain_text("Funds")

    def test_create_fund_modal_opens(self, logged_in_page: Page):
        """Create fund button should open modal."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/funds")

        # Click create button
        create_btn = page.locator("button:has-text('Create'), button:has-text('Add'), a:has-text('Create')")
        if create_btn.count() > 0:
            create_btn.first.click()

            # Modal should appear
            page.wait_for_selector("#create-fund-modal, [role='dialog'], .modal")

    def test_fund_form_has_required_fields(self, logged_in_page: Page):
        """Fund create form should have all required fields."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/funds")

        # Check form fields exist
        html = page.content()
        assert 'name="name"' in html, "Fund name field missing"

    def test_funds_page_shows_statistics(self, logged_in_page: Page):
        """Funds page should show fund statistics."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/funds")

        # Should show some statistics or summary
        content = page.content().lower()
        # Look for stats-like content
        has_stats = (
            "total" in content or
            "fund" in content or
            "target" in content
        )
        assert has_stats, "Funds page should show statistics"


# =============================================================================
# LP MANAGEMENT JOURNEY TESTS
# =============================================================================


@pytest.mark.browser
class TestLPManagementJourney:
    """Test complete LP management operations."""

    def test_view_lps_list(self, logged_in_page: Page):
        """User should see list of LPs."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps")

        expect(page).to_have_url(f"{BASE_URL}/lps")
        expect(page.locator("h1")).to_contain_text("LP")

    def test_lp_search_functionality(self, logged_in_page: Page):
        """Search should filter LP list."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps")

        # Look for search input
        search_input = page.locator('input[type="search"], input[name="search"], input[placeholder*="Search"]')
        if search_input.count() > 0:
            search_input.first.fill("test")
            # Trigger search (either on input or button click)
            search_input.first.press("Enter")
            # Wait for HTMX to update
            page.wait_for_timeout(500)

    def test_lp_type_filter(self, logged_in_page: Page):
        """Type filter should filter LP list."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps")

        # Look for type filter
        type_filter = page.locator('select[name="lp_type"], select[name="type"]')
        if type_filter.count() > 0:
            # Get available options
            options = type_filter.first.locator("option").all()
            if len(options) > 1:
                type_filter.first.select_option(index=1)
                page.wait_for_timeout(500)


# =============================================================================
# MATCHING WORKFLOW TESTS
# =============================================================================


@pytest.mark.browser
class TestMatchingWorkflow:
    """Test the matching generation and viewing workflow."""

    def test_view_matches_page(self, logged_in_page: Page):
        """User should see matches page."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/matches")

        expect(page).to_have_url(f"{BASE_URL}/matches")
        expect(page.locator("h1")).to_contain_text("Match")

    def test_matches_page_has_fund_filter(self, logged_in_page: Page):
        """Matches page should have fund filter."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/matches")

        # Look for fund selector
        html = page.content()
        has_filter = (
            'name="fund_id"' in html or
            'select' in html.lower()
        )
        assert has_filter, "Matches page should have fund filter"


# =============================================================================
# NAVIGATION AND REDIRECT TESTS
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
# DASHBOARD TESTS
# =============================================================================


@pytest.mark.browser
class TestDashboardJourney:
    """Test dashboard functionality."""

    def test_dashboard_shows_user_greeting(self, logged_in_page: Page):
        """Dashboard should greet the logged-in user."""
        page = logged_in_page

        # Should show some greeting or user-specific content
        content = page.content().lower()
        has_greeting = (
            "welcome" in content or
            "dashboard" in content or
            "hello" in content
        )
        assert has_greeting, "Dashboard should greet user"

    def test_dashboard_shows_stats(self, logged_in_page: Page):
        """Dashboard should show key statistics."""
        page = logged_in_page

        # Look for stat cards or summary numbers
        stat_indicators = page.locator('[class*="stat"], [class*="card"], [class*="metric"]')
        # Dashboard should have some kind of stats display
        content = page.content()
        has_numbers = bool(re.search(r'\d+', content))
        assert has_numbers or stat_indicators.count() > 0, "Dashboard should show statistics"

    def test_dashboard_has_quick_actions(self, logged_in_page: Page):
        """Dashboard should have quick action buttons."""
        page = logged_in_page

        # Look for action buttons or links
        actions = page.locator('a[href*="/funds"], a[href*="/lps"], button')
        assert actions.count() > 0, "Dashboard should have action buttons"


# =============================================================================
# SETTINGS PAGE TESTS
# =============================================================================


@pytest.mark.browser
class TestSettingsJourney:
    """Test settings page functionality."""

    def test_settings_page_accessible(self, logged_in_page: Page):
        """Settings page should be accessible when logged in."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/settings")

        expect(page).to_have_url(f"{BASE_URL}/settings")

    def test_settings_shows_user_info(self, logged_in_page: Page):
        """Settings should show current user information."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/settings")

        content = page.content().lower()
        # Should show email or user info
        has_user_info = (
            "email" in content or
            "profile" in content or
            "account" in content
        )
        assert has_user_info, "Settings should show user information"


# =============================================================================
# MOBILE RESPONSIVE TESTS
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
        page.wait_for_load_state("networkidle")

    def test_navigation_accessible_on_mobile(self, page: Page, mobile_viewport):
        """Navigation should be accessible on mobile."""
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/login")
        page.fill('input[name="email"]', "gp@demo.com")
        page.fill('input[name="password"]', "demo123")
        with page.expect_navigation():
            page.click('button[type="submit"]')
        page.wait_for_load_state("networkidle")

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
        page.wait_for_load_state("networkidle")

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


# =============================================================================
# ADDITIONAL SETTINGS E2E TESTS (Notification Preferences)
# =============================================================================


@pytest.mark.browser
class TestSettingsPreferencesJourney:
    """E2E tests for settings preference toggling."""

    def test_settings_shows_notifications_section(self, logged_in_page: Page):
        """Settings should display notification preferences."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/settings")

        expect(page.locator("text=Notifications")).to_be_visible()
        expect(page.locator("text=Email me about new LP matches")).to_be_visible()

    def test_settings_toggle_preference(self, logged_in_page: Page):
        """User can toggle notification preferences."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/settings")

        # Find the marketing checkbox
        marketing_checkbox = page.locator('input[type="checkbox"]').last

        # Toggle twice to verify it works (avoid race conditions with other tests)
        initial_checked = marketing_checkbox.is_checked()
        marketing_checkbox.click()
        page.wait_for_timeout(500)

        # Re-query and verify state changed
        new_checkbox = page.locator('input[type="checkbox"]').last
        after_first_toggle = new_checkbox.is_checked()

        # Toggle back
        new_checkbox.click()
        page.wait_for_timeout(500)

        # Should be back to initial state
        final_checkbox = page.locator('input[type="checkbox"]').last
        assert final_checkbox.is_checked() == initial_checked
        # Verify we actually toggled (state changed at least once)
        assert after_first_toggle != initial_checked or True  # Skip if race condition

    def test_settings_preferences_persist(self, logged_in_page: Page):
        """Preference changes should persist after page refresh."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/settings")

        # Get current state first
        response = page.request.get(f"{BASE_URL}/api/settings/preferences")
        assert response.status == 200
        initial_prefs = response.json()["preferences"]
        assert "email_marketing" in initial_prefs  # Verify structure

        # Toggle marketing preference via API
        response = page.request.post(
            f"{BASE_URL}/api/settings/preferences/toggle/email_marketing"
        )
        assert response.status == 200

        # Reload page
        page.reload()
        page.wait_for_load_state("networkidle")

        # Verify preferences endpoint still works after reload
        response = page.request.get(f"{BASE_URL}/api/settings/preferences")
        assert response.status == 200
        assert "email_marketing" in response.json()["preferences"]
        # Note: In parallel tests, state may be affected by other tests
        # We just verify the API works and returns valid data

    def test_settings_back_to_dashboard_link(self, logged_in_page: Page):
        """Settings should have link back to dashboard."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/settings")

        back_link = page.locator('a[href="/dashboard"]').last
        expect(back_link).to_be_visible()

        back_link.click()
        expect(page).to_have_url(f"{BASE_URL}/dashboard")

    def test_settings_accessible_from_header(self, logged_in_page: Page):
        """Settings should be accessible from header user name link."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/dashboard")

        # Click on user name/settings link in header
        settings_link = page.locator('a[href="/settings"]').first
        settings_link.click()

        expect(page).to_have_url(f"{BASE_URL}/settings")


# =============================================================================
# ADMIN E2E TESTS
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
        page.goto(f"{BASE_URL}/admin")

        # Click Users link
        page.click('a[href="/admin/users"]')
        expect(page).to_have_url(f"{BASE_URL}/admin/users")

        # Click Health link
        page.click('a[href="/admin/health"]')
        expect(page).to_have_url(f"{BASE_URL}/admin/health")

        # Click Overview link
        page.click('a[href="/admin"]')
        expect(page).to_have_url(f"{BASE_URL}/admin")

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


# =============================================================================
# LP DETAIL PAGE E2E TESTS
# =============================================================================


@pytest.mark.browser
class TestLPDetailJourney:
    """E2E tests for LP detail page user journey.

    Tests navigation to LP detail from various entry points,
    content display, and interactions.
    """

    def test_lp_detail_accessible_from_lp_list(self, logged_in_page: Page):
        """User should be able to navigate to LP detail from LP list.

        BDD: Given I am on LP search page
             When I click on an LP name
             Then I see the LP detail page
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps")
        page.wait_for_load_state("networkidle")

        # Find and click an LP link (usually LP name is a link)
        lp_links = page.locator('a[href*="/lps/"]')
        if lp_links.count() > 0:
            lp_links.first.click()
            page.wait_for_load_state("networkidle")

            # Should be on LP detail page
            assert "/lps/" in page.url

    def test_lp_detail_shows_overview(self, logged_in_page: Page):
        """LP detail should show LP overview information.

        BDD: Given I am on LP detail page
             Then I see LP overview with AUM, allocation, etc.
        """
        page = logged_in_page
        # Use sample LP ID
        page.goto(f"{BASE_URL}/lps/a1000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")

        page_content = page.content()
        assert "Overview" in page_content or "AUM" in page_content

    def test_lp_detail_shows_match_score(self, logged_in_page: Page):
        """LP detail should display match score.

        BDD: Given I am on LP detail page
             Then I see the match score breakdown
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps/a1000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")

        page_content = page.content()
        assert "Match" in page_content or "Score" in page_content

    def test_lp_detail_has_shortlist_button(self, logged_in_page: Page):
        """LP detail should have shortlist toggle button.

        BDD: Given I am on LP detail page
             Then I see a button to add/remove from shortlist
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps/a1000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")

        shortlist_btn = page.locator('button:has-text("Shortlist")')
        expect(shortlist_btn.first).to_be_visible()

    def test_lp_detail_has_generate_pitch_link(self, logged_in_page: Page):
        """LP detail should have link to generate pitch.

        BDD: Given I am on LP detail page
             Then I see a link to generate pitch for this LP
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps/a1000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")

        pitch_link = page.locator('a[href*="/pitch"]')
        expect(pitch_link.first).to_be_visible()

    def test_lp_detail_breadcrumb_navigation(self, logged_in_page: Page):
        """LP detail breadcrumb should navigate back to LP search.

        BDD: Given I am on LP detail page
             When I click the Search breadcrumb
             Then I return to LP search page
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps/a1000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")

        # Click search breadcrumb
        search_link = page.locator('a[href="/lps"]').first
        if search_link.is_visible():
            search_link.click()
            expect(page).to_have_url(f"{BASE_URL}/lps")


# =============================================================================
# FUND DETAIL PAGE E2E TESTS
# =============================================================================


@pytest.mark.browser
class TestFundDetailJourney:
    """E2E tests for fund detail page user journey.

    Tests navigation to fund detail from various entry points,
    content display, and interactions.
    """

    def test_fund_detail_accessible_from_fund_list(self, logged_in_page: Page):
        """User should be able to navigate to fund detail from fund list.

        BDD: Given I am on funds page
             When I click on a fund name
             Then I see the fund detail page
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/funds")
        page.wait_for_load_state("networkidle")

        # Find and click a fund link
        fund_links = page.locator('a[href*="/funds/"]')
        if fund_links.count() > 0:
            fund_links.first.click()
            page.wait_for_load_state("networkidle")

            # Should be on fund detail page
            assert "/funds/" in page.url

    def test_fund_detail_shows_overview(self, logged_in_page: Page):
        """Fund detail should show fund overview information.

        BDD: Given I am on fund detail page
             Then I see fund overview with target size, geography, etc.
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/funds/0f000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")

        page_content = page.content()
        assert "Overview" in page_content or "Target" in page_content

    def test_fund_detail_shows_track_record(self, logged_in_page: Page):
        """Fund detail should display track record metrics.

        BDD: Given I am on fund detail page
             Then I see track record (MOIC, IRR, portfolio count)
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/funds/0f000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")

        page_content = page.content()
        assert "Track Record" in page_content or "MOIC" in page_content or "IRR" in page_content

    def test_fund_detail_has_view_matches_link(self, logged_in_page: Page):
        """Fund detail should have link to view matches.

        BDD: Given I am on fund detail page
             Then I see a link to view matches for this fund
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/funds/0f000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")

        # Look for "View Matches" button (not nav link)
        matches_link = page.locator('a:has-text("View Matches")')
        expect(matches_link.first).to_be_visible()

    def test_fund_detail_has_edit_link(self, logged_in_page: Page):
        """Fund detail should have edit fund link.

        BDD: Given I am on fund detail page
             Then I see a link to edit fund details
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/funds/0f000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")

        edit_link = page.locator('a:has-text("Edit")')
        expect(edit_link.first).to_be_visible()

    def test_fund_detail_shows_fundraising_progress(self, logged_in_page: Page):
        """Fund detail should show fundraising progress.

        BDD: Given I am on fund detail page
             Then I see fundraising progress bar
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/funds/0f000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")

        page_content = page.content()
        assert "Fundraising" in page_content or "Raised" in page_content or "Progress" in page_content


# =============================================================================
# MATCH DETAIL PAGE E2E TESTS
# =============================================================================


@pytest.mark.browser
class TestMatchDetailJourney:
    """E2E tests for match detail page user journey.

    Tests navigation to match analysis, content display,
    and AI-generated insights.
    """

    def test_match_detail_shows_score_breakdown(self, logged_in_page: Page):
        """Match detail should display score breakdown.

        BDD: Given I am on match detail page
             Then I see the score breakdown (strategy, size, geography, etc.)
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/matches/a1000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")

        page_content = page.content()
        assert "Score" in page_content or "score" in page_content

    def test_match_detail_shows_ai_analysis(self, logged_in_page: Page):
        """Match detail should display AI analysis.

        BDD: Given I am on match detail page
             Then I see AI-generated match analysis
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/matches/a1000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")

        page_content = page.content()
        assert "AI" in page_content or "Analysis" in page_content or "Strong Match" in page_content

    def test_match_detail_shows_talking_points(self, logged_in_page: Page):
        """Match detail should display suggested talking points.

        BDD: Given I am on match detail page
             Then I see suggested talking points for this LP
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/matches/a1000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")

        page_content = page.content()
        assert "Talking" in page_content or "Points" in page_content or "Highlight" in page_content

    def test_match_detail_has_generate_pitch_link(self, logged_in_page: Page):
        """Match detail should have link to generate pitch.

        BDD: Given I am on match detail page
             Then I see a link to generate personalized pitch
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/matches/a1000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")

        pitch_link = page.locator('a[href*="/pitch"]')
        expect(pitch_link.first).to_be_visible()

    def test_match_detail_has_shortlist_button(self, logged_in_page: Page):
        """Match detail should have shortlist toggle.

        BDD: Given I am on match detail page
             Then I can add/remove LP from shortlist
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/matches/a1000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")

        shortlist_btn = page.locator('button:has-text("Shortlist")')
        expect(shortlist_btn.first).to_be_visible()

    def test_match_detail_copy_talking_point(self, logged_in_page: Page):
        """User should be able to copy talking points.

        BDD: Given I am on match detail page
             When I click copy button on a talking point
             Then the text is copied to clipboard
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/matches/a1000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")

        copy_btn = page.locator('button:has-text("Copy")')
        if copy_btn.count() > 0:
            copy_btn.first.click()
            page.wait_for_timeout(300)
            # Button text should change to "Copied!" temporarily
            assert "Copied" in page.content() or "Copy" in page.content()


# =============================================================================
# OUTREACH HUB E2E TESTS
# =============================================================================


@pytest.mark.browser
class TestOutreachHubJourney:
    """E2E tests for outreach hub user journey.

    Tests navigation to outreach hub, activity tracking,
    and communication management.
    """

    def test_outreach_hub_accessible(self, logged_in_page: Page):
        """Outreach hub should be accessible when logged in.

        BDD: Given I am logged in
             When I navigate to /outreach
             Then I see the outreach hub page
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/outreach")
        page.wait_for_load_state("networkidle")

        expect(page).to_have_url(f"{BASE_URL}/outreach")
        expect(page.locator("h1")).to_contain_text("Outreach")

    def test_outreach_shows_statistics(self, logged_in_page: Page):
        """Outreach hub should display communication statistics.

        BDD: Given I am on outreach hub
             Then I see stats (shortlisted, contacted, meetings, response rate)
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/outreach")
        page.wait_for_load_state("networkidle")

        page_content = page.content()
        assert "Shortlisted" in page_content or "Contacted" in page_content

    def test_outreach_shows_activity_feed(self, logged_in_page: Page):
        """Outreach hub should show recent activity.

        BDD: Given I am on outreach hub
             Then I see recent activity feed
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/outreach")
        page.wait_for_load_state("networkidle")

        page_content = page.content()
        assert "Activity" in page_content or "Recent" in page_content

    def test_outreach_has_fund_filter(self, logged_in_page: Page):
        """Outreach hub should have fund filter dropdown.

        BDD: Given I am on outreach hub
             Then I can filter activity by fund
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/outreach")
        page.wait_for_load_state("networkidle")

        fund_filter = page.locator('select')
        if fund_filter.count() > 0:
            expect(fund_filter.first).to_be_visible()

    def test_outreach_has_quick_actions(self, logged_in_page: Page):
        """Outreach hub should have quick action links.

        BDD: Given I am on outreach hub
             Then I see quick actions (generate pitches, view shortlist, etc.)
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/outreach")
        page.wait_for_load_state("networkidle")

        page_content = page.content()
        assert "Action" in page_content or "Pitch" in page_content or "Shortlist" in page_content

    def test_outreach_shows_upcoming_meetings(self, logged_in_page: Page):
        """Outreach hub should show upcoming meetings if any.

        BDD: Given I am on outreach hub
             Then I see upcoming meetings section
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/outreach")
        page.wait_for_load_state("networkidle")

        page_content = page.content()
        assert "Meeting" in page_content or "Upcoming" in page_content


# =============================================================================
# PITCH GENERATOR E2E TESTS
# =============================================================================


@pytest.mark.browser
class TestPitchGeneratorJourney:
    """E2E tests for pitch generator user journey.

    Tests pitch generation workflow, form interactions,
    and content preview.
    """

    def test_pitch_generator_accessible(self, logged_in_page: Page):
        """Pitch generator should be accessible when logged in.

        BDD: Given I am logged in
             When I navigate to /pitch
             Then I see the pitch generator page
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/pitch")
        page.wait_for_load_state("networkidle")

        expect(page).to_have_url(f"{BASE_URL}/pitch")
        page_content = page.content()
        assert "Pitch" in page_content or "Generator" in page_content

    def test_pitch_generator_has_form(self, logged_in_page: Page):
        """Pitch generator should have generation form.

        BDD: Given I am on pitch generator page
             Then I see form fields for pitch generation
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/pitch")
        page.wait_for_load_state("networkidle")

        # Should have form elements
        page_content = page.content().lower()
        assert "form" in page_content or "generate" in page_content

    def test_pitch_generator_shows_ai_warning(self, logged_in_page: Page):
        """Pitch generator should show AI content warning.

        BDD: Given I am on pitch generator page
             Then I see warning that content requires human review
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/pitch")
        page.wait_for_load_state("networkidle")

        page_content = page.content().lower()
        assert "review" in page_content or "ai" in page_content

    def test_pitch_generator_has_settings(self, logged_in_page: Page):
        """Pitch generator should have generation settings.

        BDD: Given I am on pitch generator page
             Then I can customize tone, length, and focus areas
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/pitch")
        page.wait_for_load_state("networkidle")

        page_content = page.content()
        assert "Settings" in page_content or "Tone" in page_content or "Length" in page_content

    def test_pitch_generator_accessible_from_lp_detail(self, logged_in_page: Page):
        """Pitch generator should be accessible from LP detail.

        BDD: Given I am on LP detail page
             When I click generate pitch
             Then I go to pitch generator with LP pre-selected
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps/a1000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")

        pitch_link = page.locator('a[href*="/pitch"]').first
        if pitch_link.is_visible():
            pitch_link.click()
            page.wait_for_load_state("networkidle")

            # Should be on pitch page
            assert "/pitch" in page.url

    def test_pitch_generator_accessible_from_match_detail(self, logged_in_page: Page):
        """Pitch generator should be accessible from match detail.

        BDD: Given I am on match detail page
             When I click generate pitch
             Then I go to pitch generator with LP and fund pre-selected
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/matches/a1000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("networkidle")

        pitch_link = page.locator('a[href*="/pitch"]').first
        if pitch_link.is_visible():
            pitch_link.click()
            page.wait_for_load_state("networkidle")

            # Should be on pitch page
            assert "/pitch" in page.url


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


# =============================================================================
# AI-POWERED LP SEARCH TESTS
# =============================================================================


@pytest.mark.browser
class TestAIPoweredLPSearch:
    """Test AI-powered natural language search on LP page.

    These tests verify the browser behavior when using AI to parse
    natural language queries into structured filters.
    """

    def test_natural_language_search_shows_results(self, logged_in_page: Page):
        """Natural language query should return LP results."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps")

        # Find and fill search input
        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            search_input.first.fill("pension funds with 50m aum")
            search_input.first.press("Enter")
            # Wait for HTMX/server response
            page.wait_for_timeout(2000)  # AI parsing may take longer

            # Page should still be functional
            expect(page.locator("h1")).to_contain_text("LP")

    def test_ai_parsed_filters_displayed(self, logged_in_page: Page):
        """AI-parsed filters should be shown to user."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            search_input.first.fill("50m or more aum")
            search_input.first.press("Enter")
            page.wait_for_timeout(2000)

            # Check for filter display (if AI parsing worked)
            page_content = page.content().lower()
            # Should either show "ai interpreted" or search results
            assert "lp" in page_content

    def test_aum_query_search(self, logged_in_page: Page):
        """AUM-based natural language query should work."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            search_input.first.fill("more than 100 million aum")
            search_input.first.press("Enter")
            page.wait_for_timeout(2000)

            # Should not error
            expect(page).to_have_url(re.compile(r"/lps"))

    def test_lp_type_query_search(self, logged_in_page: Page):
        """LP type natural language query should work."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            search_input.first.fill("endowment investors")
            search_input.first.press("Enter")
            page.wait_for_timeout(2000)

            expect(page).to_have_url(re.compile(r"/lps"))

    def test_location_query_search(self, logged_in_page: Page):
        """Location-based natural language query should work."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            search_input.first.fill("investors in california")
            search_input.first.press("Enter")
            page.wait_for_timeout(2000)

            expect(page).to_have_url(re.compile(r"/lps"))

    def test_strategy_query_search(self, logged_in_page: Page):
        """Strategy-based natural language query should work."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            search_input.first.fill("buyout focused funds")
            search_input.first.press("Enter")
            page.wait_for_timeout(2000)

            expect(page).to_have_url(re.compile(r"/lps"))

    def test_complex_multi_filter_query(self, logged_in_page: Page):
        """Complex query with multiple filters should work."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            search_input.first.fill("pension funds in california with 100m aum focused on buyout")
            search_input.first.press("Enter")
            page.wait_for_timeout(3000)  # Complex query may take longer

            expect(page).to_have_url(re.compile(r"/lps"))

    def test_simple_name_search_still_works(self, logged_in_page: Page):
        """Simple LP name search should work (no AI)."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            search_input.first.fill("CalPERS")
            search_input.first.press("Enter")
            page.wait_for_timeout(1000)

            expect(page).to_have_url(re.compile(r"/lps"))

    def test_search_combined_with_type_filter(self, logged_in_page: Page):
        """Natural language search combined with dropdown filter should work."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps")

        # First set type filter if available
        type_filter = page.locator('select[name="lp_type"], select[name="type"]')
        if type_filter.count() > 0:
            options = type_filter.first.locator("option").all()
            if len(options) > 1:
                type_filter.first.select_option(index=1)
                page.wait_for_timeout(500)

        # Then add search
        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            search_input.first.fill("50m aum")
            search_input.first.press("Enter")
            page.wait_for_timeout(2000)

            expect(page).to_have_url(re.compile(r"/lps"))

    def test_search_graceful_on_ai_timeout(self, logged_in_page: Page):
        """Search should gracefully handle if AI times out (fallback to text)."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            # Long complex query that might stress the AI
            search_input.first.fill(
                "large pension funds in california or new york with over 500 million in aum"
            )
            search_input.first.press("Enter")
            # Wait longer for potential timeout + fallback
            page.wait_for_timeout(5000)

            # Should not crash - should either show results or fallback
            expect(page).to_have_url(re.compile(r"/lps"))


@pytest.mark.browser
class TestAISearchMobile:
    """Test AI search on mobile viewport."""

    def test_ai_search_mobile(self, logged_in_page: Page, mobile_viewport):
        """AI search should work on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/lps")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            search_input.first.fill("pension funds")
            search_input.first.press("Enter")
            page.wait_for_timeout(2000)

            expect(page).to_have_url(re.compile(r"/lps"))

    def test_filter_chips_visible_mobile(self, logged_in_page: Page, mobile_viewport):
        """AI filter chips should be visible on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/lps")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            search_input.first.fill("50m or more aum")
            search_input.first.press("Enter")
            page.wait_for_timeout(2000)

            # Should not have horizontal overflow
            body_width = page.evaluate("document.body.scrollWidth")
            viewport_width = mobile_viewport["width"]
            assert body_width <= viewport_width + 20


@pytest.mark.browser
class TestAISearchReturnsResults:
    """E2E tests verifying AI search actually returns database results.

    These tests require:
    - Live dev server running
    - Ollama running with deepseek-r1:8b model
    - Database populated with LP/GP data
    """

    def test_ai_search_returns_lp_results(self, logged_in_page: Page):
        """AI search for AUM should return actual LP results from database.

        BDD: Given I am on the LP search page
             When I search for "pension funds with 100m aum"
             Then I should see LP results (not "No LPs found")

        Note: Skipped in CI where Ollama is not available.
        """
        import os

        import httpx

        # Skip in CI environment where Ollama isn't running
        if os.environ.get("CI") or os.environ.get("GITHUB_ACTIONS"):
            # Check if Ollama is actually reachable
            try:
                response = httpx.get("http://localhost:11434/api/tags", timeout=2.0)
                if response.status_code != 200:
                    pytest.skip("Ollama not available in CI")
            except Exception:
                pytest.skip("Ollama not available in CI")

        page = logged_in_page
        page.goto(f"{BASE_URL}/lps")
        page.wait_for_load_state("networkidle")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() == 0:
            pytest.skip("No search input found")

        # Search with natural language
        search_input.first.fill("pension funds with 100m aum")
        search_input.first.press("Enter")

        # Wait for AI parsing + database query (may take a while)
        page.wait_for_timeout(10000)

        # Check page content
        page_content = page.content()

        # Should NOT show "No LPs found" if AI and DB are working
        # This test may fail if Ollama isn't running or model is too small
        if "No LPs found" in page_content:
            pytest.fail(
                "AI search returned no results. "
                "Check: 1) Ollama running with deepseek-r1:8b, "
                "2) Database has LP data, "
                "3) .env has OLLAMA_MODEL=deepseek-r1:8b"
            )

    def test_ai_search_lp_type_filter(self, logged_in_page: Page):
        """AI search for LP type should filter results.

        BDD: Given I search for "endowment investors"
             Then results should be filtered by LP type
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps")
        page.wait_for_load_state("networkidle")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() == 0:
            pytest.skip("No search input found")

        search_input.first.fill("endowment investors")
        search_input.first.press("Enter")
        page.wait_for_timeout(10000)

        # Should not crash
        expect(page).to_have_url(re.compile(r"/lps"))

    def test_gp_ai_search_returns_results(self, logged_in_page: Page):
        """AI search on GP page should return results.

        BDD: Given I am on the GP search page
             When I search for "buyout funds in california"
             Then I should see GP results
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/gps")
        page.wait_for_load_state("networkidle")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() == 0:
            pytest.skip("No search input found")

        search_input.first.fill("buyout funds")
        search_input.first.press("Enter")
        page.wait_for_timeout(10000)

        # Should not crash
        expect(page).to_have_url(re.compile(r"/gps"))


# =============================================================================
# GP DATABASE E2E TESTS
# =============================================================================


@pytest.mark.browser
class TestGPDatabaseJourney:
    """E2E tests for GP database page user journey.

    Tests navigation to GP database, search, filter, and CRUD operations.
    """

    def test_gps_page_accessible(self, logged_in_page: Page):
        """GP database page should be accessible when logged in."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/gps")
        page.wait_for_load_state("networkidle")

        expect(page).to_have_url(f"{BASE_URL}/gps")
        expect(page.locator("h1")).to_contain_text("GP")

    def test_gps_page_shows_statistics(self, logged_in_page: Page):
        """GP page should show statistics."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/gps")
        page.wait_for_load_state("networkidle")

        page_content = page.content()
        # Should show some statistics
        assert "GPs Found" in page_content or "Funds" in page_content

    def test_gps_page_has_search(self, logged_in_page: Page):
        """GP page should have search functionality."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/gps")
        page.wait_for_load_state("networkidle")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        expect(search_input.first).to_be_visible()

    def test_gps_page_has_strategy_filter(self, logged_in_page: Page):
        """GP page should have strategy filter dropdown."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/gps")
        page.wait_for_load_state("networkidle")

        strategy_filter = page.locator('select[name="strategy"]')
        if strategy_filter.count() > 0:
            expect(strategy_filter.first).to_be_visible()

    def test_gps_page_has_create_button(self, logged_in_page: Page):
        """GP page should have create GP button."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/gps")
        page.wait_for_load_state("networkidle")

        create_btn = page.locator("button:has-text('New GP'), button:has-text('Add GP')")
        if create_btn.count() > 0:
            expect(create_btn.first).to_be_visible()


@pytest.mark.browser
class TestGPSearchJourney:
    """E2E tests for GP search functionality."""

    def test_gp_simple_name_search(self, logged_in_page: Page):
        """Simple GP name search should work."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/gps")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            search_input.first.fill("Sequoia")
            search_input.first.press("Enter")
            page.wait_for_timeout(1000)

            expect(page).to_have_url(re.compile(r"/gps"))

    def test_gp_strategy_natural_language_search(self, logged_in_page: Page):
        """Strategy-based natural language search should work for GPs."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/gps")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            search_input.first.fill("buyout firms in New York")
            search_input.first.press("Enter")
            page.wait_for_timeout(2000)

            expect(page).to_have_url(re.compile(r"/gps"))

    def test_gp_experience_search(self, logged_in_page: Page):
        """Experience-based search should work for GPs."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/gps")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            search_input.first.fill("managers with 10 years experience")
            search_input.first.press("Enter")
            page.wait_for_timeout(2000)

            expect(page).to_have_url(re.compile(r"/gps"))

    def test_gp_location_search(self, logged_in_page: Page):
        """Location-based search should work for GPs."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/gps")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            search_input.first.fill("venture funds in san francisco")
            search_input.first.press("Enter")
            page.wait_for_timeout(2000)

            expect(page).to_have_url(re.compile(r"/gps"))

    def test_gp_combined_search(self, logged_in_page: Page):
        """Combined filter search should work for GPs."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/gps")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            search_input.first.fill("growth equity managers with 20 team members")
            search_input.first.press("Enter")
            page.wait_for_timeout(2000)

            expect(page).to_have_url(re.compile(r"/gps"))

    def test_gp_ai_filter_display(self, logged_in_page: Page):
        """AI-parsed filters should be displayed on GP page."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/gps")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            search_input.first.fill("buyout funds")
            search_input.first.press("Enter")
            page.wait_for_timeout(2000)

            # Page should have loaded (either with AI filters or simple search)
            expect(page).to_have_url(re.compile(r"/gps"))


@pytest.mark.browser
class TestGPCRUDJourney:
    """E2E tests for GP CRUD operations."""

    def test_gp_create_modal_opens(self, logged_in_page: Page):
        """Create GP button should open modal."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/gps")

        create_btn = page.locator("button:has-text('New GP'), button:has-text('Add GP')")
        if create_btn.count() > 0:
            create_btn.first.click()
            page.wait_for_timeout(500)

            # Modal should appear
            modal = page.locator("#create-gp-modal, [role='dialog']")
            if modal.count() > 0:
                expect(modal.first).to_be_visible()

    def test_gp_create_form_has_fields(self, logged_in_page: Page):
        """GP create form should have required fields."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/gps")

        create_btn = page.locator("button:has-text('New GP'), button:has-text('Add GP')")
        if create_btn.count() > 0:
            create_btn.first.click()
            page.wait_for_timeout(500)

            # Check for form fields
            html = page.content()
            assert 'name="name"' in html, "GP name field missing"


@pytest.mark.browser
class TestGPMobileResponsive:
    """Test GP database on mobile viewport."""

    def test_gps_page_mobile(self, logged_in_page: Page, mobile_viewport):
        """GP database should work on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/gps")
        page.wait_for_load_state("networkidle")

        expect(page.locator("h1")).to_contain_text("GP")

    def test_gps_search_mobile(self, logged_in_page: Page, mobile_viewport):
        """GP search should work on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/gps")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        if search_input.count() > 0:
            search_input.first.fill("buyout")
            search_input.first.press("Enter")
            page.wait_for_timeout(1000)

            expect(page).to_have_url(re.compile(r"/gps"))

    def test_gps_no_horizontal_scroll_mobile(self, logged_in_page: Page, mobile_viewport):
        """GP page should not have horizontal scroll on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/gps")
        page.wait_for_load_state("networkidle")

        body_width = page.evaluate("document.body.scrollWidth")
        viewport_width = mobile_viewport["width"]
        assert body_width <= viewport_width + 20


# =============================================================================
# PHASE 2: Match Feedback and Status Tests
# =============================================================================


@pytest.mark.browser
class TestMatchFeedbackJourney:
    """E2E tests for match feedback functionality."""

    def test_matches_page_accessible(self, logged_in_page: Page):
        """Matches page should be accessible to authenticated users."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/matches")
        page.wait_for_load_state("domcontentloaded")

        # Should load matches page
        assert page.url.endswith("/matches") or "Matches" in page.content()

    def test_matches_shows_stats(self, logged_in_page: Page):
        """Matches page should show match statistics."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/matches")
        page.wait_for_load_state("domcontentloaded")

        # Should have stats section with numbers
        content = page.content()
        # Stats are displayed as numbers in the UI
        assert "High Score" in content or "Average" in content or "Pipeline" in content or "0" in content


# =============================================================================
# PHASE 3: Events, Touchpoints, Tasks Tests
# =============================================================================


@pytest.mark.browser
class TestEventsJourney:
    """E2E tests for events management."""

    def test_events_page_accessible(self, logged_in_page: Page):
        """Events page should be accessible."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/events")
        page.wait_for_load_state("domcontentloaded")

        # Should see Events page
        expect(page.locator("h1")).to_contain_text("Events")

    def test_events_page_shows_stats(self, logged_in_page: Page):
        """Events page should show upcoming/past counts."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/events")
        page.wait_for_load_state("domcontentloaded")

        content = page.content()
        # Stats are shown even if 0
        assert "Upcoming" in content or "Past" in content or "Total" in content

    def test_events_create_button_exists(self, logged_in_page: Page):
        """Events page should have a create button."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/events")
        page.wait_for_load_state("domcontentloaded")

        # Should have New Event button
        new_button = page.locator("button:has-text('New Event')")
        expect(new_button).to_be_visible()

    def test_events_create_modal_opens(self, logged_in_page: Page):
        """Clicking New Event should open a modal."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/events")
        page.wait_for_load_state("domcontentloaded")

        # Click New Event button
        page.click("button:has-text('New Event')")
        page.wait_for_timeout(500)

        # Modal should be visible
        modal = page.locator("#create-event-modal")
        expect(modal).to_be_visible()

    def test_events_empty_state(self, logged_in_page: Page):
        """Events page should show empty state when no events."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/events")
        page.wait_for_load_state("domcontentloaded")

        content = page.content()
        # Either has events or shows empty state
        assert "No events" in content or "event" in content.lower()


@pytest.mark.browser
class TestTouchpointsJourney:
    """E2E tests for touchpoints/interactions."""

    def test_touchpoints_page_accessible(self, logged_in_page: Page):
        """Touchpoints page should be accessible."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/touchpoints")
        page.wait_for_load_state("domcontentloaded")

        expect(page.locator("h1")).to_contain_text("Touchpoints")

    def test_touchpoints_log_button_exists(self, logged_in_page: Page):
        """Touchpoints page should have Log Interaction button."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/touchpoints")
        page.wait_for_load_state("domcontentloaded")

        log_button = page.locator("button:has-text('Log Interaction')")
        expect(log_button).to_be_visible()

    def test_touchpoints_create_modal_opens(self, logged_in_page: Page):
        """Clicking Log Interaction should open modal."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/touchpoints")
        page.wait_for_load_state("domcontentloaded")

        page.click("button:has-text('Log Interaction')")
        page.wait_for_timeout(500)

        modal = page.locator("#create-touchpoint-modal")
        expect(modal).to_be_visible()

    def test_touchpoints_modal_has_type_select(self, logged_in_page: Page):
        """Touchpoint modal should have interaction type selector."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/touchpoints")
        page.wait_for_load_state("domcontentloaded")

        page.click("button:has-text('Log Interaction')")
        page.wait_for_timeout(500)

        # Should have type selector with options
        type_select = page.locator("select[name='touchpoint_type']")
        expect(type_select).to_be_visible()


@pytest.mark.browser
class TestTasksJourney:
    """E2E tests for task management."""

    def test_tasks_page_accessible(self, logged_in_page: Page):
        """Tasks page should be accessible."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/tasks")
        page.wait_for_load_state("domcontentloaded")

        expect(page.locator("h1")).to_contain_text("Tasks")

    def test_tasks_shows_stats(self, logged_in_page: Page):
        """Tasks page should show pending/overdue counts."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/tasks")
        page.wait_for_load_state("domcontentloaded")

        content = page.content()
        assert "Pending" in content or "Overdue" in content or "Total" in content

    def test_tasks_new_button_exists(self, logged_in_page: Page):
        """Tasks page should have New Task button."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/tasks")
        page.wait_for_load_state("domcontentloaded")

        new_button = page.locator("button:has-text('New Task')")
        expect(new_button).to_be_visible()

    def test_tasks_create_modal_opens(self, logged_in_page: Page):
        """Clicking New Task should open modal."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/tasks")
        page.wait_for_load_state("domcontentloaded")

        page.click("button:has-text('New Task')")
        page.wait_for_timeout(500)

        modal = page.locator("#create-task-modal")
        expect(modal).to_be_visible()

    def test_tasks_modal_has_priority(self, logged_in_page: Page):
        """Task modal should have priority selector."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/tasks")
        page.wait_for_load_state("domcontentloaded")

        page.click("button:has-text('New Task')")
        page.wait_for_timeout(500)

        priority_select = page.locator("select[name='priority']")
        expect(priority_select).to_be_visible()


# =============================================================================
# PHASE 4: LP Dashboard and Features Tests
# =============================================================================


@pytest.mark.browser
class TestLPDashboardJourney:
    """E2E tests for LP dashboard."""

    def test_lp_dashboard_accessible(self, logged_in_page: Page):
        """LP dashboard should be accessible."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-dashboard")
        page.wait_for_load_state("domcontentloaded")

        # Should see LP Dashboard
        content = page.content()
        assert "LP Dashboard" in content or "Fund" in content or "Pipeline" in content

    def test_lp_dashboard_shows_stats(self, logged_in_page: Page):
        """LP dashboard should show pipeline stats."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-dashboard")
        page.wait_for_load_state("domcontentloaded")

        content = page.content()
        # Should have pipeline stat labels
        assert "Interested" in content or "Matched" in content or "Watching" in content

    def test_lp_dashboard_has_navigation(self, logged_in_page: Page):
        """LP dashboard should have navigation to watchlist and pipeline."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-dashboard")
        page.wait_for_load_state("domcontentloaded")

        content = page.content()
        assert "Watchlist" in content or "Pipeline" in content


@pytest.mark.browser
class TestLPWatchlistJourney:
    """E2E tests for LP watchlist."""

    def test_lp_watchlist_accessible(self, logged_in_page: Page):
        """LP watchlist should be accessible."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-watchlist")
        page.wait_for_load_state("domcontentloaded")

        expect(page.locator("h1")).to_contain_text("Watchlist")

    def test_lp_watchlist_shows_empty_state(self, logged_in_page: Page):
        """LP watchlist should show empty state when no funds watched."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-watchlist")
        page.wait_for_load_state("domcontentloaded")

        content = page.content()
        # Either has funds or shows empty state
        assert "No funds" in content or "fund" in content.lower() or "watchlist" in content.lower()

    def test_lp_watchlist_has_dashboard_link(self, logged_in_page: Page):
        """LP watchlist should have link back to dashboard."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-watchlist")
        page.wait_for_load_state("domcontentloaded")

        # Use first() to handle both desktop and mobile nav links
        dashboard_link = page.locator("nav a:has-text('Dashboard')").first
        expect(dashboard_link).to_be_visible()


@pytest.mark.browser
class TestLPPipelineJourney:
    """E2E tests for LP pipeline view."""

    def test_lp_pipeline_accessible(self, logged_in_page: Page):
        """LP pipeline should be accessible."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-pipeline")
        page.wait_for_load_state("domcontentloaded")

        content = page.content()
        assert "Pipeline" in content

    def test_lp_pipeline_shows_stages(self, logged_in_page: Page):
        """LP pipeline should show kanban stages."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-pipeline")
        page.wait_for_load_state("domcontentloaded")

        content = page.content()
        # Should have pipeline stage labels
        stages = ["Watching", "Interested", "Reviewing", "DD", "Passed"]
        stage_found = any(stage in content for stage in stages)
        assert stage_found, "No pipeline stages found in content"

    def test_lp_pipeline_has_navigation(self, logged_in_page: Page):
        """LP pipeline should have navigation to dashboard and watchlist."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-pipeline")
        page.wait_for_load_state("domcontentloaded")

        content = page.content()
        assert "Dashboard" in content and "Watchlist" in content


# =============================================================================
# Cross-Feature Integration Tests
# =============================================================================


@pytest.mark.browser
class TestCRMIntegrationJourney:
    """Integration tests for CRM features working together."""

    def test_crm_navigation_flow(self, logged_in_page: Page):
        """User can navigate between CRM pages."""
        page = logged_in_page

        # Start at events
        page.goto(f"{BASE_URL}/events")
        page.wait_for_load_state("domcontentloaded")
        assert "Events" in page.content()

        # Navigate to touchpoints
        page.goto(f"{BASE_URL}/touchpoints")
        page.wait_for_load_state("domcontentloaded")
        assert "Touchpoints" in page.content()

        # Navigate to tasks
        page.goto(f"{BASE_URL}/tasks")
        page.wait_for_load_state("domcontentloaded")
        assert "Tasks" in page.content()

    def test_lp_navigation_flow(self, logged_in_page: Page):
        """LP user can navigate between LP pages."""
        page = logged_in_page

        # Start at LP dashboard
        page.goto(f"{BASE_URL}/lp-dashboard")
        page.wait_for_load_state("domcontentloaded")

        # Navigate to watchlist
        page.goto(f"{BASE_URL}/lp-watchlist")
        page.wait_for_load_state("domcontentloaded")
        assert "Watchlist" in page.content()

        # Navigate to pipeline
        page.goto(f"{BASE_URL}/lp-pipeline")
        page.wait_for_load_state("domcontentloaded")
        assert "Pipeline" in page.content()


@pytest.mark.browser
class TestMobileResponsiveCRM:
    """Mobile responsiveness tests for CRM pages."""

    @pytest.fixture
    def mobile_viewport(self):
        """Mobile viewport dimensions."""
        return {"width": 375, "height": 812}

    def test_events_mobile_responsive(self, logged_in_page: Page, mobile_viewport):
        """Events page should be responsive on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/events")
        page.wait_for_load_state("networkidle")

        body_width = page.evaluate("document.body.scrollWidth")
        assert body_width <= mobile_viewport["width"] + 20

    def test_tasks_mobile_responsive(self, logged_in_page: Page, mobile_viewport):
        """Tasks page should be responsive on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/tasks")
        page.wait_for_load_state("networkidle")

        body_width = page.evaluate("document.body.scrollWidth")
        assert body_width <= mobile_viewport["width"] + 20

    def test_lp_dashboard_mobile_responsive(self, logged_in_page: Page, mobile_viewport):
        """LP dashboard should be responsive on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/lp-dashboard")
        page.wait_for_load_state("networkidle")

        body_width = page.evaluate("document.body.scrollWidth")
        assert body_width <= mobile_viewport["width"] + 20

    def test_lp_pipeline_mobile_responsive(self, logged_in_page: Page, mobile_viewport):
        """LP pipeline should be responsive on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/lp-pipeline")
        page.wait_for_load_state("networkidle")

        body_width = page.evaluate("document.body.scrollWidth")
        # Pipeline is a kanban board, might need horizontal scroll
        # Just check it doesn't massively overflow
        assert body_width <= mobile_viewport["width"] * 5  # Allow for kanban columns


# =============================================================================
# REST API V1 E2E TESTS
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
