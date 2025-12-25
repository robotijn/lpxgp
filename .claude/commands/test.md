---
description: Run pytest and summarize results (project)
allowed-tools: Bash, Read, Grep
---

# Pytest Runner

Run all pytest tests in verbose mode with detailed output.

## CRITICAL: Report Everything

**ALWAYS tell the user the details of:**
1. **All test failures** - full error messages, stack traces, what went wrong
2. **All warnings** - source, message, and recommended fix

Never summarize away important information. The user needs to see exactly what's happening.

## Warnings Are Errors

Treat warnings as seriously as errors:
- Warnings indicate real problems that will become errors later
- Do not dismiss warnings as "just third-party issues"
- If warnings come from dependencies, recommend updating or switching versions

## Step 1: Run Tests

Execute pytest with full verbosity:

```bash
uv run pytest -v --tb=long -x --strict-markers 2>&1
```

Options used:
- `-v` : Verbose - show each test name as it runs
- `--tb=long` : Full tracebacks on failures
- `-x` : Stop on first failure (faster feedback)
- `--strict-markers` : Error on unknown markers

## Step 2: Report Results (ALWAYS INCLUDE DETAILS)

### Summary
```
✅ Passed: X
❌ Failed: X
⏭️ Skipped: X
⚠️ Warnings: X
📊 Total: X tests
```

### For Each Failure (ALWAYS SHOW)
1. **Test name and location** (file:line)
2. **Full error message** - copy the actual assertion/exception
3. **What it tested** (describe the scenario)
4. **Why it failed** (your analysis)
5. **Suggested fix** (specific code change)

### For Each Warning (ALWAYS SHOW)
1. **Source** (which library/module)
2. **Full warning message** - copy it exactly
3. **Impact** (what could break)
4. **Recommended fix** (update library, change Python version, etc.)

## Step 3: Coverage Check (Optional)

If user asks for coverage:
```bash
uv run pytest --cov=src --cov-report=term-missing -v
```

## Step 4: Run Specific Tests

User can specify:
- `$ARGUMENTS` - passed directly to pytest (e.g., "test_main.py", "-k match", "--lf")

```bash
uv run pytest -v --tb=long $ARGUMENTS
```

## Common Test Patterns

| Command | Purpose |
|---------|---------|
| `/test` | Run all tests |
| `/test -k health` | Run tests matching "health" |
| `/test --lf` | Re-run last failed tests |
| `/test tests/test_main.py` | Run specific file |
| `/test -x` | Stop on first failure |

## Troubleshooting

| Issue | Solution |
|-------|----------|
| Import errors | Run `uv sync` first |
| Supabase errors | Check if `npx supabase start` is running |
| Fixture not found | Check conftest.py for missing fixtures |
| Third-party warnings | Update the library or switch Python version |
| Deprecation warnings | Check library changelog for migration guide |
