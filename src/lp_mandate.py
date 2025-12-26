"""LP Mandate management.

This module provides in-memory storage for LP mandate preferences.
In production, this would be backed by a database (lp_profiles table).
"""

from __future__ import annotations

from pydantic import BaseModel


class LPMandate(BaseModel):
    """LP investment mandate preferences.

    Attributes:
        strategies: List of preferred investment strategies.
        check_size_min_mm: Minimum check size in millions.
        check_size_max_mm: Maximum check size in millions.
        geographies: List of preferred geographic regions.
        sectors: List of preferred sectors.
    """

    strategies: list[str] = []
    check_size_min_mm: float | None = None
    check_size_max_mm: float | None = None
    geographies: list[str] = []
    sectors: list[str] = []


# Available options for mandate form
STRATEGY_OPTIONS = [
    ("buyout", "Buyout"),
    ("growth_equity", "Growth Equity"),
    ("venture", "Venture Capital"),
    ("credit", "Private Credit"),
    ("real_estate", "Real Estate"),
    ("infrastructure", "Infrastructure"),
    ("secondaries", "Secondaries"),
    ("fund_of_funds", "Fund of Funds"),
]

GEOGRAPHY_OPTIONS = [
    ("north_america", "North America"),
    ("europe", "Europe"),
    ("asia_pacific", "Asia Pacific"),
    ("latin_america", "Latin America"),
    ("middle_east", "Middle East & Africa"),
    ("global", "Global / Multi-Region"),
]

SECTOR_OPTIONS = [
    ("technology", "Technology"),
    ("healthcare", "Healthcare"),
    ("consumer", "Consumer"),
    ("industrials", "Industrials"),
    ("financial_services", "Financial Services"),
    ("energy", "Energy"),
    ("real_estate", "Real Estate"),
    ("telecommunications", "Telecommunications"),
    ("materials", "Materials"),
    ("generalist", "Generalist / Multi-Sector"),
]


# In-memory mandate storage: user_id -> LPMandate
_lp_mandates: dict[str, LPMandate] = {}


def get_lp_mandate(user_id: str) -> LPMandate:
    """Get mandate for an LP user, creating defaults if needed.

    Args:
        user_id: The user's unique identifier.

    Returns:
        LPMandate object for the user.
    """
    if user_id not in _lp_mandates:
        _lp_mandates[user_id] = LPMandate()
    return _lp_mandates[user_id]


def set_lp_mandate(user_id: str, mandate: LPMandate) -> None:
    """Set mandate for an LP user.

    Args:
        user_id: The user's unique identifier.
        mandate: The mandate to set.
    """
    _lp_mandates[user_id] = mandate


def update_lp_mandate(user_id: str, mandate: LPMandate) -> LPMandate:
    """Update an LP user's mandate.

    Args:
        user_id: The user's unique identifier.
        mandate: The new mandate to set.

    Returns:
        Updated LPMandate object.
    """
    _lp_mandates[user_id] = mandate
    return mandate
