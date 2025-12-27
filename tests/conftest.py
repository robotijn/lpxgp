"""Pytest configuration and fixtures.

This module provides test fixtures for the LPxGP application.
Fixtures follow BDD/Gherkin patterns from docs/prd/tests/*.feature.md

Fixtures:
    client: Test client without database connection.
    client_with_db: Test client with mocked database.
    mock_db_connection: Mock psycopg connection.
    sample_*: Sample data for testing.
    sql_injection_payloads: Security test payloads.
    xss_payloads: XSS test payloads.
    unicode_test_strings: Internationalization test data.

Performance optimizations:
    - Session-scoped browser contexts for reusing login sessions
    - xdist-safe fixtures with worker_id awareness
    - Helper functions for fast element-specific waits
"""

from __future__ import annotations

import asyncio
import os
from collections.abc import Generator
from typing import TYPE_CHECKING, Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app
from src.preferences import _user_preferences
from src.shortlists import _shortlists


# =============================================================================
# Event Loop Isolation for pytest-asyncio tests
# =============================================================================


@pytest.fixture(scope="function")
def event_loop():
    """Create a new event loop for each test function.

    This prevents event loop pollution between Playwright tests
    and pytest-asyncio tests.
    """
    # Get current loop if any
    try:
        old_loop = asyncio.get_event_loop()
        if old_loop.is_running():
            # Don't interfere with running loop (e.g., from Playwright)
            yield old_loop
            return
    except RuntimeError:
        pass

    # Create a fresh event loop
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    yield loop
    loop.close()

if TYPE_CHECKING:
    from playwright.sync_api import BrowserContext, Page


# =============================================================================
# Browser Test Helpers
# =============================================================================


def wait_for_page_ready(page: Page, selector: str | None = None, timeout: int = 5000) -> None:
    """Fast page ready check - avoids slow networkidle waits.

    Args:
        page: Playwright page instance.
        selector: Optional CSS selector to wait for.
        timeout: Maximum wait time in milliseconds.
    """
    page.wait_for_load_state("domcontentloaded")
    if selector:
        page.wait_for_selector(selector, timeout=timeout)


# =============================================================================
# Session-Scoped Browser Fixtures (Performance Optimization)
# =============================================================================


@pytest.fixture(scope="session")
def browser_base_url(worker_id: str) -> str:
    """Get base URL for browser tests, supporting xdist workers.

    When running with pytest-xdist, each worker could potentially
    use a different port. For now, all workers share port 8000.

    Args:
        worker_id: xdist worker identifier (e.g., 'master', 'gw0', 'gw1').

    Returns:
        Base URL for the test server.
    """
    # Future: Support multi-port with: 8000 + int(worker_id[2:]) if worker_id != "master"
    return "http://localhost:8000"


@pytest.fixture(scope="session")
def gp_session_context(browser: Any, browser_base_url: str) -> Generator[BrowserContext, None, None]:
    """Session-scoped GP login context - login once, reuse across tests.

    This dramatically speeds up browser tests by avoiding repeated logins.

    Args:
        browser: Playwright browser instance.
        browser_base_url: Base URL for the test server.

    Yields:
        BrowserContext with GP user logged in.
    """
    context = browser.new_context()
    page = context.new_page()

    # Login once for the session
    page.goto(f"{browser_base_url}/login")
    page.fill('input[name="email"]', "gp@demo.com")
    page.fill('input[name="password"]', "demo123")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{browser_base_url}/dashboard", timeout=10000)
    page.close()  # Close setup page, keep context with cookies

    yield context
    context.close()


@pytest.fixture(scope="session")
def lp_session_context(browser: Any, browser_base_url: str) -> Generator[BrowserContext, None, None]:
    """Session-scoped LP login context.

    Args:
        browser: Playwright browser instance.
        browser_base_url: Base URL for the test server.

    Yields:
        BrowserContext with LP user logged in.
    """
    context = browser.new_context()
    page = context.new_page()

    page.goto(f"{browser_base_url}/login")
    page.fill('input[name="email"]', "lp@demo.com")
    page.fill('input[name="password"]', "demo123")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{browser_base_url}/dashboard", timeout=10000)
    page.close()

    yield context
    context.close()


