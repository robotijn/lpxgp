"""Simple in-memory caching for search and matching results.

Provides LRU caching for:
- AI query parsing results (expensive Ollama calls)
- Matching scores (fund-LP combinations)
- Search results (database queries)

The cache is process-local and resets on restart.
For production, consider Redis or database-backed caching.
"""

from __future__ import annotations

import hashlib
import logging
import time
from collections import OrderedDict
from dataclasses import dataclass
from typing import Any

logger = logging.getLogger(__name__)


@dataclass
class CacheEntry[T]:
    """A cached value with metadata."""

    value: T
    created_at: float
    hits: int = 0


@dataclass
class CacheStats:
    """Statistics for cache performance."""

    hits: int = 0
    misses: int = 0
    evictions: int = 0

    @property
    def hit_rate(self) -> float:
        """Calculate hit rate as percentage."""
        total = self.hits + self.misses
        return (self.hits / total * 100) if total > 0 else 0.0


class LRUCache[T]:
    """Simple LRU cache with TTL support.

    Args:
        max_size: Maximum number of entries to keep.
        ttl_seconds: Time-to-live for entries (0 = no expiry).
        name: Name for logging purposes.

    Example:
        >>> cache = LRUCache[dict](max_size=100, ttl_seconds=300, name="search")
        >>> cache.set("query1", {"results": [...]})
        >>> result = cache.get("query1")
    """

    def __init__(
        self,
        max_size: int = 1000,
        ttl_seconds: int = 300,
        name: str = "cache",
    ) -> None:
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.name = name
        self._cache: OrderedDict[str, CacheEntry[T]] = OrderedDict()
        self._stats = CacheStats()

    def get(self, key: str) -> T | None:
        """Get value from cache if exists and not expired.

        Args:
            key: Cache key.

        Returns:
            Cached value or None if miss/expired.
        """
        if key not in self._cache:
            self._stats.misses += 1
            return None

        entry = self._cache[key]

        # Check TTL
        if self.ttl_seconds > 0:
            age = time.time() - entry.created_at
            if age > self.ttl_seconds:
                del self._cache[key]
                self._stats.misses += 1
                return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        entry.hits += 1
        self._stats.hits += 1
        return entry.value

    def set(self, key: str, value: T) -> None:
        """Store value in cache.

        Args:
            key: Cache key.
            value: Value to cache.
        """
        # Remove if exists (to update position)
        if key in self._cache:
            del self._cache[key]

        # Evict oldest if at capacity
        while len(self._cache) >= self.max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._stats.evictions += 1

        self._cache[key] = CacheEntry(value=value, created_at=time.time())

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._stats = CacheStats()

    @property
    def stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._stats

    def __len__(self) -> int:
        return len(self._cache)


def make_cache_key(*args: Any, **kwargs: Any) -> str:
    """Create a deterministic cache key from arguments.

    Args:
        *args: Positional arguments to include in key.
        **kwargs: Keyword arguments to include in key.

    Returns:
        SHA256 hash of the serialized arguments.

    Example:
        >>> key = make_cache_key("pension", aum_min=50)
        >>> print(key[:16])  # Short hash prefix
    """

    # Sort kwargs for deterministic ordering
    key_parts = [str(arg) for arg in args]
    key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
    key_str = "|".join(key_parts)

    return hashlib.sha256(key_str.encode()).hexdigest()


# =============================================================================
# Global Cache Instances
# =============================================================================

# Cache for AI query parsing results (expensive Ollama calls)
# TTL: 5 minutes, Max: 500 entries
ai_query_cache: LRUCache[dict[str, Any]] = LRUCache(
    max_size=500,
    ttl_seconds=300,
    name="ai_query",
)

# Cache for matching scores (fund_id + lp_id -> score)
# TTL: 10 minutes, Max: 10000 entries
match_score_cache: LRUCache[dict[str, Any]] = LRUCache(
    max_size=10000,
    ttl_seconds=600,
    name="match_score",
)

# Cache for search results
# TTL: 2 minutes, Max: 200 entries
search_results_cache: LRUCache[list[dict[str, Any]]] = LRUCache(
    max_size=200,
    ttl_seconds=120,
    name="search_results",
)


def get_cache_stats() -> dict[str, dict[str, Any]]:
    """Get statistics for all caches.

    Returns:
        Dictionary with stats for each cache.
    """
    return {
        "ai_query": {
            "size": len(ai_query_cache),
            "hits": ai_query_cache.stats.hits,
            "misses": ai_query_cache.stats.misses,
            "hit_rate": round(ai_query_cache.stats.hit_rate, 1),
        },
        "match_score": {
            "size": len(match_score_cache),
            "hits": match_score_cache.stats.hits,
            "misses": match_score_cache.stats.misses,
            "hit_rate": round(match_score_cache.stats.hit_rate, 1),
        },
        "search_results": {
            "size": len(search_results_cache),
            "hits": search_results_cache.stats.hits,
            "misses": search_results_cache.stats.misses,
            "hit_rate": round(search_results_cache.stats.hit_rate, 1),
        },
    }


