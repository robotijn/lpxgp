"""
Load fund records into Supabase.
"""
from collections.abc import Iterator

from supabase import Client

from ..config import SyncStats
from ..transformers.enrich import map_fund_status
from .organizations import get_org_id_by_external


def load_funds(
    client: Client | None,
    records: Iterator[dict],
    batch_size: int = 100,
    dry_run: bool = False,
) -> SyncStats:
    """
    Load fund records into Supabase.

    Links funds to GP organizations via org_external_id lookup.

    Args:
        client: Supabase client
        records: Iterator of fund dicts with keys:
            - external_id, name (required)
            - org_external_id (for GP link)
            - status_raw, fund_number, investment_thesis
            - strategy, sub_strategy, geographic_focus, sector_focus
            - esg_policy, check_size_min_mm
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

        # Look up GP organization (skip in dry run)
        org_id = None
        if dry_run:
            org_id = "dry-run-placeholder"
        elif record.get("org_external_id") and client:
            org_id = get_org_id_by_external(client, record["org_external_id"])

        if not org_id and not dry_run:
            # Can't create fund without GP org
            stats.skipped += 1
            stats.errors.append({
                "fund": record.get("name"),
                "error": f"GP org not found: {record.get('org_external_id')}",
            })
            continue

        # Map status
        status = map_fund_status(record.get("status_raw"))

        # Prepare fund record with RAW data only (for client display)
        # NOTE: AI normalized data goes to fund_ai_profiles table separately
        fund_data = {
            "external_id": record["external_id"],
            "external_source": "ipem",
            "org_id": org_id,
            "name": record["name"],
            "status": status,
            "fund_number": record.get("fund_number"),
            "investment_thesis": record.get("investment_thesis"),
            # ── RAW VALUES (what client sees) ──
            "strategies_raw": record.get("strategies_raw"),
            "fund_size_raw": record.get("fund_size_raw"),
            "geographic_scope_raw": record.get("geographic_scope_raw"),
            "domicile": record.get("domicile"),
            "fee_details": record.get("fee_details"),
            # Original arrays (still useful for display)
            "geographic_focus": record.get("geographic_focus_raw", "").split(",") if record.get("geographic_focus_raw") else [],
            "sector_focus": record.get("sectors_raw", "").split(",") if record.get("sectors_raw") else [],
            # Other fields
            "esg_policy": record.get("esg_policy", False),
            "check_size_min_mm": record.get("check_size_min_mm"),
            "data_source": "ipem",
        }

        batch.append(fund_data)

        if len(batch) >= batch_size:
            _upsert_batch(client, batch, stats, dry_run)
            batch = []

    # Process remaining
    if batch:
        _upsert_batch(client, batch, stats, dry_run)

    return stats


def _upsert_batch(client: Client, batch: list[dict], stats: SyncStats, dry_run: bool):
    """Upsert a batch of funds."""
    if dry_run:
        stats.created += len(batch)
        return

    try:
        response = client.table("funds").upsert(
            batch,
            on_conflict="external_source,external_id",
        ).execute()

        stats.created += len(response.data) if response.data else 0

    except Exception as e:
        stats.errors.append({
            "batch_size": len(batch),
            "error": str(e),
            "first_fund": batch[0].get("name") if batch else None,
        })
