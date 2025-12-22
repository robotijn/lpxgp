# LP Database

[← Back to Features Index](index.md)

---

## F-LP-01: LP Profile Storage [P0]

**Description:** Store comprehensive LP profiles

**Requirements:**
- All fields from LP data model (see [Data Model](../data-model.md))
- Support for multiple contacts per LP
- Historical commitment data
- Notes and custom fields
- Data quality score per record

**Test Cases:** See TEST-LP-01 in Testing Strategy

---

## F-LP-02: LP Search & Filter [P0]

**Description:** Find LPs by criteria

**Requirements:**
- Filter by: type, AUM, strategies, geography, ticket size
- Full-text search on text fields
- Save search as preset
- Export search results (CSV)
- Pagination with 50 results per page

**Test Cases:** See TEST-LP-02 in Testing Strategy

---

## F-LP-03: Semantic Search [P0]

**Description:** Search LPs by meaning, not just keywords

**Requirements:**
- Vector embeddings via Voyage AI for LP mandates/descriptions
- Natural language queries: "LPs interested in climate tech in Europe"
- Similarity scoring (0-100)
- Combine with traditional filters
- Response time < 500ms

**Test Cases:** See TEST-LP-03 in Testing Strategy

---

## F-LP-04: LP Data Import [P0]

**Description:** Bulk import LP data from files

**Requirements:**
- Accept CSV, Excel formats
- Field mapping interface (drag-drop or select)
- Validation and error reporting
- Duplicate detection (by name + location)
- Preview before commit
- Batch size up to 10,000 records

**Test Cases:** See TEST-LP-04 in Testing Strategy

---

## F-LP-05: LP Data Cleaning Pipeline [P0]

**Description:** Standardize and normalize imported data

**Requirements:**
- Normalize strategy names to taxonomy
- Standardize geography names to ISO codes
- Parse and validate contact information
- Detect and merge duplicates
- Flag data quality issues
- Manual review queue for low-confidence records
- AI-assisted field extraction from messy data

**Test Cases:** See TEST-LP-05 in Testing Strategy

---

## F-LP-06: LP Data Enrichment [P1]

**Description:** Enhance LP data using external sources

**Requirements:**
- Future API integrations (Preqin, PitchBook) for institutional data
- Bulk update support from external data providers
- Human review for enriched data before committing
- Confidence scoring for enriched fields
- Design for extensibility to new data sources

**Test Cases:** See TEST-LP-06 in Testing Strategy

---

[Next: Matching Engine →](matching.md)
