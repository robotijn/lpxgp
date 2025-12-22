---
description: Audit documentation for inconsistencies (read-only, no changes)
allowed-tools: Read, Glob, Grep, Bash
---

# Documentation Audit

Perform a read-only audit of all documentation. Report issues but make NO changes.

## Step 1: Load Manifest

Read `.claude/docs-manifest.json` to get the list of expected files and tables.

## Step 2: Run Checks

### Check A: Schema Consistency

**Goal:** Verify PRD Section 6 matches migration files.

1. Read `docs/prd/PRD-v1.md` lines 1350-2800 (Section 6)
2. Read all files in `supabase/migrations/`
3. Check:
   - [ ] Every table in manifest `schema.tables` exists in BOTH PRD and migrations
   - [ ] No references to `schema.deprecated_tables` exist anywhere
   - [ ] Foreign key references point to valid tables

**Search patterns for deprecated tables:**
```
grep -r "lp_commitments\|lp_contacts\|lp_fund_matches" --include="*.md" --include="*.sql" docs/ supabase/
grep -rE "REFERENCES matches\(|matches\.id|FROM matches" --include="*.md" --include="*.sql" docs/ supabase/
```

### Check B: Mockup Files Exist

**Goal:** Verify all expected mockups exist.

1. List files in `docs/mockups/`
2. Compare against `mockups.screens` in manifest
3. Report missing or extra files

### Check C: Mockup Navigation

**Goal:** Verify navigation links work.

For each HTML file in `docs/mockups/`:
1. Extract all `href="*.html"` links
2. Verify target file exists
3. Check nav items match `mockups.navigation` structure

**Search pattern:**
```bash
grep -oh 'href="[^"]*\.html"' docs/mockups/*.html | sort | uniq -c
```

### Check D: Feature ID Completeness

**Goal:** Verify all feature IDs are documented.

1. Search PRD for each ID in `manifest.feature_ids`
2. Report any missing feature IDs
3. Check test specs reference the same IDs

### Check E: Test Spec Table References

**Goal:** Verify tests use correct table names.

```bash
grep -rE "organizations|fund_lp_matches|fund_lp_status|investments" docs/prd/tests/
grep -rE "matches\b|lp_commitments|lp_fund_matches" docs/prd/tests/  # Should find nothing
```

### Check F: CLAUDE.md Currency

**Goal:** Verify CLAUDE.md reflects current state.

Compare:
- Tech stack in CLAUDE.md vs PRD Section 8
- Milestone status vs docs/milestones.md
- Project structure vs actual file tree

## Step 3: Generate Report

Output a structured report:

```markdown
# Audit Report - [DATE]

## Summary
- Total checks: X
- Passed: X
- Failed: X
- Warnings: X

## Critical Issues (blocks development)
| Issue | Location | Details |
|-------|----------|---------|
| ... | ... | ... |

## Inconsistencies (should fix)
| Check | Location 1 | Location 2 | Discrepancy |
|-------|------------|------------|-------------|
| ... | ... | ... | ... |

## Warnings (minor)
- ...

## Recommendations
1. Run `/sync-schema` to fix: [list issues]
2. Run `/fix-links` to fix: [list issues]
3. Run `/regen-pdf` after fixes

## Files Checked
- [x] File 1
- [x] File 2
...
```

## Important

- This command is READ-ONLY
- Do NOT edit any files
- Do NOT use Write or Edit tools
- Only report findings
