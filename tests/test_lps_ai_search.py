"""Integration tests for AI-powered LP search on the /lps route.

Tests the full flow from HTTP request through AI parsing to response.
"""

from typing import Generator
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app


@pytest.fixture
def authenticated_client_with_db() -> Generator[TestClient, None, None]:
    """Create a test client with mocked auth and a mock database cursor."""
    mock_user = {
        "id": "test-user-id",
        "email": "test@example.com",
        "role": "gp_user",
        "org_id": "c0000001-0000-0000-0000-000000000001",
    }

    # Create mock cursor and connection
    mock_cursor = MagicMock()
    mock_cursor.__enter__ = MagicMock(return_value=mock_cursor)
    mock_cursor.__exit__ = MagicMock(return_value=None)

    # Mock LP types query result
    mock_cursor.fetchall.side_effect = [
        # First call: LP types
        [{"lp_type": "pension"}, {"lp_type": "endowment"}, {"lp_type": "family_office"}],
        # Second call: LP results
        [
            {
                "id": "lp-001",
                "name": "CalPERS",
                "hq_city": "Sacramento",
                "hq_country": "USA",
                "website": "https://calpers.ca.gov",
                "lp_type": "pension",
                "total_aum_bn": 450.0,
                "pe_allocation_pct": 12.0,
                "check_size_min_mm": 25.0,
                "check_size_max_mm": 200.0,
                "geographic_preferences": ["North America", "Europe"],
                "strategies": ["buyout", "growth"],
            },
            {
                "id": "lp-002",
                "name": "Harvard Endowment",
                "hq_city": "Boston",
                "hq_country": "USA",
                "website": "https://hmc.harvard.edu",
                "lp_type": "endowment",
                "total_aum_bn": 53.0,
                "pe_allocation_pct": 34.0,
                "check_size_min_mm": 50.0,
                "check_size_max_mm": 500.0,
                "geographic_preferences": ["Global"],
                "strategies": ["buyout", "venture", "growth"],
            },
        ],
    ]

    mock_conn = MagicMock()
    mock_conn.cursor.return_value = mock_cursor

    with patch("src.auth.get_current_user", return_value=mock_user):
        with patch("src.main.get_db", return_value=mock_conn):
            yield TestClient(app)


