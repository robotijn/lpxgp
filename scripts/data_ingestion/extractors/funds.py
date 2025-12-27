"""
Extract fund data from CSV files.
READ-ONLY - never modify source files.
"""
import csv
from pathlib import Path
from typing import Iterator


def extract_funds(filepath: Path) -> Iterator[dict]:
    """
    Extract funds from global_funds.csv.

    Expected columns:
    - fund_id
    - fund_manager_org_id
    - fund_name
    - fund_status
    - fund_generation_number
    - description
    - private_equity_strategies
    - vc_strategies
    - geographic_focus
    - sectors
    - esg_approach
    - investment_minimum

    Yields dict per row with normalized keys.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # Parse geographic focus as array
            geo_focus = row.get("geographic_focus", "")
            geographic_focus = [g.strip() for g in geo_focus.split(",") if g.strip()]

            # Parse sectors as array
            sectors = row.get("sectors", "")
            sector_focus = [s.strip() for s in sectors.split(",") if s.strip()]

            # Parse ESG
            esg_raw = row.get("esg_approach", "").strip().lower()
            esg_policy = esg_raw in ("yes", "true", "1")

            # Parse fund number
            gen_number = row.get("fund_generation_number", "").strip()
            fund_number = int(gen_number) if gen_number.isdigit() else None

            # Parse minimum investment
            inv_min = row.get("investment_minimum", "").strip()
            check_size_min = float(inv_min) if inv_min and inv_min.replace(".", "").isdigit() else None

            yield {
                "external_id": row.get("fund_id", "").strip(),
                "org_external_id": row.get("fund_manager_org_id", "").strip() or None,
                "name": row.get("fund_name", "").strip(),
                "status_raw": row.get("fund_status", "").strip(),
                "fund_number": fund_number,
                "investment_thesis": row.get("description", "").strip() or None,
                "strategy": row.get("private_equity_strategies", "").strip() or None,
                "sub_strategy": row.get("vc_strategies", "").strip() or None,
                "geographic_focus": geographic_focus,
                "sector_focus": sector_focus,
                "esg_policy": esg_policy,
                "check_size_min_mm": check_size_min,
            }
