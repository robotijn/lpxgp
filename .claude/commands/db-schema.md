---
description: Validate database schema against PRD data model
allowed-tools: Read, Grep, Glob
---

Validate the database schema for: $ARGUMENTS (table name or "all")

## Validation Steps

1. **Read PRD Data Model**
   - Check `docs/prd/PRD-v1.md` for entity definitions
   - Compare with `supabase/migrations/` files

2. **Schema Consistency**
   - All PRD entities have corresponding tables
   - Column types match PRD specifications
   - Foreign keys are properly defined
   - Indexes exist for query patterns

3. **RLS Policies**
   - Row-Level Security enabled on all tables
   - Policies match multi-tenancy requirements
   - GP can only see their own data
   - Admin has appropriate access

4. **Vector Support**
   - pgvector extension enabled
   - Embedding columns are `vector(1536)` for Voyage AI
   - Similarity search indexes (ivfflat or hnsw)

## Output Format

```
## Schema Validation: [table_name]

### PRD Alignment
- [x] Table exists
- [x] Columns match PRD
- [ ] Missing: column_name (type)

### Security
- [x] RLS enabled
- [x] Policies defined

### Indexes
- [x] Primary key
- [x] Foreign keys
- [ ] Missing index on frequently queried column

### Issues
1. [Issue description and fix]

### Recommendations
- [Suggested improvements]
```

If "all" specified, generate summary for all tables.
