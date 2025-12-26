"""Comprehensive tests for AI-powered LP search functionality.

Tests cover:
- Natural language query detection
- JSON extraction from LLM responses
- SQL WHERE clause building
- Ollama integration with mocking
- Fallback behavior when Ollama unavailable
"""

from unittest.mock import AsyncMock, MagicMock, patch

import httpx
import pytest

from src.search import (
    _extract_json,
    build_lp_search_sql,
    is_natural_language_query,
    parse_lp_search_query,
)

# =============================================================================
# Tests for is_natural_language_query()
# =============================================================================


class TestIsNaturalLanguageQuery:
    """Tests for natural language query detection."""

    def test_simple_name_is_not_natural_language(self):
        """Simple LP names should use text search, not AI."""
        assert is_natural_language_query("CalPERS") is False
        assert is_natural_language_query("Harvard") is False
        assert is_natural_language_query("Blackstone") is False

    def test_short_queries_are_not_natural_language(self):
        """Queries under 5 chars should not trigger AI."""
        assert is_natural_language_query("") is False
        assert is_natural_language_query("abc") is False
        assert is_natural_language_query("test") is False

    def test_aum_queries_are_natural_language(self):
        """Queries with AUM amounts should trigger AI."""
        assert is_natural_language_query("50m or more aum") is True
        assert is_natural_language_query("AUM over 1B") is True
        assert is_natural_language_query("500M minimum") is True
        assert is_natural_language_query("at least 100m") is True

    def test_comparison_phrases_are_natural_language(self):
        """Comparison phrases should trigger AI."""
        assert is_natural_language_query("more than 50 million") is True
        assert is_natural_language_query("less than 1 billion") is True
        assert is_natural_language_query("at least 25m check") is True
        assert is_natural_language_query("greater than 100") is True
        assert is_natural_language_query("over 500 million") is True
        assert is_natural_language_query("under 10 billion") is True

    def test_lp_type_queries_are_natural_language(self):
        """LP type mentions should trigger AI."""
        assert is_natural_language_query("pension funds") is True
        assert is_natural_language_query("endowment investors") is True
        assert is_natural_language_query("family office") is True
        assert is_natural_language_query("sovereign wealth") is True

    def test_strategy_queries_are_natural_language(self):
        """Investment strategy mentions should trigger AI."""
        assert is_natural_language_query("buyout focused") is True
        assert is_natural_language_query("growth investors") is True
        assert is_natural_language_query("venture capital") is True
        assert is_natural_language_query("infrastructure funds") is True

    def test_location_queries_are_natural_language(self):
        """Location-based queries should trigger AI."""
        assert is_natural_language_query("in california") is True
        assert is_natural_language_query("investors in new york") is True
        assert is_natural_language_query("based in london") is True
        assert is_natural_language_query("investors in europe") is True
        assert is_natural_language_query("funds in asia") is True
        assert is_natural_language_query("middle east investors") is True

    def test_complex_queries_are_natural_language(self):
        """Complex multi-part queries should trigger AI."""
        assert is_natural_language_query("pension funds with 50m aum") is True
        assert is_natural_language_query("buyout in california over 100m") is True
        assert is_natural_language_query("family office growth investors") is True


# =============================================================================
# Tests for _extract_json()
# =============================================================================


class TestExtractJson:
    """Tests for JSON extraction from LLM responses."""

    def test_clean_json_extraction(self):
        """Clean JSON should parse directly."""
        result = _extract_json('{"aum_min": 0.05}')
        assert result == {"aum_min": 0.05}

    def test_json_with_whitespace(self):
        """JSON with whitespace should parse."""
        result = _extract_json('  {"aum_min": 0.05}  ')
        assert result == {"aum_min": 0.05}

    def test_json_embedded_in_text(self):
        """JSON embedded in explanation text should be extracted."""
        result = _extract_json('Here is the result: {"aum_min": 0.05} Hope this helps!')
        assert result == {"aum_min": 0.05}

    def test_json_with_multiple_fields(self):
        """Multi-field JSON should parse correctly."""
        result = _extract_json('{"aum_min": 0.05, "lp_type": "pension"}')
        assert result == {"aum_min": 0.05, "lp_type": "pension"}

    def test_invalid_json_returns_none(self):
        """Invalid JSON should return None."""
        assert _extract_json("not json at all") is None
        assert _extract_json("{broken json") is None
        assert _extract_json("") is None

    def test_empty_object_is_valid(self):
        """Empty JSON object should parse."""
        result = _extract_json("{}")
        assert result == {}

    def test_nested_braces_takes_first_object(self):
        """With nested braces, first complete object should be extracted."""
        # This is a limitation - we take first {...} match
        result = _extract_json('outer {"inner": 1} more')
        assert result == {"inner": 1}


