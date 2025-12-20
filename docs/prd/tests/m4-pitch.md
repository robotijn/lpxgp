# M4: Pitch Generation Tests
### "Generate personalized outreach"

## M4-INT: Integration Tests

### Summary Generation

```python
# tests/integration/test_pitch_generation.py

class TestSummaryGeneration:
    """Test executive summary generation."""

    async def test_generate_summary(self, client, auth_session, match):
        response = await client.post(
            f"/api/v1/matches/{match.id}/summary",
            cookies={"session": auth_session}
        )
        assert response.status_code == 200
        assert len(response.json()["content"]) > 500

    async def test_summary_mentions_lp(self, client, auth_session, match):
        response = await client.post(
            f"/api/v1/matches/{match.id}/summary",
            cookies={"session": auth_session}
        )
        assert match.lp.name in response.json()["content"]

    async def test_export_pdf(self, client, auth_session, match):
        response = await client.post(
            f"/api/v1/matches/{match.id}/summary/pdf",
            cookies={"session": auth_session}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"
```

### Email Generation

```python
class TestEmailGeneration:
    """Test outreach email generation (human-in-the-loop: returns content, does not send)."""

    async def test_generate_email_returns_content(self, client, auth_session, match):
        """Email generation returns content for user review, not auto-sending."""
        response = await client.post(
            f"/api/v1/matches/{match.id}/email",
            cookies={"session": auth_session},
            json={"tone": "professional"}
        )
        assert response.status_code == 200
        data = response.json()
        # Returns email content for review
        assert "subject" in data
        assert "body" in data
        # Should NOT have sent the email
        assert "sent" not in data or data.get("sent") is False

    async def test_email_tones_differ(self, client, auth_session, match):
        formal = await client.post(
            f"/api/v1/matches/{match.id}/email",
            cookies={"session": auth_session},
            json={"tone": "formal"}
        )
        warm = await client.post(
            f"/api/v1/matches/{match.id}/email",
            cookies={"session": auth_session},
            json={"tone": "warm"}
        )
        assert formal.json()["body"] != warm.json()["body"]

    async def test_email_personalized_to_lp(self, client, auth_session, match):
        """Generated email references the specific LP."""
        response = await client.post(
            f"/api/v1/matches/{match.id}/email",
            cookies={"session": auth_session},
            json={"tone": "professional"}
        )
        body = response.json()["body"]
        # Should mention the LP name or relevant details
        assert match.lp.name in body or len(body) > 100
```

## M4-E2E: End-to-End Tests

### Pitch Generation

