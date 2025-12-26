#!/usr/bin/env python3
"""Load seed data into the TEST database.

SAFETY: This script ONLY operates on TEST_DATABASE_URL, NEVER on production.

This script loads the pre-generated LP and GP data from JSON files
into the PostgreSQL TEST database.

Usage:
    uv run python scripts/load_seed_data.py [--lps] [--gps] [--clear]

Options:
    --lps     Load only LPs
    --gps     Load only GPs
    --clear   Clear existing seed data before loading
    --limit N Only load first N records (for testing)

Environment:
    Requires TEST_DATABASE_URL environment variable.
    Will REFUSE to run if only DATABASE_URL is set (production protection).
"""

import argparse
import json
import sys
from pathlib import Path

import psycopg2
from psycopg2.extras import execute_values

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

from src.config import get_settings

SEED_DIR = Path(__file__).parent.parent / "data" / "seed"


def verify_test_database() -> str:
    """Verify we're connecting to a TEST database, not production."""
    settings = get_settings()

    if not settings.test_database_url:
        print("ERROR: TEST_DATABASE_URL is not configured!")
        print("This script ONLY operates on the test database.")
        print("Set TEST_DATABASE_URL in your .env file.")
        sys.exit(1)

    return settings.test_database_url


def get_connection():
    """Get TEST database connection (with safety checks)."""
    db_url = verify_test_database()
    return psycopg2.connect(db_url)


def clear_seed_data(conn):
    """Clear all seed data (keeps demo data)."""
    print("Clearing existing seed data...")
    with conn.cursor() as cur:
        # Delete organizations that don't have specific demo IDs
        # Keep the 8 demo LPs and any user-created data
        cur.execute("""
            DELETE FROM organizations
            WHERE id NOT IN (
                -- Demo LP IDs (keep these)
                'a1000001-0000-0000-0000-000000000001',
                'a1000002-0000-0000-0000-000000000002',
                'a1000003-0000-0000-0000-000000000003',
                'a1000004-0000-0000-0000-000000000004',
                'a1000005-0000-0000-0000-000000000005',
                'a1000006-0000-0000-0000-000000000006',
                'a1000007-0000-0000-0000-000000000007',
                'a1000008-0000-0000-0000-000000000008',
                -- Demo GP IDs (keep these)
                'c0000001-0000-0000-0000-000000000001'
            )
            AND name LIKE 'SEED_%'
        """)
        deleted = cur.rowcount
        conn.commit()
        print(f"Deleted {deleted} seed organizations")


def load_lps(conn, limit: int | None = None):
    """Load LP seed data."""
    lp_file = SEED_DIR / "lps_10k.json"
    if not lp_file.exists():
        print(f"Error: {lp_file} not found. Run generate_seed_data.py first.")
        return

    print(f"Loading LPs from {lp_file}...")
    with open(lp_file) as f:
        lps = json.load(f)

    if limit:
        lps = lps[:limit]

    print(f"Inserting {len(lps)} LPs...")

    with conn.cursor() as cur:
        # Prepare organization data
        org_data = []
        for lp in lps:
            org = lp["organization"]
            org_data.append((
                lp["id"],
                f"SEED_{org['name']}",  # Prefix to identify seed data
                org["website"],
                org["hq_city"],
                org["hq_country"],
                org["description"],
                org["is_gp"],
                org["is_lp"],
            ))

        # Insert organizations
        execute_values(
            cur,
            """
            INSERT INTO organizations (id, name, website, hq_city, hq_country, description, is_gp, is_lp)
            VALUES %s
            ON CONFLICT (id) DO NOTHING
            """,
            org_data,
            page_size=1000
        )
        print(f"  Inserted {cur.rowcount} organizations")

        # Prepare LP profile data
        profile_data = []
        for lp in lps:
            p = lp["profile"]
            profile_data.append((
                lp["id"],  # org_id
                p["lp_type"],
                p["total_aum_bn"],
                p["pe_allocation_pct"],
                p["strategies"],
                p["geographic_preferences"],
                p["sector_preferences"],
                p["check_size_min_mm"],
                p["check_size_max_mm"],
                p["fund_size_min_mm"],
                p["fund_size_max_mm"],
                p["min_track_record_years"],
                p["min_fund_number"],
                p["esg_required"],
                p["emerging_manager_ok"],
            ))

        # Insert LP profiles
        execute_values(
            cur,
            """
            INSERT INTO lp_profiles (
                org_id, lp_type, total_aum_bn, pe_allocation_pct,
                strategies, geographic_preferences, sector_preferences,
                check_size_min_mm, check_size_max_mm, fund_size_min_mm, fund_size_max_mm,
                min_track_record_years, min_fund_number, esg_required, emerging_manager_ok
            )
            VALUES %s
            ON CONFLICT (org_id) DO NOTHING
            """,
            profile_data,
            page_size=1000
        )
        print(f"  Inserted {cur.rowcount} LP profiles")

    conn.commit()
    print("LPs loaded successfully!")


