# Data Pipeline Architecture

[Back to TRD Index](index.md)

---

## Overview

LPxGP ingests data from multiple sources (CSV files, API feeds, manual entry) and resolves entities using a hybrid ML/LLM approach to create high-quality "Golden Records."

---

## Entity Resolution Architecture

### The Problem

LP/GP data exists in multiple fragmented sources with:
- Inconsistent naming (e.g., "CalPERS" vs "California Public Employees")
- Missing fields (random data populated)
- Duplicates across sources
- Conflicting information

### Solution: Hybrid Ensemble Pipeline

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                    ENTITY RESOLUTION PIPELINE                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  STAGE 1: BLOCKING                                                           │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  Purpose: Reduce candidate pairs from O(n²) to manageable set           ││
│  │                                                                          ││
│  │  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐                     ││
│  │  │  Phonetic   │  │  Embedding  │  │   Rule-     │                     ││
│  │  │  (Metaphone)│  │  (Voyage AI)│  │   Based     │                     ││
│  │  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘                     ││
│  │         │                │                │                             ││
│  │         └────────────────┴────────────────┘                             ││
│  │                          │                                               ││
│  │                          ▼                                               ││
│  │              Candidate Pairs (~5-10x reduction)                         ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                             │                                                │
│                             ▼                                                │
│  STAGE 2: FEATURE EXTRACTION                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  20+ features per pair:                                                  ││
│  │                                                                          ││
│  │  STRING SIMILARITY          SEMANTIC                 STRUCTURAL          ││
│  │  ────────────────          ────────                 ──────────          ││
│  │  • Levenshtein             • Embedding cosine       • AUM ratio          ││
│  │  • Jaro-Winkler            • Thesis similarity      • Strategy overlap   ││
│  │  • Token sort ratio                                 • Entity type match  ││
│  │  • Metaphone match                                  • Geography match    ││
│  │                                                                          ││
│  │  IDENTIFIER                DOMAIN-SPECIFIC                               ││
│  │  ──────────                ───────────────                               ││
│  │  • Domain match            • Fund number match                           ││
│  │  • LinkedIn match          • Legal suffix match                          ││
│  │  • Email domain            • Vintage year diff                           ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                             │                                                │
│                             ▼                                                │
│  STAGE 3: ENSEMBLE CLASSIFIER                                                │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  Stacking Meta-Learner:                                                  ││
│  │                                                                          ││
│  │  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐                ││
│  │  │ LogReg   │  │   GBM    │  │    RF    │  │   SVM    │                ││
│  │  │  (35%)   │  │  (35%)   │  │  (20%)   │  │  (10%)   │                ││
│  │  └────┬─────┘  └────┬─────┘  └────┬─────┘  └────┬─────┘                ││
│  │       │             │             │             │                       ││
│  │       └─────────────┴─────────────┴─────────────┘                       ││
│  │                          │                                               ││
│  │                          ▼                                               ││
│  │              ┌───────────────────────┐                                  ││
│  │              │   Meta-Learner        │                                  ││
│  │              │   (LogisticRegression)│                                  ││
│  │              └───────────┬───────────┘                                  ││
│  │                          │                                               ││
│  │              ┌───────────▼───────────┐                                  ││
│  │              │     P(match)          │                                  ││
│  │              └───────────┬───────────┘                                  ││
│  │                          │                                               ││
│  │       ┌──────────────────┼──────────────────┐                           ││
│  │       ▼                  ▼                  ▼                           ││
│  │   p > 0.8            0.3 ≤ p ≤ 0.8      p < 0.3                        ││
│  │   MATCH              UNCERTAIN           NON-MATCH                      ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                             │                                                │
│              ┌──────────────┴──────────────┐                                │
│              ▼                             ▼                                │
│  STAGE 4: LLM TIEBREAKER           (Skip for high confidence)               │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  Only for UNCERTAIN pairs (~10-20% of candidates)                       ││
│  │                                                                          ││
│  │  ┌─────────────────────────────────────────────────────────────────┐   ││
│  │  │  Self-Consistency (3 samples):                                   │   ││
│  │  │                                                                   │   ││
│  │  │  Sample 1: MATCH    ──┐                                          │   ││
│  │  │  Sample 2: MATCH    ──┼── Majority Vote ──▶ MATCH (confidence:2/3)│   ││
│  │  │  Sample 3: NON_MATCH──┘                                          │   ││
│  │  └─────────────────────────────────────────────────────────────────┘   ││
│  │                                                                          ││
│  │  Model: Claude Sonnet 4 via OpenRouter                                  ││
│  │  Cost: ~$0.003-0.01 per pair                                            ││
│  │  Output: decision, confidence, evidence_for, evidence_against           ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                             │                                                │
│                             ▼                                                │
│  STAGE 5: HUMAN REVIEW QUEUE                                                 │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  Pairs where LLM disagreed or confidence < threshold                    ││
│  │                                                                          ││
│  │  Priority Queue:                                                        ││
│  │  1. High-value entities (Tier 1 LPs)                                    ││
│  │  2. Large clusters (affects many records)                               ││
│  │  3. Recent imports                                                       ││
│  │                                                                          ││
│  │  Human decisions → Retrain ensemble monthly                             ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                             │                                                │
│                             ▼                                                │
│  STAGE 6: CLUSTERING                                                         │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  Graph-based transitive closure:                                        ││
│  │                                                                          ││
│  │  A matches B, B matches C → A, B, C in same cluster                     ││
│  │                                                                          ││
│  │  Conflict detection:                                                     ││
│  │  If cluster has conflicting attributes → Flag for review                ││
│  │                                                                          ││
│  │  Library: networkx                                                       ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                             │                                                │
│                             ▼                                                │
│  STAGE 7: GOLDEN RECORD CREATION                                             │
│  ┌─────────────────────────────────────────────────────────────────────────┐│
│  │  Field-by-field merge with source priority:                             ││
│  │                                                                          ││
│  │  Priority (high to low):                                                ││
│  │  1. Manual entry (user confirmed)                                       ││
│  │  2. Verified source (PitchBook, Preqin)                                ││
│  │  3. API import (LinkedIn, etc.)                                         ││
│  │  4. CSV import (bulk data)                                              ││
│  │  5. AI inferred                                                         ││
│  │                                                                          ││
│  │  Full provenance audit trail retained                                   ││
│  └─────────────────────────────────────────────────────────────────────────┘│
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## Bootstrap Strategy (Zero-Label Start)