@pytest.fixture(scope="session")
def admin_session_context(browser: Any, browser_base_url: str) -> Generator[BrowserContext, None, None]:
    """Session-scoped admin login context.

    Args:
        browser: Playwright browser instance.
        browser_base_url: Base URL for the test server.

    Yields:
        BrowserContext with admin user logged in.
    """
    context = browser.new_context()
    page = context.new_page()

    page.goto(f"{browser_base_url}/login")
    page.fill('input[name="email"]', "admin@demo.com")
    page.fill('input[name="password"]', "admin123")
    page.click('button[type="submit"]')
    page.wait_for_url(f"{browser_base_url}/dashboard", timeout=10000)
    page.close()

    yield context
    context.close()


@pytest.fixture
def gp_page(gp_session_context: BrowserContext) -> Generator[Page, None, None]:
    """Fresh page within GP session - fast because login is reused.

    Args:
        gp_session_context: Session-scoped GP login context.

    Yields:
        New page within the logged-in GP context.
    """
    page = gp_session_context.new_page()
    yield page
    page.close()


@pytest.fixture
def lp_page(lp_session_context: BrowserContext) -> Generator[Page, None, None]:
    """Fresh page within LP session.

    Args:
        lp_session_context: Session-scoped LP login context.

    Yields:
        New page within the logged-in LP context.
    """
    page = lp_session_context.new_page()
    yield page
    page.close()


@pytest.fixture
def admin_page(admin_session_context: BrowserContext) -> Generator[Page, None, None]:
    """Fresh page within admin session.

    Args:
        admin_session_context: Session-scoped admin login context.

    Yields:
        New page within the logged-in admin context.
    """
    page = admin_session_context.new_page()
    yield page
    page.close()


@pytest.fixture(autouse=True)
def reset_in_memory_state() -> Generator[None, None, None]:
    """Reset in-memory state between tests.

    This fixture runs automatically before each test to ensure
    a clean state for shortlists and user preferences.
    """
    # Clear before test
    _shortlists.clear()
    _user_preferences.clear()

    yield

    # Clear after test
    _shortlists.clear()
    _user_preferences.clear()

# =============================================================================
# Core Application Fixtures
# =============================================================================


@pytest.fixture
def client() -> Generator[TestClient, None, None]:
    """Create a test client for the FastAPI app.

    Provides a TestClient instance for making HTTP requests to the app.
    This is the primary fixture for testing endpoints.

    By default, mocks get_db() to return None so tests don't hit real database.
    Use client_with_db fixture when you need mocked database data.

    Yields:
        TestClient for making requests to the app.
    """
    # Patch get_db at all import locations to ensure no real DB access
    # Only patch modules that actually import get_db
    with (
        patch("src.database.get_db", return_value=None),
        patch("src.utils.get_db", return_value=None),
        # Routers that import from src.database
        patch("src.routers.lps.get_db", return_value=None),
        patch("src.routers.funds.get_db", return_value=None),
        patch("src.routers.pipeline.get_db", return_value=None),
        patch("src.routers.matches.get_db", return_value=None),
        patch("src.routers.gps.get_db", return_value=None),
        patch("src.routers.crm.get_db", return_value=None),
        patch("src.routers.lp_portal.get_db", return_value=None),
        patch("src.routers.insights.get_db", return_value=None),
        patch("src.routers.shortlist.get_db", return_value=None),
        # Routers that import from src.utils
        patch("src.routers.pages.get_db", return_value=None),
        patch("src.routers.admin.get_db", return_value=None),
    ):
        yield TestClient(app)


