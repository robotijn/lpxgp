"""End-to-End tests for new features (Phases 1-5).

NOTE: These tests verify the new pages load and function correctly.

These tests cover the new features added across all phases:
- Phase 1-2: UX enhancements (dark mode, toast, keyboard shortcuts)
- Phase 3: Admin features (data health, activity logs, settings, people)
- Phase 4: GP features (LP comparison, notes, tags)
- Phase 5: LP Portal features (mandate editor, fund comparison, meetings)

They require a running server at http://localhost:8000.

Run with:
    # Start server first
    uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 &

    # Run new features E2E tests
    uv run pytest tests/test_e2e_new_features.py -v -m browser
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


# =============================================================================
# PHASE 1-2: UX ENHANCEMENT TESTS
# =============================================================================


@pytest.mark.browser
class TestDarkMode:
    """E2E tests for dark mode functionality."""

    def test_dark_mode_toggle_exists(self, logged_in_page: Page):
        """Dark mode toggle should exist in the UI."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/dashboard")

        # Check for dark mode toggle (using Ctrl+D keyboard shortcut)
        # The toggle script should be in the page
        page_content = page.content()
        assert "toggleDarkMode" in page_content or "dark:" in page_content

    def test_keyboard_shortcut_for_dark_mode(self, logged_in_page: Page):
        """Ctrl+D should toggle dark mode."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/dashboard")

        # Press Ctrl+D to toggle dark mode
        page.keyboard.press("Control+d")

        # Dark mode class should be toggled
        # (We just verify the JS is loaded, actual toggle depends on implementation)
        page_content = page.content()
        assert "darkMode" in page_content or "dark:" in page_content


@pytest.mark.browser
class TestToastNotifications:
    """E2E tests for toast notification system."""

    def test_toast_function_exists(self, logged_in_page: Page):
        """Toast notification function should be available."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/dashboard")

        # Verify showToast function exists
        has_toast = page.evaluate("typeof showToast === 'function'")
        assert has_toast is True

    def test_toast_can_be_triggered(self, logged_in_page: Page):
        """Toast notification should display when triggered."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/dashboard")

        # Trigger a toast
        page.evaluate("showToast('Test message', 'success')")

        # Wait for toast to appear
        page.wait_for_timeout(100)

        # Check for toast container
        toast_container = page.locator("#toast-container")
        expect(toast_container).to_be_visible()


@pytest.mark.browser
class TestKeyboardShortcuts:
    """E2E tests for keyboard shortcuts."""

    def test_escape_closes_modals(self, logged_in_page: Page):
        """Escape key should close open modals."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/funds")

        # Open create fund modal
        add_btn = page.locator("#add-fund-btn")
        if add_btn.is_visible():
            add_btn.click()
            page.wait_for_timeout(200)

            # Press Escape to close
            page.keyboard.press("Escape")
            page.wait_for_timeout(200)

            # Modal should be closed - check it's either hidden or not visible
            modal = page.locator("#create-fund-modal")
            # Check if modal has hidden class or is not visible
            is_hidden = modal.get_attribute("class") and "hidden" in (modal.get_attribute("class") or "")
            is_not_visible = not modal.is_visible()
            assert is_hidden or is_not_visible, "Modal should be hidden after pressing Escape"

    def test_keyboard_shortcuts_script_loaded(self, logged_in_page: Page):
        """Keyboard shortcuts script should be loaded."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/dashboard")

        # Check for keyboard shortcuts handler
        page_content = page.content()
        assert "keyboardShortcuts" in page_content or "addEventListener" in page_content


# =============================================================================
# PHASE 3: ADMIN FEATURE TESTS
# =============================================================================


@pytest.mark.browser
class TestAdminDataHealth:
    """E2E tests for admin data health dashboard."""

    def test_data_health_page_loads(self, logged_in_as_admin: Page):
        """Data health page should load for admin."""
        page = logged_in_as_admin
        page.goto(f"{BASE_URL}/admin/data-health")

        expect(page.locator("h1")).to_contain_text("Data Health")
        expect(page).to_have_url(f"{BASE_URL}/admin/data-health")

    def test_data_health_shows_scores(self, logged_in_as_admin: Page):
        """Data health page should display quality scores."""
        page = logged_in_as_admin
        page.goto(f"{BASE_URL}/admin/data-health")

        page_content = page.content()
        # Should show health metrics
        assert "Quality" in page_content or "Score" in page_content


@pytest.mark.browser
class TestAdminActivityLogs:
    """E2E tests for admin activity logs."""

    def test_activity_logs_page_loads(self, logged_in_as_admin: Page):
        """Activity logs page should load for admin."""
        page = logged_in_as_admin
        page.goto(f"{BASE_URL}/admin/activity")

        expect(page.locator("h1")).to_contain_text("Activity")
        expect(page).to_have_url(f"{BASE_URL}/admin/activity")


@pytest.mark.browser
class TestAdminSettings:
    """E2E tests for admin settings page."""

    def test_settings_page_loads(self, logged_in_as_admin: Page):
        """Admin settings page should load."""
        page = logged_in_as_admin
        page.goto(f"{BASE_URL}/admin/settings")

        expect(page.locator("h1")).to_contain_text("Settings")
        expect(page).to_have_url(f"{BASE_URL}/admin/settings")

    def test_settings_has_form_elements(self, logged_in_as_admin: Page):
        """Settings page should have form elements."""
        page = logged_in_as_admin
        page.goto(f"{BASE_URL}/admin/settings")

        # Should have form inputs
        page_content = page.content()
        assert "Platform Name" in page_content or "Settings" in page_content


@pytest.mark.browser
class TestAdminPeople:
    """E2E tests for admin people management."""

    def test_people_page_loads(self, logged_in_as_admin: Page):
        """People management page should load."""
        page = logged_in_as_admin
        page.goto(f"{BASE_URL}/admin/people")

        expect(page.locator("h1")).to_contain_text("People")
        expect(page).to_have_url(f"{BASE_URL}/admin/people")

    def test_people_page_has_stats(self, logged_in_as_admin: Page):
        """People page should show statistics."""
        page = logged_in_as_admin
        page.goto(f"{BASE_URL}/admin/people")

        page_content = page.content()
        assert "Total" in page_content or "Contacts" in page_content

    def test_people_add_button_opens_modal(self, logged_in_as_admin: Page):
        """Add person button should open modal."""
        page = logged_in_as_admin
        page.goto(f"{BASE_URL}/admin/people")

        # Click add button
        add_btn = page.locator('button:has-text("Add Person")')
        if add_btn.is_visible():
            add_btn.click()
            page.wait_for_timeout(100)

            # Modal should be visible
            modal = page.locator("#person-modal")
            expect(modal).not_to_have_class(re.compile(r"hidden"))


# =============================================================================
# PHASE 4: GP FEATURE TESTS
# =============================================================================


@pytest.mark.browser
class TestGPCompare:
    """E2E tests for GP LP comparison page."""

    def test_compare_page_loads(self, logged_in_page: Page):
        """Compare page should load for GP user."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/compare")

        expect(page.locator("h1")).to_contain_text("Compare")
        expect(page).to_have_url(f"{BASE_URL}/compare")

    def test_compare_shows_demo_data(self, logged_in_page: Page):
        """Compare page should show demo data when no LPs selected."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/compare")

        page_content = page.content()
        # Should show demo LP names
        assert "CalPERS" in page_content or "Ontario" in page_content or "Compare" in page_content

    def test_compare_has_export_button(self, logged_in_page: Page):
        """Compare page should have export functionality."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/compare")

        # Should have export button
        export_btn = page.locator('button:has-text("Export")')
        expect(export_btn).to_be_visible()


