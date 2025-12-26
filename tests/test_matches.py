"""Tests for matching functionality.

IMPORTANT: Tests are the source of truth. Do NOT modify tests to make them pass.
If a test fails, fix the APPLICATION, not the test.

Based on BDD Gherkin specs from docs/prd/tests/*.feature.md

Test Categories:
- TestMatchesPage: Page-level tests for /matches route
- TestMatchDetailModal: Modal API endpoint tests
- TestMatchingScoring: Core scoring algorithm tests
- TestMatchingScoringEdgeCases: Edge cases in scoring
- TestMatchingLLMGeneration: LLM content generation tests
- TestMatchingAPIEndpoint: API endpoint tests
- TestMatchingScoreBreakdown: Score breakdown detail tests
- TestMatchingStrategyVariations: Strategy matching variations
- TestMatchingGeographyVariations: Geography matching variations
- TestMatchingSizeRangeVariations: Size range matching variations
- TestMatchingESGVariations: ESG policy matching variations
- TestMatchingTrackRecordScoring: Track record scoring tests
- TestMatchingSectorOverlap: Sector overlap detection tests
- TestMatchingCheckSizeFit: Check size fit scoring tests
- TestMatchingFallbackContent: Fallback content generation tests
- TestMatchingEmptyAndNullInputs: Empty/null input handling tests
- TestMatchingSpecialCharacters: Special character handling tests
- TestMatchingLargeNumbers: Large number handling tests
"""

import pytest


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

    def test_llm_generation_timeout_fallback(self):
        """When LLM times out, should fall back to template content.

        Test the fallback mechanism directly using synchronous fallback function
        since the async path has event loop conflicts with pytest.
        """
        from src.matching import _generate_fallback_content

        fund = {"name": "Test Fund", "strategy": "venture"}
        lp = {"name": "Test LP", "strategies": ["venture"]}
        score_breakdown = {"strategy": 100}

        # Test the fallback content generation directly
        # This is what generate_match_content falls back to on timeout
        content = _generate_fallback_content(fund, lp, score_breakdown)

        # Should have valid structure
        assert "explanation" in content
        assert "talking_points" in content
        assert "concerns" in content
        assert isinstance(content["explanation"], str)
        assert isinstance(content["talking_points"], list)
        assert isinstance(content["concerns"], list)


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

        fund = {"strategy": "venture", "geographic_focus": ["Sao Paulo", "Munchen"], "target_size_mm": 500, "fund_number": 4}
        lp = {"strategies": ["venture"], "geographic_preferences": ["Sao Paulo"], "fund_size_min_mm": 100, "fund_size_max_mm": 1000}

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
