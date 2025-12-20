# Test Specifications
# LPxGP: GP-LP Intelligence Platform

**Version:** 2.0
**Last Updated:** 2024-12-20
**Structure:** Organized by Milestone

---

## Testing Philosophy

### TDD Approach
1. Write test first (RED)
2. Implement minimum code to pass (GREEN)
3. Refactor while keeping tests green (REFACTOR)

### Test Pyramid
```
              ┌─────────┐
              │   E2E   │  Playwright (~20 tests)
             ─┴─────────┴─
            ┌─────────────┐
            │ Integration │  pytest + httpx (~100 tests)
           ─┴─────────────┴─
          ┌─────────────────┐
          │   Unit Tests    │  pytest + Jest (~200 tests)
         ─┴─────────────────┴─
```

### Tools
| Layer | Tool |
|-------|------|
| Unit (Python) | pytest |
| Unit (Frontend) | Vitest |
| Integration | pytest + httpx |
| E2E | Playwright |

---

## Milestone 0: Foundation
### "I can search my LP database"

### M0-UNIT: Unit Tests

#### M0-UNIT-01: Data Cleaning Functions

```python
# tests/unit/test_cleaning.py

class TestStrategyNormalization:
    """Test strategy name normalization."""

    def test_lowercase_pe_normalizes(self):
        assert normalize_strategy("pe") == "Private Equity"

    def test_uppercase_PE_normalizes(self):
        assert normalize_strategy("PE") == "Private Equity"

    def test_buyout_normalizes_to_sub_strategy(self):
        assert normalize_strategy("buyout") == "Private Equity - Buyout"

    def test_vc_normalizes(self):
        assert normalize_strategy("vc") == "Venture Capital"

    def test_unknown_strategy_passes_through(self):
        assert normalize_strategy("Unknown Strategy") == "Unknown Strategy"

    def test_whitespace_trimmed(self):
        assert normalize_strategy("  pe  ") == "Private Equity"


class TestGeographyNormalization:
    """Test geography normalization."""

    def test_us_normalizes(self):
        result = normalize_geography("us")
        assert result["code"] == "US"
        assert result["region"] == "North America"

    def test_uk_normalizes(self):
        result = normalize_geography("uk")
        assert result["code"] == "GB"
        assert result["region"] == "Europe"

    def test_full_name_normalizes(self):
        result = normalize_geography("United States")
        assert result["code"] == "US"


class TestLPTypeNormalization:
    """Test LP type normalization."""

    def test_pension_normalizes(self):
        assert normalize_lp_type("pension") == "Public Pension"

    def test_family_office_normalizes(self):
        assert normalize_lp_type("FO") == "Family Office"

    def test_endowment_normalizes(self):
        assert normalize_lp_type("endowment") == "Endowment"


class TestDataQualityScore:
    """Test data quality scoring."""

    def test_minimal_lp_low_score(self):
        lp = LP(name="Test LP")
        score = calculate_data_quality_score(lp)
        assert score < 0.3

    def test_complete_lp_high_score(self):
        lp = LP(
            name="Complete LP",
            type="Public Pension",
            strategies=["Private Equity"],
            check_size_min_mm=10,
            check_size_max_mm=50,
            geographic_preferences=["North America"],
            mandate_description="Detailed mandate...",
            website="https://example.com"
        )
        score = calculate_data_quality_score(lp)
        assert score >= 0.7

    def test_score_between_0_and_1(self):
        lp = LP(name="Test", type="Endowment")
        score = calculate_data_quality_score(lp)
        assert 0 <= score <= 1
```

#### M0-UNIT-02: Pydantic Models

```python
# tests/unit/test_models.py

class TestLPModel:
    """Test LP Pydantic model."""

    def test_valid_lp_creates(self):
        lp = LPCreate(
            name="Test LP",
            type="Public Pension",
            strategies=["Private Equity"]
        )
        assert lp.name == "Test LP"

    def test_empty_name_fails(self):
        with pytest.raises(ValidationError):
            LPCreate(name="", type="Endowment")

    def test_invalid_type_fails(self):
        with pytest.raises(ValidationError):
            LPCreate(name="Test", type="Invalid Type")

    def test_check_size_min_less_than_max(self):
        with pytest.raises(ValidationError):
            LPCreate(
                name="Test",
                type="Endowment",
                check_size_min_mm=100,
                check_size_max_mm=50  # Invalid: min > max
            )
```

