"""
Load LP profile records into Supabase.

Maps lp_matchmaking.csv data to:
- lp_profiles (raw data for client display)
- organizations (ensures LP org exists)
"""
from collections.abc import Iterator

from supabase import Client

from ..config import SyncStats
from .organizations import get_org_id_by_external


def load_lp_profiles(
    client: Client | None,
    records: Iterator[dict],
    batch_size: int = 100,
    dry_run: bool = False,
) -> SyncStats:
    """
    Load LP profiles into Supabase.

    Links LP profiles to organizations via org_external_id lookup.
    Creates lp_profile records with behavioral metrics.

    Args:
        client: Supabase client
        records: Iterator of LP dicts from lps.py extractor
        batch_size: Number of records per batch
        dry_run: If True, don't write to database

    Returns:
        SyncStats with counts
    """
    stats = SyncStats()
    batch = []
    org_ids_processed = set()

    for record in records:
        # Get org external ID
        org_external_id = record.get("org_external_id")
        if not org_external_id:
            stats.skipped += 1
            continue

        # Look up organization (skip in dry run)
        org_id = None
        if dry_run:
            org_id = f"dry-run-org-{org_external_id}"
        elif client:
            org_id = get_org_id_by_external(client, org_external_id)

            # If org doesn't exist, we may need to create it
            if not org_id:
                org_id = _ensure_lp_organization(
                    client,
                    org_external_id,
                    record.get("org_name"),
                    record.get("country_raw"),
                )

        if not org_id and not dry_run:
            stats.skipped += 1
            stats.errors.append({
                "lp": record.get("org_name"),
                "error": f"Could not find/create org: {org_external_id}",
            })
            continue

        # Mark organization as LP
        if client and not dry_run and org_id not in org_ids_processed:
            _mark_org_as_lp(client, org_id)
            org_ids_processed.add(org_id)

        # Build LP profile record with RAW data
        lp_data = {
            "org_id": org_id,
            "external_id": org_external_id,
            "external_source": "ipem",
            # LP Type
            "lp_type": record.get("lp_type_raw"),
            # Behavioral metrics
            "solicitations_received": record.get("solicitations_received", 0),
            "solicitations_accepted": record.get("solicitations_accepted", 0),
            "solicitations_declined": record.get("solicitations_declined", 0),
            # Engagement
            "last_activity_at": record.get("last_activity_at"),
            # Event participation
            "event_participation": record.get("event_participation", []),
            # Data source
            "data_source": "ipem",
        }

        batch.append(lp_data)

        if len(batch) >= batch_size:
            _upsert_batch(client, batch, stats, dry_run)
            batch = []

    # Process remaining
    if batch:
        _upsert_batch(client, batch, stats, dry_run)

    return stats


def _ensure_lp_organization(
    client: Client,
    external_id: str,
    name: str | None,
    country: str | None,
) -> str | None:
    """
    Ensure organization exists for LP, create if needed.

    Returns org_id or None.
    """
    try:
        # Try to insert (will fail if exists due to unique constraint)
        response = client.table("organizations").upsert({
            "external_id": external_id,
            "external_source": "ipem",
            "name": name or f"LP Organization {external_id}",
            "hq_country": country,
            "is_lp": True,
        }, on_conflict="external_source,external_id").execute()

        if response.data:
            return response.data[0].get("id")
        return None

    except Exception:
        # Try to get existing
        try:
            response = client.table("organizations").select("id").eq(
                "external_id", external_id
            ).eq("external_source", "ipem").single().execute()
            return response.data.get("id") if response.data else None
        except Exception:
            return None


def _mark_org_as_lp(client: Client, org_id: str):
    """Mark organization as an LP."""
    try:
        client.table("organizations").update({
            "is_lp": True
        }).eq("id", org_id).execute()
    except Exception:
        pass  # Not critical if this fails


def _upsert_batch(
    client: Client | None,
    batch: list[dict],
    stats: SyncStats,
    dry_run: bool,
):
    """Upsert a batch of LP profiles."""
    if dry_run:
        stats.created += len(batch)
        return

    if not client:
        return

    try:
        # Use org_id as the unique key since that's what lp_profiles uses
        response = client.table("lp_profiles").upsert(
            batch,
            on_conflict="org_id",
        ).execute()

        stats.created += len(response.data) if response.data else 0

    except Exception as e:
        stats.errors.append({
            "batch_size": len(batch),
            "error": str(e),
            "first_lp": batch[0].get("external_id") if batch else None,
        })


def get_lp_profile_by_org(client: Client, org_id: str) -> dict | None:
    """Get LP profile by organization ID."""
    try:
        response = client.table("lp_profiles").select("*").eq(
            "org_id", org_id
        ).single().execute()
        return response.data
    except Exception:
        return None
