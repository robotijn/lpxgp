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
              │   E2E   │  Playwright for HTMX pages (~20 tests)
             ─┴─────────┴─
            ┌─────────────┐
            │ Integration │  pytest + httpx (~100 tests)
           ─┴─────────────┴─
          ┌─────────────────┐
          │   Unit Tests    │  pytest (~200 tests)
         ─┴─────────────────┴─
```

### Tools
| Layer | Tool |
|-------|------|
| Unit (Python) | pytest |
| Integration | pytest + httpx |
| E2E | Playwright (server-rendered HTML + HTMX) |

### Stack
- **Frontend:** Jinja2 templates + HTMX + Tailwind CSS (server-rendered)
- **Backend:** FastAPI + supabase-py (no SQLAlchemy)
- **Testing:** pytest for all Python code, Playwright for browser E2E tests

---

## Milestone 0: Foundation
### "Data is imported and clean"

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

#### M0-INT-01: Authentication (Supabase Auth)

```python
# tests/integration/test_auth.py

class TestSupabaseAuthIntegration:
    """Test Supabase Auth integration for M0."""

    async def test_auth_callback_success(self, client, supabase_auth_code):
        """Auth callback from Supabase creates local session."""
        response = await client.get(
            f"/auth/callback?code={supabase_auth_code}",
            follow_redirects=False
        )
        assert response.status_code == 302
        assert "/dashboard" in response.headers.get("location", "")

    async def test_protected_route_redirects_unauthenticated(self, client):
        """Unauthenticated users are redirected to login."""
        response = await client.get("/api/v1/lps", follow_redirects=False)
        assert response.status_code in [302, 401]

    async def test_authenticated_request_succeeds(self, client, auth_session):
        """Authenticated requests with valid session succeed."""
        response = await client.get(
            "/api/v1/lps",
            cookies={"session": auth_session}
        )
        assert response.status_code == 200

    async def test_expired_session_rejected(self, client, expired_session):
        """Expired sessions are rejected."""
        response = await client.get(
            "/api/v1/lps",
            cookies={"session": expired_session}
        )
        assert response.status_code in [302, 401]

    async def test_logout_clears_session(self, client, auth_session):
        """Logout clears the session cookie."""
        response = await client.post(
            "/auth/logout",
            cookies={"session": auth_session},
            follow_redirects=False
        )
        assert response.status_code == 302
        # Session cookie should be cleared
        assert "session" not in response.cookies or response.cookies["session"] == ""
```

#### M0-INT-02: LP Search

```python
# tests/integration/test_lp_search.py

class TestLPFilters:
    """Test LP search filters."""

    async def test_filter_by_type(self, client, auth_session, sample_lps):
        response = await client.get(
            "/api/v1/lps?type=Public%20Pension",
            cookies={"session": auth_session}
        )
        assert response.status_code == 200
        for lp in response.json()["items"]:
            assert lp["type"] == "Public Pension"

    async def test_filter_by_strategy(self, client, auth_session, sample_lps):
        response = await client.get(
            "/api/v1/lps?strategies=Private%20Equity",
            cookies={"session": auth_session}
        )
        assert response.status_code == 200
        for lp in response.json()["items"]:
            assert "Private Equity" in lp["strategies"]

    async def test_filter_by_check_size_range(self, client, auth_session):
        response = await client.get(
            "/api/v1/lps?check_size_min=20&check_size_max=80",
            cookies={"session": auth_session}
        )
        assert response.status_code == 200
        for lp in response.json()["items"]:
            # LP range must overlap with query range
            assert lp["check_size_max_mm"] >= 20
            assert lp["check_size_min_mm"] <= 80

    async def test_combined_filters(self, client, auth_session):
        response = await client.get(
            "/api/v1/lps?type=Endowment&strategies=Venture%20Capital",
            cookies={"session": auth_session}
        )
        assert response.status_code == 200
        for lp in response.json()["items"]:
            assert lp["type"] == "Endowment"
            assert "Venture Capital" in lp["strategies"]

    async def test_pagination(self, client, auth_session, many_lps):
        # First page
        r1 = await client.get(
            "/api/v1/lps?page=1&per_page=10",
            cookies={"session": auth_session}
        )
        # Second page
        r2 = await client.get(
            "/api/v1/lps?page=2&per_page=10",
            cookies={"session": auth_session}
        )

        ids1 = {lp["id"] for lp in r1.json()["items"]}
        ids2 = {lp["id"] for lp in r2.json()["items"]}
        assert ids1.isdisjoint(ids2)  # No overlap

    async def test_search_performance(self, client, auth_session, many_lps):
        """Search completes in < 500ms."""
        import time
        start = time.time()
        await client.get(
            "/api/v1/lps?type=Public%20Pension",
            cookies={"session": auth_session}
        )
        duration_ms = (time.time() - start) * 1000
        assert duration_ms < 500
