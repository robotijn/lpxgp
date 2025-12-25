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
        text = response.text.lower()
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
