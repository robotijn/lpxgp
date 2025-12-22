---
description: Review changes, commit, and push to GitHub
allowed-tools: Bash, Read
---

# Push Changes

Review all pending changes, create a descriptive commit, and push.

## Step 1: Review Status

```bash
git status
git diff --stat
```

List all modified files with brief descriptions of what changed.

## Step 2: Categorize Changes

Group changes by type:

```markdown
## Changes Summary

### Documentation
- docs/prd/PRD-v1.md: [what changed]
- docs/milestones.md: [what changed]

### Schema/Migrations
- supabase/migrations/XXX.sql: [what changed]

### Mockups
- docs/mockups/file.html: [what changed]

### Generated Files
- docs/LPxGP-Product-Document.pdf: Regenerated

### Other
- .claude/commands/X.md: [what changed]
```

## Step 3: Confirm with User

Show the summary and ask:
- "Ready to commit these changes?"
- "Any files to exclude?"

**STOP and wait for approval.**

## Step 4: Stage and Commit (After Approval)

```bash
git add -A
git status
```

Create commit message following project conventions:
- First line: summary (50 chars max)
- Blank line
- Bullet points for details
- Footer with Claude Code attribution

Example:
```
git commit -m "$(cat <<'EOF'
Sync documentation after data model changes

- PRD Section 6: Updated table references
- Migrations: Fixed RLS policy references
- Test specs: Replaced deprecated table names
- Mockups: Fixed 3 broken navigation links
- PDF: Regenerated with updated screenshots

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude Opus 4.5 <noreply@anthropic.com>
EOF
)"
```

## Step 5: Push

```bash
git push origin main
```

## Step 6: Verify Deployment

After push:
- GitHub Pages will update in 1-2 minutes
- Mockups visible at: https://robotijn.github.io/lpxgp/mockups/

```bash
# Check push succeeded
git log --oneline -1
git status
```

## Step 7: Report

```markdown
## Push Complete

### Commit
- Hash: [hash]
- Message: [first line]
- Files: X files changed

### Deployments
- GitHub Pages: https://robotijn.github.io/lpxgp/mockups/
  (updates in ~2 minutes)

### Verification
- [ ] Check mockups at GitHub Pages URL
- [ ] Download PDF from repo if needed
```
