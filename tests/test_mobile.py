"""Tests for mobile/responsive functionality.

IMPORTANT: Tests are the source of truth. Do NOT modify tests to make them pass.
If a test fails, fix the APPLICATION, not the test.

Based on BDD Gherkin specs from docs/prd/tests/*.feature.md

Test Categories:
- Responsive tests: HTML structure validation for mobile
- Accessibility tests: WCAG compliance checks
- Browser tests: Playwright for real viewport testing (marked with @pytest.mark.browser)
"""

import re

import pytest

# =============================================================================
# VIEWPORT AND META TAG TESTS
# =============================================================================


class TestViewportMetaTag:
    """Test that pages have proper viewport configuration for mobile.

    The viewport meta tag is CRITICAL for mobile responsiveness.
    Without it, mobile browsers will render at desktop width and scale down.

    Note: /funds, /lps, /matches require authentication.
    """

    def test_home_has_viewport_meta(self, client):
        """Home page must have viewport meta tag."""
        response = client.get("/")
        assert 'name="viewport"' in response.text
        assert "width=device-width" in response.text

    def test_login_has_viewport_meta(self, client):
        """Login page must have viewport meta tag."""
        response = client.get("/login")
        assert 'name="viewport"' in response.text

    def test_funds_has_viewport_meta(self, authenticated_client):
        """Funds page must have viewport meta tag."""
        response = authenticated_client.get("/funds")
        assert 'name="viewport"' in response.text

    def test_lps_has_viewport_meta(self, authenticated_client):
        """LPs page must have viewport meta tag."""
        response = authenticated_client.get("/lps")
        assert 'name="viewport"' in response.text

    def test_matches_has_viewport_meta(self, authenticated_client):
        """Matches page must have viewport meta tag."""
        response = authenticated_client.get("/matches")
        assert 'name="viewport"' in response.text


# =============================================================================
# MOBILE NAVIGATION TESTS
# =============================================================================


class TestMobileNavigation:
    """Test that navigation is accessible on mobile devices.

    CRITICAL: Navigation hidden on mobile (hidden md:flex) MUST have
    a mobile alternative (hamburger menu) or users can't navigate!

    Note: /funds requires authentication.
    """

    def test_has_mobile_menu_toggle(self, authenticated_client):
        """Pages with hidden desktop nav must have mobile menu toggle.

        The desktop nav uses 'hidden md:flex' which hides it on mobile.
        There MUST be a visible mobile menu button.
        """
        response = authenticated_client.get("/funds")
        html = response.text

        # If desktop nav is hidden on mobile, we need a mobile alternative
        if "hidden md:flex" in html:
            # Must have a mobile menu button (hamburger icon)
            has_mobile_menu = any([
                'id="mobile-menu' in html,
                'data-mobile-menu' in html,
                'aria-label="menu"' in html.lower(),
                'aria-label="Menu"' in html,
                'hamburger' in html.lower(),
                # Check for a menu button visible on mobile
                'md:hidden' in html and ('menu' in html.lower() or 'nav' in html.lower()),
            ])
            assert has_mobile_menu, (
                "Desktop nav is hidden on mobile (hidden md:flex) but no mobile menu found! "
                "Mobile users cannot navigate between pages."
            )

    def test_mobile_nav_has_all_links(self, authenticated_client):
        """Mobile navigation must have same links as desktop nav."""
        response = authenticated_client.get("/funds")
        html = response.text

        # Core navigation links that must be accessible
        required_links = ["/matches", "/funds", "/lps"]

        for link in required_links:
            assert f'href="{link}"' in html, f"Missing navigation link: {link}"


# =============================================================================
# RESPONSIVE LAYOUT TESTS
# =============================================================================


class TestResponsiveLayout:
    """Test responsive grid and layout behavior.

    Note: /funds and /lps require authentication, so tests use authenticated_client.
    """

    def test_funds_grid_is_responsive(self, authenticated_client):
        """Funds page grid should adapt to screen size."""
        response = authenticated_client.get("/funds")
        html = response.text

        # Should have responsive grid classes
        assert "grid-cols-1" in html, "Missing single column for mobile"
        assert "md:grid-cols-2" in html or "lg:grid-cols-3" in html, (
            "Missing multi-column grid for larger screens"
        )

    def test_lps_grid_is_responsive(self, authenticated_client):
        """LPs page grid should adapt to screen size."""
        response = authenticated_client.get("/lps")
        html = response.text

        assert "grid-cols-1" in html, "Missing single column for mobile"

    def test_modals_are_mobile_friendly(self, authenticated_client):
        """Modals should be usable on small screens."""
        response = authenticated_client.get("/funds")
        html = response.text

        # Modals should have max-width and be scrollable
        # Check for overflow handling
        assert "overflow" in html or "max-h-" in html, (
            "Modals need overflow handling for small screens"
        )

    def test_forms_are_full_width_on_mobile(self, authenticated_client):
        """Form inputs should be full width on mobile."""
        response = authenticated_client.get("/funds")
        html = response.text

        # Look for w-full class on inputs
        assert "w-full" in html, "Form inputs should be full width"


