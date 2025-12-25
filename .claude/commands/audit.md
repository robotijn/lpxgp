---
description: Audit documentation for inconsistencies (read-only, no changes)
allowed-tools: Read, Glob, Grep, Bash, Task
---

# Deep Documentation Audit

Perform a comprehensive read-only audit of ALL project artifacts using **parallel subagents** for speed.

## Execution Strategy

**Use Task tool with subagent_type="Explore" to run checks in parallel:**

```
┌─────────────────────────────────────────────────────────────────┐
│                    PARALLEL AUDIT EXECUTION                      │
│                                                                  │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Agent 1      │  │ Agent 2      │  │ Agent 3      │          │
│  │ Schema +     │  │ BDD + Test   │  │ UIX +        │          │
│  │ Query Safety │  │ Coverage     │  │ Mockups      │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│         │                │                 │                    │
│         └────────────────┼─────────────────┘                    │
│                          ▼                                      │
│                 ┌──────────────────┐                           │
│                 │ Merge Results    │                           │
│                 │ + Run Linting    │                           │
│                 └──────────────────┘                           │
└─────────────────────────────────────────────────────────────────┘
```

---

## Step 1: Load Manifest

Read `.claude/docs-manifest.json` to get the list of expected files and tables.

---

## Step 2: Launch Parallel Subagents

**Launch 3 subagents simultaneously using the Task tool:**

### Agent 1: Schema & Query Safety (Checks A, K, L)

```
Task: "Audit schema consistency and query safety"
subagent_type: "Explore"
prompt: |
  Perform read-only audit of schema consistency:

  CHECK A - Schema Consistency:
  1. Read manifest from .claude/docs-manifest.json
  2. Check schema.tables exist in supabase/migrations/
  3. Check no schema.deprecated_tables are referenced in code
  4. Grep for: lp_commitments, lp_contacts, lp_fund_matches in *.py, *.sql, *.md

  CHECK K - API Documentation:
  1. List all @app.(get|post|put|delete) routes in src/main.py
  2. Count routes with docstrings
  3. Report undocumented endpoints

  CHECK L - Query Safety:
  1. Search for SQL queries in src/
  2. Flag any string concatenation or f-strings in SQL
  3. Verify parameterized queries use %s placeholders

  Return a structured report of findings.
```

### Agent 2: BDD & Test Coverage (Checks E, G, H)

```
Task: "Audit BDD and test coverage"
subagent_type: "Explore"
prompt: |
  Perform read-only audit of test coverage:

  CHECK E - BDD Test Coverage:
  1. List all .feature.md files in docs/prd/tests/
  2. Count scenarios in each file
  3. Match to test functions in tests/

  CHECK G - Test File Coverage:
  1. Count test functions (def test_) in tests/
  2. Count by category: unit, e2e, bdd, security
  3. Check for parametrized tests

  CHECK H - Security Test Coverage:
  1. Search for: sql_injection, xss, unauthorized, 401, 403 in tests/
  2. Check auth/authz test coverage
  3. Report OWASP coverage gaps

  Return counts and coverage report.
```

### Agent 3: UIX & Mockups (Checks B, C, F)

```
Task: "Audit UIX consistency and mockups"
subagent_type: "Explore"
prompt: |
  Perform read-only audit of UIX consistency:

  CHECK B - Mockup Files:
  1. List all .html files in docs/mockups/
  2. Compare to mockups.screens in manifest
  3. Report missing or extra files

  CHECK C - Mockup Navigation:
  1. Extract href="*.html" from mockup files
  2. Verify each target file exists
  3. Report broken links

  CHECK F - UIX Consistency:
  1. List routes in src/main.py
  2. List templates in src/templates/pages/
  3. Check route-template mapping
  4. Extract HTMX endpoints from templates
  5. Verify each has matching route

  Return consistency report.
```

---

## Step 3: Sequential Checks (After Agents Complete)

Run these after merging agent results:

### Check D: Feature ID Completeness

```bash
# Check all feature IDs from manifest are in PRD
for id in F-AA F-AGENT F-AUTH F-BATCH F-BB F-DEBATE F-ER F-GP F-HITL F-IR F-LP F-MATCH F-OBSERVE F-PITCH F-PROMPT F-RI F-UI; do
  grep -r "$id" docs/prd/ > /dev/null || echo "Missing: $id"
done
```

### Check I: Code Quality

```bash
# Run linting
uv run ruff check src/ tests/ --statistics

# Type checking (optional)
uv run mypy src/ --ignore-missing-imports 2>&1 | head -30
```

### Check J: CLAUDE.md Currency

Compare:
- Tech stack in CLAUDE.md vs actual dependencies
- Project structure vs file tree
- Commands listed vs .claude/commands/

---

## Step 4: Run Tests

```bash
# Quick test summary
uv run pytest --tb=no -q 2>&1 | tail -15
```

---

## Step 5: Generate Comprehensive Report

Merge results from all agents:

```markdown
# Deep Audit Report - [DATE]

## Executive Summary
- Total checks: 12
- Passed: X
- Failed: X
- Warnings: X
- Tests: X passed, X failed

## Parallel Agent Results

### Agent 1: Schema & Query Safety
[Results from Agent 1]

### Agent 2: BDD & Test Coverage
[Results from Agent 2]

### Agent 3: UIX & Mockups
[Results from Agent 3]

## Sequential Check Results

### Feature IDs
[Check D results]

### Code Quality
[Check I results]

### CLAUDE.md Currency
[Check J results]

## Critical Issues (P0)
| Issue | Location | Details |
|-------|----------|---------|

## Inconsistencies (P1)
| Check | Location | Discrepancy |
|-------|----------|-------------|

## Warnings (P2)
- ...

## Test Results
- Total: X
- Passed: X
- Failed: X
- Errors: X

## Recommendations
1. HIGH: ...
2. MEDIUM: ...
3. LOW: ...
```

---

## Important

- This command is READ-ONLY
- Do NOT edit any files
- Only report findings
- Use subagents for parallel execution
- Merge results before presenting to user