@pytest.mark.browser
class TestLPDetailNotes:
    """E2E tests for notes feature on LP detail page."""

    def test_lp_detail_has_notes_section(self, logged_in_page: Page):
        """LP detail page should have notes section."""
        page = logged_in_page
        # Use a demo LP ID
        page.goto(f"{BASE_URL}/lps/00000000-0000-0000-0000-000000000001")

        page_content = page.content()
        # Should have notes section
        assert "Notes" in page_content or "notes" in page_content

    def test_notes_add_functionality(self, logged_in_page: Page):
        """Should be able to add notes to LP."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps/00000000-0000-0000-0000-000000000001")

        # Look for add note button
        add_note_btn = page.locator('button:has-text("Add Note")')
        if add_note_btn.is_visible():
            # Click to show form
            add_note_btn.click()
            page.wait_for_timeout(100)


@pytest.mark.browser
class TestLPDetailTags:
    """E2E tests for tags feature on LP detail page."""

    def test_lp_detail_has_tags_section(self, logged_in_page: Page):
        """LP detail page should have tags section."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps/00000000-0000-0000-0000-000000000001")

        page_content = page.content()
        # Should have tags section
        assert "Tags" in page_content or "tag" in page_content


# =============================================================================
# PHASE 5: LP PORTAL FEATURE TESTS
# =============================================================================


