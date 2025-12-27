"""
Tests for ETL normalization functions.

These functions normalize raw data values to canonical forms for AI matching.
"""


from scripts.data_ingestion.transformers.enrich import (
    GEOGRAPHY_NORMALIZATION,
    STRATEGY_NORMALIZATION,
    calculate_acceptance_rate,
    normalize_fund_size,
    normalize_geographies,
    normalize_geography,
    normalize_sectors,
    normalize_strategies,
    normalize_strategy,
    parse_fund_size_to_mm,
    parse_geographic_preferences,
    parse_strategies,
)


class TestStrategyNormalization:
    """Test strategy normalization to canonical values."""

    def test_normalize_buyout_variations(self):
        """Different buyout spellings should normalize to 'buyout'."""
        assert normalize_strategy("Buyout") == "buyout"
        assert normalize_strategy("buyout") == "buyout"
        assert normalize_strategy("buyout-6") == "buyout"
        assert normalize_strategy("lbo") == "buyout"

    def test_normalize_venture_variations(self):
        """VC strategy variations should normalize correctly."""
        assert normalize_strategy("Seed / early stage") == "venture_seed"
        assert normalize_strategy("seed-early-stage-1") == "venture_seed"
        assert normalize_strategy("Late stage / growth") == "venture_growth"
        assert normalize_strategy("late-stage-growth-1") == "venture_growth"

    def test_normalize_debt_variations(self):
        """Private debt strategies should normalize correctly."""
        assert normalize_strategy("Direct lending") == "debt_direct"
        assert normalize_strategy("Mezzanine") == "debt_mezz"
        assert normalize_strategy("Special situations") == "debt_special"
        assert normalize_strategy("Specialty finance") == "debt_specialty"

    def test_normalize_real_assets(self):
        """Real asset strategies should normalize correctly."""
        assert normalize_strategy("Infrastructure") == "infra"
        assert normalize_strategy("infrastructure-4") == "infra"
        assert normalize_strategy("Real estate") == "real_estate"

    def test_normalize_unknown_returns_none(self):
        """Unknown strategies should return None."""
        assert normalize_strategy("unknown_strategy") is None
        assert normalize_strategy("") is None
        assert normalize_strategy(None) is None

    def test_normalize_strategies_list(self):
        """List of strategies should be normalized and deduplicated."""
        raw = ["Buyout", "buyout-6", "Seed / early stage", "unknown"]
        result = normalize_strategies(raw)
        assert result == ["buyout", "venture_seed"]  # Sorted, deduped

    def test_normalize_strategies_empty(self):
        """Empty list should return empty list."""
        assert normalize_strategies([]) == []

    def test_all_strategy_mappings_have_output(self):
        """Every mapped strategy should produce a non-empty canonical value."""
        for raw, canonical in STRATEGY_NORMALIZATION.items():
            assert canonical, f"Strategy '{raw}' maps to empty value"
            assert isinstance(canonical, str)


class TestGeographyNormalization:
    """Test geography normalization to regional buckets."""

    def test_normalize_western_europe(self):
        """Western European countries should normalize to europe_west."""
        assert normalize_geography("france") == "europe_west"
        assert normalize_geography("germany") == "europe_west"
        assert normalize_geography("uk") == "europe_west"
        assert normalize_geography("western_europe") == "europe_west"

    def test_normalize_eastern_europe(self):
        """Eastern European countries should normalize to europe_east."""
        assert normalize_geography("poland") == "europe_east"
        assert normalize_geography("central_eastern_europe") == "europe_east"
        assert normalize_geography("ukraine") == "europe_east"

    def test_normalize_north_america(self):
        """North American regions should normalize correctly."""
        assert normalize_geography("usa") == "north_america"
        assert normalize_geography("united_states") == "north_america"
        assert normalize_geography("canada") == "north_america"

    def test_normalize_asia_pacific(self):
        """Asia Pacific regions should normalize correctly."""
        assert normalize_geography("china") == "asia_pac"
        assert normalize_geography("japan") == "asia_pac"
        assert normalize_geography("asia_pacific") == "asia_pac"

    def test_normalize_global(self):
        """Global scope should normalize correctly."""
        assert normalize_geography("Global") == "global"
        assert normalize_geography("global") == "global"

    def test_normalize_geographies_list(self):
        """List of geographies should be normalized and deduplicated."""
        raw = ["france", "germany", "usa", "unknown_place"]
        result = normalize_geographies(raw)
        assert "europe_west" in result
        assert "north_america" in result
        assert len(result) == 2  # Deduped

    def test_all_geography_mappings_have_output(self):
        """Every mapped geography should produce a non-empty canonical value."""
        for raw, canonical in GEOGRAPHY_NORMALIZATION.items():
            assert canonical, f"Geography '{raw}' maps to empty value"


