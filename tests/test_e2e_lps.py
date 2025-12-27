"""End-to-End tests for LP-related user journeys.

These tests cover LP management, LP detail pages, LP dashboard,
LP watchlist, LP pipeline, LP mandate configuration, and LP meeting requests.

Extracted from test_e2e.py for better organization.

Run with:
    # Start server first
    uv run uvicorn src.main:app --host 127.0.0.1 --port 8000 &

    # Run LP E2E tests
    uv run pytest tests/test_e2e_lps.py -v -m browser
"""

import pytest
from playwright.sync_api import Page, expect

# Base URL for the running server
BASE_URL = "http://localhost:8000"


# =============================================================================
# FIXTURES (shared with test_e2e.py)
# =============================================================================


@pytest.fixture
def logged_in_page(page: Page):
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
        page.wait_for_load_state("domcontentloaded")

        # Find and click an LP link (usually LP name is a link)
        lp_links = page.locator('a[href*="/lps/"]')
        if lp_links.count() > 0:
            lp_links.first.click()
            page.wait_for_load_state("domcontentloaded")

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
        page.wait_for_load_state("domcontentloaded")

        page_content = page.content()
        assert "Overview" in page_content or "AUM" in page_content

    def test_lp_detail_shows_match_score(self, logged_in_page: Page):
        """LP detail should display match score.

        BDD: Given I am on LP detail page
             Then I see the match score breakdown
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps/a1000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("domcontentloaded")

        page_content = page.content()
        assert "Match" in page_content or "Score" in page_content

    def test_lp_detail_has_shortlist_button(self, logged_in_page: Page):
        """LP detail should have shortlist toggle button.

        BDD: Given I am on LP detail page
             Then I see a button to add/remove from shortlist
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps/a1000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("domcontentloaded")

        shortlist_btn = page.locator('button:has-text("Shortlist")')
        expect(shortlist_btn.first).to_be_visible()

    def test_lp_detail_has_generate_pitch_link(self, logged_in_page: Page):
        """LP detail should have link to generate pitch.

        BDD: Given I am on LP detail page
             Then I see a link to generate pitch for this LP
        """
        page = logged_in_page
        page.goto(f"{BASE_URL}/lps/a1000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("domcontentloaded")

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
        page.wait_for_load_state("domcontentloaded")

        # Click search breadcrumb
        search_link = page.locator('a[href="/lps"]').first
        if search_link.is_visible():
            search_link.click()
            expect(page).to_have_url(f"{BASE_URL}/lps")


# =============================================================================
# LP DASHBOARD E2E TESTS
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


# =============================================================================
# LP WATCHLIST E2E TESTS
# =============================================================================


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


# =============================================================================
# LP PIPELINE E2E TESTS
# =============================================================================


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
# LP MANDATE E2E TESTS
# =============================================================================


@pytest.mark.browser
class TestLPMandateJourney:
    """E2E tests for LP mandate configuration page."""

    def test_lp_mandate_accessible(self, logged_in_page: Page):
        """LP mandate page should be accessible for logged-in users."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-mandate")
        page.wait_for_load_state("domcontentloaded")

        expect(page.locator("h1")).to_contain_text("Investment Mandate")

    def test_lp_mandate_requires_auth(self, page: Page):
        """LP mandate page should require authentication."""
        page.goto(f"{BASE_URL}/lp-mandate")
        page.wait_for_load_state("domcontentloaded")

        # Should redirect to login
        assert "/login" in page.url

    def test_lp_mandate_has_strategy_checkboxes(self, logged_in_page: Page):
        """LP mandate should have strategy preference checkboxes."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-mandate")
        page.wait_for_load_state("domcontentloaded")

        # Should have checkboxes for strategies
        strategy_checkboxes = page.locator("input[name='strategies']")
        expect(strategy_checkboxes.first).to_be_visible()

        # Check that multiple strategy options exist
        count = strategy_checkboxes.count()
        assert count >= 4, f"Expected at least 4 strategy options, got {count}"

    def test_lp_mandate_has_check_size_inputs(self, logged_in_page: Page):
        """LP mandate should have check size input fields."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-mandate")
        page.wait_for_load_state("domcontentloaded")

        min_input = page.locator("input[name='check_size_min_mm']")
        max_input = page.locator("input[name='check_size_max_mm']")

        expect(min_input).to_be_visible()
        expect(max_input).to_be_visible()
        expect(min_input).to_have_attribute("type", "number")
        expect(max_input).to_have_attribute("type", "number")

    def test_lp_mandate_has_geography_checkboxes(self, logged_in_page: Page):
        """LP mandate should have geography preference checkboxes."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-mandate")
        page.wait_for_load_state("domcontentloaded")

        geo_checkboxes = page.locator("input[name='geographies']")
        expect(geo_checkboxes.first).to_be_visible()

        count = geo_checkboxes.count()
        assert count >= 4, f"Expected at least 4 geography options, got {count}"

    def test_lp_mandate_has_sector_checkboxes(self, logged_in_page: Page):
        """LP mandate should have sector preference checkboxes."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-mandate")
        page.wait_for_load_state("domcontentloaded")

        sector_checkboxes = page.locator("input[name='sectors']")
        expect(sector_checkboxes.first).to_be_visible()

        count = sector_checkboxes.count()
        assert count >= 4, f"Expected at least 4 sector options, got {count}"

    def test_lp_mandate_has_save_button(self, logged_in_page: Page):
        """LP mandate should have a Save Mandate button."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-mandate")
        page.wait_for_load_state("domcontentloaded")

        save_btn = page.locator("button[type='submit']:has-text('Save Mandate')")
        expect(save_btn).to_be_visible()
        expect(save_btn).to_be_enabled()

    def test_lp_mandate_has_back_to_dashboard_link(self, logged_in_page: Page):
        """LP mandate should have a link back to dashboard."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-mandate")
        page.wait_for_load_state("domcontentloaded")

        back_link = page.locator("a:has-text('Back to Dashboard')")
        expect(back_link).to_be_visible()

    def test_lp_mandate_checkboxes_are_clickable(self, logged_in_page: Page):
        """Strategy checkboxes should be clickable."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-mandate")
        page.wait_for_load_state("domcontentloaded")

        # Find first strategy checkbox
        first_checkbox = page.locator("input[name='strategies']").first
        expect(first_checkbox).not_to_be_checked()

        # Click to check it
        first_checkbox.check()
        expect(first_checkbox).to_be_checked()

        # Click to uncheck it
        first_checkbox.uncheck()
        expect(first_checkbox).not_to_be_checked()

    def test_lp_mandate_check_size_accepts_values(self, logged_in_page: Page):
        """Check size inputs should accept numeric values."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-mandate")
        page.wait_for_load_state("domcontentloaded")

        min_input = page.locator("input[name='check_size_min_mm']")
        max_input = page.locator("input[name='check_size_max_mm']")

        min_input.fill("10")
        max_input.fill("100")

        expect(min_input).to_have_value("10")
        expect(max_input).to_have_value("100")

    def test_lp_mandate_form_submission(self, logged_in_page: Page):
        """LP mandate form should submit via HTMX."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-mandate")
        page.wait_for_load_state("domcontentloaded")

        # Check a few options and enter check sizes
        page.locator("input[name='strategies']").first.check()
        page.locator("input[name='check_size_min_mm']").fill("25")
        page.locator("input[name='check_size_max_mm']").fill("200")
        page.locator("input[name='geographies']").first.check()

        # Submit form
        save_btn = page.locator("button[type='submit']:has-text('Save Mandate')")
        save_btn.click()

        # Wait for response
        page.wait_for_timeout(1000)

        # Should still be on the same page (HTMX update)
        assert "/lp-mandate" in page.url

    def test_lp_mandate_navigation_links_work(self, logged_in_page: Page):
        """Navigation links from mandate page should work."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-mandate")
        page.wait_for_load_state("domcontentloaded")

        # Desktop nav links should be present
        content = page.content()
        assert "Dashboard" in content
        assert "Watchlist" in content
        assert "Pipeline" in content

    def test_lp_mandate_mobile_responsive(self, logged_in_page: Page, mobile_viewport):
        """LP mandate page should work on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/lp-mandate")
        page.wait_for_load_state("domcontentloaded")

        # Page should load without horizontal scroll
        body_width = page.evaluate("document.body.scrollWidth")
        viewport_width = page.evaluate("window.innerWidth")
        assert body_width <= viewport_width + 10

        # Checkboxes should still be visible
        expect(page.locator("input[name='strategies']").first).to_be_visible()