### M0-INT: Integration Tests

#### M0-INT-01: Authentication

```python
# tests/integration/test_auth.py

class TestRegistration:
    """Test user registration."""

    async def test_register_success(self, client):
        response = await client.post("/api/v1/auth/register", json={
            "email": "new@example.com",
            "password": "SecurePass123!",
            "full_name": "New User"
        })
        assert response.status_code == 201
        assert "id" in response.json()

    async def test_register_duplicate_email_fails(self, client, existing_user):
        response = await client.post("/api/v1/auth/register", json={
            "email": existing_user.email,
            "password": "SecurePass123!",
            "full_name": "Duplicate"
        })
        assert response.status_code == 409

    async def test_register_weak_password_fails(self, client):
        response = await client.post("/api/v1/auth/register", json={
            "email": "test@example.com",
            "password": "weak",
            "full_name": "Test"
        })
        assert response.status_code == 422


class TestLogin:
    """Test user login."""

    async def test_login_success(self, client, verified_user):
        response = await client.post("/api/v1/auth/login", json={
            "email": verified_user.email,
            "password": "TestPassword123!"
        })
        assert response.status_code == 200
        assert "access_token" in response.json()

    async def test_login_wrong_password_fails(self, client, verified_user):
        response = await client.post("/api/v1/auth/login", json={
            "email": verified_user.email,
            "password": "WrongPassword!"
        })
        assert response.status_code == 401

    async def test_login_unverified_fails(self, client, unverified_user):
        response = await client.post("/api/v1/auth/login", json={
            "email": unverified_user.email,
            "password": "TestPassword123!"
        })
        assert response.status_code == 403
```

#### M0-INT-02: LP Search

```python
# tests/integration/test_lp_search.py

class TestLPFilters:
    """Test LP search filters."""

    async def test_filter_by_type(self, client, auth_token, sample_lps):
        response = await client.get(
            "/api/v1/lps?type=Public%20Pension",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        for lp in response.json()["items"]:
            assert lp["type"] == "Public Pension"

    async def test_filter_by_strategy(self, client, auth_token, sample_lps):
        response = await client.get(
            "/api/v1/lps?strategies=Private%20Equity",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        for lp in response.json()["items"]:
            assert "Private Equity" in lp["strategies"]

    async def test_filter_by_check_size_range(self, client, auth_token):
        response = await client.get(
            "/api/v1/lps?check_size_min=20&check_size_max=80",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        for lp in response.json()["items"]:
            # LP range must overlap with query range
            assert lp["check_size_max_mm"] >= 20
            assert lp["check_size_min_mm"] <= 80

    async def test_combined_filters(self, client, auth_token):
        response = await client.get(
            "/api/v1/lps?type=Endowment&strategies=Venture%20Capital",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        for lp in response.json()["items"]:
            assert lp["type"] == "Endowment"
            assert "Venture Capital" in lp["strategies"]

    async def test_pagination(self, client, auth_token, many_lps):
        # First page
        r1 = await client.get(
            "/api/v1/lps?page=1&per_page=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        # Second page
        r2 = await client.get(
            "/api/v1/lps?page=2&per_page=10",
            headers={"Authorization": f"Bearer {auth_token}"}
        )

        ids1 = {lp["id"] for lp in r1.json()["items"]}
        ids2 = {lp["id"] for lp in r2.json()["items"]}
        assert ids1.isdisjoint(ids2)  # No overlap

    async def test_search_performance(self, client, auth_token, many_lps):
        """Search completes in < 500ms."""
        import time
        start = time.time()
        await client.get(
            "/api/v1/lps?type=Public%20Pension",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        duration_ms = (time.time() - start) * 1000
        assert duration_ms < 500
```

#### M0-INT-03: Multi-tenancy