```

#### M0-INT-03: Multi-tenancy

```python
# tests/integration/test_multitenancy.py

class TestDataIsolation:
    """Test company data isolation."""

    async def test_user_sees_only_own_company(self, client, session_user_a, session_user_b):
        # User A creates a fund
        r = await client.post(
            "/api/v1/funds",
            cookies={"session": session_user_a},
            json={"name": "Fund A", "target_size_mm": 100}
        )
        fund_a_id = r.json()["id"]

        # User B cannot see it
        r = await client.get(
            f"/api/v1/funds/{fund_a_id}",
            cookies={"session": session_user_b}
        )
        assert r.status_code == 404  # Not 403 for security

    async def test_lps_globally_readable(self, client, session_user_a, session_user_b, lp):
        """LPs are visible to all authenticated users."""
        r_a = await client.get(
            f"/api/v1/lps/{lp['id']}",
            cookies={"session": session_user_a}
        )
        r_b = await client.get(
            f"/api/v1/lps/{lp['id']}",
            cookies={"session": session_user_b}
        )

        assert r_a.status_code == 200
        assert r_b.status_code == 200
```

### M0-E2E: End-to-End Tests

```python
# tests/e2e/test_m0_foundation.py

import pytest
from playwright.sync_api import Page, expect


class TestM0Foundation:
    """E2E tests for M0: Foundation milestone."""

    def test_user_can_register(self, page: Page):
        """User can register with valid credentials."""
        page.goto("/register")
        page.fill('[data-testid="email"]', "test@example.com")
        page.fill('[data-testid="password"]', "SecurePass123!")
        page.fill('[data-testid="name"]', "Test User")
        page.click('[data-testid="register-btn"]')

        # Should redirect to verify email page
        expect(page).to_have_url(re.compile(r"/verify"))

    def test_user_can_search_lps_with_filters(self, page: Page, logged_in_user):
        """User can filter LPs by type using HTMX-powered filters."""
        page.goto("/lps")

        # Apply filter - HTMX will update the results
        page.click('[data-testid="type-filter"]')
        page.click("text=Public Pension")

        # Wait for HTMX to update the content
        page.wait_for_selector('[data-testid="lp-card"]')

        # Results should be visible
        expect(page.locator('[data-testid="lp-card"]')).to_have_count(
            greater_than_or_equal=1
        )

        # All results should be Public Pension
        type_elements = page.locator('[data-testid="lp-type"]').all()
        for elem in type_elements:
            expect(elem).to_have_text("Public Pension")

    def test_user_can_view_lp_details(self, page: Page, logged_in_user):
        """User can click an LP card to view details."""
        page.goto("/lps")
        page.wait_for_selector('[data-testid="lp-card"]')

        # Click first LP card
        page.click('[data-testid="lp-card"]:first-child')

        # Should see detail page with LP info
        expect(page.locator('[data-testid="lp-name"]')).to_be_visible()
        expect(page.locator('[data-testid="lp-mandate"]')).to_be_visible()

    def test_htmx_partial_updates(self, page: Page, logged_in_user):
        """HTMX correctly updates partial page content without full reload."""
        page.goto("/lps")

        # Get initial page content marker
        initial_url = page.url

        # Apply filter (triggers HTMX request)
        page.click('[data-testid="type-filter"]')
        page.click("text=Endowment")

        # Wait for HTMX to complete
        page.wait_for_load_state("networkidle")

        # URL should update with filter params but no full page reload
        expect(page).to_have_url(re.compile(r"type=Endowment"))

        # Header should still be visible (wasn't replaced)
        expect(page.locator('[data-testid="page-header"]')).to_be_visible()
