#!/usr/bin/env python3
"""Reset the TEST database and reload seed data.

SAFETY: This script ONLY operates on TEST_DATABASE_URL, NEVER on production.

This script provides a clean slate for testing by:
1. Truncating all tables (preserving schema)
2. Optionally loading seed data (10k LPs + 10k GPs)
3. Optionally loading demo data (8 LPs for quick testing)

Usage:
    uv run python scripts/reset_database.py              # Reset + load demo data
    uv run python scripts/reset_database.py --seed       # Reset + load 10k seed data
    uv run python scripts/reset_database.py --seed --demo # Reset + load both
    uv run python scripts/reset_database.py --empty      # Reset only, no data
    uv run python scripts/reset_database.py --seed --limit 1000  # Load 1000 of each

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

# =============================================================================
# PRODUCTION SAFETY CHECKS
# =============================================================================


def verify_test_database() -> str:
    """Verify we're connecting to a TEST database, not production.

    Returns:
        The test database URL if safe to proceed.

    Raises:
        SystemExit: If production database would be affected.
    """
    settings = get_settings()

    # MUST have TEST_DATABASE_URL set
    if not settings.test_database_url:
        print("=" * 60)
        print("ERROR: TEST_DATABASE_URL is not configured!")
        print("=" * 60)
        print()
        print("This script ONLY operates on the test database.")
        print("Set TEST_DATABASE_URL in your .env file:")
        print()
        print("  TEST_DATABASE_URL=postgresql://user:pass@host:port/test_db")
        print()
        print("NEVER use your production database URL here!")
        print("=" * 60)
        sys.exit(1)

    # Additional safety: check database name contains 'test' or is localhost
    db_url = settings.test_database_url.lower()
    is_safe = (
        "test" in db_url or
        "localhost" in db_url or
        "127.0.0.1" in db_url or
        "dev" in db_url
    )

    if not is_safe and settings.is_production:
        print("=" * 60)
        print("ERROR: REFUSING to reset database in production environment!")
        print("=" * 60)
        print()
        print("The TEST_DATABASE_URL does not appear to be a test database:")
        print(f"  {settings.test_database_url[:50]}...")
        print()
        print("Test database URL should contain 'test', 'dev', or 'localhost'.")
        print("=" * 60)
        sys.exit(1)

    # Warn if production database is also configured
    if settings.database_url:
        print("NOTE: Production DATABASE_URL is configured but will NOT be touched.")
        print(f"      Using TEST_DATABASE_URL: {settings.test_database_url[:50]}...")
        print()

    return settings.test_database_url

# Demo data - 8 well-known LPs for quick testing
DEMO_LPS = [
    {
        "id": "a1000001-0000-0000-0000-000000000001",
        "name": "CalPERS",
        "website": "https://www.calpers.ca.gov",
        "hq_city": "Sacramento",
        "hq_country": "USA",
        "lp_type": "pension",
        "total_aum_bn": 450.0,
        "pe_allocation_pct": 12.0,
        "check_size_min_mm": 50.0,
        "check_size_max_mm": 500.0,
        "strategies": ["buyout", "growth", "venture"],
        "geographic_preferences": ["North America", "Europe"],
    },
    {
        "id": "a1000002-0000-0000-0000-000000000002",
        "name": "Ontario Teachers Pension Plan",
        "website": "https://www.otpp.com",
        "hq_city": "Toronto",
        "hq_country": "Canada",
        "lp_type": "pension",
        "total_aum_bn": 250.0,
        "pe_allocation_pct": 15.0,
        "check_size_min_mm": 100.0,
        "check_size_max_mm": 750.0,
        "strategies": ["buyout", "infrastructure"],
        "geographic_preferences": ["North America", "Europe", "Asia Pacific"],
    },
    {
        "id": "a1000003-0000-0000-0000-000000000003",
        "name": "Harvard Management Company",
        "website": "https://www.hmc.harvard.edu",
        "hq_city": "Boston",
        "hq_country": "USA",
        "lp_type": "endowment",
        "total_aum_bn": 53.0,
        "pe_allocation_pct": 34.0,
        "check_size_min_mm": 50.0,
        "check_size_max_mm": 500.0,
        "strategies": ["buyout", "venture", "growth"],
        "geographic_preferences": ["Global"],
    },
    {
        "id": "a1000004-0000-0000-0000-000000000004",
        "name": "Abu Dhabi Investment Authority",
        "website": "https://www.adia.ae",
        "hq_city": "Abu Dhabi",
        "hq_country": "UAE",
        "lp_type": "sovereign_wealth",
        "total_aum_bn": 900.0,
        "pe_allocation_pct": 8.0,
        "check_size_min_mm": 200.0,
        "check_size_max_mm": 2000.0,
        "strategies": ["buyout", "growth", "venture"],
        "geographic_preferences": ["Global"],
    },
    {
        "id": "a1000005-0000-0000-0000-000000000005",
        "name": "GIC Private Limited",
        "website": "https://www.gic.com.sg",
        "hq_city": "Singapore",
        "hq_country": "Singapore",
        "lp_type": "sovereign_wealth",
        "total_aum_bn": 750.0,
        "pe_allocation_pct": 11.0,
        "check_size_min_mm": 150.0,
        "check_size_max_mm": 1500.0,
        "strategies": ["buyout", "growth", "venture"],
        "geographic_preferences": ["Global"],
    },
    {
        "id": "a1000006-0000-0000-0000-000000000006",
        "name": "Future Fund",
        "website": "https://www.futurefund.gov.au",
        "hq_city": "Melbourne",
        "hq_country": "Australia",
        "lp_type": "sovereign_wealth",
        "total_aum_bn": 200.0,
        "pe_allocation_pct": 14.0,
        "check_size_min_mm": 50.0,
        "check_size_max_mm": 400.0,
        "strategies": ["buyout", "growth", "infrastructure"],
        "geographic_preferences": ["Asia Pacific", "Global"],
    },
    {
        "id": "a1000007-0000-0000-0000-000000000007",
        "name": "Walton Family Office",
        "website": "https://www.waltonfamilyoffice.com",
        "hq_city": "Bentonville",
        "hq_country": "USA",
        "lp_type": "family_office",
        "total_aum_bn": 5.0,
        "pe_allocation_pct": 25.0,
        "check_size_min_mm": 25.0,
        "check_size_max_mm": 150.0,
        "strategies": ["growth", "venture"],
        "geographic_preferences": ["North America"],
    },
    {
        "id": "a1000008-0000-0000-0000-000000000008",
        "name": "Ford Foundation",
        "website": "https://www.fordfoundation.org",
        "hq_city": "New York",
        "hq_country": "USA",
        "lp_type": "foundation",
        "total_aum_bn": 16.0,
        "pe_allocation_pct": 10.0,
        "check_size_min_mm": 20.0,
        "check_size_max_mm": 100.0,
        "strategies": ["growth", "venture"],
        "geographic_preferences": ["North America", "Global"],
    },
]

# Demo GP
DEMO_GPS = [
    {
        "id": "c0000001-0000-0000-0000-000000000001",
        "name": "Demo GP Partners",
        "website": "https://www.demogp.com",
        "hq_city": "New York",
        "hq_country": "USA",
        "investment_philosophy": "Growth-oriented investments in technology and healthcare",
        "team_size": 25,
        "years_investing": 15,
    },
]

# Demo Funds for GP
DEMO_FUNDS = [
    {
        "id": "f0000001-0000-0000-0000-000000000001",
        "gp_org_id": "c0000001-0000-0000-0000-000000000001",
        "name": "Demo GP Growth Fund III",
        "strategy": "growth",
        "target_size_mm": 500,
        "geographic_focus": "North America",
        "vintage_year": 2024,
        "status": "fundraising",
        "sectors": ["technology", "healthcare"],
    },
    {
        "id": "f0000002-0000-0000-0000-000000000002",
        "gp_org_id": "c0000001-0000-0000-0000-000000000001",
        "name": "Demo GP Buyout Fund II",
        "strategy": "buyout",
        "target_size_mm": 750,
        "geographic_focus": "North America, Europe",
        "vintage_year": 2023,
        "status": "fundraising",
        "sectors": ["industrials", "consumer"],
    },
]

# Pipeline entries - GP pursuing various LPs at different stages
DEMO_PIPELINE = [
    # CalPERS - Mutual interest (GP pursuing, LP interested)
    {
        "fund_id": "f0000001-0000-0000-0000-000000000001",
        "lp_org_id": "a1000001-0000-0000-0000-000000000001",
        "pipeline_stage": "mutual_interest",
        "gp_interest": "pursuing",
        "lp_interest": "interested",
        "notes": "Had initial call, LP requested DDQ",
    },
    # Ontario Teachers - In diligence
    {
        "fund_id": "f0000001-0000-0000-0000-000000000001",
        "lp_org_id": "a1000002-0000-0000-0000-000000000002",
        "pipeline_stage": "in_diligence",
        "gp_interest": "pursuing",
        "lp_interest": "reviewing",
        "notes": "Due diligence in progress, site visit scheduled",
    },
    # Harvard - GP interested, awaiting response
    {
        "fund_id": "f0000001-0000-0000-0000-000000000001",
        "lp_org_id": "a1000003-0000-0000-0000-000000000003",
        "pipeline_stage": "gp_pursuing",
        "gp_interest": "pursuing",
        "lp_interest": None,
        "notes": "Sent materials, follow-up call next week",
    },
    # ADIA - Recommended, not yet contacted
    {
        "fund_id": "f0000001-0000-0000-0000-000000000001",
        "lp_org_id": "a1000004-0000-0000-0000-000000000004",
        "pipeline_stage": "recommended",
        "gp_interest": "interested",
        "lp_interest": None,
        "notes": "High priority target based on strategy fit",
    },
    # GIC - LP passed
    {
        "fund_id": "f0000002-0000-0000-0000-000000000002",
        "lp_org_id": "a1000005-0000-0000-0000-000000000005",
        "pipeline_stage": "lp_passed",
        "gp_interest": "pursuing",
        "lp_interest": "not_interested",
        "notes": "LP declined - already at allocation limit",
    },
    # Future Fund - GP interested, Fund II
    {
        "fund_id": "f0000002-0000-0000-0000-000000000002",
        "lp_org_id": "a1000006-0000-0000-0000-000000000006",
        "pipeline_stage": "gp_interested",
        "gp_interest": "interested",
        "lp_interest": None,
        "notes": "Good geographic fit",
    },
]

# Demo shortlist for GP user
DEMO_SHORTLIST = [
    {"lp_id": "a1000001-0000-0000-0000-000000000001", "priority": 5, "notes": "Top priority - perfect strategy fit"},
    {"lp_id": "a1000002-0000-0000-0000-000000000002", "priority": 4, "notes": "Strong track record together"},
    {"lp_id": "a1000003-0000-0000-0000-000000000003", "priority": 4, "notes": "Endowment with venture appetite"},
    {"lp_id": "a1000007-0000-0000-0000-000000000007", "priority": 3, "notes": "Family office - quick decisions"},
]

# Demo touchpoints for activity timeline
DEMO_TOUCHPOINTS = [
    {
        "lp_org_id": "a1000001-0000-0000-0000-000000000001",
        "fund_id": "f0000001-0000-0000-0000-000000000001",
        "touchpoint_type": "meeting",
        "notes": "Initial intro call with investment team",
    },
    {
        "lp_org_id": "a1000001-0000-0000-0000-000000000001",
        "fund_id": "f0000001-0000-0000-0000-000000000001",
        "touchpoint_type": "email",
        "notes": "Sent DDQ and fund presentation",
    },
    {
        "lp_org_id": "a1000002-0000-0000-0000-000000000002",
        "fund_id": "f0000001-0000-0000-0000-000000000001",
        "touchpoint_type": "meeting",
        "notes": "On-site due diligence meeting",
    },
    {
        "lp_org_id": "a1000003-0000-0000-0000-000000000003",
        "fund_id": "f0000001-0000-0000-0000-000000000001",
        "touchpoint_type": "call",
        "notes": "Follow-up call to discuss strategy",
    },
]

# LP Demo user watchlist/pipeline (for demo LP user viewing funds)
DEMO_LP_PIPELINE = [
    # LP is interested in Demo GP Growth Fund III
    {
        "fund_id": "f0000001-0000-0000-0000-000000000001",
        "lp_org_id": "a1000001-0000-0000-0000-000000000001",  # CalPERS (demo LP is linked here)
    },
]


def get_connection():
    """Get TEST database connection (with safety checks)."""
    db_url = verify_test_database()
    return psycopg2.connect(db_url)


def truncate_all_tables(conn):
    """Truncate all data tables (preserves schema)."""
    print("Truncating all tables...")

    # Truncate in dependency order (children first)
    # Note: Only include tables that exist in the schema
    tables = [
        "touchpoints",
        "shortlists",
        "tracking_links",
        "fund_lp_status",
        "fund_lp_matches",
        "investments",
        "funds",
        "lp_profiles",
        "gp_profiles",
        "organizations",
    ]

    with conn.cursor() as cur:
        # Disable foreign key checks temporarily
        cur.execute("SET session_replication_role = 'replica';")
        conn.commit()

        for table in tables:
            try:
                cur.execute(f"TRUNCATE TABLE {table} CASCADE;")
                conn.commit()
                print(f"  Truncated {table}")
            except psycopg2.Error as e:
                conn.rollback()
                print(f"  Skipped {table}: {e.pgerror.strip() if e.pgerror else str(e)}")

        # Re-enable foreign key checks
        cur.execute("SET session_replication_role = 'origin';")
        conn.commit()

    print("All tables truncated.")


def load_demo_data(conn):
    """Load the 8 demo LPs, 1 demo GP, funds, pipeline, shortlist, and touchpoints."""
    print("Loading demo data...")

    with conn.cursor() as cur:
        # Insert demo LPs
        for lp in DEMO_LPS:
            cur.execute("""
                INSERT INTO organizations (id, name, website, hq_city, hq_country, is_gp, is_lp)
                VALUES (%s, %s, %s, %s, %s, FALSE, TRUE)
                ON CONFLICT (id) DO NOTHING
            """, (lp["id"], lp["name"], lp["website"], lp["hq_city"], lp["hq_country"]))

            cur.execute("""
                INSERT INTO lp_profiles (
                    org_id, lp_type, total_aum_bn, pe_allocation_pct,
                    check_size_min_mm, check_size_max_mm, strategies, geographic_preferences
                )
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (org_id) DO NOTHING
            """, (
                lp["id"], lp["lp_type"], lp["total_aum_bn"], lp["pe_allocation_pct"],
                lp["check_size_min_mm"], lp["check_size_max_mm"],
                lp["strategies"], lp["geographic_preferences"]
            ))

        print(f"  Loaded {len(DEMO_LPS)} demo LPs")

        # Insert demo GPs
        for gp in DEMO_GPS:
            cur.execute("""
                INSERT INTO organizations (id, name, website, hq_city, hq_country, is_gp, is_lp)
                VALUES (%s, %s, %s, %s, %s, TRUE, FALSE)
                ON CONFLICT (id) DO NOTHING
            """, (gp["id"], gp["name"], gp["website"], gp["hq_city"], gp["hq_country"]))

            cur.execute("""
                INSERT INTO gp_profiles (org_id, investment_philosophy, team_size, years_investing)
                VALUES (%s, %s, %s, %s)
                ON CONFLICT (org_id) DO NOTHING
            """, (gp["id"], gp["investment_philosophy"], gp["team_size"], gp["years_investing"]))

        print(f"  Loaded {len(DEMO_GPS)} demo GPs")

        # Insert demo funds
        for fund in DEMO_FUNDS:
            cur.execute("""
                INSERT INTO funds (id, gp_org_id, name, strategy, target_size_mm,
                                   geographic_focus, vintage_year, status, sectors)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                ON CONFLICT (id) DO NOTHING
            """, (
                fund["id"], fund["gp_org_id"], fund["name"], fund["strategy"],
                fund["target_size_mm"], fund["geographic_focus"], fund["vintage_year"],
                fund["status"], fund["sectors"]
            ))

        print(f"  Loaded {len(DEMO_FUNDS)} demo funds")

        # Insert demo pipeline entries (fund_lp_status)
        for entry in DEMO_PIPELINE:
            cur.execute("""
                INSERT INTO fund_lp_status (fund_id, lp_org_id, pipeline_stage,
                                            gp_interest, lp_interest, notes)
                VALUES (%s, %s, %s, %s, %s, %s)
                ON CONFLICT (fund_id, lp_org_id) DO NOTHING
            """, (
                entry["fund_id"], entry["lp_org_id"], entry["pipeline_stage"],
                entry["gp_interest"], entry["lp_interest"], entry["notes"]
            ))

        print(f"  Loaded {len(DEMO_PIPELINE)} demo pipeline entries")

        # Insert demo shortlist (need to get/create demo GP user ID)
        # We'll use a placeholder user_id that matches the demo GP user
        demo_gp_user_id = "00000000-0000-0000-0000-000000000001"  # Placeholder

        # Check if shortlists table exists and has correct schema
        try:
            for item in DEMO_SHORTLIST:
                cur.execute("""
                    INSERT INTO shortlists (user_id, lp_id, priority, notes)
                    VALUES (%s, %s, %s, %s)
                    ON CONFLICT DO NOTHING
                """, (demo_gp_user_id, item["lp_id"], item["priority"], item["notes"]))
            print(f"  Loaded {len(DEMO_SHORTLIST)} demo shortlist entries")
        except Exception as e:
            print(f"  Skipped shortlist (table may not exist): {e}")

        # Insert demo touchpoints
        try:
            for tp in DEMO_TOUCHPOINTS:
                cur.execute("""
                    INSERT INTO touchpoints (lp_org_id, fund_id, touchpoint_type, notes, occurred_at)
                    VALUES (%s, %s, %s, %s, NOW() - interval '1 day' * (random() * 30)::int)
                """, (tp["lp_org_id"], tp["fund_id"], tp["touchpoint_type"], tp["notes"]))
            print(f"  Loaded {len(DEMO_TOUCHPOINTS)} demo touchpoints")
        except Exception as e:
            print(f"  Skipped touchpoints (table may not exist): {e}")

        # Note: Users are managed by Supabase Auth, not a custom users table
        print("  Demo users: Use Supabase Auth (gp@demo.com, admin@demo.com, lp@demo.com)")

    conn.commit()
    print("Demo data loaded.")


def load_seed_data(conn, limit: int | None = None):
    """Load seed data from JSON files."""
    lp_file = SEED_DIR / "lps_10k.json"
    gp_file = SEED_DIR / "gps_10k.json"

    if not lp_file.exists() or not gp_file.exists():
        print("Seed data files not found. Generating...")
        import subprocess
        subprocess.run([sys.executable, str(Path(__file__).parent / "generate_seed_data.py")], check=True)

    print(f"Loading seed data (limit={limit or 'all'})...")

    # Load LPs
    with open(lp_file) as f:
        lps = json.load(f)
    if limit:
        lps = lps[:limit]

    with conn.cursor() as cur:
        org_data = [(
            lp["id"],
            lp["organization"]["name"],
            lp["organization"]["website"],
            lp["organization"]["hq_city"],
            lp["organization"]["hq_country"],
            lp["organization"]["description"],
            False,  # is_gp
            True,   # is_lp
        ) for lp in lps]

        execute_values(cur, """
            INSERT INTO organizations (id, name, website, hq_city, hq_country, description, is_gp, is_lp)
            VALUES %s ON CONFLICT (id) DO NOTHING
        """, org_data, page_size=1000)

        profile_data = [(
            lp["id"],
            lp["profile"]["lp_type"],
            lp["profile"]["total_aum_bn"],
            lp["profile"]["pe_allocation_pct"],
            lp["profile"]["strategies"],
            lp["profile"]["geographic_preferences"],
            lp["profile"]["sector_preferences"],
            lp["profile"]["check_size_min_mm"],
            lp["profile"]["check_size_max_mm"],
            lp["profile"]["fund_size_min_mm"],
            lp["profile"]["fund_size_max_mm"],
            lp["profile"]["min_track_record_years"],
            lp["profile"]["min_fund_number"],
            lp["profile"]["esg_required"],
            lp["profile"]["emerging_manager_ok"],
        ) for lp in lps]

        execute_values(cur, """
            INSERT INTO lp_profiles (
                org_id, lp_type, total_aum_bn, pe_allocation_pct,
                strategies, geographic_preferences, sector_preferences,
                check_size_min_mm, check_size_max_mm, fund_size_min_mm, fund_size_max_mm,
                min_track_record_years, min_fund_number, esg_required, emerging_manager_ok
            ) VALUES %s ON CONFLICT (org_id) DO NOTHING
        """, profile_data, page_size=1000)

    print(f"  Loaded {len(lps)} LPs")

    # Load GPs
    with open(gp_file) as f:
        gps = json.load(f)
    if limit:
        gps = gps[:limit]

    with conn.cursor() as cur:
        org_data = [(
            gp["id"],
            gp["organization"]["name"],
            gp["organization"]["website"],
            gp["organization"]["hq_city"],
            gp["organization"]["hq_country"],
            gp["organization"]["description"],
            True,   # is_gp
            False,  # is_lp
        ) for gp in gps]

        execute_values(cur, """
            INSERT INTO organizations (id, name, website, hq_city, hq_country, description, is_gp, is_lp)
            VALUES %s ON CONFLICT (id) DO NOTHING
        """, org_data, page_size=1000)

        profile_data = [(
            gp["id"],
            gp["profile"]["investment_philosophy"],
            gp["profile"]["team_size"],
            gp["profile"]["years_investing"],
            gp["profile"]["spun_out_from"],
            json.dumps(gp["profile"]["notable_exits"]),
            json.dumps(gp["profile"]["track_record_summary"]),
        ) for gp in gps]

        execute_values(cur, """
            INSERT INTO gp_profiles (
                org_id, investment_philosophy, team_size, years_investing,
                spun_out_from, notable_exits, track_record_summary
            ) VALUES %s ON CONFLICT (org_id) DO NOTHING
        """, profile_data, page_size=1000)

    print(f"  Loaded {len(gps)} GPs")
    conn.commit()
    print("Seed data loaded.")


def show_stats(conn):
    """Show database statistics."""
    with conn.cursor() as cur:
        cur.execute("SELECT COUNT(*) FROM organizations WHERE is_lp = TRUE")
        lp_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM organizations WHERE is_gp = TRUE")
        gp_count = cur.fetchone()[0]
        cur.execute("SELECT COUNT(*) FROM funds")
        fund_count = cur.fetchone()[0]

    print("\nDatabase statistics:")
    print(f"  LPs: {lp_count}")
    print(f"  GPs: {gp_count}")
    print(f"  Funds: {fund_count}")


def main():
    parser = argparse.ArgumentParser(description="Reset database and load test data")
    parser.add_argument("--seed", action="store_true", help="Load 10k seed data")
    parser.add_argument("--demo", action="store_true", help="Load demo data (8 LPs)")
    parser.add_argument("--empty", action="store_true", help="Reset only, don't load any data")
    parser.add_argument("--limit", type=int, help="Limit seed records to load")
    parser.add_argument("--no-truncate", action="store_true", help="Don't truncate, just add data")
    args = parser.parse_args()

    # Default: load demo data if no options specified
    if not args.seed and not args.demo and not args.empty:
        args.demo = True

    try:
        print("=" * 60)
        print("TEST DATABASE RESET")
        print("=" * 60)
        conn = get_connection()
        print("Connected to TEST database")

        if not args.no_truncate:
            truncate_all_tables(conn)

        if args.demo:
            load_demo_data(conn)

        if args.seed:
            load_seed_data(conn, args.limit)

        show_stats(conn)
        conn.close()
        print("\nDone!")

    except Exception as e:
        print(f"Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