```python
# tests/integration/test_multitenancy.py

class TestDataIsolation:
    """Test company data isolation."""

    async def test_user_sees_only_own_company(self, client, user_a, user_b):
        token_a = await login_user(client, user_a)
        token_b = await login_user(client, user_b)

        # User A creates a fund
        r = await client.post(
            "/api/v1/funds",
            headers={"Authorization": f"Bearer {token_a}"},
            json={"name": "Fund A", "target_size_mm": 100}
        )
        fund_a_id = r.json()["id"]

        # User B cannot see it
        r = await client.get(
            f"/api/v1/funds/{fund_a_id}",
            headers={"Authorization": f"Bearer {token_b}"}
        )
        assert r.status_code == 404  # Not 403 for security

    async def test_lps_globally_readable(self, client, user_a, user_b, lp):
        """LPs are visible to all authenticated users."""
        token_a = await login_user(client, user_a)
        token_b = await login_user(client, user_b)

        r_a = await client.get(
            f"/api/v1/lps/{lp.id}",
            headers={"Authorization": f"Bearer {token_a}"}
        )
        r_b = await client.get(
            f"/api/v1/lps/{lp.id}",
            headers={"Authorization": f"Bearer {token_b}"}
        )

        assert r_a.status_code == 200
        assert r_b.status_code == 200
```

### M0-E2E: End-to-End Tests

```typescript
// tests/e2e/m0-foundation.spec.ts

import { test, expect } from '@playwright/test';

test.describe('M0: Foundation', () => {

  test('user can register and login', async ({ page }) => {
    await page.goto('/register');
    await page.fill('[data-testid="email"]', 'test@example.com');
    await page.fill('[data-testid="password"]', 'SecurePass123!');
    await page.fill('[data-testid="name"]', 'Test User');
    await page.click('[data-testid="register-btn"]');

    // Should redirect to verify email page
    await expect(page).toHaveURL(/verify/);
  });

  test('user can search LPs with filters', async ({ page }) => {
    await loginAs(page, 'member@example.com');
    await page.goto('/lps');

    // Apply filter
    await page.click('[data-testid="type-filter"]');
    await page.click('text=Public Pension');

    // Results should update
    await expect(page.locator('[data-testid="lp-card"]')).toHaveCount({ min: 1 });

    // All results should be Public Pension
    const types = await page.locator('[data-testid="lp-type"]').allTextContents();
    for (const type of types) {
      expect(type).toBe('Public Pension');
    }
  });

  test('user can view LP details', async ({ page }) => {
    await loginAs(page, 'member@example.com');
    await page.goto('/lps');

    // Click first LP
    await page.click('[data-testid="lp-card"]:first-child');

    // Should see detail page
    await expect(page.locator('[data-testid="lp-name"]')).toBeVisible();
    await expect(page.locator('[data-testid="lp-mandate"]')).toBeVisible();
  });

});
```

---

## Milestone 1: Smart Search
### "Find LPs using natural language"

### M1-UNIT: Unit Tests

```python
# tests/unit/test_embeddings.py

class TestEmbeddingGeneration:
    """Test embedding generation."""

    async def test_embedding_has_correct_dimensions(self, mock_voyage):
        embedding = await generate_embedding("test text")
        assert len(embedding) == 1024

    async def test_similar_text_similar_embeddings(self, mock_voyage):
        e1 = await generate_embedding("growth equity technology")
        e2 = await generate_embedding("growth stage tech investing")
        similarity = cosine_similarity(e1, e2)
        assert similarity > 0.7

    async def test_different_text_different_embeddings(self, mock_voyage):
        e1 = await generate_embedding("real estate core")
        e2 = await generate_embedding("venture capital biotech")
        similarity = cosine_similarity(e1, e2)
        assert similarity < 0.5
```

### M1-INT: Integration Tests

