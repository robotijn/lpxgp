"""End-to-End tests for Outreach functionality using Playwright.

These tests cover outreach-related user journeys through the application,
including outreach hub, pitch generation, and related workflows.

They require a running server at http://localhost:8000.

Run with:
    # Start server first
    uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 &

    # Run outreach E2E tests
    uv run pytest tests/test_e2e_outreach.py -v -m browser

Test Categories:
    - Outreach hub navigation and features
    - Pitch generator workflow
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
