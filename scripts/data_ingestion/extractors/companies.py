"""
Extract company/organization data from CSV files.
READ-ONLY - never modify source files.
"""
import csv
from pathlib import Path
from typing import Iterator


def _clean_null(value: str | None) -> str | None:
    """Convert 'null' string and empty values to None."""
    if not value:
        return None
    cleaned = value.strip()
    if cleaned.lower() == "null" or cleaned == "":
        return None
    return cleaned


def extract_companies(filepath: Path) -> Iterator[dict]:
    """
    Extract companies from companies_crm.csv.

    Expected columns:
    - Organization ID
    - Company Name
    - Website
    - Description
    - Country

    Yields dict per row with normalized keys.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            yield {
                "external_id": row.get("Organization ID", "").strip(),
                "name": row.get("Company Name", "").strip(),
                "website": _clean_null(row.get("Website")),
                "description": _clean_null(row.get("Description")),
                "hq_country": _clean_null(row.get("Country")),
            }


def extract_parent_companies(filepath: Path) -> Iterator[dict]:
    """
    Extract parent company hierarchy from parent_companies.csv.

    Expected columns:
    - parent_company_id
    - parent_company_name
    - parent_country
    - child_companies (comma-separated IDs)

    Yields dict per row.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            child_ids = row.get("child_companies", "")
            yield {
                "external_id": row.get("parent_company_id", "").strip(),
                "name": row.get("parent_company_name", "").strip(),
                "hq_country": row.get("parent_country", "").strip() or None,
                "child_external_ids": [
                    cid.strip() for cid in child_ids.split(",") if cid.strip()
                ],
            }