```python
# tests/integration/test_semantic_search.py

class TestSemanticSearch:
    """Test semantic LP search."""

    async def test_semantic_search_returns_results(
        self, client, auth_token, lps_with_embeddings
    ):
        response = await client.post(
            "/api/v1/lps/semantic-search",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"query": "climate tech investors in Europe"}
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) > 0

    async def test_results_have_similarity_scores(
        self, client, auth_token, lps_with_embeddings
    ):
        response = await client.post(
            "/api/v1/lps/semantic-search",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"query": "growth equity"}
        )
        for item in response.json()["items"]:
            assert "similarity_score" in item
            assert 0 <= item["similarity_score"] <= 1

    async def test_results_sorted_by_relevance(
        self, client, auth_token, lps_with_embeddings
    ):
        response = await client.post(
            "/api/v1/lps/semantic-search",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"query": "technology growth"}
        )
        scores = [r["similarity_score"] for r in response.json()["items"]]
        assert scores == sorted(scores, reverse=True)

    async def test_semantic_combined_with_filters(
        self, client, auth_token, lps_with_embeddings
    ):
        response = await client.post(
            "/api/v1/lps/semantic-search",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "query": "technology",
                "filters": {"type": ["Endowment"]}
            }
        )
        for item in response.json()["items"]:
            assert item["type"] == "Endowment"

    async def test_semantic_search_performance(
        self, client, auth_token, many_lps_with_embeddings
    ):
        """Semantic search completes in < 2 seconds."""
        import time
        start = time.time()
        await client.post(
            "/api/v1/lps/semantic-search",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"query": "healthcare focused investor"}
        )
        duration = time.time() - start
        assert duration < 2.0
```

### M1-E2E: End-to-End Tests

```typescript
// tests/e2e/m1-semantic-search.spec.ts

test.describe('M1: Semantic Search', () => {

  test('natural language search returns relevant results', async ({ page }) => {
    await loginAs(page, 'member@example.com');
    await page.goto('/lps');

    await page.fill('[data-testid="semantic-search"]', 'family offices interested in fintech');
    await page.press('[data-testid="semantic-search"]', 'Enter');

    await expect(page.locator('[data-testid="loading"]')).not.toBeVisible();
    await expect(page.locator('[data-testid="lp-card"]')).toHaveCount({ min: 1 });
    await expect(page.locator('[data-testid="similarity-score"]')).toBeVisible();
  });

  test('can combine semantic search with filters', async ({ page }) => {
    await loginAs(page, 'member@example.com');
    await page.goto('/lps');

    // Apply filter first
    await page.click('[data-testid="type-filter"]');
    await page.click('text=Endowment');

    // Then semantic search
    await page.fill('[data-testid="semantic-search"]', 'technology');
    await page.press('[data-testid="semantic-search"]', 'Enter');

    // All results should be Endowments
    const types = await page.locator('[data-testid="lp-type"]').allTextContents();
    for (const type of types) {
      expect(type).toBe('Endowment');
    }
  });

});
```

---

## Milestone 2: Matching
### "See which LPs match my fund"

### M2-UNIT: Unit Tests

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

### M2-INT: Integration Tests

```python
# tests/integration/test_fund_matching.py

class TestFundCreation:
    """Test fund profile creation."""

    async def test_create_fund(self, client, auth_token):
        response = await client.post(
            "/api/v1/funds",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={
                "name": "Growth Fund III",
                "target_size_mm": 200,
                "strategy": "Private Equity - Growth",
                "geographic_focus": ["North America"]
            }
        )
        assert response.status_code == 201
        assert response.json()["name"] == "Growth Fund III"

    async def test_upload_deck(self, client, auth_token, fund, sample_pdf):
        response = await client.post(
            f"/api/v1/funds/{fund.id}/upload-deck",
            headers={"Authorization": f"Bearer {auth_token}"},
            files={"file": ("deck.pdf", sample_pdf, "application/pdf")}
        )
        assert response.status_code == 200
        assert response.json()["pitch_deck_url"] is not None


class TestMatchGeneration:
    """Test match generation."""

    async def test_generate_matches(self, client, auth_token, fund, sample_lps):
        response = await client.post(
            f"/api/v1/funds/{fund.id}/matches/generate",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        matches = response.json()["matches"]
        assert len(matches) > 0

    async def test_matches_sorted_by_score(self, client, auth_token, fund, sample_lps):
        response = await client.post(
            f"/api/v1/funds/{fund.id}/matches/generate",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        scores = [m["total_score"] for m in response.json()["matches"]]
        assert scores == sorted(scores, reverse=True)

    async def test_match_has_score_breakdown(self, client, auth_token, fund, sample_lps):
        response = await client.post(
            f"/api/v1/funds/{fund.id}/matches/generate",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        match = response.json()["matches"][0]
        assert "score_breakdown" in match
        assert "strategy_fit" in match["score_breakdown"]
```

