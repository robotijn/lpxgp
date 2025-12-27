"""
Load people and employment records into Supabase.
"""
from collections.abc import Iterator

from supabase import Client

from ..config import EMPLOYED_WORK_STATUSES, VALID_CERTIFICATIONS, SyncStats
from .organizations import get_org_id_by_external


def load_people(
    client: Client | None,
    records: Iterator[dict],
    batch_size: int = 100,
    dry_run: bool = False,
) -> SyncStats:
    """
    Load people records and their employment into Supabase.

    Filters to only import contacts with valid certification status.
    Creates employment records linking to organizations.

    Args:
        client: Supabase client
        records: Iterator of contact dicts with keys:
            - full_name, email (required)
            - linkedin_url, certification_status, email_valid (optional)
            - org_external_id, title (for employment)
        batch_size: Number of records per batch
        dry_run: If True, don't actually write to database

    Returns:
        SyncStats with counts
    """
    stats = SyncStats()

    for record in records:
        # Validate required fields
        if not record.get("full_name"):
            stats.skipped += 1
            continue

        # Filter by certification status
        cert_status = record.get("certification_status", "")
        work_status = record.get("work_status", "")
        if cert_status not in VALID_CERTIFICATIONS and work_status not in EMPLOYED_WORK_STATUSES:
            stats.skipped += 1
            continue

        # Prepare person record
        person_data = {
            "full_name": record["full_name"],
            "email": record.get("email"),
            "linkedin_url": record.get("linkedin_url"),
            "certification_status": cert_status or None,
            "email_valid": record.get("email_valid"),
            "external_source": "ipem",
        }

        # If we have org link, look up org_id
        org_id = None
        if record.get("org_external_id"):
            org_id = get_org_id_by_external(client, record["org_external_id"])

        if dry_run:
            stats.created += 1
            continue

        try:
            # Insert or update person
            # Use email as unique key if available, otherwise insert new
            if record.get("email"):
                response = client.table("people").upsert(
                    person_data,
                    on_conflict="email",
                ).execute()
            else:
                response = client.table("people").insert(person_data).execute()

            person_id = response.data[0]["id"] if response.data else None

            # Create employment link if we have org_id
            if person_id and org_id:
                _create_employment(
                    client,
                    person_id=person_id,
                    org_id=org_id,
                    title=record.get("title"),
                )

            stats.created += 1

        except Exception as e:
            stats.errors.append({
                "record": record.get("email") or record.get("full_name"),
                "error": str(e),
            })

    return stats


def _create_employment(
    client: Client,
    person_id: str,
    org_id: str,
    title: str | None = None,
):
    """Create or update employment record."""
    try:
        # Check if employment already exists
        existing = client.table("employment").select("id").eq(
            "person_id", person_id
        ).eq("org_id", org_id).eq("is_current", True).execute()

        if existing.data:
            # Update existing
            client.table("employment").update({
                "title": title,
            }).eq("id", existing.data[0]["id"]).execute()
        else:
            # Create new
            client.table("employment").insert({
                "person_id": person_id,
                "org_id": org_id,
                "title": title,
                "is_current": True,
                "source": "ipem",
            }).execute()
    except Exception:
        # Non-fatal - person was created, employment link failed
        pass
