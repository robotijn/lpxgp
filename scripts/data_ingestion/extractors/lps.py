"""
Extract LP data from lp_matchmaking.csv.

Maps to lp_profiles + lp_ai_profiles tables.
"""
import csv
from pathlib import Path
from typing import Iterator

from ..transformers.enrich import (
    normalize_strategies,
    normalize_geographies,
    calculate_acceptance_rate,
)


def extract_lps(filepath: Path) -> Iterator[dict]:
    """
    Extract LP profiles from lp_matchmaking.csv.

    Yields dicts with:
    - Raw data for lp_profiles (client display)
    - AI normalized data for lp_ai_profiles (matching)
    - Behavioral metrics (solicitations, engagement)

    Args:
        filepath: Path to lp_matchmaking.csv

    Yields:
        Dict with LP profile data
    """
    with open(filepath, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)

        for row in reader:
            # Skip rows without org_id
            org_external_id = row.get("organization_id", "").strip()
            if not org_external_id:
                continue

            # Parse behavioral metrics
            solicitations_received = _parse_int(row.get("solicitations_received"))
            solicitations_accepted = _parse_int(row.get("solicitations_accepted"))
            solicitations_declined = _parse_int(row.get("solicitations_declined"))

            # Calculate acceptance rate
            acceptance_rate = calculate_acceptance_rate(
                solicitations_received,
                solicitations_accepted
            )

            # Parse contact info
            first_name = row.get("first_name", "").strip()
            last_name = row.get("last_name", "").strip()
            full_name = f"{first_name} {last_name}".strip()

            # Parse engagement timestamps
            last_login = row.get("lastlogin_at", "").strip() or None
            last_activity = row.get("lastactivity_at", "").strip() or None

            # Determine lp_type from organization name (heuristic)
            org_name = row.get("organization_name", "").lower()
            lp_type = _infer_lp_type(org_name)

            # Event participation
            is_participating = row.get("is_participating_at_paris_2025", "").lower() == "yes"

            # Infer geographic preference from country
            country = row.get("country_name", "").strip()
            inferred_geography = _infer_geography_from_country(country)

            yield {
                # ── IDENTIFIERS ──
                "org_external_id": org_external_id,
                "org_name": row.get("organization_name", "").strip(),
                "external_source": "ipem",

                # ── CONTACT PERSON ──
                "contact_user_id": row.get("lp_user_id", "").strip() or None,
                "contact_name": full_name if full_name else None,
                "contact_title": row.get("title", "").strip() or None,
                "contact_email": row.get("email", "").strip() or None,
                "contact_phone": row.get("telephoneFixe", "").strip() or None,
                "contact_mobile": row.get("telephonePort", "").strip() or None,

                # ── RAW DATA (for client display) ──
                "country_raw": country,
                "lp_type_raw": lp_type,  # Inferred, could be overwritten by actual data

                # ── BEHAVIORAL METRICS ──
                "solicitations_received": solicitations_received,
                "solicitations_accepted": solicitations_accepted,
                "solicitations_declined": solicitations_declined,
                "acceptance_rate": acceptance_rate,
                "last_login_at": last_login,
                "last_activity_at": last_activity,

                # ── EVENT PARTICIPATION ──
                "event_participation": ["ipem_paris_2025"] if is_participating else [],

                # ── AI NORMALIZED DATA (for matching) ──
                "ai_lp_type": lp_type,
                "ai_geography_interests": inferred_geography,
                "ai_strategy_interests": [],  # Not in CSV, would come from form data
                "ai_sector_interests": [],    # Not in CSV, would come from form data

                # ── ENGAGEMENT SCORING ──
                "engagement_score": _calculate_engagement_score(
                    solicitations_received,
                    acceptance_rate,
                    last_activity,
                ),
            }


def _parse_int(value: str | None) -> int:
    """Parse string to int, defaulting to 0."""
    if not value:
        return 0
    try:
        return int(value)
    except ValueError:
        return 0


def _infer_lp_type(org_name: str) -> str:
    """
    Infer LP type from organization name.

    This is a heuristic - actual type should come from form data.
    """
    name_lower = org_name.lower()

    if "family office" in name_lower or "family-office" in name_lower:
        return "family_office"
    if "pension" in name_lower:
        return "pension"
    if "endowment" in name_lower:
        return "endowment"
    if "foundation" in name_lower:
        return "foundation"
    if "insurance" in name_lower or "assurance" in name_lower or "mutuelle" in name_lower:
        return "insurance"
    if "fund of funds" in name_lower or "fof" in name_lower:
        return "fund_of_funds"
    if "sovereign" in name_lower:
        return "sovereign_wealth"

    return "other"


def _infer_geography_from_country(country: str) -> list[str]:
    """
    Infer geographic interests from LP's country.

    Assumption: LPs tend to prefer investments in their own region.
    """
    country_lower = country.lower()

    # Western Europe
    western_europe = [
        "france", "germany", "royaume-uni", "united kingdom", "uk",
        "espagne", "spain", "italie", "italy", "pays-bas", "netherlands",
        "belgique", "belgium", "luxembourg", "suisse", "switzerland",
        "autriche", "austria", "portugal", "irlande", "ireland",
    ]
    if country_lower in western_europe:
        return ["europe_west"]

    # Nordic
    nordic = ["suède", "sweden", "norvège", "norway", "danemark", "denmark", "finlande", "finland"]
    if country_lower in nordic:
        return ["europe_north"]

    # US/Canada
    north_america = ["états-unis", "united states", "usa", "canada"]
    if country_lower in north_america:
        return ["north_america"]

    # Middle East
    middle_east = ["israël", "israel", "émirats", "uae", "qatar", "arabie", "saudi"]
    if any(me in country_lower for me in middle_east):
        return ["middle_east"]

    # Asia
    asia = ["chine", "china", "japon", "japan", "singapour", "singapore", "hong kong"]
    if any(a in country_lower for a in asia):
        return ["asia_pacific"]

    return ["global"]


def _calculate_engagement_score(
    solicitations_received: int,
    acceptance_rate: float | None,
    last_activity: str | None,
) -> float:
    """
    Calculate engagement score (0.0 to 1.0).

    Based on:
    - Volume of interactions (30%)
    - Acceptance rate (40%)
    - Activity recency (30%)
    """
    score = 0.0

    # Volume component (0-30 points)
    if solicitations_received >= 100:
        score += 0.3
    elif solicitations_received >= 50:
        score += 0.2
    elif solicitations_received >= 10:
        score += 0.1

    # Acceptance rate component (0-40 points)
    if acceptance_rate is not None:
        score += acceptance_rate * 0.4

    # Recency component (0-30 points)
    # If we have last_activity, they're somewhat engaged
    if last_activity:
        score += 0.2  # Has recent activity
        # Could add datetime parsing for more granular scoring

    return round(min(score, 1.0), 2)