### M2-E2E: End-to-End Tests

```typescript
// tests/e2e/m2-matching.spec.ts

test.describe('M2: Matching', () => {

  test('create fund and generate matches', async ({ page }) => {
    await loginAs(page, 'member@example.com');

    // Create fund
    await page.goto('/funds/new');
    await page.fill('[data-testid="fund-name"]', 'Test Fund');
    await page.fill('[data-testid="target-size"]', '200');
    await page.selectOption('[data-testid="strategy"]', 'Private Equity - Growth');
    await page.click('[data-testid="save-btn"]');

    // Generate matches
    await page.click('[data-testid="find-matches-btn"]');
    await expect(page.locator('[data-testid="loading"]')).toBeVisible();
    await expect(page.locator('[data-testid="loading"]')).not.toBeVisible({ timeout: 30000 });

    // Should have matches
    await expect(page.locator('[data-testid="match-card"]')).toHaveCount({ min: 1 });
  });

  test('match cards show scores', async ({ page }) => {
    await loginAs(page, 'member@example.com');
    await page.goto('/funds/123/matches');

    const scoreElements = page.locator('[data-testid="match-score"]');
    await expect(scoreElements).toHaveCount({ min: 1 });

    // Scores should be visible numbers
    const firstScore = await scoreElements.first().textContent();
    expect(parseInt(firstScore!)).toBeGreaterThan(0);
  });

});
```

---

## Milestone 3: Explanations
### "Understand WHY an LP matches"

### M3-UNIT: Unit Tests

```python
# tests/unit/test_explanations.py

class TestExplanationGeneration:
    """Test explanation generation."""

    async def test_explanation_generated(self, mock_claude, fund, lp, match):
        explanation = await generate_explanation(fund, lp, match.score)
        assert explanation is not None
        assert len(explanation) > 100

    async def test_explanation_includes_talking_points(self, mock_claude, fund, lp, match):
        result = await generate_explanation_with_points(fund, lp, match.score)
        assert "talking_points" in result
        assert len(result["talking_points"]) >= 3

    async def test_explanation_references_lp_data(self, mock_claude, fund, lp, match):
        lp.mandate_description = "We focus on growth equity"
        result = await generate_explanation(fund, lp, match.score)
        # Should reference the mandate
        assert "growth" in result.lower() or "mandate" in result.lower()
```

### M3-INT: Integration Tests

```python
# tests/integration/test_explanations.py

class TestExplanationEndpoint:
    """Test explanation API."""

    async def test_get_explanation(self, client, auth_token, match):
        response = await client.get(
            f"/api/v1/matches/{match.id}/explanation",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert "explanation" in response.json()
        assert "talking_points" in response.json()

    async def test_explanation_cached(self, client, auth_token, match, mock_claude):
        # First request
        await client.get(
            f"/api/v1/matches/{match.id}/explanation",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        call_count_1 = mock_claude.call_count

        # Second request (should use cache)
        await client.get(
            f"/api/v1/matches/{match.id}/explanation",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        call_count_2 = mock_claude.call_count

        assert call_count_1 == call_count_2  # No new API call

    async def test_explanation_time(self, client, auth_token, match):
        """Explanation generates in < 5 seconds."""
        import time
        start = time.time()
        await client.get(
            f"/api/v1/matches/{match.id}/explanation",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        duration = time.time() - start
        assert duration < 5.0
```

### M3-E2E: End-to-End Tests

