"""Shortlist data model and helper functions.

This module provides the data structures and in-memory storage for
user shortlists. A shortlist allows users to save LPs they're interested
in for later review.

Attributes:
    _shortlists: In-memory storage mapping user_id to list of ShortlistItems.
"""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field


class ShortlistItem(BaseModel):
    """Represents an LP saved to a user's shortlist.

    Attributes:
        lp_id: The unique identifier of the LP organization.
        fund_id: Optional fund context for this shortlist entry.
        notes: User notes about why this LP was shortlisted.
        added_at: ISO timestamp when the LP was added.
        priority: Priority level (1=high, 2=medium, 3=low).
    """

    lp_id: str
    fund_id: str | None = None
    notes: str = ""
    added_at: str = Field(default_factory=lambda: "")
    priority: int = Field(default=2, ge=1, le=3)


class ShortlistAddRequest(BaseModel):
    """Request body for adding an LP to shortlist."""

    lp_id: str
    fund_id: str | None = None
    notes: str = ""
    priority: int = Field(default=2, ge=1, le=3)


class ShortlistUpdateRequest(BaseModel):
    """Request body for updating a shortlist entry."""

    notes: str | None = None
    priority: int | None = Field(default=None, ge=1, le=3)


# In-memory shortlist storage: user_id -> list of ShortlistItems
_shortlists: dict[str, list[ShortlistItem]] = {}


def get_user_shortlist(user_id: str) -> list[ShortlistItem]:
    """Get the shortlist for a user.

    Args:
        user_id: The user's unique identifier.

    Returns:
        List of ShortlistItem objects for this user.
    """
    return _shortlists.get(user_id, [])


def add_to_shortlist(user_id: str, item: ShortlistItem) -> ShortlistItem:
    """Add an LP to a user's shortlist.

    Args:
        user_id: The user's unique identifier.
        item: The ShortlistItem to add.

    Returns:
        The added ShortlistItem with timestamp set.

    Raises:
        ValueError: If LP is already in shortlist.
    """
    if user_id not in _shortlists:
        _shortlists[user_id] = []

    # Check if already exists
    for existing in _shortlists[user_id]:
        if existing.lp_id == item.lp_id and existing.fund_id == item.fund_id:
            raise ValueError("LP already in shortlist")

    # Set timestamp
    item.added_at = datetime.now(UTC).isoformat()
    _shortlists[user_id].append(item)
    return item


def remove_from_shortlist(user_id: str, lp_id: str, fund_id: str | None = None) -> bool:
    """Remove an LP from a user's shortlist.

    Args:
        user_id: The user's unique identifier.
        lp_id: The LP organization ID to remove.
        fund_id: Optional fund context to match.

    Returns:
        True if item was removed, False if not found.
    """
    if user_id not in _shortlists:
        return False

    original_len = len(_shortlists[user_id])
    _shortlists[user_id] = [
        item
        for item in _shortlists[user_id]
        if not (item.lp_id == lp_id and item.fund_id == fund_id)
    ]
    return len(_shortlists[user_id]) < original_len


def update_shortlist_item(
    user_id: str, lp_id: str, updates: ShortlistUpdateRequest
) -> ShortlistItem | None:
    """Update a shortlist item's notes or priority.

    Args:
        user_id: The user's unique identifier.
        lp_id: The LP organization ID to update.
        updates: The fields to update.

    Returns:
        Updated ShortlistItem or None if not found.
    """
    if user_id not in _shortlists:
        return None

    for item in _shortlists[user_id]:
        if item.lp_id == lp_id:
            if updates.notes is not None:
                item.notes = updates.notes
            if updates.priority is not None:
                item.priority = updates.priority
            return item
    return None


def is_in_shortlist(user_id: str, lp_id: str) -> bool:
    """Check if an LP is in the user's shortlist.

    Args:
        user_id: The user's unique identifier.
        lp_id: The LP organization ID to check.

    Returns:
        True if LP is in shortlist, False otherwise.
    """
    if user_id not in _shortlists:
        return False
    return any(item.lp_id == lp_id for item in _shortlists[user_id])


def clear_user_shortlist(user_id: str) -> int:
    """Clear all items from a user's shortlist.

    Args:
        user_id: The user's unique identifier.

    Returns:
        Number of items that were cleared.
    """
    if user_id not in _shortlists:
        return 0
    count = len(_shortlists[user_id])
    _shortlists[user_id] = []
    return count


# =============================================================================
# LP Watchlist (for LP users watching funds)
# =============================================================================


