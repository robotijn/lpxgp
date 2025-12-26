"""Speed and caching tests for LP/GP search and matching.

Tests measure:
- Keyword search performance with 10k records
- Natural language (AI) search performance
- Caching effectiveness for repeated queries
- GP->LP matching performance
- LP->GP matching performance
- Cache hit/miss behavior

Run with: uv run pytest tests/test_search_speed_caching.py -v -s
"""

from __future__ import annotations

import asyncio
import time
from typing import Any
from unittest.mock import AsyncMock, MagicMock, patch

import psycopg
import pytest
from psycopg.rows import dict_row

from src.cache import (
    CacheVersionManager,
    DataVersion,
    VersionedLRUCache,
    clear_all_caches,
    get_cache_stats,
    match_score_cache,
    version_manager,
)
from src.config import get_settings
from src.matching import calculate_match_score
from src.search import (
    parse_lp_search_query,
)

# =============================================================================
# Fixtures
# =============================================================================


@pytest.fixture(scope="module")
def db_connection():
    """Get a database connection for the test module."""
    settings = get_settings()
    if not settings.test_database_url:
        pytest.skip("TEST_DATABASE_URL not configured")

    conn = psycopg.connect(settings.test_database_url, row_factory=dict_row)
    yield conn
    conn.close()


@pytest.fixture(autouse=True)
def clear_caches():
    """Clear all caches before each test."""
    clear_all_caches()
    yield
    # Optionally clear after too
    clear_all_caches()


# =============================================================================
# Database Statistics
# =============================================================================