```typescript
// tests/e2e/m3-explanations.spec.ts

test.describe('M3: Explanations', () => {

  test('view match explanation', async ({ page }) => {
    await loginAs(page, 'member@example.com');
    await page.goto('/funds/123/matches');

    // Expand explanation
    await page.click('[data-testid="expand-explanation-btn"]:first-child');

    // Should see explanation content
    await expect(page.locator('[data-testid="explanation-text"]')).toBeVisible();
    await expect(page.locator('[data-testid="talking-points"]')).toBeVisible();
  });

  test('explanation shows talking points', async ({ page }) => {
    await loginAs(page, 'member@example.com');
    await page.goto('/funds/123/matches');

    await page.click('[data-testid="expand-explanation-btn"]:first-child');

    const points = page.locator('[data-testid="talking-point"]');
    await expect(points).toHaveCount({ min: 3 });
  });

});
```

---

## Milestone 4: Pitch Generation
### "Generate personalized outreach"

### M4-INT: Integration Tests

```python
# tests/integration/test_pitch_generation.py

class TestSummaryGeneration:
    """Test executive summary generation."""

    async def test_generate_summary(self, client, auth_token, match):
        response = await client.post(
            f"/api/v1/matches/{match.id}/summary",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert len(response.json()["content"]) > 500

    async def test_summary_mentions_lp(self, client, auth_token, match):
        response = await client.post(
            f"/api/v1/matches/{match.id}/summary",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert match.lp.name in response.json()["content"]

    async def test_export_pdf(self, client, auth_token, match):
        response = await client.post(
            f"/api/v1/matches/{match.id}/summary/pdf",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 200
        assert response.headers["content-type"] == "application/pdf"


class TestEmailGeneration:
    """Test outreach email generation."""

    async def test_generate_email(self, client, auth_token, match):
        response = await client.post(
            f"/api/v1/matches/{match.id}/email",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"tone": "professional"}
        )
        assert response.status_code == 200
        assert "subject" in response.json()
        assert "body" in response.json()

    async def test_email_tones_differ(self, client, auth_token, match):
        formal = await client.post(
            f"/api/v1/matches/{match.id}/email",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"tone": "formal"}
        )
        warm = await client.post(
            f"/api/v1/matches/{match.id}/email",
            headers={"Authorization": f"Bearer {auth_token}"},
            json={"tone": "warm"}
        )
        assert formal.json()["body"] != warm.json()["body"]
```

### M4-E2E: End-to-End Tests

```typescript
// tests/e2e/m4-pitch.spec.ts

test.describe('M4: Pitch Generation', () => {

  test('generate and download summary', async ({ page }) => {
    await loginAs(page, 'member@example.com');
    await page.goto('/funds/123/matches');

    await page.click('[data-testid="generate-pitch-btn"]:first-child');
    await page.click('[data-testid="summary-option"]');

    await expect(page.locator('[data-testid="summary-content"]')).toBeVisible();

    // Download PDF
    const [download] = await Promise.all([
      page.waitForEvent('download'),
      page.click('[data-testid="download-pdf-btn"]')
    ]);
    expect(download.suggestedFilename()).toMatch(/\.pdf$/);
  });

  test('generate and copy email', async ({ page }) => {
    await loginAs(page, 'member@example.com');
    await page.goto('/funds/123/matches');

    await page.click('[data-testid="generate-pitch-btn"]:first-child');
    await page.click('[data-testid="email-option"]');
    await page.selectOption('[data-testid="tone-select"]', 'warm');

    await expect(page.locator('[data-testid="email-subject"]')).toBeVisible();
    await expect(page.locator('[data-testid="email-body"]')).toBeVisible();

    await page.click('[data-testid="copy-btn"]');
    await expect(page.locator('[data-testid="copied-toast"]')).toBeVisible();
  });

});
```

---

## Milestone 5: Production
### "Live system with automation"

### M5-INT: Integration Tests

```python
# tests/integration/test_admin.py

class TestAdminDashboard:
    """Test admin functionality."""

    async def test_super_admin_sees_all_companies(self, client, super_admin_token):
        response = await client.get(
            "/api/v1/admin/companies",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) > 0

    async def test_regular_user_cannot_access_admin(self, client, auth_token):
        response = await client.get(
            "/api/v1/admin/companies",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        assert response.status_code == 403

    async def test_data_quality_stats(self, client, super_admin_token):
        response = await client.get(
            "/api/v1/admin/stats/data-quality",
            headers={"Authorization": f"Bearer {super_admin_token}"}
        )
        assert response.status_code == 200
        assert "average_score" in response.json()
        assert "lps_needing_review" in response.json()
```

