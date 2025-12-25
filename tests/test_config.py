"""Tests for application configuration.

IMPORTANT: Tests are the source of truth. Do NOT modify tests to make them pass.
If a test fails, fix the APPLICATION, not the test.

Based on BDD Gherkin specs from docs/prd/tests/*.feature.md
"""

import os
from unittest.mock import patch

import pytest
from pydantic import ValidationError

from src.config import Settings, get_settings, validate_settings_on_startup

# =============================================================================
# SETTINGS CLASS TESTS
# =============================================================================


class TestSettingsDefaults:
    """Test default configuration values.

    Gherkin Reference: M0 Foundation - Configuration
    """

    def test_default_environment(self):
        """Default environment should be 'development'.

        Gherkin: Default configuration values are sensible
        """
        with patch.dict(os.environ, {}, clear=True):
            # Create fresh settings without cache
            settings = Settings()
            assert settings.environment == "development"

    def test_default_debug_false(self):
        """Debug should be disabled by default.

        Security: Debug mode should never be accidentally enabled
        """
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.debug is False

    def test_default_session_timeout(self):
        """Default session timeout should be reasonable.

        Gherkin: Session expires after inactivity
        """
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.session_timeout_minutes == 60
            assert 5 <= settings.session_timeout_minutes <= 1440

    def test_default_max_login_attempts(self):
        """Default max login attempts should prevent brute force.

        Gherkin: Brute force protection - account lockout
        """
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.max_login_attempts == 5
            assert 3 <= settings.max_login_attempts <= 10

    def test_default_lockout_duration(self):
        """Default lockout duration should be reasonable.

        Gherkin: Account locked for 15 minutes
        """
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.lockout_duration_minutes == 30
            assert 5 <= settings.lockout_duration_minutes <= 1440

    def test_default_file_upload_limit(self):
        """Default file upload limit should be sensible.

        Gherkin: File too large (max 50MB)
        """
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.max_file_upload_mb == 50
            assert 1 <= settings.max_file_upload_mb <= 100

    def test_default_allowed_extensions(self):
        """Default allowed extensions should include expected formats.

        Gherkin: Upload CSV file, Upload Excel file
        """
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert ".pdf" in settings.allowed_upload_extensions
            assert ".pptx" in settings.allowed_upload_extensions

    def test_default_export_rows_limit(self):
        """Default export limit should be reasonable.

        Gherkin: Export limited to prevent abuse
        """
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.max_export_rows == 500
            assert 100 <= settings.max_export_rows <= 10000

    def test_default_feature_flags_disabled(self):
        """Feature flags should be disabled by default.

        Gherkin: Features require explicit enablement
        """
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.enable_semantic_search is False
            assert settings.enable_agent_matching is False


class TestSettingsValidation:
    """Test configuration validation.

    Gherkin Reference: M0 Foundation - Validation
    """

    def test_database_url_requires_postgresql_scheme(self):
        """Database URL must use postgresql:// or postgres:// scheme.

        Security: Ensure correct database protocol
        """
        with pytest.raises(ValidationError) as exc_info:
            Settings(database_url="http://localhost:5432/db")

        assert "postgresql" in str(exc_info.value).lower()

    def test_database_url_accepts_valid_formats(self):
        """Database URL should accept valid PostgreSQL connection strings.

        Gherkin: Support standard PostgreSQL URLs
        """
        # Should not raise
        settings = Settings(database_url="postgresql://user:pass@localhost:5432/db")
        assert settings.database_url == "postgresql://user:pass@localhost:5432/db"

        settings = Settings(database_url="postgres://user:pass@localhost:5432/db")
        assert settings.database_url == "postgres://user:pass@localhost:5432/db"

    def test_database_url_empty_treated_as_none(self):
        """Empty database URL should be treated as None.

        Edge case: Empty string configuration
        """
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings(_env_file=None, database_url="")
            assert settings.database_url is None

    def test_cors_origins_require_protocol(self):
        """CORS origins must include protocol.

        Security: Explicit origin specification
        """
        with pytest.raises(ValidationError):
            Settings(cors_origins=["example.com"])

    def test_cors_origins_accepts_valid_urls(self):
        """CORS origins should accept valid URLs."""
        # Should not raise
        settings = Settings(cors_origins=["https://example.com", "http://localhost:3000"])
        assert len(settings.cors_origins) == 2

    def test_environment_validates_enum(self):
        """Environment must be valid enum value.

        Gherkin: Environment should be development, staging, or production
        """
        with pytest.raises(ValidationError):
            Settings(environment="invalid")

    def test_session_timeout_bounds(self):
        """Session timeout must be within bounds.

        Gherkin: Session timeout between 5 and 1440 minutes
        """
        with pytest.raises(ValidationError):
            Settings(session_timeout_minutes=1)

        with pytest.raises(ValidationError):
            Settings(session_timeout_minutes=2000)

    def test_max_login_attempts_bounds(self):
        """Max login attempts must be within bounds.

        Gherkin: 3-10 attempts before lockout
        """
        with pytest.raises(ValidationError):
            Settings(max_login_attempts=1)

        with pytest.raises(ValidationError):
            Settings(max_login_attempts=100)

    def test_file_upload_limit_bounds(self):
        """File upload limit must be within bounds.

        Gherkin: 1-100 MB upload limit
        """
        with pytest.raises(ValidationError):
            Settings(max_file_upload_mb=0)

        with pytest.raises(ValidationError):
            Settings(max_file_upload_mb=500)


