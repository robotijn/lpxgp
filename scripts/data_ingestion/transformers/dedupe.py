"""
Deduplication utilities.
"""
from collections.abc import Callable, Iterator


def dedupe_by_key(
    records: Iterator[dict],
    key_func: Callable[[dict], str],
    merge_func: Callable[[dict, dict], dict] | None = None,
) -> Iterator[dict]:
    """
    Deduplicate records by a key function.

    Args:
        records: Iterator of record dicts
        key_func: Function to extract dedup key from record
        merge_func: Optional function to merge duplicate records.
                   If None, first record wins.

    Yields:
        Deduplicated records
    """
    seen = {}

    for record in records:
        key = key_func(record)
        if not key:
            # Skip records with no key
            continue

        if key in seen:
            if merge_func:
                # Merge with existing
                seen[key] = merge_func(seen[key], record)
        else:
            seen[key] = record

    yield from seen.values()


def merge_prefer_filled(existing: dict, new: dict) -> dict:
    """
    Merge strategy: prefer non-empty values from either record.
    Existing values take precedence if both are filled.
    """
    merged = existing.copy()
    for key, value in new.items():
        if value and not merged.get(key):
            merged[key] = value
    return merged


def create_name_country_key(record: dict) -> str:
    """
    Create a dedup key from normalized name + country.
    Useful for organizations when external_id is not available.
    """
    name = (record.get("name") or "").strip().lower()
    country = (record.get("hq_country") or "").strip().lower()
    return f"{name}|{country}" if name else ""