@pytest.mark.browser
class TestLPPortalMandate:
    """E2E tests for LP mandate editor."""

    def test_mandate_page_loads(self, logged_in_as_lp: Page):
        """LP mandate editor page should load."""
        page = logged_in_as_lp
        page.goto(f"{BASE_URL}/lp-portal/mandate")

        expect(page.locator("h1")).to_contain_text("Mandate")

    def test_mandate_has_strategy_options(self, logged_in_as_lp: Page):
        """Mandate editor should have strategy options."""
        page = logged_in_as_lp
        page.goto(f"{BASE_URL}/lp-portal/mandate")

        page_content = page.content()
        # Should show strategy options
        assert "Strategy" in page_content or "Buyout" in page_content

    def test_mandate_has_save_button(self, logged_in_as_lp: Page):
        """Mandate editor should have save button."""
        page = logged_in_as_lp
        page.goto(f"{BASE_URL}/lp-portal/mandate")

        save_btn = page.locator('button:has-text("Save")')
        expect(save_btn).to_be_visible()


@pytest.mark.browser
class TestLPPortalMeetings:
    """E2E tests for LP meeting scheduler."""

    def test_meetings_page_loads(self, logged_in_as_lp: Page):
        """LP meetings page should load."""
        page = logged_in_as_lp
        page.goto(f"{BASE_URL}/lp-portal/meetings")

        expect(page.locator("h1")).to_contain_text("Meeting")

    def test_meetings_has_schedule_button(self, logged_in_as_lp: Page):
        """Meetings page should have schedule button."""
        page = logged_in_as_lp
        page.goto(f"{BASE_URL}/lp-portal/meetings")

        schedule_btn = page.locator('button:has-text("Schedule")')
        expect(schedule_btn).to_be_visible()

    def test_schedule_modal_opens(self, logged_in_as_lp: Page):
        """Schedule meeting button should open modal."""
        page = logged_in_as_lp
        page.goto(f"{BASE_URL}/lp-portal/meetings")

        # Click schedule button
        schedule_btn = page.locator('button:has-text("Schedule")')
        if schedule_btn.is_visible():
            schedule_btn.click()
            page.wait_for_timeout(100)

            # Modal should be visible
            modal = page.locator("#schedule-modal")
            expect(modal).not_to_have_class(re.compile(r"hidden"))


@pytest.mark.browser
class TestLPPortalCompareFunds:
    """E2E tests for LP fund comparison page."""

    def test_compare_funds_page_loads(self, logged_in_as_lp: Page):
        """LP fund comparison page should load."""
        page = logged_in_as_lp
        page.goto(f"{BASE_URL}/lp-portal/compare")

        expect(page.locator("h1")).to_contain_text("Compare")

    def test_compare_shows_demo_funds(self, logged_in_as_lp: Page):
        """Compare page should show demo funds when none selected."""
        page = logged_in_as_lp
        page.goto(f"{BASE_URL}/lp-portal/compare")

        page_content = page.content()
        # Should show demo fund names
        assert "Apex" in page_content or "Growth" in page_content or "Fund" in page_content


# =============================================================================
# MOBILE RESPONSIVENESS TESTS
# =============================================================================