# =============================================================================
# Tests for build_lp_search_sql()
# =============================================================================


class TestBuildLpSearchSql:
    """Tests for SQL WHERE clause building."""

    def test_empty_filters_returns_base_condition(self):
        """Empty filters should only have base LP condition."""
        where, params = build_lp_search_sql({})
        assert "o.is_lp = TRUE" in where
        assert params == []

    def test_aum_min_filter(self):
        """AUM minimum filter should create >= condition."""
        where, params = build_lp_search_sql({"aum_min": 0.05})
        assert "lp.total_aum_bn >= %s" in where
        assert 0.05 in params

    def test_aum_max_filter(self):
        """AUM maximum filter should create <= condition."""
        where, params = build_lp_search_sql({"aum_max": 1.0})
        assert "lp.total_aum_bn <= %s" in where
        assert 1.0 in params

    def test_aum_range_filter(self):
        """AUM range should create both >= and <= conditions."""
        where, params = build_lp_search_sql({"aum_min": 0.05, "aum_max": 1.0})
        assert "lp.total_aum_bn >= %s" in where
        assert "lp.total_aum_bn <= %s" in where
        assert 0.05 in params
        assert 1.0 in params

    def test_lp_type_filter(self):
        """LP type filter should create exact match condition."""
        where, params = build_lp_search_sql({"lp_type": "pension"})
        assert "lp.lp_type = %s" in where
        assert "pension" in params

    def test_location_filter(self):
        """Location filter should search city and country."""
        where, params = build_lp_search_sql({"location": "California"})
        assert "o.hq_city ILIKE %s" in where
        assert "o.hq_country ILIKE %s" in where
        assert "%California%" in params

    def test_strategies_filter_single(self):
        """Single strategy should use array overlap."""
        where, params = build_lp_search_sql({"strategies": ["buyout"]})
        assert "lp.strategies && %s::text[]" in where
        assert ["buyout"] in params

    def test_strategies_filter_multiple(self):
        """Multiple strategies should use array overlap."""
        where, params = build_lp_search_sql({"strategies": ["buyout", "growth"]})
        assert "lp.strategies && %s::text[]" in where
        assert ["buyout", "growth"] in params

    def test_strategies_filter_string_converted_to_list(self):
        """String strategy should be converted to list."""
        where, params = build_lp_search_sql({"strategies": "buyout"})
        assert "lp.strategies && %s::text[]" in where
        assert ["buyout"] in params

    def test_check_size_min_filter(self):
        """Check size minimum should filter on LP's max check size."""
        where, params = build_lp_search_sql({"check_size_min": 25})
        assert "lp.check_size_max_mm >= %s" in where
        assert 25.0 in params

    def test_check_size_max_filter(self):
        """Check size maximum should filter on LP's min check size."""
        where, params = build_lp_search_sql({"check_size_max": 100})
        assert "lp.check_size_min_mm <= %s" in where
        assert 100.0 in params

    def test_text_search_fallback(self):
        """Text search should search name and city."""
        where, params = build_lp_search_sql({"text_search": "CalPERS"})
        assert "o.name ILIKE %s" in where
        assert "o.hq_city ILIKE %s" in where
        assert "%CalPERS%" in params

    def test_combined_filters(self):
        """Multiple filters should be combined with AND."""
        where, params = build_lp_search_sql({
            "aum_min": 0.05,
            "lp_type": "pension",
            "location": "California",
        })
        assert "o.is_lp = TRUE" in where
        assert "lp.total_aum_bn >= %s" in where
        assert "lp.lp_type = %s" in where
        assert "o.hq_city ILIKE %s" in where
        assert " AND " in where
        assert len(params) == 4  # aum_min, lp_type, city pattern, country pattern

    def test_custom_base_conditions(self):
        """Custom base conditions should be included."""
        where, params = build_lp_search_sql(
            {"aum_min": 0.05},
            base_conditions=["custom_condition = TRUE"]
        )
        assert "custom_condition = TRUE" in where
        assert "lp.total_aum_bn >= %s" in where


