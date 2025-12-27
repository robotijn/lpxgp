"""
Load AI matching profiles into Supabase.

IMPORTANT: These tables are for AI matching algorithms ONLY.
Client-facing code should NEVER read from these tables.

Tables:
- fund_ai_profiles: Normalized fund data for matching
- lp_ai_profiles: Normalized LP data for matching
- match_cache: Pre-computed match scores
"""
from collections.abc import Iterator

from supabase import Client

from ..config import SyncStats


def load_fund_ai_profiles(
    client: Client | None,
    records: Iterator[dict],
    batch_size: int = 100,
    dry_run: bool = False,
) -> SyncStats:
    """
    Load fund AI profiles from extracted fund records.

    Maps fund_id → fund_ai_profiles with normalized AI fields.

    Args:
        client: Supabase client
        records: Iterator of fund dicts with ai_* prefixed keys
        batch_size: Number of records per batch
        dry_run: If True, don't write to database

    Returns:
        SyncStats with counts
    """
    stats = SyncStats()
    batch = []

    for record in records:
        # Need fund_id to link to funds table
        fund_id = record.get("fund_id")
        if not fund_id:
            stats.skipped += 1
            continue

        # Build AI profile from ai_* prefixed fields
        ai_profile = {
            "fund_id": fund_id,
            "strategy_tags": record.get("ai_strategy_tags", []),
            "geography_tags": record.get("ai_geography_tags", []),
            "sector_tags": record.get("ai_sector_tags", []),
            "size_bucket": record.get("ai_size_bucket"),
            "size_mm": record.get("ai_size_mm"),
            "has_esg": record.get("ai_has_esg", False),
            # Completeness score based on filled fields
            "completeness_score": _calculate_completeness(record),
        }

        batch.append(ai_profile)

        if len(batch) >= batch_size:
            _upsert_fund_ai_batch(client, batch, stats, dry_run)
            batch = []

    if batch:
        _upsert_fund_ai_batch(client, batch, stats, dry_run)

    return stats


def _calculate_completeness(record: dict) -> float:
    """Calculate data completeness score (0.0 to 1.0)."""
    fields = [
        "ai_strategy_tags",
        "ai_geography_tags",
        "ai_sector_tags",
        "ai_size_bucket",
        "investment_thesis",
    ]
    filled = sum(1 for f in fields if record.get(f))
    return round(filled / len(fields), 2)


def _upsert_fund_ai_batch(
    client: Client | None,
    batch: list[dict],
    stats: SyncStats,
    dry_run: bool,
):
    """Upsert a batch of fund AI profiles."""
    if dry_run:
        stats.created += len(batch)
        return

    if not client:
        return

    try:
        response = client.table("fund_ai_profiles").upsert(
            batch,
            on_conflict="fund_id",
        ).execute()

        stats.created += len(response.data) if response.data else 0

    except Exception as e:
        stats.errors.append({
            "batch_size": len(batch),
            "error": str(e),
            "first_fund_id": batch[0].get("fund_id") if batch else None,
        })


def load_lp_ai_profiles(
    client: Client | None,
    records: Iterator[dict],
    batch_size: int = 100,
    dry_run: bool = False,
) -> SyncStats:
    """
    Load LP AI profiles from extracted LP records.

    Maps lp_profile_id → lp_ai_profiles with normalized AI fields
    and behavioral metrics.

    Args:
        client: Supabase client
        records: Iterator of LP dicts with ai_* prefixed keys
        batch_size: Number of records per batch
        dry_run: If True, don't write to database

    Returns:
        SyncStats with counts
    """
    stats = SyncStats()
    batch = []

    for record in records:
        lp_profile_id = record.get("lp_profile_id")
        org_id = record.get("org_id")
        if not lp_profile_id or not org_id:
            stats.skipped += 1
            continue

        # Calculate acceptance rate from behavioral data
        received = record.get("solicitations_received", 0)
        accepted = record.get("solicitations_accepted", 0)
        acceptance_rate = (accepted / received) if received > 0 else None

        # Build AI profile
        ai_profile = {
            "lp_profile_id": lp_profile_id,
            "org_id": org_id,
            "strategy_interests": record.get("ai_strategy_interests", []),
            "geography_interests": record.get("ai_geography_interests", []),
            "sector_interests": record.get("ai_sector_interests", []),
            "size_preferences": record.get("ai_size_preferences", []),
            "check_size_min_mm": record.get("check_size_min_mm"),
            "check_size_max_mm": record.get("check_size_max_mm"),
            "requires_esg": record.get("ai_requires_esg", False),
            "accepts_emerging": record.get("ai_accepts_emerging", False),
            # Behavioral metrics
            "acceptance_rate": acceptance_rate,
            "total_interactions": received,
            "engagement_score": _calculate_engagement(record, acceptance_rate),
            # Data sources
            "data_sources": _determine_data_sources(record),
            "confidence_score": _calculate_confidence(record),
        }

        batch.append(ai_profile)

        if len(batch) >= batch_size:
            _upsert_lp_ai_batch(client, batch, stats, dry_run)
            batch = []

    if batch:
        _upsert_lp_ai_batch(client, batch, stats, dry_run)

    return stats


