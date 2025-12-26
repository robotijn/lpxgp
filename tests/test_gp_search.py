"""Tests for GP search functionality.

Tests the AI-powered GP search including:
- GP search SQL building
- Natural language query detection
- GP route responses
- GP CRUD API endpoints
"""

from __future__ import annotations

from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.search import (
    build_gp_search_sql,
    is_natural_language_query,
    parse_gp_search_query,
)


class TestBuildGpSearchSql:
    """Tests for build_gp_search_sql function."""

    def test_empty_filters_returns_base_condition(self):
        """Empty filters should return just the base GP condition."""
        where_clause, params = build_gp_search_sql({})
        assert where_clause == "o.is_gp = TRUE"
        assert params == []

    def test_strategy_filter(self):
        """Strategy filter should search in investment_philosophy."""
        filters = {"strategy": "buyout"}
        where_clause, params = build_gp_search_sql(filters)
        assert "investment_philosophy ILIKE" in where_clause
        assert "%buyout%" in params

    def test_location_filter(self):
        """Location filter should search city and country."""
        filters = {"location": "New York"}
        where_clause, params = build_gp_search_sql(filters)
        assert "o.hq_city ILIKE" in where_clause
        assert "o.hq_country ILIKE" in where_clause
        assert "%New York%" in params

    def test_team_size_filter(self):
        """Team size filter should check team_size >= value."""
        filters = {"team_size_min": 10}
        where_clause, params = build_gp_search_sql(filters)
        assert "gp.team_size >= %s" in where_clause
        assert 10 in params

    def test_years_investing_filter(self):
        """Years investing filter should check years_investing >= value."""
        filters = {"years_investing_min": 15}
        where_clause, params = build_gp_search_sql(filters)
        assert "gp.years_investing >= %s" in where_clause
        assert 15 in params

    def test_text_search_filter(self):
        """Text search should search name, city, and philosophy."""
        filters = {"text_search": "Sequoia"}
        where_clause, params = build_gp_search_sql(filters)
        assert "o.name ILIKE" in where_clause
        assert "o.hq_city ILIKE" in where_clause
        assert "gp.investment_philosophy ILIKE" in where_clause
        assert "%Sequoia%" in params

    def test_multiple_filters(self):
        """Multiple filters should be combined with AND."""
        filters = {
            "strategy": "venture",
            "location": "San Francisco",
            "team_size_min": 5,
        }
        where_clause, params = build_gp_search_sql(filters)
        assert "AND" in where_clause
        assert "%venture%" in params
        assert "%San Francisco%" in params
        assert 5 in params

    def test_custom_base_conditions(self):
        """Custom base conditions should be included."""
        filters = {"strategy": "growth"}
        where_clause, params = build_gp_search_sql(filters, base_conditions=["o.id IS NOT NULL"])
        assert "o.id IS NOT NULL" in where_clause
        assert "%growth%" in params


class TestNaturalLanguageDetection:
    """Tests for natural language query detection."""

    def test_simple_name_is_not_natural_language(self):
        """Simple names should not trigger AI parsing."""
        assert is_natural_language_query("Sequoia") is False
        assert is_natural_language_query("KKR") is False
        assert is_natural_language_query("TPG") is False

    def test_short_queries_are_not_natural_language(self):
        """Short queries (< 5 chars) should not trigger AI parsing."""
        assert is_natural_language_query("test") is False
        assert is_natural_language_query("") is False

    def test_queries_with_numbers_are_natural_language(self):
        """Queries with fund sizes should trigger AI parsing."""
        assert is_natural_language_query("500M fund") is True
        assert is_natural_language_query("1B aum") is True

    def test_strategy_keywords_are_natural_language(self):
        """Strategy-related queries should trigger AI parsing."""
        assert is_natural_language_query("buyout funds in new york") is True
        assert is_natural_language_query("growth equity managers") is True
        assert is_natural_language_query("venture capital focused") is True

    def test_location_phrases_are_natural_language(self):
        """Location-related queries should trigger AI parsing."""
        assert is_natural_language_query("funds in California") is True
        assert is_natural_language_query("managers based in Europe") is True


