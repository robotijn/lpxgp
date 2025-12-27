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