### Cold Start Problem

No human labels exist initially. Solution: Generate training labels from high-confidence heuristic rules.

### Tier 1: Very High Confidence (use for training)

```python
# These rules have near-100% precision
tier1_match_rules = [
    # Same unique identifier
    lambda a, b: a.get("linkedin_url") == b.get("linkedin_url") and a.get("linkedin_url"),

    # Exact name + same registered address
    lambda a, b: (
        normalize(a["name"]) == normalize(b["name"])
        and a.get("hq_city") == b.get("hq_city")
        and a.get("hq_country") == b.get("hq_country")
    ),

    # Same SEC CIK number
    lambda a, b: a.get("sec_cik") == b.get("sec_cik") and a.get("sec_cik"),
]

tier1_non_match_rules = [
    # Different entity types AND different countries
    lambda a, b: (
        a.get("lp_type") != b.get("lp_type")
        and a.get("hq_country") != b.get("hq_country")
        and a.get("lp_type") and b.get("lp_type")
    ),

    # 1000x AUM difference
    lambda a, b: (
        a.get("total_aum_bn") and b.get("total_aum_bn")
        and max(a["total_aum_bn"], b["total_aum_bn"]) /
            max(min(a["total_aum_bn"], b["total_aum_bn"]), 0.001) > 1000
    ),
]
```

### Tier 2: High Confidence (reduced weight)

```python
tier2_match_rules = [
    # Same website domain + name similarity > 0.8
    lambda a, b: (
        same_domain(a.get("website"), b.get("website"))
        and fuzz.token_set_ratio(a["name"], b["name"]) > 80
    ),

    # Phonetic match + same city
    lambda a, b: (
        doublemetaphone(a["name"])[0] == doublemetaphone(b["name"])[0]
        and a.get("hq_city") == b.get("hq_city")
    ),
]
```

### Bootstrap Timeline

| Day | State | Labels | Accuracy |
|-----|-------|--------|----------|
| Day 1 | Heuristic model | Tier 1+2 only | ~70-80% |
| Week 2 | First human labels | ~50 human + heuristics | ~85% |
| Month 1 | Stable model | ~200 human labels | ~90% |
| Ongoing | Monthly retrain | Accumulated data | ~95%+ |

---

## Domain-Specific Features

Beyond generic string similarity, extract financial domain features:

```python
@dataclass
class FinancialFeatures:
    """Domain-specific features for GP/LP entity resolution."""

    # Organization Type
    both_gp: float
    both_lp: float
    type_compatible: float

    # Investment Strategy
    strategy_jaccard: float
    primary_strategy_match: float
    strategy_embedding_sim: float

    # Size & Scale
    aum_log_diff: float
    aum_same_order: float
    check_size_overlap: float

    # Geographic
    same_country: float
    same_region: float
    geo_preference_overlap: float

    # Track Record
    vintage_year_diff: float
    fund_number_diff: float

    # Name Patterns
    has_fund_number_a: float
    has_fund_number_b: float
    fund_number_match: float
    same_legal_suffix: float
    name_without_suffix_sim: float
```

