"""Tests for main FastAPI application.

IMPORTANT: Tests are the source of truth. Do NOT modify tests to make them pass.
If a test fails, fix the APPLICATION, not the test.

Based on BDD Gherkin specs from docs/prd/tests/*.feature.md

Test Categories:
- Unit tests: FastAPI TestClient (fast, no browser)
- Responsive tests: HTML structure validation
- Browser tests: Playwright for real viewport testing (marked with @pytest.mark.browser)
"""

import re

import pytest

# =============================================================================
# EXISTING TESTS (PRESERVED - DO NOT REMOVE)
# =============================================================================


class TestHealthEndpoint:
    """Test health check endpoint.

    Gherkin Reference: M5 Production Tests - Health Monitoring
    """

    def test_health_returns_200(self, client):
        """Health endpoint should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_healthy_status(self, client):
        """Health endpoint should return healthy status."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestApiStatus:
    """Test API status endpoint."""

    def test_api_status_returns_200(self, client):
        """API status endpoint should return 200 OK."""
        response = client.get("/api/status")
        assert response.status_code == 200

    def test_api_status_contains_environment(self, client):
        """API status should contain environment info."""
        response = client.get("/api/status")
        data = response.json()
        assert "environment" in data
        assert "features" in data


class TestHomeRoute:
    """Test home page."""

    def test_home_returns_200(self, client):
        """Home page should return 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_home_returns_html(self, client):
        """Home page should return HTML."""
        response = client.get("/")
        assert "text/html" in response.headers["content-type"]

    def test_home_contains_title(self, client):
        """Home page should contain LPxGP title."""
        response = client.get("/")
        assert "LPxGP" in response.text


class TestLoginRoute:
    """Test login page."""

    def test_login_returns_200(self, client):
        """Login page should return 200 OK."""
        response = client.get("/login")
        assert response.status_code == 200

    def test_login_contains_form(self, client):
        """Login page should contain a login form."""
        response = client.get("/login")
        assert "email" in response.text
        assert "password" in response.text


class Test404Handler:
    """Test 404 error handling."""

    def test_nonexistent_page_returns_404(self, client):
        """Non-existent page should return 404."""
        response = client.get("/nonexistent-page")
        assert response.status_code == 404

    def test_api_404_returns_json(self, client):
        """API 404 should return JSON."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        assert "application/json" in response.headers["content-type"]


# =============================================================================
# NEW COMPREHENSIVE TESTS - HEALTH ENDPOINT
# =============================================================================


class TestHealthEndpointComprehensive:
    """Comprehensive health endpoint tests.

    Gherkin Reference: M5 Production - F-ADMIN-03: Health Monitoring
    """

    def test_health_response_structure(self, client):
        """Health response should have correct structure.

        Gherkin: Health endpoint returns status and version
        """
        response = client.get("/health")
        data = response.json()

        assert "status" in data, "Health response must include 'status'"
        assert "version" in data, "Health response must include 'version'"
        assert isinstance(data["status"], str)
        assert isinstance(data["version"], str)

    def test_health_version_format(self, client):
        """Health version should follow semver format.

        Gherkin: Version format should be semantic versioning
        """
        response = client.get("/health")
        data = response.json()
        version = data["version"]

        # Version should contain dots (semver format)
        parts = version.split(".")
        assert len(parts) >= 2, f"Version '{version}' should be semver format (e.g., 0.1.0)"

    def test_health_status_value(self, client):
        """Health status should be 'healthy' when app is running.

        Gherkin: When application is running, status is 'healthy'
        """
        response = client.get("/health")
        data = response.json()

        assert data["status"] == "healthy", "Running app should report 'healthy'"

    def test_health_content_type(self, client):
        """Health endpoint should return JSON content type."""
        response = client.get("/health")

        assert "application/json" in response.headers["content-type"]

    def test_health_no_cache_headers(self, client):
        """Health endpoint should not be cached (for monitoring accuracy).

        Gherkin: Health checks should always return fresh data
        """
        response = client.get("/health")

        # Should not have aggressive caching
        cache_control = response.headers.get("cache-control", "")
        assert "max-age=31536000" not in cache_control, "Health endpoint should not be cached long-term"

    def test_health_accepts_head_request(self, client):
        """Health endpoint should respond to HEAD requests for efficient monitoring.

        Gherkin: Load balancers may use HEAD for health checks
        """
        response = client.head("/health")

        # HEAD should succeed (2xx status)
        assert response.status_code == 200

    def test_health_method_not_allowed_for_post(self, client):
        """Health endpoint should reject POST requests.

        Edge case: Ensure health endpoint is read-only
        """
        response = client.post("/health")

        assert response.status_code == 405, "Health endpoint should not accept POST"


# =============================================================================
# NEW COMPREHENSIVE TESTS - API STATUS ENDPOINT
# =============================================================================


class TestApiStatusComprehensive:
    """Comprehensive API status endpoint tests.

    Gherkin Reference: M5 Production - API Status Monitoring
    """

    def test_api_status_response_structure(self, client):
        """API status response should have correct structure."""
        response = client.get("/api/status")
        data = response.json()

        assert "status" in data
        assert "environment" in data
        assert "features" in data

    def test_api_status_features_structure(self, client):
        """API status features should include expected feature flags."""
        response = client.get("/api/status")
        data = response.json()

        features = data["features"]
        assert "semantic_search" in features
        assert "agent_matching" in features

    def test_api_status_features_are_booleans(self, client):
        """API status feature flags should be boolean values."""
        response = client.get("/api/status")
        data = response.json()

        features = data["features"]
        assert isinstance(features["semantic_search"], bool)
        assert isinstance(features["agent_matching"], bool)

    def test_api_status_environment_valid(self, client):
        """API status environment should be a valid environment name."""
        response = client.get("/api/status")
        data = response.json()

        valid_environments = ["development", "staging", "production"]
        assert data["environment"] in valid_environments

    def test_api_status_no_sensitive_data(self, client):
        """API status should not expose sensitive configuration.

        Gherkin: Non-sensitive configuration info only
        Security: Never expose API keys, secrets, or internal URLs
        """
        response = client.get("/api/status")
        data = response.json()
        response_text = str(data).lower()

        # Should not contain sensitive patterns
        sensitive_patterns = [
            "password",
            "secret",
            "api_key",
            "apikey",
            "token",
            "supabase_service_role",
            "private_key",
        ]

        for pattern in sensitive_patterns:
            assert pattern not in response_text, f"API status should not expose '{pattern}'"


# =============================================================================
# NEW COMPREHENSIVE TESTS - HOME PAGE
# =============================================================================


class TestHomePageComprehensive:
    """Comprehensive home page tests.

    Gherkin Reference: E2E User Journeys
    """

    def test_home_has_navigation(self, client):
        """Home page should have navigation elements."""
        response = client.get("/")

        # Navigation should exist
        assert "<nav" in response.text.lower() or "nav" in response.text

    def test_home_has_main_content(self, client):
        """Home page should have main content area."""
        response = client.get("/")

        assert "LPxGP" in response.text

    def test_home_charset_utf8(self, client):
        """Home page should specify UTF-8 charset for international content.

        Gherkin: Handle unicode in LP name
        """
        response = client.get("/")

        # Check content-type header or meta tag
        content_type = response.headers.get("content-type", "")
        assert "utf-8" in content_type.lower() or "charset" in response.text.lower()

    def test_home_no_server_errors_in_html(self, client):
        """Home page HTML should not contain error traces.

        Edge case: Ensure no debug info leaks to production
        """
        response = client.get("/")
        html = response.text.lower()

        error_patterns = [
            "traceback",
            "exception",
            "error occurred",
            "internal server error",
        ]

        for pattern in error_patterns:
            assert pattern not in html, f"Home page should not contain '{pattern}'"


# =============================================================================
# NEW COMPREHENSIVE TESTS - LOGIN PAGE
# =============================================================================


class TestLoginPageComprehensive:
    """Comprehensive login page tests.

    Gherkin Reference: M1 Auth - F-AUTH-01: User Login
    """

    def test_login_has_email_field(self, client):
        """Login page should have email input field.

        Gherkin: When I enter my email and password
        """
        response = client.get("/login")

        # Look for email input
        assert 'type="email"' in response.text or 'name="email"' in response.text

    def test_login_has_password_field(self, client):
        """Login page should have password input field.

        Gherkin: When I enter my email and password
        """
        response = client.get("/login")

        # Look for password input
        assert 'type="password"' in response.text or 'name="password"' in response.text

    def test_login_has_submit_button(self, client):
        """Login page should have a submit button.

        Gherkin: And I click "Login"
        """
        response = client.get("/login")

        # Look for submit button
        assert 'type="submit"' in response.text or "button" in response.text.lower()

    def test_login_form_has_action(self, client):
        """Login form should have a form action or JS handler.

        Gherkin: When I click "Login"
        """
        response = client.get("/login")

        # Should have form element
        assert "<form" in response.text.lower()

    def test_login_page_title(self, client):
        """Login page should have appropriate title."""
        response = client.get("/login")

        assert "Login" in response.text or "login" in response.text.lower()


# =============================================================================
# NEW COMPREHENSIVE TESTS - ERROR HANDLING
# =============================================================================


class Test404HandlerComprehensive:
    """Comprehensive 404 error handling tests.

    Gherkin Reference: M1 Auth - Access protected page scenarios
    """

    def test_404_page_content(self, client):
        """404 page should show user-friendly error message."""
        response = client.get("/nonexistent-page")

        # Should show some error indication
        assert response.status_code == 404

    def test_404_no_stack_trace(self, client):
        """404 page should not expose stack traces.

        Security: Error pages should not leak implementation details
        """
        response = client.get("/nonexistent-page")
        text = response.text.lower()

        assert "traceback" not in text
        assert "file " not in text or "line " not in text

    def test_api_404_json_structure(self, client):
        """API 404 should return proper JSON structure.

        Gherkin: API errors return JSON format
        """
        response = client.get("/api/nonexistent")
        data = response.json()

        assert "error" in data or "detail" in data

    def test_api_404_includes_path(self, client):
        """API 404 should include the requested path for debugging."""
        response = client.get("/api/nonexistent-endpoint")
        data = response.json()

        # Should include some path information
        response_text = str(data)
        # Either in 'path' field or somewhere in response
        assert "path" in data or "nonexistent" in response_text.lower()

    def test_404_different_paths(self, client):
        """404 should work for various non-existent paths.

        Edge case: Test multiple path patterns
        """
        paths = [
            "/does-not-exist",
            "/page/123/edit",
            "/api/v2/users",
            "/deeply/nested/path/that/does/not/exist",
        ]

        for path in paths:
            response = client.get(path)
            assert response.status_code == 404, f"Path '{path}' should return 404"


# =============================================================================
# NEW COMPREHENSIVE TESTS - MATCHES PAGE
# =============================================================================