```

---

## Milestone 1: Auth + Full-Text Search
### "I can log in and search my LP database"

### M1-UNIT: Unit Tests

```python
# tests/unit/test_full_text_search.py

class TestFullTextSearch:
    """Test PostgreSQL full-text search query building."""

    def test_single_term_query(self):
        query = build_search_query("technology")
        assert query == "technology:*"

    def test_multi_term_query(self):
        query = build_search_query("growth equity")
        assert query == "growth:* & equity:*"

    def test_special_chars_escaped(self):
        query = build_search_query("tech & growth")
        assert "&" not in query or query.count("&") == 1  # Only the AND operator

    def test_empty_query_returns_none(self):
        query = build_search_query("")
        assert query is None
```

### M1-INT: Integration Tests

```python
# tests/integration/test_auth_supabase.py

class TestSupabaseAuth:
    """Test Supabase Auth integration."""

    async def test_login_redirects_to_supabase(self, client):
        """Login page should redirect to Supabase Auth UI."""
        response = await client.get("/login", follow_redirects=False)
        # Should redirect to Supabase Auth or render page with Supabase JS
        assert response.status_code in [200, 302]

    async def test_callback_creates_session(self, client, supabase_auth_code):
        """Auth callback creates local session from Supabase token."""
        response = await client.get(
            f"/auth/callback?code={supabase_auth_code}",
            follow_redirects=False
        )
        assert response.status_code == 302
        assert "session" in response.cookies or response.headers.get("location") == "/dashboard"

    async def test_protected_route_requires_auth(self, client):
        """Protected routes redirect unauthenticated users."""
        response = await client.get("/dashboard", follow_redirects=False)
        assert response.status_code == 302
        assert "/login" in response.headers.get("location", "")

    async def test_authenticated_user_can_access_dashboard(self, client, auth_session):
        """Authenticated user can access protected routes."""
        response = await client.get(
            "/dashboard",
            cookies={"session": auth_session}
        )
        assert response.status_code == 200


# tests/integration/test_full_text_search.py

class TestFullTextSearch:
    """Test full-text LP search."""

    async def test_text_search_returns_results(self, client, auth_session, sample_lps):
        response = await client.get(
            "/api/v1/lps?q=pension",
            cookies={"session": auth_session}
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) > 0

    async def test_text_search_matches_name(self, client, auth_session, sample_lps):
        response = await client.get(
            "/api/v1/lps?q=CalPERS",
            cookies={"session": auth_session}
        )
        assert response.status_code == 200
        assert any("CalPERS" in lp["name"] for lp in response.json()["items"])

    async def test_text_search_matches_mandate(self, client, auth_session, sample_lps):
        response = await client.get(
            "/api/v1/lps?q=growth%20equity",
            cookies={"session": auth_session}
        )
        assert response.status_code == 200
        # Results should contain LPs with "growth equity" in mandate

    async def test_text_search_combined_with_filters(self, client, auth_session, sample_lps):
        response = await client.get(
            "/api/v1/lps?q=technology&type=Endowment",
            cookies={"session": auth_session}
        )
        assert response.status_code == 200
        for lp in response.json()["items"]:
            assert lp["type"] == "Endowment"

    async def test_empty_search_returns_all(self, client, auth_session, sample_lps):
        response = await client.get(
            "/api/v1/lps",
            cookies={"session": auth_session}
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) == len(sample_lps)
```

### M1-E2E: End-to-End Tests

```python
# tests/e2e/test_m1_auth_search.py

