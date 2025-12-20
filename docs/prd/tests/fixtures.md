# Test Fixtures

## Core Fixtures

```python
# tests/conftest.py

import pytest
from httpx import AsyncClient
from supabase import create_client
from src.main import app
from src.config import settings

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

## Playwright E2E Fixtures

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
    from src.config import settings
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
