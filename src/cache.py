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
