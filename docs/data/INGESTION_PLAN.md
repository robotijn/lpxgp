# Data Ingestion Plan: Metabase → Supabase

## Overview

**Source:** Metabase (IPEM ERP readonly MySQL)
**Target:** Supabase (LPxGP PostgreSQL)
**Mode:** READ-ONLY from source, COPY to target

---

## Data Sources Summary

| Source File | Rows | Maps To |
|-------------|------|---------|
| `contacts.csv` | 5,880 | `people` + `employment` |
| `companies_crm.csv` | 30,339 | `organizations` |
| `global_funds.csv` | 1,773 | `funds` |
| `lp_matchmaking.csv` | 1,757 | `lp_profiles` (enrichment) |
| `parent_companies.csv` | 28,426 | `organizations` (parent links) |

---

## Phase 1: Organizations (Companies)

### Source: `companies_crm.csv`
```
Organization ID  → external_id (new column for mapping)
Company Name     → name
Website          → website
Description      → description
Country          → hq_country
```

### Source: `parent_companies.csv` (enrichment)
```
parent_company_id      → external_id
parent_company_name    → name
parent_country         → hq_country
child_companies        → used for hierarchy
```

### Transformation Rules:
1. Deduplicate by `Organization ID`
2. Set `is_lp = TRUE` if company appears in LP contacts
3. Set `is_gp = TRUE` if company appears in fund_manager data
4. Store original `Organization ID` in metadata for future syncs

### New Column Needed:
```sql
ALTER TABLE organizations ADD COLUMN external_id TEXT;
ALTER TABLE organizations ADD COLUMN external_source TEXT DEFAULT 'ipem';
CREATE UNIQUE INDEX idx_org_external ON organizations(external_source, external_id);
```

---

## Phase 2: People (Contacts)

### Source: `contacts.csv`
```
Name                        → full_name
Email                       → email
LinkedIn                    → linkedin_url
Old Job Title               → (to employment.title)
Company name                → (lookup org_id)
Associated org ID           → (link to organizations.external_id)
contact certification status → certification_status (new column)
Work Status                 → employment_status
Validation result           → email_valid (new column)
```

### Transformation Rules:
1. Split `Name` into first_name/last_name if needed (keep full_name)
2. Normalize email (lowercase, trim)
3. Only import contacts with `Work Status = 'yes'` OR `certification status = 'Certified'`
4. Create `employment` record linking person to organization

### New Columns Needed:
```sql
ALTER TABLE people ADD COLUMN external_id TEXT;
ALTER TABLE people ADD COLUMN external_source TEXT DEFAULT 'ipem';
ALTER TABLE people ADD COLUMN certification_status TEXT;
ALTER TABLE people ADD COLUMN email_valid BOOLEAN;
CREATE UNIQUE INDEX idx_people_external ON people(external_source, external_id);
```

---

## Phase 3: Funds

### Source: `global_funds.csv`
```
fund_id                    → external_id
fund_manager_org_id        → org_id (via external_id lookup)
fund_name                  → name
fund_status                → status (map values)
fund_generation_number     → fund_number
description                → investment_thesis
private_equity_strategies  → strategy (parse)
vc_strategies              → sub_strategy
geographic_focus           → geographic_focus (array)
sectors                    → sector_focus (array)
esg_approach               → esg_policy (boolean)
investment_minimum         → check_size_min_mm
```

### Status Mapping:
```python
STATUS_MAP = {
    'Open': 'raising',
    'Closed': 'closed',
    'In Fundraising': 'raising',
    'Final Close': 'closed',
    'First Close': 'raising',
}
```

### New Columns Needed:
```sql
ALTER TABLE funds ADD COLUMN external_id TEXT;
ALTER TABLE funds ADD COLUMN external_source TEXT DEFAULT 'ipem';
CREATE UNIQUE INDEX idx_funds_external ON funds(external_source, external_id);
```

---

## Phase 4: LP Profiles (Enrichment)

### Source: `lp_matchmaking.csv`
```
organization_id           → org_id (via external_id lookup)
organization_name         → (verify match)
country_name              → (verify/update hq_country)
solicitations_received    → metadata for scoring
solicitations_accepted    → metadata for scoring
```