### M5-PERF: Performance Tests

```python
# tests/performance/test_performance.py

class TestPerformance:
    """Performance benchmarks."""

    @pytest.mark.benchmark
    async def test_search_10k_lps(self, client, auth_token, setup_10k_lps):
        times = []
        for _ in range(10):
            start = time.time()
            await client.get(
                "/api/v1/lps?type=Public%20Pension",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            times.append((time.time() - start) * 1000)

        avg = sum(times) / len(times)
        p95 = sorted(times)[9]

        assert avg < 300, f"Average {avg}ms > 300ms"
        assert p95 < 500, f"P95 {p95}ms > 500ms"

    @pytest.mark.benchmark
    async def test_match_generation_1k_lps(self, client, auth_token, fund, setup_1k_lps):
        start = time.time()
        await client.post(
            f"/api/v1/funds/{fund.id}/matches/generate",
            headers={"Authorization": f"Bearer {auth_token}"}
        )
        duration = time.time() - start
        assert duration < 30.0

    @pytest.mark.benchmark
    async def test_concurrent_users(self, client, setup_test_users):
        async def user_session(user):
            token = await login_user(client, user)
            r = await client.get(
                "/api/v1/lps",
                headers={"Authorization": f"Bearer {token}"}
            )
            return r.status_code == 200

        results = await asyncio.gather(*[
            user_session(u) for u in setup_test_users[:100]
        ])
        success_rate = sum(results) / len(results)
        assert success_rate >= 0.99
```

### M5-SEC: Security Tests

```python
# tests/security/test_security.py

class TestSecurity:
    """Security tests."""

    async def test_sql_injection_blocked(self, client, auth_token):
        payloads = [
            "'; DROP TABLE lps; --",
            "1 OR 1=1",
            "' UNION SELECT * FROM users --"
        ]
        for payload in payloads:
            response = await client.get(
                f"/api/v1/lps?name={payload}",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            assert response.status_code in [200, 422]  # Not 500

    async def test_rate_limiting(self, client, auth_token):
        responses = []
        for _ in range(150):  # Exceed 100/min
            r = await client.get(
                "/api/v1/lps",
                headers={"Authorization": f"Bearer {auth_token}"}
            )
            responses.append(r.status_code)

        assert 429 in responses  # Some should be rate limited

    async def test_expired_jwt_rejected(self, client):
        expired_token = create_jwt(
            {"sub": "user-id", "exp": datetime.now() - timedelta(hours=1)}
        )
        response = await client.get(
            "/api/v1/lps",
            headers={"Authorization": f"Bearer {expired_token}"}
        )
        assert response.status_code == 401
```

---

## Test Fixtures

```python
# tests/conftest.py

import pytest
from httpx import AsyncClient
from backend.main import app

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def sample_lps(db_session):
    lps = [
        LP(name="CalPERS", type="Public Pension", strategies=["Private Equity"]),
        LP(name="Harvard", type="Endowment", strategies=["Venture Capital"]),
        LP(name="Smith Family", type="Family Office", strategies=["Private Equity"]),
    ]
    for lp in lps:
        db_session.add(lp)
    db_session.commit()
    return lps

@pytest.fixture
async def auth_token(client, verified_user):
    response = await client.post("/api/v1/auth/login", json={
        "email": verified_user.email,
        "password": "TestPassword123!"
    })
    return response.json()["access_token"]
```

---

## Running Tests

```bash
# All tests
uv run pytest

# By milestone
uv run pytest tests/ -k "M0"
uv run pytest tests/ -k "M1"
uv run pytest tests/ -k "M2"

# By type
uv run pytest tests/unit/
uv run pytest tests/integration/
npm run test:e2e

# With coverage
uv run pytest --cov=backend --cov-report=html

# Performance only
uv run pytest -m benchmark
```
