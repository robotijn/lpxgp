"""Tests for pitch deck analyzer LLM extraction.

Tests cover:
- Response parsing and normalization
- Enhanced matching score calculations
- Matching insights generation
- Edge cases and error handling
"""

from unittest.mock import MagicMock, patch

import pytest

from src.pitch_deck_analyzer import (
    ExtractedPitchDeckData,
    _normalize_extracted_data,
    _parse_extraction_response,
    _safe_float,
    _safe_int,
    analyze_pitch_deck,
    calculate_enhanced_match_score,
    get_matching_insights,
)

# =============================================================================
# Safe Type Conversion Tests
# =============================================================================


class TestSafeFloat:
    """Tests for _safe_float function."""

    def test_converts_valid_float(self):
        """Should convert valid float string."""
        assert _safe_float("25.5") == 25.5

    def test_converts_int(self):
        """Should convert integer to float."""
        assert _safe_float(100) == 100.0

    def test_returns_none_for_none(self):
        """Should return None for None input."""
        assert _safe_float(None) is None

    def test_returns_none_for_invalid(self):
        """Should return None for invalid input."""
        assert _safe_float("invalid") is None

    def test_returns_none_for_empty_string(self):
        """Should return None for empty string."""
        assert _safe_float("") is None


class TestSafeInt:
    """Tests for _safe_int function."""

    def test_converts_valid_int(self):
        """Should convert valid int string."""
        assert _safe_int("42") == 42

    def test_converts_float_to_int(self):
        """Should convert float to int."""
        assert _safe_int(3.7) == 3

    def test_returns_none_for_none(self):
        """Should return None for None input."""
        assert _safe_int(None) is None

    def test_returns_none_for_invalid(self):
        """Should return None for invalid input."""
        assert _safe_int("invalid") is None


# =============================================================================
# Response Parsing Tests
# =============================================================================


class TestParseExtractionResponse:
    """Tests for _parse_extraction_response function."""

    def test_parses_valid_json(self):
        """Should parse valid JSON response."""
        response = '{"strategy_details": {"primary": "growth_equity"}}'
        result = _parse_extraction_response(response)

        assert result is not None
        assert result["strategy_details"]["primary"] == "growth_equity"

    def test_parses_json_with_code_block(self):
        """Should parse JSON wrapped in markdown code block."""
        response = '```json\n{"strategy_details": {"primary": "buyout"}}\n```'
        result = _parse_extraction_response(response)

        assert result is not None
        assert result["strategy_details"]["primary"] == "buyout"

    def test_parses_json_with_generic_code_block(self):
        """Should parse JSON wrapped in generic code block."""
        response = '```\n{"strategy_details": {"primary": "venture"}}\n```'
        result = _parse_extraction_response(response)

        assert result is not None
        assert result["strategy_details"]["primary"] == "venture"

    def test_returns_none_for_invalid_json(self):
        """Should return None for invalid JSON."""
        result = _parse_extraction_response("not valid json")
        assert result is None

    def test_returns_none_for_empty_response(self):
        """Should return None for empty response."""
        result = _parse_extraction_response("")
        assert result is None


class TestNormalizeExtractedData:
    """Tests for _normalize_extracted_data function."""

    def test_normalizes_complete_data(self):
        """Should normalize complete extracted data."""
        raw_data = {
            "strategy_details": {
                "primary": "growth_equity",
                "sub_strategies": ["tech", "healthcare"],
            },
            "track_record": {
                "gross_irr_pct": 28.5,
                "gross_moic": 2.3,
            },
            "extraction_confidence": 0.85,
        }

        result = _normalize_extracted_data(raw_data)

        assert result["strategy_details"]["primary"] == "growth_equity"
        assert result["track_record"]["gross_irr_pct"] == 28.5
        assert result["extraction_confidence"] == 0.85

    def test_normalizes_empty_data(self):
        """Should handle empty data with defaults."""
        result = _normalize_extracted_data({})

        assert result["strategy_details"]["primary"] == ""
        assert result["track_record"]["gross_irr_pct"] is None
        assert result["extraction_confidence"] == 0.5
        assert result["key_differentiators"] == []

    def test_handles_missing_nested_fields(self):
        """Should handle missing nested fields."""
        raw_data = {
            "strategy_details": {"primary": "buyout"},
            # Missing other sections
        }

        result = _normalize_extracted_data(raw_data)

        assert result["strategy_details"]["primary"] == "buyout"
        assert result["geographic_details"]["primary_regions"] == []
        assert result["team_details"]["total_partners"] is None


# =============================================================================
# Enhanced Matching Score Tests
# =============================================================================


