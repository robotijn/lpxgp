# Data Pipeline & Enrichment

[← Back to Index](index.md)

---

## 7.1 Data Import Pipeline

```
┌─────────────────────────────────────────────────────────────────┐
│                     Data Import Pipeline                         │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌──────────┐  │
│  │  Upload  │───>│  Parse   │───>│  Clean   │───>│  Store   │  │
│  │ CSV/Excel│    │  Detect  │    │ Normalize│    │ Database │  │
│  └──────────┘    │  Types   │    │ Validate │    └──────────┘  │
│                  └──────────┘    └──────────┘                   │
│                                       │                          │
│                                       ▼                          │
│                              ┌──────────────┐                   │
│                              │   Enrich     │                   │
│                              │  (async job) │                   │
│                              └──────────────┘                   │
│                                       │                          │
│                                       ▼                          │
│                              ┌──────────────┐                   │
│                              │  Vectorize   │                   │
│                              │  (Voyage AI) │                   │
│                              └──────────────┘                   │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

---

## 7.2 Cleaning Rules

### Strategy Normalization

```python
STRATEGY_MAPPING = {
    # Input variations -> Canonical name
    "pe": "Private Equity",
    "private equity": "Private Equity",
    "buyout": "Private Equity - Buyout",
    "lbo": "Private Equity - Buyout",
    "growth": "Private Equity - Growth",
    "growth equity": "Private Equity - Growth",
    "vc": "Venture Capital",
    "venture": "Venture Capital",
    "venture capital": "Venture Capital",
    "early stage": "Venture Capital - Early Stage",
    "seed": "Venture Capital - Seed",
    "real estate": "Real Estate",
    "re": "Real Estate",
    "infrastructure": "Infrastructure",
    "infra": "Infrastructure",
    "credit": "Private Credit",
    "private credit": "Private Credit",
    "direct lending": "Private Credit - Direct Lending",
    "mezzanine": "Private Credit - Mezzanine",
    "mezz": "Private Credit - Mezzanine",
    # ... more mappings
}
```

### Geography Normalization

```python
GEOGRAPHY_MAPPING = {
    # Input variations -> ISO code + region
    "us": {"code": "US", "region": "North America"},
    "usa": {"code": "US", "region": "North America"},
    "united states": {"code": "US", "region": "North America"},
    "uk": {"code": "GB", "region": "Europe"},
    "united kingdom": {"code": "GB", "region": "Europe"},
    "germany": {"code": "DE", "region": "Europe"},
    "de": {"code": "DE", "region": "Europe"},
    # ... more mappings
}
```

### LP Type Normalization

```python
LP_TYPE_MAPPING = {
    "pension": "Public Pension",
    "public pension": "Public Pension",
    "corporate pension": "Corporate Pension",
    "endowment": "Endowment",
    "university endowment": "Endowment",
    "foundation": "Foundation",
    "family office": "Family Office",
    "fo": "Family Office",
    "sfo": "Single Family Office",
    "mfo": "Multi Family Office",
    "fof": "Fund of Funds",
    "fund of funds": "Fund of Funds",
    "swf": "Sovereign Wealth Fund",
    "sovereign wealth": "Sovereign Wealth Fund",
    "insurance": "Insurance Company",
    "insurance company": "Insurance Company",
    # ... more mappings
}
```

---

## 7.3 Data Sources & Enrichment

**Data Sources (No Web Scraping):**
- **CSV Import:** Bulk upload from spreadsheets (primary source)
- **Manual Entry:** Users add/edit LP records directly
- **Future API Integrations:** Preqin, PitchBook, and other data providers

**Design Principles:**
- No web scraping (no Puppeteer, no automated browsing)
- All data comes from explicit imports or manual entry
- Bulk update support for external data provider feeds
- Human review required before committing enriched data

```
┌─────────────────────────────────────────────────────────────────┐
│                    Data Enrichment Flow                          │
├─────────────────────────────────────────────────────────────────┤
│                                                                  │
│  Data Sources:                                                   │
│  ├── CSV/Excel Import (current)                                 │
│  ├── Manual Entry (current)                                     │
│  └── API Integrations (future: Preqin, PitchBook)               │
│                                                                  │
│  Processing Pipeline:                                            │
│                                                                  │
│  1. Import/Update Detection                                     │
│     ├── Parse incoming data                                     │
│     ├── Match against existing records (name + location)        │
│     └── Queue for human review if conflicts detected            │
│                                                                  │
│  2. Human Review (for bulk updates)                             │
│     ├── Show diff between old and new values                    │
│     ├── Allow field-by-field approval                           │
│     └── Require explicit confirmation                           │
│                                                                  │
│  3. Generate Embeddings                                         │
│     ├── Combine: mandate_description + strategies + notes       │
│     ├── Voyage AI: Generate 1024-dim embedding                  │
│     └── Supabase: Store in mandate_embedding column             │
│                                                                  │
│  4. Calculate Data Quality Score                                │
│     ├── Score = weighted sum of field completeness              │
│     ├── Bonus for recent verification                           │
│     └── Supabase: Store in data_quality_score                   │
│                                                                  │
│  5. Update Audit Trail                                          │
│     ├── Record data_source for each field                       │
│     ├── Track last_verified date                                │
│     └── Set verification_status                                 │
│                                                                  │
└─────────────────────────────────────────────────────────────────┘
```

**Future API Integration Design:**
- Standardized adapter pattern for data providers
- Scheduled sync jobs (configurable frequency)
- Field-level merge rules (e.g., "prefer Preqin for AUM")
- Conflict resolution queue for human review

---

## 7.4 Data Quality Scoring

```python
def calculate_data_quality_score(lp: LP) -> float:
    """
    Calculate data quality score from 0.0 to 1.0
    """
    weights = {
        # High importance (must have)
        "name": 0.10,
        "type": 0.10,
        "strategies": 0.10,
        "check_size_min_mm": 0.05,
        "check_size_max_mm": 0.05,

        # Medium importance (should have)
        "total_aum_bn": 0.08,
        "geographic_preferences": 0.08,
        "mandate_description": 0.10,
        "website": 0.04,

        # Lower importance (nice to have)
        "sector_preferences": 0.05,
        "min_track_record_years": 0.05,
        "esg_required": 0.03,
        "emerging_manager_program": 0.03,

        # Enrichment bonus
        "has_contacts": 0.07,
        "has_commitments": 0.05,
        "recently_verified": 0.02,
    }

    score = 0.0
    for field, weight in weights.items():
        if field == "has_contacts":
            if lp.contacts and len(lp.contacts) > 0:
                score += weight
        elif field == "has_commitments":
            if lp.commitments and len(lp.commitments) > 0:
                score += weight
        elif field == "recently_verified":
            if lp.last_verified and (now() - lp.last_verified).days < 180:
                score += weight
        elif getattr(lp, field, None):
            score += weight

    return round(score, 2)
```

---

[Next: Technical Architecture →](technical.md)
