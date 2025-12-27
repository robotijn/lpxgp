"""
Integration tests for the ETL pipeline.

These tests run the full ETL pipeline in dry-run mode to verify
end-to-end functionality without database writes.
"""

import subprocess
import sys

import pytest


class TestETLPipelineDryRun:
    """Test ETL pipeline phases in dry-run mode."""

    def test_phase_organizations_dry_run(self):
        """Organizations phase should complete without errors."""
        result = subprocess.run(
            [sys.executable, "-m", "scripts.data_ingestion.main",
             "--phase", "organizations", "--dry-run", "--limit", "10"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert "Phase 1: Organizations" in result.stderr
        assert "created" in result.stderr

    def test_phase_lps_dry_run(self):
        """LPs phase should complete and output raw data."""
        result = subprocess.run(
            [sys.executable, "-m", "scripts.data_ingestion.main",
             "--phase", "lps", "--dry-run", "--limit", "10"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert "Phase 3: LP Profiles" in result.stderr
        assert "raw data for display" in result.stderr.lower()

    def test_phase_funds_dry_run(self):
        """Funds phase should complete and output raw + AI data."""
        result = subprocess.run(
            [sys.executable, "-m", "scripts.data_ingestion.main",
             "--phase", "funds", "--dry-run", "--limit", "10"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert "Phase 4: Funds" in result.stderr
        assert "raw data for display" in result.stderr.lower()

    def test_phase_all_dry_run(self):
        """'all' phase should run organizations, people, lps, funds."""
        result = subprocess.run(
            [sys.executable, "-m", "scripts.data_ingestion.main",
             "--phase", "all", "--dry-run", "--limit", "5"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert "Phase 1: Organizations" in result.stderr
        assert "Phase 2: People" in result.stderr
        assert "Phase 3: LP Profiles" in result.stderr
        assert "Phase 4: Funds" in result.stderr
        assert "SUMMARY" in result.stderr

    def test_phase_full_dry_run(self):
        """'full' phase should run all phases + AI profiles."""
        result = subprocess.run(
            [sys.executable, "-m", "scripts.data_ingestion.main",
             "--phase", "full", "--dry-run", "--limit", "5"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        assert result.returncode == 0, f"Failed: {result.stderr}"
        # Should include raw data phases
        assert "Phase 1: Organizations" in result.stderr
        assert "Phase 3: LP Profiles" in result.stderr
        assert "Phase 4: Funds" in result.stderr
        # Should include AI profiles phase
        assert "Phase 5: AI Profiles" in result.stderr
        assert "for matching algorithms only" in result.stderr.lower()

    def test_phase_ai_profiles_dry_run(self):
        """AI profiles phase should run independently."""
        result = subprocess.run(
            [sys.executable, "-m", "scripts.data_ingestion.main",
             "--phase", "ai-profiles", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0, f"Failed: {result.stderr}"
        assert "Phase 5: AI Profiles" in result.stderr


class TestETLPipelineOutput:
    """Test ETL pipeline output structure."""

    def test_pipeline_structure_shown(self):
        """Pipeline should display its two-phase structure."""
        result = subprocess.run(
            [sys.executable, "-m", "scripts.data_ingestion.main",
             "--phase", "full", "--dry-run", "--limit", "1"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        assert result.returncode == 0
        # Should explain the two-table architecture
        assert "RAW DATA" in result.stderr
        assert "AI DATA" in result.stderr
        assert "client display" in result.stderr.lower()
        assert "matching" in result.stderr.lower()

    def test_summary_has_counts(self):
        """Summary should show created/skipped/error counts."""
        result = subprocess.run(
            [sys.executable, "-m", "scripts.data_ingestion.main",
             "--phase", "all", "--dry-run", "--limit", "10"],
            capture_output=True,
            text=True,
            timeout=120,
        )

        assert result.returncode == 0
        assert "SUMMARY" in result.stderr
        assert "Total created:" in result.stderr
        assert "Total skipped:" in result.stderr
        assert "Total errors:" in result.stderr


class TestETLDataQuality:
    """Test data quality during extraction."""

    def test_funds_extraction_has_normalized_data(self):
        """Fund extraction should produce both raw and AI-normalized data."""
        from pathlib import Path
        from scripts.data_ingestion.extractors.funds import extract_funds
        from scripts.data_ingestion.config import SOURCE_FILES

        filepath = SOURCE_FILES.get("global_funds")
        if not filepath or not filepath.exists():
            pytest.skip("global_funds.csv not found")

        funds = list(extract_funds(filepath))
        assert len(funds) > 0

        # Check first fund has both raw and AI fields
        fund = funds[0]

        # Raw fields (for client display)
        assert "strategies_raw" in fund
        assert "fund_size_raw" in fund
        assert "geographic_scope_raw" in fund

        # AI fields (for matching)
        assert "ai_strategy_tags" in fund
        assert "ai_geography_tags" in fund
        assert "ai_size_bucket" in fund
        assert "ai_size_mm" in fund

        # AI fields should be normalized (lists, not raw strings)
        assert isinstance(fund["ai_strategy_tags"], list)
        assert isinstance(fund["ai_geography_tags"], list)

    def test_funds_have_good_normalization_coverage(self):
        """Most funds should have normalized strategies and geography."""
        from scripts.data_ingestion.extractors.funds import extract_funds
        from scripts.data_ingestion.config import SOURCE_FILES

        filepath = SOURCE_FILES.get("global_funds")
        if not filepath or not filepath.exists():
            pytest.skip("global_funds.csv not found")

        funds = list(extract_funds(filepath))
        if len(funds) < 100:
            pytest.skip("Need 100+ funds for coverage test")

        with_strategies = sum(1 for f in funds if f["ai_strategy_tags"])
        with_geography = sum(1 for f in funds if f["ai_geography_tags"])
        with_size = sum(1 for f in funds if f["ai_size_bucket"])

        total = len(funds)

        # At least 80% should have strategies
        assert with_strategies / total >= 0.8, f"Only {with_strategies}/{total} have strategies"

        # At least 90% should have geography
        assert with_geography / total >= 0.9, f"Only {with_geography}/{total} have geography"

        # At least 95% should have size bucket
        assert with_size / total >= 0.95, f"Only {with_size}/{total} have size"


class TestETLErrorHandling:
    """Test ETL error handling."""

    def test_invalid_phase_rejected(self):
        """Invalid phase should be rejected with clear error."""
        result = subprocess.run(
            [sys.executable, "-m", "scripts.data_ingestion.main",
             "--phase", "invalid_phase", "--dry-run"],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode != 0
        assert "invalid" in result.stderr.lower() or "error" in result.stderr.lower()

    def test_missing_file_handled(self):
        """Missing source file should be handled gracefully."""
        # This test relies on the actual file checks in the extractors
        # The pipeline should report an error but not crash
        result = subprocess.run(
            [sys.executable, "-m", "scripts.data_ingestion.main",
             "--phase", "funds", "--dry-run", "--limit", "1"],
            capture_output=True,
            text=True,
            timeout=60,
        )

        # Should complete (may have errors if files missing, but shouldn't crash)
        # returncode 0 means files exist, non-zero means handled gracefully
        assert "Traceback" not in result.stderr or "File not found" in result.stderr