def clear_all_caches() -> None:
    """Clear all caches. Useful for testing."""
    ai_query_cache.clear()
    match_score_cache.clear()
    search_results_cache.clear()
    logger.info("All caches cleared")


# =============================================================================
# Version-Based Cache Invalidation
# =============================================================================


@dataclass
class DataVersion:
    """Represents a snapshot of data state for cache invalidation."""

    entity_type: str  # 'lp', 'gp', 'fund', 'organization'
    row_count: int
    last_modified: str | None  # ISO timestamp or None
    checksum: str  # Hash of count + timestamp

    @classmethod
    def compute(cls, entity_type: str, row_count: int, last_modified: Any) -> "DataVersion":
        """Compute a version from database stats."""
        modified_str = str(last_modified) if last_modified else ""
        checksum = hashlib.md5(f"{row_count}|{modified_str}".encode()).hexdigest()[:8]
        return cls(
            entity_type=entity_type,
            row_count=row_count,
            last_modified=modified_str,
            checksum=checksum,
        )


class CacheVersionManager:
    """Manages cache versions by polling database for changes.

    Uses row count + max(updated_at) as a lightweight change detector.
    Polls periodically to avoid hitting the database on every cache access.

    Example:
        >>> manager = CacheVersionManager(poll_interval=30)
        >>> versions = await manager.get_versions(conn)
        >>> if manager.has_changed("lp", cached_version):
        ...     # Invalidate LP-related caches
    """

    def __init__(self, poll_interval: int = 30) -> None:
        """Initialize the version manager.

        Args:
            poll_interval: Seconds between database polls. Default 30.
        """
        self.poll_interval = poll_interval
        self._versions: dict[str, DataVersion] = {}
        self._last_poll: float = 0
        self._combined_checksum: str = ""

    @property
    def versions(self) -> dict[str, DataVersion]:
        """Get current cached versions."""
        return self._versions

    @property
    def combined_checksum(self) -> str:
        """Get combined checksum of all entity versions.

        Use this to quickly check if ANY data has changed.
        """
        return self._combined_checksum

    def is_stale(self) -> bool:
        """Check if versions need refreshing."""
        return time.time() - self._last_poll > self.poll_interval

    def update_from_db(self, db_stats: dict[str, dict[str, Any]]) -> bool:
        """Update versions from database statistics.

        Args:
            db_stats: Dict of entity_type -> {count, last_modified}

        Returns:
            True if any version changed, False otherwise.

        Example:
            >>> stats = {
            ...     "lp": {"count": 10000, "last_modified": "2024-01-15T10:30:00"},
            ...     "gp": {"count": 5000, "last_modified": "2024-01-15T09:00:00"},
            ... }
            >>> changed = manager.update_from_db(stats)
        """
        old_checksum = self._combined_checksum
        new_versions = {}

        for entity_type, stats in db_stats.items():
            new_versions[entity_type] = DataVersion.compute(
                entity_type=entity_type,
                row_count=stats.get("count", 0),
                last_modified=stats.get("last_modified"),
            )

        self._versions = new_versions
        self._last_poll = time.time()

        # Compute combined checksum
        checksums = sorted(f"{k}:{v.checksum}" for k, v in new_versions.items())
        self._combined_checksum = hashlib.md5("|".join(checksums).encode()).hexdigest()[:12]

        changed = old_checksum != "" and old_checksum != self._combined_checksum
        if changed:
            logger.info(f"Data version changed: {old_checksum} -> {self._combined_checksum}")

        return changed

    def has_entity_changed(self, entity_type: str, cached_checksum: str) -> bool:
        """Check if a specific entity type has changed.

        Args:
            entity_type: The entity type to check ('lp', 'gp', 'fund').
            cached_checksum: The checksum when the cache was created.

        Returns:
            True if entity has changed since cached_checksum was created.
        """
        current = self._versions.get(entity_type)
        if current is None:
            return True  # Unknown entity, assume changed
        return current.checksum != cached_checksum

    def get_checksums(self) -> dict[str, str]:
        """Get current checksums for all entity types.

        Returns:
            Dict of entity_type -> checksum.
        """
        return {k: v.checksum for k, v in self._versions.items()}


# Global version manager instance
version_manager = CacheVersionManager(poll_interval=30)


@dataclass
class VersionedCacheEntry[T]:
    """Cache entry with version tracking for invalidation."""

    value: T
    created_at: float
    checksums: dict[str, str]  # entity_type -> checksum at cache time
    hits: int = 0


