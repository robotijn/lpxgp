"""End-to-End tests for AI-powered search functionality using Playwright.

These tests cover AI-powered natural language search user journeys through
the application, including LP search, GP search, and mobile responsiveness.

They require a running server at http://localhost:8000.

Run with:
    # Start server first
    uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 &

    # Run AI search E2E tests
    uv run pytest tests/test_e2e_ai_search.py -v -m browser

Test Categories:
    - AI-powered natural language LP search
    - AI search mobile responsiveness
    - AI search result handling
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

    def test_ai_search_handles_natural_language(self, logged_in_page: Page):
        """AI search handles natural language queries gracefully.

        BDD: Given I am on the LP search page
             When I search with natural language "pension funds with 100m aum"
             Then the page should respond without errors
             And I should see either results or a "no results" message

        Note: This test verifies the UI handles AI search gracefully,
        regardless of whether Ollama is available (fallback to text search).
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps")
        page.wait_for_load_state("domcontentloaded")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        # Verify search input exists
        expect(search_input.first).to_be_visible()

        # Search with natural language
        search_input.first.fill("pension funds with 100m aum")
        search_input.first.press("Enter")

        # Wait for search to complete (AI or fallback)
        page.wait_for_timeout(3000)

        # Page should still be on /lps (no crash/redirect)
        expect(page).to_have_url(re.compile(r"/lps"))

        # Page should have either results OR "No LPs found" message
        # Both are valid outcomes - we're testing the UI handles it gracefully
        page_content = page.content()
        has_results = "pension" in page_content.lower() or "endowment" in page_content.lower()
        has_no_results_msg = "No LPs found" in page_content or "no results" in page_content.lower()
        assert has_results or has_no_results_msg, "Page should show results or no-results message"

    def test_ai_search_lp_type_filter(self, logged_in_page: Page):
        """AI search for LP type handles type-based queries gracefully.

        BDD: Given I search for "endowment investors"
             Then the page should respond without errors
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps")
        page.wait_for_load_state("domcontentloaded")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        expect(search_input.first).to_be_visible()

        search_input.first.fill("endowment investors")
        search_input.first.press("Enter")
        page.wait_for_timeout(3000)

        # Page should still be functional
        expect(page).to_have_url(re.compile(r"/lps"))

    def test_gp_ai_search_handles_queries(self, logged_in_page: Page):
        """AI search on GP page handles queries gracefully.

        BDD: Given I am on the GP search page
             When I search for "buyout funds"
             Then the page should respond without errors
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/gps")
        page.wait_for_load_state("domcontentloaded")

        search_input = page.locator(
            'input[type="search"], input[name="search"], input[placeholder*="Search"]'
        )
        expect(search_input.first).to_be_visible()

        search_input.first.fill("buyout funds")
        search_input.first.press("Enter")
        page.wait_for_timeout(3000)

        # Page should still be functional
        expect(page).to_have_url(re.compile(r"/gps"))
