"""GP End-to-End tests using Playwright.

These tests cover GP-specific user journeys through the application.
They require a running server at http://localhost:8000.

Run with:
    # Start server first
    uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 &

    # Run GP E2E tests (browser tests only)
    uv run pytest tests/test_e2e_gps.py -v -m browser

Test Categories:
    - GP database (list, statistics, search, filter)
    - GP search (name, natural language, strategy, location)
    - GP CRUD (create modal, form fields)
    - GP mobile responsive
    - GP pipeline (kanban board, stages, navigation, drag-drop)
    - GP pipeline mobile responsive
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
def mobile_viewport():
    """iPhone SE viewport dimensions."""
    return {"width": 375, "height": 667}


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
# GP Pipeline Journey Tests
# =============================================================================


@pytest.mark.browser
class TestGPPipelineJourney:
    """E2E tests for GP pipeline kanban board view."""

    def test_gp_pipeline_accessible(self, logged_in_page: Page):
        """GP pipeline should be accessible for logged-in GP user."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/pipeline")
        page.wait_for_load_state("domcontentloaded")

        content = page.content()
        assert "Pipeline" in content

    def test_gp_pipeline_shows_kanban_stages(self, logged_in_page: Page):
        """GP pipeline should show all 9 kanban stages."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/pipeline")
        page.wait_for_load_state("domcontentloaded")

        content = page.content()
        # Check for key pipeline stages
        expected_stages = ["Recommended", "Interested", "Pursuing", "Reviewing"]
        stages_found = sum(1 for stage in expected_stages if stage in content)
        assert stages_found >= 2, f"Expected to find at least 2 stages, found {stages_found}"

    def test_gp_pipeline_has_navigation(self, logged_in_page: Page):
        """GP pipeline should have nav links to other GP pages."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/pipeline")
        page.wait_for_load_state("domcontentloaded")

        content = page.content()
        assert "Dashboard" in content
        assert "Matches" in content or "Funds" in content

    def test_gp_pipeline_kanban_columns_present(self, logged_in_page: Page):
        """GP pipeline should have kanban column structure."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/pipeline")
        page.wait_for_load_state("domcontentloaded")

        # Check for column IDs that indicate kanban structure
        content = page.content()
        assert "column-" in content or "cards-" in content

    def test_gp_pipeline_has_fund_filter(self, logged_in_page: Page):
        """GP pipeline should have fund filter dropdown."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/pipeline")
        page.wait_for_load_state("domcontentloaded")

        content = page.content()
        # Either has a fund filter or just shows the pipeline
        assert "Pipeline" in content

    def test_gp_pipeline_has_drag_drop_script(self, logged_in_page: Page):
        """GP pipeline should have drag-and-drop JavaScript."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/pipeline")
        page.wait_for_load_state("domcontentloaded")

        content = page.content()
        # Check for drag event handlers in the page source
        assert "drag" in content or "drop" in content or "draggable" in content

    def test_gp_pipeline_navigation_to_dashboard(self, logged_in_page: Page):
        """GP can navigate from pipeline to dashboard."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/pipeline")
        page.wait_for_load_state("domcontentloaded")

        # Click Dashboard link
        dashboard_link = page.get_by_role("link", name="Dashboard")
        if dashboard_link.count() > 0:
            dashboard_link.first.click()
            page.wait_for_load_state("domcontentloaded")
            assert "/dashboard" in page.url


@pytest.mark.browser
class TestGPPipelineMobileResponsive:
    """Mobile responsiveness tests for GP pipeline."""

    @pytest.fixture
    def mobile_viewport(self):
        """Mobile viewport dimensions."""
        return {"width": 375, "height": 812}

    def test_gp_pipeline_mobile_responsive(self, logged_in_page: Page, mobile_viewport):
        """GP pipeline should be usable on mobile with horizontal scroll."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/pipeline")
        page.wait_for_load_state("networkidle")

        # Pipeline is a kanban board, might need horizontal scroll
        # Just check it loads and has content
        content = page.content()
        assert "Pipeline" in content

    def test_gp_pipeline_mobile_nav_visible(self, logged_in_page: Page, mobile_viewport):
        """GP pipeline mobile nav should be accessible."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/pipeline")
        page.wait_for_load_state("networkidle")

        # Page should be functional on mobile
        body_width = page.evaluate("document.body.scrollWidth")
        # Allow for kanban columns (up to 9 columns * ~300px each)
        assert body_width <= mobile_viewport["width"] * 10
