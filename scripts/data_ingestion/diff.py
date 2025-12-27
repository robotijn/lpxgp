#!/usr/bin/env python3
"""
Data Diff Tool - Compare Metabase exports for daily sync.

Usage:
    python -m scripts.data_ingestion.diff --old data/2024-01-01/ --new data/2024-01-02/
    python -m scripts.data_ingestion.diff --new data/2024-01-02/ --baseline supabase
"""
import argparse
import csv
import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Iterator

from supabase import create_client

from .config import SUPABASE_URL, SUPABASE_SERVICE_KEY

logging.basicConfig(level=logging.INFO, format="%(asctime)s | %(message)s")
logger = logging.getLogger(__name__)


@dataclass
class DiffResult:
    """Results of comparing two datasets."""
    added: list = field(default_factory=list)
    removed: list = field(default_factory=list)
    changed: list = field(default_factory=list)

    @property
    def has_changes(self) -> bool:
        return bool(self.added or self.removed or self.changed)

    def summary(self) -> str:
        return f"Added: {len(self.added)}, Removed: {len(self.removed)}, Changed: {len(self.changed)}"


def load_csv_as_dict(filepath: Path, key_column: str) -> dict[str, dict]:
    """Load CSV file into dict keyed by specified column."""
    result = {}
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            key = row.get(key_column, "").strip()
            if key:
                result[key] = row
    return result


def compare_records(old: dict, new: dict, ignore_columns: set | None = None) -> list[str]:
    """
    Compare two records and return list of changed field names.
    """
    ignore = ignore_columns or {"updated_at", "last_modified"}
    changes = []

    all_keys = set(old.keys()) | set(new.keys())
    for key in all_keys:
        if key in ignore:
            continue
        old_val = old.get(key, "").strip() if old.get(key) else ""
        new_val = new.get(key, "").strip() if new.get(key) else ""
        if old_val != new_val:
            changes.append(key)

    return changes


def diff_csv_files(
    old_file: Path,
    new_file: Path,
    key_column: str,
    ignore_columns: set | None = None,
) -> DiffResult:
    """
    Compare two CSV files and return differences.

    Args:
        old_file: Path to old CSV
        new_file: Path to new CSV
        key_column: Column to use as unique key
        ignore_columns: Columns to ignore when comparing

    Returns:
        DiffResult with added, removed, and changed records
    """
    logger.info(f"Comparing {old_file.name} vs {new_file.name}")

    old_data = load_csv_as_dict(old_file, key_column)
    new_data = load_csv_as_dict(new_file, key_column)

    result = DiffResult()

    # Find added (in new but not in old)
    for key in new_data:
        if key not in old_data:
            result.added.append({"key": key, "record": new_data[key]})

    # Find removed (in old but not in new)
    for key in old_data:
        if key not in new_data:
            result.removed.append({"key": key, "record": old_data[key]})

    # Find changed (in both but different)
    for key in old_data:
        if key in new_data:
            changes = compare_records(old_data[key], new_data[key], ignore_columns)
            if changes:
                result.changed.append({
                    "key": key,
                    "changed_fields": changes,
                    "old": old_data[key],
                    "new": new_data[key],
                })

    return result


def diff_against_supabase(
    new_file: Path,
    table_name: str,
    key_column: str,
    external_id_column: str,
) -> DiffResult:
    """
    Compare new CSV against current Supabase state.

    Args:
        new_file: Path to new CSV export
        table_name: Supabase table to compare against
        key_column: CSV column with external ID
        external_id_column: Supabase column with external ID

    Returns:
        DiffResult with differences
    """
    logger.info(f"Comparing {new_file.name} against Supabase {table_name}")

    # Load CSV
    new_data = load_csv_as_dict(new_file, key_column)

    # Load from Supabase
    client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)
    response = client.table(table_name).select("*").eq("external_source", "ipem").execute()

    old_data = {}
    for row in response.data or []:
        ext_id = row.get(external_id_column)
        if ext_id:
            old_data[ext_id] = row

    result = DiffResult()

    # Find added (in CSV but not in Supabase)
    for key in new_data:
        if key not in old_data:
            result.added.append({"key": key, "record": new_data[key]})

    # Find removed (in Supabase but not in CSV)
    for key in old_data:
        if key not in new_data:
            result.removed.append({"key": key, "record": old_data[key]})

    logger.info(f"  New in CSV: {len(result.added)}")
    logger.info(f"  Removed from source: {len(result.removed)}")

    return result


def main():
    parser = argparse.ArgumentParser(description="Compare data exports for sync")
    parser.add_argument("--old", type=Path, help="Path to old export directory")
    parser.add_argument("--new", type=Path, required=True, help="Path to new export directory")
    parser.add_argument("--baseline", choices=["file", "supabase"], default="file",
                       help="Compare against files or Supabase")
    parser.add_argument("--output", type=Path, help="Output diff report to JSON file")

    args = parser.parse_args()

    # Define files to compare
    file_configs = [
        {
            "filename": "companies_crm.csv",
            "key_column": "Organization ID",
            "table": "organizations",
            "external_id_column": "external_id",
        },
        {
            "filename": "global_funds.csv",
            "key_column": "fund_id",
            "table": "funds",
            "external_id_column": "external_id",
        },
    ]

    all_results = {}

    for config in file_configs:
        new_file = args.new / config["filename"]
        if not new_file.exists():
            logger.warning(f"Skipping {config['filename']} - not found")
            continue

        if args.baseline == "supabase":
            result = diff_against_supabase(
                new_file,
                config["table"],
                config["key_column"],
                config["external_id_column"],
            )
        else:
            if not args.old:
                logger.error("--old required when baseline is 'file'")
                return
            old_file = args.old / config["filename"]
            if not old_file.exists():
                logger.warning(f"Skipping {config['filename']} - old file not found")
                continue
            result = diff_csv_files(old_file, new_file, config["key_column"])

        all_results[config["filename"]] = {
            "summary": result.summary(),
            "added_count": len(result.added),
            "removed_count": len(result.removed),
            "changed_count": len(result.changed),
        }

        logger.info(f"  {config['filename']}: {result.summary()}")

    # Output report
    if args.output:
        with open(args.output, "w") as f:
            json.dump(all_results, f, indent=2)
        logger.info(f"Report saved to {args.output}")


if __name__ == "__main__":
    main()