def _calculate_engagement(record: dict, acceptance_rate: float | None) -> float:
    """
    Calculate engagement score (0.0 to 1.0).

    Composite of:
    - Acceptance rate (40%)
    - Activity recency (30%)
    - Interaction volume (30%)
    """
    score = 0.0

    # Acceptance rate component (0-40 points)
    if acceptance_rate is not None:
        score += acceptance_rate * 0.4

    # Recency component (0-30 points) - would need last_activity_at
    # For now, assume recent if we have behavioral data
    if record.get("solicitations_received", 0) > 0:
        score += 0.2  # Has some activity

    # Volume component (0-30 points)
    received = record.get("solicitations_received", 0)
    if received >= 100:
        score += 0.3
    elif received >= 50:
        score += 0.2
    elif received >= 10:
        score += 0.1

    return round(min(score, 1.0), 2)


def _determine_data_sources(record: dict) -> list[str]:
    """Determine which data sources contributed to this profile."""
    sources = []

    # Explicit preferences from forms
    if any(record.get(f"ai_{key}", []) for key in ["strategy_interests", "sector_interests"]):
        sources.append("explicit")

    # Behavioral data
    if record.get("solicitations_received", 0) > 0:
        sources.append("behavioral")

    # Inferred (would be added by ML pipeline later)
    if record.get("inferred_strategy_probs"):
        sources.append("inferred")

    return sources or ["unknown"]


def _calculate_confidence(record: dict) -> float:
    """Calculate confidence score based on data quality."""
    score = 0.0

    # Has explicit preferences
    if record.get("ai_strategy_interests"):
        score += 0.3

    # Has behavioral data
    received = record.get("solicitations_received", 0)
    if received >= 50:
        score += 0.4
    elif received >= 10:
        score += 0.2

    # Has geographic data
    if record.get("ai_geography_interests"):
        score += 0.2

    # Has size preferences
    if record.get("check_size_min_mm") or record.get("ai_size_preferences"):
        score += 0.1

    return round(min(score, 1.0), 2)


def _upsert_lp_ai_batch(
    client: Client | None,
    batch: list[dict],
    stats: SyncStats,
    dry_run: bool,
):
    """Upsert a batch of LP AI profiles."""
    if dry_run:
        stats.created += len(batch)
        return

    if not client:
        return

    try:
        response = client.table("lp_ai_profiles").upsert(
            batch,
            on_conflict="lp_profile_id",
        ).execute()

        stats.created += len(response.data) if response.data else 0

    except Exception as e:
        stats.errors.append({
            "batch_size": len(batch),
            "error": str(e),
            "first_lp_id": batch[0].get("lp_profile_id") if batch else None,
        })


def sync_fund_ai_profiles(client: Client, dry_run: bool = False) -> SyncStats:
    """
    Sync all fund_ai_profiles from existing funds table.

    Call this after loading funds to populate AI profiles.
    """
    stats = SyncStats()

    if dry_run:
        return stats

    try:
        # Get all funds with their data
        response = client.table("funds").select(
            "id, investment_thesis, strategy, sub_strategy, geographic_focus, "
            "sector_focus, esg_policy, target_size_mm, strategies_raw, fund_size_raw"
        ).execute()

        if not response.data:
            return stats

        # For each fund, create/update AI profile
        # Note: In production, this would use the normalizers
        for fund in response.data:
            ai_profile = {
                "fund_id": fund["id"],
                # These would be normalized from raw values
                "strategy_tags": fund.get("strategy", "").split(",") if fund.get("strategy") else [],
                "geography_tags": fund.get("geographic_focus", []),
                "sector_tags": fund.get("sector_focus", []),
                "has_esg": fund.get("esg_policy", False),
                "size_mm": fund.get("target_size_mm"),
            }

            try:
                client.table("fund_ai_profiles").upsert(
                    ai_profile,
                    on_conflict="fund_id",
                ).execute()
                stats.created += 1
            except Exception as e:
                stats.errors.append({"fund_id": fund["id"], "error": str(e)})

    except Exception as e:
        stats.errors.append({"error": f"Failed to sync: {e}"})

    return stats
