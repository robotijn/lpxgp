---
description: Full documentation sync workflow (orchestrates audit → fix → push)
allowed-tools: Read, Bash
---

# Documentation Sync (Orchestrator)

This command guides you through the full documentation sync workflow.

## Overview

The sync process has 4 phases:

```
┌─────────────────────────────────────────────────────────────┐
│  /audit          →  /sync-schema  →  /fix-links  →  /push  │
│  (read-only)        (if needed)      (if needed)    (final)│
│                          ↓               ↓                  │
│                    /regen-pdf ←──────────┘                  │
└─────────────────────────────────────────────────────────────┘
```

## Quick Start

Choose your workflow:

### Option A: Full Sync
```
1. /audit           # Find all issues
2. /sync-schema     # Fix schema issues (if any)
3. /fix-links       # Fix mockup links (if any)
4. /regen-pdf       # Regenerate PDF
5. /push            # Commit and push
```

### Option B: Just Audit (no changes)
```
1. /audit           # See what needs fixing
```

### Option C: Just Regenerate PDF
```
1. /regen-pdf       # Regenerate PDF only
2. /push            # Commit and push
```

### Option D: Just Fix Links
```
1. /fix-links       # Fix mockup navigation
2. /regen-pdf       # Regenerate PDF with fixes
3. /push            # Commit and push
```

## Which Command to Use?

| Situation | Command |
|-----------|---------|
| "What's broken?" | `/audit` |
| "PRD and migrations don't match" | `/sync-schema` |
| "Mockup links are broken" | `/fix-links` |
| "Just need fresh PDF" | `/regen-pdf` |
| "Ready to commit" | `/push` |
| "Do everything" | Follow Option A above |

## Manifest

All expected files are listed in `.claude/docs-manifest.json`.

Update the manifest when:
- Adding new mockup screens
- Adding new tables
- Adding new test spec files
- Deprecating old tables

## Tips

1. **Always audit first** - Know what's broken before fixing
2. **Fix in order** - Schema → Links → PDF
3. **Review before push** - Check git diff
4. **PDF takes time** - 2-4 minutes for full regeneration

## Current State

To see current state without running audit:

```bash
# Git status
git status --short

# Recent changes
git log --oneline -5

# Count mockups
ls docs/mockups/*.html | wc -l

# Check PDF age
ls -la docs/LPxGP-Product-Document.pdf
```