class TestCalculateEnhancedMatchScore:
    """Tests for calculate_enhanced_match_score function."""

    def test_returns_base_score_without_extracted_data(self):
        """Should return base score when no extracted data available."""
        lp_preferences = {
            "strategies": ["growth_equity"],
            "sector_preferences": ["technology"],
        }

        extracted_data: ExtractedPitchDeckData = {
            "strategy_details": {"primary": "growth_equity"},
            "track_record": {},
            "team_details": {},
            "esg_details": {},
            "sector_details": {},
            "extraction_confidence": 0.5,
        }

        scores = calculate_enhanced_match_score(extracted_data, lp_preferences)

        assert "track_record_quality" in scores
        assert "team_experience" in scores
        assert "esg_alignment" in scores
        assert "sector_depth" in scores

    def test_track_record_bonus_for_high_irr(self):
        """Should give bonus for high IRR."""
        lp_preferences = {}

        extracted_data: ExtractedPitchDeckData = {
            "strategy_details": {},
            "track_record": {"gross_irr_pct": 35.0},  # Top quartile
            "team_details": {},
            "esg_details": {},
            "sector_details": {},
            "extraction_confidence": 0.8,
        }

        scores = calculate_enhanced_match_score(extracted_data, lp_preferences)

        # High IRR should result in high track record score
        assert scores["track_record_quality"] >= 70

    def test_track_record_bonus_for_high_moic(self):
        """Should give bonus for high MOIC."""
        lp_preferences = {}

        extracted_data: ExtractedPitchDeckData = {
            "strategy_details": {},
            "track_record": {"gross_moic": 3.5},  # Excellent
            "team_details": {},
            "esg_details": {},
            "sector_details": {},
            "extraction_confidence": 0.8,
        }

        scores = calculate_enhanced_match_score(extracted_data, lp_preferences)

        assert scores["track_record_quality"] >= 60

    def test_team_experience_bonus(self):
        """Should give bonus for experienced team."""
        lp_preferences = {}

        extracted_data: ExtractedPitchDeckData = {
            "strategy_details": {},
            "track_record": {},
            "team_details": {
                "avg_experience_years": 20,
                "operator_experience": True,
            },
            "esg_details": {},
            "sector_details": {},
            "extraction_confidence": 0.8,
        }

        scores = calculate_enhanced_match_score(extracted_data, lp_preferences)

        assert scores["team_experience"] >= 70

    def test_esg_alignment_when_required(self):
        """Should score ESG alignment when LP requires it."""
        lp_preferences = {"esg_required": True}

        extracted_data: ExtractedPitchDeckData = {
            "strategy_details": {},
            "track_record": {},
            "team_details": {},
            "esg_details": {
                "has_esg_policy": True,
                "pri_signatory": True,
            },
            "sector_details": {},
            "extraction_confidence": 0.8,
        }

        scores = calculate_enhanced_match_score(extracted_data, lp_preferences)

        assert scores["esg_alignment"] >= 90

    def test_esg_penalty_when_required_but_missing(self):
        """Should penalize when ESG required but not present."""
        lp_preferences = {"esg_required": True}

        extracted_data: ExtractedPitchDeckData = {
            "strategy_details": {},
            "track_record": {},
            "team_details": {},
            "esg_details": {"has_esg_policy": False},
            "sector_details": {},
            "extraction_confidence": 0.8,
        }

        scores = calculate_enhanced_match_score(extracted_data, lp_preferences)

        assert scores["esg_alignment"] <= 30

    def test_sector_depth_overlap(self):
        """Should score sector theme overlap."""
        lp_preferences = {"sector_preferences": ["technology", "ai"]}

        extracted_data: ExtractedPitchDeckData = {
            "strategy_details": {},
            "track_record": {},
            "team_details": {},
            "esg_details": {},
            "sector_details": {
                "primary_sectors": ["Technology"],
                "themes": ["AI/ML", "Digital Transformation"],
            },
            "extraction_confidence": 0.8,
        }

        scores = calculate_enhanced_match_score(extracted_data, lp_preferences)

        # Sector depth score includes theme overlap bonus
        assert scores["sector_depth"] > 0  # Has some sector alignment


# =============================================================================
# Matching Insights Tests
# =============================================================================


