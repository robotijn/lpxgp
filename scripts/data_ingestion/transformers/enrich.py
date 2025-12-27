"""
Data enrichment utilities.
"""
from ..config import FUND_STATUS_MAP, LP_TYPE_MAP


def map_fund_status(raw_status: str | None) -> str:
    """
    Map raw fund status from source to our status enum.
    Default to 'draft' if unknown.
    """
    if not raw_status:
        return "draft"
    return FUND_STATUS_MAP.get(raw_status.strip(), "draft")


def map_lp_type(raw_type: str | None) -> str | None:
    """
    Map raw LP type from source to our lp_type enum.
    """
    if not raw_type:
        return None
    normalized = raw_type.strip().lower()
    return LP_TYPE_MAP.get(normalized)


def detect_org_type(record: dict, lp_org_ids: set, gp_org_ids: set) -> tuple[bool, bool]:
    """
    Determine if an organization is LP, GP, or both.

    Args:
        record: Organization record with external_id
        lp_org_ids: Set of external_ids for known LPs
        gp_org_ids: Set of external_ids for known GPs

    Returns:
        (is_lp, is_gp) tuple
    """
    ext_id = record.get("external_id", "")
    is_lp = ext_id in lp_org_ids
    is_gp = ext_id in gp_org_ids
    return (is_lp, is_gp)


def parse_strategies(raw: str | None) -> list[str]:
    """
    Parse comma-separated strategy string into list.
    """
    if not raw:
        return []
    return [s.strip() for s in raw.split(",") if s.strip()]


def parse_geographic_preferences(raw: str | None) -> list[str]:
    """
    Parse geographic preferences from various formats.
    """
    if not raw:
        return []
    # Handle comma, semicolon, or pipe separated
    for sep in ["|", ";", ","]:
        if sep in raw:
            return [g.strip() for g in raw.split(sep) if g.strip()]
    return [raw.strip()] if raw.strip() else []


# =============================================================================
# NORMALIZATION MAPS - Simplify varied source values to canonical forms
# =============================================================================

STRATEGY_NORMALIZATION = {
    # Private Equity
    "buyout": "buyout",
    "buyout-6": "buyout",
    "Buyout": "buyout",
    "lbo": "buyout",
    "development / minority": "growth",
    "development-minority-1": "growth",
    "Development / Minority": "growth",
    "growth equity": "growth",
    "growth": "growth",
    "turnaround / restructuring": "turnaround",
    "turnaround-restructuring-3": "turnaround",
    "Turnaround / Restructuring": "turnaround",
    "distressed": "turnaround",
    "co-investment": "coinvest",
    "co-investment-3": "coinvest",
    "Co-investment": "coinvest",
    "fund of funds": "fof",
    "fund-of-funds-10": "fof",
    "Fund of funds": "fof",
    "secondaries": "secondaries",
    "secondaries-8": "secondaries",
    "Secondaries": "secondaries",

    # Venture Capital
    "seed / early stage": "venture_seed",
    "seed-early-stage-1": "venture_seed",
    "Seed / early stage": "venture_seed",
    "seed": "venture_seed",
    "early stage": "venture_seed",
    "late stage / growth": "venture_growth",
    "late-stage-growth-1": "venture_growth",
    "Late stage / growth": "venture_growth",
    "growth stage": "venture_growth",

    # Private Debt
    "direct lending": "debt_direct",
    "direct-lending-1": "debt_direct",
    "Direct lending": "debt_direct",
    "mezzanine": "debt_mezz",
    "mezzanine-2": "debt_mezz",
    "Mezzanine": "debt_mezz",
    "special situations": "debt_special",
    "special-situations-3": "debt_special",
    "Special situations": "debt_special",
    "specialty finance": "debt_specialty",
    "specialty-finance-1": "debt_specialty",
    "Specialty finance": "debt_specialty",

    # Real Assets
    "infrastructure": "infra",
    "infrastructure-4": "infra",
    "Infrastructure": "infra",
    "real estate": "real_estate",
    "real-estate-4": "real_estate",
    "Real estate": "real_estate",
    "natural resources": "natural_resources",
    "natural-resources-2": "natural_resources",
    "Natural resources": "natural_resources",

    # Other
    "gp stakes": "gp_stakes",
    "gp-stakes-3": "gp_stakes",
    "other private markets": "other",
    "other-private-markets-3": "other",
}

