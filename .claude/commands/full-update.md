---
description: Full documentation update cycle - orchestrates audit/fix loop then PDF/push
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TodoWrite, Task, mcp__puppeteer__puppeteer_navigate, mcp__puppeteer__puppeteer_screenshot, mcp__puppeteer__puppeteer_click, mcp__puppeteer__puppeteer_evaluate
---

# Full Documentation Update

Orchestrates the complete update workflow using **parallel subagents** for speed.

```
┌─────────────────────────────────────────────────────────────────┐
│                     PHASE 1: PARALLEL AUDIT                      │
│                                                                  │
│  Launch 3 subagents simultaneously:                              │
│  ┌──────────────┐  ┌──────────────┐  ┌──────────────┐          │
│  │ Agent 1      │  │ Agent 2      │  │ Agent 3      │          │
│  │ Schema       │  │ BDD/Tests    │  │ UIX/Mockups  │          │
│  └──────────────┘  └──────────────┘  └──────────────┘          │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                     PHASE 2: FIX LOOP                            │
│                                                                  │
│        Report Issues → User Reviews → Apply Fixes                │
│                     ↑               ↓                            │
│                     └───────────────┘                            │
│                                                                  │
├──────────────────────────────────────────────────────────────────┤
│                     PHASE 3: FINALIZE                            │
│                                                                  │
│              /regen-pdf  →  /push                                │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## PHASE 1: Parallel Deep Audit

### Step 1: Launch 3 Subagents in Parallel

**Use Task tool to launch all 3 agents simultaneously in a single message:**

```python
# Agent 1: Schema & Query Safety
Task(
    description="Audit schema and queries",
    subagent_type="Explore",
    prompt="""
    CHECK A - Schema Consistency:
    - Read .claude/docs-manifest.json
    - Verify schema.tables exist in migrations
    - Check no deprecated tables referenced

    CHECK K - API Documentation:
    - List routes in src/main.py
    - Count undocumented endpoints

    CHECK L - Query Safety:
    - Find SQL queries, verify parameterized
    """
)

# Agent 2: BDD & Test Coverage
Task(
    description="Audit BDD and tests",
    subagent_type="Explore",
    prompt="""
    CHECK E - BDD Coverage:
    - List .feature.md files
    - Count scenarios vs test functions

    CHECK G - Test Coverage:
    - Count unit/e2e/bdd/security tests

    CHECK H - Security Coverage:
    - Check auth/authz tests
    - Check OWASP coverage
    """
)

# Agent 3: UIX & Mockups
Task(
    description="Audit UIX consistency",
    subagent_type="Explore",
    prompt="""
    CHECK B - Mockup Files:
    - Verify all expected files exist

    CHECK C - Navigation:
    - Check mockup links work

    CHECK F - UIX Consistency:
    - Match routes to templates
    - Verify HTMX endpoints exist
    """
)
```

### Step 2: Run Sequential Checks

While waiting for agents, run:
- Linting: `uv run ruff check src/ tests/`
- Tests: `uv run pytest --tb=no -q`

### Step 3: Merge Results

Combine all agent results into unified report.

---

## PHASE 2: Fix Loop

### Present Audit Report

```
## Deep Audit Complete (Parallel Execution)

[Merged report from all agents]

What would you like to do?

1. "fix schema" → Run /sync-schema
2. "fix links" → Run /fix-links
3. "fix tests" → Show test gap guidance
4. "fix code" → Run ruff --fix
5. "fix all" → Run all automated fixes
6. "approved" → Move to Phase 3
7. "stop" → End here
```

**WAIT for user response.**

### Apply Fixes

| User Says | Action |
|-----------|--------|
| "fix schema" | Execute `/sync-schema` |
| "fix links" | Execute `/fix-links` |
| "fix tests" | Show specific gaps |
| "fix code" | Run `uv run ruff check --fix` |
| "fix all" | Execute all in sequence |
| "approved" | → Go to Phase 3 |
| "stop" | → End command |

After fixes: **Re-run parallel audit** to verify.

---

## PHASE 3: Finalize

### Step 4: Run /regen-pdf

```bash
source /tmp/pdf-env/bin/activate && python docs/product-doc/build_pdf.py
```

### Step 5: Run /push

- Show git status
- Ask for approval
- Commit and push

---

## Performance Benefits

**Sequential execution:** ~5-10 minutes
**Parallel with subagents:** ~2-3 minutes

Speedup: **2-3x faster**

---

## Commands Used

| Command | Purpose |
|---------|---------|
| `/audit` | Parallel deep scan (3 agents) |
| `/sync-schema` | Fix PRD ↔ migrations |
| `/fix-links` | Fix mockup navigation |
| `/regen-pdf` | Regenerate PDF |
| `/push` | Commit and push |

---

## Quick Reference

| User Says | Result |
|-----------|--------|
| "fix schema" | Run sync-schema, re-audit |
| "fix links" | Run fix-links, re-audit |
| "fix tests" | Show test gaps |
| "fix code" | Run ruff --fix, re-audit |
| "fix all" | Run all fixes, re-audit |
| "approved" | Proceed to PDF + push |
| "stop" | End immediately |

---

## Exit Criteria

Before "approved":
- [ ] All critical issues resolved
- [ ] Linting passes
- [ ] Tests pass (or failures understood)
- [ ] No security warnings