@pytest.fixture
def client_with_db(mock_db_connection: MagicMock) -> Generator[TestClient, None, None]:
    """Create a test client with mocked database connection.

    Use this fixture when testing endpoints that require database access.

    Args:
        mock_db_connection: Mock database connection fixture.

    Yields:
        TestClient with mocked database.
    """
    # Patch get_db at all import locations with the mock connection
    # Only patch modules that actually import get_db
    with (
        patch("src.database.get_db", return_value=mock_db_connection),
        patch("src.utils.get_db", return_value=mock_db_connection),
        # Routers that import from src.database
        patch("src.routers.lps.get_db", return_value=mock_db_connection),
        patch("src.routers.funds.get_db", return_value=mock_db_connection),
        patch("src.routers.pipeline.get_db", return_value=mock_db_connection),
        patch("src.routers.matches.get_db", return_value=mock_db_connection),
        patch("src.routers.gps.get_db", return_value=mock_db_connection),
        patch("src.routers.crm.get_db", return_value=mock_db_connection),
        patch("src.routers.lp_portal.get_db", return_value=mock_db_connection),
        patch("src.routers.insights.get_db", return_value=mock_db_connection),
        patch("src.routers.shortlist.get_db", return_value=mock_db_connection),
        # Routers that import from src.utils
        patch("src.routers.pages.get_db", return_value=mock_db_connection),
        patch("src.routers.admin.get_db", return_value=mock_db_connection),
    ):
        yield TestClient(app)


# =============================================================================
# Database/psycopg Fixtures
# =============================================================================


