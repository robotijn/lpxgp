"""Shared utility functions for the LPxGP application.

This module contains utility functions used across multiple routers
to avoid circular imports and code duplication.
"""

from __future__ import annotations

import os
from decimal import Decimal
from typing import Any
from uuid import UUID

import psycopg
from psycopg.rows import dict_row


def serialize_row(row: dict[str, Any]) -> dict[str, Any]:
    """Convert a database row dict to JSON-serializable format.

    Converts UUID objects to strings and Decimal to float for JSON serialization.

    Args:
        row: Database row as a dictionary.

    Returns:
        Dictionary with JSON-serializable values.
    """
    result: dict[str, Any] = {}
    for key, value in row.items():
        if isinstance(value, UUID):
            result[key] = str(value)
        elif isinstance(value, Decimal):
            result[key] = float(value)
        else:
            result[key] = value
    return result


def is_valid_uuid(value: str) -> bool:
    """Check if a string is a valid UUID.

    Used to validate user input before database queries to prevent
    crashes and potential injection attacks.

    Args:
        value: String to validate as UUID.

    Returns:
        True if the string is a valid UUID, False otherwise.
    """
    try:
        UUID(value)
        return True
    except (ValueError, TypeError, AttributeError):
        return False


def get_db() -> psycopg.Connection[dict[str, Any]] | None:
    """Get database connection if configured.

    Creates a new psycopg connection with dict_row factory for easy
    data access. The caller is responsible for closing the connection.

    IMPORTANT: This function automatically selects the appropriate database:
    - In tests (pytest): Uses TEST_DATABASE_URL
    - In production: Uses DATABASE_URL
    - In development: Prefers TEST_DATABASE_URL if set

    Returns:
        psycopg Connection object with dict_row factory, or None if not configured.
    """
    from src.config import get_settings

    settings = get_settings()

    # Check for test database first (from settings or env)
    db_url = settings.test_database_url or os.environ.get("TEST_DATABASE_URL")

    # Fall back to production database
    if not db_url:
        db_url = settings.database_url or os.environ.get("DATABASE_URL")

    if not db_url:
        return None

    return psycopg.connect(db_url, row_factory=dict_row)