class VersionedLRUCache[T]:
    """LRU cache with version-based invalidation.

    Extends basic LRU cache to track data versions and automatically
    invalidate entries when underlying data changes.

    Args:
        entity_types: List of entity types this cache depends on.
        max_size: Maximum number of entries to keep.
        ttl_seconds: Time-to-live for entries (0 = no expiry).
        name: Name for logging purposes.

    Example:
        >>> cache = VersionedLRUCache[list](
        ...     entity_types=["lp", "gp"],
        ...     max_size=100,
        ...     name="search_results"
        ... )
        >>> cache.set("query1", results, version_manager)
        >>> result = cache.get("query1", version_manager)
    """

    def __init__(
        self,
        entity_types: list[str],
        max_size: int = 1000,
        ttl_seconds: int = 300,
        name: str = "cache",
    ) -> None:
        self.entity_types = entity_types
        self.max_size = max_size
        self.ttl_seconds = ttl_seconds
        self.name = name
        self._cache: OrderedDict[str, VersionedCacheEntry[T]] = OrderedDict()
        self._stats = CacheStats()

    def get(self, key: str, vm: CacheVersionManager | None = None) -> T | None:
        """Get value from cache if exists, not expired, and versions match.

        Args:
            key: Cache key.
            vm: Version manager to check for data changes.

        Returns:
            Cached value or None if miss/expired/invalidated.
        """
        if key not in self._cache:
            self._stats.misses += 1
            return None

        entry = self._cache[key]

        # Check TTL
        if self.ttl_seconds > 0:
            age = time.time() - entry.created_at
            if age > self.ttl_seconds:
                del self._cache[key]
                self._stats.misses += 1
                return None

        # Check versions if manager provided
        if vm is not None:
            for entity_type in self.entity_types:
                cached_checksum = entry.checksums.get(entity_type, "")
                if vm.has_entity_changed(entity_type, cached_checksum):
                    # Version mismatch - data changed
                    del self._cache[key]
                    self._stats.misses += 1
                    logger.debug(f"Cache invalidated for {key}: {entity_type} changed")
                    return None

        # Move to end (most recently used)
        self._cache.move_to_end(key)
        entry.hits += 1
        self._stats.hits += 1
        return entry.value

    def set(self, key: str, value: T, vm: CacheVersionManager | None = None) -> None:
        """Store value in cache with current version checksums.

        Args:
            key: Cache key.
            value: Value to cache.
            vm: Version manager to get current checksums.
        """
        # Remove if exists (to update position)
        if key in self._cache:
            del self._cache[key]

        # Evict oldest if at capacity
        while len(self._cache) >= self.max_size:
            oldest_key = next(iter(self._cache))
            del self._cache[oldest_key]
            self._stats.evictions += 1

        # Get current checksums
        checksums = vm.get_checksums() if vm else {}

        self._cache[key] = VersionedCacheEntry(
            value=value,
            created_at=time.time(),
            checksums=checksums,
        )

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()
        self._stats = CacheStats()

    def invalidate_by_entity(self, entity_type: str) -> int:
        """Invalidate all entries that depend on an entity type.

        Args:
            entity_type: Entity type that changed.

        Returns:
            Number of entries invalidated.
        """
        if entity_type not in self.entity_types:
            return 0

        # Clear everything since all entries depend on this entity
        count = len(self._cache)
        self.clear()
        logger.info(f"Invalidated {count} entries in {self.name} due to {entity_type} change")
        return count

    @property
    def stats(self) -> CacheStats:
        """Get cache statistics."""
        return self._stats

    def __len__(self) -> int:
        return len(self._cache)


# =============================================================================
# Database Version Polling
# =============================================================================


def fetch_db_versions_sync(conn: Any) -> dict[str, dict[str, Any]]:
    """Fetch current data versions from database (synchronous).

    Args:
        conn: Database connection with cursor() method.

    Returns:
        Dict of entity_type -> {count, last_modified}.
    """
    with conn.cursor() as cur:
        # Check if tables have updated_at column
        cur.execute("""
            SELECT
                (SELECT COUNT(*) FROM lp_profiles) as lp_count,
                (SELECT COUNT(*) FROM gp_profiles) as gp_count,
                (SELECT COUNT(*) FROM organizations) as org_count
        """)
        row = cur.fetchone()

        # Try to get last modified times (may not exist in all schemas)
        try:
            cur.execute("""
                SELECT
                    (SELECT MAX(created_at) FROM organizations) as org_modified
            """)
            modified_row = cur.fetchone()
            org_modified = modified_row.get("org_modified") if modified_row else None
        except Exception:
            org_modified = None

    return {
        "lp": {"count": row["lp_count"], "last_modified": org_modified},
        "gp": {"count": row["gp_count"], "last_modified": org_modified},
        "organization": {"count": row["org_count"], "last_modified": org_modified},
    }


def refresh_versions_if_stale(conn: Any) -> bool:
    """Refresh version manager if stale.

    Args:
        conn: Database connection.

    Returns:
        True if versions were refreshed and changed, False otherwise.
    """
    if not version_manager.is_stale():
        return False

    stats = fetch_db_versions_sync(conn)
    return version_manager.update_from_db(stats)
