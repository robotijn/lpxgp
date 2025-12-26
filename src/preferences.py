"""User preferences management.

This module provides in-memory storage for user preferences.
In production, this would be backed by a database.
"""

from __future__ import annotations

from pydantic import BaseModel


class UserPreferences(BaseModel):
    """User notification and display preferences.

    Attributes:
        email_new_matches: Email about new LP matches.
        email_weekly_summary: Weekly summary of fund activity.
        email_marketing: Marketing and product updates.
    """

    email_new_matches: bool = True
    email_weekly_summary: bool = True
    email_marketing: bool = False


# In-memory preferences storage: user_id -> UserPreferences
_user_preferences: dict[str, UserPreferences] = {}


def get_user_preferences(user_id: str) -> UserPreferences:
    """Get preferences for a user, creating defaults if needed.

    Args:
        user_id: The user's unique identifier.

    Returns:
        UserPreferences object for the user.
    """
    if user_id not in _user_preferences:
        _user_preferences[user_id] = UserPreferences()
    return _user_preferences[user_id]


def set_user_preferences(user_id: str, preferences: UserPreferences) -> None:
    """Set preferences for a user.

    Args:
        user_id: The user's unique identifier.
        preferences: The preferences to set.
    """
    _user_preferences[user_id] = preferences


def update_user_preferences(
    user_id: str, preferences: UserPreferences
) -> UserPreferences:
    """Update a user's preferences.

    Args:
        user_id: The user's unique identifier.
        preferences: The new preferences to set.

    Returns:
        Updated UserPreferences object.
    """
    _user_preferences[user_id] = preferences
    return preferences