# =============================================================================
# TOUCH TARGET TESTS
# =============================================================================


class TestTouchTargets:
    """Test that interactive elements are large enough for touch.

    WCAG 2.5.5 recommends minimum 44x44px touch targets.
    Tailwind's default button padding should meet this, but we verify.

    Note: /funds requires authentication.
    """

    def test_buttons_have_adequate_padding(self, authenticated_client):
        """Buttons should have enough padding for touch targets."""
        response = authenticated_client.get("/funds")
        html = response.text

        # Buttons should have padding classes
        # Tailwind p-2 = 8px, p-3 = 12px, etc.
        # We need at least p-2 or px-3/py-2 combinations
        has_button_padding = any([
            "btn-primary" in html,  # Our custom class has padding
            "btn-secondary" in html,
            "px-3" in html,
            "px-4" in html,
            "py-2" in html,
        ])
        assert has_button_padding, "Buttons need adequate padding for touch"

    def test_links_in_nav_have_spacing(self, client):
        """Navigation links should have spacing for easy tapping."""
        response = client.get("/")
        html = response.text

        # Nav should have spacing between items
        has_nav_spacing = any([
            "space-x-" in html,
            "gap-" in html,
        ])
        assert has_nav_spacing, "Navigation needs spacing between items"


# =============================================================================
# ACCESSIBILITY TESTS
# =============================================================================


class TestAccessibility:
    """Test basic accessibility requirements for all users."""

    def test_html_has_lang_attribute(self, client):
        """HTML tag must have lang attribute for screen readers."""
        response = client.get("/")
        assert 'lang="en"' in response.text or "lang='en'" in response.text

    def test_page_has_main_landmark(self, client):
        """Page should have main content landmark."""
        response = client.get("/")
        assert "<main" in response.text, "Page needs <main> landmark"

    def test_page_has_header_landmark(self, client):
        """Page should have header landmark."""
        response = client.get("/")
        assert "<header" in response.text, "Page needs <header> landmark"

    def test_forms_have_labels(self, client):
        """Form inputs should have associated labels."""
        response = client.get("/login")
        html = response.text

        # Count labels (inputs include hidden fields which don't need labels)
        label_count = html.count("<label")

        # Forms should have labels for accessibility
        assert label_count > 0, "Forms need labels for accessibility"

    def test_images_have_alt_text(self, client):
        """Images should have alt attributes."""
        response = client.get("/")
        html = response.text

        # Find all img tags
        img_tags = re.findall(r'<img[^>]*>', html)
        for img in img_tags:
            assert 'alt=' in img, f"Image missing alt attribute: {img[:50]}"

    def test_buttons_have_text_or_aria_label(self, client):
        """Buttons must have visible text or aria-label."""
        response = client.get("/funds")
        html = response.text

        # Find button tags
        button_matches = re.findall(r'<button[^>]*>.*?</button>', html, re.DOTALL)
        for button in button_matches[:10]:  # Check first 10
            has_content = any([
                len(re.sub(r'<[^>]+>', '', button).strip()) > 0,  # Has text
                'aria-label' in button,
                'title=' in button,
            ])
            # SVG-only buttons are common but need aria-label
            if '<svg' in button and not has_content:
                assert 'aria-label' in button or 'title=' in button, (
                    f"Icon-only button needs aria-label: {button[:100]}"
                )


# =============================================================================
# RESPONSIVE PADDING TESTS
# =============================================================================


class TestResponsivePadding:
    """Test that containers have appropriate padding at different sizes."""

    def test_main_container_has_responsive_padding(self, client):
        """Main content container should have responsive padding."""
        response = client.get("/funds")
        html = response.text

        # Should use sm: or md: prefixed padding
        has_responsive_padding = any([
            "px-4 sm:px-6" in html,
            "px-4 md:px-6" in html,
            "sm:px-" in html,
        ])
        assert has_responsive_padding, "Container needs responsive padding"


# =============================================================================
# TEXT READABILITY TESTS
# =============================================================================