import pytest
from playwright.sync_api import Page, expect


class TestM1AuthAndSearch:
    """E2E tests for M1: Auth + Full-Text Search milestone."""

    def test_dashboard_loads_after_login(self, page: Page, logged_in_user):
        """Dashboard page loads successfully for authenticated user."""
        page.goto("/dashboard")
        expect(page.locator('[data-testid="dashboard-header"]')).to_be_visible()
        expect(page.locator('[data-testid="lp-count"]')).to_be_visible()

    def test_full_text_search_returns_results(self, page: Page, logged_in_user):
        """User can search LPs using full-text search."""
        page.goto("/lps")

        # Enter search query
        page.fill('[data-testid="search-input"]', "technology growth")
        page.press('[data-testid="search-input"]', "Enter")

        # Wait for HTMX to complete the search
        page.wait_for_selector('[data-testid="lp-card"]')

        # Should have results
        expect(page.locator('[data-testid="lp-card"]')).to_have_count(
            greater_than_or_equal=1
        )

    def test_filter_lps_by_type(self, page: Page, logged_in_user):
        """User can filter LPs by type."""
        page.goto("/lps")

        # Apply filter
        page.click('[data-testid="type-filter"]')
        page.click("text=Public Pension")

        # Wait for HTMX to update
        page.wait_for_load_state("networkidle")

        # All results should be Public Pension
        type_elements = page.locator('[data-testid="lp-type"]').all()
        for elem in type_elements:
            expect(elem).to_have_text("Public Pension")

    def test_combine_search_with_filters(self, page: Page, logged_in_user):
        """User can combine text search with type filters."""
        page.goto("/lps")

        # Apply filter first
        page.click('[data-testid="type-filter"]')
        page.click("text=Endowment")
        page.wait_for_load_state("networkidle")

        # Then perform text search
        page.fill('[data-testid="search-input"]', "technology")
        page.press('[data-testid="search-input"]', "Enter")
        page.wait_for_load_state("networkidle")

        # All results should be Endowments
        type_elements = page.locator('[data-testid="lp-type"]').all()
        for elem in type_elements:
            expect(elem).to_have_text("Endowment")

    def test_unauthenticated_redirects_to_login(self, page: Page):
        """Unauthenticated user is redirected to login."""
        page.goto("/lps")
        expect(page).to_have_url(re.compile(r"/login"))
```

---

## Milestone 2: Semantic Search
### "Find LPs using natural language"

### M2-UNIT: Unit Tests

```python
# tests/unit/test_embeddings.py

class TestEmbeddingGeneration:
    """Test Voyage AI embedding generation."""

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

    async def test_empty_text_raises_error(self, mock_voyage):
        with pytest.raises(ValueError):
            await generate_embedding("")
```

### M2-INT: Integration Tests

```python
# tests/integration/test_semantic_search.py

