"""
Extract fund data from CSV files.
READ-ONLY - never modify source files.
"""
import csv
from pathlib import Path
from typing import Iterator

from ..transformers.enrich import (
    parse_strategies,
    normalize_strategies,
    parse_geographic_preferences,
    normalize_geographies,
    normalize_sectors,
    normalize_fund_size,
    parse_fund_size_to_mm,
)


def extract_funds(filepath: Path) -> Iterator[dict]:
    """
    Extract funds from global_funds.csv.

    Expected columns:
    - fund_id
    - fund_manager_org_id
    - fund_name
    - fund_status
    - fund_generation_number
    - fund_size_category_EM
    - description
    - private_equity_strategies, vc_strategies, private_debt_strategies,
      real_assets_strategies, other_strategies
    - geographic_focus
    - sectors, technologies
    - esg_approach
    - investment_minimum

    Yields dict per row with normalized keys.
    """
    with open(filepath, "r", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            # ── STRATEGIES: Merge all strategy columns ──
            all_strategies = []
            for col in [
                "private_equity_strategies",
                "vc_strategies",
                "private_debt_strategies",
                "real_assets_strategies",
                "other_strategies",
            ]:
                all_strategies.extend(parse_strategies(row.get(col, "")))
            normalized_strategies = normalize_strategies(all_strategies)

            # ── GEOGRAPHY: Parse and normalize ──
            geo_focus = parse_geographic_preferences(row.get("geographic_focus", ""))
            normalized_geo = normalize_geographies(geo_focus)

            # ── SECTORS: Merge sectors + technologies ──
            sectors = parse_strategies(row.get("sectors", ""))
            technologies = parse_strategies(row.get("technologies", ""))
            all_sectors = sectors + technologies
            normalized_sectors = normalize_sectors(all_sectors)

            # ── FUND SIZE: Normalize category ──
            size_raw = row.get("fund_size_category_EM", "")
            size_normalized = normalize_fund_size(size_raw)
            size_mm = parse_fund_size_to_mm(size_raw)

            # ── ESG: Any non-empty text = true ──
            esg_raw = row.get("esg_approach", "").strip()
            esg_policy = bool(esg_raw)

            # ── FUND NUMBER: Parse integer ──
            gen_number = row.get("fund_generation_number", "").strip()
            fund_number = int(gen_number) if gen_number.isdigit() else None

            # ── MINIMUM INVESTMENT: Parse amount ──
            inv_min = row.get("investment_minimum", "").strip()
            # Handle formats like "€1m", "€5m", "$10M"
            check_size_min = _parse_investment_amount(inv_min)

            yield {
                "external_id": row.get("fund_id", "").strip(),
                "org_external_id": row.get("fund_manager_org_id", "").strip() or None,
                "name": row.get("fund_name", "").strip(),
                "status_raw": row.get("fund_status", "").strip(),
                "fund_number": fund_number,
                "investment_thesis": row.get("description", "").strip() or None,

                # ══════════════════════════════════════════════════════════
                # RAW VALUES (for client display - stored in funds table)
                # Client sees exactly what was in the source
                # ══════════════════════════════════════════════════════════
                "strategies_raw": ", ".join(all_strategies) if all_strategies else None,
                "geographic_focus_raw": row.get("geographic_focus", ""),
                "sectors_raw": ", ".join(all_sectors) if all_sectors else None,
                "fund_size_raw": size_raw,
                "geographic_scope_raw": row.get("geographic_scopes", "").strip() or None,
                "domicile": row.get("fund_domiciliation", "").strip() or None,
                "fee_details": row.get("fee_structure_explanation", "").strip() or None,
                "esg_policy": esg_policy,
                "check_size_min_mm": check_size_min,

                # ══════════════════════════════════════════════════════════
                # AI NORMALIZED VALUES (for matching - stored in fund_ai_profiles)
                # AI algorithms ONLY use these canonical values
                # ══════════════════════════════════════════════════════════
                "ai_strategy_tags": normalized_strategies,
                "ai_geography_tags": normalized_geo,
                "ai_sector_tags": normalized_sectors,
                "ai_size_bucket": size_normalized,
                "ai_size_mm": size_mm,
                "ai_has_esg": esg_policy,
            }


def _parse_investment_amount(raw: str) -> float | None:
    """
    Parse investment amount strings like '€1m', '$5M', '€10 million'.

    Returns:
        Amount in millions as float, or None if unparseable.
    """
    if not raw:
        return None

    # Normalize: lowercase, remove currency symbols
    cleaned = raw.lower().replace("€", "").replace("$", "").replace("£", "").strip()

    # Extract number and multiplier
    import re
    match = re.match(r"([0-9.]+)\s*(m|mm|million|k|thousand|bn|billion)?", cleaned)
    if not match:
        return None

    try:
        value = float(match.group(1))
        unit = match.group(2) or ""

        if unit in ("m", "mm", "million"):
            return value
        elif unit in ("k", "thousand"):
            return value / 1000
        elif unit in ("bn", "billion"):
            return value * 1000
        else:
            # Assume raw millions if no unit
            return value if value < 1000 else value / 1000000
    except ValueError:
        return None