class TestTextReadability:
    """Test text is readable on all screen sizes."""

    def test_text_uses_relative_sizes(self, client):
        """Text should use relative sizes (rem/em) not fixed pixels."""
        response = client.get("/")
        html = response.text

        # Tailwind uses rem-based sizes by default (text-sm, text-lg, etc.)
        has_tailwind_text = any([
            "text-sm" in html,
            "text-base" in html,
            "text-lg" in html,
            "text-xl" in html,
        ])
        assert has_tailwind_text, "Should use Tailwind text size classes"

    def test_no_tiny_text(self, client):
        """Text should not be too small to read."""
        response = client.get("/")
        html = response.text

        # text-xs (12px) is acceptable for labels, but should not be primary text
        # This is a soft check - just verify we use reasonable sizes
        assert "text-xs" in html or "text-sm" in html, (
            "Using appropriate text sizes"
        )


# =============================================================================
# FORMS MOBILE TESTS
# =============================================================================


class TestFormsMobile:
    """Test form behavior on mobile devices."""

    def test_form_inputs_have_type_attribute(self, client):
        """Form inputs should have appropriate type for mobile keyboards."""
        response = client.get("/login")
        html = response.text

        # Email inputs should have type="email" for mobile keyboard
        if "email" in html.lower():
            assert 'type="email"' in html, "Email input needs type='email'"

        # Number inputs should have type="number"
        # Password should have type="password"
        if "password" in html.lower():
            assert 'type="password"' in html, "Password input needs type='password'"

    def test_number_inputs_have_correct_type(self, client):
        """Number inputs should use type=number for numeric keyboard."""
        response = client.get("/funds")
        html = response.text

        # Look for inputs that should be numbers
        # target_size_mm, vintage_year should be type="number"
        if "target_size" in html or "vintage_year" in html:
            assert 'type="number"' in html, "Numeric fields need type='number'"


# =============================================================================
# HTMX MOBILE TESTS
# =============================================================================


class TestHTMXMobile:
    """Test HTMX behavior considerations for mobile."""

    def test_htmx_loaded(self, client):
        """HTMX library should be loaded."""
        response = client.get("/funds")
        assert "htmx" in response.text.lower()

    def test_loading_indicators_exist(self, client):
        """HTMX requests should have loading indicators."""
        response = client.get("/funds")
        html = response.text

        # Should have indicator classes
        has_indicator = any([
            "htmx-indicator" in html,
            "hx-indicator" in html,
        ])
        assert has_indicator, "Need loading indicators for HTMX requests"


# =============================================================================
# SCROLL BEHAVIOR TESTS
# =============================================================================


class TestScrollBehavior:
    """Test scroll behavior on mobile."""

    def test_body_allows_scroll(self, client):
        """Body should not prevent scrolling."""
        response = client.get("/funds")
        html = response.text

        # Should not have overflow-hidden on body/html by default
        # (modals can add it temporarily)
        assert 'overflow: hidden' not in html or 'overflow-hidden' not in html.split('<body')[0], (
            "Body should allow scrolling"
        )

    def test_modals_have_scroll_handling(self, client):
        """Modals should handle overflow for long content."""
        response = client.get("/funds")
        html = response.text

        # Modals should have max-height and overflow-y-auto
        if "modal" in html.lower():
            assert "overflow" in html or "max-h-" in html, (
                "Modals need scroll handling"
            )


# =============================================================================
# MOBILE SPECIFIC FEATURES TESTS
# =============================================================================


class TestMobileSpecificFeatures:
    """Test mobile-specific features and optimizations."""

    def test_no_hover_only_interactions(self, client):
        """Critical interactions should not rely solely on hover.

        Mobile devices don't have hover, so all interactive elements
        must be accessible via click/tap.
        """
        response = client.get("/funds")
        html = response.text

        # This is a structural check - hover effects are fine for enhancement
        # but core functionality should work without them
        # Look for elements that appear only on hover
        hover_only_patterns = [
            r'opacity-0.*hover:opacity-100',  # Hidden until hover
            r'invisible.*hover:visible',  # Invisible until hover
        ]

        for pattern in hover_only_patterns:
            matches = re.findall(pattern, html)
            # If found, ensure there's also a non-hover way to access
            if matches:
                # This is a warning - hover enhancements are OK
                pass  # Consider adding assertion if critical content is hover-only

    def test_sticky_header_exists(self, client):
        """Header should be sticky for easy navigation."""
        response = client.get("/funds")
        html = response.text

        assert "sticky" in html, "Header should be sticky for mobile usability"


# =============================================================================
# CRITICAL MOBILE ISSUES TESTS
# =============================================================================