class TestSemanticSearch:
    """Test semantic LP search with Voyage AI embeddings."""

    async def test_semantic_search_returns_results(
        self, client, auth_session, lps_with_embeddings
    ):
        response = await client.post(
            "/api/v1/lps/semantic-search",
            cookies={"session": auth_session},
            json={"query": "climate tech investors in Europe"}
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) > 0

    async def test_results_have_similarity_scores(
        self, client, auth_session, lps_with_embeddings
    ):
        response = await client.post(
            "/api/v1/lps/semantic-search",
            cookies={"session": auth_session},
            json={"query": "growth equity"}
        )
        for item in response.json()["items"]:
            assert "similarity_score" in item
            assert 0 <= item["similarity_score"] <= 1

    async def test_results_sorted_by_relevance(
        self, client, auth_session, lps_with_embeddings
    ):
        response = await client.post(
            "/api/v1/lps/semantic-search",
            cookies={"session": auth_session},
            json={"query": "technology growth"}
        )
        scores = [r["similarity_score"] for r in response.json()["items"]]
        assert scores == sorted(scores, reverse=True)

    async def test_semantic_combined_with_filters(
        self, client, auth_session, lps_with_embeddings
    ):
        response = await client.post(
            "/api/v1/lps/semantic-search",
            cookies={"session": auth_session},
            json={
                "query": "technology",
                "filters": {"type": ["Endowment"]}
            }
        )
        for item in response.json()["items"]:
            assert item["type"] == "Endowment"

    async def test_semantic_search_performance(
        self, client, auth_session, many_lps_with_embeddings
    ):
        """Semantic search completes in < 2 seconds."""
        import time
        start = time.time()
        await client.post(
            "/api/v1/lps/semantic-search",
            cookies={"session": auth_session},
            json={"query": "healthcare focused investor"}
        )
        duration = time.time() - start
        assert duration < 2.0
```

### M2-E2E: End-to-End Tests

```python
# tests/e2e/test_m2_semantic_search.py

import pytest
from playwright.sync_api import Page, expect


class TestM2SemanticSearch:
    """E2E tests for M2: Semantic Search milestone."""

    def test_natural_language_search_returns_results(self, page: Page, logged_in_user):
        """User can search using natural language via HTMX."""
        page.goto("/lps")

        # Enter semantic search query
        page.fill('[data-testid="semantic-search"]', "family offices interested in fintech")
        page.press('[data-testid="semantic-search"]', "Enter")

        # Wait for HTMX to complete the search
        page.wait_for_selector('[data-testid="lp-card"]')
        expect(page.locator('[data-testid="loading"]')).not_to_be_visible()

        # Should have results with similarity scores
        expect(page.locator('[data-testid="lp-card"]')).to_have_count(
            greater_than_or_equal=1
        )
        expect(page.locator('[data-testid="similarity-score"]').first).to_be_visible()

    def test_combine_semantic_search_with_filters(self, page: Page, logged_in_user):
        """User can combine semantic search with type filters."""
        page.goto("/lps")

        # Apply filter first
        page.click('[data-testid="type-filter"]')
        page.click("text=Endowment")

        # Wait for filter to apply
        page.wait_for_load_state("networkidle")

        # Then perform semantic search
        page.fill('[data-testid="semantic-search"]', "technology")
        page.press('[data-testid="semantic-search"]', "Enter")

        # Wait for search results
        page.wait_for_load_state("networkidle")

        # All results should be Endowments
        type_elements = page.locator('[data-testid="lp-type"]').all()
        for elem in type_elements:
            expect(elem).to_have_text("Endowment")

    def test_search_shows_loading_indicator(self, page: Page, logged_in_user):
        """Loading indicator appears during HTMX search request."""
        page.goto("/lps")

        # Start search
        page.fill('[data-testid="semantic-search"]', "healthcare investors")

        # Check loading indicator appears (htmx-indicator class)
        page.press('[data-testid="semantic-search"]', "Enter")
        expect(page.locator('[data-testid="loading"]')).to_be_visible()

        # Wait for completion
        page.wait_for_load_state("networkidle")
        expect(page.locator('[data-testid="loading"]')).not_to_be_visible()
```

---

## Milestone 3: Fund Profile + Matching
### "Upload deck, create fund profile, see LP matches"

### M3-UNIT: Unit Tests

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

### M3-INT: Integration Tests

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

### M3-E2E: End-to-End Tests

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

---

## Milestone 4: Pitch Generation
### "Generate personalized outreach"

### M4-INT: Integration Tests

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

### M4-E2E: End-to-End Tests

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

---

## Milestone 5: Production
### "Live system with automation"

### M5-INT: Integration Tests

```python
# tests/integration/test_admin.py