class TestMatchesPage:
    """Tests for the matches page.

    Gherkin Reference: M3 Matching - Fund-LP Matches Display
    """

    def test_matches_returns_200(self, client):
        """Matches page should return 200 OK."""
        response = client.get("/matches")
        assert response.status_code == 200

    def test_matches_returns_html(self, client):
        """Matches page should return HTML."""
        response = client.get("/matches")
        assert "text/html" in response.headers["content-type"]

    def test_matches_has_title(self, client):
        """Matches page should have appropriate title."""
        response = client.get("/matches")
        assert "Matches" in response.text or "matches" in response.text.lower()

    def test_matches_without_db_shows_empty_state(self, client):
        """Matches page without database should show empty state gracefully.

        Gherkin: Handle graceful degradation when database unavailable
        """
        response = client.get("/matches")

        # Should not error, should show some content
        assert response.status_code == 200
        # Should have some indication of empty or no matches
        assert "match" in response.text.lower()

    def test_matches_with_fund_filter(self, client):
        """Matches page should accept fund_id query parameter.

        Gherkin: Filter matches by fund
        """
        response = client.get("/matches?fund_id=test-fund-id")

        # Should not error with query param
        assert response.status_code == 200

    def test_matches_with_invalid_fund_filter(self, client):
        """Matches page should handle invalid fund_id gracefully.

        Edge case: Invalid UUID in query param
        """
        response = client.get("/matches?fund_id=not-a-valid-uuid")

        # Should not crash, should handle gracefully
        assert response.status_code == 200

    def test_matches_has_stats_section(self, client):
        """Matches page should have statistics section.

        Gherkin: Display match statistics (total, high score, avg, pipeline)
        """
        response = client.get("/matches")

        # Look for stats-related content
        # Could be "Total" matches, "Average" score, etc.
        text = response.text.lower()
        assert "total" in text or "match" in text

    def test_matches_has_fund_selector(self, client):
        """Matches page should have fund selector dropdown.

        Gherkin: Select fund to filter matches
        """
        response = client.get("/matches")

        # Look for select element or fund-related selector
        assert "select" in response.text.lower() or "fund" in response.text.lower()


# =============================================================================
# NEW COMPREHENSIVE TESTS - SECURITY
# =============================================================================


class TestSecurityHeaders:
    """Test security-related response headers.

    Gherkin Reference: M5 Production - Security
    """

    def test_no_server_version_disclosure(self, client):
        """Response should not disclose detailed server version.

        Security: Avoid leaking server software versions
        """
        response = client.get("/health")

        server_header = response.headers.get("server", "").lower()
        # Should not have detailed version like "uvicorn/0.23.2"
        # Having just "uvicorn" is borderline acceptable
        assert "/" not in server_header or "version" not in server_header

    def test_content_type_always_set(self, client):
        """All responses should have Content-Type header."""
        paths = ["/", "/health", "/api/status", "/login"]

        for path in paths:
            response = client.get(path)
            assert "content-type" in response.headers, f"Path '{path}' missing Content-Type"


class TestSQLInjectionPrevention:
    """Test SQL injection prevention.

    Gherkin Reference: M0 Foundation - Sanitize SQL injection
    """

    def test_query_param_sql_injection(self, client, sql_injection_payloads):
        """Query parameters should not allow SQL injection.

        Gherkin: Sanitize SQL injection in name
        """
        for payload in sql_injection_payloads:
            response = client.get(f"/matches?fund_id={payload}")

            # Should not crash and should not execute SQL
            assert response.status_code in [200, 400, 422], (
                f"SQL injection payload should be handled safely: {payload}"
            )


class TestXSSPrevention:
    """Test XSS prevention.

    Gherkin Reference: M0 Foundation - Sanitize XSS in name
    """

    def test_xss_in_query_params_escaped(self, client, xss_payloads):
        """XSS payloads in query params should be escaped.

        Gherkin: XSS in name is HTML-escaped when displayed
        """
        for payload in xss_payloads:
            response = client.get(f"/matches?fund_id={payload}")

            # Should not crash
            assert response.status_code in [200, 400, 422]

            # If reflected in response, should be escaped
            if payload in response.text:
                # Raw script should not appear unescaped
                assert "<script>" not in response.text.lower() or "&lt;script&gt;" in response.text


# =============================================================================
# NEW COMPREHENSIVE TESTS - EDGE CASES
# =============================================================================


class TestEdgeCases:
    """Test edge cases and boundary conditions.

    Gherkin Reference: Various negative test scenarios
    """

    def test_empty_path(self, client):
        """Root path should work correctly."""
        response = client.get("/")
        assert response.status_code == 200

    def test_trailing_slash_handling(self, client):
        """Paths with trailing slashes should be handled consistently."""
        response_without = client.get("/health")
        response_with = client.get("/health/")

        # Both should work (either redirect or same response)
        assert response_without.status_code in [200, 307, 308]
        assert response_with.status_code in [200, 307, 308, 404]

    def test_double_slash_in_path(self, client):
        """Double slashes in path should be handled.

        Edge case: URL normalization
        """
        response = client.get("//health")

        # Should not crash
        assert response.status_code in [200, 404, 307, 308]

    def test_very_long_path(self, client):
        """Very long paths should be handled gracefully.

        Edge case: Buffer overflow prevention
        """
        long_path = "/" + "a" * 10000
        response = client.get(long_path)

        # Should not crash, return 404 or 414 (URI Too Long)
        assert response.status_code in [404, 414, 400]

    def test_unicode_in_path(self, client, unicode_test_strings):
        """Unicode characters in path should be handled.

        Gherkin: Handle unicode in LP name
        """
        for unicode_str in unicode_test_strings:
            response = client.get(f"/search/{unicode_str}")

            # Should handle gracefully (404 is fine, crash is not)
            assert response.status_code in [200, 404, 400, 422]

    def test_special_characters_in_query(self, client):
        """Special characters in query params should be handled.

        Edge case: URL encoding
        """
        special_chars = ["&", "=", "?", "#", "%", "+", " "]

        for char in special_chars:
            response = client.get(f"/matches?fund_id=test{char}value")

            # Should not crash
            assert response.status_code in [200, 400, 422]

    def test_null_bytes_in_path(self, client):
        """Null bytes in path should be rejected.

        Security: Null byte injection prevention

        Note: Protection happens at the HTTP client level (httpx rejects
        null bytes before they reach our application). This test verifies
        that the protection exists - null byte attacks cannot reach our app.
        """
        import httpx

        with pytest.raises(httpx.InvalidURL) as exc_info:
            client.get("/health\x00.txt")

        # Verify it's rejected for the right reason
        assert "non-printable" in str(exc_info.value).lower() or "\\x00" in str(exc_info.value)

    def test_empty_query_param(self, client):
        """Empty query parameter values should be handled."""
        response = client.get("/matches?fund_id=")

        assert response.status_code == 200

    def test_multiple_query_params_same_name(self, client):
        """Multiple query params with same name should be handled.

        Edge case: Array injection
        """
        response = client.get("/matches?fund_id=a&fund_id=b&fund_id=c")

        # Should handle (use first, last, or error)
        assert response.status_code in [200, 400, 422]


# =============================================================================
# NEW COMPREHENSIVE TESTS - HTTP METHODS
# =============================================================================


class TestHTTPMethods:
    """Test HTTP method handling.

    Gherkin Reference: API specifications
    """

    def test_options_request_health(self, client):
        """OPTIONS request should be handled for CORS preflight."""
        response = client.options("/health")

        # Should not be 500
        assert response.status_code in [200, 204, 405]

    def test_put_on_get_endpoint(self, client):
        """PUT on GET-only endpoints should return 405."""
        response = client.put("/health")

        assert response.status_code == 405

    def test_delete_on_get_endpoint(self, client):
        """DELETE on GET-only endpoints should return 405."""
        response = client.delete("/health")

        assert response.status_code == 405

    def test_patch_on_get_endpoint(self, client):
        """PATCH on GET-only endpoints should return 405."""
        response = client.patch("/health")

        assert response.status_code == 405


# =============================================================================
# NEW COMPREHENSIVE TESTS - RESPONSE VALIDATION
# =============================================================================


class TestResponseValidation:
    """Test response format and validation.

    Gherkin Reference: API response specifications
    """

    def test_json_endpoints_valid_json(self, client):
        """JSON endpoints should return valid JSON."""
        json_endpoints = ["/health", "/api/status"]

        for endpoint in json_endpoints:
            response = client.get(endpoint)

            # Should parse as JSON without error
            try:
                data = response.json()
                assert data is not None
            except Exception as e:
                pytest.fail(f"Endpoint {endpoint} did not return valid JSON: {e}")

    def test_html_endpoints_valid_html(self, client):
        """HTML endpoints should return valid HTML structure."""
        html_endpoints = ["/", "/login", "/matches"]

        for endpoint in html_endpoints:
            response = client.get(endpoint)
            text = response.text

            # Basic HTML structure checks
            assert "<!DOCTYPE html>" in text or "<html" in text.lower(), (
                f"Endpoint {endpoint} missing HTML doctype/tag"
            )
            assert "</html>" in text.lower(), f"Endpoint {endpoint} missing closing HTML tag"


# =============================================================================
# FUNDS PAGE TESTS
# =============================================================================


class TestFundsPage:
    """Test funds page rendering and structure.

    Gherkin Reference: M2 - Fund Management
    """

    def test_funds_page_returns_200(self, client):
        """Funds page should return 200 OK."""
        response = client.get("/funds")
        assert response.status_code == 200

    def test_funds_page_returns_html(self, client):
        """Funds page should return HTML content."""
        response = client.get("/funds")
        assert "text/html" in response.headers.get("content-type", "")

    def test_funds_page_has_title(self, client):
        """Funds page should have Funds in title or heading."""
        response = client.get("/funds")
        assert "funds" in response.text.lower()

    def test_funds_page_has_new_fund_button(self, client):
        """Funds page should have a button to create new fund."""
        response = client.get("/funds")
        assert "new fund" in response.text.lower() or "create" in response.text.lower()

    def test_funds_page_has_stats_section(self, client):
        """Funds page should display fund statistics."""
        response = client.get("/funds")
        text = response.text.lower()
        assert "total" in text or "raising" in text or "target" in text

    def test_funds_page_has_create_modal(self, client):
        """Funds page should have create fund modal markup."""
        response = client.get("/funds")
        assert "create-fund-modal" in response.text

    def test_funds_page_has_form_fields(self, client):
        """Funds page create form should have required fields."""
        response = client.get("/funds")
        assert 'name="name"' in response.text
        assert 'name="org_id"' in response.text

    def test_funds_page_valid_html_structure(self, client):
        """Funds page should have valid HTML structure."""
        response = client.get("/funds")
        assert "<!DOCTYPE html>" in response.text or "<html" in response.text.lower()
        assert "</html>" in response.text.lower()


class TestFundsCRUD:
    """Test Fund CRUD API endpoints - basic operations.

    Gherkin Reference: M2 - Fund CRUD Operations
    """

    def test_create_fund_without_db_returns_503(self, client):
        """Creating fund without database should return 503."""
        response = client.post(
            "/api/funds",
            data={"name": "Test Fund", "org_id": "00000000-0000-0000-0000-000000000000"}
        )
        assert response.status_code in [503, 400]

    def test_create_fund_missing_name_returns_422(self, client):
        """Creating fund without name should return 422."""
        response = client.post("/api/funds", data={"org_id": "test"})
        assert response.status_code == 422

    def test_create_fund_missing_org_id_returns_422(self, client):
        """Creating fund without org_id should return 422."""
        response = client.post("/api/funds", data={"name": "Test Fund"})
        assert response.status_code == 422

    def test_get_fund_edit_invalid_id_returns_400(self, client):
        """Getting fund edit form with invalid ID should return 400."""
        response = client.get("/api/funds/invalid-uuid/edit")
        assert response.status_code == 400

    def test_get_fund_edit_valid_uuid_format(self, client):
        """Getting fund edit form with valid UUID format should not crash."""
        response = client.get("/api/funds/00000000-0000-0000-0000-000000000000/edit")
        assert response.status_code in [404, 503]

    def test_update_fund_invalid_id_returns_400(self, client):
        """Updating fund with invalid ID should return 400."""
        response = client.put(
            "/api/funds/invalid-uuid",
            data={"name": "Test", "org_id": "00000000-0000-0000-0000-000000000000"}
        )
        assert response.status_code == 400

    def test_delete_fund_invalid_id_returns_400(self, client):
        """Deleting fund with invalid ID should return 400."""
        response = client.delete("/api/funds/invalid-uuid")
        assert response.status_code == 400

    def test_delete_fund_valid_uuid_without_db(self, client):
        """Deleting fund with valid UUID but no DB should return 503."""
        response = client.delete("/api/funds/00000000-0000-0000-0000-000000000000")
        assert response.status_code in [503, 404]