# =============================================================================
# Tests for parse_lp_search_query() with mocked Ollama
# =============================================================================


class TestParseLpSearchQuery:
    """Tests for Ollama-based query parsing with mocked responses."""

    def _create_mock_response(self, json_data: dict) -> MagicMock:
        """Create a mock httpx Response with sync json() method."""
        mock_response = MagicMock()
        mock_response.json.return_value = json_data
        mock_response.raise_for_status.return_value = None
        return mock_response

    @pytest.mark.asyncio
    async def test_successful_aum_parsing(self):
        """Ollama should parse AUM query into filters."""
        mock_response = self._create_mock_response({
            "response": '{"aum_min": 0.05}'
        })

        with patch("src.search.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            result = await parse_lp_search_query("50m or more aum")

            assert result.get("aum_min") == 0.05

    @pytest.mark.asyncio
    async def test_successful_complex_parsing(self):
        """Ollama should parse complex query into multiple filters."""
        mock_response = self._create_mock_response({
            "response": '{"aum_min": 0.1, "lp_type": "pension", "location": "California"}'
        })

        with patch("src.search.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            result = await parse_lp_search_query("pension funds in california with 100m aum")

            assert result.get("aum_min") == 0.1
            assert result.get("lp_type") == "pension"
            assert result.get("location") == "California"

    @pytest.mark.asyncio
    async def test_timeout_falls_back_to_text_search(self):
        """Timeout should fall back to text search."""
        with patch("src.search.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.side_effect = httpx.TimeoutException("timeout")

            result = await parse_lp_search_query("50m or more aum")

            assert result["text_search"] == "50m or more aum"
            assert result["_cache_hit"] is False
            assert "_parse_time_ms" in result

    @pytest.mark.asyncio
    async def test_http_error_falls_back_to_text_search(self):
        """HTTP error should fall back to text search."""
        with patch("src.search.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.side_effect = httpx.HTTPError("connection failed")

            result = await parse_lp_search_query("pension funds")

            assert result["text_search"] == "pension funds"
            assert result["_cache_hit"] is False

    @pytest.mark.asyncio
    async def test_invalid_json_response_falls_back(self):
        """Invalid JSON from Ollama should fall back to text search."""
        mock_response = self._create_mock_response({
            "response": "I cannot parse this query properly"
        })

        with patch("src.search.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            result = await parse_lp_search_query("weird query")

            assert result["text_search"] == "weird query"
            assert result["_cache_hit"] is False

    @pytest.mark.asyncio
    async def test_empty_response_falls_back(self):
        """Empty response from Ollama should fall back to text search."""
        mock_response = self._create_mock_response({
            "response": ""
        })

        with patch("src.search.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            result = await parse_lp_search_query("some query")

            assert result["text_search"] == "some query"
            assert result["_cache_hit"] is False

    @pytest.mark.asyncio
    async def test_json_embedded_in_explanation(self):
        """JSON embedded in explanation should be extracted."""
        mock_response = self._create_mock_response({
            "response": 'Based on your query, here are the filters: {"aum_min": 0.05} I hope this helps!'
        })

        with patch("src.search.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            result = await parse_lp_search_query("50m aum")

            assert result.get("aum_min") == 0.05


# =============================================================================
# Integration Tests - SQL Generation End-to-End
# =============================================================================


class TestSqlGenerationIntegration:
    """Integration tests for full query -> SQL flow."""

    def test_realistic_aum_query_produces_valid_sql(self):
        """Realistic AUM filter should produce valid SQL structure."""
        filters = {"aum_min": 0.05}  # 50M in billions
        where, params = build_lp_search_sql(filters)

        # Should be valid SQL structure
        assert where.count("%s") == len(params)
        assert "AND" in where or where.count("=") == 1

    def test_realistic_complex_query_produces_valid_sql(self):
        """Complex filter should produce valid SQL structure."""
        filters = {
            "aum_min": 0.1,
            "aum_max": 10.0,
            "lp_type": "pension",
            "location": "California",
            "strategies": ["buyout", "growth"],
        }
        where, params = build_lp_search_sql(filters)

        # Should be valid SQL structure
        assert where.count("%s") == len(params)
        # Should have all conditions
        assert "total_aum_bn >=" in where
        assert "total_aum_bn <=" in where
        assert "lp_type =" in where
        assert "hq_city ILIKE" in where
        assert "strategies &&" in where

    def test_no_sql_injection_in_text_search(self):
        """Text search should be parameterized, not interpolated."""
        filters = {"text_search": "'; DROP TABLE organizations; --"}
        where, params = build_lp_search_sql(filters)

        # The malicious string should be in params, not in the WHERE clause
        assert "DROP TABLE" not in where
        assert any("DROP TABLE" in str(p) for p in params)
        # Should use %s placeholder
        assert "ILIKE %s" in where


# =============================================================================
# Tests for Bad Model Responses (like smaller models)
# =============================================================================


class TestBadModelResponses:
    """Tests for handling bad responses from smaller/weaker LLM models."""

    def _create_mock_response(self, json_data: dict) -> MagicMock:
        """Create a mock httpx Response."""
        mock_response = MagicMock()
        mock_response.json.return_value = json_data
        mock_response.raise_for_status.return_value = None
        return mock_response

    @pytest.mark.asyncio
    async def test_null_response_falls_back_to_text_search(self):
        """Model returning 'null' should fall back to text search.

        This catches the deepseek-r1:1.5b issue where it returns null.
        """
        mock_response = self._create_mock_response({
            "response": "null"
        })

        with patch("src.search.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            result = await parse_lp_search_query("50m or more aum")

            # Should fall back to text search, not crash
            assert result.get("text_search") == "50m or more aum"
            assert result.get("_cache_hit") is False

    @pytest.mark.asyncio
    async def test_markdown_wrapped_json_extracted(self):
        """Model returning JSON wrapped in markdown should be extracted.

        Some models return ```json\n{...}\n```
        """
        mock_response = self._create_mock_response({
            "response": '```json\n{"aum_min": 0.05}\n```'
        })

        with patch("src.search.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            result = await parse_lp_search_query("50m aum")

            assert result.get("aum_min") == 0.05

    @pytest.mark.asyncio
    async def test_thinking_tags_with_json_extracted(self):
        """Model with <think> tags should still extract JSON.

        deepseek-r1 models include <think>...</think> before the answer.
        """
        mock_response = self._create_mock_response({
            "response": '<think>The user wants 50M which is 0.05B</think>\n{"aum_min": 0.05}'
        })

        with patch("src.search.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            result = await parse_lp_search_query("50m aum")

            assert result.get("aum_min") == 0.05

    def test_lp_type_as_list_handled_gracefully(self):
        """Model returning lp_type as list should not break SQL.

        Bad models might return {"lp_type": ["pension", "endowment"]}
        instead of {"lp_type": "pension"}
        """
        # This is a bad filter - lp_type should be scalar
        filters = {"lp_type": ["pension", "endowment"]}

        # Should not crash - SQL generation should handle it
        # (even if the query might not return expected results)
        where, params = build_lp_search_sql(filters)

        # Query should still be valid syntax
        assert "o.is_lp = TRUE" in where
        assert "lp.lp_type = %s" in where

    def test_aum_as_none_ignored(self):
        """Model returning aum_min: None should be ignored.

        Bad response: {"aum_min": null, "lp_type": "pension"}
        """
        filters = {"aum_min": None, "lp_type": "pension"}
        where, params = build_lp_search_sql(filters)

        # aum_min: None should be ignored
        assert "total_aum_bn" not in where
        # lp_type should still work
        assert "lp.lp_type = %s" in where
        assert "pension" in params

    def test_empty_string_location_ignored(self):
        """Model returning empty location should be ignored."""
        filters = {"location": "", "aum_min": 0.05}
        where, params = build_lp_search_sql(filters)

        # Empty location should not create ILIKE condition
        assert "hq_city" not in where
        # aum_min should still work
        assert "total_aum_bn >= %s" in where

    def test_empty_list_strategies_ignored(self):
        """Model returning empty strategies list should be ignored."""
        filters = {"strategies": [], "aum_min": 0.05}
        where, params = build_lp_search_sql(filters)

        # Empty list should not create array overlap
        assert "strategies &&" not in where
        # aum_min should still work
        assert "total_aum_bn >= %s" in where
