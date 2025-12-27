"""
Tests for LP ETL pipeline.

Tests the LP extractor (lps.py) and loader (lp_profiles.py).
"""

from pathlib import Path

import pytest

from scripts.data_ingestion.extractors.lps import (
    _calculate_engagement_score,
    _infer_geography_from_country,
    _infer_lp_type,
    _parse_int,
    extract_lps,
)
from scripts.data_ingestion.loaders.lp_profiles import (
    load_lp_profiles,
)


class TestLPExtractor:
    """Tests for LP data extraction from lp_matchmaking.csv."""

    def test_extract_lps_basic(self, tmp_path):
        """Extract basic LP data from CSV."""
        csv_file = tmp_path / "lp_matchmaking.csv"
        csv_file.write_text(
            "organization_id,organization_name,country_name,lp_user_id,title,first_name,last_name,email,telephoneFixe,telephonePort,is_participating_at_paris_2025,solicitations_received,solicitations_accepted,solicitations_declined,lastlogin_at,lastactivity_at\n"
            "1001,Test Family Office,France,100,mr,Jean,Dupont,jean@test.com,+33123,+33456,Yes,50,5,10,2025-01-01T10:00:00Z,2025-01-02T10:00:00Z\n"
        )

        records = list(extract_lps(csv_file))
        assert len(records) == 1

        lp = records[0]
        assert lp["org_external_id"] == "1001"
        assert lp["org_name"] == "Test Family Office"
        assert lp["country_raw"] == "France"
        assert lp["contact_name"] == "Jean Dupont"
        assert lp["contact_email"] == "jean@test.com"
        assert lp["solicitations_received"] == 50
        assert lp["solicitations_accepted"] == 5
        assert lp["acceptance_rate"] == 0.1
        assert "ipem_paris_2025" in lp["event_participation"]

    def test_extract_lps_infers_lp_type(self, tmp_path):
        """LP type is inferred from organization name."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "organization_id,organization_name,country_name,lp_user_id,title,first_name,last_name,email,telephoneFixe,telephonePort,is_participating_at_paris_2025,solicitations_received,solicitations_accepted,solicitations_declined,lastlogin_at,lastactivity_at\n"
            "1,Test Family Office,France,1,mr,A,B,a@b.com,,,,0,0,0,,\n"
            "2,State Pension Fund,UK,2,mr,C,D,c@d.com,,,,0,0,0,,\n"
            "3,University Endowment,USA,3,mr,E,F,e@f.com,,,,0,0,0,,\n"
            "4,Insurance Company,Germany,4,mr,G,H,g@h.com,,,,0,0,0,,\n"
        )

        records = list(extract_lps(csv_file))
        types = {r["org_name"]: r["ai_lp_type"] for r in records}

        assert types["Test Family Office"] == "family_office"
        assert types["State Pension Fund"] == "pension"
        assert types["University Endowment"] == "endowment"
        assert types["Insurance Company"] == "insurance"

    def test_extract_lps_infers_geography(self, tmp_path):
        """Geographic interests are inferred from country."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "organization_id,organization_name,country_name,lp_user_id,title,first_name,last_name,email,telephoneFixe,telephonePort,is_participating_at_paris_2025,solicitations_received,solicitations_accepted,solicitations_declined,lastlogin_at,lastactivity_at\n"
            "1,LP1,France,1,mr,A,B,a@b.com,,,,0,0,0,,\n"
            "2,LP2,États-Unis,2,mr,C,D,c@d.com,,,,0,0,0,,\n"
            "3,LP3,Japon,3,mr,E,F,e@f.com,,,,0,0,0,,\n"
        )

        records = list(extract_lps(csv_file))
        geo = {r["org_name"]: r["ai_geography_interests"] for r in records}

        assert geo["LP1"] == ["europe_west"]
        assert geo["LP2"] == ["north_america"]
        assert geo["LP3"] == ["asia_pacific"]

    def test_extract_lps_calculates_acceptance_rate(self, tmp_path):
        """Acceptance rate is calculated correctly."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "organization_id,organization_name,country_name,lp_user_id,title,first_name,last_name,email,telephoneFixe,telephonePort,is_participating_at_paris_2025,solicitations_received,solicitations_accepted,solicitations_declined,lastlogin_at,lastactivity_at\n"
            "1,LP1,France,1,mr,A,B,a@b.com,,,No,100,25,50,,\n"
            "2,LP2,France,2,mr,C,D,c@d.com,,,No,0,0,0,,\n"
            "3,LP3,France,3,mr,E,F,e@f.com,,,No,50,50,0,,\n"
        )

        records = list(extract_lps(csv_file))
        rates = {r["org_name"]: r["acceptance_rate"] for r in records}

        assert rates["LP1"] == 0.25  # 25/100
        assert rates["LP2"] is None  # 0/0 = None
        assert rates["LP3"] == 1.0   # 50/50

    def test_extract_lps_skips_empty_org_id(self, tmp_path):
        """Records without org_id are skipped."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "organization_id,organization_name,country_name,lp_user_id,title,first_name,last_name,email,telephoneFixe,telephonePort,is_participating_at_paris_2025,solicitations_received,solicitations_accepted,solicitations_declined,lastlogin_at,lastactivity_at\n"
            ",No Org,France,1,mr,A,B,a@b.com,,,No,0,0,0,,\n"
            "1,Has Org,France,2,mr,C,D,c@d.com,,,No,0,0,0,,\n"
        )

        records = list(extract_lps(csv_file))
        assert len(records) == 1
        assert records[0]["org_name"] == "Has Org"

    def test_extract_lps_event_participation(self, tmp_path):
        """Event participation is tracked."""
        csv_file = tmp_path / "test.csv"
        csv_file.write_text(
            "organization_id,organization_name,country_name,lp_user_id,title,first_name,last_name,email,telephoneFixe,telephonePort,is_participating_at_paris_2025,solicitations_received,solicitations_accepted,solicitations_declined,lastlogin_at,lastactivity_at\n"
            "1,LP1,France,1,mr,A,B,a@b.com,,,Yes,0,0,0,,\n"
            "2,LP2,France,2,mr,C,D,c@d.com,,,No,0,0,0,,\n"
            "3,LP3,France,3,mr,E,F,e@f.com,,,,0,0,0,,\n"
        )

        records = list(extract_lps(csv_file))
        events = {r["org_name"]: r["event_participation"] for r in records}

        assert events["LP1"] == ["ipem_paris_2025"]
        assert events["LP2"] == []
        assert events["LP3"] == []