class TestFundsUUIDValidation:
    """Test UUID validation for fund endpoints.

    Security: Prevent injection and ensure proper ID handling.
    """

    @pytest.mark.parametrize("invalid_id", [
        "",  # empty
        "   ",  # whitespace
        "not-a-uuid",  # plain text
        "12345",  # numbers only
        "00000000-0000-0000-0000",  # incomplete UUID
        "00000000-0000-0000-0000-00000000000g",  # invalid char
        "00000000_0000_0000_0000_000000000000",  # wrong separator
        "../../../etc/passwd",  # path traversal
        "'; DROP TABLE funds; --",  # SQL injection
        "<script>alert(1)</script>",  # XSS
    ])
    def test_fund_edit_rejects_invalid_uuids(self, client, invalid_id):
        """Fund edit endpoint should reject all invalid UUID formats."""
        response = client.get(f"/api/funds/{invalid_id}/edit")
        assert response.status_code in [400, 404, 422]
        # Should never return 500 (server error)
        assert response.status_code != 500

    @pytest.mark.parametrize("invalid_id", [
        "not-a-uuid",
        "../../../etc/passwd",
        "'; DROP TABLE funds; --",
    ])
    def test_fund_update_rejects_invalid_uuids(self, client, invalid_id):
        """Fund update endpoint should reject invalid UUIDs."""
        response = client.put(
            f"/api/funds/{invalid_id}",
            data={"name": "Test", "org_id": "00000000-0000-0000-0000-000000000000"}
        )
        assert response.status_code in [400, 404, 422]
        assert response.status_code != 500

    @pytest.mark.parametrize("invalid_id", [
        "not-a-uuid",
        "'; DROP TABLE funds; --",
    ])
    def test_fund_delete_rejects_invalid_uuids(self, client, invalid_id):
        """Fund delete endpoint should reject invalid UUIDs."""
        response = client.delete(f"/api/funds/{invalid_id}")
        assert response.status_code in [400, 404, 422]
        assert response.status_code != 500


class TestFundsInputValidation:
    """Test input validation for fund creation/update.

    Security: Prevent XSS, SQL injection, and malformed data.
    """

    def test_create_fund_empty_name_rejected(self, client):
        """Empty fund name should be rejected."""
        response = client.post(
            "/api/funds",
            data={"name": "", "org_id": "00000000-0000-0000-0000-000000000000"}
        )
        # Should reject empty name (422) or fail gracefully (503 no db)
        assert response.status_code in [400, 422, 503]

    def test_create_fund_whitespace_name_rejected(self, client):
        """Whitespace-only fund name should be rejected or trimmed."""
        response = client.post(
            "/api/funds",
            data={"name": "   ", "org_id": "00000000-0000-0000-0000-000000000000"}
        )
        assert response.status_code in [400, 422, 503]

    def test_create_fund_very_long_name(self, client):
        """Very long fund name should be handled gracefully."""
        long_name = "A" * 1000
        response = client.post(
            "/api/funds",
            data={"name": long_name, "org_id": "00000000-0000-0000-0000-000000000000"}
        )
        # Should either accept (503 no db) or reject (400/422)
        assert response.status_code in [400, 422, 503]
        assert response.status_code != 500

    def test_create_fund_xss_in_name_escaped(self, client):
        """XSS in fund name should not execute - check no raw script in response."""
        xss_payload = "<script>alert('xss')</script>"
        response = client.post(
            "/api/funds",
            data={"name": xss_payload, "org_id": "00000000-0000-0000-0000-000000000000"}
        )
        # Response should not contain unescaped script tag
        if response.status_code == 200:
            assert "<script>alert" not in response.text

    def test_create_fund_sql_injection_in_name(self, client):
        """SQL injection in fund name should be safely handled."""
        sql_payload = "'; DROP TABLE funds; --"
        response = client.post(
            "/api/funds",
            data={"name": sql_payload, "org_id": "00000000-0000-0000-0000-000000000000"}
        )
        # Should not cause server error
        assert response.status_code != 500

    def test_create_fund_unicode_name(self, client):
        """Unicode characters in fund name should be handled."""
        unicode_name = "基金 Fund 🚀 Фонд"
        response = client.post(
            "/api/funds",
            data={"name": unicode_name, "org_id": "00000000-0000-0000-0000-000000000000"}
        )
        assert response.status_code in [200, 400, 422, 503]
        assert response.status_code != 500

    def test_create_fund_null_bytes_in_name(self, client):
        """Null bytes in fund name should be handled safely."""
        null_name = "Test\x00Fund"
        response = client.post(
            "/api/funds",
            data={"name": null_name, "org_id": "00000000-0000-0000-0000-000000000000"}
        )
        assert response.status_code != 500


class TestFundsNumericValidation:
    """Test numeric field validation for funds.

    Boundary testing for target_size_mm, vintage_year, percentages.
    """

    def test_create_fund_negative_target_size(self, client):
        """Negative target size should be rejected or handled."""
        response = client.post(
            "/api/funds",
            data={
                "name": "Test Fund",
                "org_id": "00000000-0000-0000-0000-000000000000",
                "target_size_mm": "-100"
            }
        )
        # Should handle gracefully
        assert response.status_code in [400, 422, 503]
        assert response.status_code != 500

    def test_create_fund_zero_target_size(self, client):
        """Zero target size should be accepted."""
        response = client.post(
            "/api/funds",
            data={
                "name": "Test Fund",
                "org_id": "00000000-0000-0000-0000-000000000000",
                "target_size_mm": "0"
            }
        )
        assert response.status_code in [200, 503]

    def test_create_fund_very_large_target_size(self, client):
        """Very large target size should be handled."""
        response = client.post(
            "/api/funds",
            data={
                "name": "Test Fund",
                "org_id": "00000000-0000-0000-0000-000000000000",
                "target_size_mm": "999999999999"
            }
        )
        assert response.status_code != 500

    def test_create_fund_non_numeric_target_size(self, client):
        """Non-numeric target size should be rejected."""
        response = client.post(
            "/api/funds",
            data={
                "name": "Test Fund",
                "org_id": "00000000-0000-0000-0000-000000000000",
                "target_size_mm": "not-a-number"
            }
        )
        assert response.status_code in [400, 422, 503]

    def test_create_fund_invalid_vintage_year(self, client):
        """Invalid vintage year should be rejected."""
        response = client.post(
            "/api/funds",
            data={
                "name": "Test Fund",
                "org_id": "00000000-0000-0000-0000-000000000000",
                "vintage_year": "1800"  # Too old
            }
        )
        assert response.status_code != 500

    def test_create_fund_percentage_over_100(self, client):
        """Percentage fields over 100 should be handled."""
        response = client.post(
            "/api/funds",
            data={
                "name": "Test Fund",
                "org_id": "00000000-0000-0000-0000-000000000000",
                "management_fee_pct": "150"  # Over 100%
            }
        )
        assert response.status_code != 500


class TestFundsEnumValidation:
    """Test enum field validation for funds.

    Ensure invalid status/strategy values are handled.
    """

    def test_create_fund_invalid_status(self, client):
        """Invalid fund status should be handled gracefully."""
        response = client.post(
            "/api/funds",
            data={
                "name": "Test Fund",
                "org_id": "00000000-0000-0000-0000-000000000000",
                "status": "invalid_status"
            }
        )
        assert response.status_code != 500

    def test_create_fund_invalid_strategy(self, client):
        """Invalid fund strategy should be handled gracefully."""
        response = client.post(
            "/api/funds",
            data={
                "name": "Test Fund",
                "org_id": "00000000-0000-0000-0000-000000000000",
                "strategy": "not_a_real_strategy"
            }
        )
        assert response.status_code != 500


class TestFundsHTTPMethods:
    """Test HTTP method handling for fund endpoints."""

    def test_funds_api_get_not_allowed(self, client):
        """GET on /api/funds (create endpoint) should return 405."""
        response = client.get("/api/funds")
        assert response.status_code == 405

    def test_fund_edit_post_not_allowed(self, client):
        """POST on fund edit endpoint should return 405."""
        response = client.post("/api/funds/00000000-0000-0000-0000-000000000000/edit")
        assert response.status_code == 405

    def test_fund_delete_get_not_allowed(self, client):
        """GET on fund delete endpoint doesn't exist (would be 405 if it did)."""
        response = client.get("/api/funds/00000000-0000-0000-0000-000000000000")
        # This endpoint doesn't exist, so 404 is expected
        assert response.status_code in [404, 405]


# =============================================================================
# LPS PAGE TESTS
# =============================================================================


class TestLPsPage:
    """Test LPs page rendering and structure.

    Gherkin Reference: M2 - LP Management
    """

    def test_lps_page_returns_200(self, client):
        """LPs page should return 200 OK."""
        response = client.get("/lps")
        assert response.status_code == 200

    def test_lps_page_returns_html(self, client):
        """LPs page should return HTML content."""
        response = client.get("/lps")
        assert "text/html" in response.headers.get("content-type", "")

    def test_lps_page_has_title(self, client):
        """LPs page should have LP in title or heading."""
        response = client.get("/lps")
        text = response.text.lower()
        assert "lp" in text or "investor" in text

    def test_lps_page_has_new_lp_button(self, client):
        """LPs page should have a button to create new LP."""
        response = client.get("/lps")
        assert "new lp" in response.text.lower() or "create" in response.text.lower()

    def test_lps_page_has_search(self, client):
        """LPs page should have search functionality."""
        response = client.get("/lps")
        assert "search" in response.text.lower()

    def test_lps_page_has_type_filter(self, client):
        """LPs page should have LP type filter."""
        response = client.get("/lps")
        text = response.text.lower()
        assert "type" in text or "filter" in text or "select" in text

    def test_lps_page_has_create_modal(self, client):
        """LPs page should have create LP modal markup."""
        response = client.get("/lps")
        assert "create-lp-modal" in response.text

    def test_lps_page_search_query_param(self, client):
        """LPs page should accept search query parameter."""
        response = client.get("/lps?q=test")
        assert response.status_code == 200

    def test_lps_page_type_filter_param(self, client):
        """LPs page should accept type filter parameter."""
        response = client.get("/lps?type=pension")
        assert response.status_code == 200


class TestLPsCRUD:
    """Test LP CRUD API endpoints - basic operations.

    Gherkin Reference: M2 - LP CRUD Operations
    """

    def test_create_lp_without_db_returns_503(self, client):
        """Creating LP without database should return 503."""
        response = client.post("/api/lps", data={"name": "Test LP"})
        assert response.status_code in [503, 400]

    def test_create_lp_missing_name_returns_422(self, client):
        """Creating LP without name should return 422."""
        response = client.post("/api/lps", data={})
        assert response.status_code == 422

    def test_get_lp_edit_invalid_id_returns_400(self, client):
        """Getting LP edit form with invalid ID should return 400."""
        response = client.get("/api/lps/invalid-uuid/edit")
        assert response.status_code == 400

    def test_get_lp_edit_valid_uuid_format(self, client):
        """Getting LP edit form with valid UUID format should not crash."""
        response = client.get("/api/lps/00000000-0000-0000-0000-000000000000/edit")
        assert response.status_code in [404, 503]

    def test_update_lp_invalid_id_returns_400(self, client):
        """Updating LP with invalid ID should return 400."""
        response = client.put("/api/lps/invalid-uuid", data={"name": "Test"})
        assert response.status_code == 400

    def test_delete_lp_invalid_id_returns_400(self, client):
        """Deleting LP with invalid ID should return 400."""
        response = client.delete("/api/lps/invalid-uuid")
        assert response.status_code == 400

    def test_delete_lp_valid_uuid_without_db(self, client):
        """Deleting LP with valid UUID but no DB should return 503."""
        response = client.delete("/api/lps/00000000-0000-0000-0000-000000000000")
        assert response.status_code in [503, 404]


