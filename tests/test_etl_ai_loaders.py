"""
Tests for AI profile loaders.

These loaders populate the fund_ai_profiles and lp_ai_profiles tables
used ONLY by AI matching algorithms - never for client display.
"""

import pytest
from unittest.mock import MagicMock, patch

from scripts.data_ingestion.loaders.ai_profiles import (
    load_fund_ai_profiles,
    load_lp_ai_profiles,
    _calculate_completeness,
    _calculate_engagement,
    _determine_data_sources,
    _calculate_confidence,
)
from scripts.data_ingestion.config import SyncStats


class TestFundAIProfileLoader:
    """Test fund AI profile loading."""

    def test_load_fund_ai_profiles_dry_run(self):
        """Dry run should count records without database writes."""
        records = [
            {
                "fund_id": "uuid-1",
                "ai_strategy_tags": ["buyout", "growth"],
                "ai_geography_tags": ["europe_west"],
                "ai_sector_tags": ["tech"],
                "ai_size_bucket": "small",
                "ai_size_mm": 300,
                "ai_has_esg": True,
                "investment_thesis": "A growth equity fund",
            },
            {
                "fund_id": "uuid-2",
                "ai_strategy_tags": ["venture_seed"],
                "ai_geography_tags": ["north_america"],
                "ai_sector_tags": [],
                "ai_size_bucket": "micro",
                "ai_size_mm": 50,
                "ai_has_esg": False,
                "investment_thesis": "",
            },
        ]

        stats = load_fund_ai_profiles(
            client=None,
            records=iter(records),
            dry_run=True,
        )

        assert stats.created == 2
        assert stats.skipped == 0
        assert len(stats.errors) == 0

    def test_load_fund_ai_profiles_skips_missing_fund_id(self):
        """Records without fund_id should be skipped."""
        records = [
            {"ai_strategy_tags": ["buyout"]},  # No fund_id
            {"fund_id": "", "ai_strategy_tags": ["growth"]},  # Empty fund_id
            {"fund_id": "uuid-1", "ai_strategy_tags": ["venture_seed"]},  # Valid
        ]

        stats = load_fund_ai_profiles(
            client=None,
            records=iter(records),
            dry_run=True,
        )

        assert stats.created == 1
        assert stats.skipped == 2

    def test_calculate_completeness(self):
        """Completeness score should reflect filled fields."""
        # All fields filled
        full_record = {
            "ai_strategy_tags": ["buyout"],
            "ai_geography_tags": ["europe"],
            "ai_sector_tags": ["tech"],
            "ai_size_bucket": "small",
            "investment_thesis": "A fund thesis",
        }
        assert _calculate_completeness(full_record) == 1.0

        # No fields filled
        empty_record = {}
        assert _calculate_completeness(empty_record) == 0.0

        # Partial (3 of 5)
        partial_record = {
            "ai_strategy_tags": ["buyout"],
            "ai_geography_tags": ["europe"],
            "investment_thesis": "thesis",
        }
        assert _calculate_completeness(partial_record) == 0.6


class TestLPAIProfileLoader:
    """Test LP AI profile loading."""

    def test_load_lp_ai_profiles_dry_run(self):
        """Dry run should count records without database writes."""
        records = [
            {
                "lp_profile_id": "lp-uuid-1",
                "org_id": "org-uuid-1",
                "ai_strategy_interests": ["buyout"],
                "ai_geography_interests": ["europe_west"],
                "solicitations_received": 100,
                "solicitations_accepted": 10,
            },
        ]

        stats = load_lp_ai_profiles(
            client=None,
            records=iter(records),
            dry_run=True,
        )

        assert stats.created == 1
        assert stats.skipped == 0

    def test_load_lp_ai_profiles_skips_missing_ids(self):
        """Records without lp_profile_id or org_id should be skipped."""
        records = [
            {"org_id": "org-1"},  # No lp_profile_id
            {"lp_profile_id": "lp-1"},  # No org_id
            {"lp_profile_id": "lp-2", "org_id": "org-2"},  # Valid
        ]

        stats = load_lp_ai_profiles(
            client=None,
            records=iter(records),
            dry_run=True,
        )

        assert stats.created == 1
        assert stats.skipped == 2


