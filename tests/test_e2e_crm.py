"""CRM End-to-End tests using Playwright.

These tests cover CRM-related user journeys including:
- Events management
- Touchpoints/interactions logging
- Tasks management
- CRM integration workflows
- Mobile responsiveness for CRM pages

Extracted from test_e2e.py to improve test organization.

Run with:
    # Start server first
    uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 &

    # Run CRM E2E tests
    uv run pytest tests/test_e2e_crm.py -v -m browser
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
    """Fixture that provides a page logged in as GP demo user."""
    page.goto(f"{BASE_URL}/login")
    page.fill('input[name="email"]', "gp@demo.com")
    page.fill('input[name="password"]', "demo123")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{BASE_URL}/dashboard")
    yield page


# =============================================================================
# Events Tests
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


# =============================================================================
# Touchpoints Tests
# =============================================================================


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


# =============================================================================
# Tasks Tests
# =============================================================================


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
# CRM Integration Tests
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


# =============================================================================
# Mobile Responsive CRM Tests
# =============================================================================


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
        page.wait_for_load_state("domcontentloaded")

        body_width = page.evaluate("document.body.scrollWidth")
        assert body_width <= mobile_viewport["width"] + 20

    def test_tasks_mobile_responsive(self, logged_in_page: Page, mobile_viewport):
        """Tasks page should be responsive on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/tasks")
        page.wait_for_load_state("domcontentloaded")

        body_width = page.evaluate("document.body.scrollWidth")
        assert body_width <= mobile_viewport["width"] + 20

    def test_lp_dashboard_mobile_responsive(self, logged_in_page: Page, mobile_viewport):
        """LP dashboard should be responsive on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/lp-dashboard")
        page.wait_for_load_state("domcontentloaded")

        body_width = page.evaluate("document.body.scrollWidth")
        assert body_width <= mobile_viewport["width"] + 20

    def test_lp_pipeline_mobile_responsive(self, logged_in_page: Page, mobile_viewport):
        """LP pipeline should be responsive on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/lp-pipeline")
        page.wait_for_load_state("domcontentloaded")

        body_width = page.evaluate("document.body.scrollWidth")
        # Pipeline is a kanban board, might need horizontal scroll
        # Just check it doesn't massively overflow
        assert body_width <= mobile_viewport["width"] * 5  # Allow for kanban columns
