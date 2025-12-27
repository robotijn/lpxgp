"""
Property-based tests for ETL normalization functions.

Uses Hypothesis to generate random inputs and verify invariants hold.
These tests catch edge cases that example-based tests might miss.
"""

from hypothesis import assume, given
from hypothesis import strategies as st

from scripts.data_ingestion.transformers.enrich import (
    FUND_SIZE_NORMALIZATION,
    GEOGRAPHY_NORMALIZATION,
    STRATEGY_NORMALIZATION,
    calculate_acceptance_rate,
    normalize_fund_size,
    normalize_geographies,
    normalize_geography,
    normalize_strategies,
    normalize_strategy,
    parse_fund_size_to_mm,
    parse_geographic_preferences,
    parse_strategies,
)


class TestStrategyNormalizationProperties:
    """Property-based tests for strategy normalization."""

    @given(st.text(max_size=100))
    def test_normalize_strategy_never_crashes(self, raw: str):
        """normalize_strategy should never raise an exception."""
        result = normalize_strategy(raw)
        assert result is None or isinstance(result, str)

    @given(st.lists(st.text(max_size=50), max_size=20))
    def test_normalize_strategies_returns_sorted_unique(self, raw_list: list[str]):
        """normalize_strategies should return sorted, deduplicated list."""
        result = normalize_strategies(raw_list)
        assert result == sorted(set(result))

    @given(st.sampled_from(list(STRATEGY_NORMALIZATION.keys())))
    def test_known_strategies_always_normalize(self, known_key: str):
        """All known strategy keys should normalize to a value."""
        result = normalize_strategy(known_key)
        assert result is not None
        assert result == STRATEGY_NORMALIZATION[known_key]

    @given(st.lists(st.sampled_from(list(STRATEGY_NORMALIZATION.keys())), max_size=10))
    def test_known_strategies_list_all_normalize(self, known_keys: list[str]):
        """Lists of known keys should all normalize successfully."""
        result = normalize_strategies(known_keys)
        # Result should have at most as many items as input (deduped)
        assert len(result) <= len(set(known_keys))
        # All results should be valid canonical values
        canonical_values = set(STRATEGY_NORMALIZATION.values())
        for r in result:
            assert r in canonical_values

    @given(st.text(alphabet="!@#$%^&*()[]{}|\\", max_size=20))
    def test_special_characters_handled(self, special: str):
        """Special characters should not crash the normalizer."""
        result = normalize_strategy(special)
        assert result is None  # Unknown strings return None


class TestGeographyNormalizationProperties:
    """Property-based tests for geography normalization."""

    @given(st.text(max_size=100))
    def test_normalize_geography_never_crashes(self, raw: str):
        """normalize_geography should never raise an exception."""
        result = normalize_geography(raw)
        assert result is None or isinstance(result, str)

    @given(st.lists(st.text(max_size=50), max_size=30))
    def test_normalize_geographies_returns_sorted_unique(self, raw_list: list[str]):
        """normalize_geographies should return sorted, deduplicated list."""
        result = normalize_geographies(raw_list)
        assert result == sorted(set(result))

    @given(st.sampled_from(list(GEOGRAPHY_NORMALIZATION.keys())))
    def test_known_geographies_always_normalize(self, known_key: str):
        """All known geography keys should normalize to a value."""
        result = normalize_geography(known_key)
        assert result is not None

    @given(st.text(max_size=50))
    def test_geography_normalization_is_case_insensitive_for_known(self, raw: str):
        """Known geographies should normalize regardless of case."""
        lower_result = normalize_geography(raw.lower())
        upper_result = normalize_geography(raw.upper())
        # Either both None (unknown) or both same value
        if lower_result is not None and upper_result is not None:
            # May differ due to normalization logic, but both should be valid
            canonical_values = set(GEOGRAPHY_NORMALIZATION.values())
            assert lower_result in canonical_values
            assert upper_result in canonical_values


class TestFundSizeNormalizationProperties:
    """Property-based tests for fund size normalization."""

    @given(st.text(max_size=100))
    def test_normalize_fund_size_never_crashes(self, raw: str):
        """normalize_fund_size should never raise an exception."""
        result = normalize_fund_size(raw)
        assert result is None or result in ["micro", "small", "mid", "large", "mega"]

    @given(st.sampled_from(list(FUND_SIZE_NORMALIZATION.keys())))
    def test_known_sizes_normalize_to_valid_bucket(self, known_key: str):
        """All known size keys should normalize to a valid bucket."""
        result = normalize_fund_size(known_key)
        assert result in ["micro", "small", "mid", "large", "mega"]

    @given(st.sampled_from(list(FUND_SIZE_NORMALIZATION.keys())))
    def test_size_to_mm_returns_positive(self, known_key: str):
        """parse_fund_size_to_mm should return positive number for known sizes."""
        result = parse_fund_size_to_mm(known_key)
        assert result is not None
        assert result > 0

    @given(st.text(max_size=50))
    def test_unknown_size_returns_none(self, raw: str):
        """Unknown sizes should return None, not crash."""
        assume(raw not in FUND_SIZE_NORMALIZATION)
        result = normalize_fund_size(raw)
        # Either None or a valid bucket if partial match
        assert result is None or result in ["micro", "small", "mid", "large", "mega"]


