"""Tests for LP Portal functionality.

IMPORTANT: Tests are the source of truth. Do NOT modify tests to make them pass.
If a test fails, fix the APPLICATION, not the test.

Test Categories:
- TestLPPortalMandate: Mandate editor page tests
- TestLPPortalMeetings: Meeting scheduler page tests
- TestLPPortalCompare: Fund comparison page tests
- TestLPPortalRedirects: Redirect behavior tests
- TestLPPortalSecurity: Security and access control tests
"""

import pytest


def login_as_lp(client):
    """Helper to log in as LP user."""
    client.post(
        "/api/auth/login",
        data={"email": "lp@demo.com", "password": "demo123"},
    )


class TestLPPortalMandate:
    """Tests for LP mandate editor page (/lp-portal/mandate)."""

    def test_mandate_page_returns_200(self, client):
        """Mandate page should return 200 OK."""
        login_as_lp(client)
        response = client.get("/lp-portal/mandate")
        assert response.status_code == 200

    def test_mandate_page_returns_html(self, client):
        """Mandate page should return HTML."""
        login_as_lp(client)
        response = client.get("/lp-portal/mandate")
        assert "text/html" in response.headers["content-type"]

    def test_mandate_page_has_title(self, client):
        """Mandate page should have appropriate title."""
        login_as_lp(client)
        response = client.get("/lp-portal/mandate")
        assert "Mandate" in response.text

    def test_mandate_page_has_strategy_section(self, client):
        """Mandate page should have strategy preferences section."""
        login_as_lp(client)
        response = client.get("/lp-portal/mandate")
        text = response.text
        assert "Strategy" in text or "strategy" in text.lower()

    def test_mandate_page_has_geography_section(self, client):
        """Mandate page should have geographic focus section."""
        login_as_lp(client)
        response = client.get("/lp-portal/mandate")
        text = response.text.lower()
        assert "geographic" in text or "region" in text

    def test_mandate_page_has_commitment_section(self, client):
        """Mandate page should have commitment parameters section."""
        login_as_lp(client)
        response = client.get("/lp-portal/mandate")
        text = response.text.lower()
        assert "commitment" in text or "size" in text

    def test_mandate_page_has_esg_section(self, client):
        """Mandate page should have ESG requirements section."""
        login_as_lp(client)
        response = client.get("/lp-portal/mandate")
        text = response.text
        assert "ESG" in text or "esg" in text.lower()

    def test_mandate_page_has_save_button(self, client):
        """Mandate page should have save functionality."""
        login_as_lp(client)
        response = client.get("/lp-portal/mandate")
        text = response.text.lower()
        assert "save" in text


class TestLPPortalMeetings:
    """Tests for LP meeting scheduler page (/lp-portal/meetings)."""

    def test_meetings_page_returns_200(self, client):
        """Meetings page should return 200 OK."""
        login_as_lp(client)
        response = client.get("/lp-portal/meetings")
        assert response.status_code == 200

    def test_meetings_page_returns_html(self, client):
        """Meetings page should return HTML."""
        login_as_lp(client)
        response = client.get("/lp-portal/meetings")
        assert "text/html" in response.headers["content-type"]

    def test_meetings_page_has_title(self, client):
        """Meetings page should have appropriate title."""
        login_as_lp(client)
        response = client.get("/lp-portal/meetings")
        assert "Meeting" in response.text

    def test_meetings_page_has_schedule_button(self, client):
        """Meetings page should have schedule button."""
        login_as_lp(client)
        response = client.get("/lp-portal/meetings")
        text = response.text
        assert "Schedule" in text or "schedule" in text.lower()

    def test_meetings_page_has_availability_section(self, client):
        """Meetings page should have availability settings."""
        login_as_lp(client)
        response = client.get("/lp-portal/meetings")
        text = response.text
        assert "Availability" in text or "availability" in text.lower()

    def test_meetings_page_has_upcoming_section(self, client):
        """Meetings page should have upcoming meetings section."""
        login_as_lp(client)
        response = client.get("/lp-portal/meetings")
        text = response.text.lower()
        assert "upcoming" in text or "meeting" in text


