#!/usr/bin/env python3
"""
Data Ingestion Pipeline - Main Orchestrator

Two-phase ETL:
1. RAW DATA (for client display): organizations → people → funds
2. AI DATA (for matching algorithms): fund_ai_profiles → lp_ai_profiles

Usage:
    # Raw data only (client display)
    python -m scripts.data_ingestion.main --phase organizations
    python -m scripts.data_ingestion.main --phase funds
    python -m scripts.data_ingestion.main --phase all

    # AI profiles (for matching)
    python -m scripts.data_ingestion.main --phase ai-profiles

    # Full pipeline (raw + AI)
    python -m scripts.data_ingestion.main --phase full
    python -m scripts.data_ingestion.main --phase full --dry-run
"""
import argparse
import logging
import sys
import time
from pathlib import Path

from supabase import Client, create_client

from .config import (
    SOURCE_FILES,
    SUPABASE_SERVICE_KEY,
    SUPABASE_URL,
    SyncStats,
)
from .extractors.companies import extract_companies
from .extractors.contacts import extract_contacts
from .extractors.funds import extract_funds
from .extractors.lps import extract_lps
from .loaders.ai_profiles import sync_fund_ai_profiles
from .loaders.funds import load_funds
from .loaders.lp_profiles import load_lp_profiles
from .loaders.organizations import load_organizations
from .loaders.people import load_people
from .transformers.dedupe import dedupe_by_key
from .transformers.normalize import normalize_linkedin_url, normalize_name, normalize_url

# Logging setup
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger(__name__)


def get_supabase_client() -> Client:
    """Create Supabase client with service key for admin access."""
    if not SUPABASE_URL or not SUPABASE_SERVICE_KEY:
        raise ValueError(
            "Missing SUPABASE_URL or SUPABASE_SERVICE_KEY environment variables"
        )
    return create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY)


def run_organizations(client: Client | None, dry_run: bool = False, limit: int | None = None) -> SyncStats:
    """Phase 1: Import organizations from companies_crm.csv"""
    logger.info("Phase 1: Organizations")

    filepath = SOURCE_FILES["companies"]
    if not filepath.exists():
        logger.error(f"Source file not found: {filepath}")
        return SyncStats(errors=[{"error": f"File not found: {filepath}"}])

    # Extract
    logger.info(f"  Extracting from {filepath.name}...")
    records = extract_companies(filepath)

    # Transform: normalize and dedupe
    def transform(record):
        record["name"] = normalize_name(record.get("name"))
        record["website"] = normalize_url(record.get("website"))
        return record

    records = (transform(r) for r in records)
    records = dedupe_by_key(records, lambda r: r.get("external_id", ""))

    # Apply limit if specified
    if limit:
        records = list(records)[:limit]
        logger.info(f"  Limited to {limit} records")
    else:
        records = list(records)

    logger.info(f"  Found {len(records)} unique organizations")

    # Load
    logger.info("  Loading to Supabase...")
    stats = load_organizations(client, iter(records), dry_run=dry_run)

    logger.info(f"  Done: {stats.created} created, {stats.skipped} skipped, {len(stats.errors)} errors")
    return stats


def run_people(client: Client | None, dry_run: bool = False, limit: int | None = None) -> SyncStats:
    """Phase 2: Import people from contacts.csv"""
    logger.info("Phase 2: People")

    # Use the original contacts file
    filepath = Path("/home/tijn/code/lpxgp/docs/data/Data recollection pre-holiday - contacts.csv")
    if not filepath.exists():
        filepath = SOURCE_FILES.get("contacts")
    if not filepath or not filepath.exists():
        logger.error("Contacts source file not found")
        return SyncStats(errors=[{"error": "Contacts file not found"}])

    # Extract
    logger.info(f"  Extracting from {filepath.name}...")
    records = extract_contacts(filepath)

    # Transform: normalize
    def transform(record):
        record["linkedin_url"] = normalize_linkedin_url(record.get("linkedin_url"))
        return record

    records = (transform(r) for r in records)
    records = list(records)

    # Apply limit if specified
    if limit:
        records = records[:limit]
        logger.info(f"  Limited to {limit} records")

    logger.info(f"  Found {len(records)} contacts")

    # Load
    logger.info("  Loading to Supabase...")
    stats = load_people(client, iter(records), dry_run=dry_run)

    logger.info(f"  Done: {stats.created} created, {stats.skipped} skipped, {len(stats.errors)} errors")
    return stats


