"""
Configuration for data ingestion pipeline.
"""
import os
from pathlib import Path
from dataclasses import dataclass

# Paths
PROJECT_ROOT = Path(__file__).parent.parent.parent
DATA_DIR = PROJECT_ROOT / "docs" / "data" / "metabase_copy"

# Source files
SOURCE_FILES = {
    "companies": DATA_DIR / "companies_crm.csv",
    "parent_companies": DATA_DIR / "parent_companies.csv",
    "contacts": DATA_DIR / "contacts.csv",
    "global_funds": DATA_DIR / "global_funds.csv",
    "lp_matchmaking": DATA_DIR / "lp_matchmaking.csv",
}

# Supabase connection (from environment)
SUPABASE_URL = os.getenv("SUPABASE_URL", "")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY", "")

# Status mappings for funds
FUND_STATUS_MAP = {
    "Open for investment": "raising",
    "Closed for investment": "closed",
    "Not in market yet": "draft",
    "": "draft",
    # Legacy values from ingestion plan
    "Open": "raising",
    "Closed": "closed",
    "In Fundraising": "raising",
    "Final Close": "closed",
    "First Close": "raising",
}

# LP types mapping
LP_TYPE_MAP = {
    "pension": "pension",
    "endowment": "endowment",
    "foundation": "foundation",
    "family office": "family_office",
    "family-office": "family_office",
    "sovereign wealth": "sovereign_wealth",
    "sovereign-wealth": "sovereign_wealth",
    "insurance": "insurance",
    "fund of funds": "fund_of_funds",
    "fund-of-funds": "fund_of_funds",
}

# Certification statuses to import (filter to only import these)
VALID_CERTIFICATIONS = {"Certified", "Waiting"}

# Status that means "employed" in the data
EMPLOYED_WORK_STATUSES = {"yes", "Yes", "YES"}


@dataclass
class SyncStats:
    """Statistics for a sync operation."""
    created: int = 0
    updated: int = 0
    skipped: int = 0
    errors: list = None

    def __post_init__(self):
        if self.errors is None:
            self.errors = []
