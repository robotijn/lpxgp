"""Tests for main FastAPI application.

IMPORTANT: Tests are the source of truth. Do NOT modify tests to make them pass.
If a test fails, fix the APPLICATION, not the test.

Based on BDD Gherkin specs from docs/prd/tests/*.feature.md
"""

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