def load_gps(conn, limit: int | None = None):
    """Load GP seed data."""
    gp_file = SEED_DIR / "gps_10k.json"
    if not gp_file.exists():
        print(f"Error: {gp_file} not found. Run generate_seed_data.py first.")
        return

    print(f"Loading GPs from {gp_file}...")
    with open(gp_file) as f:
        gps = json.load(f)

    if limit:
        gps = gps[:limit]

    print(f"Inserting {len(gps)} GPs...")

    with conn.cursor() as cur:
        # Prepare organization data
        org_data = []
        for gp in gps:
            org = gp["organization"]
            org_data.append((
                gp["id"],
                f"SEED_{org['name']}",  # Prefix to identify seed data
                org["website"],
                org["hq_city"],
                org["hq_country"],
                org["description"],
                org["is_gp"],
                org["is_lp"],
            ))

        # Insert organizations
        execute_values(
            cur,
            """
            INSERT INTO organizations (id, name, website, hq_city, hq_country, description, is_gp, is_lp)
            VALUES %s
            ON CONFLICT (id) DO NOTHING
            """,
            org_data,
            page_size=1000
        )
        print(f"  Inserted {cur.rowcount} organizations")

        # Prepare GP profile data
        profile_data = []
        for gp in gps:
            p = gp["profile"]
            profile_data.append((
                gp["id"],  # org_id
                p["investment_philosophy"],
                p["team_size"],
                p["years_investing"],
                p["spun_out_from"],
                json.dumps(p["notable_exits"]),
                json.dumps(p["track_record_summary"]),
            ))

        # Insert GP profiles
        execute_values(
            cur,
            """
            INSERT INTO gp_profiles (
                org_id, investment_philosophy, team_size, years_investing,
                spun_out_from, notable_exits, track_record_summary
            )
            VALUES %s
            ON CONFLICT (org_id) DO NOTHING
            """,
            profile_data,
            page_size=1000
        )
        print(f"  Inserted {cur.rowcount} GP profiles")

    conn.commit()
    print("GPs loaded successfully!")


def main():
    parser = argparse.ArgumentParser(description="Load seed data into database")
    parser.add_argument("--lps", action="store_true", help="Load only LPs")
    parser.add_argument("--gps", action="store_true", help="Load only GPs")
    parser.add_argument("--clear", action="store_true", help="Clear seed data first")
    parser.add_argument("--limit", type=int, help="Limit records to load")
    args = parser.parse_args()

    # Default to loading both if neither specified
    load_both = not args.lps and not args.gps

    try:
        conn = get_connection()
        print("Connected to database")

        if args.clear:
            clear_seed_data(conn)

        if args.lps or load_both:
            load_lps(conn, args.limit)

        if args.gps or load_both:
            load_gps(conn, args.limit)

        # Show final counts
        with conn.cursor() as cur:
            cur.execute("SELECT COUNT(*) FROM organizations WHERE is_lp = TRUE")
            lp_count = cur.fetchone()[0]
            cur.execute("SELECT COUNT(*) FROM organizations WHERE is_gp = TRUE")
            gp_count = cur.fetchone()[0]
            print(f"\nDatabase now has: {lp_count} LPs, {gp_count} GPs")

        conn.close()

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