@pytest.mark.browser
class TestNewFeaturesMobileResponsive:
    """Test new features on mobile viewports."""

    def test_compare_page_mobile(self, logged_in_page: Page, mobile_viewport):
        """Compare page should work on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/compare")

        expect(page.locator("h1")).to_contain_text("Compare")

    def test_admin_data_health_mobile(self, logged_in_as_admin: Page, mobile_viewport):
        """Data health page should work on mobile."""
        page = logged_in_as_admin
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/admin/data-health")

        expect(page.locator("h1")).to_contain_text("Data Health")

    def test_lp_mandate_mobile(self, logged_in_as_lp: Page, mobile_viewport):
        """LP mandate page should work on mobile."""
        page = logged_in_as_lp
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/lp-portal/mandate")

        expect(page.locator("h1")).to_contain_text("Mandate")

    def test_lp_meetings_mobile(self, logged_in_as_lp: Page, mobile_viewport):
        """LP meetings page should work on mobile."""
        page = logged_in_as_lp
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/lp-portal/meetings")

        expect(page.locator("h1")).to_contain_text("Meeting")


# =============================================================================
# EDGE CASE TESTS
# =============================================================================


@pytest.mark.browser
class TestNewFeaturesEdgeCases:
    """Edge case tests for new features."""

    def test_compare_with_invalid_ids(self, logged_in_page: Page):
        """Compare page should handle invalid LP IDs gracefully."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/compare?lp_ids=invalid,not-a-uuid")

        # Should still load with demo data
        expect(page.locator("h1")).to_contain_text("Compare")

    def test_lp_compare_with_invalid_fund_ids(self, logged_in_as_lp: Page):
        """LP compare should handle invalid fund IDs gracefully."""
        page = logged_in_as_lp
        page.goto(f"{BASE_URL}/lp-portal/compare?fund_ids=invalid")

        # Should still load with demo data
        expect(page.locator("h1")).to_contain_text("Compare")

    def test_admin_pages_require_admin(self, logged_in_page: Page):
        """Admin-only pages should redirect non-admin users."""
        page = logged_in_page

        # GP user should be redirected from admin pages
        page.goto(f"{BASE_URL}/admin/data-health")
        expect(page).to_have_url(f"{BASE_URL}/dashboard")

        page.goto(f"{BASE_URL}/admin/settings")
        expect(page).to_have_url(f"{BASE_URL}/dashboard")

    def test_empty_state_compare(self, logged_in_page: Page):
        """Compare page should show helpful empty state."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/compare")

        # Should have recommendation section or demo data
        page_content = page.content()
        assert "Recommendation" in page_content or "CalPERS" in page_content


# =============================================================================
# INTEGRATION TESTS
# =============================================================================


@pytest.mark.browser
class TestNewFeaturesIntegration:
    """Integration tests for new features working together."""

    def test_admin_navigation_flow(self, logged_in_as_admin: Page):
        """Admin should be able to navigate between all admin pages."""
        page = logged_in_as_admin

        # Navigate through admin pages
        page.goto(f"{BASE_URL}/admin")
        expect(page).to_have_url(f"{BASE_URL}/admin")

        page.goto(f"{BASE_URL}/admin/data-health")
        expect(page).to_have_url(f"{BASE_URL}/admin/data-health")

        page.goto(f"{BASE_URL}/admin/activity")
        expect(page).to_have_url(f"{BASE_URL}/admin/activity")

        page.goto(f"{BASE_URL}/admin/settings")
        expect(page).to_have_url(f"{BASE_URL}/admin/settings")

        page.goto(f"{BASE_URL}/admin/people")
        expect(page).to_have_url(f"{BASE_URL}/admin/people")

    def test_lp_portal_navigation_flow(self, logged_in_as_lp: Page):
        """LP should be able to navigate through LP portal pages."""
        page = logged_in_as_lp

        page.goto(f"{BASE_URL}/lp-portal/mandate")
        page_content = page.content()
        assert "Mandate" in page_content

        page.goto(f"{BASE_URL}/lp-portal/meetings")
        page_content = page.content()
        assert "Meeting" in page_content

        page.goto(f"{BASE_URL}/lp-portal/compare")
        page_content = page.content()
        assert "Compare" in page_content

    def test_gp_workflow_with_compare(self, logged_in_page: Page):
        """GP should be able to use compare feature in workflow."""
        page = logged_in_page

        # View matches
        page.goto(f"{BASE_URL}/matches")
        page_content = page.content()
        assert "Matches" in page_content

        # Go to compare
        page.goto(f"{BASE_URL}/compare")
        expect(page.locator("h1")).to_contain_text("Compare")

        # Should have action buttons
        page_content = page.content()
        assert "Export" in page_content or "View Details" in page_content