---

## Import Adapters

### Adapter Interface

```python
from abc import ABC, abstractmethod
from typing import Iterator

class ImportAdapter(ABC):
    """Base class for data source adapters."""

    @abstractmethod
    def connect(self) -> None:
        """Establish connection to data source."""
        pass

    @abstractmethod
    def fetch_records(self) -> Iterator[dict]:
        """Yield normalized records."""
        pass

    @abstractmethod
    def get_source_metadata(self) -> dict:
        """Return source information for provenance."""
        pass
```

### CSV Adapter

```python
class CSVAdapter(ImportAdapter):
    """Import from CSV files with column mapping."""

    def __init__(self, file_path: str, mapping: dict):
        self.file_path = file_path
        self.mapping = mapping  # {source_col: target_field}

    def fetch_records(self) -> Iterator[dict]:
        import csv
        with open(self.file_path) as f:
            reader = csv.DictReader(f)
            for row in reader:
                yield self._normalize(row)

    def _normalize(self, row: dict) -> dict:
        normalized = {}
        for source_col, target_field in self.mapping.items():
            if source_col in row:
                normalized[target_field] = self._clean(row[source_col])
        return normalized
```

### Salesforce Adapter

```python
class SalesforceAdapter(ImportAdapter):
    """Import from Salesforce CRM."""

    def __init__(self, instance_url: str, access_token: str):
        self.sf = Salesforce(instance_url=instance_url, session_id=access_token)

    def fetch_records(self) -> Iterator[dict]:
        query = """
            SELECT Id, Name, Type, Website, BillingCity, BillingCountry
            FROM Account
            WHERE Type IN ('LP', 'GP')
        """
        for record in self.sf.query_all(query)["records"]:
            yield self._normalize(record)
```

### HubSpot Adapter

```python
class HubSpotAdapter(ImportAdapter):
    """Import from HubSpot CRM."""

    def __init__(self, api_key: str):
        self.client = hubspot.Client.create(api_key=api_key)

    def fetch_records(self) -> Iterator[dict]:
        companies = self.client.crm.companies.get_all()
        for company in companies:
            yield self._normalize(company.properties)
```

---

## Golden Record Creation

### Source Priority Rules

```python
SOURCE_PRIORITY = {
    "manual": 100,      # User confirmed
    "verified": 90,     # Known reliable source
    "pitchbook": 85,    # PitchBook API
    "preqin": 85,       # Preqin API
    "linkedin": 70,     # LinkedIn scrape
    "crm": 65,          # Salesforce/HubSpot
    "csv_import": 50,   # Bulk CSV
    "ai_inferred": 30,  # LLM extraction
}

def merge_field(existing: dict, new: dict, field: str) -> tuple[any, str]:
    """
    Merge a single field with source priority.
    Returns (value, source).
    """
    existing_source = existing.get(f"{field}_source", "unknown")
    new_source = new.get(f"{field}_source", "unknown")

    existing_priority = SOURCE_PRIORITY.get(existing_source, 0)
    new_priority = SOURCE_PRIORITY.get(new_source, 0)

    if new_priority > existing_priority:
        return new.get(field), new_source
    elif new_priority == existing_priority:
        # Same priority: prefer non-null, newer
        if new.get(field) and not existing.get(field):
            return new.get(field), new_source
        if new.get("updated_at", "") > existing.get("updated_at", ""):
            return new.get(field), new_source

    return existing.get(field), existing_source
```

### Provenance Tracking

```sql
-- Track source of each field value
CREATE TABLE field_provenance (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL,
    entity_id UUID NOT NULL,
    field_name TEXT NOT NULL,
    current_value TEXT,
    source TEXT NOT NULL,
    source_record_id TEXT,
    confidence DECIMAL(3,2),
    captured_at TIMESTAMPTZ DEFAULT NOW(),
    captured_by UUID,  -- User or system process
    superseded_by UUID REFERENCES field_provenance(id)
);

-- Index for quick lookup
CREATE INDEX idx_provenance_entity ON field_provenance(entity_type, entity_id, field_name);
```

---

## Caching Strategy

### Entity Cache Table

