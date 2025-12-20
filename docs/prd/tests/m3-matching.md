# M3: Fund Profile + Matching Tests
### "Upload deck, create fund profile, see LP matches"

## M3-UNIT: Unit Tests

### Deck Extraction

```python
# tests/unit/test_deck_extraction.py

class TestDeckExtraction:
    """Test pitch deck field extraction."""

    async def test_extract_fund_name(self, mock_llm, sample_deck_text):
        result = await extract_fund_fields(sample_deck_text)
        assert "fund_name" in result
        assert result["fund_name"] is not None

    async def test_extract_target_size(self, mock_llm, sample_deck_text):
        result = await extract_fund_fields(sample_deck_text)
        assert "target_size_mm" in result
        assert isinstance(result["target_size_mm"], (int, float))

    async def test_extract_strategy(self, mock_llm, sample_deck_text):
        result = await extract_fund_fields(sample_deck_text)
        assert "strategy" in result

    async def test_missing_fields_flagged(self, mock_llm, incomplete_deck_text):
        result = await extract_fund_fields(incomplete_deck_text)
        assert "missing_fields" in result
        assert len(result["missing_fields"]) > 0
```

### Matching Algorithm

```python
# tests/unit/test_matching.py

class TestHardFilters:
    """Test hard filter matching."""

    def test_strategy_mismatch_filtered(self):
        fund = Fund(strategy="Private Equity - Growth", geographic_focus=["US"])
        lp = LP(strategies=["Venture Capital"], geographic_preferences=["US"])

        result = apply_hard_filters(fund, [lp])
        assert len(result) == 0

    def test_geography_mismatch_filtered(self):
        fund = Fund(strategy="Private Equity", geographic_focus=["US"])
        lp = LP(strategies=["Private Equity"], geographic_preferences=["Europe"])

        result = apply_hard_filters(fund, [lp])
        assert len(result) == 0

    def test_fund_size_out_of_range_filtered(self):
        fund = Fund(
            strategy="Private Equity",
            geographic_focus=["US"],
            target_size_mm=1000
        )
        lp = LP(
            strategies=["Private Equity"],
            geographic_preferences=["US"],
            max_fund_size_mm=200
        )

        result = apply_hard_filters(fund, [lp])
        assert len(result) == 0

    def test_compatible_lp_passes(self):
        fund = Fund(
            strategy="Private Equity - Growth",
            geographic_focus=["US"],
            target_size_mm=200
        )
        lp = LP(
            strategies=["Private Equity", "Private Equity - Growth"],
            geographic_preferences=["US", "Europe"],
            max_fund_size_mm=500
        )

        result = apply_hard_filters(fund, [lp])
        assert len(result) == 1


class TestSoftScoring:
    """Test soft scoring algorithm."""

    def test_score_between_0_and_100(self):
        fund = Fund(strategy="PE", geographic_focus=["US"], target_size_mm=100)
        lp = LP(strategies=["PE"], geographic_preferences=["US"])

        score = calculate_score(fund, lp)
        assert 0 <= score <= 100

    def test_perfect_match_high_score(self):
        fund = Fund(
            strategy="Private Equity - Growth",
            geographic_focus=["US"],
            target_size_mm=200,
            investment_thesis="Growth technology focus"
        )
        lp = LP(
            strategies=["Private Equity - Growth"],
            geographic_preferences=["US"],
            sweet_spot_mm=200,
            mandate_description="Growth technology investing"
        )

        score = calculate_score(fund, lp)
        assert score > 80

    def test_score_breakdown_provided(self):
        fund = Fund(strategy="PE", geographic_focus=["US"], target_size_mm=100)
        lp = LP(strategies=["PE"], geographic_preferences=["US"])

        result = calculate_score_with_breakdown(fund, lp)

        assert "total" in result
        assert "breakdown" in result
        assert "strategy_fit" in result["breakdown"]
        assert "geography_fit" in result["breakdown"]
```

## M3-INT: Integration Tests

### Deck Upload

```python
# tests/integration/test_deck_upload.py

class TestDeckUpload:
    """Test pitch deck upload and extraction."""

    async def test_upload_deck_returns_extracted_fields(self, client, auth_session, sample_pdf):
        """Deck upload returns extracted fields for confirmation."""
        response = await client.post(
            "/api/v1/funds/upload-deck",
            cookies={"session": auth_session},
            files={"file": ("deck.pdf", sample_pdf, "application/pdf")}
        )
        assert response.status_code == 200
        data = response.json()
        # Returns extracted fields, not a created fund
        assert "extracted_fields" in data
        assert "fund_name" in data["extracted_fields"]
        assert "confidence_scores" in data

    async def test_upload_deck_identifies_missing_fields(self, client, auth_session, incomplete_pdf):
        """Deck upload identifies fields that need manual input."""
        response = await client.post(
            "/api/v1/funds/upload-deck",
            cookies={"session": auth_session},
            files={"file": ("deck.pdf", incomplete_pdf, "application/pdf")}
        )
        assert response.status_code == 200
        data = response.json()
        assert "missing_fields" in data
        assert len(data["missing_fields"]) > 0
```

### Fund Profile Confirmation