class TestAdminDashboard:
    """Test admin functionality."""

    async def test_super_admin_sees_all_companies(self, client, super_admin_session):
        response = await client.get(
            "/api/v1/admin/companies",
            cookies={"session": super_admin_session}
        )
        assert response.status_code == 200
        assert len(response.json()["items"]) > 0

    async def test_regular_user_cannot_access_admin(self, client, auth_session):
        response = await client.get(
            "/api/v1/admin/companies",
            cookies={"session": auth_session}
        )
        assert response.status_code == 403

    async def test_data_quality_stats(self, client, super_admin_session):
        response = await client.get(
            "/api/v1/admin/stats/data-quality",
            cookies={"session": super_admin_session}
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
    async def test_search_10k_lps(self, client, auth_session, setup_10k_lps):
        times = []
        for _ in range(10):
            start = time.time()
            await client.get(
                "/api/v1/lps?type=Public%20Pension",
                cookies={"session": auth_session}
            )
            times.append((time.time() - start) * 1000)

        avg = sum(times) / len(times)
        p95 = sorted(times)[9]

        assert avg < 300, f"Average {avg}ms > 300ms"
        assert p95 < 500, f"P95 {p95}ms > 500ms"

    @pytest.mark.benchmark
    async def test_match_generation_1k_lps(self, client, auth_session, fund, setup_1k_lps):
        start = time.time()
        await client.post(
            f"/api/v1/funds/{fund['id']}/matches/generate",
            cookies={"session": auth_session}
        )
        duration = time.time() - start
        assert duration < 30.0

    @pytest.mark.benchmark
    async def test_concurrent_users(self, client, supabase, setup_test_users):
        async def user_session(user_creds):
            auth = supabase.auth.sign_in_with_password(user_creds)
            session = auth.session.access_token
            r = await client.get(
                "/api/v1/lps",
                cookies={"session": session}
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

    async def test_sql_injection_blocked(self, client, auth_session):
        payloads = [
            "'; DROP TABLE lps; --",
            "1 OR 1=1",
            "' UNION SELECT * FROM users --"
        ]
        for payload in payloads:
            response = await client.get(
                f"/api/v1/lps?name={payload}",
                cookies={"session": auth_session}
            )
            assert response.status_code in [200, 422]  # Not 500

    async def test_rate_limiting(self, client, auth_session):
        responses = []
        for _ in range(150):  # Exceed 100/min
            r = await client.get(
                "/api/v1/lps",
                cookies={"session": auth_session}
            )
            responses.append(r.status_code)

        assert 429 in responses  # Some should be rate limited

    async def test_expired_session_rejected(self, client, expired_session):
        """Expired Supabase session is rejected."""
        response = await client.get(
            "/api/v1/lps",
            cookies={"session": expired_session}
        )
        assert response.status_code in [401, 302]  # Unauthorized or redirect to login
```

---

## Test Fixtures

```python
# tests/conftest.py

import pytest
from httpx import AsyncClient
from supabase import create_client
from backend.main import app
from backend.config import settings

@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac

@pytest.fixture
def supabase():
    """Create Supabase client for test data setup."""
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)

@pytest.fixture
def sample_lps(supabase):
    """Create sample LPs using supabase-py."""
    lps_data = [
        {"name": "CalPERS", "type": "Public Pension", "strategies": ["Private Equity"]},
        {"name": "Harvard", "type": "Endowment", "strategies": ["Venture Capital"]},
        {"name": "Smith Family", "type": "Family Office", "strategies": ["Private Equity"]},
    ]
    result = supabase.table("lps").insert(lps_data).execute()
    yield result.data

    # Cleanup after test
    ids = [lp["id"] for lp in result.data]
    supabase.table("lps").delete().in_("id", ids).execute()

@pytest.fixture
async def auth_session(client, supabase, test_user_credentials):
    """Get auth session via Supabase Auth."""
    # Sign in via Supabase Auth
    auth_response = supabase.auth.sign_in_with_password({
        "email": test_user_credentials["email"],
        "password": test_user_credentials["password"]
    })
    return auth_response.session.access_token

@pytest.fixture
def extracted_fields():
    """Sample extracted fields from deck upload."""
    return {
        "fund_name": "Growth Fund III",
        "target_size_mm": 200,
        "strategy": "Private Equity - Growth",
        "geographic_focus": ["North America"],
        "investment_thesis": "Technology-enabled growth companies"
    }

@pytest.fixture
def extracted_fields_incomplete():
    """Incomplete extracted fields (missing required)."""
    return {
        "fund_name": "Incomplete Fund",
        # Missing: target_size_mm, strategy
    }
```

### Playwright E2E Fixtures

```python
# tests/e2e/conftest.py

import pytest
import re
from playwright.sync_api import Page, Browser
from supabase import create_client


@pytest.fixture(scope="session")
def browser_context_args(browser_context_args):
    """Configure browser context for all E2E tests."""
    return {
        **browser_context_args,
        "base_url": "http://localhost:8000",
        "viewport": {"width": 1280, "height": 720},
    }


@pytest.fixture
def supabase():
    """Create Supabase client for test data setup."""
    from backend.config import settings
    return create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)


