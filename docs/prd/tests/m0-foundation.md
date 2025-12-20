# M0: Foundation Tests
### "Data is imported and clean"

## M0-UNIT: Unit Tests

### M0-UNIT-01: Data Cleaning Functions

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

### M0-UNIT-02: Pydantic Models

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

## M0-INT: Integration Tests

### M0-INT-01: LP Search (Basic Filters)

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

### M0-INT-02: Multi-tenancy

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

## M0-E2E: End-to-End Tests

```python
# tests/e2e/test_m0_foundation.py

import pytest
from playwright.sync_api import Page, expect


class TestM0Foundation:
    """E2E tests for M0: Foundation milestone."""

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