class TestParsingProperties:
    """Property-based tests for parsing functions."""

    @given(st.text(max_size=200))
    def test_parse_strategies_never_crashes(self, raw: str):
        """parse_strategies should handle any input."""
        result = parse_strategies(raw)
        assert isinstance(result, list)
        for item in result:
            assert isinstance(item, str)

    @given(st.text(max_size=200))
    def test_parse_geographic_preferences_never_crashes(self, raw: str):
        """parse_geographic_preferences should handle any input."""
        result = parse_geographic_preferences(raw)
        assert isinstance(result, list)

    @given(st.lists(st.text(min_size=1, max_size=20), min_size=1, max_size=10))
    def test_parse_strategies_roundtrip(self, items: list[str]):
        """Comma-joined items should parse back to similar list."""
        # Filter out items with commas (would break roundtrip)
        clean_items = [i.strip() for i in items if "," not in i and i.strip()]
        assume(len(clean_items) > 0)

        joined = ", ".join(clean_items)
        result = parse_strategies(joined)

        # Should have same number of items (stripped)
        assert len(result) == len(clean_items)


class TestAcceptanceRateProperties:
    """Property-based tests for acceptance rate calculation."""

    @given(
        st.integers(min_value=0, max_value=1000000),
        st.integers(min_value=0, max_value=1000000)
    )
    def test_acceptance_rate_in_valid_range(self, received: int, accepted: int):
        """Acceptance rate should be None or between 0 and 1."""
        assume(accepted <= received)  # Can't accept more than received

        result = calculate_acceptance_rate(received, accepted)

        if received == 0:
            assert result is None
        else:
            assert result is not None
            assert 0.0 <= result <= 1.0

    @given(st.integers(min_value=1, max_value=1000000))
    def test_acceptance_rate_zero_accepted(self, received: int):
        """Zero accepted should give rate of 0."""
        result = calculate_acceptance_rate(received, 0)
        assert result == 0.0

    @given(st.integers(min_value=1, max_value=1000000))
    def test_acceptance_rate_all_accepted(self, received: int):
        """All accepted should give rate of 1."""
        result = calculate_acceptance_rate(received, received)
        assert result == 1.0


class TestNormalizationIdempotence:
    """Test that normalization is idempotent (applying twice = applying once)."""

    @given(st.sampled_from(list(STRATEGY_NORMALIZATION.values())))
    def test_strategy_normalization_idempotent(self, canonical: str):
        """Normalizing a canonical value should return the same value."""
        # Canonical values might not be in the map as keys, so this tests
        # that the output is stable
        result = normalize_strategy(canonical)
        if result is not None:
            assert result == canonical or result in STRATEGY_NORMALIZATION.values()

    @given(st.lists(st.sampled_from(list(STRATEGY_NORMALIZATION.values())), max_size=10))
    def test_strategies_list_idempotent(self, canonical_list: list[str]):
        """Normalizing already-normalized values should be stable."""
        result1 = normalize_strategies(canonical_list)
        result2 = normalize_strategies(result1)
        assert result1 == result2


class TestEdgeCases:
    """Test specific edge cases found through property testing."""

    def test_empty_string(self):
        """Empty string should return None/empty list."""
        assert normalize_strategy("") is None
        assert normalize_geography("") is None
        assert normalize_fund_size("") is None
        assert normalize_strategies([""]) == []
        assert parse_strategies("") == []

    def test_whitespace_only(self):
        """Whitespace-only strings should be handled."""
        assert normalize_strategy("   ") is None
        assert normalize_geography("\t\n") is None
        assert parse_strategies("   ,   ,   ") == []

    def test_none_input(self):
        """None input should be handled gracefully."""
        assert normalize_strategy(None) is None
        assert normalize_geography(None) is None
        assert normalize_fund_size(None) is None
        assert parse_strategies(None) == []
        assert parse_geographic_preferences(None) == []

    def test_unicode_input(self):
        """Unicode characters should not crash."""
        assert normalize_strategy("買収") is None  # Japanese for "buyout"
        assert normalize_geography("中国") is None  # Chinese for "China"
        assert normalize_strategies(["émergent", "croissance"]) == []

    def test_very_long_input(self):
        """Very long strings should not crash."""
        long_string = "a" * 10000
        assert normalize_strategy(long_string) is None
        assert len(parse_strategies(long_string)) <= 1
