---
description: Fix navigation links in mockup HTML files
allowed-tools: Read, Write, Edit, Glob, Grep, Bash, TodoWrite, mcp__puppeteer__puppeteer_navigate, mcp__puppeteer__puppeteer_screenshot, mcp__puppeteer__puppeteer_click
---

# Fix Mockup Links

Fix navigation and internal links in mockup HTML files.

## Step 1: Load Navigation Map

Read `.claude/docs-manifest.json` and extract:
- `mockups.screens` - all expected screens by category
- `mockups.navigation` - expected nav structures

## Step 2: Analyze Current Links

For each HTML file in `docs/mockups/`:

```bash
# Extract all internal links
grep -oh 'href="[^"]*\.html"' docs/mockups/*.html | sort | uniq -c | sort -rn
```

Create a link inventory:
| Source File | Target Link | Target Exists | Category |
|-------------|-------------|---------------|----------|
| dashboard.html | fund-list.html | ✓ | nav |
| dashboard.html | settings.html | ✗ | broken |

## Step 3: Identify Issues

Check for:
1. **Broken links** - target file doesn't exist
2. **Orphan pages** - no links point TO this page
3. **Inconsistent nav** - nav items don't match manifest
4. **Dead-end pages** - page has no outbound links (except index)

## Step 4: Plan Fixes

```markdown
## Link Fixes Needed

### Broken Links (must fix)
| File | Bad Link | Should Be |
|------|----------|-----------|
| settings-profile.html | settings.html | settings-company.html |

### Missing Nav Items
| File | Missing Item |
|------|--------------|
| admin-users.html | Link to admin-escalations.html |

### Orphan Pages (no incoming links)
- loading-matches.html (OK - UI state)
- error-api.html (OK - UI state)

### Dead-End Pages (need back/nav links)
- None found
```

**STOP and ask for approval before proceeding.**

## Step 5: Apply Fixes (After Approval)

Use TodoWrite to track each file.

For each file needing fixes:
1. Read the file
2. Identify the exact line with the broken/missing link
3. Use Edit to fix
4. Verify the fix

Example fix:
```
# Bad:  href="settings.html"
# Good: href="settings-company.html"
```

## Step 6: Verify with Puppeteer

After fixes, test navigation:

1. Navigate to index.html
2. Click through main nav items
3. Take screenshots to verify pages load
4. Check that clicking works

```javascript
// Test each nav link
const navLinks = ['dashboard.html', 'fund-list.html', 'lp-search.html', 'matches.html'];
for (const link of navLinks) {
  // Navigate and screenshot
}
```

## Step 7: Report

```markdown
## Link Fixes Complete

### Fixed
- X broken links
- X missing nav items
- X dead-end pages

### Files Modified
- dashboard.html: Fixed 2 links
- settings-profile.html: Added nav back link

### Verified Working
- Main nav: ✓
- Settings sub-nav: ✓
- Admin nav: ✓

### Screenshots Taken
- [list if applicable]
```

Do NOT commit. User will use `/push` when ready.