class TestParseGpSearchQuery:
    """Tests for GP search query parsing."""

    @pytest.mark.asyncio
    async def test_returns_fallback_on_timeout(self):
        """Should return text_search on Ollama timeout."""
        with patch("src.search.httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            import httpx
            mock_instance.post = AsyncMock(side_effect=httpx.TimeoutException("timeout"))

            result = await parse_gp_search_query("buyout firms", use_cache=False)

            assert result["text_search"] == "buyout firms"
            assert result["_cache_hit"] is False

    @pytest.mark.asyncio
    async def test_returns_fallback_on_http_error(self):
        """Should return text_search on HTTP error."""
        with patch("src.search.httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            import httpx
            mock_instance.post = AsyncMock(side_effect=httpx.HTTPError("error"))

            result = await parse_gp_search_query("buyout firms", use_cache=False)

            assert result["text_search"] == "buyout firms"
            assert result["_cache_hit"] is False

    @pytest.mark.asyncio
    async def test_parses_strategy_from_valid_response(self):
        """Should extract strategy from Ollama response."""
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": '{"strategy": "buyout", "location": "New York"}'
        }
        mock_response.raise_for_status = MagicMock()

        with patch("src.search.httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_instance.post = AsyncMock(return_value=mock_response)

            result = await parse_gp_search_query("buyout firms in NYC", use_cache=False)

            assert result["strategy"] == "buyout"
            assert result["location"] == "New York"
            assert result["_cache_hit"] is False

    @pytest.mark.asyncio
    async def test_cache_hit_returns_cached_result(self):
        """Cached queries should return cached result."""
        from src.cache import clear_all_caches

        clear_all_caches()

        # First call - should miss cache
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": '{"strategy": "venture"}'
        }
        mock_response.raise_for_status = MagicMock()

        with patch("src.search.httpx.AsyncClient") as mock_client:
            mock_instance = MagicMock()
            mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_instance)
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
            mock_instance.post = AsyncMock(return_value=mock_response)

            result1 = await parse_gp_search_query("venture firms", use_cache=True)
            assert result1["_cache_hit"] is False

            # Second call - should hit cache
            result2 = await parse_gp_search_query("venture firms", use_cache=True)
            assert result2["_cache_hit"] is True
            assert result2["strategy"] == "venture"


class TestGpRoutes:
    """Tests for GP route endpoints."""

    @pytest.fixture
    def mock_user(self):
        """Create a mock authenticated user."""
        return {
            "id": "test-user-id",
            "email": "test@example.com",
            "role": "member",
        }

    def test_gps_page_requires_auth(self, client):
        """GPs page should redirect unauthenticated users."""
        response = client.get("/gps", follow_redirects=False)
        assert response.status_code in [303, 307, 302]

    def test_gps_page_returns_html(self, authenticated_client):
        """GPs page should return HTML for authenticated users."""
        response = authenticated_client.get("/gps")
        assert response.status_code == 200
        assert "GP Database" in response.text or "text/html" in response.headers.get("content-type", "")


class TestGpCrudApi:
    """Tests for GP CRUD API endpoints."""

    def test_create_gp_without_db(self, authenticated_client):
        """Creating GP without DB should return 503."""
        response = authenticated_client.post(
            "/api/gps",
            data={
                "name": "Test GP",
                "hq_city": "San Francisco",
            },
        )
        # Without DB configured, should get 503 or form response
        assert response.status_code in [200, 503]

    def test_get_gp_edit_invalid_id(self, authenticated_client):
        """Getting GP edit with invalid ID should return 400."""
        response = authenticated_client.get("/api/gps/invalid-uuid/edit")
        assert response.status_code == 400
        assert "Invalid GP ID" in response.text

    def test_update_gp_invalid_id(self, authenticated_client):
        """Updating GP with invalid ID should return 400."""
        response = authenticated_client.put(
            "/api/gps/not-a-uuid",
            data={"name": "Updated GP"},
        )
        assert response.status_code == 400
        assert "Invalid GP ID" in response.text

    def test_delete_gp_invalid_id(self, authenticated_client):
        """Deleting GP with invalid ID should return 400."""
        response = authenticated_client.delete("/api/gps/not-a-uuid")
        assert response.status_code == 400
        assert "Invalid GP ID" in response.text

    def test_get_gp_detail_invalid_id(self, authenticated_client):
        """Getting GP detail with invalid ID should return 400."""
        response = authenticated_client.get("/api/gp/not-a-uuid/detail")
        assert response.status_code == 400
        assert "Invalid GP ID" in response.text
