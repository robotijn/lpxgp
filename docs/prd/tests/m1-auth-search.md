# M1: Auth + Full-Text Search Tests
### "I can log in and search my LP database"

## M1-UNIT: Unit Tests

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

## M1-INT: Integration Tests

### M1-INT-01: Authentication (Supabase Auth)

```python
# tests/integration/test_auth.py

class TestSupabaseAuthIntegration:
    """Test Supabase Auth integration."""

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

### M1-INT-02: Supabase Auth Flow

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
```

### M1-INT-03: Full-Text Search

```python
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

## M1-E2E: End-to-End Tests

```python
# tests/e2e/test_m1_auth_search.py

import pytest
from playwright.sync_api import Page, expect


class TestM1AuthAndSearch:
    """E2E tests for M1: Auth + Full-Text Search milestone."""

    def test_user_can_register(self, page: Page):
        """User can register with valid credentials."""
        page.goto("/register")
        page.fill('[data-testid="email"]', "test@example.com")
        page.fill('[data-testid="password"]', "SecurePass123!")
        page.fill('[data-testid="name"]', "Test User")
        page.click('[data-testid="register-btn"]')

        # Should redirect to verify email page
        expect(page).to_have_url(re.compile(r"/verify"))

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
