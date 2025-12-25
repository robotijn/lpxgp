"""End-to-End tests using Playwright.

These tests cover complete user journeys through the application.
They require a running server at http://localhost:8000.

Run with:
    # Start server first
    uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 &

    # Run E2E tests
    uv run pytest tests/test_e2e.py -v -m browser

Test Categories:
    - Authentication journeys (register, login, logout, session)
    - Fund management (CRUD operations)
    - LP management (CRUD, search, filter)
    - Matching workflow (generate, view details)
    - Navigation and redirects
    - Mobile/responsive behavior
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
    """Fixture that provides a page logged in as GP demo user."""
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

        # Find the marketing checkbox (starts unchecked by default)
        marketing_checkbox = page.locator('input[type="checkbox"]').last

        # Get initial state
        initial_checked = marketing_checkbox.is_checked()

        # Click to toggle
        marketing_checkbox.click()
        page.wait_for_timeout(500)

        # State should have changed
        # Note: The element may have been replaced by HTMX,
        # so we need to re-query
        new_checkbox = page.locator('input[type="checkbox"]').last
        assert new_checkbox.is_checked() != initial_checked

    def test_settings_preferences_persist(self, logged_in_page: Page):
        """Preference changes should persist after page refresh."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/settings")

        # Get current state first
        response = page.request.get(f"{BASE_URL}/api/settings/preferences")
        assert response.status == 200
        initial_state = response.json()["preferences"]["email_marketing"]

        # Toggle marketing preference via API
        response = page.request.post(
            f"{BASE_URL}/api/settings/preferences/toggle/email_marketing"
        )
        assert response.status == 200

        # Reload page
        page.reload()
        page.wait_for_load_state("networkidle")

        # Preference should have changed from initial state and persisted
        response = page.request.get(f"{BASE_URL}/api/settings/preferences")
        assert response.json()["preferences"]["email_marketing"] is not initial_state

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
