"""Tests for GP-related API endpoints.

IMPORTANT: Tests are the source of truth. Do NOT modify tests to make them pass.
If a test fails, fix the APPLICATION, not the test.

Based on BDD Gherkin specs from docs/prd/tests/*.feature.md
"""


# =============================================================================
# REST API V1: GP Search
# M1 Requirement: GET /api/v1/gps with filters
# =============================================================================


class TestRestApiV1Gps:
    """Test REST API endpoint GET /api/v1/gps.

    Returns JSON for programmatic access to GP data.
    """

    def test_api_v1_gps_returns_json(self, authenticated_client):
        """API should return JSON response."""
        response = authenticated_client.get("/api/v1/gps")
        assert response.status_code == 200
        assert "application/json" in response.headers["content-type"]

    def test_api_v1_gps_response_structure(self, authenticated_client):
        """API response should have standard structure."""
        response = authenticated_client.get("/api/v1/gps")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data
        assert isinstance(data["data"], list)
        assert "total" in data
        assert "page" in data
        assert "per_page" in data

    def test_api_v1_gps_returns_gp_data(self, authenticated_client):
        """API should return GP data with expected fields."""
        response = authenticated_client.get("/api/v1/gps")
        assert response.status_code == 200
        data = response.json()
        if data["data"]:
            gp = data["data"][0]
            assert "id" in gp
            assert "name" in gp

    def test_api_v1_gps_search_filter(self, authenticated_client):
        """API should support search parameter."""
        response = authenticated_client.get("/api/v1/gps?search=venture")
        assert response.status_code == 200
        data = response.json()
        assert "data" in data

    def test_api_v1_gps_strategy_filter(self, authenticated_client):
        """API should support strategy filter."""
        response = authenticated_client.get("/api/v1/gps?strategy=buyout")
        assert response.status_code == 200

    def test_api_v1_gps_pagination(self, authenticated_client):
        """API should support pagination parameters."""
        response = authenticated_client.get("/api/v1/gps?page=1&per_page=10")
        assert response.status_code == 200
        data = response.json()
        assert data["page"] == 1
        assert data["per_page"] == 10

    def test_api_v1_gps_requires_auth(self, client):
        """API should require authentication."""
        response = client.get("/api/v1/gps")
        assert response.status_code in [401, 302, 303, 307]

    def test_api_v1_gps_location_filter(self, authenticated_client):
        """API should support location filter."""
        response = authenticated_client.get("/api/v1/gps?location=California")
        assert response.status_code == 200