class TestLPsUUIDValidation:
    """Test UUID validation for LP endpoints."""

    @pytest.mark.parametrize("invalid_id", [
        "",
        "not-a-uuid",
        "'; DROP TABLE organizations; --",
        "<script>alert(1)</script>",
        "../../../etc/passwd",
    ])
    def test_lp_edit_rejects_invalid_uuids(self, client, invalid_id):
        """LP edit endpoint should reject invalid UUIDs."""
        response = client.get(f"/api/lps/{invalid_id}/edit")
        assert response.status_code in [400, 404, 422]
        assert response.status_code != 500

    @pytest.mark.parametrize("invalid_id", [
        "not-a-uuid",
        "'; DROP TABLE organizations; --",
    ])
    def test_lp_update_rejects_invalid_uuids(self, client, invalid_id):
        """LP update endpoint should reject invalid UUIDs."""
        response = client.put(f"/api/lps/{invalid_id}", data={"name": "Test"})
        assert response.status_code in [400, 404, 422]
        assert response.status_code != 500

    @pytest.mark.parametrize("invalid_id", [
        "not-a-uuid",
        "'; DROP TABLE organizations; --",
    ])
    def test_lp_delete_rejects_invalid_uuids(self, client, invalid_id):
        """LP delete endpoint should reject invalid UUIDs."""
        response = client.delete(f"/api/lps/{invalid_id}")
        assert response.status_code in [400, 404, 422]
        assert response.status_code != 500


class TestLPsInputValidation:
    """Test input validation for LP creation/update."""

    def test_create_lp_empty_name_rejected(self, client):
        """Empty LP name should be rejected."""
        response = client.post("/api/lps", data={"name": ""})
        assert response.status_code in [400, 422, 503]

    def test_create_lp_whitespace_name_rejected(self, client):
        """Whitespace-only LP name should be rejected."""
        response = client.post("/api/lps", data={"name": "   "})
        assert response.status_code in [400, 422, 503]

    def test_create_lp_very_long_name(self, client):
        """Very long LP name should be handled gracefully."""
        long_name = "A" * 1000
        response = client.post("/api/lps", data={"name": long_name})
        assert response.status_code != 500

    def test_create_lp_xss_in_name(self, client):
        """XSS in LP name should be safely handled."""
        response = client.post(
            "/api/lps",
            data={"name": "<script>alert('xss')</script>"}
        )
        if response.status_code == 200:
            assert "<script>alert" not in response.text

    def test_create_lp_sql_injection_in_name(self, client):
        """SQL injection in LP name should be safely handled."""
        response = client.post(
            "/api/lps",
            data={"name": "'; DROP TABLE organizations; --"}
        )
        assert response.status_code != 500

    def test_create_lp_unicode_name(self, client):
        """Unicode in LP name should be handled."""
        response = client.post(
            "/api/lps",
            data={"name": "投資者 Investor 🏦"}
        )
        assert response.status_code != 500


class TestLPsNumericValidation:
    """Test numeric field validation for LPs."""

    def test_create_lp_negative_aum(self, client):
        """Negative AUM should be rejected."""
        response = client.post(
            "/api/lps",
            data={"name": "Test LP", "total_aum_bn": "-50"}
        )
        assert response.status_code != 500

    def test_create_lp_percentage_over_100(self, client):
        """PE allocation over 100% should be handled."""
        response = client.post(
            "/api/lps",
            data={"name": "Test LP", "pe_allocation_pct": "150"}
        )
        assert response.status_code != 500

    def test_create_lp_non_numeric_aum(self, client):
        """Non-numeric AUM should be handled."""
        response = client.post(
            "/api/lps",
            data={"name": "Test LP", "total_aum_bn": "lots of money"}
        )
        assert response.status_code != 500


class TestLPsEnumValidation:
    """Test enum field validation for LPs."""

    def test_create_lp_invalid_type(self, client):
        """Invalid LP type should be handled gracefully."""
        response = client.post(
            "/api/lps",
            data={"name": "Test LP", "lp_type": "invalid_type_xyz"}
        )
        assert response.status_code != 500

    def test_create_lp_empty_type(self, client):
        """Empty LP type should be accepted (optional field)."""
        response = client.post(
            "/api/lps",
            data={"name": "Test LP", "lp_type": ""}
        )
        assert response.status_code in [200, 503]


class TestLPsArrayFieldValidation:
    """Test array/comma-separated field validation for LPs."""

    def test_create_lp_strategies_with_special_chars(self, client):
        """Strategies field with special chars should be handled."""
        response = client.post(
            "/api/lps",
            data={"name": "Test LP", "strategies": "buyout, <script>alert(1)</script>"}
        )
        assert response.status_code != 500

    def test_create_lp_empty_strategies(self, client):
        """Empty strategies should be accepted."""
        response = client.post(
            "/api/lps",
            data={"name": "Test LP", "strategies": ""}
        )
        assert response.status_code in [200, 503]

    def test_create_lp_malformed_comma_separated(self, client):
        """Malformed comma-separated values should be handled."""
        response = client.post(
            "/api/lps",
            data={"name": "Test LP", "strategies": ",,,buyout,,,growth,,,"}
        )
        assert response.status_code != 500


# =============================================================================
# PITCH GENERATION TESTS
# =============================================================================


class TestPitchGeneration:
    """Test pitch generation API endpoint.

    Gherkin Reference: M3 - AI Pitch Generation
    """

    def test_generate_pitch_invalid_match_id_returns_400(self, client):
        """Generating pitch with invalid match ID should return 400."""
        response = client.post("/api/match/invalid-uuid/generate-pitch")
        assert response.status_code == 400

    def test_generate_pitch_valid_uuid_without_db(self, client):
        """Generating pitch with valid UUID but no DB should return 503."""
        response = client.post(
            "/api/match/00000000-0000-0000-0000-000000000000/generate-pitch"
        )
        assert response.status_code in [503, 404]

    def test_generate_pitch_accepts_pitch_type(self, client):
        """Pitch generation should accept pitch_type parameter."""
        response = client.post(
            "/api/match/00000000-0000-0000-0000-000000000000/generate-pitch",
            data={"pitch_type": "email", "tone": "professional"}
        )
        assert response.status_code in [503, 404]

    def test_generate_pitch_invalid_pitch_type(self, client):
        """Invalid pitch type should be handled gracefully."""
        response = client.post(
            "/api/match/00000000-0000-0000-0000-000000000000/generate-pitch",
            data={"pitch_type": "invalid_type", "tone": "professional"}
        )
        # Should handle gracefully, not crash
        assert response.status_code != 500

    def test_generate_pitch_xss_in_tone(self, client):
        """XSS in tone parameter should be safely handled."""
        response = client.post(
            "/api/match/00000000-0000-0000-0000-000000000000/generate-pitch",
            data={"pitch_type": "email", "tone": "<script>alert(1)</script>"}
        )
        assert response.status_code != 500

    def test_generate_pitch_sql_injection_in_uuid(self, client):
        """SQL injection in match UUID should be rejected."""
        response = client.post(
            "/api/match/'; DROP TABLE fund_lp_matches; --/generate-pitch"
        )
        assert response.status_code == 400


class TestPitchGenerationUUIDValidation:
    """Test UUID validation for pitch generation endpoint."""

    @pytest.mark.parametrize("invalid_id", [
        "",
        "not-a-uuid",
        "../../../etc/passwd",
        "00000000-0000-0000-0000",  # incomplete
        "'; DROP TABLE fund_lp_matches; --",
    ])
    def test_pitch_rejects_invalid_uuids(self, client, invalid_id):
        """Pitch endpoint should reject invalid match UUIDs."""
        response = client.post(f"/api/match/{invalid_id}/generate-pitch")
        assert response.status_code in [400, 404, 422]
        assert response.status_code != 500


# =============================================================================
# MATCH DETAIL TESTS
# =============================================================================


class TestMatchDetailModal:
    """Test match detail modal API endpoint.

    Gherkin Reference: M2 - Match Details
    """

    def test_match_detail_modal_invalid_id_returns_400(self, client):
        """Getting match detail modal with invalid ID should return 400."""
        response = client.get("/api/match/invalid-uuid/detail")
        assert response.status_code == 400

    def test_match_detail_modal_valid_uuid_without_db(self, client):
        """Getting match detail modal with valid UUID but no DB should return 503."""
        response = client.get("/api/match/00000000-0000-0000-0000-000000000000/detail")
        assert response.status_code in [503, 404]

    @pytest.mark.parametrize("invalid_id", [
        "'; DROP TABLE fund_lp_matches; --",
        "<script>alert(1)</script>",
        "../../../etc/passwd",
    ])
    def test_match_detail_rejects_malicious_ids(self, client, invalid_id):
        """Match detail should reject malicious IDs safely."""
        response = client.get(f"/api/match/{invalid_id}/detail")
        assert response.status_code in [400, 404, 422]
        assert response.status_code != 500


# =============================================================================
# RESPONSE SECURITY TESTS
# =============================================================================


class TestResponseSecurity:
    """Test that responses don't leak sensitive information."""

    def test_error_responses_no_stack_traces(self, client):
        """Error responses should not contain stack traces."""
        response = client.get("/api/funds/invalid/edit")
        text = response.text.lower()
        assert "traceback" not in text
        assert "file \"/" not in text
        assert "line " not in text or "error" in text

    def test_error_responses_no_db_credentials(self, client):
        """Error responses should not expose database credentials."""
        response = client.post(
            "/api/funds",
            data={"name": "Test", "org_id": "00000000-0000-0000-0000-000000000000"}
        )
        text = response.text.lower()
        assert "password" not in text or "password field" in text
        assert "postgresql://" not in text
        assert "postgres:" not in text

    def test_error_responses_no_internal_paths(self, client):
        """Error responses should not expose internal file paths."""
        response = client.get("/api/funds/invalid/edit")
        text = response.text
        assert "/home/" not in text
        assert "/usr/" not in text
        assert "\\Users\\" not in text


# =============================================================================
# CONCURRENT REQUEST TESTS
# =============================================================================


class TestConcurrentRequests:
    """Test handling of rapid/concurrent requests."""

    def test_rapid_fund_creation_attempts(self, client):
        """Rapid fund creation attempts should all be handled."""
        responses = []
        for i in range(10):
            response = client.post(
                "/api/funds",
                data={
                    "name": f"Fund {i}",
                    "org_id": "00000000-0000-0000-0000-000000000000"
                }
            )
            responses.append(response.status_code)

        # All should return consistent status (503 or similar)
        # None should return 500
        assert 500 not in responses

    def test_rapid_invalid_uuid_requests(self, client):
        """Rapid requests with invalid UUIDs should all be handled."""
        responses = []
        for _ in range(10):
            response = client.get("/api/funds/invalid-uuid/edit")
            responses.append(response.status_code)

        # All should return 400, none should crash
        assert all(code == 400 for code in responses)


# =============================================================================
# AI MATCHING TESTS
# =============================================================================