def run_lps(client: Client | None, dry_run: bool = False, limit: int | None = None) -> tuple[SyncStats, list[dict]]:
    """
    Phase 3: Import LPs from lp_matchmaking.csv

    Returns:
        Tuple of (stats, records) - records needed for AI profile phase
    """
    logger.info("Phase 3: LP Profiles (raw data for display)")

    filepath = SOURCE_FILES.get("lp_matchmaking")
    if not filepath or not filepath.exists():
        logger.error(f"Source file not found: {filepath}")
        return SyncStats(errors=[{"error": f"File not found: {filepath}"}]), []

    # Extract
    logger.info(f"  Extracting from {filepath.name}...")
    records = extract_lps(filepath)

    # Dedupe by org_external_id
    records = dedupe_by_key(records, lambda r: r.get("org_external_id", ""))

    # Apply limit if specified
    if limit:
        records = list(records)[:limit]
        logger.info(f"  Limited to {limit} records")
    else:
        records = list(records)

    logger.info(f"  Found {len(records)} unique LP profiles")

    # Load RAW data to lp_profiles table
    logger.info("  Loading RAW data to lp_profiles table...")
    stats = load_lp_profiles(client, iter(records), dry_run=dry_run)

    logger.info(f"  Done: {stats.created} created, {stats.skipped} skipped, {len(stats.errors)} errors")
    return stats, records


def run_funds(client: Client | None, dry_run: bool = False, limit: int | None = None) -> tuple[SyncStats, list[dict]]:
    """
    Phase 4: Import funds from global_funds.csv

    Returns:
        Tuple of (stats, records) - records needed for AI profile phase
    """
    logger.info("Phase 4: Funds (raw data for display)")

    filepath = SOURCE_FILES["global_funds"]
    if not filepath.exists():
        logger.error(f"Source file not found: {filepath}")
        return SyncStats(errors=[{"error": f"File not found: {filepath}"}]), []

    # Extract
    logger.info(f"  Extracting from {filepath.name}...")
    records = extract_funds(filepath)

    # Dedupe by external_id
    records = dedupe_by_key(records, lambda r: r.get("external_id", ""))

    # Apply limit if specified
    if limit:
        records = list(records)[:limit]
        logger.info(f"  Limited to {limit} records")
    else:
        records = list(records)

    logger.info(f"  Found {len(records)} unique funds")

    # Load RAW data to funds table
    logger.info("  Loading RAW data to funds table...")
    stats = load_funds(client, iter(records), dry_run=dry_run)

    logger.info(f"  Done: {stats.created} created, {stats.skipped} skipped, {len(stats.errors)} errors")
    return stats, records


def run_ai_profiles(
    client: Client | None,
    fund_records: list[dict] | None = None,
    lp_records: list[dict] | None = None,
    dry_run: bool = False,
) -> SyncStats:
    """
    Phase 5: Populate AI matching profiles from raw data.

    This phase creates normalized data for AI algorithms ONLY.
    Client-facing code should NEVER use these tables.

    Args:
        client: Supabase client
        fund_records: Fund records from extraction (with ai_* fields)
        lp_records: LP records from extraction (with ai_* and behavioral fields)
        dry_run: If True, don't write to database
    """
    logger.info("Phase 5: AI Profiles (for matching algorithms only)")
    stats = SyncStats()

    # ── FUND AI PROFILES ──
    if fund_records:
        logger.info(f"  Loading {len(fund_records)} fund AI profiles...")
        if client and not dry_run:
            logger.info("  Syncing fund_ai_profiles from funds table...")
            ai_stats = sync_fund_ai_profiles(client, dry_run=dry_run)
            stats.created += ai_stats.created
            stats.errors.extend(ai_stats.errors)
            logger.info(f"  Fund AI profiles: {ai_stats.created} synced")
    elif client and not dry_run:
        # Sync from existing database records
        logger.info("  Syncing fund_ai_profiles from existing funds...")
        ai_stats = sync_fund_ai_profiles(client, dry_run=dry_run)
        stats.created += ai_stats.created
        stats.errors.extend(ai_stats.errors)
        logger.info(f"  Fund AI profiles: {ai_stats.created} synced")

    # ── LP AI PROFILES ──
    if lp_records:
        logger.info(f"  Loading {len(lp_records)} LP AI profiles...")
        if dry_run:
            # In dry run, count the records
            lp_ai_count = len(lp_records)
            stats.created += lp_ai_count
            logger.info(f"  LP AI profiles: {lp_ai_count} would be created")
        elif client:
            # Need to get lp_profile_ids from database
            lp_ai_stats = _sync_lp_ai_profiles(client, lp_records)
            stats.created += lp_ai_stats.created
            stats.errors.extend(lp_ai_stats.errors)
            logger.info(f"  LP AI profiles: {lp_ai_stats.created} synced")
    elif client and not dry_run:
        # Sync from existing lp_profiles
        logger.info("  Syncing lp_ai_profiles from existing LP profiles...")
        lp_ai_stats = _sync_lp_ai_profiles_from_db(client)
        stats.created += lp_ai_stats.created
        stats.errors.extend(lp_ai_stats.errors)
        logger.info(f"  LP AI profiles: {lp_ai_stats.created} synced")

    logger.info(f"  Done: {stats.created} AI profiles created, {len(stats.errors)} errors")
    return stats


