"""Pytest configuration and fixtures.

This module provides test fixtures for the LPxGP application.
Fixtures follow BDD/Gherkin patterns from docs/prd/tests/*.feature.md
"""

import os
from typing import Any
from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from src.main import app


# =============================================================================
# Core Application Fixtures
# =============================================================================


@pytest.fixture
def client():
    """Create a test client for the FastAPI app.

    Provides a TestClient instance for making HTTP requests to the app.
    This is the primary fixture for testing endpoints.

    By default, mocks get_db() to return None so tests don't hit real database.
    Use client_with_db fixture when you need mocked database data.
    """
    with patch("src.main.get_db", return_value=None):
        yield TestClient(app)


@pytest.fixture
def client_with_db(mock_db_connection):
    """Create a test client with mocked database connection.

    Use this fixture when testing endpoints that require database access.
    """
    with patch("src.main.get_db", return_value=mock_db_connection):
        yield TestClient(app)


# =============================================================================
# Database/psycopg Fixtures
# =============================================================================


@pytest.fixture
def mock_db_connection():
    """Create a mock psycopg database connection for testing.

    Returns a MagicMock that simulates psycopg connection behavior.
    Use this to test database interactions without actual DB connection.
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
def mock_db_with_data(sample_organizations, sample_funds, sample_lp_profiles, sample_matches):
    """Database connection with pre-configured test data.

    Returns a mock that returns sample data when queried.
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
def sample_organizations():
    """Sample organization data for testing.

    Includes GP and LP organizations matching seed data patterns.
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
def sample_funds():
    """Sample fund data for testing."""
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
def sample_lp_profiles():
    """Sample LP profile data for testing."""
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
def sample_matches():
    """Sample fund-LP match data for testing."""
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
def sample_pipeline_statuses():
    """Sample pipeline status data for testing."""
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
def clean_env():
    """Fixture that provides a clean environment without Supabase config.

    Removes Supabase environment variables to test unconfigured state.
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
def production_env():
    """Fixture that sets production environment configuration."""
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
def sql_injection_payloads():
    """Common SQL injection payloads for security testing.

    Based on Gherkin scenario: Sanitize SQL injection in name
    """
    return [
        "'; DROP TABLE organizations; --",
        "' OR '1'='1",
        "'; DELETE FROM funds; --",
        "1; UPDATE users SET role='admin' WHERE '1'='1",
        "' UNION SELECT * FROM users; --",
    ]


@pytest.fixture
def xss_payloads():
    """Common XSS payloads for security testing.

    Based on Gherkin scenario: Sanitize XSS in name
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
def unicode_test_strings():
    """Unicode strings for internationalization testing.

    Based on Gherkin scenario: Handle unicode in LP name
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
def emoji_test_strings():
    """Emoji strings for testing.

    Based on Gherkin scenario: Handle emojis in notes
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
def invalid_email_formats():
    """Invalid email formats for validation testing.

    Based on Gherkin scenario: Reject invalid email formats (variations)
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
def valid_email_formats():
    """Valid email formats including edge cases.

    Based on Gherkin scenario: Accept valid email edge cases
    """
    return [
        "user+tag@example.com",
        "user.name@subdomain.example.com",
        "user@example.co.uk",
        "test@test.io",
    ]


@pytest.fixture
def invalid_phone_formats():
    """Invalid phone number formats for validation testing."""
    return [
        "abc123",
        "12345",
        "phone",
        "",
    ]


@pytest.fixture
def valid_phone_formats():
    """Valid phone number formats.

    Based on Gherkin scenario: Handle international phone formats
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
def valid_csv_content():
    """Valid CSV content for import testing."""
    return """name,type,aum_bn,headquarters
CalPERS,Public Pension,450,Sacramento
Yale Endowment,Endowment,41.4,New Haven
Stanford Endowment,Endowment,37.8,Stanford"""


@pytest.fixture
def malformed_csv_content():
    """Malformed CSV content for error testing.

    Based on Gherkin scenario: Reject malformed CSV
    """
    return """name,type,aum_bn
CalPERS,Public Pension,450,Extra Column
Yale Endowment"""


@pytest.fixture
def csv_with_formula_injection():
    """CSV with potential formula injection.

    Based on Gherkin scenario: Scan for formula injection
    """
    return """name,type,notes
CalPERS,Public Pension,=1+1
Evil LP,Family Office,+cmd|' /C calc'!A0
Another LP,Endowment,-2+2"""
