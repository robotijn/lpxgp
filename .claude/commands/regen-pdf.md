---
description: Regenerate the PDF product document
allowed-tools: Read, Bash, mcp__puppeteer__puppeteer_navigate, mcp__puppeteer__puppeteer_screenshot
---

# Regenerate PDF

Regenerate `docs/LPxGP-Product-Document.pdf` from mockups and PRD content.

## Prerequisites

- All mockup HTML files should be current
- PRD content should be current
- Run `/audit` and fix issues first

## Step 1: Check Environment

```bash
# Check if virtualenv exists
ls -la /tmp/pdf-env/bin/activate
```

If missing, create it:
```bash
python3 -m venv /tmp/pdf-env
source /tmp/pdf-env/bin/activate
pip install playwright weasyprint jinja2
playwright install chromium
```

## Step 2: Verify Mockups

Quick check that mockups render:
```bash
# Count mockup files
ls docs/mockups/*.html | wc -l
# Should be ~31 files
```

## Step 3: Run PDF Builder

```bash
source /tmp/pdf-env/bin/activate && python docs/product-doc/build_pdf.py
```

This will:
1. Start a local server for mockups
2. Take screenshots of all screens (~30)
3. Generate PDF with WeasyPrint
4. Save to `docs/LPxGP-Product-Document.pdf`

**Expected duration: 2-4 minutes**

## Step 4: Verify Output

```bash
# Check PDF was created
ls -la docs/LPxGP-Product-Document.pdf

# Check file size (should be 2-4 MB)
du -h docs/LPxGP-Product-Document.pdf

# Check page count (should be ~50+ pages)
pdfinfo docs/LPxGP-Product-Document.pdf 2>/dev/null | grep Pages || echo "pdfinfo not installed"
```

## Step 5: Report

```markdown
## PDF Regeneration Complete

- File: docs/LPxGP-Product-Document.pdf
- Size: X.X MB
- Pages: ~XX
- Screenshots: XX screens captured

### Build Log
[any warnings or errors]

### Next Steps
- Review PDF manually if needed
- Run `/push` to commit and push
```

## Troubleshooting

**Playwright fails:**
```bash
playwright install chromium --with-deps
```

**WeasyPrint fails:**
```bash
# On Ubuntu/Debian
sudo apt-get install libpango-1.0-0 libpangocairo-1.0-0 libgdk-pixbuf2.0-0
```

**Timeout on screenshots:**
- Check if mockups have errors (missing Tailwind, etc.)
- Try running with verbose mode if supported