def _sync_lp_ai_profiles(client: Client, lp_records: list[dict]) -> SyncStats:
    """Sync LP AI profiles from extracted records."""
    stats = SyncStats()

    for record in lp_records:
        org_external_id = record.get("org_external_id")
        if not org_external_id:
            stats.skipped += 1
            continue

        try:
            # Get lp_profile_id and org_id from database
            response = client.table("lp_profiles").select(
                "id, org_id"
            ).eq("external_id", org_external_id).eq("external_source", "ipem").single().execute()

            if not response.data:
                stats.skipped += 1
                continue

            lp_profile_id = response.data["id"]
            org_id = response.data["org_id"]

            # Build AI profile
            ai_profile = {
                "lp_profile_id": lp_profile_id,
                "org_id": org_id,
                "strategy_interests": record.get("ai_strategy_interests", []),
                "geography_interests": record.get("ai_geography_interests", []),
                "sector_interests": record.get("ai_sector_interests", []),
                "acceptance_rate": record.get("acceptance_rate"),
                "total_interactions": record.get("solicitations_received", 0),
                "engagement_score": record.get("engagement_score", 0.0),
                "data_sources": ["behavioral"] if record.get("solicitations_received", 0) > 0 else ["unknown"],
            }

            client.table("lp_ai_profiles").upsert(
                ai_profile,
                on_conflict="lp_profile_id",
            ).execute()
            stats.created += 1

        except Exception as e:
            stats.errors.append({
                "lp_external_id": org_external_id,
                "error": str(e),
            })

    return stats


def _sync_lp_ai_profiles_from_db(client: Client) -> SyncStats:
    """Sync LP AI profiles from existing lp_profiles table."""
    stats = SyncStats()

    try:
        # Get all LP profiles with behavioral data
        response = client.table("lp_profiles").select(
            "id, org_id, solicitations_received, solicitations_accepted, last_activity_at"
        ).execute()

        if not response.data:
            return stats

        for lp in response.data:
            received = lp.get("solicitations_received", 0)
            accepted = lp.get("solicitations_accepted", 0)
            acceptance_rate = (accepted / received) if received > 0 else None

            ai_profile = {
                "lp_profile_id": lp["id"],
                "org_id": lp["org_id"],
                "strategy_interests": [],  # Would come from form data
                "geography_interests": [],  # Would come from form data
                "sector_interests": [],
                "acceptance_rate": acceptance_rate,
                "total_interactions": received,
                "engagement_score": min(0.3 if received >= 100 else 0.1 if received >= 10 else 0.0, 1.0),
                "data_sources": ["behavioral"] if received > 0 else ["unknown"],
            }

            try:
                client.table("lp_ai_profiles").upsert(
                    ai_profile,
                    on_conflict="lp_profile_id",
                ).execute()
                stats.created += 1
            except Exception as e:
                stats.errors.append({"lp_profile_id": lp["id"], "error": str(e)})

    except Exception as e:
        stats.errors.append({"error": f"Failed to sync: {e}"})

    return stats


