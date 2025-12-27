# Complete CSV-to-Schema Column Mapping

Every column from raw CSV files mapped to our database schema, with expansion suggestions.

---

## 1. global_funds.csv → funds + organizations

| CSV Column | DB Table.Column | Transform | Status |
|------------|-----------------|-----------|--------|
| `fund_id` | `funds.external_id` | Direct | NEW (add external_id) |
| `fund_manager_org_id` | `organizations.external_id` → `funds.org_id` | Lookup | ✓ Exists |
| `fund_manager_name` | `organizations.name` | For matching | ✓ Exists |
| `created_at` | `funds.created_at` | Timestamp | ✓ Exists |
| `updated_at` | `funds.updated_at` | Timestamp | ✓ Exists |
| `fund_name` | `funds.name` | Direct | ✓ Exists |
| `fund_status` | `funds.status` | Map: "Open for investment"→"raising" | ✓ Exists |
| `fund_generation_number` | `funds.fund_number` | Parse int | ✓ Exists |
| `fund_size_category_EM` | `funds.fund_size_bucket` | Normalize | NEW COLUMN |
| `estimated_date_of_1st_close` | `funds.first_close_target` | Parse date | NEW COLUMN |
| `description` | `funds.investment_thesis` | Direct | ✓ Exists |
| `private_equity_strategies` | `funds.strategy_tags[]` | Normalize + merge | NEW COLUMN (array) |
| `vc_strategies` | `funds.strategy_tags[]` | Normalize + merge | ↑ same |
| `private_debt_strategies` | `funds.strategy_tags[]` | Normalize + merge | ↑ same |
| `real_assets_strategies` | `funds.strategy_tags[]` | Normalize + merge | ↑ same |
| `other_strategies` | `funds.strategy_tags[]` | Normalize + merge | ↑ same |
| `sectors` | `funds.sector_focus[]` | Normalize | ✓ Exists |
| `technologies` | `funds.sector_focus[]` | Merge with sectors | ✓ Exists |
| `geographic_focus` | `funds.geographic_focus[]` | Normalize | ✓ Exists |
| `geographic_scopes` | `funds.geographic_scope` | "Global"/"Regional"/"National" | NEW COLUMN |
| `esg_approach` | `funds.esg_policy` | Non-empty = true | ✓ Exists |
| `investment_term_duration` | `funds.fund_term_years` | Parse "7-10 years" → 8 | ✓ Exists |
| `fund_domiciliation` | `funds.domicile` | Direct | NEW COLUMN |
| `investment_minimum` | `funds.check_size_min_mm` | Parse "€1m" → 1.0 | ✓ Exists |
| `fee_structure_explanation` | `funds.fee_details` | Direct text | NEW COLUMN |
| `is_accessible_to_non_accredited` | `funds.non_accredited_ok` | Parse bool | NEW COLUMN |
| `contacts` | → `fund_team` junction | Parse "id:name" | ✓ Exists (via fund_team) |
| `teaser_document_urls` | `funds.pitch_deck_url` | First URL | ✓ Exists |

**LLM Enhancement Opportunities:**
- `description` + `sectors` + `strategies` → Generate enhanced `investment_thesis`
- `fee_structure_explanation` → Extract `management_fee_pct`, `carried_interest_pct`
- `esg_approach` text → Classify `esg_certifications[]`

---

## 2. lp_matchmaking.csv → organizations + lp_profiles + people

| CSV Column | DB Table.Column | Transform | Status |
|------------|-----------------|-----------|--------|
| `organization_id` | `organizations.external_id` | Direct | ✓ Exists |
| `organization_name` | `organizations.name` | Direct | ✓ Exists |
| `country_name` | `organizations.hq_country` | Direct | ✓ Exists |
| `lp_user_id` | `people.external_id` | Direct | NEW (add external_id) |
| `title` | `people.title` | Parse "mr"/"ms" | NEW COLUMN |
| `first_name` | `people.full_name` | Concat with last | ✓ Exists |
| `last_name` | `people.full_name` | Concat with first | ✓ Exists |
| `email` | `people.email` | Direct | ✓ Exists |
| `telephoneFixe` | `people.phone` | Direct | ✓ Exists |
| `telephonePort` | `people.mobile` | Direct | NEW COLUMN |
| `is_participating_at_paris_2025` | `lp_profiles.event_participation` JSONB | Event array | NEW COLUMN |
| `solicitations_received` | `lp_profiles.solicitations_received` | Direct | NEW COLUMN |
| `solicitations_accepted` | `lp_profiles.solicitations_accepted` | Direct | NEW COLUMN |
| `solicitations_declined` | `lp_profiles.solicitations_declined` | Direct | NEW COLUMN |
| `lastlogin_at` | `lp_profiles.last_activity_at` | Timestamp | NEW COLUMN |
| `lastactivity_at` | `lp_profiles.last_activity_at` | Use most recent | NEW COLUMN |