class TestEngagementCalculations:
    """Test LP engagement score calculations."""

    def test_calculate_engagement_high(self):
        """High engagement: good acceptance rate + volume."""
        record = {
            "solicitations_received": 100,
            "solicitations_accepted": 30,
        }
        acceptance_rate = 0.3

        score = _calculate_engagement(record, acceptance_rate)
        assert score >= 0.5  # High engagement

    def test_calculate_engagement_low(self):
        """Low engagement: low acceptance rate + low volume."""
        record = {
            "solicitations_received": 5,
            "solicitations_accepted": 0,
        }
        acceptance_rate = 0.0

        score = _calculate_engagement(record, acceptance_rate)
        assert score <= 0.2  # Low engagement

    def test_calculate_engagement_no_data(self):
        """No data should give low score."""
        record = {}
        score = _calculate_engagement(record, None)
        assert score == 0.0

    def test_calculate_engagement_capped_at_one(self):
        """Score should never exceed 1.0."""
        record = {
            "solicitations_received": 1000,
            "solicitations_accepted": 500,
        }
        acceptance_rate = 0.5

        score = _calculate_engagement(record, acceptance_rate)
        assert score <= 1.0


class TestDataSourceDetermination:
    """Test data source classification."""

    def test_determine_sources_explicit(self):
        """Records with explicit preferences should be tagged."""
        record = {
            "ai_strategy_interests": ["buyout", "growth"],
        }
        sources = _determine_data_sources(record)
        assert "explicit" in sources

    def test_determine_sources_behavioral(self):
        """Records with behavioral data should be tagged."""
        record = {
            "solicitations_received": 50,
        }
        sources = _determine_data_sources(record)
        assert "behavioral" in sources

    def test_determine_sources_inferred(self):
        """Records with ML-inferred data should be tagged."""
        record = {
            "inferred_strategy_probs": {"buyout": 0.8},
        }
        sources = _determine_data_sources(record)
        assert "inferred" in sources

    def test_determine_sources_unknown(self):
        """Empty records should be tagged as unknown."""
        record = {}
        sources = _determine_data_sources(record)
        assert sources == ["unknown"]

    def test_determine_sources_multiple(self):
        """Records can have multiple source types."""
        record = {
            "ai_strategy_interests": ["buyout"],
            "solicitations_received": 100,
            "inferred_strategy_probs": {"buyout": 0.9},
        }
        sources = _determine_data_sources(record)
        assert "explicit" in sources
        assert "behavioral" in sources
        assert "inferred" in sources


class TestConfidenceScore:
    """Test confidence score calculation."""

    def test_confidence_high(self):
        """High confidence with explicit prefs + behavioral data."""
        record = {
            "ai_strategy_interests": ["buyout"],
            "ai_geography_interests": ["europe"],
            "solicitations_received": 100,
            "check_size_min_mm": 5.0,
        }
        score = _calculate_confidence(record)
        assert score >= 0.8

    def test_confidence_low(self):
        """Low confidence with minimal data."""
        record = {
            "solicitations_received": 3,
        }
        score = _calculate_confidence(record)
        assert score <= 0.3

    def test_confidence_capped_at_one(self):
        """Confidence should never exceed 1.0."""
        record = {
            "ai_strategy_interests": ["buyout"],
            "ai_geography_interests": ["europe"],
            "ai_sector_interests": ["tech"],
            "solicitations_received": 500,
            "check_size_min_mm": 10.0,
            "ai_size_preferences": ["small"],
        }
        score = _calculate_confidence(record)
        assert score <= 1.0


class TestDatabaseIntegration:
    """Test database operations (mocked)."""

    def test_fund_ai_upsert_success(self):
        """Successful upsert should increment created count."""
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.data = [{"id": "new-id"}]
        mock_client.table.return_value.upsert.return_value.execute.return_value = mock_response

        records = [
            {
                "fund_id": "uuid-1",
                "ai_strategy_tags": ["buyout"],
            },
        ]

        stats = load_fund_ai_profiles(
            client=mock_client,
            records=iter(records),
            dry_run=False,
        )

        assert stats.created == 1
        mock_client.table.assert_called_with("fund_ai_profiles")

    def test_fund_ai_upsert_error(self):
        """Database errors should be captured in stats."""
        mock_client = MagicMock()
        mock_client.table.return_value.upsert.return_value.execute.side_effect = Exception("DB error")

        records = [
            {
                "fund_id": "uuid-1",
                "ai_strategy_tags": ["buyout"],
            },
        ]

        stats = load_fund_ai_profiles(
            client=mock_client,
            records=iter(records),
            dry_run=False,
        )

        assert stats.created == 0
        assert len(stats.errors) == 1
        assert "DB error" in stats.errors[0]["error"]
