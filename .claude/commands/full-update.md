---
description: Full documentation update cycle - orchestrates audit/fix loop then PDF/push
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TodoWrite, Task, mcp__puppeteer__puppeteer_navigate, mcp__puppeteer__puppeteer_screenshot, mcp__puppeteer__puppeteer_click, mcp__puppeteer__puppeteer_evaluate
---

# Full Documentation Update

Orchestrates the complete update workflow using the individual commands.

```
┌──────────────────────────────────────────────────────────┐
│                     PHASE 1: LOOP                        │
│   ┌─────────┐      ┌─────────────────────┐              │
│   │ /audit  │─────▶│ /sync-schema and/or │              │
│   └────┬────┘      │ /fix-links          │              │
│        │           └──────────┬──────────┘              │
│        └──────────────────────┘                         │
│                    ▲          │                         │
│                    │          ▼                         │
│                    │   ┌──────────────┐                 │
│                    └───│ User reviews │                 │
│         "more issues"  └──────┬───────┘                 │
│                               │                         │
│                         "approved"                      │
├───────────────────────────────┼─────────────────────────┤
│                     PHASE 2: FINALIZE                   │
│                               ▼                         │
│                        ┌────────────┐                   │
│                        │ /regen-pdf │                   │
│                        └─────┬──────┘                   │
│                              ▼                          │
│                        ┌────────────┐                   │
│                        │   /push    │                   │
│                        └────────────┘                   │
└──────────────────────────────────────────────────────────┘
```

---

## PHASE 1: Audit & Fix Loop

### Step 1: Run /audit

Execute the audit command (see `.claude/commands/audit.md`):
- Load manifest from `.claude/docs-manifest.json`
- Check schema consistency
- Check mockup files and navigation
- Check feature IDs and test coverage
- Generate audit report

### Step 2: Present Findings

Show the audit report and ask:

```
## Audit Complete

[audit report here]

What would you like to do?

1. "fix schema" → Run /sync-schema
2. "fix links" → Run /fix-links
3. "fix all" → Run both
4. "approved" → Move to Phase 2
5. "stop" → End here
```

**WAIT for user response.**

### Step 3: Apply Fixes

Based on user response:

| User Says | Action |
|-----------|--------|
| "fix schema" | Execute `/sync-schema` command logic |
| "fix links" | Execute `/fix-links` command logic |
| "fix all" | Execute both in sequence |
| "approved" | → Go to Phase 2 |
| "stop" | → End command |

After fixes: **Loop back to Step 1** (re-run /audit)

---

## PHASE 2: Finalize (after "approved")

### Step 4: Run /regen-pdf

Execute the regen-pdf command (see `.claude/commands/regen-pdf.md`):
- Check/create virtualenv
- Run `python docs/product-doc/build_pdf.py`
- Verify PDF was created

### Step 5: Run /push

Execute the push command (see `.claude/commands/push.md`):
- Show git status and diff
- Ask for approval
- Commit with descriptive message
- Push to origin/main

---

## Command References

This command orchestrates:

| Command | File | Purpose |
|---------|------|---------|
| `/audit` | `audit.md` | Read-only scan for issues |
| `/sync-schema` | `sync-schema.md` | Fix PRD ↔ migrations |
| `/fix-links` | `fix-links.md` | Fix mockup navigation |
| `/regen-pdf` | `regen-pdf.md` | Regenerate PDF |
| `/push` | `push.md` | Commit and push |

---

## Quick Reference

| User Says | Result |
|-----------|--------|
| "fix schema" | Run sync-schema, then re-audit |
| "fix links" | Run fix-links, then re-audit |
| "fix all" | Run both, then re-audit |
| "approved" | Stop loop, proceed to PDF + push |
| "stop" | End immediately, no changes |