class WatchlistItem(BaseModel):
    """Represents a fund saved to an LP user's watchlist.

    Attributes:
        fund_id: The unique identifier of the fund.
        gp_id: The GP organization that owns the fund.
        notes: User notes about why this fund was watchlisted.
        added_at: ISO timestamp when the fund was added.
    """

    fund_id: str
    gp_id: str | None = None
    notes: str = ""
    added_at: str = Field(default_factory=lambda: "")


# In-memory watchlist storage: lp_user_id -> list of WatchlistItems
_watchlists: dict[str, list[WatchlistItem]] = {}


def get_lp_watchlist(user_id: str) -> list[WatchlistItem]:
    """Get the watchlist for an LP user."""
    return _watchlists.get(user_id, [])


def add_to_watchlist(user_id: str, item: WatchlistItem) -> WatchlistItem:
    """Add a fund to an LP user's watchlist."""
    if user_id not in _watchlists:
        _watchlists[user_id] = []

    for existing in _watchlists[user_id]:
        if existing.fund_id == item.fund_id:
            raise ValueError("Fund already in watchlist")

    item.added_at = datetime.now(UTC).isoformat()
    _watchlists[user_id].append(item)
    return item


def is_fund_in_watchlist(user_id: str, fund_id: str) -> bool:
    """Check if a fund is in the LP user's watchlist."""
    if user_id not in _watchlists:
        return False
    return any(item.fund_id == fund_id for item in _watchlists[user_id])


# =============================================================================
# Mutual Interest Detection
# =============================================================================


class MutualInterest(BaseModel):
    """Represents a mutual interest between GP and LP.

    When a GP shortlists an LP, and that LP has the GP's fund
    in their watchlist, we have mutual interest.
    """

    lp_id: str
    lp_name: str
    gp_id: str
    gp_name: str
    fund_id: str
    fund_name: str
    detected_at: str


# Cache of detected mutual interests
_mutual_interests: list[MutualInterest] = []


def detect_mutual_interests(
    gp_shortlists: dict[str, list[ShortlistItem]],
    lp_watchlists: dict[str, list[WatchlistItem]],
    lp_info: dict[str, dict],
    gp_info: dict[str, dict],
    fund_info: dict[str, dict],
) -> list[MutualInterest]:
    """Detect mutual interest between GPs and LPs.

    Args:
        gp_shortlists: GP user_id -> list of shortlisted LPs
        lp_watchlists: LP user_id -> list of watchlisted funds
        lp_info: LP user_id -> {name, lp_id}
        gp_info: GP user_id -> {name, gp_id}
        fund_info: fund_id -> {name, gp_id}

    Returns:
        List of MutualInterest objects.
    """
    results: list[MutualInterest] = []

    # For each GP's shortlisted LP
    for gp_user_id, shortlist in gp_shortlists.items():
        gp = gp_info.get(gp_user_id, {})

        for item in shortlist:
            lp_id = item.lp_id
            # Check if any LP user has the GP's fund in their watchlist
            for lp_user_id, watchlist in lp_watchlists.items():
                lp = lp_info.get(lp_user_id, {})
                if lp.get("lp_id") != lp_id:
                    continue

                for watched in watchlist:
                    fund = fund_info.get(watched.fund_id, {})
                    if fund.get("gp_id") == gp.get("gp_id"):
                        results.append(
                            MutualInterest(
                                lp_id=lp_id,
                                lp_name=lp.get("name", "Unknown LP"),
                                gp_id=gp.get("gp_id", ""),
                                gp_name=gp.get("name", "Unknown GP"),
                                fund_id=watched.fund_id,
                                fund_name=fund.get("name", "Unknown Fund"),
                                detected_at=datetime.now(UTC).isoformat(),
                            )
                        )

    return results


def get_mutual_interest_for_lp(lp_id: str) -> list[MutualInterest]:
    """Get all mutual interests involving a specific LP."""
    return [mi for mi in _mutual_interests if mi.lp_id == lp_id]


def get_mutual_interest_for_fund(fund_id: str) -> list[MutualInterest]:
    """Get all mutual interests involving a specific fund."""
    return [mi for mi in _mutual_interests if mi.fund_id == fund_id]


def has_mutual_interest(lp_id: str, fund_id: str) -> bool:
    """Check if there's mutual interest between an LP and fund."""
    return any(
        mi.lp_id == lp_id and mi.fund_id == fund_id for mi in _mutual_interests
    )