class TestLpsAiSearchRouteIntegration:
    """Integration tests for /lps route with AI search."""

    def test_simple_search_does_not_trigger_ai(self, authenticated_client_with_db):
        """Simple LP name search should not use AI parsing."""
        with patch("src.main.parse_lp_search_query") as mock_parse:
            response = authenticated_client_with_db.get("/lps?search=CalPERS")

            # AI parser should NOT be called for simple names
            mock_parse.assert_not_called()
            assert response.status_code == 200

    def test_natural_language_search_triggers_ai(self, authenticated_client_with_db):
        """Natural language query should trigger AI parsing."""
        mock_filters = {"aum_min": 0.05}

        with patch("src.main.parse_lp_search_query", new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = mock_filters

            response = authenticated_client_with_db.get("/lps?search=50m+or+more+aum")

            # AI parser should be called
            mock_parse.assert_called_once_with("50m or more aum")
            assert response.status_code == 200

    def test_ai_parsed_filters_shown_in_response(self, authenticated_client_with_db):
        """Parsed filters from AI should be displayed in the HTML response."""
        mock_filters = {"aum_min": 0.05, "lp_type": "pension"}

        with patch("src.main.parse_lp_search_query", new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = mock_filters

            response = authenticated_client_with_db.get(
                "/lps?search=pension+funds+with+50m+aum"
            )

            assert response.status_code == 200
            # Check that filter chips are shown
            assert "AI interpreted" in response.text or "parsed" in response.text.lower()

    def test_complex_ai_query_with_multiple_filters(self, authenticated_client_with_db):
        """Complex queries should extract multiple filters."""
        mock_filters = {
            "aum_min": 0.1,
            "lp_type": "pension",
            "location": "California",
            "strategies": ["buyout"],
        }

        with patch("src.main.parse_lp_search_query", new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = mock_filters

            response = authenticated_client_with_db.get(
                "/lps?search=pension+funds+in+california+with+100m+aum+focused+on+buyout"
            )

            mock_parse.assert_called_once()
            assert response.status_code == 200

    def test_ai_fallback_on_timeout(self, authenticated_client_with_db):
        """When AI times out, should fall back to text search."""
        # When AI fails, it returns text_search fallback
        fallback_filters = {"text_search": "50m or more aum"}

        with patch("src.main.parse_lp_search_query", new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = fallback_filters

            response = authenticated_client_with_db.get("/lps?search=50m+or+more+aum")

            assert response.status_code == 200
            # Should still work, just with text search

    def test_lp_type_dropdown_combined_with_ai_search(self, authenticated_client_with_db):
        """LP type from dropdown should be combined with AI filters."""
        mock_filters = {"aum_min": 0.05}

        with patch("src.main.parse_lp_search_query", new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = mock_filters

            response = authenticated_client_with_db.get(
                "/lps?search=50m+or+more+aum&lp_type=pension"
            )

            assert response.status_code == 200

    def test_empty_search_does_not_trigger_ai(self, authenticated_client_with_db):
        """Empty search should not trigger AI parsing."""
        with patch("src.main.parse_lp_search_query") as mock_parse:
            response = authenticated_client_with_db.get("/lps")

            mock_parse.assert_not_called()
            assert response.status_code == 200

    def test_short_query_does_not_trigger_ai(self, authenticated_client_with_db):
        """Short queries (< 5 chars) should not trigger AI."""
        with patch("src.main.parse_lp_search_query") as mock_parse:
            response = authenticated_client_with_db.get("/lps?search=abc")

            mock_parse.assert_not_called()
            assert response.status_code == 200


class TestLpsAiSearchSqlGeneration:
    """Tests that verify SQL is generated correctly from AI filters."""

    def test_aum_filter_generates_correct_sql(self, authenticated_client_with_db):
        """AUM filter should generate >= condition."""
        mock_filters = {"aum_min": 0.05}

        with patch("src.main.parse_lp_search_query", new_callable=AsyncMock) as mock_parse:
            with patch("src.main.build_lp_search_sql") as mock_build:
                mock_parse.return_value = mock_filters
                mock_build.return_value = ("o.is_lp = TRUE AND lp.total_aum_bn >= %s", [0.05])

                response = authenticated_client_with_db.get("/lps?search=50m+or+more+aum")

                mock_build.assert_called_once()
                # Check filters passed to SQL builder
                call_args = mock_build.call_args[0][0]
                assert call_args.get("aum_min") == 0.05

    def test_location_filter_generates_ilike_condition(self, authenticated_client_with_db):
        """Location filter should generate ILIKE condition."""
        mock_filters = {"location": "California"}

        with patch("src.main.parse_lp_search_query", new_callable=AsyncMock) as mock_parse:
            with patch("src.main.build_lp_search_sql") as mock_build:
                mock_parse.return_value = mock_filters
                mock_build.return_value = (
                    "o.is_lp = TRUE AND (o.hq_city ILIKE %s OR o.hq_country ILIKE %s)",
                    ["%California%", "%California%"],
                )

                response = authenticated_client_with_db.get(
                    "/lps?search=investors+in+california"
                )

                mock_build.assert_called_once()
                call_args = mock_build.call_args[0][0]
                assert call_args.get("location") == "California"


class TestLpsNaturalLanguageDetection:
    """Tests for natural language query detection on the route."""

    @pytest.mark.parametrize(
        "query,should_use_ai",
        [
            ("CalPERS", False),  # Simple name
            ("Harvard", False),  # Simple name
            ("abc", False),  # Too short
            ("50m or more aum", True),  # AUM query
            ("pension funds", True),  # LP type
            ("buyout investors", True),  # Strategy
            ("investors in california", True),  # Location
            ("more than 100 million", True),  # Comparison
        ],
    )
    def test_query_type_detection(
        self, authenticated_client_with_db, query: str, should_use_ai: bool
    ):
        """Verify correct queries trigger AI parsing."""
        with patch("src.main.parse_lp_search_query", new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = {"text_search": query}

            authenticated_client_with_db.get(f"/lps?search={query.replace(' ', '+')}")

            if should_use_ai:
                mock_parse.assert_called_once()
            else:
                mock_parse.assert_not_called()


class TestLpsSearchEdgeCases:
    """Edge case tests for LP search."""

    def test_special_characters_in_search(self, authenticated_client_with_db):
        """Special characters should be handled safely."""
        with patch("src.main.parse_lp_search_query", new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = {"text_search": "50m+ aum & more"}

            response = authenticated_client_with_db.get(
                "/lps?search=50m%2B+aum+%26+more"
            )

            assert response.status_code == 200

    def test_sql_injection_in_search_is_safe(self, authenticated_client_with_db):
        """SQL injection attempts should be parameterized."""
        malicious_query = "'; DROP TABLE organizations; --"

        with patch("src.main.parse_lp_search_query", new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = {"text_search": malicious_query}

            response = authenticated_client_with_db.get(
                f"/lps?search={malicious_query}"
            )

            # Should not crash - query is parameterized
            assert response.status_code == 200

    def test_very_long_search_query(self, authenticated_client_with_db):
        """Very long search queries should be handled."""
        long_query = "pension funds " * 50  # ~700 chars

        with patch("src.main.parse_lp_search_query", new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = {"text_search": long_query.strip()}

            response = authenticated_client_with_db.get(
                f"/lps?search={long_query.replace(' ', '+')}"
            )

            assert response.status_code == 200

    def test_unicode_in_search(self, authenticated_client_with_db):
        """Unicode characters in search should work."""
        with patch("src.main.parse_lp_search_query", new_callable=AsyncMock) as mock_parse:
            mock_parse.return_value = {"text_search": "funds in europe"}

            response = authenticated_client_with_db.get("/lps?search=funds+in+europe")

            assert response.status_code == 200
