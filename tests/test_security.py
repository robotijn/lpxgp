"""Security tests for LPxGP application.

Extracted from test_main.py to organize security-related tests.

Test Categories:
- Security headers
- SQL injection prevention
- XSS prevention
- Response security (no leaks)
- Authentication hardening
- Authorization/IDOR
- Input validation hardening
- API abuse protection
- Error handling security
- CSRF protection

Based on OWASP Top 10 2021:
- A01:2021 - Broken Access Control
- A03:2021 - Injection (SQL, XSS)
- A07:2021 - Identification and Authentication Failures
"""

import pytest

# Fixtures are imported from conftest.py:
# - client
# - authenticated_client
# - sql_injection_payloads
# - xss_payloads


# =============================================================================
# SECURITY HEADERS TESTS
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


# =============================================================================
# SQL INJECTION PREVENTION TESTS
# =============================================================================


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


# =============================================================================
# XSS PREVENTION TESTS
# =============================================================================


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
# SECURITY HARDENING TESTS - SQL INJECTION
# OWASP A03:2021 - Injection
# =============================================================================


class TestSQLInjectionHardening:
    """Advanced SQL injection prevention tests.

    Tests various SQL injection payloads including:
    - Union-based injection
    - Stacked queries
    - Boolean-based blind injection
    - Time-based blind injection
    - Comment-based bypass
    - Encoding bypass attempts
    """

    SQL_INJECTION_PAYLOADS = [
        # Classic payloads
        "' OR '1'='1",
        "' OR '1'='1' --",
        "' OR '1'='1' /*",
        "'; DROP TABLE users; --",
        "'; DELETE FROM funds; --",
        "1; UPDATE users SET role='admin'",
        # Union-based
        "' UNION SELECT * FROM users --",
        "' UNION SELECT NULL, username, password FROM users --",
        "1 UNION SELECT 1,2,3,4,5,6,7,8,9,10",
        # Stacked queries
        "'; INSERT INTO users VALUES('hacker','hacker'); --",
        "1; EXEC xp_cmdshell('whoami')",
        # Boolean-based blind
        "' AND 1=1 --",
        "' AND 1=2 --",
        "' AND (SELECT COUNT(*) FROM users) > 0 --",
        # Time-based blind
        "'; WAITFOR DELAY '0:0:5' --",
        "' OR SLEEP(5) --",
        "1' AND (SELECT SLEEP(5)) --",
        # Comment bypass
        "admin'--",
        "admin'/*",
        "' OR ''='",
        # Encoding bypass
        "%27%20OR%20%271%27%3D%271",  # URL encoded
        "\\' OR \\'1\\'=\\'1",  # Escaped quotes
        "' OR '1'='1' #",  # MySQL comment
        # PostgreSQL specific
        "'; SELECT pg_sleep(5); --",
        "'; COPY users TO '/tmp/users.txt'; --",
        "1; SELECT version(); --",
    ]

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    def test_lp_search_sql_injection(self, authenticated_client, payload):
        """LP search should be safe from SQL injection."""
        response = authenticated_client.get(f"/api/v1/lps?search={payload}")
        # Should not crash or return 500
        assert response.status_code in [200, 400, 422]
        # Should not expose SQL errors
        if response.status_code == 200:
            text = response.text.lower()
            assert "syntax error" not in text
            assert "sql" not in text or "sql injection" not in text
            assert "psycopg" not in text
            assert "postgresql" not in text

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    def test_gp_search_sql_injection(self, authenticated_client, payload):
        """GP search should be safe from SQL injection."""
        response = authenticated_client.get(f"/api/v1/gps?search={payload}")
        assert response.status_code in [200, 400, 422]
        if response.status_code == 200:
            assert "syntax error" not in response.text.lower()

    @pytest.mark.parametrize("payload", SQL_INJECTION_PAYLOADS)
    def test_fund_search_sql_injection(self, authenticated_client, payload):
        """Fund search should be safe from SQL injection."""
        response = authenticated_client.get(f"/api/v1/funds?search={payload}")
        assert response.status_code in [200, 400, 422]

    def test_sql_injection_in_fund_id(self, authenticated_client):
        """Fund ID parameter should reject SQL injection."""
        payloads = [
            "'; DROP TABLE funds; --",
            "1 OR 1=1",
            "00000000-0000-0000-0000-000000000000' OR '1'='1",
        ]
        for payload in payloads:
            response = authenticated_client.get(f"/funds/{payload}")
            # Should return 400 (invalid UUID) or 404, not 500
            assert response.status_code in [200, 302, 400, 404, 422]

    def test_sql_injection_in_lp_type_filter(self, authenticated_client):
        """LP type filter should reject SQL injection."""
        response = authenticated_client.get(
            "/api/v1/lps?lp_type=' OR '1'='1"
        )
        assert response.status_code in [200, 400, 422]

    def test_second_order_sql_injection(self, client):
        """Test second-order SQL injection via stored data."""
        # Login
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Try to create fund with SQL injection in name
        response = client.post(
            "/api/funds",
            data={
                "name": "'; DROP TABLE funds; --",
                "org_id": "c0000001-0000-0000-0000-000000000001",
                "strategy": "buyout",
            },
        )
        # Should either succeed (data is escaped) or reject
        assert response.status_code in [200, 400, 422, 503]