class TestFundSizeNormalization:
    """Test fund size category normalization."""

    def test_normalize_size_categories(self):
        """Fund size categories should normalize to buckets."""
        assert normalize_fund_size("Micro (0-€100m)") == "micro"
        assert normalize_fund_size("Small (€100m-€500m)") == "small"
        assert normalize_fund_size("Mid (€500m-€2bn)") == "mid"
        assert normalize_fund_size("Large (€2bn-€10bn)") == "large"
        assert normalize_fund_size("Mega (>€10bn)") == "mega"

    def test_normalize_size_slugs(self):
        """Size slugs from forms should normalize correctly."""
        assert normalize_fund_size("micro-0-eur100m-2") == "micro"
        assert normalize_fund_size("small-eur100m-eur500m-2") == "small"

    def test_normalize_unknown_size(self):
        """Unknown size should return None."""
        assert normalize_fund_size("Unknown") is None
        assert normalize_fund_size("") is None
        assert normalize_fund_size(None) is None

    def test_parse_size_to_mm(self):
        """Size categories should parse to midpoint in millions."""
        assert parse_fund_size_to_mm("Micro (0-€100m)") == 50
        assert parse_fund_size_to_mm("Small (€100m-€500m)") == 300
        assert parse_fund_size_to_mm("Mid (€500m-€2bn)") == 1250
        assert parse_fund_size_to_mm("Large (€2bn-€10bn)") == 6000
        assert parse_fund_size_to_mm("Mega (>€10bn)") == 15000

    def test_parse_size_to_mm_unknown(self):
        """Unknown size should return None."""
        assert parse_fund_size_to_mm("Unknown") is None


class TestSectorNormalization:
    """Test sector normalization."""

    def test_normalize_sectors(self):
        """Sectors should normalize to canonical values."""
        raw = ["Technology and software", "Healthcare", "Unknown Sector"]
        result = normalize_sectors(raw)
        assert "tech" in result
        assert "healthcare" in result
        assert len(result) == 2  # Unknown filtered out


class TestParsingFunctions:
    """Test parsing utility functions."""

    def test_parse_strategies_comma_separated(self):
        """Comma-separated strategies should parse to list."""
        raw = "Buyout, Growth, Venture"
        result = parse_strategies(raw)
        assert result == ["Buyout", "Growth", "Venture"]

    def test_parse_strategies_empty(self):
        """Empty string should return empty list."""
        assert parse_strategies("") == []
        assert parse_strategies(None) == []

    def test_parse_geographic_preferences_comma(self):
        """Comma-separated geos should parse to list."""
        raw = "france, germany, usa"
        result = parse_geographic_preferences(raw)
        assert result == ["france", "germany", "usa"]

    def test_parse_geographic_preferences_pipe(self):
        """Pipe-separated geos should parse to list."""
        raw = "france|germany|usa"
        result = parse_geographic_preferences(raw)
        assert result == ["france", "germany", "usa"]


class TestBehavioralMetrics:
    """Test behavioral metric calculations."""

    def test_calculate_acceptance_rate(self):
        """Acceptance rate should be calculated correctly."""
        assert calculate_acceptance_rate(100, 10) == 0.1
        assert calculate_acceptance_rate(1000, 93) == 0.093
        assert calculate_acceptance_rate(50, 25) == 0.5

    def test_acceptance_rate_zero_received(self):
        """Zero received should return None."""
        assert calculate_acceptance_rate(0, 0) is None
        assert calculate_acceptance_rate(0, 10) is None

    def test_acceptance_rate_rounding(self):
        """Rate should be rounded to 3 decimal places."""
        rate = calculate_acceptance_rate(3, 1)
        assert rate == 0.333
