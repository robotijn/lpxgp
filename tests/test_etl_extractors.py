"""
Tests for ETL extractors.

Extractors read CSV files and yield normalized records.
"""

import csv
import tempfile
from pathlib import Path

import pytest

from scripts.data_ingestion.extractors.funds import extract_funds, _parse_investment_amount
from scripts.data_ingestion.extractors.companies import extract_companies
from scripts.data_ingestion.extractors.contacts import extract_contacts


class TestFundExtractor:
    """Test fund extraction from CSV."""

    @pytest.fixture
    def sample_funds_csv(self, tmp_path):
        """Create a sample funds CSV for testing."""
        csv_path = tmp_path / "test_funds.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "fund_id", "fund_manager_org_id", "fund_manager_name",
                "fund_name", "fund_status", "fund_generation_number",
                "fund_size_category_EM", "description",
                "private_equity_strategies", "vc_strategies",
                "private_debt_strategies", "real_assets_strategies",
                "other_strategies", "sectors", "technologies",
                "geographic_focus", "geographic_scopes",
                "esg_approach", "investment_minimum",
                "fund_domiciliation", "fee_structure_explanation",
            ])
            # Fund 1: PE buyout fund
            writer.writerow([
                "1001", "ORG123", "Test GP",
                "Test Buyout Fund III", "Open for investment", "3",
                "Small (€100m-€500m)", "A buyout fund targeting tech companies",
                "Buyout", "", "", "", "",
                "Technology and software, Healthcare", "",
                "france, germany, uk", "Pan-European",
                "We have ESG policy", "€5m",
                "Luxembourg", "2% management, 20% carry",
            ])
            # Fund 2: VC fund
            writer.writerow([
                "1002", "ORG456", "Another GP",
                "Seed Fund I", "Raising", "1",
                "Micro (0-€100m)", "Early stage tech investments",
                "", "Seed / early stage", "", "", "",
                "", "Artificial intelligence",
                "usa, canada", "Global",
                "", "€1m",
                "Cayman Islands", "",
            ])
            # Fund 3: No strategies (edge case)
            writer.writerow([
                "1003", "ORG789", "Empty GP",
                "Empty Fund", "", "",
                "", "",
                "", "", "", "", "",
                "", "",
                "", "",
                "", "",
                "", "",
            ])
        return csv_path

    def test_extract_funds_basic(self, sample_funds_csv):
        """Extract funds and verify basic fields."""
        funds = list(extract_funds(sample_funds_csv))
        assert len(funds) == 3

        # Check first fund
        fund1 = funds[0]
        assert fund1["external_id"] == "1001"
        assert fund1["org_external_id"] == "ORG123"
        assert fund1["name"] == "Test Buyout Fund III"
        assert fund1["fund_number"] == 3
        assert fund1["status_raw"] == "Open for investment"

    def test_extract_funds_raw_values(self, sample_funds_csv):
        """Verify raw values are preserved for client display."""
        funds = list(extract_funds(sample_funds_csv))
        fund1 = funds[0]

        # Raw values should be preserved exactly
        assert fund1["strategies_raw"] == "Buyout"
        assert fund1["fund_size_raw"] == "Small (€100m-€500m)"
        assert fund1["geographic_scope_raw"] == "Pan-European"
        assert fund1["domicile"] == "Luxembourg"
        assert fund1["fee_details"] == "2% management, 20% carry"

    def test_extract_funds_ai_normalized(self, sample_funds_csv):
        """Verify AI-normalized values are correct."""
        funds = list(extract_funds(sample_funds_csv))
        fund1 = funds[0]

        # AI values should be normalized
        assert fund1["ai_strategy_tags"] == ["buyout"]
        assert "europe_west" in fund1["ai_geography_tags"]
        assert fund1["ai_size_bucket"] == "small"
        assert fund1["ai_size_mm"] == 300  # Midpoint of 100-500

    def test_extract_funds_vc_strategies(self, sample_funds_csv):
        """VC fund strategies should normalize correctly."""
        funds = list(extract_funds(sample_funds_csv))
        fund2 = funds[1]

        assert fund2["ai_strategy_tags"] == ["venture_seed"]
        assert fund2["ai_size_bucket"] == "micro"
        assert "north_america" in fund2["ai_geography_tags"]

    def test_extract_funds_empty_handling(self, sample_funds_csv):
        """Empty fields should be handled gracefully."""
        funds = list(extract_funds(sample_funds_csv))
        fund3 = funds[2]

        assert fund3["external_id"] == "1003"
        assert fund3["ai_strategy_tags"] == []
        assert fund3["ai_geography_tags"] == []
        assert fund3["ai_size_bucket"] is None
        assert fund3["fund_number"] is None

    def test_extract_funds_esg_detection(self, sample_funds_csv):
        """ESG policy should be detected from non-empty text."""
        funds = list(extract_funds(sample_funds_csv))

        assert funds[0]["esg_policy"] is True  # Has ESG text
        assert funds[0]["ai_has_esg"] is True
        assert funds[1]["esg_policy"] is False  # Empty
        assert funds[2]["esg_policy"] is False  # Empty