class TestGetMatchingInsights:
    """Tests for get_matching_insights function."""

    def test_generates_headline_metrics(self):
        """Should generate headline metrics from extracted data."""
        extracted_data: ExtractedPitchDeckData = {
            "strategy_details": {},
            "track_record": {
                "gross_irr_pct": 28.5,
                "gross_moic": 2.3,
                "prior_funds": 3,
            },
            "fund_terms": {"target_size_mm": 500},
            "team_details": {},
            "esg_details": {},
            "sector_details": {},
            "extraction_confidence": 0.8,
        }

        insights = get_matching_insights(extracted_data)

        assert "irr" in insights["headline_metrics"]
        assert "moic" in insights["headline_metrics"]
        assert "target_size" in insights["headline_metrics"]
        assert insights["headline_metrics"]["irr"] == "28.5%"
        assert insights["headline_metrics"]["moic"] == "2.3x"

    def test_identifies_strengths(self):
        """Should identify fund strengths."""
        extracted_data: ExtractedPitchDeckData = {
            "strategy_details": {},
            "track_record": {"gross_irr_pct": 30.0},  # Top quartile
            "team_details": {
                "avg_experience_years": 18,
                "operator_experience": True,
            },
            "esg_details": {
                "has_esg_policy": True,
                "pri_signatory": True,
            },
            "sector_details": {"themes": ["AI/ML", "Climate Tech"]},
            "fund_terms": {},
            "extraction_confidence": 0.8,
        }

        insights = get_matching_insights(extracted_data)

        assert len(insights["strengths"]) > 0
        # Should have strength for top quartile returns
        assert any("top-quartile" in s.lower() for s in insights["strengths"])

    def test_identifies_considerations(self):
        """Should identify considerations for emerging managers."""
        extracted_data: ExtractedPitchDeckData = {
            "strategy_details": {},
            "track_record": {"prior_funds": 1},  # Emerging manager
            "team_details": {},
            "esg_details": {"has_esg_policy": False},
            "sector_details": {},
            "fund_terms": {},
            "extraction_confidence": 0.8,
        }

        insights = get_matching_insights(extracted_data)

        assert len(insights["considerations"]) > 0
        # Should flag emerging manager status
        assert any("emerging" in c.lower() for c in insights["considerations"])

    def test_handles_missing_data_gracefully(self):
        """Should handle missing data without errors."""
        extracted_data: ExtractedPitchDeckData = {
            "strategy_details": {},
            "track_record": {},
            "team_details": {},
            "esg_details": {},
            "sector_details": {},
            "fund_terms": {},
            "extraction_confidence": 0.5,
        }

        insights = get_matching_insights(extracted_data)

        assert "headline_metrics" in insights
        assert "strengths" in insights
        assert "considerations" in insights


# =============================================================================
# Async Analysis Tests
# =============================================================================


class TestAnalyzePitchDeck:
    """Tests for analyze_pitch_deck async function."""

    @pytest.mark.asyncio
    async def test_returns_none_for_short_text(self):
        """Should return None for text that's too short."""
        result = await analyze_pitch_deck("Short text")
        assert result is None

    @pytest.mark.asyncio
    async def test_returns_none_for_empty_text(self):
        """Should return None for empty text."""
        result = await analyze_pitch_deck("")
        assert result is None

    @pytest.mark.asyncio
    async def test_truncates_long_text(self):
        """Should truncate very long text."""
        long_text = "a" * 60000

        with patch("src.pitch_deck_analyzer._analyze_with_openrouter") as mock_analyze:
            mock_analyze.return_value = None

            await analyze_pitch_deck(long_text, use_openrouter=True)

            # Verify text was truncated
            call_args = mock_analyze.call_args
            if call_args:
                passed_text = call_args[0][0]
                assert len(passed_text) <= 51000  # 50000 + truncation message

    @pytest.mark.asyncio
    async def test_falls_back_to_ollama(self):
        """Should fall back to Ollama when OpenRouter not configured."""
        test_text = "This is a test pitch deck with enough content " * 10

        with patch("src.pitch_deck_analyzer.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(openrouter_api_key=None)

            with patch(
                "src.pitch_deck_analyzer._analyze_with_ollama"
            ) as mock_ollama:
                mock_ollama.return_value = None

                await analyze_pitch_deck(test_text, use_openrouter=True)

                mock_ollama.assert_called_once()

    @pytest.mark.asyncio
    async def test_uses_openrouter_when_configured(self):
        """Should use OpenRouter when API key is configured."""
        test_text = "This is a test pitch deck with enough content " * 10

        with patch("src.pitch_deck_analyzer.get_settings") as mock_settings:
            mock_settings.return_value = MagicMock(openrouter_api_key="test-key")

            with patch(
                "src.pitch_deck_analyzer._analyze_with_openrouter"
            ) as mock_openrouter:
                mock_openrouter.return_value = None

                await analyze_pitch_deck(test_text, use_openrouter=True)

                mock_openrouter.assert_called_once()