**LLM Enhancement Opportunities:**
- `organization_name` → Classify `lp_profiles.lp_type` (pension, endowment, etc.)
- `country_name` → Infer `lp_profiles.geographic_preferences[]`
- `solicitations_accepted/declined` ratio → Score engagement quality

**Derived Fields (calculate on load):**
```sql
acceptance_rate = solicitations_accepted / solicitations_received
engagement_score = f(acceptance_rate, lastactivity_at, solicitations_received)
```

---

## 3. companies_crm.csv → organizations

| CSV Column | DB Table.Column | Transform | Status |
|------------|-----------------|-----------|--------|
| `Organization ID` | `organizations.external_id` | Direct | ✓ Exists |
| `Company Name` | `organizations.name` | Direct | ✓ Exists |
| `Website` | `organizations.website` | Direct | ✓ Exists |
| `Description` | `organizations.description` | Direct | ✓ Exists |
| `Country` | `organizations.hq_country` | Direct | ✓ Exists |

**LLM Enhancement Opportunities:**
- `Description` + `Company Name` → Classify `is_lp`, `is_gp`
- `Description` → Generate `gp_profiles.investment_philosophy`
- `Website` → Scrape for additional metadata

---

## 4. contacts.csv → people + employment

| CSV Column | DB Table.Column | Transform | Status |
|------------|-----------------|-----------|--------|
| `Source` | `people.data_source` | Direct | NEW COLUMN |
| `original ID` | `people.external_id` | Direct | NEW (add external_id) |
| `contact certification status` | `people.certification_status` | Direct | NEW COLUMN |
| `Name` | `people.full_name` | Direct | ✓ Exists |
| `Old Job Title` | `employment.title` (historical) | With is_current=false | ✓ Exists |
| `Company name` | → `organizations.name` lookup → `employment.org_id` | Lookup | ✓ Exists |
| `Associated org ID` | `organizations.external_id` → `employment.org_id` | Lookup | ✓ Exists |
| `Company LinkedIn` | `organizations.linkedin_url` | Direct | NEW COLUMN |
| `Company domain` | `organizations.website` | Derive if empty | ✓ Exists |
| `Email` | `people.email` | Direct | ✓ Exists |
| `Validation result` | `people.email_valid` | Parse bool | NEW COLUMN |
| `LinkedIn` | `people.linkedin_url` | Direct | ✓ Exists |
| `Work Status` | `people.employment_status` | Map values | ✓ Exists |
| `New Company` | → New employment record | Create if different | ✓ Exists |
| `New Job Title` | `employment.title` (is_current=true) | Direct | ✓ Exists |
| `Reasoning` | `people.notes` | Job change notes | ✓ Exists |
| `New email` | `people.email` | Update if changed | ✓ Exists |
| `New email status` | `people.email_valid` | Parse bool | NEW COLUMN |

**Smart Join with LLM:**
- `Old Job Title` + `New Job Title` → Classify career trajectory (promoted, lateral, left industry)
- `Company name` + `New Company` → Detect M&A, rebrandings
- `Reasoning` → Extract structured job change data

---

## 5. parent_companies.csv → organizations (hierarchy)

| CSV Column | DB Table.Column | Transform | Status |
|------------|-----------------|-----------|--------|
| `parent_company_id` | `organizations.external_id` | Direct | ✓ Exists |
| `parent_company_name` | `organizations.name` | Direct | ✓ Exists |
| `parent_preqin_id` | `organizations.preqin_id` | Direct | NEW COLUMN |
| `parent_country` | `organizations.hq_country` | Direct | ✓ Exists |
| `company_managers_name` | → `people` records | Parse pipe-separated | ✓ Exists |
| `company_managers_crm_user_id` | `people.external_id` | Parse pipe-separated | NEW (add external_id) |
| `child_companies` | `organizations.parent_org_id` (on children) | Parse and link | NEW COLUMN |

**Hierarchy Modeling:**
```sql
-- Add to organizations table
parent_org_id UUID REFERENCES organizations(id),
org_level TEXT CHECK (org_level IN ('parent', 'subsidiary', 'division', 'standalone'))
```

---

## 6. form_questions.csv → Reference Data (Enum Values)

This file defines the SCHEMA for LP preferences. Use to validate enum values.

| CSV Column | Usage | Status |
|------------|-------|--------|
| `entity_type` | Filter: LP vs GP forms | Reference |
| `property_id` | Foreign key to Metabase | Reference |
| `property_key` | Maps to our column names | Reference |
| `question_name` | UI label | Reference |
| `enum_value_id` | Metabase FK | Reference |
| `enum_value_slug` | Normalize to this | Reference |
| `enum_value_name` | Display name | Reference |
| `input_type` | UI hint | Reference |