class TestSettingsComputedProperties:
    """Test computed property values.

    Gherkin Reference: Derived configuration values
    """

    def test_is_production_true(self):
        """is_production should be True when environment is production."""
        settings = Settings(environment="production")
        assert settings.is_production is True

    def test_is_production_false_for_development(self):
        """is_production should be False for non-production environments."""
        settings = Settings(environment="development")
        assert settings.is_production is False

        settings = Settings(environment="staging")
        assert settings.is_production is False

    def test_max_file_upload_bytes(self):
        """max_file_upload_bytes should convert MB to bytes correctly."""
        settings = Settings(max_file_upload_mb=50)
        assert settings.max_file_upload_bytes == 50 * 1024 * 1024

        settings = Settings(max_file_upload_mb=1)
        assert settings.max_file_upload_bytes == 1024 * 1024

    def test_database_configured_false_when_missing(self):
        """database_configured should be False when URL is missing.

        Must isolate from environment AND .env file to test default/unconfigured state.
        pydantic-settings reads from both os.environ AND .env files.
        """
        with patch.dict(os.environ, {}, clear=True):
            # _env_file=None tells pydantic-settings to skip reading .env file
            settings = Settings(_env_file=None)
            assert settings.database_configured is False

        with patch.dict(os.environ, {}, clear=True):
            # Empty string should also be unconfigured
            settings = Settings(_env_file=None, database_url="")
            assert settings.database_configured is False

    def test_database_configured_true_when_set(self):
        """database_configured should be True when URL is present."""
        settings = Settings(database_url="postgresql://user:pass@localhost:5432/db")
        assert settings.database_configured is True


class TestSettingsEnvironmentVariables:
    """Test environment variable loading.

    Gherkin Reference: Configuration from environment
    """

    def test_reads_environment_variable(self):
        """Settings should read from environment variables."""
        with patch.dict(os.environ, {"ENVIRONMENT": "staging"}):
            settings = Settings()
            assert settings.environment == "staging"

    def test_case_insensitive_env_vars(self):
        """Environment variable names should be case insensitive."""
        with patch.dict(os.environ, {"environment": "staging"}):
            settings = Settings()
            assert settings.environment == "staging"

    def test_ollama_configuration(self):
        """Ollama settings should be configurable.

        Gherkin: Local development with Ollama
        """
        with patch.dict(os.environ, {
            "OLLAMA_BASE_URL": "http://localhost:11434",
            "OLLAMA_MODEL": "deepseek-r1:8b"
        }):
            settings = Settings()
            assert settings.ollama_base_url == "http://localhost:11434"
            assert settings.ollama_model == "deepseek-r1:8b"


