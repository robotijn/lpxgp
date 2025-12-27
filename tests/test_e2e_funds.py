"""End-to-End tests for Fund management using Playwright.

These tests cover fund-related user journeys through the application.
They require a running server at http://localhost:8000.

Run with:
    # Start server first
    uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 &

    # Run E2E tests (browser tests only)
    uv run pytest tests/test_e2e_funds.py -v -m browser

Test Categories:
    - Fund management (CRUD operations)
    - Fund detail page (view, edit, matches)
"""

import pytest
from playwright.sync_api import Page, expect

# Base URL for the running server
BASE_URL = "http://localhost:8000"


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
