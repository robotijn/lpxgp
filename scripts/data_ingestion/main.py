#!/usr/bin/env python3
"""
Data Ingestion Pipeline - Main Orchestrator

Imports data from Metabase/IPEM CSV exports into Supabase.

Usage:
    python -m scripts.data_ingestion.main --phase organizations
    python -m scripts.data_ingestion.main --phase people
    python -m scripts.data_ingestion.main --phase funds
    python -m scripts.data_ingestion.main --phase all
    python -m scripts.data_ingestion.main --phase all --dry-run
    python -m scripts.data_ingestion.main --phase all --limit 100
"""
import argparse
import json
import logging
import sys
import time
from datetime import datetime, timezone
from pathlib import Path

from supabase import create_client, Client

from .config import (
    SUPABASE_URL,
    SUPABASE_SERVICE_KEY,
    SOURCE_FILES,
    SyncStats,
)
from .extractors.companies import extract_companies
from .extractors.contacts import extract_contacts
from .extractors.funds import extract_funds
from .transformers.normalize import normalize_name, normalize_url, normalize_linkedin_url
from .transformers.dedupe import dedupe_by_key
from .loaders.organizations import load_organizations
from .loaders.people import load_people
from .loaders.funds import load_funds

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


def run_funds(client: Client | None, dry_run: bool = False, limit: int | None = None) -> SyncStats:
    """Phase 3: Import funds from global_funds.csv"""
    logger.info("Phase 3: Funds")

    filepath = SOURCE_FILES["global_funds"]
    if not filepath.exists():
        logger.error(f"Source file not found: {filepath}")
        return SyncStats(errors=[{"error": f"File not found: {filepath}"}])

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

    # Load
    logger.info("  Loading to Supabase...")
    stats = load_funds(client, iter(records), dry_run=dry_run)

    logger.info(f"  Done: {stats.created} created, {stats.skipped} skipped, {len(stats.errors)} errors")
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
        choices=["organizations", "people", "funds", "all"],
        default="all",
        help="Which phase to run",
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

    phases = []
    if args.phase == "all":
        phases = ["organizations", "people", "funds"]
    else:
        phases = [args.phase]

    total_stats = SyncStats()

    for phase in phases:
        start_time = time.time()

        if phase == "organizations":
            stats = run_organizations(client, args.dry_run, args.limit)
        elif phase == "people":
            stats = run_people(client, args.dry_run, args.limit)
        elif phase == "funds":
            stats = run_funds(client, args.dry_run, args.limit)
        else:
            continue

        duration_ms = int((time.time() - start_time) * 1000)

        # Accumulate stats
        total_stats.created += stats.created
        total_stats.skipped += stats.skipped
        total_stats.errors.extend(stats.errors)

        # Log to database (unless dry run)
        if not args.dry_run:
            log_sync(client, phase, stats, duration_ms)

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