class TestLPInferenceHelpers:
    """Tests for LP inference helper functions."""

    def test_parse_int_valid(self):
        assert _parse_int("100") == 100
        assert _parse_int("0") == 0
        assert _parse_int("999999") == 999999

    def test_parse_int_invalid(self):
        assert _parse_int("") == 0
        assert _parse_int(None) == 0
        assert _parse_int("abc") == 0
        assert _parse_int("12.5") == 0

    def test_infer_lp_type_family_office(self):
        assert _infer_lp_type("Smith Family Office") == "family_office"
        assert _infer_lp_type("ABC FAMILY-OFFICE") == "family_office"
        assert _infer_lp_type("XYZ Family Office LLC") == "family_office"

    def test_infer_lp_type_pension(self):
        assert _infer_lp_type("California Pension Fund") == "pension"
        assert _infer_lp_type("Teachers Pension") == "pension"

    def test_infer_lp_type_endowment(self):
        assert _infer_lp_type("Harvard Endowment") == "endowment"
        assert _infer_lp_type("Yale University Endowment Fund") == "endowment"

    def test_infer_lp_type_foundation(self):
        assert _infer_lp_type("Gates Foundation") == "foundation"
        assert _infer_lp_type("Ford Foundation Trust") == "foundation"

    def test_infer_lp_type_insurance(self):
        assert _infer_lp_type("AXA Insurance") == "insurance"
        assert _infer_lp_type("Mutuelle de Paris") == "insurance"
        assert _infer_lp_type("Assurance Vie SA") == "insurance"

    def test_infer_lp_type_other(self):
        assert _infer_lp_type("Random Company") == "other"
        assert _infer_lp_type("ABC Capital") == "other"

    def test_infer_geography_europe(self):
        assert _infer_geography_from_country("France") == ["europe_west"]
        assert _infer_geography_from_country("Germany") == ["europe_west"]
        assert _infer_geography_from_country("Royaume-Uni") == ["europe_west"]
        assert _infer_geography_from_country("Suisse") == ["europe_west"]

    def test_infer_geography_nordic(self):
        assert _infer_geography_from_country("Sweden") == ["europe_north"]
        assert _infer_geography_from_country("Finlande") == ["europe_north"]

    def test_infer_geography_north_america(self):
        assert _infer_geography_from_country("États-Unis") == ["north_america"]
        assert _infer_geography_from_country("USA") == ["north_america"]
        assert _infer_geography_from_country("Canada") == ["north_america"]

    def test_infer_geography_middle_east(self):
        assert _infer_geography_from_country("Israël") == ["middle_east"]
        assert _infer_geography_from_country("UAE") == ["middle_east"]

    def test_infer_geography_asia(self):
        assert _infer_geography_from_country("Japon") == ["asia_pacific"]
        assert _infer_geography_from_country("Singapore") == ["asia_pacific"]
        assert _infer_geography_from_country("Hong Kong") == ["asia_pacific"]

    def test_infer_geography_unknown(self):
        assert _infer_geography_from_country("Unknown Country") == ["global"]
        assert _infer_geography_from_country("") == ["global"]