class TestInvestmentAmountParser:
    """Test investment amount parsing."""

    def test_parse_euro_millions(self):
        """Parse €Xm format."""
        assert _parse_investment_amount("€5m") == 5.0
        assert _parse_investment_amount("€1m") == 1.0
        assert _parse_investment_amount("€10m") == 10.0

    def test_parse_dollar_millions(self):
        """Parse $Xm format."""
        assert _parse_investment_amount("$5m") == 5.0
        assert _parse_investment_amount("$100m") == 100.0

    def test_parse_with_spaces(self):
        """Parse amounts with spaces."""
        assert _parse_investment_amount("€5 m") == 5.0
        assert _parse_investment_amount("5 million") == 5.0

    def test_parse_thousands(self):
        """Parse amounts in thousands."""
        assert _parse_investment_amount("€500k") == 0.5
        assert _parse_investment_amount("$1000k") == 1.0

    def test_parse_billions(self):
        """Parse amounts in billions."""
        assert _parse_investment_amount("€1bn") == 1000.0
        assert _parse_investment_amount("$2billion") == 2000.0

    def test_parse_empty(self):
        """Empty input should return None."""
        assert _parse_investment_amount("") is None
        assert _parse_investment_amount(None) is None

    def test_parse_invalid(self):
        """Invalid input should return None."""
        assert _parse_investment_amount("abc") is None
        assert _parse_investment_amount("N/A") is None


class TestCompanyExtractor:
    """Test company extraction from CSV."""

    @pytest.fixture
    def sample_companies_csv(self, tmp_path):
        """Create a sample companies CSV."""
        csv_path = tmp_path / "test_companies.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow(["Organization ID", "Company Name", "Website", "Description", "Country"])
            writer.writerow(["ORG001", "Test Company", "https://test.com", "A test company", "France"])
            writer.writerow(["ORG002", "Another Co", "", "null", "Germany"])
        return csv_path

    def test_extract_companies_basic(self, sample_companies_csv):
        """Extract companies and verify fields."""
        companies = list(extract_companies(sample_companies_csv))
        assert len(companies) == 2

        co1 = companies[0]
        assert co1["external_id"] == "ORG001"
        assert co1["name"] == "Test Company"
        assert co1["website"] == "https://test.com"
        assert co1["hq_country"] == "France"

    def test_extract_companies_null_handling(self, sample_companies_csv):
        """'null' string should be treated as empty."""
        companies = list(extract_companies(sample_companies_csv))
        co2 = companies[1]

        # 'null' should be converted to None
        assert co2["description"] is None or co2["description"] == ""


class TestContactExtractor:
    """Test contact extraction from CSV."""

    @pytest.fixture
    def sample_contacts_csv(self, tmp_path):
        """Create a sample contacts CSV."""
        csv_path = tmp_path / "test_contacts.csv"
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "Source", "original ID", "contact certification status",
                "Name", "Old Job Title", "Company name", "Associated org ID",
                "Company LinkedIn", "Company domain", "Email", "Validation result",
                "LinkedIn", "Work Status", "New Company", "New Job Title",
                "Reasoning", "New email", "New email status"
            ])
            writer.writerow([
                "IPEM", "12345", "CERTIFIED",
                "John Doe", "Partner", "Test GP", "ORG001",
                "linkedin.com/company/test", "test.com", "john@test.com", "valid",
                "linkedin.com/in/johndoe", "EMPLOYED", "", "",
                "", "", ""
            ])
            writer.writerow([
                "IPEM", "12346", "DECERTIFIED AUTOMATICALY",
                "Jane Smith", "Analyst", "Another Co", "ORG002",
                "", "", "jane@example.com", "invalid",
                "", "LEFT", "New Company", "Director",
                "Promoted", "jane@newco.com", "valid"
            ])
        return csv_path

    def test_extract_contacts_basic(self, sample_contacts_csv):
        """Extract contacts and verify fields."""
        contacts = list(extract_contacts(sample_contacts_csv))
        assert len(contacts) == 2

        c1 = contacts[0]
        assert c1["full_name"] == "John Doe"
        assert c1["email"] == "john@test.com"
        assert c1["certification_status"] == "CERTIFIED"
        assert c1["org_external_id"] == "ORG001"

    def test_extract_contacts_work_status(self, sample_contacts_csv):
        """Work status should be extracted correctly."""
        contacts = list(extract_contacts(sample_contacts_csv))

        assert contacts[0]["work_status"] == "EMPLOYED"
        assert contacts[1]["work_status"] == "LEFT"