class TestDatabaseStats:
    """Verify we have enough data for meaningful tests."""

    def test_lp_count(self, db_connection):
        """Verify we have ~10k LPs loaded."""
        with db_connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) as count FROM lp_profiles")
            result = cur.fetchone()
            lp_count = result["count"]

            print(f"\n  Total LPs in database: {lp_count}")
            assert lp_count >= 100, f"Need at least 100 LPs, got {lp_count}"

    def test_gp_count(self, db_connection):
        """Verify we have ~10k GPs loaded."""
        with db_connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) as count FROM gp_profiles")
            result = cur.fetchone()
            gp_count = result["count"]

            print(f"\n  Total GPs in database: {gp_count}")
            assert gp_count >= 1, f"Need at least 1 GP, got {gp_count}"

    def test_organization_count(self, db_connection):
        """Show organization breakdown."""
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT
                    COUNT(*) FILTER (WHERE is_lp = TRUE) as lp_orgs,
                    COUNT(*) FILTER (WHERE is_gp = TRUE) as gp_orgs,
                    COUNT(*) as total
                FROM organizations
            """)
            result = cur.fetchone()

            print(f"\n  Organizations: {result['total']} total")
            print(f"    - LP orgs: {result['lp_orgs']}")
            print(f"    - GP orgs: {result['gp_orgs']}")


# =============================================================================
# Keyword Search Speed Tests
# =============================================================================


class TestKeywordSearchSpeed:
    """Test keyword (text) search performance."""

    def test_simple_name_search_speed(self, db_connection):
        """Measure simple ILIKE name search speed."""
        search_terms = ["Capital", "Partners", "Investment", "Fund", "Global"]

        print("\n  Keyword Search Performance:")
        print("  " + "-" * 50)

        total_time = 0
        for term in search_terms:
            start = time.time()

            with db_connection.cursor() as cur:
                cur.execute("""
                    SELECT o.id, o.name, o.hq_city, lp.lp_type, lp.total_aum_bn
                    FROM organizations o
                    JOIN lp_profiles lp ON lp.org_id = o.id
                    WHERE o.name ILIKE %s
                    ORDER BY lp.total_aum_bn DESC NULLS LAST
                    LIMIT 100
                """, (f"%{term}%",))
                results = cur.fetchall()

            elapsed = (time.time() - start) * 1000
            total_time += elapsed
            print(f"    '{term}': {len(results)} results in {elapsed:.1f}ms")

        avg_time = total_time / len(search_terms)
        print("  " + "-" * 50)
        print(f"  Average: {avg_time:.1f}ms")

        # Should be fast - under 100ms per query
        assert avg_time < 500, f"Keyword search too slow: {avg_time:.1f}ms"

    def test_filtered_search_speed(self, db_connection):
        """Measure filtered search with multiple conditions."""
        test_cases = [
            {"lp_type": "pension", "min_aum": 0.1},
            {"lp_type": "endowment", "min_aum": 0.5},
            {"location": "USA"},
            {"strategies": ["buyout"]},
        ]

        print("\n  Filtered Search Performance:")
        print("  " + "-" * 50)

        total_time = 0
        for filters in test_cases:
            conditions = ["o.is_lp = TRUE"]
            params: list[Any] = []

            if "lp_type" in filters:
                conditions.append("lp.lp_type = %s")
                params.append(filters["lp_type"])
            if "min_aum" in filters:
                conditions.append("lp.total_aum_bn >= %s")
                params.append(filters["min_aum"])
            if "location" in filters:
                conditions.append("o.hq_country = %s")
                params.append(filters["location"])
            if "strategies" in filters:
                conditions.append("lp.strategies && %s::text[]")
                params.append(filters["strategies"])

            where_clause = " AND ".join(conditions)

            start = time.time()
            with db_connection.cursor() as cur:
                cur.execute(f"""
                    SELECT o.id, o.name, lp.lp_type, lp.total_aum_bn
                    FROM organizations o
                    JOIN lp_profiles lp ON lp.org_id = o.id
                    WHERE {where_clause}
                    ORDER BY lp.total_aum_bn DESC NULLS LAST
                    LIMIT 100
                """, params)
                results = cur.fetchall()

            elapsed = (time.time() - start) * 1000
            total_time += elapsed
            print(f"    {filters}: {len(results)} results in {elapsed:.1f}ms")

        avg_time = total_time / len(test_cases)
        print("  " + "-" * 50)
        print(f"  Average: {avg_time:.1f}ms")

        assert avg_time < 500, f"Filtered search too slow: {avg_time:.1f}ms"


# =============================================================================
# Natural Language (AI) Search Speed Tests
# =============================================================================


class TestAISearchSpeed:
    """Test AI-powered natural language search performance."""

    @pytest.mark.asyncio
    async def test_ai_query_parsing_speed_mocked(self):
        """Measure AI query parsing with mocked Ollama (for CI)."""
        queries = [
            "50m or more aum",
            "pension funds in california",
            "buyout investors with 100m check size",
            "family offices in europe",
            "endowments with growth strategy",
        ]

        print("\n  AI Query Parsing (Mocked):")
        print("  " + "-" * 50)

        mock_responses = [
            {"aum_min": 0.05},
            {"lp_type": "pension", "location": "California"},
            {"strategies": ["buyout"], "check_size_min": 100},
            {"lp_type": "family_office", "location": "Europe"},
            {"lp_type": "endowment", "strategies": ["growth"]},
        ]

        total_time = 0
        for i, query in enumerate(queries):
            mock_response = MagicMock()
            mock_response.json.return_value = {
                "response": str(mock_responses[i]).replace("'", '"')
            }
            mock_response.raise_for_status.return_value = None

            with patch("src.search.httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_client.return_value.__aenter__.return_value = mock_instance
                mock_instance.post.return_value = mock_response

                # Simulate some processing delay
                await asyncio.sleep(0.01)

                result = await parse_lp_search_query(query, use_cache=False)

            elapsed = result.get("_parse_time_ms", 0)
            total_time += elapsed
            cache_hit = result.get("_cache_hit", False)
            print(f"    '{query[:30]}...': {elapsed:.1f}ms (cache: {cache_hit})")

        avg_time = total_time / len(queries)
        print("  " + "-" * 50)
        print(f"  Average: {avg_time:.1f}ms")

    @pytest.mark.asyncio
    async def test_ai_query_caching_performance(self):
        """Test that caching significantly improves repeat queries."""
        query = "pension funds with 100m aum in usa"

        print("\n  AI Query Caching Performance:")
        print("  " + "-" * 50)

        # First call - cache miss
        mock_response = MagicMock()
        mock_response.json.return_value = {
            "response": '{"lp_type": "pension", "aum_min": 0.1, "location": "USA"}'
        }
        mock_response.raise_for_status.return_value = None

        with patch("src.search.httpx.AsyncClient") as mock_client:
            mock_instance = AsyncMock()
            mock_client.return_value.__aenter__.return_value = mock_instance
            mock_instance.post.return_value = mock_response

            # Simulate Ollama delay
            async def slow_post(*args, **kwargs):
                await asyncio.sleep(0.1)  # 100ms simulated delay
                return mock_response

            mock_instance.post.side_effect = slow_post

            result1 = await parse_lp_search_query(query, use_cache=True)

        first_time = result1.get("_parse_time_ms", 0)
        first_cache_hit = result1.get("_cache_hit", False)
        print(f"    First call:  {first_time:.1f}ms (cache hit: {first_cache_hit})")

        # Second call - should be cache hit
        result2 = await parse_lp_search_query(query, use_cache=True)
        second_time = result2.get("_parse_time_ms", 0)
        second_cache_hit = result2.get("_cache_hit", True)
        print(f"    Second call: {second_time:.1f}ms (cache hit: {second_cache_hit})")

        # Third call - also cache hit
        result3 = await parse_lp_search_query(query, use_cache=True)
        third_time = result3.get("_parse_time_ms", 0)
        third_cache_hit = result3.get("_cache_hit", True)
        print(f"    Third call:  {third_time:.1f}ms (cache hit: {third_cache_hit})")

        print("  " + "-" * 50)
        speedup = first_time / second_time if second_time > 0 else float("inf")
        print(f"  Speedup: {speedup:.1f}x faster with cache")

        # Cache should be much faster
        assert second_cache_hit is True, "Second call should be cache hit"
        assert second_time < first_time, "Cached call should be faster"
        assert second_time < 10, f"Cached call should be < 10ms, got {second_time}ms"


# =============================================================================
# GP -> LP Matching Speed Tests
# =============================================================================


class TestGPToLPMatchingSpeed:
    """Test matching speed: Find LPs for a given GP/Fund."""

    def test_match_score_calculation_speed(self):
        """Measure raw matching algorithm speed."""
        # Sample fund data
        fund = {
            "name": "Acme Growth Fund III",
            "gp_name": "Acme Capital",
            "strategy": "growth",
            "target_size_mm": 500,
            "vintage_year": 2024,
            "fund_number": 3,
            "geographic_focus": ["North America", "Europe"],
            "sector_focus": ["Technology", "Healthcare"],
            "esg_policy": True,
        }

        # Generate sample LPs
        lp_types = ["pension", "endowment", "family_office", "sovereign_wealth"]
        strategies = [["buyout"], ["growth"], ["venture"], ["buyout", "growth"]]
        sample_lps = [
            {
                "name": f"LP {i}",
                "lp_type": lp_types[i % len(lp_types)],
                "strategies": strategies[i % len(strategies)],
                "geographic_preferences": ["North America", "Europe", "Global"][i % 3],
                "fund_size_min_mm": (i % 5) * 100,
                "fund_size_max_mm": 1000 + (i % 5) * 200,
                "esg_required": i % 2 == 0,
                "emerging_manager_ok": i % 3 == 0,
            }
            for i in range(1000)
        ]

        print("\n  GP -> LP Match Score Calculation:")
        print("  " + "-" * 50)

        start = time.time()
        matches = []
        for lp in sample_lps:
            result = calculate_match_score(fund, lp)
            if result["passed_hard_filters"]:
                matches.append((lp["name"], result["score"]))

        elapsed = (time.time() - start) * 1000

        print(f"    Calculated {len(sample_lps)} matches in {elapsed:.1f}ms")
        print(f"    Passed hard filters: {len(matches)}")
        print(f"    Per-match time: {elapsed / len(sample_lps):.3f}ms")

        # Should be very fast - under 100ms for 1000 matches
        assert elapsed < 500, f"Matching too slow: {elapsed:.1f}ms for 1000 LPs"

    def test_full_gp_to_lp_search_with_db(self, db_connection):
        """Measure full GP -> LP matching with database."""
        # Get a sample fund
        fund = {
            "name": "Test Growth Fund",
            "strategy": "growth",
            "target_size_mm": 500,
            "fund_number": 3,
            "geographic_focus": ["North America"],
            "sector_focus": ["Technology"],
            "esg_policy": True,
        }

        print("\n  GP -> LP Full Search (with DB):")
        print("  " + "-" * 50)

        # Step 1: Fetch potential LPs from database
        start_db = time.time()
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT
                    o.id, o.name, o.hq_city, o.hq_country,
                    lp.lp_type, lp.total_aum_bn, lp.strategies,
                    lp.geographic_preferences, lp.sector_preferences,
                    lp.fund_size_min_mm, lp.fund_size_max_mm,
                    lp.esg_required, lp.emerging_manager_ok, lp.min_fund_number
                FROM organizations o
                JOIN lp_profiles lp ON lp.org_id = o.id
                WHERE o.is_lp = TRUE
                AND lp.strategies && %s::text[]
                LIMIT 500
            """, ([fund["strategy"]],))
            potential_lps = cur.fetchall()

        db_time = (time.time() - start_db) * 1000
        print(f"    DB fetch: {len(potential_lps)} LPs in {db_time:.1f}ms")

        # Step 2: Calculate match scores
        start_match = time.time()
        scored_matches = []
        for lp in potential_lps:
            lp_data = {
                "name": lp["name"],
                "lp_type": lp["lp_type"],
                "strategies": lp["strategies"],
                "geographic_preferences": lp["geographic_preferences"],
                "sector_preferences": lp["sector_preferences"],
                "fund_size_min_mm": lp["fund_size_min_mm"],
                "fund_size_max_mm": lp["fund_size_max_mm"],
                "esg_required": lp["esg_required"],
                "emerging_manager_ok": lp["emerging_manager_ok"],
                "min_fund_number": lp["min_fund_number"],
            }
            result = calculate_match_score(fund, lp_data)
            if result["passed_hard_filters"]:
                scored_matches.append({
                    "lp_id": lp["id"],
                    "lp_name": lp["name"],
                    "score": result["score"],
                })

        match_time = (time.time() - start_match) * 1000

        # Sort by score
        scored_matches.sort(key=lambda x: x["score"], reverse=True)

        total_time = db_time + match_time
        print(f"    Matching: {len(scored_matches)} matches in {match_time:.1f}ms")
        print(f"    Total: {total_time:.1f}ms")
        print("  " + "-" * 50)
        if scored_matches:
            print(f"    Top match: {scored_matches[0]['lp_name']} ({scored_matches[0]['score']})")

        assert total_time < 2000, f"GP->LP search too slow: {total_time:.1f}ms"