class TestLPPortalCompare:
    """Tests for LP fund comparison page (/lp-portal/compare)."""

    def test_compare_page_returns_200(self, client):
        """Compare funds page should return 200 OK."""
        login_as_lp(client)
        response = client.get("/lp-portal/compare")
        assert response.status_code == 200

    def test_compare_page_returns_html(self, client):
        """Compare funds page should return HTML."""
        login_as_lp(client)
        response = client.get("/lp-portal/compare")
        assert "text/html" in response.headers["content-type"]

    def test_compare_page_has_title(self, client):
        """Compare funds page should have appropriate title."""
        login_as_lp(client)
        response = client.get("/lp-portal/compare")
        assert "Compare" in response.text

    def test_compare_page_shows_demo_funds(self, client):
        """Compare funds page should show demo funds when none selected."""
        login_as_lp(client)
        response = client.get("/lp-portal/compare")
        text = response.text
        # Should show demo fund names
        assert "Apex" in text or "Growth" in text or "Fund" in text

    def test_compare_page_with_invalid_fund_ids(self, client):
        """Compare funds page should handle invalid fund IDs gracefully."""
        login_as_lp(client)
        response = client.get("/lp-portal/compare?fund_ids=not-a-uuid")
        assert response.status_code == 200
        assert "Compare" in response.text

    def test_compare_page_with_valid_uuid_no_db(self, client):
        """Compare funds page with valid UUID but no DB should show demo data."""
        login_as_lp(client)
        response = client.get("/lp-portal/compare?fund_ids=00000000-0000-0000-0000-000000000001")
        assert response.status_code == 200
        assert "Compare" in response.text

    def test_compare_page_has_export_button(self, client):
        """Compare funds page should have export functionality."""
        login_as_lp(client)
        response = client.get("/lp-portal/compare")
        text = response.text.lower()
        assert "export" in text

    @pytest.mark.parametrize("malicious_input", [
        "'; DROP TABLE funds; --",
        "<script>alert(1)</script>",
        "../../../etc/passwd",
    ])
    def test_compare_rejects_malicious_fund_ids(self, client, malicious_input):
        """Compare funds page should handle malicious input safely."""
        login_as_lp(client)
        response = client.get(f"/lp-portal/compare?fund_ids={malicious_input}")
        assert response.status_code == 200
        assert "Compare" in response.text


class TestLPPortalRedirects:
    """Tests for LP portal redirect behavior."""

    def test_lp_portal_home_redirects(self, client):
        """LP portal home should redirect to dashboard."""
        response = client.get("/lp-portal", follow_redirects=False)
        assert response.status_code == 303

    def test_lp_portal_funds_redirects(self, client):
        """LP portal funds should redirect to watchlist."""
        response = client.get("/lp-portal/funds", follow_redirects=False)
        assert response.status_code == 303


class TestLPPortalSecurity:
    """Security tests for LP portal."""

    @pytest.mark.parametrize("path", [
        "/lp-portal/mandate",
        "/lp-portal/meetings",
        "/lp-portal/compare",
    ])
    def test_lp_portal_pages_accessible(self, client, path):
        """LP portal pages should be accessible when logged in."""
        login_as_lp(client)
        response = client.get(path)
        # Pages should render
        assert response.status_code == 200

    @pytest.mark.parametrize("malicious_input", [
        "'; DROP TABLE users; --",
        "<script>alert(1)</script>",
        "{{constructor.constructor('return this')()}}",
    ])
    def test_lp_portal_mandate_rejects_xss_in_params(self, client, malicious_input):
        """LP portal should not reflect malicious input unsafely."""
        login_as_lp(client)
        response = client.get(f"/lp-portal/mandate?q={malicious_input}")
        assert response.status_code == 200
        # Input should not appear raw in response
        assert malicious_input not in response.text