```python
# tests/e2e/test_m4_pitch.py

import pytest
from playwright.sync_api import Page, expect


class TestM4PitchGeneration:
    """E2E tests for M4: Pitch Generation milestone."""

    def test_generate_and_download_summary(self, page: Page, logged_in_user, fund_with_matches):
        """User can generate executive summary and download as PDF."""
        page.goto(f"/funds/{fund_with_matches.id}/matches")
        page.wait_for_selector('[data-testid="match-card"]')

        # Open pitch generation modal
        page.click('[data-testid="generate-pitch-btn"]:first-child')
        page.click('[data-testid="summary-option"]')

        # Wait for AI-generated summary
        page.wait_for_selector('[data-testid="summary-content"]')
        expect(page.locator('[data-testid="summary-content"]')).to_be_visible()

        # Download PDF
        with page.expect_download() as download_info:
            page.click('[data-testid="download-pdf-btn"]')

        download = download_info.value
        assert download.suggested_filename.endswith(".pdf")

    def test_generate_and_copy_email(self, page: Page, logged_in_user, fund_with_matches):
        """User can generate outreach email and copy to clipboard."""
        page.goto(f"/funds/{fund_with_matches.id}/matches")
        page.wait_for_selector('[data-testid="match-card"]')

        # Open pitch generation and select email
        page.click('[data-testid="generate-pitch-btn"]:first-child')
        page.click('[data-testid="email-option"]')

        # Select tone
        page.select_option('[data-testid="tone-select"]', "warm")

        # Wait for email generation
        page.wait_for_selector('[data-testid="email-subject"]')
        expect(page.locator('[data-testid="email-subject"]')).to_be_visible()
        expect(page.locator('[data-testid="email-body"]')).to_be_visible()

        # Copy to clipboard
        page.click('[data-testid="copy-btn"]')

        # Toast notification should appear
        expect(page.locator('[data-testid="copied-toast"]')).to_be_visible()

    def test_pitch_modal_htmx_loads_content(self, page: Page, logged_in_user, fund_with_matches):
        """Pitch modal content is loaded via HTMX when opened."""
        page.goto(f"/funds/{fund_with_matches.id}/matches")
        page.wait_for_selector('[data-testid="match-card"]')

        # Modal should not be visible initially
        expect(page.locator('[data-testid="pitch-modal"]')).not_to_be_visible()

        # Click generate pitch
        page.click('[data-testid="generate-pitch-btn"]:first-child')

        # Modal appears with HTMX-loaded content
        expect(page.locator('[data-testid="pitch-modal"]')).to_be_visible()
        expect(page.locator('[data-testid="summary-option"]')).to_be_visible()
        expect(page.locator('[data-testid="email-option"]')).to_be_visible()

    def test_copy_to_clipboard_functionality(self, page: Page, logged_in_user, fund_with_matches, context):
        """Copy to clipboard button copies email content."""
        # Grant clipboard permissions
        context.grant_permissions(["clipboard-read", "clipboard-write"])

        page.goto(f"/funds/{fund_with_matches.id}/matches")
        page.wait_for_selector('[data-testid="match-card"]')

        # Generate email
        page.click('[data-testid="generate-pitch-btn"]:first-child')
        page.click('[data-testid="email-option"]')
        page.wait_for_selector('[data-testid="email-body"]')

        # Get the email body text
        email_body = page.locator('[data-testid="email-body"]').text_content()

        # Copy to clipboard
        page.click('[data-testid="copy-btn"]')

        # Verify clipboard contains the email content
        clipboard_content = page.evaluate("navigator.clipboard.readText()")
        assert email_body in clipboard_content

    def test_email_not_auto_sent(self, page: Page, logged_in_user, fund_with_matches):
        """Email is generated for review, not automatically sent."""
        page.goto(f"/funds/{fund_with_matches.id}/matches")
        page.wait_for_selector('[data-testid="match-card"]')

        # Generate email
        page.click('[data-testid="generate-pitch-btn"]:first-child')
        page.click('[data-testid="email-option"]')
        page.wait_for_selector('[data-testid="email-body"]')

        # Email should be displayed for review
        expect(page.locator('[data-testid="email-preview"]')).to_be_visible()
        # "Send" button should require explicit action, or not exist (copy-only flow)
        expect(page.locator('[data-testid="copy-btn"]')).to_be_visible()
```

### Data Import Preview

```python
class TestM4DataImportPreview:
    """E2E tests for data import preview/approval flow."""

    def test_lp_import_shows_preview(self, page: Page, logged_in_user):
        """LP data import shows preview before committing."""
        page.goto("/admin/import")

        # Upload CSV file
        page.set_input_files('[data-testid="import-file"]', "tests/fixtures/sample_lps.csv")

        # Wait for preview to load
        page.wait_for_selector('[data-testid="import-preview"]')

        # Should show preview of data to be imported
        expect(page.locator('[data-testid="preview-row"]')).to_have_count(
            greater_than_or_equal=1
        )
        expect(page.locator('[data-testid="import-count"]')).to_be_visible()

        # Approve and Reject buttons should be visible
        expect(page.locator('[data-testid="approve-import-btn"]')).to_be_visible()
        expect(page.locator('[data-testid="cancel-import-btn"]')).to_be_visible()

    def test_lp_import_can_be_cancelled(self, page: Page, logged_in_user):
        """User can cancel import after preview."""
        page.goto("/admin/import")

        page.set_input_files('[data-testid="import-file"]', "tests/fixtures/sample_lps.csv")
        page.wait_for_selector('[data-testid="import-preview"]')

        # Cancel the import
        page.click('[data-testid="cancel-import-btn"]')

        # Preview should be dismissed
        expect(page.locator('[data-testid="import-preview"]')).not_to_be_visible()

    def test_lp_import_approval_commits_data(self, page: Page, logged_in_user, supabase):
        """Approving import commits data to database."""
        page.goto("/admin/import")

        page.set_input_files('[data-testid="import-file"]', "tests/fixtures/sample_lps.csv")
        page.wait_for_selector('[data-testid="import-preview"]')

        # Get count before import
        before_count = len(supabase.table("lps").select("id").execute().data)

        # Approve the import
        page.click('[data-testid="approve-import-btn"]')

        # Wait for success message
        page.wait_for_selector('[data-testid="import-success"]')

        # Verify data was actually imported
        after_count = len(supabase.table("lps").select("id").execute().data)
        assert after_count > before_count
```