@pytest.fixture
def mock_db_connection() -> MagicMock:
    """Create a mock psycopg database connection for testing.

    Returns a MagicMock that simulates psycopg connection behavior.
    Use this to test database interactions without actual DB connection.

    Returns:
        Mock connection with cursor context manager configured.
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # Configure cursor context manager
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    # Default empty results
    mock_cursor.fetchall.return_value = []
    mock_cursor.fetchone.return_value = None

    return mock_conn


@pytest.fixture
def mock_db_with_data(
    sample_organizations: list[dict[str, Any]],
    sample_funds: list[dict[str, Any]],
    sample_lp_profiles: list[dict[str, Any]],
    sample_matches: list[dict[str, Any]],
) -> MagicMock:
    """Database connection with pre-configured test data.

    Returns a mock that returns sample data when queried.

    Args:
        sample_organizations: Sample organization data.
        sample_funds: Sample fund data.
        sample_lp_profiles: Sample LP profile data.
        sample_matches: Sample match data.

    Returns:
        Mock connection configured to return sample data.
    """
    mock_conn = MagicMock()
    mock_cursor = MagicMock()

    # Configure cursor context manager
    mock_conn.cursor.return_value.__enter__ = MagicMock(return_value=mock_cursor)
    mock_conn.cursor.return_value.__exit__ = MagicMock(return_value=False)

    # Return funds for first query, matches for second
    mock_cursor.fetchall.side_effect = [sample_funds, sample_matches]

    return mock_conn


# =============================================================================
# Sample Data Fixtures
# =============================================================================


@pytest.fixture
def sample_organizations() -> list[dict[str, Any]]:
    """Sample organization data for testing.

    Includes GP and LP organizations matching seed data patterns.

    Returns:
        List of organization dictionaries.
    """
    return [
        {
            "id": "c0000001-0000-0000-0000-000000000001",
            "name": "Acme Capital",
            "is_gp": True,
            "is_lp": False,
            "hq_city": "San Francisco",
            "hq_country": "USA",
        },
        {
            "id": "0a000001-0000-0000-0000-000000000001",
            "name": "CalPERS",
            "is_gp": False,
            "is_lp": True,
            "hq_city": "Sacramento",
            "hq_country": "USA",
        },
        {
            "id": "0a000002-0000-0000-0000-000000000002",
            "name": "Yale Endowment",
            "is_gp": False,
            "is_lp": True,
            "hq_city": "New Haven",
            "hq_country": "USA",
        },
    ]


@pytest.fixture
def sample_funds() -> list[dict[str, Any]]:
    """Sample fund data for testing.

    Returns:
        List of fund dictionaries.
    """
    return [
        {
            "id": "0f000001-0000-0000-0000-000000000001",
            "name": "Acme Growth Fund III",
            "manager_org_id": "c0000001-0000-0000-0000-000000000001",
            "status": "fundraising",
            "target_size_mm": 500,
            "vintage_year": 2024,
            "primary_strategy": "growth_equity",
        },
        {
            "id": "0f000002-0000-0000-0000-000000000002",
            "name": "Tech Ventures IV",
            "manager_org_id": "c0000001-0000-0000-0000-000000000001",
            "status": "fundraising",
            "target_size_mm": 250,
            "vintage_year": 2024,
            "primary_strategy": "venture_capital",
        },
    ]


@pytest.fixture
def sample_lp_profiles() -> list[dict[str, Any]]:
    """Sample LP profile data for testing.

    Returns:
        List of LP profile dictionaries.
    """
    return [
        {
            "id": "1a000001-0000-0000-0000-000000000001",
            "org_id": "0a000001-0000-0000-0000-000000000001",
            "lp_type": "public_pension",
            "total_aum_bn": 450.0,
            "pe_allocation_pct": 8.0,
            "check_size_min_mm": 50,
            "check_size_max_mm": 200,
        },
        {
            "id": "1a000002-0000-0000-0000-000000000002",
            "org_id": "0a000002-0000-0000-0000-000000000002",
            "lp_type": "endowment",
            "total_aum_bn": 41.4,
            "pe_allocation_pct": 23.0,
            "check_size_min_mm": 25,
            "check_size_max_mm": 150,
        },
    ]


@pytest.fixture
def sample_matches() -> list[dict[str, Any]]:
    """Sample fund-LP match data for testing.

    Returns:
        List of match dictionaries with scores and AI content.
    """
    return [
        {
            "id": "2a000001-0000-0000-0000-000000000001",
            "fund_id": "0f000001-0000-0000-0000-000000000001",
            "lp_org_id": "0a000001-0000-0000-0000-000000000001",
            "score": 95,
            "score_breakdown": {
                "strategy": 98,
                "geography": 95,
                "size_fit": 92,
                "track_record": 95,
            },
            "explanation": "Excellent strategy alignment with CalPERS PE program.",
            "talking_points": [
                "Strong track record in growth equity",
                "Geographic focus matches LP preferences",
                "Fund size within check size range",
            ],
            "concerns": [
                "First-time fund from this team",
            ],
        },
        {
            "id": "2a000002-0000-0000-0000-000000000002",
            "fund_id": "0f000001-0000-0000-0000-000000000001",
            "lp_org_id": "0a000002-0000-0000-0000-000000000002",
            "score": 88,
            "score_breakdown": {
                "strategy": 90,
                "geography": 85,
                "size_fit": 88,
                "track_record": 89,
            },
            "explanation": "Good fit with Yale's innovation-focused strategy.",
            "talking_points": [
                "Tech-focused approach aligns with Yale priorities",
            ],
            "concerns": [
                "Smaller fund size than typical Yale commitment",
            ],
        },
    ]


@pytest.fixture
def sample_pipeline_statuses() -> list[dict[str, Any]]:
    """Sample pipeline status data for testing.

    Returns:
        List of pipeline status dictionaries.
    """
    return [
        {
            "fund_id": "0f000001-0000-0000-0000-000000000001",
            "lp_org_id": "0a000001-0000-0000-0000-000000000001",
            "pipeline_stage": "initial_contact",
            "interest_level": "warm",
        },
    ]


# =============================================================================
# Configuration Fixtures
# =============================================================================


@pytest.fixture
def clean_env() -> Generator[None, None, None]:
    """Fixture that provides a clean environment without Supabase config.

    Removes Supabase environment variables to test unconfigured state.

    Yields:
        None, after removing Supabase env vars.
    """
    env_vars = [
        "SUPABASE_URL",
        "SUPABASE_ANON_KEY",
        "SUPABASE_SERVICE_ROLE_KEY",
    ]
    original_values = {}

    # Store and remove env vars
    for var in env_vars:
        original_values[var] = os.environ.pop(var, None)

    yield

    # Restore original values
    for var, value in original_values.items():
        if value is not None:
            os.environ[var] = value


@pytest.fixture
def production_env() -> Generator[None, None, None]:
    """Fixture that sets production environment configuration.

    Yields:
        None, after setting ENVIRONMENT to 'production'.
    """
    original_env = os.environ.get("ENVIRONMENT")
    os.environ["ENVIRONMENT"] = "production"

    yield

    if original_env is not None:
        os.environ["ENVIRONMENT"] = original_env
    else:
        os.environ.pop("ENVIRONMENT", None)


# =============================================================================
# Security Test Fixtures
# =============================================================================


@pytest.fixture
def sql_injection_payloads() -> list[str]:
    """Common SQL injection payloads for security testing.

    Based on Gherkin scenario: Sanitize SQL injection in name

    Returns:
        List of SQL injection attack strings.
    """
    return [
        "'; DROP TABLE organizations; --",
        "' OR '1'='1",
        "'; DELETE FROM funds; --",
        "1; UPDATE users SET role='admin' WHERE '1'='1",
        "' UNION SELECT * FROM users; --",
    ]


@pytest.fixture
def xss_payloads() -> list[str]:
    """Common XSS payloads for security testing.

    Based on Gherkin scenario: Sanitize XSS in name

    Returns:
        List of XSS attack strings.
    """
    return [
        "<script>alert('xss')</script>",
        "<img src=x onerror=alert('xss')>",
        "javascript:alert('xss')",
        "<svg onload=alert('xss')>",
        "'\"><script>alert('xss')</script>",
    ]


# =============================================================================
# Unicode and Edge Case Fixtures
# =============================================================================


@pytest.fixture
def unicode_test_strings() -> list[str]:
    """Unicode strings for internationalization testing.

    Based on Gherkin scenario: Handle unicode in LP name

    Returns:
        List of Unicode strings from various languages.
    """
    return [
        "北京投资基金",  # Chinese
        "東京ファンド",  # Japanese
        "Société Générale",  # French
        "München Capital",  # German
        "مؤسسة أبوظبي",  # Arabic
        "Привет Капитал",  # Russian
    ]


@pytest.fixture
def emoji_test_strings() -> list[str]:
    """Emoji strings for testing.

    Based on Gherkin scenario: Handle emojis in notes

    Returns:
        List of strings containing emojis.
    """
    return [
        "Great partner 👍🏼",
        "Top tier LP 🌟",
        "Excellent track record 📈",
        "⚠️ Needs follow-up",
    ]


# =============================================================================
# Validation Test Fixtures
# =============================================================================


@pytest.fixture
def invalid_email_formats() -> list[str]:
    """Invalid email formats for validation testing.

    Based on Gherkin scenario: Reject invalid email formats (variations)

    Returns:
        List of invalid email address strings.
    """
    return [
        "@example.com",
        "user@",
        "user@.com",
        "user space@example.com",
        "user@example",
        "not-a-valid-email",
        "",
        "   ",
    ]


@pytest.fixture
def valid_email_formats() -> list[str]:
    """Valid email formats including edge cases.

    Based on Gherkin scenario: Accept valid email edge cases

    Returns:
        List of valid email address strings.
    """
    return [
        "user+tag@example.com",
        "user.name@subdomain.example.com",
        "user@example.co.uk",
        "test@test.io",
    ]


@pytest.fixture
def invalid_phone_formats() -> list[str]:
    """Invalid phone number formats for validation testing.

    Returns:
        List of invalid phone number strings.
    """
    return [
        "abc123",
        "12345",
        "phone",
        "",
    ]


@pytest.fixture
def valid_phone_formats() -> list[str]:
    """Valid phone number formats.

    Based on Gherkin scenario: Handle international phone formats

    Returns:
        List of valid international phone number strings.
    """
    return [
        "+1 (555) 123-4567",
        "+44 20 7946 0958",
        "+86 21 1234 5678",
    ]


# =============================================================================
# File Upload Test Fixtures
# =============================================================================


@pytest.fixture
def valid_csv_content() -> str:
    """Valid CSV content for import testing.

    Returns:
        Well-formed CSV string with LP data.
    """
    return """name,type,aum_bn,headquarters
