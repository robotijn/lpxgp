"""
Extract contact/people data from CSV files.
READ-ONLY - never modify source files.
"""
import csv
from pathlib import Path
from typing import Iterator


def extract_contacts(filepath: Path) -> Iterator[dict]:
    """
    Extract contacts from contacts.csv.

    Expected columns:
    - Name
    - Email
    - LinkedIn
    - Old Job Title
    - Company name
    - Associated org ID
    - contact certification status
    - Work Status
    - Validation result

    Yields dict per row with normalized keys.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Normalize email
            email = row.get("Email", "").strip().lower() or None

            # Parse validation result
            validation = row.get("Validation result", "").strip().lower()
            email_valid = validation == "valid" if validation else None

            yield {
                "full_name": row.get("Name", "").strip(),
                "email": email,
                "linkedin_url": row.get("LinkedIn", "").strip() or None,
                "title": row.get("Old Job Title", "").strip() or None,
                "company_name": row.get("Company name", "").strip() or None,
                "org_external_id": row.get("Associated org ID", "").strip() or None,
                "certification_status": row.get("contact certification status", "").strip() or None,
                "work_status": row.get("Work Status", "").strip() or None,
                "email_valid": email_valid,
            }