**Use for Validation:**
```python
VALID_STRATEGIES = ["buyout", "venture_seed", "venture_growth", ...]
VALID_GEOGRAPHIES = ["europe_west", "europe_east", "north_america", ...]
```

---

## Schema Expansion Migration (015_etl_expansion.sql)

```sql
-- ============================================================================
-- Migration: Add columns for ETL data ingestion
-- ============================================================================

-- Organizations: External sync + hierarchy
ALTER TABLE organizations
    ADD COLUMN IF NOT EXISTS linkedin_url TEXT,
    ADD COLUMN IF NOT EXISTS preqin_id TEXT,
    ADD COLUMN IF NOT EXISTS parent_org_id UUID REFERENCES organizations(id),
    ADD COLUMN IF NOT EXISTS org_level TEXT CHECK (org_level IN ('parent', 'subsidiary', 'division', 'standalone')) DEFAULT 'standalone';

-- People: External sync + data quality
ALTER TABLE people
    ADD COLUMN IF NOT EXISTS title TEXT,  -- Mr/Ms/Dr
    ADD COLUMN IF NOT EXISTS mobile TEXT,
    ADD COLUMN IF NOT EXISTS email_valid BOOLEAN,
    ADD COLUMN IF NOT EXISTS certification_status TEXT,
    ADD COLUMN IF NOT EXISTS data_source TEXT DEFAULT 'manual';

-- Funds: Strategy tags + sizing + terms
ALTER TABLE funds
    ADD COLUMN IF NOT EXISTS strategy_tags TEXT[] DEFAULT '{}',
    ADD COLUMN IF NOT EXISTS fund_size_bucket TEXT CHECK (fund_size_bucket IN ('micro', 'small', 'mid', 'large', 'mega')),
    ADD COLUMN IF NOT EXISTS geographic_scope TEXT CHECK (geographic_scope IN ('global', 'regional', 'national', 'local')),
    ADD COLUMN IF NOT EXISTS domicile TEXT,
    ADD COLUMN IF NOT EXISTS first_close_target DATE,
    ADD COLUMN IF NOT EXISTS fee_details TEXT,
    ADD COLUMN IF NOT EXISTS non_accredited_ok BOOLEAN DEFAULT FALSE;

-- LP Profiles: Behavioral metrics
ALTER TABLE lp_profiles
    ADD COLUMN IF NOT EXISTS solicitations_received INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS solicitations_accepted INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS solicitations_declined INTEGER DEFAULT 0,
    ADD COLUMN IF NOT EXISTS acceptance_rate DECIMAL(5,4) GENERATED ALWAYS AS (
        CASE WHEN solicitations_received > 0
             THEN solicitations_accepted::DECIMAL / solicitations_received
             ELSE NULL END
    ) STORED,
    ADD COLUMN IF NOT EXISTS last_activity_at TIMESTAMPTZ,
    ADD COLUMN IF NOT EXISTS event_participation JSONB DEFAULT '[]';

-- Indexes for new columns
CREATE INDEX IF NOT EXISTS idx_funds_strategy_tags ON funds USING GIN(strategy_tags);
CREATE INDEX IF NOT EXISTS idx_funds_size_bucket ON funds(fund_size_bucket);
CREATE INDEX IF NOT EXISTS idx_lp_profiles_acceptance ON lp_profiles(acceptance_rate) WHERE acceptance_rate IS NOT NULL;
CREATE INDEX IF NOT EXISTS idx_organizations_parent ON organizations(parent_org_id);
```

---

## Summary: What's Missing

### High Priority (blocking ETL)
| Column | Table | Reason |
|--------|-------|--------|
| `external_id` | people | Already on organizations, need on people too |
| `strategy_tags[]` | funds | Normalized merged strategies |
| `fund_size_bucket` | funds | Normalized size category |
| `solicitations_*` | lp_profiles | Behavioral matching signals |
| `acceptance_rate` | lp_profiles | Computed field for scoring |

### Medium Priority (data quality)
| Column | Table | Reason |
|--------|-------|--------|
| `email_valid` | people | Skip bad emails in outreach |
| `certification_status` | people | Filter qualified contacts |
| `last_activity_at` | lp_profiles | Engagement scoring |
| `domicile` | funds | LP jurisdiction preferences |

### Low Priority (nice to have)
| Column | Table | Reason |
|--------|-------|--------|
| `linkedin_url` | organizations | Enrichment source |
| `preqin_id` | organizations | External data linking |
| `parent_org_id` | organizations | Corporate hierarchy |
| `event_participation` | lp_profiles | Conference tracking |
