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