### Source: Form data (from contacts.csv)
LP preferences are embedded in contact form data. Extract:
- Asset class preferences → strategies[]
- Geographic preferences → geographic_preferences[]
- Sector preferences → sector_preferences[]
- Check size range → check_size_min_mm, check_size_max_mm

---

## Ingestion Script Structure

```
scripts/
  data_ingestion/
    __init__.py
    config.py           # DB connections, mappings
    extractors/
      contacts.py       # Read contacts CSV
      companies.py      # Read companies CSV
      funds.py          # Read funds CSV
    transformers/
      normalize.py      # Clean/normalize data
      dedupe.py         # Deduplication logic
      enrich.py         # Add computed fields
    loaders/
      organizations.py  # Load to organizations table
      people.py         # Load to people + employment
      funds.py          # Load to funds table
      lp_profiles.py    # Load to lp_profiles
    main.py             # Orchestrate ETL
    diff.py             # Daily diff for updates
```

---

## Execution Order

```
1. Organizations (companies_crm.csv + parent_companies.csv)
   ├── Create organizations with is_gp/is_lp flags
   └── Store external_id for linking

2. People (contacts.csv)
   ├── Create people records
   ├── Create employment linking to organizations
   └── Filter by certification status

3. LP Profiles (enrichment)
   ├── Create lp_profiles for LP organizations
   └── Extract preferences from form data

4. Funds (global_funds.csv)
   ├── Create fund records
   └── Link to GP organizations via fund_manager_org_id

5. Fund Teams (future)
   └── Link people to funds (requires contact-fund mapping)
```

---

## Data Quality Rules

### Organizations
- **Required:** name
- **Dedupe:** by external_id, then by normalized name+country
- **Validation:** website must be valid URL or NULL

### People
- **Required:** full_name, email
- **Dedupe:** by external_id, then by email
- **Validation:** email format, LinkedIn URL format
- **Filter:** Only `certification_status IN ('Certified', 'Waiting')`

### Funds
- **Required:** name, org_id
- **Dedupe:** by external_id
- **Validation:** target_size > 0 if provided

---

## Daily Sync Strategy

1. **Export from Metabase** (cron job using `metabase_exporter.py`)
2. **Compute diff** against last import
3. **Apply changes:**
   - New records → INSERT
   - Changed records → UPDATE (preserve our local changes)
   - Deleted records → SOFT DELETE (set deleted_at)
4. **Log all changes** for audit trail

### Conflict Resolution
- **Source wins:** external_id, certification_status, original company data
- **Local wins:** manual notes, custom fields, embeddings
- **Merge:** arrays (strategies, preferences) - union of both

---

## Schema Migrations Needed

```sql
-- Migration: Add external ID tracking
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE organizations ADD COLUMN IF NOT EXISTS external_source TEXT DEFAULT 'ipem';
ALTER TABLE people ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE people ADD COLUMN IF NOT EXISTS external_source TEXT DEFAULT 'ipem';
ALTER TABLE people ADD COLUMN IF NOT EXISTS certification_status TEXT;
ALTER TABLE people ADD COLUMN IF NOT EXISTS email_valid BOOLEAN;
ALTER TABLE funds ADD COLUMN IF NOT EXISTS external_id TEXT;
ALTER TABLE funds ADD COLUMN IF NOT EXISTS external_source TEXT DEFAULT 'ipem';

-- Indexes for sync
CREATE UNIQUE INDEX IF NOT EXISTS idx_org_external
  ON organizations(external_source, external_id) WHERE external_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_people_external
  ON people(external_source, external_id) WHERE external_id IS NOT NULL;
CREATE UNIQUE INDEX IF NOT EXISTS idx_funds_external
  ON funds(external_source, external_id) WHERE external_id IS NOT NULL;

-- Audit trail
CREATE TABLE IF NOT EXISTS sync_log (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  sync_date TIMESTAMPTZ DEFAULT NOW(),
  source TEXT NOT NULL,
  table_name TEXT NOT NULL,
  records_created INTEGER DEFAULT 0,
  records_updated INTEGER DEFAULT 0,
  records_deleted INTEGER DEFAULT 0,
  errors JSONB DEFAULT '[]'
);
```

---

## Next Steps

1. [ ] Create migration for external_id columns
2. [ ] Build ETL script skeleton
3. [ ] Test with small batch (100 records)
4. [ ] Run full import
5. [ ] Set up daily sync cron job
6. [ ] Build diff reporting dashboard
