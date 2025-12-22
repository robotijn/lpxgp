---
description: Sync data model between PRD and migrations
allowed-tools: Read, Write, Edit, Grep, Bash, TodoWrite
---

# Sync Schema

Synchronize data model between PRD Section 6 and Supabase migrations.

## Prerequisites

Run `/audit` first to identify schema issues.

## Step 1: Identify Scope

Read `.claude/docs-manifest.json` for:
- `schema.tables` - expected tables
- `schema.deprecated_tables` - tables that should NOT exist

## Step 2: Analyze Current State

1. Read PRD Section 6 (`docs/prd/PRD-v1.md` lines 1350-2800)
2. Read all migration files in `supabase/migrations/`
3. Create a comparison table:

| Table | In PRD | In Migrations | In RLS | Status |
|-------|--------|---------------|--------|--------|
| organizations | ✓ | ✓ | ✓ | OK |
| ... | ... | ... | ... | ... |

## Step 3: Plan Changes

Before making ANY changes, list:

```markdown
## Planned Changes

### PRD Updates
- [ ] Section 6.X: [description]

### Migration Updates
- [ ] 00X_file.sql: [description]

### Test Spec Updates
- [ ] [file]: Replace `old_table` with `new_table`

### No Changes Needed
- [file]: Already consistent
```

**STOP and ask for approval before proceeding.**

## Step 4: Apply Changes (After Approval)

Use TodoWrite to track progress.

Order of operations:
1. Update PRD first (source of truth)
2. Update migrations to match PRD
3. Update RLS policies
4. Search-and-replace deprecated names in test specs

For each deprecated table reference found:
```bash
grep -rn "deprecated_table_name" docs/ supabase/ --include="*.md" --include="*.sql"
```

Replace with correct table name.

## Step 5: Verify

After changes:
```bash
# Check no deprecated references remain
grep -rE "matches\b|lp_commitments|lp_fund_matches|lp_contacts" docs/ supabase/ --include="*.md" --include="*.sql"
```

Should return empty.

## Step 6: Report

```markdown
## Schema Sync Complete

### Files Modified
- docs/prd/PRD-v1.md: [X changes]
- supabase/migrations/00X.sql: [X changes]
- docs/prd/tests/[file].md: [X changes]

### Deprecated References Removed
- `matches` → `fund_lp_matches`: X occurrences
- `lp_commitments` → `investments`: X occurrences

### Next Steps
- Run `/regen-pdf` to update PDF
- Run `git status` to review changes
```

Do NOT commit. User will use `/push` when ready.