def log_sync(client: Client, phase: str, stats: SyncStats, duration_ms: int):
    """Log sync operation to sync_log table."""
    try:
        client.table("sync_log").insert({
            "source": "ipem",
            "table_name": phase,
            "records_created": stats.created,
            "records_updated": 0,  # Can't distinguish in upsert
            "records_skipped": stats.skipped,
            "errors": stats.errors[:10],  # Limit error log size
            "duration_ms": duration_ms,
            "metadata": {"total_errors": len(stats.errors)},
        }).execute()
    except Exception as e:
        logger.warning(f"Failed to log sync: {e}")


def main():
    parser = argparse.ArgumentParser(description="Import data from Metabase to Supabase")
    parser.add_argument(
        "--phase",
        choices=["organizations", "people", "lps", "funds", "ai-profiles", "all", "full"],
        default="all",
        help="Which phase to run. 'all' = raw data only, 'full' = raw + AI profiles",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Don't actually write to database",
    )
    parser.add_argument(
        "--limit",
        type=int,
        help="Limit number of records per phase (for testing)",
    )
    args = parser.parse_args()

    logger.info("=" * 60)
    logger.info("LPxGP Data Ingestion Pipeline")
    logger.info(f"Phase: {args.phase}")
    logger.info(f"Dry run: {args.dry_run}")
    if args.limit:
        logger.info(f"Limit: {args.limit} records")
    logger.info("=" * 60)
    logger.info("")
    logger.info("Pipeline structure:")
    logger.info("  RAW DATA (client display): organizations → people → lps → funds")
    logger.info("  AI DATA (matching only):   fund_ai_profiles + lp_ai_profiles")
    logger.info("")

    # Connect to Supabase (skip for dry run if no credentials)
    client = None
    if args.dry_run and (not SUPABASE_URL or not SUPABASE_SERVICE_KEY):
        logger.info("Dry run mode - skipping Supabase connection")
    else:
        try:
            client = get_supabase_client()
            logger.info("Connected to Supabase")
        except Exception as e:
            logger.error(f"Failed to connect to Supabase: {e}")
            sys.exit(1)

    # Determine which phases to run
    raw_phases = []
    run_ai = False
    fund_records = []  # Store for AI profile phase
    lp_records = []    # Store for AI profile phase

    if args.phase == "all":
        raw_phases = ["organizations", "people", "lps", "funds"]
    elif args.phase == "full":
        raw_phases = ["organizations", "people", "lps", "funds"]
        run_ai = True
    elif args.phase == "ai-profiles":
        run_ai = True
    else:
        raw_phases = [args.phase]

    total_stats = SyncStats()

    # ═══════════════════════════════════════════════════════════════
    # PHASE 1-4: RAW DATA (for client display)
    # ═══════════════════════════════════════════════════════════════
    for phase in raw_phases:
        start_time = time.time()

        if phase == "organizations":
            stats = run_organizations(client, args.dry_run, args.limit)
        elif phase == "people":
            stats = run_people(client, args.dry_run, args.limit)
        elif phase == "lps":
            stats, lp_records = run_lps(client, args.dry_run, args.limit)
        elif phase == "funds":
            stats, fund_records = run_funds(client, args.dry_run, args.limit)
        else:
            continue

        duration_ms = int((time.time() - start_time) * 1000)

        # Accumulate stats
        total_stats.created += stats.created
        total_stats.skipped += stats.skipped
        total_stats.errors.extend(stats.errors)

        # Log to database (unless dry run)
        if client and not args.dry_run:
            log_sync(client, phase, stats, duration_ms)

    # ═══════════════════════════════════════════════════════════════
    # PHASE 5: AI PROFILES (for matching algorithms)
    # ═══════════════════════════════════════════════════════════════
    if run_ai:
        start_time = time.time()
        ai_stats = run_ai_profiles(client, fund_records, lp_records, args.dry_run)
        duration_ms = int((time.time() - start_time) * 1000)

        total_stats.created += ai_stats.created
        total_stats.errors.extend(ai_stats.errors)

        if client and not args.dry_run:
            log_sync(client, "ai_profiles", ai_stats, duration_ms)

    # Summary
    logger.info("=" * 60)
    logger.info("SUMMARY")
    logger.info(f"  Total created: {total_stats.created}")
    logger.info(f"  Total skipped: {total_stats.skipped}")
    logger.info(f"  Total errors: {len(total_stats.errors)}")

    if total_stats.errors:
        logger.info("First 5 errors:")
        for err in total_stats.errors[:5]:
            logger.info(f"    {err}")

    logger.info("=" * 60)


if __name__ == "__main__":
    main()