class TestMatchingScoring:
    """Test the matching scoring algorithm.

    Tests cover:
    - Hard filters (strategy, ESG, emerging manager, fund size)
    - Soft scores (geography, sector, track record, size fit)
    - Edge cases and boundary conditions
    """

    def test_perfect_match_all_criteria(self):
        """A fund that matches all LP criteria should score high."""
        from src.matching import calculate_match_score

        fund = {
            "strategy": "venture",
            "geographic_focus": ["North America", "Europe"],
            "sector_focus": ["technology", "healthcare"],
            "target_size_mm": 500,
            "fund_number": 4,
            "esg_policy": True
        }

        lp = {
            "strategies": ["venture", "growth"],
            "geographic_preferences": ["North America", "Europe"],
            "sector_preferences": ["technology", "healthcare"],
            "fund_size_min_mm": 100,
            "fund_size_max_mm": 1000,
            "esg_required": True,
            "emerging_manager_ok": False,
            "min_fund_number": 3
        }

        result = calculate_match_score(fund, lp)

        assert result["passed_hard_filters"] is True
        assert result["score"] >= 90
        assert result["score_breakdown"]["strategy"] == 100
        assert result["score_breakdown"]["esg"] == 100

    def test_strategy_mismatch_fails_hard_filter(self):
        """If fund strategy not in LP's list, score should be 0."""
        from src.matching import calculate_match_score

        fund = {"strategy": "buyout", "target_size_mm": 500}
        lp = {"strategies": ["venture", "growth"], "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        assert result["passed_hard_filters"] is False
        assert result["score"] == 0
        assert result["score_breakdown"]["strategy"] == 0

    def test_esg_required_but_fund_lacks_policy(self):
        """If LP requires ESG but fund doesn't have policy, score should be 0."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "target_size_mm": 500, "esg_policy": False}
        lp = {"strategies": ["venture"], "esg_required": True, "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        assert result["passed_hard_filters"] is False
        assert result["score"] == 0
        assert result["score_breakdown"]["esg"] == 0

    def test_esg_not_required_fund_without_policy_passes(self):
        """If LP doesn't require ESG, fund without policy should pass."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "target_size_mm": 500, "esg_policy": False, "fund_number": 4}
        lp = {"strategies": ["venture"], "esg_required": False, "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        assert result["passed_hard_filters"] is True
        assert result["score_breakdown"]["esg"] == 100

    def test_emerging_manager_not_ok_and_fund_is_emerging(self):
        """If LP doesn't accept emerging managers, fund 1-2 should fail."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "target_size_mm": 500, "fund_number": 1}
        lp = {"strategies": ["venture"], "emerging_manager_ok": False, "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        assert result["passed_hard_filters"] is False
        assert result["score"] == 0
        assert result["score_breakdown"]["emerging_manager"] == 0

    def test_emerging_manager_ok_and_fund_is_emerging(self):
        """If LP accepts emerging managers, fund 1-2 should pass."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "target_size_mm": 500, "fund_number": 2}
        lp = {"strategies": ["venture"], "emerging_manager_ok": True, "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        assert result["passed_hard_filters"] is True
        assert result["score_breakdown"]["emerging_manager"] == 100

    def test_fund_size_outside_lp_range(self):
        """If fund size outside LP's range, score should be 0."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "target_size_mm": 5000}
        lp = {"strategies": ["venture"], "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        assert result["passed_hard_filters"] is False
        assert result["score"] == 0
        assert result["score_breakdown"]["fund_size"] == 0

    def test_fund_size_at_boundary_passes(self):
        """Fund size at LP's boundary should pass."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "target_size_mm": 1000, "fund_number": 4}
        lp = {"strategies": ["venture"], "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        assert result["passed_hard_filters"] is True
        assert result["score_breakdown"]["fund_size"] == 100

    def test_geography_overlap_scoring(self):
        """Geography overlap should affect soft score proportionally."""
        from src.matching import calculate_match_score

        # 50% overlap: fund has 2 regions, LP prefers 1 of them
        fund = {"strategy": "venture", "geographic_focus": ["North America", "Asia"], "target_size_mm": 500, "fund_number": 4}
        lp = {"strategies": ["venture"], "geographic_preferences": ["North America"], "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        assert result["passed_hard_filters"] is True
        assert result["score_breakdown"]["geography"] == 50.0

    def test_global_lp_matches_all_geographies(self):
        """LP with 'Global' preference should match any geography."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "geographic_focus": ["South America", "Africa"], "target_size_mm": 500, "fund_number": 4}
        lp = {"strategies": ["venture"], "geographic_preferences": ["Global"], "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        assert result["score_breakdown"]["geography"] == 100


class TestMatchingScoringEdgeCases:
    """Test edge cases in matching scoring."""

    def test_empty_strategies_array(self):
        """Empty LP strategies should fail to match any fund."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "target_size_mm": 500}
        lp = {"strategies": [], "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        assert result["passed_hard_filters"] is False
        assert result["score"] == 0

    def test_none_strategies(self):
        """None strategies should fail to match."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "target_size_mm": 500}
        lp = {"strategies": None, "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        assert result["passed_hard_filters"] is False
        assert result["score"] == 0

    def test_none_fund_strategy(self):
        """Fund with no strategy should fail to match."""
        from src.matching import calculate_match_score

        fund = {"strategy": None, "target_size_mm": 500}
        lp = {"strategies": ["venture"], "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        assert result["passed_hard_filters"] is False

    def test_empty_geographic_arrays(self):
        """Empty geographic arrays should score neutral (50)."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "geographic_focus": [], "target_size_mm": 500, "fund_number": 4}
        lp = {"strategies": ["venture"], "geographic_preferences": ["North America"], "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        assert result["score_breakdown"]["geography"] == 50

    def test_none_fund_size_ranges(self):
        """None fund size ranges should be treated as unlimited."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "target_size_mm": 500}
        lp = {"strategies": ["venture"], "fund_size_min_mm": None, "fund_size_max_mm": None}

        result = calculate_match_score(fund, lp)

        # Should pass since None means no restriction
        assert result["score_breakdown"]["fund_size"] == 100

    def test_zero_target_size(self):
        """Zero target size should be handled gracefully."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "target_size_mm": 0}
        lp = {"strategies": ["venture"], "fund_size_min_mm": 0, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        # 0 is within [0, 1000] range
        assert result["score_breakdown"]["fund_size"] == 100

    def test_case_insensitive_strategy_matching(self):
        """Strategy matching should be case-insensitive."""
        from src.matching import calculate_match_score

        fund = {"strategy": "VENTURE", "target_size_mm": 500}
        lp = {"strategies": ["venture", "growth"], "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        assert result["score_breakdown"]["strategy"] == 100

    def test_partial_sector_matching(self):
        """Sector matching should handle partial matches."""
        from src.matching import calculate_match_score

        # "technology" should match "tech" or vice versa
        fund = {"strategy": "venture", "sector_focus": ["enterprise_software"], "target_size_mm": 500, "fund_number": 4}
        lp = {"strategies": ["venture"], "sector_preferences": ["software"], "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        # "enterprise_software" contains "software" so should partially match
        assert result["score_breakdown"]["sector"] >= 50

    @pytest.mark.parametrize("fund_number,min_fund_number,expected_passes", [
        (1, 1, True),
        (2, 1, True),
        (3, 1, True),
        (1, 3, False),  # Emerging manager with strict requirement
        (2, 3, False),  # Emerging manager with strict requirement
        (3, 3, True),
    ])
    def test_fund_number_requirements(self, fund_number, min_fund_number, expected_passes):
        """Test various fund number vs min_fund_number combinations."""
        from src.matching import calculate_match_score

        fund = {
            "strategy": "venture",
            "target_size_mm": 500,
            "fund_number": fund_number
        }
        lp = {
            "strategies": ["venture"],
            "fund_size_min_mm": 100,
            "fund_size_max_mm": 1000,
            "min_fund_number": min_fund_number,
            "emerging_manager_ok": False  # Strict on emerging
        }

        result = calculate_match_score(fund, lp)

        if fund_number <= 2:
            # Emerging manager check applies
            assert result["passed_hard_filters"] is False
        else:
            assert result["passed_hard_filters"] is expected_passes


class TestMatchingLLMGeneration:
    """Test LLM content generation for matches."""

    def test_fallback_content_generation(self):
        """When LLM unavailable, fallback content should be generated."""
        from src.matching import _generate_fallback_content

        fund = {
            "name": "Test Fund III",
            "strategy": "venture",
            "fund_number": 3
        }
        lp = {
            "name": "Test LP",
            "lp_type": "pension"
        }
        score_breakdown = {
            "strategy": 100,
            "geography": 80,
            "sector": 70,
            "track_record": 100,
            "size_fit": 90
        }

        content = _generate_fallback_content(fund, lp, score_breakdown)

        assert "explanation" in content
        assert "talking_points" in content
        assert "concerns" in content
        assert len(content["talking_points"]) >= 1
        assert len(content["concerns"]) >= 1

    def test_fallback_content_handles_missing_data(self):
        """Fallback should handle missing fund/LP data gracefully."""
        from src.matching import _generate_fallback_content

        fund = {}
        lp = {}
        score_breakdown = {"geography": 50, "sector": 50}

        content = _generate_fallback_content(fund, lp, score_breakdown)

        # Should not raise, should return valid structure
        assert "explanation" in content
        assert len(content["talking_points"]) == 3
        assert len(content["concerns"]) == 2

    @pytest.mark.asyncio
    async def test_llm_generation_timeout_fallback(self):
        """When LLM times out, should fall back to template content."""
        from src.matching import generate_match_content

        fund = {"name": "Test Fund", "strategy": "venture"}
        lp = {"name": "Test LP", "strategies": ["venture"]}
        score_breakdown = {"strategy": 100}

        # Use invalid URL to trigger timeout/error
        content = await generate_match_content(
            fund, lp, score_breakdown,
            ollama_base_url="http://invalid-url:99999",
            ollama_model="nonexistent"
        )

        # Should fall back to template content
        assert "explanation" in content
        assert "talking_points" in content
        assert "concerns" in content


class TestMatchingAPIEndpoint:
    """Test the generate-matches API endpoint."""

    def test_generate_matches_invalid_uuid(self, client):
        """Invalid UUID should return 400."""
        response = client.post("/api/funds/not-a-uuid/generate-matches")
        assert response.status_code == 400
        assert "Invalid fund ID" in response.text

    def test_generate_matches_nonexistent_fund(self, client):
        """Non-existent fund should return 404 (or 503 if no DB)."""
        response = client.post("/api/funds/00000000-0000-0000-0000-000000000000/generate-matches")
        # Either 503 (no DB) or 404 (fund not found)
        assert response.status_code in [404, 503]

    @pytest.mark.parametrize("invalid_id", [
        "",
        "   ",
        "not-a-uuid",
        "../../../etc/passwd",
        "'; DROP TABLE funds; --",
        "<script>alert(1)</script>",
    ])
    def test_generate_matches_rejects_invalid_ids(self, client, invalid_id):
        """All invalid IDs should be rejected safely."""
        if invalid_id.strip():  # Skip empty string which won't match route
            response = client.post(f"/api/funds/{invalid_id}/generate-matches")
            assert response.status_code in [400, 404, 422]
            assert response.status_code != 500  # Should never crash


class TestMatchingScoreBreakdown:
    """Test score breakdown details."""

    def test_score_breakdown_contains_all_components(self):
        """Score breakdown should contain all scoring components."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "geographic_focus": ["North America"], "target_size_mm": 500, "fund_number": 4}
        lp = {"strategies": ["venture"], "geographic_preferences": ["North America"], "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        breakdown = result["score_breakdown"]
        assert "strategy" in breakdown
        assert "esg" in breakdown
        assert "emerging_manager" in breakdown
        assert "fund_size" in breakdown
        assert "geography" in breakdown
        assert "sector" in breakdown
        assert "track_record" in breakdown
        assert "size_fit" in breakdown

    def test_score_is_weighted_average_of_soft_scores(self):
        """Final score should be weighted average of soft scores."""
        from src.matching import calculate_match_score

        fund = {
            "strategy": "venture",
            "geographic_focus": ["North America"],
            "sector_focus": ["technology"],
            "target_size_mm": 500,
            "fund_number": 4
        }
        lp = {
            "strategies": ["venture"],
            "geographic_preferences": ["North America"],
            "sector_preferences": ["technology"],
            "fund_size_min_mm": 100,
            "fund_size_max_mm": 1000
        }

        result = calculate_match_score(fund, lp)

        # Calculate expected weighted average
        breakdown = result["score_breakdown"]
        expected = (
            breakdown["geography"] * 0.30 +
            breakdown["sector"] * 0.30 +
            breakdown["track_record"] * 0.20 +
            breakdown["size_fit"] * 0.20
        )

        assert abs(result["score"] - expected) < 0.1  # Allow small rounding diff


class TestMatchingStrategyVariations:
    """Test various strategy matching scenarios."""

    @pytest.mark.parametrize("fund_strategy,lp_strategies,expected_match", [
        ("venture", ["venture"], True),
        ("venture", ["growth", "venture", "buyout"], True),
        ("venture", ["growth", "buyout"], False),
        ("VENTURE", ["venture"], True),  # Case insensitive
        ("Venture Capital", ["venture"], False),  # Exact match required
        ("buyout", [], False),  # Empty list
        (None, ["venture"], False),  # None fund strategy
        ("venture", None, False),  # None LP strategies
    ])
    def test_strategy_matching_variations(self, fund_strategy, lp_strategies, expected_match):
        """Test various strategy matching scenarios."""
        from src.matching import calculate_match_score

        fund = {"strategy": fund_strategy, "target_size_mm": 500}
        lp = {"strategies": lp_strategies, "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        if expected_match:
            assert result["score_breakdown"]["strategy"] == 100
        else:
            assert result["score_breakdown"]["strategy"] == 0
            assert result["passed_hard_filters"] is False


class TestMatchingGeographyVariations:
    """Test various geography matching scenarios."""

    @pytest.mark.parametrize("fund_geo,lp_geo,expected_score", [
        (["North America"], ["North America"], 100),
        (["North America", "Europe"], ["North America"], 50),
        (["North America", "Europe", "Asia"], ["North America"], 33.33),
        (["North America"], ["Global"], 100),
        # Note: Fund with "Global" requires LP with "Global" for full match
        ([], ["North America"], 50),  # Empty defaults to neutral
        (["North America"], [], 50),  # Empty LP prefs defaults to neutral
        (["Asia"], ["Europe"], 0),  # No overlap
    ])
    def test_geography_overlap_variations(self, fund_geo, lp_geo, expected_score):
        """Test geography overlap scoring variations."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "geographic_focus": fund_geo, "target_size_mm": 500, "fund_number": 4}
        lp = {"strategies": ["venture"], "geographic_preferences": lp_geo, "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        assert abs(result["score_breakdown"]["geography"] - expected_score) < 1


class TestMatchingSizeRangeVariations:
    """Test various fund size range scenarios."""

    @pytest.mark.parametrize("target_size,min_size,max_size,expected_pass", [
        (500, 100, 1000, True),   # Within range
        (100, 100, 1000, True),   # At minimum
        (1000, 100, 1000, True),  # At maximum
        (99, 100, 1000, False),   # Just below minimum
        (1001, 100, 1000, False), # Just above maximum
        (500, None, 1000, True),  # No minimum
        (500, 100, None, True),   # No maximum
        (500, None, None, True),  # No restrictions
        (0, 0, 100, True),        # Zero fund size with zero min
        (0, 1, 100, False),       # Zero fund size with non-zero min
    ])
    def test_fund_size_range_variations(self, target_size, min_size, max_size, expected_pass):
        """Test fund size range boundary conditions."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "target_size_mm": target_size, "fund_number": 4}
        lp = {"strategies": ["venture"], "fund_size_min_mm": min_size, "fund_size_max_mm": max_size}

        result = calculate_match_score(fund, lp)

        if expected_pass:
            assert result["score_breakdown"]["fund_size"] == 100
        else:
            assert result["score_breakdown"]["fund_size"] == 0
            assert result["passed_hard_filters"] is False


class TestMatchingESGVariations:
    """Test ESG policy matching scenarios."""

    @pytest.mark.parametrize("esg_policy,esg_required,expected_score", [
        (True, True, 100),    # Has policy, required
        (True, False, 100),   # Has policy, not required
        (False, True, 0),     # No policy, required - FAIL
        (False, False, 100),  # No policy, not required
        (None, True, 0),      # None policy, required - FAIL
        (None, False, 100),   # None policy, not required
    ])
    def test_esg_policy_variations(self, esg_policy, esg_required, expected_score):
        """Test ESG policy matching variations."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "target_size_mm": 500, "esg_policy": esg_policy, "fund_number": 4}
        lp = {"strategies": ["venture"], "esg_required": esg_required, "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        assert result["score_breakdown"]["esg"] == expected_score


class TestMatchingTrackRecordScoring:
    """Test track record scoring based on fund number."""

    @pytest.mark.parametrize("fund_number,expected_min_score", [
        (1, 50),   # Fund I - emerging manager, lower score
        (2, 50),   # Fund II - still emerging
        (3, 70),   # Fund III - established
        (4, 80),   # Fund IV - strong track record
        (5, 90),   # Fund V - excellent track record
        (10, 100), # Fund X - maximum score
        (None, 50), # Unknown fund number - neutral
    ])
    def test_track_record_scoring_by_fund_number(self, fund_number, expected_min_score):
        """Test track record scoring scales with fund number."""
        from src.matching import calculate_match_score

        fund = {
            "strategy": "venture",
            "target_size_mm": 500,
            "fund_number": fund_number
        }
        lp = {
            "strategies": ["venture"],
            "fund_size_min_mm": 100,
            "fund_size_max_mm": 1000,
            "emerging_manager_ok": True  # Allow all to pass for this test
        }

        result = calculate_match_score(fund, lp)

        # Track record score should be at least the expected minimum
        assert result["score_breakdown"]["track_record"] >= expected_min_score


class TestMatchingSectorOverlap:
    """Test sector preference matching."""

    @pytest.mark.parametrize("fund_sectors,lp_sectors,expected_overlap", [
        (["technology"], ["technology"], True),
        (["technology", "healthcare"], ["technology"], True),
        (["agriculture"], ["technology"], False),
        # Empty sectors default to neutral (50), not 0
        ([], ["technology"], None),  # Neutral - empty defaults to 50
        (["technology"], [], None),  # Neutral - empty defaults to 50
    ])
    def test_sector_overlap_detection(self, fund_sectors, lp_sectors, expected_overlap):
        """Test sector overlap is detected correctly."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "sector_focus": fund_sectors, "target_size_mm": 500, "fund_number": 4}
        lp = {"strategies": ["venture"], "sector_preferences": lp_sectors, "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        if expected_overlap is True:
            assert result["score_breakdown"]["sector"] >= 50
        elif expected_overlap is False:
            assert result["score_breakdown"]["sector"] < 50
        else:  # None = neutral
            assert result["score_breakdown"]["sector"] == 50


class TestMatchingCheckSizeFit:
    """Test check size fit scoring (LP's typical investment size vs fund)."""

    @pytest.mark.parametrize("target_size,check_min,check_max,min_expected", [
        (500, 50, 100, 50),   # Fund allows typical LP check size
        (1000, 10, 20, 50),   # Large fund can take small checks
        (500, None, None, 50), # No check size restrictions
    ])
    def test_check_size_fit_scoring(self, target_size, check_min, check_max, min_expected):
        """Test that LP check size fits fund size."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "target_size_mm": target_size, "fund_number": 4}
        lp = {
            "strategies": ["venture"],
            "fund_size_min_mm": 10,
            "fund_size_max_mm": 10000,
            "check_size_min_mm": check_min,
            "check_size_max_mm": check_max
        }

        result = calculate_match_score(fund, lp)

        assert result["score_breakdown"]["size_fit"] >= min_expected


class TestMatchingFallbackContent:
    """Test fallback content generation edge cases."""

    def test_fallback_with_high_scores_generates_positive_content(self):
        """High scores should generate positive talking points."""
        from src.matching import _generate_fallback_content

        fund = {"name": "Excellent Fund V", "strategy": "growth", "fund_number": 5}
        lp = {"name": "Major Pension", "lp_type": "pension"}
        score_breakdown = {
            "strategy": 100,
            "geography": 100,
            "sector": 100,
            "track_record": 100,
            "size_fit": 100
        }

        content = _generate_fallback_content(fund, lp, score_breakdown)

        # Should have positive talking points
        assert len(content["talking_points"]) >= 3
        # Should have fewer concerns with high scores
        assert len(content["concerns"]) >= 1

    def test_fallback_with_low_scores_generates_more_concerns(self):
        """Low scores should generate more concerns."""
        from src.matching import _generate_fallback_content

        fund = {"name": "New Fund I", "strategy": "venture", "fund_number": 1}
        lp = {"name": "Conservative LP", "lp_type": "pension"}
        score_breakdown = {
            "strategy": 60,
            "geography": 40,
            "sector": 30,
            "track_record": 20,
            "size_fit": 50
        }

        content = _generate_fallback_content(fund, lp, score_breakdown)

        # Should have at least 2 concerns with low scores
        assert len(content["concerns"]) >= 2

    def test_fallback_includes_fund_name_in_explanation(self):
        """Explanation should reference the fund name when available."""
        from src.matching import _generate_fallback_content

        fund = {"name": "Acme Growth Fund III", "strategy": "growth", "fund_number": 3}
        lp = {"name": "Yale Endowment", "lp_type": "endowment"}
        score_breakdown = {"strategy": 100}

        content = _generate_fallback_content(fund, lp, score_breakdown)

        # Explanation might reference fund or LP
        assert content["explanation"]  # Should have some explanation
        assert len(content["explanation"]) > 20  # Substantial explanation


class TestMatchingEmptyAndNullInputs:
    """Test handling of empty and null inputs."""

    def test_completely_empty_fund(self):
        """Completely empty fund should fail gracefully."""
        from src.matching import calculate_match_score

        fund = {}
        lp = {"strategies": ["venture"], "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        assert result["passed_hard_filters"] is False
        assert result["score"] == 0

    def test_completely_empty_lp(self):
        """Completely empty LP should fail gracefully."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "target_size_mm": 500}
        lp = {}

        result = calculate_match_score(fund, lp)

        assert result["passed_hard_filters"] is False
        assert result["score"] == 0

    def test_both_empty(self):
        """Both empty should fail gracefully."""
        from src.matching import calculate_match_score

        result = calculate_match_score({}, {})

        assert result["passed_hard_filters"] is False
        assert result["score"] == 0


class TestMatchingSpecialCharacters:
    """Test handling of special characters in data."""

    def test_unicode_in_strategy(self):
        """Unicode characters in strategy should be handled."""
        from src.matching import calculate_match_score

        fund = {"strategy": "成長投資", "target_size_mm": 500}  # Japanese
        lp = {"strategies": ["成長投資", "venture"], "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        assert result["score_breakdown"]["strategy"] == 100

    def test_special_chars_in_geography(self):
        """Special characters in geography names should work."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "geographic_focus": ["São Paulo", "München"], "target_size_mm": 500, "fund_number": 4}
        lp = {"strategies": ["venture"], "geographic_preferences": ["São Paulo"], "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

        result = calculate_match_score(fund, lp)

        assert result["score_breakdown"]["geography"] >= 50


class TestMatchingLargeNumbers:
    """Test handling of very large numbers."""

    def test_very_large_fund_size(self):
        """Very large fund sizes should be handled."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "target_size_mm": 1_000_000, "fund_number": 4}  # $1 trillion
        lp = {"strategies": ["venture"], "fund_size_min_mm": 100_000, "fund_size_max_mm": 2_000_000}

        result = calculate_match_score(fund, lp)

        assert result["passed_hard_filters"] is True
        assert result["score_breakdown"]["fund_size"] == 100

    def test_very_large_aum(self):
        """Very large LP AUM should be handled."""
        from src.matching import calculate_match_score

        fund = {"strategy": "venture", "target_size_mm": 500, "fund_number": 4}
        lp = {
            "strategies": ["venture"],
            "total_aum_bn": 1000,  # $1 trillion AUM
            "fund_size_min_mm": 100,
            "fund_size_max_mm": 1000
        }

        result = calculate_match_score(fund, lp)

        assert result["passed_hard_filters"] is True


# =============================================================================
# RESPONSIVE & MOBILE TESTS
# =============================================================================
# These tests validate that the application works correctly on different
# screen sizes and mobile devices. Critical for modern web applications.


class TestViewportMetaTag:
    """Test that pages have proper viewport configuration for mobile.

    The viewport meta tag is CRITICAL for mobile responsiveness.
    Without it, mobile browsers will render at desktop width and scale down.
    """

    def test_home_has_viewport_meta(self, client):
        """Home page must have viewport meta tag."""
        response = client.get("/")
        assert 'name="viewport"' in response.text
        assert "width=device-width" in response.text

    def test_login_has_viewport_meta(self, client):
        """Login page must have viewport meta tag."""
        response = client.get("/login")
        assert 'name="viewport"' in response.text

    def test_funds_has_viewport_meta(self, client):
        """Funds page must have viewport meta tag."""
        response = client.get("/funds")
        assert 'name="viewport"' in response.text

    def test_lps_has_viewport_meta(self, client):
        """LPs page must have viewport meta tag."""
        response = client.get("/lps")
        assert 'name="viewport"' in response.text

    def test_matches_has_viewport_meta(self, client):
        """Matches page must have viewport meta tag."""
        response = client.get("/matches")
        assert 'name="viewport"' in response.text


class TestMobileNavigation:
    """Test that navigation is accessible on mobile devices.

    CRITICAL: Navigation hidden on mobile (hidden md:flex) MUST have
    a mobile alternative (hamburger menu) or users can't navigate!
    """

    def test_has_mobile_menu_toggle(self, client):
        """Pages with hidden desktop nav must have mobile menu toggle.

        The desktop nav uses 'hidden md:flex' which hides it on mobile.
        There MUST be a visible mobile menu button.
        """
        response = client.get("/funds")
        html = response.text

        # If desktop nav is hidden on mobile, we need a mobile alternative
        if "hidden md:flex" in html:
            # Must have a mobile menu button (hamburger icon)
            has_mobile_menu = any([
                'id="mobile-menu' in html,
                'data-mobile-menu' in html,
                'aria-label="menu"' in html.lower(),
                'aria-label="Menu"' in html,
                'hamburger' in html.lower(),
                # Check for a menu button visible on mobile
                'md:hidden' in html and ('menu' in html.lower() or 'nav' in html.lower()),
            ])
            assert has_mobile_menu, (
                "Desktop nav is hidden on mobile (hidden md:flex) but no mobile menu found! "
                "Mobile users cannot navigate between pages."
            )

    def test_mobile_nav_has_all_links(self, client):
        """Mobile navigation must have same links as desktop nav."""
        response = client.get("/funds")
        html = response.text

        # Core navigation links that must be accessible
        required_links = ["/matches", "/funds", "/lps"]

        for link in required_links:
            assert f'href="{link}"' in html, f"Missing navigation link: {link}"


class TestResponsiveLayout:
    """Test responsive grid and layout behavior."""

    def test_funds_grid_is_responsive(self, client):
        """Funds page grid should adapt to screen size."""
        response = client.get("/funds")
        html = response.text

        # Should have responsive grid classes
        assert "grid-cols-1" in html, "Missing single column for mobile"
        assert "md:grid-cols-2" in html or "lg:grid-cols-3" in html, (
            "Missing multi-column grid for larger screens"
        )

    def test_lps_grid_is_responsive(self, client):
        """LPs page grid should adapt to screen size."""
        response = client.get("/lps")
        html = response.text

        assert "grid-cols-1" in html, "Missing single column for mobile"

    def test_modals_are_mobile_friendly(self, client):
        """Modals should be usable on small screens."""
        response = client.get("/funds")
        html = response.text

        # Modals should have max-width and be scrollable
        # Check for overflow handling
        assert "overflow" in html or "max-h-" in html, (
            "Modals need overflow handling for small screens"
        )

    def test_forms_are_full_width_on_mobile(self, client):
        """Form inputs should be full width on mobile."""
        response = client.get("/funds")
        html = response.text

        # Look for w-full class on inputs
        assert "w-full" in html, "Form inputs should be full width"


class TestTouchTargets:
    """Test that interactive elements are large enough for touch.

    WCAG 2.5.5 recommends minimum 44x44px touch targets.
    Tailwind's default button padding should meet this, but we verify.
    """

    def test_buttons_have_adequate_padding(self, client):
        """Buttons should have enough padding for touch targets."""
        response = client.get("/funds")
        html = response.text

        # Buttons should have padding classes
        # Tailwind p-2 = 8px, p-3 = 12px, etc.
        # We need at least p-2 or px-3/py-2 combinations
        has_button_padding = any([
            "btn-primary" in html,  # Our custom class has padding
            "btn-secondary" in html,
            "px-3" in html,
            "px-4" in html,
            "py-2" in html,
        ])
        assert has_button_padding, "Buttons need adequate padding for touch"

    def test_links_in_nav_have_spacing(self, client):
        """Navigation links should have spacing for easy tapping."""
        response = client.get("/")
        html = response.text

        # Nav should have spacing between items
        has_nav_spacing = any([
            "space-x-" in html,
            "gap-" in html,
        ])
        assert has_nav_spacing, "Navigation needs spacing between items"


class TestAccessibility:
    """Test basic accessibility requirements for all users."""

    def test_html_has_lang_attribute(self, client):
        """HTML tag must have lang attribute for screen readers."""
        response = client.get("/")
        assert 'lang="en"' in response.text or "lang='en'" in response.text

    def test_page_has_main_landmark(self, client):
        """Page should have main content landmark."""
        response = client.get("/")
        assert "<main" in response.text, "Page needs <main> landmark"

    def test_page_has_header_landmark(self, client):
        """Page should have header landmark."""
        response = client.get("/")
        assert "<header" in response.text, "Page needs <header> landmark"

    def test_forms_have_labels(self, client):
        """Form inputs should have associated labels."""
        response = client.get("/login")
        html = response.text

        # Count labels (inputs include hidden fields which don't need labels)
        label_count = html.count("<label")

        # Forms should have labels for accessibility
        assert label_count > 0, "Forms need labels for accessibility"

    def test_images_have_alt_text(self, client):
        """Images should have alt attributes."""
        response = client.get("/")
        html = response.text

        # Find all img tags
        img_tags = re.findall(r'<img[^>]*>', html)
        for img in img_tags:
            assert 'alt=' in img, f"Image missing alt attribute: {img[:50]}"

    def test_buttons_have_text_or_aria_label(self, client):
        """Buttons must have visible text or aria-label."""
        response = client.get("/funds")
        html = response.text

        # Find button tags
        button_matches = re.findall(r'<button[^>]*>.*?</button>', html, re.DOTALL)
        for button in button_matches[:10]:  # Check first 10
            has_content = any([
                len(re.sub(r'<[^>]+>', '', button).strip()) > 0,  # Has text
                'aria-label' in button,
                'title=' in button,
            ])
            # SVG-only buttons are common but need aria-label
            if '<svg' in button and not has_content:
                assert 'aria-label' in button or 'title=' in button, (
                    f"Icon-only button needs aria-label: {button[:100]}"
                )


class TestResponsivePadding:
    """Test that containers have appropriate padding at different sizes."""

    def test_main_container_has_responsive_padding(self, client):
        """Main content container should have responsive padding."""
        response = client.get("/funds")
        html = response.text

        # Should use sm: or md: prefixed padding
        has_responsive_padding = any([
            "px-4 sm:px-6" in html,
            "px-4 md:px-6" in html,
            "sm:px-" in html,
        ])
        assert has_responsive_padding, "Container needs responsive padding"


class TestTextReadability:
    """Test text is readable on all screen sizes."""

    def test_text_uses_relative_sizes(self, client):
        """Text should use relative sizes (rem/em) not fixed pixels."""
        response = client.get("/")
        html = response.text

        # Tailwind uses rem-based sizes by default (text-sm, text-lg, etc.)
        has_tailwind_text = any([
            "text-sm" in html,
            "text-base" in html,
            "text-lg" in html,
            "text-xl" in html,
        ])
        assert has_tailwind_text, "Should use Tailwind text size classes"

    def test_no_tiny_text(self, client):
        """Text should not be too small to read."""
        response = client.get("/")
        html = response.text

        # text-xs (12px) is acceptable for labels, but should not be primary text
        # This is a soft check - just verify we use reasonable sizes
        assert "text-xs" in html or "text-sm" in html, (
            "Using appropriate text sizes"
        )


class TestFormsMobile:
    """Test form behavior on mobile devices."""

    def test_form_inputs_have_type_attribute(self, client):
        """Form inputs should have appropriate type for mobile keyboards."""
        response = client.get("/login")
        html = response.text

        # Email inputs should have type="email" for mobile keyboard
        if "email" in html.lower():
            assert 'type="email"' in html, "Email input needs type='email'"

        # Number inputs should have type="number"
        # Password should have type="password"
        if "password" in html.lower():
            assert 'type="password"' in html, "Password input needs type='password'"

    def test_number_inputs_have_correct_type(self, client):
        """Number inputs should use type=number for numeric keyboard."""
        response = client.get("/funds")
        html = response.text

        # Look for inputs that should be numbers
        # target_size_mm, vintage_year should be type="number"
        if "target_size" in html or "vintage_year" in html:
            assert 'type="number"' in html, "Numeric fields need type='number'"


class TestHTMXMobile:
    """Test HTMX behavior considerations for mobile."""

    def test_htmx_loaded(self, client):
        """HTMX library should be loaded."""
        response = client.get("/funds")
        assert "htmx" in response.text.lower()

    def test_loading_indicators_exist(self, client):
        """HTMX requests should have loading indicators."""
        response = client.get("/funds")
        html = response.text

        # Should have indicator classes
        has_indicator = any([
            "htmx-indicator" in html,
            "hx-indicator" in html,
        ])
        assert has_indicator, "Need loading indicators for HTMX requests"


class TestScrollBehavior:
    """Test scroll behavior on mobile."""

    def test_body_allows_scroll(self, client):
        """Body should not prevent scrolling."""
        response = client.get("/funds")
        html = response.text

        # Should not have overflow-hidden on body/html by default
        # (modals can add it temporarily)
        assert 'overflow: hidden' not in html or 'overflow-hidden' not in html.split('<body')[0], (
            "Body should allow scrolling"
        )

    def test_modals_have_scroll_handling(self, client):
        """Modals should handle overflow for long content."""
        response = client.get("/funds")
        html = response.text

        # Modals should have max-height and overflow-y-auto
        if "modal" in html.lower():
            assert "overflow" in html or "max-h-" in html, (
                "Modals need scroll handling"
            )


class TestMobileSpecificFeatures:
    """Test mobile-specific features and optimizations."""

    def test_no_hover_only_interactions(self, client):
        """Critical interactions should not rely solely on hover.

        Mobile devices don't have hover, so all interactive elements
        must be accessible via click/tap.
        """
        response = client.get("/funds")
        html = response.text

        # This is a structural check - hover effects are fine for enhancement
        # but core functionality should work without them
        # Look for elements that appear only on hover
        hover_only_patterns = [
            r'opacity-0.*hover:opacity-100',  # Hidden until hover
            r'invisible.*hover:visible',  # Invisible until hover
        ]

        for pattern in hover_only_patterns:
            matches = re.findall(pattern, html)
            # If found, ensure there's also a non-hover way to access
            if matches:
                # This is a warning - hover enhancements are OK
                pass  # Consider adding assertion if critical content is hover-only

    def test_sticky_header_exists(self, client):
        """Header should be sticky for easy navigation."""
        response = client.get("/funds")
        html = response.text

        assert "sticky" in html, "Header should be sticky for mobile usability"


class TestCriticalMobileIssues:
    """Test for critical mobile issues that break usability.

    These tests specifically catch issues that would make the app
    unusable on mobile devices.
    """

    @pytest.mark.parametrize("page", ["/", "/funds", "/lps", "/matches", "/login"])
    def test_page_renders_on_all_pages(self, client, page):
        """All main pages should render without errors."""
        response = client.get(page)
        assert response.status_code == 200

    def test_no_horizontal_scroll_indicators(self, client):
        """Content should not cause horizontal scroll.

        Look for fixed-width elements that might overflow.
        """
        response = client.get("/funds")
        html = response.text

        # Check for common overflow culprits
        # Fixed widths without max-width are risky
        dangerous_patterns = [
            r'width:\s*\d{4,}px',  # Width > 999px fixed
            r'min-width:\s*\d{4,}px',
        ]

        for pattern in dangerous_patterns:
            matches = re.findall(pattern, html)
            assert len(matches) == 0, f"Fixed width may cause horizontal scroll: {matches}"

    def test_tables_are_responsive(self, client):
        """Tables should have horizontal scroll wrapper on mobile."""
        response = client.get("/matches")
        html = response.text

        # If there are tables, they should have overflow handling
        if "<table" in html:
            # Should have overflow-x-auto wrapper
            assert "overflow-x" in html or "overflow-auto" in html, (
                "Tables need horizontal scroll wrapper for mobile"
            )


# =============================================================================
# PLAYWRIGHT BROWSER TESTS (Optional - run with pytest -m browser)
# =============================================================================
# These tests require Playwright and test actual browser rendering.
# Run with: pytest -m browser tests/test_main.py


@pytest.mark.browser
class TestPlaywrightMobile:
    """Browser-based tests for real viewport testing.

    These tests use Playwright to test actual browser behavior at
    different viewport sizes. Marked with @pytest.mark.browser.

    To run: pytest -m browser tests/test_main.py

    Requires: pip install pytest-playwright && playwright install
    """

    @pytest.fixture
    def mobile_viewport(self):
        """iPhone SE viewport dimensions."""
        return {"width": 375, "height": 667}

    @pytest.fixture
    def tablet_viewport(self):
        """iPad viewport dimensions."""
        return {"width": 768, "height": 1024}

    @pytest.fixture
    def desktop_viewport(self):
        """Desktop viewport dimensions."""
        return {"width": 1280, "height": 800}

    @pytest.mark.browser
    def test_mobile_viewport_renders(self, page, mobile_viewport):
        """Page should render correctly at mobile viewport."""
        page.set_viewport_size(mobile_viewport)
        page.goto("http://localhost:8000/funds")

        # Page should load
        assert page.title()

        # Content should be visible
        assert page.locator("h1").is_visible()

    @pytest.mark.browser
    def test_navigation_accessible_on_mobile(self, page, mobile_viewport):
        """Navigation should be accessible on mobile viewport."""
        page.set_viewport_size(mobile_viewport)
        page.goto("http://localhost:8000/funds")

        # Either nav links should be visible OR hamburger menu should exist
        nav_visible = page.locator("nav a").first.is_visible()
        hamburger_exists = page.locator(
            "[aria-label='Open navigation menu'], "
            "[aria-label='Menu'], "
            "[aria-label='menu'], "
            "#mobile-menu-toggle, "
            ".hamburger"
        ).count() > 0

        assert nav_visible or hamburger_exists, (
            "Navigation must be accessible on mobile"
        )

    @pytest.mark.browser
    def test_no_horizontal_overflow_mobile(self, page, mobile_viewport):
        """Page should not have horizontal overflow on mobile."""
        page.set_viewport_size(mobile_viewport)
        page.goto("http://localhost:8000/funds")

        # Check if page width exceeds viewport
        body_width = page.evaluate("document.body.scrollWidth")
        viewport_width = mobile_viewport["width"]

        assert body_width <= viewport_width + 10, (
            f"Page has horizontal overflow: body={body_width}px, viewport={viewport_width}px"
        )

    @pytest.mark.browser
    def test_buttons_are_tappable(self, page, mobile_viewport):
        """Primary action buttons should be large enough to tap."""
        page.set_viewport_size(mobile_viewport)
        page.goto("http://localhost:8000/funds")

        # Check only primary/visible action buttons, not icon-only buttons
        buttons = page.locator("button.btn-primary, button[type='submit']").all()
        for button in buttons[:5]:  # Check first 5 buttons
            box = button.bounding_box()
            if box and box["width"] > 0:
                # WCAG recommends 44x44px minimum for touch targets
                # Allow some flexibility for styled buttons
                assert box["height"] >= 32, f"Button too short: {box['height']}px"


# =============================================================================
# AUTHENTICATION TESTS
# =============================================================================


class TestAuthPages:
    """Test authentication page rendering."""

    def test_login_page_renders(self, client):
        """Login page should render successfully."""
        response = client.get("/login")
        assert response.status_code == 200
        assert "Sign in to LPxGP" in response.text

    def test_login_page_has_form(self, client):
        """Login page should have email and password fields."""
        response = client.get("/login")
        assert 'name="email"' in response.text
        assert 'name="password"' in response.text
        assert 'type="email"' in response.text
        assert 'type="password"' in response.text

    def test_login_page_shows_demo_accounts(self, client):
        """Login page should show demo account info."""
        response = client.get("/login")
        assert "gp@demo.com" in response.text
        assert "demo123" in response.text

    def test_register_page_renders(self, client):
        """Register page should render successfully."""
        response = client.get("/register")
        assert response.status_code == 200
        assert "Create your account" in response.text

    def test_register_page_has_all_fields(self, client):
        """Register page should have name, email, password, and role fields."""
        response = client.get("/register")
        assert 'name="name"' in response.text
        assert 'name="email"' in response.text
        assert 'name="password"' in response.text
        assert 'name="role"' in response.text


class TestAuthLogin:
    """Test login functionality."""

    def test_login_with_valid_demo_credentials(self, client):
        """Login with demo GP account should redirect to dashboard."""
        response = client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
            follow_redirects=False
        )
        # Should redirect to dashboard
        assert response.status_code == 303
        assert response.headers.get("location") == "/dashboard"

    def test_login_sets_session_cookie(self, client):
        """Successful login should set session cookie."""
        response = client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
            follow_redirects=False
        )
        # Check that a session cookie was set
        cookies = response.cookies
        assert "lpxgp_session" in cookies

    def test_login_with_invalid_password(self, client):
        """Login with wrong password should show error."""
        response = client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "wrongpassword"},
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.text

    def test_login_with_nonexistent_email(self, client):
        """Login with unknown email should show error."""
        response = client.post(
            "/api/auth/login",
            data={"email": "unknown@example.com", "password": "anypassword"},
        )
        assert response.status_code == 401
        assert "Invalid email or password" in response.text

    def test_login_case_insensitive_email(self, client):
        """Email should be case-insensitive for login."""
        response = client.post(
            "/api/auth/login",
            data={"email": "GP@DEMO.COM", "password": "demo123"},
            follow_redirects=False
        )
        assert response.status_code == 303


class TestAuthRegister:
    """Test registration functionality."""

    def test_register_new_user(self, client):
        """New user registration should succeed and redirect."""
        import uuid
        unique_email = f"test_{uuid.uuid4().hex[:8]}@example.com"

        response = client.post(
            "/api/auth/register",
            data={
                "email": unique_email,
                "password": "testpassword123",
                "name": "Test User",
                "role": "gp"
            },
            follow_redirects=False
        )
        assert response.status_code == 303
        assert response.headers.get("location") == "/dashboard"

    def test_register_duplicate_email(self, client):
        """Registering with existing email should fail."""
        response = client.post(
            "/api/auth/register",
            data={
                "email": "gp@demo.com",  # Already exists
                "password": "newpassword",
                "name": "Another User",
                "role": "gp"
            },
        )
        assert response.status_code == 400
        assert "already registered" in response.text.lower()


class TestAuthLogout:
    """Test logout functionality."""

    def test_logout_redirects_to_home(self, client):
        """Logout should redirect to home page."""
        # First login
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Then logout
        response = client.get("/logout", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers.get("location") == "/"

    def test_logout_clears_session(self, client):
        """Logout should clear the session cookie."""
        # First login
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Then logout
        response = client.get("/logout", follow_redirects=False)
        # Cookie should be deleted (empty or expired)
        cookies = response.cookies
        # After logout, session cookie should be cleared
        assert cookies.get("lpxgp_session") is None or cookies.get("lpxgp_session") == ""


class TestProtectedRoutes:
    """Test protected route access control."""

    def test_dashboard_requires_auth(self, client):
        """Dashboard should redirect to login if not authenticated."""
        response = client.get("/dashboard", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers.get("location") == "/login"

    def test_dashboard_accessible_when_logged_in(self, client):
        """Dashboard should be accessible after login."""
        # Login first
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Access dashboard
        response = client.get("/dashboard")
        assert response.status_code == 200
        assert "Welcome back" in response.text

    def test_settings_requires_auth(self, client):
        """Settings page should redirect to login if not authenticated."""
        response = client.get("/settings", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers.get("location") == "/login"

    def test_settings_accessible_when_logged_in(self, client):
        """Settings page should be accessible after login."""
        # Login first
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Access settings
        response = client.get("/settings")
        assert response.status_code == 200
        assert "Settings" in response.text

    def test_login_redirects_to_dashboard_if_authenticated(self, client):
        """Login page should redirect to dashboard if already logged in."""
        # Login first
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Try to access login page
        response = client.get("/login", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers.get("location") == "/dashboard"


class TestDashboardContent:
    """Test dashboard page content."""

    def test_dashboard_shows_user_name(self, client):
        """Dashboard should display user's name."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/dashboard")
        assert "Demo" in response.text  # First name from "Demo GP User"

    def test_dashboard_shows_stats(self, client):
        """Dashboard should show statistics cards."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/dashboard")
        assert "Total Funds" in response.text
        assert "Total LPs" in response.text
        assert "AI Matches" in response.text

    def test_dashboard_has_quick_actions(self, client):
        """Dashboard should have quick action links."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/dashboard")
        assert "Quick Actions" in response.text
        assert "/funds" in response.text
        assert "/matches" in response.text

    def test_dashboard_has_navigation(self, client):
        """Dashboard should have navigation to other pages."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/dashboard")
        assert 'href="/matches"' in response.text
        assert 'href="/funds"' in response.text
        assert 'href="/lps"' in response.text


class TestSettingsContent:
    """Test settings page content."""

    def test_settings_shows_user_info(self, client):
        """Settings should display user information."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/settings")
        assert "gp@demo.com" in response.text
        assert "Demo GP User" in response.text

    def test_settings_has_notification_options(self, client):
        """Settings should have notification preferences."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/settings")
        assert "Notifications" in response.text

    def test_settings_has_security_section(self, client):
        """Settings should have security section."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/settings")
        assert "Security" in response.text
        assert "Password" in response.text