```sql
CREATE TABLE entity_cache (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    entity_type TEXT NOT NULL,  -- 'match', 'pitch', 'constraint', 'lp', 'fund'
    entity_id TEXT NOT NULL,    -- Composite key for matches: "fund_id:lp_id"
    cache_key TEXT NOT NULL,    -- 'debate_result', 'generated_pitch', etc.
    cache_value JSONB NOT NULL,
    source_debate_id UUID,
    valid_from TIMESTAMPTZ DEFAULT NOW(),
    valid_until TIMESTAMPTZ,
    invalidated_at TIMESTAMPTZ,
    invalidation_reason TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    UNIQUE(entity_type, entity_id, cache_key)
);
```

### Cache Invalidation

```python
class EntityCache:
    """Manages cached results with automatic invalidation."""

    @staticmethod
    async def invalidate_fund(fund_id: str, reason: str = "fund_updated"):
        """Invalidate all cached results for a fund."""
        await supabase.table("entity_cache").update({
            "invalidated_at": datetime.now().isoformat(),
            "invalidation_reason": reason,
        }).eq("entity_type", "match").like(
            "entity_id", f"{fund_id}:%"
        ).execute()

    @staticmethod
    async def invalidate_lp(lp_id: str, reason: str = "lp_updated"):
        """Invalidate all cached results for an LP."""
        await supabase.table("entity_cache").update({
            "invalidated_at": datetime.now().isoformat(),
            "invalidation_reason": reason,
        }).eq("entity_type", "match").like(
            "entity_id", f"%:{lp_id}"
        ).execute()
```

### Cache Lifetime

| Cache Type | Lifetime | Invalidation Trigger |
|------------|----------|---------------------|
| Match results | 90 days | Fund or LP updated |
| Pitches | 30 days | Match invalidated |
| LP constraints | 90 days | Mandate text changed |
| Research enrichment | 30 days | Re-enrichment run |

---

## Monthly Retrain Schedule

```python
class CachedERClassifier:
    """Entity resolution with monthly retrain and caching."""

    async def monthly_retrain(self):
        """Retrain model monthly with accumulated human labels."""
        # Fetch all training data
        training_data = await fetch_all_training_data()

        # Retrain stacking classifier
        new_model = StackingClassifier(
            estimators=[
                ('logreg', LogisticRegression()),
                ('gbm', GradientBoostingClassifier()),
                ('rf', RandomForestClassifier()),
                ('svm', CalibratedClassifierCV(SVC())),
            ],
            final_estimator=LogisticRegression(),
            cv=5,
        )
        new_model.fit(X_train, y_train)

        # Evaluate
        cv_score = cross_val_score(new_model, X, y, cv=5)

        # Only deploy if improvement
        if cv_score.mean() >= self.current_score - 0.02:
            self.model = new_model
            self.model_version = datetime.now().strftime("%Y%m")
            self.cache.clear()  # Invalidate stale predictions
            return {"status": "updated", "score": cv_score.mean()}

        return {"status": "kept_existing"}

# Scheduler (Railway cron)
# Run on 1st of each month at 3am
@scheduler.scheduled_job('cron', day=1, hour=3)
async def scheduled_retrain():
    classifier = get_classifier_instance()
    result = await classifier.monthly_retrain()
    log.info(f"Monthly retrain: {result}")
```

---

## Data Quality Monitoring

### Quality Metrics

```python
@dataclass
class DataQualityMetrics:
    total_records: int
    complete_records: int  # All required fields filled
    duplicate_rate: float
    stale_records: int     # Not updated in 6+ months
    confidence_distribution: dict  # {confirmed: N, likely: N, inferred: N}

async def compute_quality_metrics(entity_type: str) -> DataQualityMetrics:
    """Compute data quality metrics for an entity type."""
    # Implementation...
```

### Quality Dashboard

| Metric | Target | Alert Threshold |
|--------|--------|-----------------|
| Completeness (required fields) | > 80% | < 60% |
| Duplicate rate | < 5% | > 10% |
| Staleness (6+ months) | < 20% | > 40% |
| Confirmed confidence | > 50% | < 30% |

---

## Dependencies

```toml
[project.dependencies]
# Entity Resolution
scikit-learn = ">=1.4.0"
rapidfuzz = ">=3.0.0"
metaphone = ">=0.6"
networkx = ">=3.2"

# Embeddings
voyageai = ">=0.2.0"

# Data processing
pandas = ">=2.0.0"
```

---

## Related Documents

- [M1b: IR Core](../milestones/m1b-ir-core.md) - IR team integration features
- [M9: IR Advanced](../milestones/m9-ir-events.md) - Events and advanced IR
- [Architecture](architecture.md) - Database schema
- [Agents](agents.md) - LLM tiebreaker integration