class TestEngagementScore:
    """Tests for engagement score calculation."""

    def test_engagement_high_volume_high_rate(self):
        """High volume + high acceptance = high score."""
        score = _calculate_engagement_score(150, 0.5, "2025-01-01T10:00:00Z")
        assert score >= 0.7

    def test_engagement_low_volume_no_activity(self):
        """Low volume + no acceptance = low score."""
        score = _calculate_engagement_score(5, 0.0, None)
        assert score <= 0.2

    def test_engagement_capped_at_one(self):
        """Score should never exceed 1.0."""
        score = _calculate_engagement_score(1000, 1.0, "2025-01-01T10:00:00Z")
        assert score <= 1.0

    def test_engagement_zero_volume(self):
        """Zero volume = minimal score."""
        score = _calculate_engagement_score(0, None, None)
        assert score == 0.0


class TestLPProfileLoader:
    """Tests for LP profile loading."""

    def test_load_lp_profiles_dry_run(self):
        """Dry run should count records without database writes."""
        records = [
            {
                "org_external_id": "1001",
                "org_name": "Test Family Office",
                "country_raw": "France",
                "lp_type_raw": "family_office",
                "solicitations_received": 50,
                "solicitations_accepted": 5,
                "last_activity_at": "2025-01-01T10:00:00Z",
                "event_participation": ["ipem_paris_2025"],
            },
            {
                "org_external_id": "1002",
                "org_name": "Test Pension",
                "country_raw": "UK",
                "lp_type_raw": "pension",
                "solicitations_received": 100,
                "solicitations_accepted": 20,
                "last_activity_at": None,
                "event_participation": [],
            },
        ]

        stats = load_lp_profiles(
            client=None,
            records=iter(records),
            dry_run=True,
        )

        assert stats.created == 2
        assert stats.skipped == 0
        assert len(stats.errors) == 0

    def test_load_lp_profiles_skips_missing_org_id(self):
        """Records without org_external_id should be skipped."""
        records = [
            {"org_name": "No ID"},  # No org_external_id
            {"org_external_id": "", "org_name": "Empty ID"},  # Empty
            {"org_external_id": "1001", "org_name": "Valid"},  # Valid
        ]

        stats = load_lp_profiles(
            client=None,
            records=iter(records),
            dry_run=True,
        )

        assert stats.created == 1
        assert stats.skipped == 2


