"""
Loaders: Write data to Supabase.
Uses upsert with external_id for idempotent imports.
"""
from .funds import load_funds
from .organizations import load_organizations
from .people import load_people

__all__ = ["load_organizations", "load_people", "load_funds"]