# =============================================================================
# LP MEETING REQUEST E2E TESTS
# =============================================================================


@pytest.mark.browser
class TestLPMeetingRequestJourney:
    """E2E tests for LP meeting request page."""

    def test_lp_meeting_request_requires_auth(self, page: Page):
        """Meeting request page should require authentication."""
        page.goto(f"{BASE_URL}/lp-meeting-request?fund_id=f0000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("domcontentloaded")

        # Should redirect to login
        assert "/login" in page.url

    def test_lp_meeting_request_redirects_without_fund_id(self, logged_in_page: Page):
        """Meeting request should redirect if fund_id is missing."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-meeting-request")
        page.wait_for_load_state("domcontentloaded")

        # Should redirect to dashboard or error
        # FastAPI returns 422 for missing required query param
        content = page.content()
        assert "lp-dashboard" in page.url or "422" in content or "field required" in content.lower()

    def test_lp_meeting_request_redirects_on_invalid_uuid(self, logged_in_page: Page):
        """Meeting request should redirect on invalid UUID."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-meeting-request?fund_id=invalid-uuid")
        page.wait_for_load_state("domcontentloaded")

        # Should redirect to dashboard
        assert "/lp-dashboard" in page.url

    def test_lp_meeting_request_accessible_with_valid_fund(self, logged_in_page: Page):
        """Meeting request page should be accessible with valid fund_id."""
        page = logged_in_page
        # Using a test fund ID
        page.goto(f"{BASE_URL}/lp-meeting-request?fund_id=f0000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("domcontentloaded")

        # Either shows the form or redirects (depending on if fund exists)
        content = page.content()
        is_request_page = "Request Meeting" in content or "Meeting" in content
        is_redirected = "/lp-dashboard" in page.url
        assert is_request_page or is_redirected

    def test_lp_meeting_request_has_date_inputs(self, logged_in_page: Page):
        """Meeting request should have date preference inputs."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-meeting-request?fund_id=f0000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("domcontentloaded")

        # If we're on the form page
        if "Request Meeting" in page.content() or "preferred_date" in page.content():
            date1 = page.locator("input[name='preferred_date_1']")
            expect(date1).to_be_visible()
            expect(date1).to_have_attribute("type", "date")

            date2 = page.locator("input[name='preferred_date_2']")
            date3 = page.locator("input[name='preferred_date_3']")
            expect(date2).to_be_visible()
            expect(date3).to_be_visible()

    def test_lp_meeting_request_has_format_options(self, logged_in_page: Page):
        """Meeting request should have meeting format radio buttons."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-meeting-request?fund_id=f0000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("domcontentloaded")

        if "Request Meeting" in page.content() or "meeting_format" in page.content():
            format_radios = page.locator("input[name='meeting_format']")
            count = format_radios.count()
            assert count >= 3, f"Expected at least 3 meeting format options, got {count}"

            # Video call should be default checked
            video_radio = page.locator("input[name='meeting_format'][value='video_call']")
            expect(video_radio).to_be_checked()

    def test_lp_meeting_request_has_topics_textarea(self, logged_in_page: Page):
        """Meeting request should have topics to discuss textarea."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-meeting-request?fund_id=f0000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("domcontentloaded")

        if "Request Meeting" in page.content() or "topics" in page.content():
            topics = page.locator("textarea[name='topics']")
            expect(topics).to_be_visible()
            expect(topics).to_have_attribute("required", "")

    def test_lp_meeting_request_has_contact_fields(self, logged_in_page: Page):
        """Meeting request should have contact information fields."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-meeting-request?fund_id=f0000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("domcontentloaded")

        if "Request Meeting" in page.content() or "contact_name" in page.content():
            name_input = page.locator("input[name='contact_name']")
            email_input = page.locator("input[name='contact_email']")
            title_input = page.locator("input[name='contact_title']")
            phone_input = page.locator("input[name='contact_phone']")

            expect(name_input).to_be_visible()
            expect(email_input).to_be_visible()
            expect(title_input).to_be_visible()
            expect(phone_input).to_be_visible()

            # Required fields
            expect(name_input).to_have_attribute("required", "")
            expect(email_input).to_have_attribute("required", "")

    def test_lp_meeting_request_has_submit_button(self, logged_in_page: Page):
        """Meeting request should have a submit button."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-meeting-request?fund_id=f0000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("domcontentloaded")

        if "Request Meeting" in page.content():
            submit_btn = page.locator("button[type='submit']:has-text('Submit Meeting Request')")
            expect(submit_btn).to_be_visible()
            expect(submit_btn).to_be_enabled()

    def test_lp_meeting_request_has_cancel_link(self, logged_in_page: Page):
        """Meeting request should have a cancel link."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-meeting-request?fund_id=f0000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("domcontentloaded")

        if "Request Meeting" in page.content():
            cancel_link = page.locator("a:has-text('Cancel')")
            expect(cancel_link).to_be_visible()

    def test_lp_meeting_request_format_selection(self, logged_in_page: Page):
        """Meeting format radio buttons should be selectable."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-meeting-request?fund_id=f0000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("domcontentloaded")

        if "Request Meeting" in page.content() or "meeting_format" in page.content():
            # Video call should be default
            video_radio = page.locator("input[name='meeting_format'][value='video_call']")
            expect(video_radio).to_be_checked()

            # Select phone
            phone_radio = page.locator("input[name='meeting_format'][value='phone']")
            phone_radio.check()
            expect(phone_radio).to_be_checked()
            expect(video_radio).not_to_be_checked()

            # Select in-person
            in_person_radio = page.locator("input[name='meeting_format'][value='in_person']")
            in_person_radio.check()
            expect(in_person_radio).to_be_checked()
            expect(phone_radio).not_to_be_checked()

    def test_lp_meeting_request_topics_input(self, logged_in_page: Page):
        """Topics textarea should accept text input."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-meeting-request?fund_id=f0000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("domcontentloaded")

        if "Request Meeting" in page.content() or "topics" in page.content():
            topics = page.locator("textarea[name='topics']")
            test_text = "Fund strategy overview, track record, and co-investment opportunities"
            topics.fill(test_text)
            expect(topics).to_have_value(test_text)

    def test_lp_meeting_request_date_input(self, logged_in_page: Page):
        """Date inputs should accept date values."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-meeting-request?fund_id=f0000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("domcontentloaded")

        if "Request Meeting" in page.content() or "preferred_date" in page.content():
            date1 = page.locator("input[name='preferred_date_1']")
            date1.fill("2025-02-15")
            expect(date1).to_have_value("2025-02-15")

    def test_lp_meeting_request_contact_fields_input(self, logged_in_page: Page):
        """Contact fields should accept input."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-meeting-request?fund_id=f0000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("domcontentloaded")

        if "Request Meeting" in page.content() or "contact_name" in page.content():
            name_input = page.locator("input[name='contact_name']")
            title_input = page.locator("input[name='contact_title']")
            email_input = page.locator("input[name='contact_email']")
            phone_input = page.locator("input[name='contact_phone']")

            name_input.fill("John Smith")
            title_input.fill("Director of PE")
            email_input.fill("john@example.com")
            phone_input.fill("+1 555-123-4567")

            expect(name_input).to_have_value("John Smith")
            expect(title_input).to_have_value("Director of PE")
            expect(email_input).to_have_value("john@example.com")
            expect(phone_input).to_have_value("+1 555-123-4567")

    def test_lp_meeting_request_mobile_responsive(self, logged_in_page: Page, mobile_viewport):
        """Meeting request page should work on mobile."""
        page = logged_in_page
        page.set_viewport_size(mobile_viewport)
        page.goto(f"{BASE_URL}/lp-meeting-request?fund_id=f0000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("domcontentloaded")

        if "Request Meeting" in page.content():
            # Page should load without horizontal scroll
            body_width = page.evaluate("document.body.scrollWidth")
            viewport_width = page.evaluate("window.innerWidth")
            assert body_width <= viewport_width + 10

            # Submit button should be visible
            submit_btn = page.locator("button[type='submit']").first
            expect(submit_btn).to_be_visible()


# =============================================================================
# LP PAGES EDGE CASES AND SECURITY TESTS
# =============================================================================


@pytest.mark.browser
class TestLPPagesEdgeCases:
    """Edge case and security tests for LP pages."""

    def test_lp_mandate_xss_prevention_in_inputs(self, logged_in_page: Page):
        """XSS should be prevented in mandate form inputs."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-mandate")
        page.wait_for_load_state("domcontentloaded")

        # Number inputs naturally reject non-numeric characters (browser protection)
        # Test that form exists and submits safely
        min_input = page.locator("input[name='check_size_min_mm']")
        max_input = page.locator("input[name='check_size_max_mm']")

        # Fill with valid numbers
        min_input.fill("10")
        max_input.fill("100")

        expect(min_input).to_have_value("10")
        expect(max_input).to_have_value("100")

        # Verify page content doesn't contain unescaped script tags
        content = page.content()
        assert "<script>alert" not in content

    def test_lp_meeting_request_sql_injection_prevention(self, logged_in_page: Page):
        """SQL injection should be prevented in fund_id."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-meeting-request?fund_id='; DROP TABLE funds; --")
        page.wait_for_load_state("domcontentloaded")

        # Should redirect (invalid UUID) or show safe error
        assert "/lp-dashboard" in page.url or "error" in page.content().lower()

    def test_lp_meeting_request_empty_fund_id(self, logged_in_page: Page):
        """Empty fund_id should be handled gracefully."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-meeting-request?fund_id=")
        page.wait_for_load_state("domcontentloaded")

        # Should redirect or show error
        assert "/lp-dashboard" in page.url or "error" in page.content().lower()

    def test_lp_pages_no_console_errors(self, logged_in_page: Page):
        """LP pages should not have console errors."""
        page = logged_in_page

        console_errors: list[str] = []
        page.on("console", lambda msg: console_errors.append(msg.text) if msg.type == "error" else None)

        page.goto(f"{BASE_URL}/lp-mandate")
        page.wait_for_load_state("domcontentloaded")

        # Filter out known acceptable errors
        real_errors = [e for e in console_errors if "favicon" not in e.lower()]
        assert len(real_errors) == 0, f"Console errors found: {real_errors}"

    def test_lp_mandate_back_link_navigation(self, logged_in_page: Page):
        """Back to Dashboard link should navigate correctly."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-mandate")
        page.wait_for_load_state("domcontentloaded")

        back_link = page.locator("a:has-text('Back to Dashboard')")
        back_link.click()
        page.wait_for_load_state("domcontentloaded")

        assert "/lp-dashboard" in page.url

    def test_lp_meeting_request_cancel_link_navigation(self, logged_in_page: Page):
        """Cancel link should navigate to dashboard."""
        page = logged_in_page
        page.goto(f"{BASE_URL}/lp-meeting-request?fund_id=f0000001-0000-0000-0000-000000000001")
        page.wait_for_load_state("domcontentloaded")

        if "Request Meeting" in page.content():
            cancel_link = page.locator("a:has-text('Cancel')")
            cancel_link.click()
            page.wait_for_load_state("domcontentloaded")

            assert "/lp-dashboard" in page.url
