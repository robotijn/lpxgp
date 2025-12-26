"""Tests for LP (Limited Partner) functionality.

IMPORTANT: Tests are the source of truth. Do NOT modify tests to make them pass.
If a test fails, fix the APPLICATION, not the test.

Based on BDD Gherkin specs from docs/prd/tests/*.feature.md

Test Categories:
- TestLPsPage: LP page rendering and structure
- TestLPsCRUD: LP CRUD API endpoints
- TestLPsUUIDValidation: UUID validation for LP endpoints
- TestLPsInputValidation: Input validation for LP creation/update
- TestLPsNumericValidation: Numeric field validation
- TestLPsEnumValidation: Enum field validation
- TestLPsArrayFieldValidation: Array/comma-separated field validation
- TestRestApiV1Lps: REST API endpoint GET /api/v1/lps
- TestRestApiV1LpsFilters: Advanced filters for REST API
"""

import pytest

# =============================================================================
# LP PAGE TESTS
# =============================================================================


class TestLPsPage:
    """Test LPs page rendering and structure.

    Gherkin Reference: M2 - LP Management
    Note: /lps requires authentication, so tests use authenticated_client.
    """

    def test_lps_page_returns_200(self, authenticated_client):
        """LPs page should return 200 OK."""
        response = authenticated_client.get("/lps")
        assert response.status_code == 200

    def test_lps_page_returns_html(self, authenticated_client):
        """LPs page should return HTML content."""
        response = authenticated_client.get("/lps")
        assert "text/html" in response.headers.get("content-type", "")

    def test_lps_page_has_title(self, authenticated_client):
        """LPs page should have LP in title or heading."""
        response = authenticated_client.get("/lps")
        text = response.text.lower()
        assert "lp" in text or "investor" in text

    def test_lps_page_has_new_lp_button(self, authenticated_client):
        """LPs page should have a button to create new LP."""
        response = authenticated_client.get("/lps")
        assert "new lp" in response.text.lower() or "create" in response.text.lower()

    def test_lps_page_has_search(self, authenticated_client):
        """LPs page should have search functionality."""
        response = authenticated_client.get("/lps")
        assert "search" in response.text.lower()

    def test_lps_page_has_type_filter(self, authenticated_client):
        """LPs page should have LP type filter."""
        response = authenticated_client.get("/lps")
        text = response.text.lower()
        assert "type" in text or "filter" in text or "select" in text

    def test_lps_page_has_create_modal(self, authenticated_client):
        """LPs page should have create LP modal markup."""
        response = authenticated_client.get("/lps")
        assert "create-lp-modal" in response.text

    def test_lps_page_search_query_param(self, authenticated_client):
        """LPs page should accept search query parameter."""
        response = authenticated_client.get("/lps?q=test")
        assert response.status_code == 200

    def test_lps_page_type_filter_param(self, authenticated_client):
        """LPs page should accept type filter parameter."""
        response = authenticated_client.get("/lps?type=pension")
        assert response.status_code == 200


# =============================================================================
# LP CRUD TESTS
# =============================================================================


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


# =============================================================================
# LP UUID VALIDATION TESTS
# =============================================================================


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


# =============================================================================
# LP INPUT VALIDATION TESTS
# =============================================================================


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
            data={"name": "投資者 Investor"}
        )
        assert response.status_code != 500


# =============================================================================
# LP NUMERIC VALIDATION TESTS
# =============================================================================


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


# =============================================================================
# LP ENUM VALIDATION TESTS
# =============================================================================


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


# =============================================================================
# LP ARRAY FIELD VALIDATION TESTS
# =============================================================================


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
# REST API V1 LPS TESTS
# =============================================================================


class TestRestApiV1Lps:
    """Test REST API endpoint GET /api/v1/lps.

    M1 Requirement: API: GET /api/v1/lps with filters
    Returns JSON for programmatic access.
    """

    def test_api_v1_lps_returns_json(self, authenticated_client):
        """API should return JSON response."""
        response = authenticated_client.get("/api/v1/lps")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_api_v1_lps_response_structure(self, authenticated_client):
        """API response should have standard structure."""
        response = authenticated_client.get("/api/v1/lps")
        assert response.status_code == 200
        data = response.json()
        # Should have standard API response structure
        assert "data" in data
        assert isinstance(data["data"], list)
        assert "total" in data
        assert "page" in data
        assert "per_page" in data

    def test_api_v1_lps_returns_lp_data(self, authenticated_client):
        """API should return LP data with expected fields."""
        response = authenticated_client.get("/api/v1/lps")
        assert response.status_code == 200
        data = response.json()
        if data["data"]:  # If there's data
            lp = data["data"][0]
            # Check required LP fields
            assert "id" in lp
            assert "name" in lp

    def test_api_v1_lps_search_filter(self, authenticated_client):
        """API should support search parameter."""
        response = authenticated_client.get("/api/v1/lps?search=pension")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_api_v1_lps_type_filter(self, authenticated_client):
        """API should support lp_type filter."""
        response = authenticated_client.get("/api/v1/lps?lp_type=pension")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_api_v1_lps_pagination(self, authenticated_client):
        """API should support pagination parameters."""
        response = authenticated_client.get("/api/v1/lps?page=1&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 10

    def test_api_v1_lps_requires_auth(self, client):
        """API should require authentication."""
        response = client.get("/api/v1/lps")
        # Should return 401 or redirect to login
        assert response.status_code in [401, 302, 303, 307]

    def test_api_v1_lps_invalid_page_returns_error(self, authenticated_client):
        """API should handle invalid pagination gracefully."""
        response = authenticated_client.get("/api/v1/lps?page=-1")
        # Should return error or default to page 1
        assert response.status_code in [200, 400, 422]

    def test_api_v1_lps_sql_injection_safe(self, authenticated_client):
        """API should be safe from SQL injection."""
        response = authenticated_client.get(
            "/api/v1/lps?search='; DROP TABLE organizations; --"
        )
        # Should not crash
        assert response.status_code in [200, 400, 422]
        assert "error" not in response.json().get("data", [])


# =============================================================================
# REST API V1 LPS FILTERS TESTS
# =============================================================================


class TestRestApiV1LpsFilters:
    """Test advanced filters for REST API /api/v1/lps."""

    def test_api_v1_lps_aum_min_filter(self, authenticated_client):
        """API should support minimum AUM filter."""
        response = authenticated_client.get("/api/v1/lps?aum_min=100")
        assert response.status_code == 200

    def test_api_v1_lps_aum_max_filter(self, authenticated_client):
        """API should support maximum AUM filter."""
        response = authenticated_client.get("/api/v1/lps?aum_max=500")
        assert response.status_code == 200

    def test_api_v1_lps_location_filter(self, authenticated_client):
        """API should support location filter."""
        response = authenticated_client.get("/api/v1/lps?location=California")
        assert response.status_code == 200

    def test_api_v1_lps_strategy_filter(self, authenticated_client):
        """API should support strategy filter."""
        response = authenticated_client.get("/api/v1/lps?strategy=buyout")
        assert response.status_code == 200

    def test_api_v1_lps_combined_filters(self, authenticated_client):
        """API should support multiple filters combined."""
        response = authenticated_client.get(
            "/api/v1/lps?lp_type=pension&aum_min=100&strategy=buyout"
        )
        assert response.status_code == 200