CalPERS,Public Pension,450,Sacramento
Yale Endowment,Endowment,41.4,New Haven
Stanford Endowment,Endowment,37.8,Stanford"""


@pytest.fixture
def malformed_csv_content() -> str:
    """Malformed CSV content for error testing.

    Based on Gherkin scenario: Reject malformed CSV

    Returns:
        Malformed CSV string with inconsistent columns.
    """
    return """name,type,aum_bn
CalPERS,Public Pension,450,Extra Column
Yale Endowment"""


@pytest.fixture
def csv_with_formula_injection() -> str:
    """CSV with potential formula injection.

    Based on Gherkin scenario: Scan for formula injection

    Returns:
        CSV string with Excel formula injection attempts.
    """
    return """name,type,notes
CalPERS,Public Pension,=1+1
Evil LP,Family Office,+cmd|' /C calc'!A0
Another LP,Endowment,-2+2"""


# =============================================================================
# Authenticated Client Fixture
# =============================================================================


@pytest.fixture
def authenticated_client() -> Generator[TestClient, None, None]:
    """Create a test client with mocked authentication.

    Use this fixture when testing endpoints that require authentication
    (e.g., /funds, /lps, /matches).

    Yields:
        TestClient that appears authenticated.
    """
    mock_user = {
        "id": "test-user-id",
        "email": "test@example.com",
        "role": "gp_user",
        "org_id": "c0000001-0000-0000-0000-000000000001",
    }
    with patch("src.main.get_db", return_value=None):
        with patch("src.auth.get_current_user", return_value=mock_user):
            yield TestClient(app)


# =============================================================================
# Database Reset Fixtures (for integration tests with real database)
# =============================================================================


@pytest.fixture(scope="session")
def reset_test_database_once():
    """Reset TEST database once at the start of the test session.

    SAFETY: Only operates on TEST_DATABASE_URL, never production.

    Use this for integration tests that need a clean database with seed data.
    Only runs if TEST_DATABASE_URL is configured.
    """
    import subprocess
    import sys
    from pathlib import Path

    scripts_dir = Path(__file__).parent.parent / "scripts"
    reset_script = scripts_dir / "reset_database.py"

    if not reset_script.exists():
        pytest.skip("reset_database.py not found")

    try:
        # Check if TEST database is configured
        from src.config import get_settings
        settings = get_settings()

        if not settings.test_database_url:
            pytest.skip("TEST_DATABASE_URL not configured - tests use test database only")

        # Verify we're not accidentally targeting production
        if settings.is_production:
            pytest.fail("REFUSING to reset database in production environment!")

        # Reset with demo data
        result = subprocess.run(
            [sys.executable, str(reset_script), "--demo"],
            capture_output=True,
            text=True,
            timeout=60,
        )
        if result.returncode != 0:
            print(f"Test database reset failed: {result.stderr}")
            pytest.skip(f"Test database reset failed: {result.stderr}")

        yield True

    except Exception as e:
        pytest.skip(f"Test database reset not available: {e}")


@pytest.fixture
def test_database(reset_test_database_once):
    """Get a connection to the TEST database.

    SAFETY: Only connects to TEST_DATABASE_URL, never production.

    Depends on reset_test_database_once to ensure database is reset at session start.
    Individual tests can use this to verify database is available.
    """
    from src.config import get_settings

    settings = get_settings()
    if not settings.test_database_url:
        pytest.skip("TEST_DATABASE_URL not configured")

    import psycopg2
    conn = psycopg2.connect(settings.test_database_url)
    yield conn
    conn.close()


# Alias for backwards compatibility
@pytest.fixture
def fresh_database(test_database):
    """Alias for test_database fixture (backwards compatibility)."""
    yield test_database
