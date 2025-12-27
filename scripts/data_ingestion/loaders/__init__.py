"""
Loaders: Write data to Supabase.
Uses upsert with external_id for idempotent imports.
"""
from .organizations import load_organizations
from .people import load_people
from .funds import load_funds

__all__ = ["load_organizations", "load_people", "load_funds"]