```python
class TestFundProfileConfirmation:
    """Test fund profile confirmation flow (human-in-the-loop)."""

    async def test_confirm_extracted_fields_creates_fund(self, client, auth_session, extracted_fields):
        """GP confirms extracted fields to create fund profile."""
        response = await client.post(
            "/api/v1/funds/confirm",
            cookies={"session": auth_session},
            json={
                "extracted_fields": extracted_fields,
                "confirmed": True
            }
        )
        assert response.status_code == 201
        assert "id" in response.json()
        assert response.json()["name"] == extracted_fields["fund_name"]

    async def test_edit_extracted_fields_before_confirm(self, client, auth_session, extracted_fields):
        """GP can edit extracted fields before confirming."""
        extracted_fields["fund_name"] = "Edited Fund Name"
        extracted_fields["target_size_mm"] = 300  # Changed from extracted value

        response = await client.post(
            "/api/v1/funds/confirm",
            cookies={"session": auth_session},
            json={
                "extracted_fields": extracted_fields,
                "confirmed": True
            }
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Edited Fund Name"
        assert response.json()["target_size_mm"] == 300

    async def test_questionnaire_for_missing_fields(self, client, auth_session, extracted_fields_incomplete):
        """System prompts for missing fields via questionnaire."""
        response = await client.post(
            "/api/v1/funds/confirm",
            cookies={"session": auth_session},
            json={
                "extracted_fields": extracted_fields_incomplete,
                "confirmed": True
            }
        )
        # Should fail validation and return required fields
        assert response.status_code == 422
        assert "missing_required" in response.json()
```

### Match Generation

```python
# tests/integration/test_fund_matching.py

class TestMatchGeneration:
    """Test match generation."""

    async def test_generate_matches(self, client, auth_session, fund, sample_lps):
        response = await client.post(
            f"/api/v1/funds/{fund.id}/matches/generate",
            cookies={"session": auth_session}
        )
        assert response.status_code == 200
        matches = response.json()["matches"]
        assert len(matches) > 0

    async def test_matches_sorted_by_score(self, client, auth_session, fund, sample_lps):
        response = await client.post(
            f"/api/v1/funds/{fund.id}/matches/generate",
            cookies={"session": auth_session}
        )
        scores = [m["total_score"] for m in response.json()["matches"]]
        assert scores == sorted(scores, reverse=True)

    async def test_match_has_score_breakdown(self, client, auth_session, fund, sample_lps):
        response = await client.post(
            f"/api/v1/funds/{fund.id}/matches/generate",
            cookies={"session": auth_session}
        )
        match = response.json()["matches"][0]
        assert "score_breakdown" in match
        assert "strategy_fit" in match["score_breakdown"]
```

## M3-E2E: End-to-End Tests

```python
# tests/e2e/test_m3_fund_matching.py

import pytest
from playwright.sync_api import Page, expect


class TestM3FundMatching:
    """E2E tests for M3: Fund Profile + Matching milestone."""

    def test_upload_deck_shows_confirmation_screen(self, page: Page, logged_in_user):
        """Uploading deck shows extracted fields for confirmation."""
        page.goto("/funds/new")

        # Upload deck file
        page.set_input_files('[data-testid="deck-upload"]', "tests/fixtures/sample_deck.pdf")

        # Wait for extraction to complete
        page.wait_for_selector('[data-testid="confirmation-screen"]')

        # Should see extracted fields for review
        expect(page.locator('[data-testid="extracted-fund-name"]')).to_be_visible()
        expect(page.locator('[data-testid="extracted-target-size"]')).to_be_visible()
        expect(page.locator('[data-testid="extracted-strategy"]')).to_be_visible()

        # Confirm button should be visible
        expect(page.locator('[data-testid="confirm-btn"]')).to_be_visible()

    def test_gp_can_edit_extracted_fields(self, page: Page, logged_in_user):
        """GP can edit extracted fields before confirming."""
        page.goto("/funds/new")
        page.set_input_files('[data-testid="deck-upload"]', "tests/fixtures/sample_deck.pdf")
        page.wait_for_selector('[data-testid="confirmation-screen"]')

        # Edit the fund name
        page.fill('[data-testid="edit-fund-name"]', "My Edited Fund Name")

        # Confirm
        page.click('[data-testid="confirm-btn"]')

        # Should redirect to fund page with edited name
        page.wait_for_url(re.compile(r"/funds/\d+"))
        expect(page.locator('[data-testid="fund-name"]')).to_have_text("My Edited Fund Name")

    def test_questionnaire_appears_for_missing_fields(self, page: Page, logged_in_user):
        """Questionnaire appears when deck is missing required fields."""
        page.goto("/funds/new")

        # Upload incomplete deck
        page.set_input_files('[data-testid="deck-upload"]', "tests/fixtures/incomplete_deck.pdf")
        page.wait_for_selector('[data-testid="confirmation-screen"]')

        # Should see questionnaire for missing fields
        expect(page.locator('[data-testid="missing-fields-questionnaire"]')).to_be_visible()
        expect(page.locator('[data-testid="required-field-input"]')).to_have_count(
            greater_than_or_equal=1
        )

    def test_generate_matches_after_fund_creation(self, page: Page, logged_in_user, fund):
        """User can generate LP matches after fund profile is complete."""
        page.goto(f"/funds/{fund.id}")

        # Generate matches (HTMX button)
        page.click('[data-testid="find-matches-btn"]')

        # Loading indicator should appear
        expect(page.locator('[data-testid="loading"]')).to_be_visible()

        # Wait for matches to load
        page.wait_for_selector('[data-testid="match-card"]', timeout=30000)
        expect(page.locator('[data-testid="loading"]')).not_to_be_visible()

        # Should have match results
        expect(page.locator('[data-testid="match-card"]')).to_have_count(
            greater_than_or_equal=1
        )

    def test_match_cards_show_scores(self, page: Page, logged_in_user, fund_with_matches):
        """Match cards display score values."""
        page.goto(f"/funds/{fund_with_matches.id}/matches")
        page.wait_for_selector('[data-testid="match-card"]')

        score_elements = page.locator('[data-testid="match-score"]')
        expect(score_elements).to_have_count(greater_than_or_equal=1)

        # First score should be a visible number
        first_score = score_elements.first.text_content()
        assert int(first_score) > 0
```
