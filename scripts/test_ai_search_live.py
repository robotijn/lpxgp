#!/usr/bin/env python3
"""Live test of AI-powered LP search with Ollama.

This script tests the AI search functionality against a running Ollama instance
and the test database with 10k records.

Usage:
    uv run python scripts/test_ai_search_live.py
"""

import asyncio
import sys
import time
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent))

import psycopg
from psycopg.rows import dict_row

from src.cache import clear_all_caches, get_cache_stats
from src.config import get_settings
from src.search import build_lp_search_sql, is_natural_language_query, parse_lp_search_query


def print_header(text: str) -> None:
    """Print a formatted header."""
    print("\n" + "=" * 60)
    print(f"  {text}")
    print("=" * 60)


def print_section(text: str) -> None:
    """Print a section header."""
    print(f"\n  {text}")
    print("  " + "-" * 50)


async def test_query(query: str, conn) -> dict:
    """Test a single query and return results."""
    print(f"\n  Query: \"{query}\"")

    # Check if it's natural language
    is_nl = is_natural_language_query(query)
    print(f"    Natural language: {is_nl}")

    if not is_nl:
        print("    Skipping AI parsing (simple text search)")
        return {"query": query, "is_nl": False}

    # Parse with AI
    start = time.time()
    filters = await parse_lp_search_query(query, use_cache=True)
    parse_time = filters.get("_parse_time_ms", 0)
    cache_hit = filters.get("_cache_hit", False)

    # Remove metadata for display
    display_filters = {k: v for k, v in filters.items() if not k.startswith("_")}
    print(f"    Parsed filters: {display_filters}")
    print(f"    Parse time: {parse_time:.1f}ms (cache hit: {cache_hit})")

    # Build SQL
    where_clause, params = build_lp_search_sql(filters)
    print(f"    SQL WHERE: {where_clause[:80]}...")

    # Execute query
    start_db = time.time()
    with conn.cursor() as cur:
        cur.execute(f"""
            SELECT o.id, o.name, o.hq_city, o.hq_country,
                   lp.lp_type, lp.total_aum_bn, lp.strategies
            FROM organizations o
            JOIN lp_profiles lp ON lp.org_id = o.id
            WHERE {where_clause}
            ORDER BY lp.total_aum_bn DESC NULLS LAST
            LIMIT 10
        """, params)
        results = cur.fetchall()

    db_time = (time.time() - start_db) * 1000
    print(f"    DB query time: {db_time:.1f}ms")
    print(f"    Results: {len(results)} LPs found")

    if results:
        print("    Top 3:")
        for i, r in enumerate(results[:3]):
            aum = f"${r['total_aum_bn']:.1f}B" if r['total_aum_bn'] else "N/A"
            print(f"      {i+1}. {r['name']} ({r['lp_type']}, {aum})")

    return {
        "query": query,
        "is_nl": True,
        "filters": display_filters,
        "parse_time_ms": parse_time,
        "cache_hit": cache_hit,
        "db_time_ms": db_time,
        "result_count": len(results),
    }


async def main():
    print_header("LIVE AI SEARCH TEST WITH OLLAMA")

    # Check settings
    settings = get_settings()
    print(f"\n  Ollama URL: {settings.ollama_base_url}")
    print(f"  Ollama Model: {settings.ollama_model}")

    # Connect to database
    if not settings.test_database_url:
        print("  ERROR: TEST_DATABASE_URL not configured")
        return

    conn = psycopg.connect(settings.test_database_url, row_factory=dict_row)

    # Get DB stats
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM lp_profiles")
        lp_count = cur.fetchone()["count"]
    print(f"  Database: {lp_count:,} LPs")

    # Clear caches for clean test
    clear_all_caches()
    print("  Caches cleared")

    # Test queries
    test_queries = [
        # AUM queries
        "50m or more aum",
        "investors with at least 1 billion aum",
        "small funds under 100 million",

        # LP type queries
        "pension funds",
        "family offices in europe",
        "endowments with growth strategy",

        # Location queries
        "investors in california",
        "funds based in new york",
        "european pension funds",

        # Strategy queries
        "buyout investors",
        "growth equity funds with 500m check size",
        "venture capital friendly LPs",

        # Complex queries
        "pension funds in california with over 100m aum focused on buyout",
        "family offices that accept emerging managers",

        # Simple text (should NOT use AI)
        "CalPERS",
        "Harvard",
    ]

    print_section("Testing Queries (First Pass - No Cache)")
    results = []
    for query in test_queries:
        result = await test_query(query, conn)
        results.append(result)

    print_section("Cache Statistics After First Pass")
    stats = get_cache_stats()
    print(f"    AI Query Cache:")
    print(f"      Size: {stats['ai_query']['size']}")
    print(f"      Hits: {stats['ai_query']['hits']}")
    print(f"      Misses: {stats['ai_query']['misses']}")

    print_section("Testing Repeated Queries (Cache Hits)")
    # Run same queries again to test caching
    cache_test_queries = [
        "50m or more aum",
        "pension funds",
        "investors in california",
    ]

    for query in cache_test_queries:
        result = await test_query(query, conn)
        if result.get("cache_hit"):
            print(f"    ✓ Cache hit confirmed!")

    print_section("Final Cache Statistics")
    stats = get_cache_stats()
    print(f"    AI Query Cache:")
    print(f"      Size: {stats['ai_query']['size']}")
    print(f"      Hits: {stats['ai_query']['hits']}")
    print(f"      Misses: {stats['ai_query']['misses']}")
    print(f"      Hit Rate: {stats['ai_query']['hit_rate']:.1f}%")

    print_section("Performance Summary")
    nl_results = [r for r in results if r.get("is_nl")]
    if nl_results:
        avg_parse = sum(r["parse_time_ms"] for r in nl_results) / len(nl_results)
        avg_db = sum(r["db_time_ms"] for r in nl_results) / len(nl_results)
        print(f"    Average AI parse time: {avg_parse:.1f}ms")
        print(f"    Average DB query time: {avg_db:.1f}ms")
        print(f"    Total queries tested: {len(results)}")
        print(f"    Natural language queries: {len(nl_results)}")

    conn.close()
    print("\n" + "=" * 60)
    print("  TEST COMPLETE")
    print("=" * 60 + "\n")


if __name__ == "__main__":
    asyncio.run(main())
