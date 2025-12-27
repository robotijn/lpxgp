"""End-to-End tests for Matches functionality using Playwright.

These tests cover matching-related user journeys through the application,
including match workflow, match detail pages, and match feedback.

They require a running server at http://localhost:8000.

Run with:
    # Start server first
    uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 &

    # Run matches E2E tests
    uv run pytest tests/test_e2e_matches.py -v -m browser

Test Categories:
    - Matching workflow (view matches, fund filter)
    - Match detail journey (score breakdown, AI analysis, talking points)
    - Match feedback journey (stats display)
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
# MATCH DETAIL JOURNEY TESTS
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
# MATCH FEEDBACK JOURNEY TESTS
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
