"""
Load organizations into Supabase.
"""
from collections.abc import Iterator

from supabase import Client

from ..config import SyncStats


def load_organizations(
    client: Client | None,
    records: Iterator[dict],
    batch_size: int = 100,
    dry_run: bool = False,
) -> SyncStats:
    """
    Load organization records into Supabase.

    Uses upsert on (external_source, external_id) for idempotent imports.
    Creates new records or updates existing ones.

    Args:
        client: Supabase client
        records: Iterator of organization dicts with keys:
            - external_id (required)
            - name (required)
            - website, description, hq_country (optional)
            - is_lp, is_gp (booleans)
        batch_size: Number of records per batch
        dry_run: If True, don't actually write to database

    Returns:
        SyncStats with counts
    """
    stats = SyncStats()
    batch = []

    for record in records:
        # Validate required fields
        if not record.get("external_id") or not record.get("name"):
            stats.skipped += 1
            continue

        # Prepare record for insert
        org_data = {
            "external_id": record["external_id"],
            "external_source": "ipem",
            "name": record["name"],
            "website": record.get("website"),
            "description": record.get("description"),
            "hq_country": record.get("hq_country"),
            "is_lp": record.get("is_lp", False),
            "is_gp": record.get("is_gp", False),
        }

        batch.append(org_data)

        if len(batch) >= batch_size:
            _upsert_batch(client, batch, stats, dry_run)
            batch = []

    # Process remaining
    if batch:
        _upsert_batch(client, batch, stats, dry_run)

    return stats


def _upsert_batch(client: Client, batch: list[dict], stats: SyncStats, dry_run: bool):
    """Upsert a batch of organizations."""
    if dry_run:
        stats.created += len(batch)
        return

    try:
        # Use upsert with on_conflict on external_source + external_id
        response = client.table("organizations").upsert(
            batch,
            on_conflict="external_source,external_id",
        ).execute()

        # Count results (Supabase doesn't differentiate created vs updated in response)
        stats.created += len(response.data) if response.data else 0

    except Exception as e:
        stats.errors.append({
            "batch_size": len(batch),
            "error": str(e),
            "first_record": batch[0] if batch else None,
        })


def get_org_id_by_external(client: Client, external_id: str, source: str = "ipem") -> str | None:
    """
    Look up internal org_id by external_id.

    Returns:
        UUID string or None if not found
    """
    try:
        response = client.table("organizations").select("id").eq(
            "external_source", source
        ).eq("external_id", external_id).limit(1).execute()

        if response.data and len(response.data) > 0:
            return response.data[0].get("id")
        return None
    except Exception:
        return None