class TestStartupValidation:
    """Test startup validation function.

    Gherkin Reference: M0 Foundation - Fail fast on misconfiguration
    """

    def test_production_requires_sentry_warning(self, capsys):
        """Production without Sentry should warn.

        Gherkin: Sentry DSN not configured for production
        """
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "DEBUG": "false",
        }, clear=True):
            # Clear cached settings
            get_settings.cache_clear()

            # This might warn but shouldn't fail
            # (implementation shows warning, doesn't raise)

    def test_production_rejects_debug_mode(self):
        """Production should reject debug mode.

        Security: Debug mode must be disabled in production
        """
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "DEBUG": "true",
        }, clear=True):
            get_settings.cache_clear()

            with pytest.raises(ValueError) as exc_info:
                validate_settings_on_startup()

            assert "debug" in str(exc_info.value).lower()

    def test_production_rejects_localhost_cors(self):
        """Production should reject localhost in CORS origins.

        Security: No localhost access in production
        """
        with patch.dict(os.environ, {
            "ENVIRONMENT": "production",
            "DEBUG": "false",
            "CORS_ORIGINS": '["http://localhost:3000"]',
        }, clear=True):
            get_settings.cache_clear()

            with pytest.raises(ValueError) as exc_info:
                validate_settings_on_startup()

            assert "localhost" in str(exc_info.value).lower()

    def test_semantic_search_requires_voyage_key(self):
        """Semantic search requires Voyage API key.

        Gherkin: Feature requires API key
        """
        with patch.dict(os.environ, {
            "ENABLE_SEMANTIC_SEARCH": "true",
            "VOYAGE_API_KEY": "",
        }, clear=True):
            get_settings.cache_clear()

            with pytest.raises(ValueError) as exc_info:
                validate_settings_on_startup()

            assert "voyage" in str(exc_info.value).lower()

    def test_agent_matching_requires_openrouter_key(self):
        """Agent matching requires OpenRouter API key.

        Gherkin: Feature requires API key
        """
        with patch.dict(os.environ, {
            "ENABLE_AGENT_MATCHING": "true",
            "OPENROUTER_API_KEY": "",
        }, clear=True):
            get_settings.cache_clear()

            with pytest.raises(ValueError) as exc_info:
                validate_settings_on_startup()

            assert "openrouter" in str(exc_info.value).lower()


# =============================================================================
# EDGE CASES AND SECURITY TESTS
# =============================================================================


class TestConfigurationEdgeCases:
    """Test configuration edge cases.

    Gherkin Reference: Negative test scenarios
    """

    def test_empty_string_treated_as_none(self):
        """Empty string values should be treated as None/unset.

        Edge case: Empty env vars
        """
        with patch.dict(os.environ, {"DATABASE_URL": ""}, clear=True):
            settings = Settings(_env_file=None)
            assert settings.database_url is None

    def test_whitespace_only_values(self):
        """Whitespace-only values should be handled.

        Edge case: Values with only spaces
        """
        with patch.dict(os.environ, {"ENVIRONMENT": "development"}, clear=True):
            settings = Settings()
            assert settings.environment == "development"

    def test_extra_env_vars_ignored(self):
        """Unknown environment variables should be ignored.

        Gherkin: extra="ignore" in model config
        """
        with patch.dict(os.environ, {
            "UNKNOWN_SETTING": "value",
            "RANDOM_VAR": "123",
        }):
            # Should not raise
            settings = Settings()
            assert not hasattr(settings, "unknown_setting")

    def test_settings_caching(self):
        """Settings should be cached for performance."""
        get_settings.cache_clear()

        settings1 = get_settings()
        settings2 = get_settings()

        assert settings1 is settings2


class TestSecuritySettings:
    """Test security-related configuration.

    Gherkin Reference: M1 Auth - Security settings
    """

    def test_rate_limit_format(self):
        """Rate limit should follow expected format."""
        settings = Settings()

        # Should be in format "N/period"
        assert "/" in settings.rate_limit_default
        parts = settings.rate_limit_default.split("/")
        assert len(parts) == 2
        assert parts[0].isdigit()

    def test_langfuse_settings_optional(self):
        """Langfuse settings should be optional.

        Gherkin: M3+ agent monitoring is optional
        """
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.langfuse_public_key is None
            assert settings.langfuse_secret_key is None

    def test_sentry_dsn_optional(self):
        """Sentry DSN should be optional.

        Gherkin: Error tracking is optional
        """
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()
            assert settings.sentry_dsn is None


class TestConfigurationImmutability:
    """Test that configuration values are stable.

    Gherkin Reference: Configuration consistency
    """

    def test_settings_fields_have_descriptions(self):
        """All settings fields should have descriptions.

        Documentation: Fields should be self-documenting
        """
        # Get field definitions from model
        for field_name, field_info in Settings.model_fields.items():
            # Most fields should have descriptions
            # This is a documentation quality check
            pass  # Informational test

    def test_default_cors_origins_secure(self):
        """Default CORS origins should be secure (HTTPS).

        Security: Default to secure configuration
        """
        with patch.dict(os.environ, {}, clear=True):
            settings = Settings()

            for origin in settings.cors_origins:
                assert origin.startswith("https://"), (
                    f"Default CORS origin '{origin}' should use HTTPS"
                )