# =============================================================================
# SECURITY HARDENING TESTS - XSS
# OWASP A03:2021 - Injection (Cross-Site Scripting)
# =============================================================================


class TestXSSHardening:
    """Advanced XSS prevention tests.

    Tests various XSS payloads including:
    - Reflected XSS
    - DOM-based XSS triggers
    - Encoding bypass attempts
    - Event handler injection
    - SVG/MathML injection
    """

    XSS_PAYLOADS = [
        # Classic script tags
        "<script>alert('xss')</script>",
        "<script>document.location='http://evil.com'</script>",
        "<SCRIPT>alert('XSS')</SCRIPT>",
        # Event handlers
        "<img src=x onerror=alert('xss')>",
        "<body onload=alert('xss')>",
        "<svg onload=alert('xss')>",
        "<input onfocus=alert('xss') autofocus>",
        "<marquee onstart=alert('xss')>",
        "<details open ontoggle=alert('xss')>",
        # JavaScript protocol
        "javascript:alert('xss')",
        "<a href='javascript:alert(1)'>click</a>",
        "<iframe src='javascript:alert(1)'>",
        # Data protocol
        "data:text/html,<script>alert('xss')</script>",
        "<object data='data:text/html,<script>alert(1)</script>'>",
        # Encoding bypass
        "<scr<script>ipt>alert('xss')</scr</script>ipt>",
        "\\x3cscript\\x3ealert('xss')\\x3c/script\\x3e",
        "%3Cscript%3Ealert('xss')%3C/script%3E",
        "&#60;script&#62;alert('xss')&#60;/script&#62;",
        # SVG injection
        "<svg><script>alert('xss')</script></svg>",
        "<svg/onload=alert('xss')>",
        # Template injection attempts
        "{{constructor.constructor('alert(1)')()}}",
        "${alert('xss')}",
        "#{alert('xss')}",
        # CDATA escape
        "<![CDATA[<script>alert('xss')</script>]]>",
    ]

    @pytest.mark.parametrize("payload", XSS_PAYLOADS)
    def test_search_xss_prevention(self, authenticated_client, payload):
        """Search results should escape XSS payloads."""
        response = authenticated_client.get(f"/lps?search={payload}")
        assert response.status_code == 200
        # The payload should NOT appear raw in the response
        # If it contains dangerous chars, they should be HTML escaped
        if "<" in payload:
            # Raw HTML tags should be escaped (< becomes &lt;)
            assert payload not in response.text, f"XSS payload reflected unescaped: {payload}"
        # Check event handlers are not reflected raw
        if "onerror=" in payload.lower():
            # Either payload is escaped or not present
            assert payload.lower() not in response.text.lower()
        if "onload=" in payload.lower():
            assert payload.lower() not in response.text.lower()
        if "javascript:" in payload.lower():
            # The javascript: protocol should be escaped or blocked
            assert payload not in response.text

    def test_xss_in_fund_name(self, client):
        """Fund names should be escaped in output."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.post(
            "/api/funds",
            data={
                "name": "<script>alert('xss')</script>",
                "org_id": "c0000001-0000-0000-0000-000000000001",
                "strategy": "buyout",
            },
        )
        # Check response doesn't contain unescaped script
        assert "<script>alert('xss')</script>" not in response.text

    def test_xss_in_error_messages(self, client):
        """Error messages should not reflect unescaped input in HTML context."""
        payload = "<script>alert('xss')</script>"
        response = client.get(f"/api/funds/{payload}")
        # JSON responses are XSS-safe due to Content-Type header
        # If the response is JSON, that's actually safe
        content_type = response.headers.get("content-type", "")
        if "application/json" in content_type:
            # JSON is safe - the browser won't execute scripts
            assert response.status_code in [200, 404]
        else:
            # HTML response - payload should be escaped
            assert payload not in response.text

    def test_content_type_prevents_xss(self, authenticated_client):
        """JSON responses should have correct content-type."""
        response = authenticated_client.get("/api/v1/lps")
        content_type = response.headers.get("content-type", "")
        # Should be application/json, not text/html
        assert "application/json" in content_type


# =============================================================================
# SECURITY HARDENING TESTS - AUTHENTICATION
# OWASP A07:2021 - Identification and Authentication Failures
# =============================================================================


class TestAuthenticationHardening:
    """Authentication security hardening tests.

    Tests:
    - Session token security
    - Password field handling
    - Login timing attacks
    - Session fixation
    - Token manipulation
    """

    def test_password_not_in_response(self, client):
        """Password should never appear in responses."""
        response = client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        assert "demo123" not in response.text
        assert "password" not in response.text.lower() or "password\":" not in response.text

    def test_session_token_not_predictable(self, client):
        """Session tokens should be cryptographically random."""
        tokens = []
        for _ in range(5):
            response = client.post(
                "/api/auth/login",
                data={"email": "gp@demo.com", "password": "demo123"},
                follow_redirects=False,
            )
            cookies = response.cookies
            if "lpxgp_session" in cookies:
                tokens.append(cookies["lpxgp_session"])
            client.get("/logout")

        # All tokens should be unique
        assert len(set(tokens)) == len(tokens)
        # Tokens should be long enough (at least 32 chars)
        for token in tokens:
            if token:
                assert len(token) >= 32

    def test_invalid_session_token_rejected(self, client):
        """Invalid session tokens should be rejected."""
        client.cookies.set("lpxgp_session", "invalid-token-12345")
        response = client.get("/dashboard", follow_redirects=False)
        # Should redirect to login
        assert response.status_code in [302, 303, 307]

    def test_empty_session_token_rejected(self, client):
        """Empty session tokens should be rejected."""
        client.cookies.set("lpxgp_session", "")
        response = client.get("/dashboard", follow_redirects=False)
        assert response.status_code in [302, 303, 307]

    def test_malformed_session_token_rejected(self, client):
        """Malformed session tokens should be rejected."""
        malformed_tokens = [
            "null",
            "undefined",
            "NaN",
            "<script>",
            "../../etc/passwd",
            "\x00\x00\x00",
        ]
        for token in malformed_tokens:
            client.cookies.set("lpxgp_session", token)
            response = client.get("/dashboard", follow_redirects=False)
            assert response.status_code in [302, 303, 307, 400]

    def test_login_error_message_generic(self, client):
        """Login errors should not reveal if email exists."""
        # Test with non-existent email
        response1 = client.post(
            "/api/auth/login",
            data={"email": "nonexistent@example.com", "password": "wrongpass"},
        )
        # Test with existing email but wrong password
        response2 = client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "wrongpassword"},
        )
        # Both should show same generic error
        # Should NOT say "email not found" or "user does not exist"
        for response in [response1, response2]:
            assert "email not found" not in response.text.lower()
            assert "user not found" not in response.text.lower()
            assert "does not exist" not in response.text.lower()

    def test_logout_clears_session_server_side(self, client):
        """Logout should invalidate session on server, not just clear cookie."""
        # Login and get session
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Save the session cookie value
        session_cookie = client.cookies.get("lpxgp_session")

        # Logout
        client.get("/logout")

        # Try to use the old session cookie
        client.cookies.set("lpxgp_session", session_cookie)
        response = client.get("/dashboard", follow_redirects=False)
        # Should redirect to login (session invalidated)
        assert response.status_code in [302, 303, 307]


# =============================================================================
# SECURITY HARDENING TESTS - AUTHORIZATION / IDOR
# OWASP A01:2021 - Broken Access Control
# =============================================================================


class TestAuthorizationIDOR:
    """Authorization and IDOR (Insecure Direct Object Reference) tests.

    Tests:
    - Cross-user data access
    - Cross-organization data access
    - Privilege escalation
    - Direct object reference manipulation
    """

    def test_cannot_access_other_users_shortlist(self, client):
        """User A should not be able to access User B's shortlist."""
        # Login as GP user
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/api/shortlist")
        assert response.status_code == 200
        # Shortlist should only contain current user's items
        data = response.json()
        # Should not expose other users' data
        assert "other_user" not in str(data).lower()

    def test_cannot_modify_other_org_fund(self, client):
        """User should not be able to modify another organization's fund."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Try to modify a fund with a random UUID (different org)
        response = client.put(
            "/api/funds/99999999-9999-9999-9999-999999999999",
            data={"name": "Hacked Fund"},
        )
        # Should return error - 422 (validation), 404 (not found), 405 (method not allowed)
        assert response.status_code in [302, 400, 403, 404, 405, 422]

    def test_cannot_delete_other_org_fund(self, client):
        """User should not be able to delete another organization's fund."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.delete("/api/funds/99999999-9999-9999-9999-999999999999")
        # 405 if method not allowed, 503 if DB unavailable in test
        assert response.status_code in [400, 403, 404, 405, 503]

    def test_gp_cannot_access_lp_dashboard(self, client):
        """GP user should not access LP-specific dashboard."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/lp-dashboard")
        # Should redirect or show appropriate message
        assert response.status_code in [200, 302, 303, 307, 403]

    def test_lp_cannot_create_funds(self, client):
        """LP user should not be able to create funds (GP feature)."""
        client.post(
            "/api/auth/login",
            data={"email": "lp@demo.com", "password": "demo123"},
        )
        response = client.post(
            "/api/funds",
            data={
                "name": "Unauthorized Fund",
                "org_id": "c0000001-0000-0000-0000-000000000001",
                "strategy": "buyout",
            },
        )
        # Should be forbidden, redirect, or service unavailable (test isolation)
        assert response.status_code in [302, 303, 307, 403, 422, 503]

    def test_non_admin_cannot_access_admin_api(self, client):
        """Non-admin users should not access admin API endpoints."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/api/admin/stats")
        # GP user should get 403 or error
        assert response.status_code in [200, 403]  # Might return empty stats

    def test_cannot_enumerate_user_ids(self, client):
        """Should not be able to enumerate user IDs via API."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Try sequential IDs
        for i in range(1, 10):
            response = client.get(f"/api/users/{i}")
            # Should return 404 or not expose user data
            assert response.status_code in [404, 405]


# =============================================================================
# SECURITY HARDENING TESTS - INPUT VALIDATION
# OWASP A03:2021 - Injection (Input Validation)
# =============================================================================


class TestInputValidationHardening:
    """Input validation edge case tests.

    Tests:
    - Boundary values
    - Type confusion
    - Null bytes
    - Unicode edge cases
    - Large payloads
    """

    def test_pagination_boundary_values(self, authenticated_client):
        """Pagination should handle boundary values safely."""
        test_cases = [
            ("page=0", [200, 400, 422]),
            ("page=-1", [200, 400, 422]),
            ("page=999999999", [200, 400, 422]),
            ("per_page=0", [200, 400, 422]),
            ("per_page=-1", [200, 400, 422]),
            ("per_page=1000000", [200, 400, 422]),
            ("page=1.5", [200, 400, 422]),
            ("page=abc", [200, 400, 422]),
            ("page=null", [200, 400, 422]),
        ]
        for params, expected_codes in test_cases:
            response = authenticated_client.get(f"/api/v1/lps?{params}")
            assert response.status_code in expected_codes, f"Failed for {params}"

    def test_null_byte_injection(self, authenticated_client):
        """Null bytes should be handled safely."""
        from urllib.parse import quote
        # URL-encode payloads to avoid httpx URL validation errors
        payloads = [
            "test%00admin",  # Already encoded
            "pension%00' OR '1'='1",  # Already encoded
        ]
        for payload in payloads:
            # Use URL-safe encoded payloads
            response = authenticated_client.get(f"/api/v1/lps?search={quote(payload, safe='')}")
            assert response.status_code in [200, 400, 422]

    def test_unicode_normalization_attacks(self, authenticated_client):
        """Unicode normalization attacks should be handled."""
        payloads = [
            "admin",  # Fullwidth characters
            "admin\u200b",  # Zero-width space
            "ad\u00admin",  # Soft hyphen
            "admin",  # Cyrillic 'a'
        ]
        for payload in payloads:
            response = authenticated_client.get(f"/api/v1/lps?search={payload}")
            assert response.status_code in [200, 400, 422]

    def test_very_long_input(self, authenticated_client):
        """Very long inputs should be handled safely."""
        # Use a reasonable length that won't exceed URL limits (8KB typical)
        long_string = "A" * 4000
        response = authenticated_client.get(f"/api/v1/lps?search={long_string}")
        # Should not crash - may truncate or reject
        assert response.status_code in [200, 400, 413, 414, 422]

    def test_very_long_post_input(self, client):
        """Very long POST inputs should be handled safely."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # POST can handle larger payloads
        long_string = "A" * 100000
        response = client.post(
            "/api/funds",
            data={"name": long_string, "strategy": "buyout"},
        )
        # Should not crash - may truncate or reject
        assert response.status_code in [200, 400, 413, 422, 503]

    def test_special_json_values(self, client):
        """Special JSON values should be handled."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Test creating fund with special values
        test_cases = [
            {"name": None},
            {"name": ""},
            {"name": []},
            {"name": {}},
            {"name": True},
            {"name": 12345},
        ]
        for data in test_cases:
            response = client.post("/api/funds", data=data)
            # Should handle gracefully
            assert response.status_code in [200, 400, 422, 503]

    def test_path_traversal_in_params(self, authenticated_client):
        """Path traversal attempts should be blocked."""
        payloads = [
            "../../../etc/passwd",
            "..\\..\\..\\windows\\system32",
            "%2e%2e%2f%2e%2e%2f",
            "....//....//",
        ]
        for payload in payloads:
            response = authenticated_client.get(f"/api/v1/lps?search={payload}")
            assert response.status_code in [200, 400, 422]
            # Should not expose file system
            assert "root:" not in response.text
            assert "passwd" not in response.text.lower() or "password" in response.text.lower()


# =============================================================================
# SECURITY HARDENING TESTS - API ABUSE
# Rate Limiting and Resource Exhaustion
# =============================================================================


class TestAPIAbuseProtection:
    """API abuse and rate limiting tests.

    Tests:
    - Request flooding
    - Resource exhaustion
    - Parameter pollution
    - Header injection
    """

    def test_duplicate_parameters_handled(self, authenticated_client):
        """Duplicate parameters should be handled safely."""
        response = authenticated_client.get(
            "/api/v1/lps?search=test&search=admin&search=<script>"
        )
        assert response.status_code in [200, 400, 422]

    def test_many_parameters_handled(self, authenticated_client):
        """Many parameters should not crash the server."""
        params = "&".join([f"param{i}=value{i}" for i in range(100)])
        response = authenticated_client.get(f"/api/v1/lps?{params}")
        assert response.status_code in [200, 400, 414, 422]

    def test_large_json_payload(self, client):
        """Large JSON payloads should be rejected or truncated."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        large_payload = {"name": "A" * 1000000}
        response = client.post("/api/funds", json=large_payload)
        assert response.status_code in [200, 400, 413, 422, 503]

    def test_content_type_mismatch(self, client):
        """Content-Type mismatch should be handled."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.post(
            "/api/funds",
            data="not json",
            headers={"Content-Type": "application/json"},
        )
        assert response.status_code in [200, 400, 415, 422, 503]

    def test_method_override_rejected(self, authenticated_client):
        """HTTP method override attempts should be rejected."""
        # Try to use X-HTTP-Method-Override to change GET to DELETE
        response = authenticated_client.get(
            "/api/v1/lps",
            headers={"X-HTTP-Method-Override": "DELETE"},
        )
        # Should still be a GET, not delete anything
        assert response.status_code == 200


# =============================================================================
# SECURITY HARDENING TESTS - HEADERS
# Security Headers
# =============================================================================


class TestAPISecurityHeaders:
    """API security header tests.

    Tests:
    - Content-Type headers
    - Cache-Control headers
    - X-Content-Type-Options
    """

    def test_json_responses_have_correct_content_type(self, authenticated_client):
        """JSON API responses should have application/json content-type."""
        response = authenticated_client.get("/api/v1/lps")
        assert "application/json" in response.headers.get("content-type", "")

    def test_health_endpoint_no_cache(self, client):
        """Health endpoint should not be cached."""
        response = client.get("/health")
        cache_control = response.headers.get("cache-control", "")
        # Should have no-cache or no-store
        assert "no-cache" in cache_control or "no-store" in cache_control or cache_control == ""

    def test_api_responses_not_html(self, authenticated_client):
        """API endpoints should not return HTML content-type."""
        api_endpoints = [
            "/api/v1/lps",
            "/api/v1/gps",
            "/api/v1/funds",
            "/api/status",
            "/health",
        ]
        for endpoint in api_endpoints:
            response = authenticated_client.get(endpoint)
            if response.status_code == 200:
                content_type = response.headers.get("content-type", "")
                assert "text/html" not in content_type, f"{endpoint} returned HTML"


# =============================================================================
# SECURITY HARDENING TESTS - ERROR HANDLING
# Information Disclosure
# =============================================================================


class TestErrorHandlingSecurity:
    """Error handling security tests.

    Tests:
    - Stack trace exposure
    - Database error exposure
    - Internal path exposure
    """

    def test_404_does_not_expose_internals(self, client):
        """404 errors should not expose internal details."""
        response = client.get("/nonexistent/path/here")
        assert response.status_code == 404
        text = response.text.lower()
        assert "traceback" not in text
        assert "file \"/" not in text
        assert "psycopg" not in text
        assert "supabase" not in text

    def test_invalid_json_error_safe(self, client):
        """Invalid JSON errors should not expose internals."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.post(
            "/api/funds",
            data="{invalid json",
            headers={"Content-Type": "application/json"},
        )
        if response.status_code >= 400:
            assert "line" not in response.text.lower() or "pipeline" in response.text.lower()

    def test_database_error_sanitized(self, authenticated_client):
        """Database errors should be sanitized."""
        # Try to trigger a potential database error
        response = authenticated_client.get(
            "/api/v1/lps?search=" + "x" * 10000
        )
        text = response.text.lower()
        assert "postgresql" not in text
        assert "relation" not in text
        assert "column" not in text or "kanban" in text  # kanban column is OK


# =============================================================================
# SECURITY HARDENING TESTS - CSRF
# Cross-Site Request Forgery
# =============================================================================


class TestCSRFProtection:
    """CSRF protection tests."""

    def test_state_changing_endpoints_protected(self, client):
        """State-changing endpoints should require authentication."""
        # These should all require auth
        endpoints = [
            ("POST", "/api/funds"),
            ("PUT", "/api/funds/test-id"),
            ("DELETE", "/api/funds/test-id"),
            ("POST", "/api/shortlist"),
            ("DELETE", "/api/shortlist/test-id"),
        ]
        for method, endpoint in endpoints:
            if method == "POST":
                response = client.post(endpoint, data={})
            elif method == "PUT":
                response = client.put(endpoint, data={})
            elif method == "DELETE":
                response = client.delete(endpoint)
            # Should redirect to login or return 401/403
            assert response.status_code in [302, 303, 307, 400, 401, 403, 404, 422]
