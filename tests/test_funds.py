"""Tests for Fund-related endpoints.

IMPORTANT: Tests are the source of truth. Do NOT modify tests to make them pass.
If a test fails, fix the APPLICATION, not the test.

Extracted from test_main.py for better organization.
Based on BDD Gherkin specs from docs/prd/tests/*.feature.md
"""

import pytest


class TestFundsPage:
    """Test funds page rendering and structure.

    Gherkin Reference: M2 - Fund Management
    Note: /funds requires authentication, so tests use authenticated_client.
    """

    def test_funds_page_returns_200(self, authenticated_client):
        """Funds page should return 200 OK."""
        response = authenticated_client.get("/funds")
        assert response.status_code == 200

    def test_funds_page_returns_html(self, authenticated_client):
        """Funds page should return HTML content."""
        response = authenticated_client.get("/funds")
        assert "text/html" in response.headers.get("content-type", "")

    def test_funds_page_has_title(self, authenticated_client):
        """Funds page should have Funds in title or heading."""
        response = authenticated_client.get("/funds")
        assert "funds" in response.text.lower()

    def test_funds_page_has_new_fund_button(self, authenticated_client):
        """Funds page should have a button to create new fund."""
        response = authenticated_client.get("/funds")
        assert "new fund" in response.text.lower() or "create" in response.text.lower()

    def test_funds_page_has_stats_section(self, authenticated_client):
        """Funds page should display fund statistics."""
        response = authenticated_client.get("/funds")
        text = response.text.lower()
        assert "total" in text or "raising" in text or "target" in text

    def test_funds_page_has_create_modal(self, authenticated_client):
        """Funds page should have create fund modal markup."""
        response = authenticated_client.get("/funds")
        assert "create-fund-modal" in response.text

    def test_funds_page_has_form_fields(self, authenticated_client):
        """Funds page create form should have required fields."""
        response = authenticated_client.get("/funds")
        assert 'name="name"' in response.text
        assert 'name="org_id"' in response.text

    def test_funds_page_valid_html_structure(self, authenticated_client):
        """Funds page should have valid HTML structure."""
        response = authenticated_client.get("/funds")
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


class TestRestApiV1Funds:
    """Test REST API endpoint GET /api/v1/funds.

    Returns JSON for programmatic access to Fund data.
    """

    def test_api_v1_funds_returns_json(self, authenticated_client):
        """API should return JSON response."""
        response = authenticated_client.get("/api/v1/funds")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_api_v1_funds_response_structure(self, authenticated_client):
        """API response should have standard structure."""
        response = authenticated_client.get("/api/v1/funds")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)
        assert "total" in data
        assert "page" in data
        assert "per_page" in data

    def test_api_v1_funds_returns_fund_data(self, authenticated_client):
        """API should return Fund data with expected fields."""
        response = authenticated_client.get("/api/v1/funds")
        assert response.status_code == 200
        data = response.json()
        if data["data"]:
            fund = data["data"][0]
            assert "id" in fund
            assert "name" in fund

    def test_api_v1_funds_search_filter(self, authenticated_client):
        """API should support search parameter."""
        response = authenticated_client.get("/api/v1/funds?search=growth")
        assert response.status_code == 200

    def test_api_v1_funds_strategy_filter(self, authenticated_client):
        """API should support strategy filter."""
        response = authenticated_client.get("/api/v1/funds?strategy=buyout")
        assert response.status_code == 200

    def test_api_v1_funds_status_filter(self, authenticated_client):
        """API should support status filter."""
        response = authenticated_client.get("/api/v1/funds?status=raising")
        assert response.status_code == 200

    def test_api_v1_funds_vintage_year_filter(self, authenticated_client):
        """API should support vintage_year filter."""
        response = authenticated_client.get("/api/v1/funds?vintage_year=2024")
        assert response.status_code == 200

    def test_api_v1_funds_pagination(self, authenticated_client):
        """API should support pagination parameters."""
        response = authenticated_client.get("/api/v1/funds?page=1&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 10

    def test_api_v1_funds_requires_auth(self, client):
        """API should require authentication."""
        response = client.get("/api/v1/funds")
        assert response.status_code in [401, 302, 303, 307]