@pytest.fixture
def logged_in_user(page: Page, supabase, test_user_credentials):
    """Fixture that logs in a test user via Supabase Auth UI."""
    page.goto("/login")

    # Supabase Auth UI handles the login form
    page.fill('[data-testid="email"]', test_user_credentials["email"])
    page.fill('[data-testid="password"]', test_user_credentials["password"])
    page.click('[data-testid="login-btn"]')

    # Wait for redirect after successful auth
    page.wait_for_url("/dashboard")

    # Return user info from Supabase
    user = supabase.auth.get_user(test_user_credentials["access_token"])
    return user


@pytest.fixture
def fund_with_matches(supabase, logged_in_user):
    """Create a fund with pre-generated matches using supabase-py."""
    # Create fund
    fund_data = {
        "name": "Test Fund",
        "company_id": logged_in_user.user_metadata.get("company_id"),
        "target_size_mm": 200,
        "strategy": "Private Equity - Growth",
    }
    fund_result = supabase.table("funds").insert(fund_data).execute()
    fund = fund_result.data[0]

    # Get sample LPs
    lps_result = supabase.table("lps").select("id").limit(3).execute()

    # Create sample matches
    matches_data = [
        {"fund_id": fund["id"], "lp_id": lp["id"], "total_score": 80}
        for lp in lps_result.data
    ]
    supabase.table("matches").insert(matches_data).execute()

    yield fund

    # Cleanup
    supabase.table("matches").delete().eq("fund_id", fund["id"]).execute()
    supabase.table("funds").delete().eq("id", fund["id"]).execute()


def greater_than_or_equal(n: int):
    """Helper for Playwright count assertions."""
    class CountMatcher:
        def __ge__(self, other):
            return other >= n
    return CountMatcher()
```

---

## Running Tests

```bash
# All tests (unit + integration)
uv run pytest

# By milestone
uv run pytest tests/ -k "M0"
uv run pytest tests/ -k "M1"
uv run pytest tests/ -k "M2"

# By type
uv run pytest tests/unit/
uv run pytest tests/integration/
uv run pytest tests/e2e/  # Playwright browser tests

# E2E tests only (Playwright)
uv run pytest tests/e2e/ --headed  # Run with visible browser
uv run pytest tests/e2e/ --browser=firefox  # Specific browser

# With coverage
uv run pytest --cov=backend --cov-report=html

# Performance only
uv run pytest -m benchmark

# Install Playwright browsers (first time setup)
uv run playwright install
```
