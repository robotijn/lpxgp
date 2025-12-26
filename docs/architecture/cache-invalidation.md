# Cache Invalidation Strategy

## Problem

The LRU caches store query results and match scores that depend on database data. When LPs, GPs, or funds change, cached results become stale.

## Cache Types and Dependencies

| Cache | Depends On | Invalidation Trigger |
|-------|------------|---------------------|
| `ai_query_cache` | Nothing (just text parsing) | TTL only (5 min) |
| `search_results_cache` | LP/GP data | LP or GP changes |
| `match_score_cache` | Fund + LP data | Fund or LP changes |

## Solution: Version-Based Invalidation

### Concept

1. Track a **version number** for each entity type (lp, gp, fund)
2. Increment version on any INSERT, UPDATE, or DELETE
3. Store version number with each cache entry
4. On cache lookup, compare stored version with current version
5. If versions differ → cache miss (data changed)

### Benefits

- **O(1) check**: Just compare two integers
- **O(1) update**: Increment counter on change
- **Accurate**: Catches all changes via database triggers
- **No scanning**: Don't need to hash or scan data

### Implementation

#### 1. Database Table

```sql
CREATE TABLE cache_versions (
    entity_type TEXT PRIMARY KEY,  -- 'lp', 'gp', 'fund', 'organization'
    version BIGINT NOT NULL DEFAULT 1,
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

INSERT INTO cache_versions (entity_type) VALUES
    ('organization'),
    ('lp'),
    ('gp'),
    ('fund');
```

#### 2. Database Triggers

```sql
-- Function to increment version
CREATE OR REPLACE FUNCTION increment_cache_version()
RETURNS TRIGGER AS $$
BEGIN
    UPDATE cache_versions
    SET version = version + 1, updated_at = NOW()
    WHERE entity_type = TG_ARGV[0];
    RETURN NULL;
END;
$$ LANGUAGE plpgsql;

-- Triggers for each table
CREATE TRIGGER lp_profiles_cache_invalidate
AFTER INSERT OR UPDATE OR DELETE ON lp_profiles
FOR EACH STATEMENT EXECUTE FUNCTION increment_cache_version('lp');

CREATE TRIGGER gp_profiles_cache_invalidate
AFTER INSERT OR UPDATE OR DELETE ON gp_profiles
FOR EACH STATEMENT EXECUTE FUNCTION increment_cache_version('gp');

CREATE TRIGGER funds_cache_invalidate
AFTER INSERT OR UPDATE OR DELETE ON funds
FOR EACH STATEMENT EXECUTE FUNCTION increment_cache_version('fund');

CREATE TRIGGER organizations_cache_invalidate
AFTER INSERT OR UPDATE OR DELETE ON organizations
FOR EACH STATEMENT EXECUTE FUNCTION increment_cache_version('organization');
```

#### 3. Python Cache Enhancement

```python
# In src/cache.py

@dataclass
class VersionedCacheEntry[T]:
    """Cache entry with version tracking."""
    value: T
    created_at: float
    versions: dict[str, int]  # entity_type -> version at cache time
    hits: int = 0


class VersionedLRUCache[T](LRUCache[T]):
    """LRU cache with version-based invalidation."""

    def __init__(
        self,
        entity_types: list[str],  # Which entity types to track
        **kwargs
    ):
        super().__init__(**kwargs)
        self.entity_types = entity_types

    def get(self, key: str, current_versions: dict[str, int]) -> T | None:
        """Get value, checking versions match."""
        entry = super().get(key)
        if entry is None:
            return None

        # Check if any tracked version has changed
        for entity_type in self.entity_types:
            cached_ver = entry.versions.get(entity_type, 0)
            current_ver = current_versions.get(entity_type, 0)
            if cached_ver != current_ver:
                # Version mismatch - data changed, invalidate
                del self._cache[key]
                self._stats.misses += 1
                return None

        return entry.value

    def set(self, key: str, value: T, versions: dict[str, int]) -> None:
        """Store value with current versions."""
        # ... store with versions
```

#### 4. Version Fetching

```python
# In src/cache.py

async def get_current_versions(conn) -> dict[str, int]:
    """Fetch current cache versions from database."""
    with conn.cursor() as cur:
        cur.execute("SELECT entity_type, version FROM cache_versions")
        return {row["entity_type"]: row["version"] for row in cur.fetchall()}
```

### Usage Flow

```
1. User searches "pension funds in california"
2. Generate cache key from query
3. Fetch current versions: {"lp": 42, "gp": 15, ...}
4. Check cache:
   - If hit AND versions match → return cached results
   - If miss OR versions differ → execute query, cache with versions
5. Return results
```

### Alternative: Lightweight Polling

If triggers are too invasive, use periodic polling:

```python
class CacheVersionManager:
    """Manages cache versions with polling."""

    def __init__(self, poll_interval: int = 60):
        self._versions: dict[str, int] = {}
        self._last_poll: float = 0
        self._poll_interval = poll_interval

    async def get_versions(self, conn) -> dict[str, int]:
        """Get versions, polling if stale."""
        now = time.time()
        if now - self._last_poll > self._poll_interval:
            self._versions = await self._fetch_versions(conn)
            self._last_poll = now
        return self._versions

    async def _fetch_versions(self, conn) -> dict[str, int]:
        """Fast version check using aggregate queries."""
        with conn.cursor() as cur:
            cur.execute("""
                SELECT
                    (SELECT COUNT(*) FROM lp_profiles) as lp_count,
                    (SELECT MAX(updated_at) FROM lp_profiles) as lp_updated,
                    (SELECT COUNT(*) FROM gp_profiles) as gp_count,
                    (SELECT MAX(updated_at) FROM gp_profiles) as gp_updated
            """)
            row = cur.fetchone()
            # Create pseudo-version from count + timestamp hash
            return {
                "lp": hash((row["lp_count"], str(row["lp_updated"]))),
                "gp": hash((row["gp_count"], str(row["gp_updated"]))),
            }
```

### Comparison

| Approach | Accuracy | Performance | Complexity |
|----------|----------|-------------|------------|
| DB Triggers | Exact | O(1) check | Medium (DB changes) |
| Polling w/ Count+Time | Good | O(1) check, periodic poll | Low |
| Full Table Hash | Exact | O(n) per check | Low |
| TTL Only | Eventual | O(1) | Very Low |

### Recommendation

1. **Start with TTL only** (current implementation) - simple, works for most cases
2. **Add polling** when needed - no DB changes required
3. **Add triggers** for production - most accurate, best performance

## Implementation Priority

1. ✅ TTL-based expiry (current)
2. 🔲 Add `updated_at` column to tables (if not present)
3. 🔲 Implement polling-based version check
4. 🔲 Add database triggers for real-time invalidation (M5+)