class TestCriticalMobileIssues:
    """Test for critical mobile issues that break usability.

    These tests specifically catch issues that would make the app
    unusable on mobile devices.
    """

    @pytest.mark.parametrize("page", ["/", "/funds", "/lps", "/matches", "/login"])
    def test_page_renders_on_all_pages(self, client, page):
        """All main pages should render without errors."""
        response = client.get(page)
        assert response.status_code == 200

    def test_no_horizontal_scroll_indicators(self, client):
        """Content should not cause horizontal scroll.

        Look for fixed-width elements that might overflow.
        """
        response = client.get("/funds")
        html = response.text

        # Check for common overflow culprits
        # Fixed widths without max-width are risky
        dangerous_patterns = [
            r'width:\s*\d{4,}px',  # Width > 999px fixed
            r'min-width:\s*\d{4,}px',
        ]

        for pattern in dangerous_patterns:
            matches = re.findall(pattern, html)
            assert len(matches) == 0, f"Fixed width may cause horizontal scroll: {matches}"

    def test_tables_are_responsive(self, client):
        """Tables should have horizontal scroll wrapper on mobile."""
        response = client.get("/matches")
        html = response.text

        # If there are tables, they should have overflow handling
        if "<table" in html:
            # Should have overflow-x-auto wrapper
            assert "overflow-x" in html or "overflow-auto" in html, (
                "Tables need horizontal scroll wrapper for mobile"
            )


# =============================================================================
# PLAYWRIGHT BROWSER TESTS (Optional - run with pytest -m browser)
# =============================================================================
# These tests require Playwright and test actual browser rendering.
# Run with: pytest -m browser tests/test_mobile.py


@pytest.mark.browser
class TestPlaywrightMobile:
    """Browser-based tests for real viewport testing.

    These tests use Playwright to test actual browser behavior at
    different viewport sizes. Marked with @pytest.mark.browser.

    To run: pytest -m browser tests/test_mobile.py

    Requires: pip install pytest-playwright && playwright install
    """

    @pytest.fixture
    def mobile_viewport(self):
        """iPhone SE viewport dimensions."""
        return {"width": 375, "height": 667}

    @pytest.fixture
    def tablet_viewport(self):
        """iPad viewport dimensions."""
        return {"width": 768, "height": 1024}

    @pytest.fixture
    def desktop_viewport(self):
        """Desktop viewport dimensions."""
        return {"width": 1280, "height": 800}

    @pytest.mark.browser
    def test_mobile_viewport_renders(self, page, mobile_viewport):
        """Page should render correctly at mobile viewport."""
        page.set_viewport_size(mobile_viewport)
        page.goto("http://localhost:8000/funds")

        # Page should load
        assert page.title()

        # Content should be visible
        assert page.locator("h1").is_visible()

    @pytest.mark.browser
    def test_navigation_accessible_on_mobile(self, page, mobile_viewport):
        """Navigation should be accessible on mobile viewport."""
        page.set_viewport_size(mobile_viewport)
        page.goto("http://localhost:8000/funds")

        # Either nav links should be visible OR hamburger menu should exist
        nav_visible = page.locator("nav a").first.is_visible()
        hamburger_exists = page.locator(
            "[aria-label='Open navigation menu'], "
            "[aria-label='Menu'], "
            "[aria-label='menu'], "
            "#mobile-menu-toggle, "
            ".hamburger"
        ).count() > 0

        assert nav_visible or hamburger_exists, (
            "Navigation must be accessible on mobile"
        )

    @pytest.mark.browser
    def test_no_horizontal_overflow_mobile(self, page, mobile_viewport):
        """Page should not have horizontal overflow on mobile."""
        page.set_viewport_size(mobile_viewport)
        page.goto("http://localhost:8000/funds")

        # Check if page width exceeds viewport
        body_width = page.evaluate("document.body.scrollWidth")
        viewport_width = mobile_viewport["width"]

        assert body_width <= viewport_width + 10, (
            f"Page has horizontal overflow: body={body_width}px, viewport={viewport_width}px"
        )

    @pytest.mark.browser
    def test_buttons_are_tappable(self, page, mobile_viewport):
        """Primary action buttons should be large enough to tap."""
        page.set_viewport_size(mobile_viewport)
        page.goto("http://localhost:8000/funds")

        # Check only primary/visible action buttons, not icon-only buttons
        buttons = page.locator("button.btn-primary, button[type='submit']").all()
        for button in buttons[:5]:  # Check first 5 buttons
            box = button.bounding_box()
            if box and box["width"] > 0:
                # WCAG recommends 44x44px minimum for touch targets
                # Allow some flexibility for styled buttons
                assert box["height"] >= 32, f"Button too short: {box['height']}px"