class TestLPDataQuality:
    """Test data quality with real lp_matchmaking.csv."""

    def test_extract_from_real_csv(self):
        """Extract from actual lp_matchmaking.csv if available."""
        real_csv = Path("docs/data/metabase_copy/lp_matchmaking.csv")
        if not real_csv.exists():
            pytest.skip("lp_matchmaking.csv not found")

        records = list(extract_lps(real_csv))
        assert len(records) > 0

        # Check first record has expected fields
        lp = records[0]
        assert "org_external_id" in lp
        assert "org_name" in lp
        assert "solicitations_received" in lp
        assert "ai_lp_type" in lp
        assert "ai_geography_interests" in lp

    def test_real_data_has_behavioral_metrics(self):
        """Real data should have behavioral metrics."""
        real_csv = Path("docs/data/metabase_copy/lp_matchmaking.csv")
        if not real_csv.exists():
            pytest.skip("lp_matchmaking.csv not found")

        records = list(extract_lps(real_csv))

        # Count LPs with behavioral data
        with_solicitations = sum(
            1 for r in records if r["solicitations_received"] > 0
        )

        # Most LPs should have some behavioral data
        assert with_solicitations > len(records) * 0.5, \
            f"Expected most LPs to have solicitations, got {with_solicitations}/{len(records)}"

    def test_real_data_lp_types_distribution(self):
        """Check LP type distribution in real data."""
        real_csv = Path("docs/data/metabase_copy/lp_matchmaking.csv")
        if not real_csv.exists():
            pytest.skip("lp_matchmaking.csv not found")

        records = list(extract_lps(real_csv))

        # Count LP types
        types = {}
        for r in records:
            lp_type = r["ai_lp_type"]
            types[lp_type] = types.get(lp_type, 0) + 1

        # Should have family offices (most common in IPEM data)
        assert types.get("family_office", 0) > 0, \
            f"Expected family offices, got types: {types}"

        print("\nLP Type Distribution:")
        for t, count in sorted(types.items(), key=lambda x: -x[1]):
            print(f"  {t}: {count}")


class TestLPETLIntegration:
    """Integration tests for LP ETL flow."""

    def test_full_lp_extraction_and_load(self, tmp_path):
        """Test full extraction and loading flow."""
        # Create test CSV
        csv_file = tmp_path / "lp_matchmaking.csv"
        csv_file.write_text(
            "organization_id,organization_name,country_name,lp_user_id,title,first_name,last_name,email,telephoneFixe,telephonePort,is_participating_at_paris_2025,solicitations_received,solicitations_accepted,solicitations_declined,lastlogin_at,lastactivity_at\n"
            "1001,Alpha Family Office,France,100,mr,Jean,Dupont,jean@alpha.com,+33123,+33456,Yes,50,5,10,2025-01-01T10:00:00Z,2025-01-02T10:00:00Z\n"
            "1002,Beta Pension Fund,Germany,101,ms,Anna,Schmidt,anna@beta.com,+49123,,No,100,20,30,2025-01-01T10:00:00Z,2025-01-02T10:00:00Z\n"
            "1003,Gamma Endowment,États-Unis,102,mr,John,Smith,john@gamma.com,+1123,,Yes,75,15,25,2025-01-01T10:00:00Z,2025-01-02T10:00:00Z\n"
        )

        # Extract
        records = list(extract_lps(csv_file))
        assert len(records) == 3

        # Verify extraction
        alpha = next(r for r in records if r["org_name"] == "Alpha Family Office")
        assert alpha["ai_lp_type"] == "family_office"
        assert alpha["ai_geography_interests"] == ["europe_west"]
        assert alpha["acceptance_rate"] == 0.1

        beta = next(r for r in records if r["org_name"] == "Beta Pension Fund")
        assert beta["ai_lp_type"] == "pension"
        assert beta["acceptance_rate"] == 0.2

        gamma = next(r for r in records if r["org_name"] == "Gamma Endowment")
        assert gamma["ai_lp_type"] == "endowment"
        assert gamma["ai_geography_interests"] == ["north_america"]

        # Load in dry-run mode
        stats = load_lp_profiles(
            client=None,
            records=iter(records),
            dry_run=True,
        )

        assert stats.created == 3
        assert stats.skipped == 0