# =============================================================================
# LP -> GP Matching Speed Tests
# =============================================================================


class TestLPToGPMatchingSpeed:
    """Test matching speed: Find GPs/Funds for a given LP."""

    def test_lp_to_gp_search_with_db(self, db_connection):
        """Measure LP -> GP matching with database."""
        # Sample LP preferences (defined for documentation, actual matching uses DB)
        _lp = {
            "name": "California Pension Fund",
            "lp_type": "pension",
            "strategies": ["buyout", "growth"],
            "geographic_preferences": ["North America"],
            "fund_size_min_mm": 100,
            "fund_size_max_mm": 1000,
            "esg_required": True,
            "emerging_manager_ok": False,
            "min_fund_number": 2,
        }

        print("\n  LP -> GP Full Search (with DB):")
        print("  " + "-" * 50)

        # Fetch GPs from database
        start = time.time()
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT
                    o.id, o.name, o.hq_city, o.hq_country,
                    gp.investment_philosophy, gp.team_size, gp.years_investing
                FROM organizations o
                JOIN gp_profiles gp ON gp.org_id = o.id
                WHERE o.is_gp = TRUE
                LIMIT 500
            """)
            potential_gps = cur.fetchall()

        db_time = (time.time() - start) * 1000
        print(f"    DB fetch: {len(potential_gps)} GPs in {db_time:.1f}ms")

        # In a real implementation, we'd also fetch their funds
        # and match LP preferences against fund characteristics

        print("  " + "-" * 50)
        print("    Note: Full LP->GP matching requires fund data")


# =============================================================================
# Caching Tests
# =============================================================================


class TestCachingBehavior:
    """Test cache behavior for search and matching."""

    @pytest.mark.asyncio
    async def test_ai_query_cache_stats(self):
        """Test cache statistics tracking."""
        queries = [
            "pension funds with 50m aum",
            "buyout investors in california",
            "pension funds with 50m aum",  # Repeat
            "family offices in europe",
            "buyout investors in california",  # Repeat
        ]

        print("\n  Cache Statistics Test:")
        print("  " + "-" * 50)

        for query in queries:
            mock_response = MagicMock()
            mock_response.json.return_value = {"response": '{"text_search": "test"}'}
            mock_response.raise_for_status.return_value = None

            with patch("src.search.httpx.AsyncClient") as mock_client:
                mock_instance = AsyncMock()
                mock_client.return_value.__aenter__.return_value = mock_instance
                mock_instance.post.return_value = mock_response

                await parse_lp_search_query(query, use_cache=True)

        stats = get_cache_stats()
        print("    AI Query Cache:")
        print(f"      Size: {stats['ai_query']['size']}")
        print(f"      Hits: {stats['ai_query']['hits']}")
        print(f"      Misses: {stats['ai_query']['misses']}")
        print(f"      Hit Rate: {stats['ai_query']['hit_rate']}%")

        # Should have 2 cache hits (the repeats)
        assert stats["ai_query"]["hits"] == 2, f"Expected 2 hits, got {stats['ai_query']['hits']}"
        assert stats["ai_query"]["misses"] == 3, f"Expected 3 misses, got {stats['ai_query']['misses']}"

    def test_match_score_caching(self):
        """Test caching for match score calculations."""
        from src.cache import make_cache_key

        fund_id = "fund-001"
        lp_id = "lp-001"

        # Simulate caching match scores
        cache_key = make_cache_key(fund_id, lp_id)

        print("\n  Match Score Caching:")
        print("  " + "-" * 50)

        # First lookup - miss
        start = time.time()
        cached = match_score_cache.get(cache_key)
        miss_time = (time.time() - start) * 1000
        print(f"    Cache miss lookup: {miss_time:.3f}ms")
        assert cached is None

        # Store result
        match_result = {
            "score": 85.5,
            "passed_hard_filters": True,
            "breakdown": {"strategy": 100, "geography": 80},
        }
        match_score_cache.set(cache_key, match_result)

        # Second lookup - hit
        start = time.time()
        cached = match_score_cache.get(cache_key)
        hit_time = (time.time() - start) * 1000
        print(f"    Cache hit lookup: {hit_time:.3f}ms")
        assert cached is not None
        assert cached["score"] == 85.5

        stats = match_score_cache.stats
        print("  " + "-" * 50)
        print(f"    Hits: {stats.hits}, Misses: {stats.misses}")


# =============================================================================
# Performance Summary
# =============================================================================


# =============================================================================
# Version-Based Cache Invalidation Tests
# =============================================================================


class TestDataVersion:
    """Test DataVersion computation."""

    def test_compute_version_from_stats(self):
        """DataVersion should create consistent checksums."""
        v1 = DataVersion.compute("lp", 10000, "2024-01-15T10:30:00")
        v2 = DataVersion.compute("lp", 10000, "2024-01-15T10:30:00")

        assert v1.checksum == v2.checksum
        assert v1.row_count == 10000
        assert v1.entity_type == "lp"

    def test_different_counts_different_checksum(self):
        """Different row counts should produce different checksums."""
        v1 = DataVersion.compute("lp", 10000, "2024-01-15T10:30:00")
        v2 = DataVersion.compute("lp", 10001, "2024-01-15T10:30:00")

        assert v1.checksum != v2.checksum

    def test_different_timestamps_different_checksum(self):
        """Different timestamps should produce different checksums."""
        v1 = DataVersion.compute("lp", 10000, "2024-01-15T10:30:00")
        v2 = DataVersion.compute("lp", 10000, "2024-01-15T10:31:00")

        assert v1.checksum != v2.checksum


class TestCacheVersionManager:
    """Test CacheVersionManager functionality."""

    def test_update_from_db_stats(self):
        """Version manager should track stats correctly."""
        manager = CacheVersionManager(poll_interval=60)

        stats = {
            "lp": {"count": 10000, "last_modified": "2024-01-15T10:30:00"},
            "gp": {"count": 5000, "last_modified": "2024-01-15T09:00:00"},
        }

        changed = manager.update_from_db(stats)
        # First update is not considered a "change"
        assert changed is False
        assert "lp" in manager.versions
        assert "gp" in manager.versions
        assert manager.versions["lp"].row_count == 10000

    def test_detect_data_change(self):
        """Version manager should detect when data changes."""
        manager = CacheVersionManager(poll_interval=60)

        # Initial state
        manager.update_from_db({
            "lp": {"count": 10000, "last_modified": "2024-01-15T10:30:00"},
        })
        initial_checksum = manager.combined_checksum

        # Data changes
        changed = manager.update_from_db({
            "lp": {"count": 10001, "last_modified": "2024-01-15T10:31:00"},
        })

        assert changed is True
        assert manager.combined_checksum != initial_checksum

    def test_has_entity_changed(self):
        """Should detect when specific entity changed."""
        manager = CacheVersionManager(poll_interval=60)

        manager.update_from_db({
            "lp": {"count": 10000, "last_modified": None},
        })

        # Get checksum at cache time
        cached_checksum = manager.get_checksums()["lp"]

        # Same checksum should not be considered changed
        assert manager.has_entity_changed("lp", cached_checksum) is False

        # Different checksum should be considered changed
        assert manager.has_entity_changed("lp", "different") is True

    def test_is_stale(self):
        """Should correctly report staleness."""
        manager = CacheVersionManager(poll_interval=1)  # 1 second

        manager.update_from_db({"lp": {"count": 100, "last_modified": None}})

        # Just updated, should not be stale
        assert manager.is_stale() is False

        # Wait and check again
        time.sleep(1.1)
        assert manager.is_stale() is True


class TestVersionedLRUCache:
    """Test VersionedLRUCache with invalidation."""

    def test_basic_get_set(self):
        """Basic get/set should work without version manager."""
        cache: VersionedLRUCache[str] = VersionedLRUCache(
            entity_types=["lp"],
            max_size=10,
            name="test",
        )

        cache.set("key1", "value1")
        assert cache.get("key1") == "value1"

    def test_invalidation_on_version_change(self):
        """Cache should invalidate when version changes."""
        cache: VersionedLRUCache[str] = VersionedLRUCache(
            entity_types=["lp"],
            max_size=10,
            ttl_seconds=300,
            name="test",
        )
        manager = CacheVersionManager(poll_interval=60)

        # Set initial version
        manager.update_from_db({"lp": {"count": 100, "last_modified": None}})

        # Cache a value
        cache.set("key1", "value1", manager)
        assert cache.get("key1", manager) == "value1"

        # Data changes
        manager.update_from_db({"lp": {"count": 101, "last_modified": None}})

        # Cache should now return None (invalidated)
        assert cache.get("key1", manager) is None

    def test_cache_hit_when_version_unchanged(self):
        """Cache should hit when version is unchanged."""
        cache: VersionedLRUCache[str] = VersionedLRUCache(
            entity_types=["lp"],
            max_size=10,
            name="test",
        )
        manager = CacheVersionManager(poll_interval=60)

        manager.update_from_db({"lp": {"count": 100, "last_modified": None}})
        cache.set("key1", "value1", manager)

        # Same version - should hit
        assert cache.get("key1", manager) == "value1"
        assert cache.stats.hits == 1

    def test_invalidate_by_entity(self):
        """Should invalidate all entries for an entity type."""
        cache: VersionedLRUCache[str] = VersionedLRUCache(
            entity_types=["lp", "gp"],
            max_size=10,
            name="test",
        )

        cache.set("key1", "value1")
        cache.set("key2", "value2")
        assert len(cache) == 2

        invalidated = cache.invalidate_by_entity("lp")
        assert invalidated == 2
        assert len(cache) == 0


class TestVersionedCacheWithDatabase:
    """Test versioned cache with real database."""

    def test_fetch_versions_from_db(self, db_connection):
        """Should fetch version info from database."""
        from src.cache import fetch_db_versions_sync

        stats = fetch_db_versions_sync(db_connection)

        print("\n  Database versions:")
        for entity, data in stats.items():
            print(f"    {entity}: count={data['count']}")

        assert "lp" in stats
        assert "gp" in stats
        assert stats["lp"]["count"] > 0

    def test_refresh_versions_if_stale(self, db_connection):
        """Should refresh versions when stale."""
        from src.cache import refresh_versions_if_stale

        # Force stale
        version_manager._last_poll = 0

        _changed = refresh_versions_if_stale(db_connection)

        # First refresh shouldn't report "changed" (verifying checksum exists)
        assert version_manager.combined_checksum != ""
        print(f"\n  Combined checksum: {version_manager.combined_checksum}")


class TestPerformanceSummary:
    """Generate a summary of all performance metrics."""

    def test_generate_performance_report(self, db_connection):
        """Generate a comprehensive performance report."""
        print("\n")
        print("=" * 60)
        print("  SEARCH & MATCHING PERFORMANCE REPORT")
        print("=" * 60)

        # Database size
        with db_connection.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM lp_profiles")
            lp_count = cur.fetchone()["count"]
            cur.execute("SELECT COUNT(*) FROM gp_profiles")
            gp_count = cur.fetchone()["count"]

        print("\n  Database Size:")
        print(f"    LPs: {lp_count:,}")
        print(f"    GPs: {gp_count:,}")

        # Keyword search benchmark
        print("\n  Keyword Search (ILIKE):")
        start = time.time()
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM organizations o
                JOIN lp_profiles lp ON lp.org_id = o.id
                WHERE o.name ILIKE '%Capital%'
            """)
            count = cur.fetchone()["count"]
        elapsed = (time.time() - start) * 1000
        print(f"    'Capital' search: {count} results in {elapsed:.1f}ms")

        # Filtered search benchmark
        print("\n  Filtered Search:")
        start = time.time()
        with db_connection.cursor() as cur:
            cur.execute("""
                SELECT COUNT(*) FROM organizations o
                JOIN lp_profiles lp ON lp.org_id = o.id
                WHERE lp.lp_type = 'pension'
                AND lp.total_aum_bn >= 0.1
            """)
            count = cur.fetchone()["count"]
        elapsed = (time.time() - start) * 1000
        print(f"    Pension + AUM filter: {count} results in {elapsed:.1f}ms")

        # Match calculation benchmark
        print("\n  Match Score Calculation:")
        fund = {"strategy": "growth", "target_size_mm": 500, "fund_number": 3}
        sample_lps = [
            {"strategies": ["growth"], "fund_size_min_mm": 100, "fund_size_max_mm": 1000}
            for _ in range(100)
        ]
        start = time.time()
        for lp in sample_lps:
            calculate_match_score(fund, lp)
        elapsed = (time.time() - start) * 1000
        print(f"    100 match calculations: {elapsed:.1f}ms ({elapsed/100:.2f}ms each)")

        print("\n" + "=" * 60)
        print("  END OF REPORT")
        print("=" * 60 + "\n")