GEOGRAPHY_NORMALIZATION = {
    # Western Europe
    "western_europe": "europe_west",
    "france": "europe_west",
    "germany": "europe_west",
    "uk": "europe_west",
    "united_kingdom": "europe_west",
    "spain": "europe_west",
    "italy": "europe_west",
    "netherlands": "europe_west",
    "belgium": "europe_west",
    "luxembourg": "europe_west",
    "switzerland": "europe_west",
    "austria": "europe_west",
    "portugal": "europe_west",
    "ireland": "europe_west",
    "scandinavian countries": "europe_north",
    "nordics": "europe_north",
    "sweden": "europe_north",
    "norway": "europe_north",
    "denmark": "europe_north",
    "finland": "europe_north",

    # Eastern Europe
    "central_eastern_europe": "europe_east",
    "eastern_europe": "europe_east",
    "poland": "europe_east",
    "czech_republic": "europe_east",
    "hungary": "europe_east",
    "romania": "europe_east",
    "ukraine": "europe_east",
    "turkey": "europe_east",
    "russia": "europe_east",
    "balkans": "europe_east",

    # North America
    "north_america": "north_america",
    "usa": "north_america",
    "united_states": "north_america",
    "canada": "north_america",

    # Asia Pacific
    "asia_pacific": "asia_pac",
    "asia": "asia_pac",
    "china": "asia_pac",
    "japan": "asia_pac",
    "korea": "asia_pac",
    "south_korea": "asia_pac",
    "india": "asia_pac",
    "southeast_asia": "asia_pac",
    "australia": "asia_pac",
    "new_zealand": "asia_pac",

    # Other regions
    "latin_america": "latam",
    "south_america": "latam",
    "brazil": "latam",
    "mexico": "latam",
    "middle_east": "mena",
    "mena": "mena",
    "africa": "africa",
    "sub_saharan_africa": "africa",

    # Scopes
    "global": "global",
    "Global": "global",
    "international-pan-regional": "global",
    "pan-european": "europe",
    "national": "national",
    "local": "local",
}

FUND_SIZE_NORMALIZATION = {
    "Micro (0-€100m)": "micro",
    "micro-0-eur100m-2": "micro",
    "Small (€100m-€500m)": "small",
    "small-eur100m-eur500m-2": "small",
    "Mid (€500m-€2bn)": "mid",
    "mid-eur500m-eur2bn-2": "mid",
    "Large (€2bn-€10bn)": "large",
    "large-eur2bn-eur10bn-2": "large",
    "Mega (>€10bn)": "mega",
    "mega-eur10bn-2": "mega",
}

SECTOR_NORMALIZATION = {
    "Technology and software": "tech",
    "technology-and-software-1": "tech",
    "Healthcare": "healthcare",
    "healthcare-3": "healthcare",
    "Consumer goods and services": "consumer",
    "consumer-goods-and-services-1": "consumer",
    "Communication and media": "media",
    "communication-and-media-1": "media",
    "Energy / Utilities": "energy",
    "energy-utilities-1": "energy",
    "Financial services": "finserv",
    "financial-services-1": "finserv",
    "Industrial": "industrial",
    "industrial-2": "industrial",
    "Business services": "bizserv",
    "business-services-1": "bizserv",
}


def normalize_strategy(raw: str) -> str | None:
    """Normalize a single strategy value to canonical form."""
    if not raw:
        return None
    key = raw.strip().lower()
    return STRATEGY_NORMALIZATION.get(key) or STRATEGY_NORMALIZATION.get(raw.strip())


def normalize_strategies(raw_list: list[str]) -> list[str]:
    """Normalize a list of strategies, removing duplicates."""
    normalized = set()
    for raw in raw_list:
        norm = normalize_strategy(raw)
        if norm:
            normalized.add(norm)
    return sorted(normalized)


def normalize_geography(raw: str) -> str | None:
    """Normalize a single geography value to canonical form."""
    if not raw:
        return None
    key = raw.strip().lower().replace(" ", "_").replace("-", "_")
    return GEOGRAPHY_NORMALIZATION.get(key) or GEOGRAPHY_NORMALIZATION.get(raw.strip())


def normalize_geographies(raw_list: list[str]) -> list[str]:
    """Normalize a list of geographies, removing duplicates."""
    normalized = set()
    for raw in raw_list:
        norm = normalize_geography(raw)
        if norm:
            normalized.add(norm)
    return sorted(normalized)


def normalize_fund_size(raw: str | None) -> str | None:
    """Normalize fund size category."""
    if not raw:
        return None
    return FUND_SIZE_NORMALIZATION.get(raw.strip())


def normalize_sectors(raw_list: list[str]) -> list[str]:
    """Normalize sector list."""
    normalized = set()
    for raw in raw_list:
        key = raw.strip()
        norm = SECTOR_NORMALIZATION.get(key)
        if norm:
            normalized.add(norm)
    return sorted(normalized)


def parse_fund_size_to_mm(raw: str | None) -> float | None:
    """
    Parse fund size category to midpoint in millions.

    Returns:
        Midpoint of range in EUR millions, or None
    """
    if not raw:
        return None

    size_map = {
        "micro": 50,      # 0-100M → 50M
        "small": 300,     # 100-500M → 300M
        "mid": 1250,      # 500M-2B → 1.25B
        "large": 6000,    # 2-10B → 6B
        "mega": 15000,    # 10B+ → 15B estimate
    }

    normalized = normalize_fund_size(raw)
    return size_map.get(normalized)


def calculate_acceptance_rate(received: int, accepted: int) -> float | None:
    """
    Calculate LP acceptance rate from behavioral data.

    Returns:
        Rate as decimal (0.0-1.0) or None if no data
    """
    if not received or received == 0:
        return None
    return round(accepted / received, 3)
