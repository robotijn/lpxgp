"""Application configuration with validation.

This module provides centralized configuration management for the LPxGP
application using Pydantic Settings. Configuration values are loaded from
environment variables and .env files with full type validation.

Features:
    - Environment-based configuration (development, staging, production)
    - Automatic .env file loading
    - Type validation and coercion
    - Computed properties for derived settings
    - Startup validation with fail-fast behavior

Example:
    Basic usage::

        from src.config import get_settings

        settings = get_settings()
        if settings.database_configured:
            # Use database connection
            conn = connect(settings.database_url)

Environment Variables:
    DATABASE_URL: PostgreSQL connection string
    ENVIRONMENT: One of 'development', 'staging', 'production'
    DEBUG: Enable debug mode (default: False)
    OPENROUTER_API_KEY: API key for OpenRouter LLM service
    VOYAGE_API_KEY: API key for Voyage AI embeddings

Note:
    Settings are cached via lru_cache. Call get_settings.cache_clear()
    if you need to reload settings at runtime (testing only).
"""

from __future__ import annotations

from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict

# =============================================================================
# Type Aliases
# =============================================================================

Environment = Literal["development", "staging", "production"]
"""Valid environment names for deployment."""


# =============================================================================
# Settings Class
# =============================================================================


class Settings(BaseSettings):
    """Application settings with validation.

    Loads configuration from environment variables and .env files.
    All fields have sensible defaults for local development.

    Attributes:
        database_url: PostgreSQL connection URL. None means no database.
        environment: Deployment environment (development/staging/production).
        debug: Enable debug mode. Must be False in production.
        openrouter_api_key: API key for OpenRouter LLM calls.
        voyage_api_key: API key for Voyage AI embeddings.
        ollama_base_url: Base URL for local Ollama instance.
        ollama_model: Default Ollama model for AI agents.
        langfuse_public_key: Langfuse public key for monitoring.
        langfuse_secret_key: Langfuse secret key for monitoring.
        langfuse_host: Langfuse API host URL.
        sentry_dsn: Sentry DSN for error tracking.
        cors_origins: List of allowed CORS origins.
        rate_limit_default: Default rate limit string (e.g., "100/minute").
        session_timeout_minutes: Session expiration time in minutes.
        max_login_attempts: Failed login attempts before lockout.
        lockout_duration_minutes: Account lockout duration.
        max_file_upload_mb: Maximum file upload size in megabytes.
        allowed_upload_extensions: Allowed file extensions for uploads.
        max_export_rows: Maximum rows in CSV exports.
        enable_semantic_search: Feature flag for semantic search.
        enable_agent_matching: Feature flag for AI agent matching.

    Example:
        >>> settings = Settings()
        >>> print(settings.environment)
        'development'
        >>> print(settings.is_production)
        False
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # =========================================================================
    # Database Settings (IMPORTANT: Separate test and production!)
    # =========================================================================

    database_url: str | None = Field(
        default=None,
        description="PRODUCTION PostgreSQL connection URL - NEVER use for testing!",
    )
    """PRODUCTION database connection URL. Protected from test operations."""

    test_database_url: str | None = Field(
        default=None,
        description="TEST PostgreSQL connection URL - safe to reset/delete",
    )
    """TEST database connection URL. Can be safely reset, truncated, or deleted."""

    # =========================================================================
    # Environment Settings
    # =========================================================================

    environment: Environment = Field(
        default="development",
        description="Deployment environment",
    )
    """Current deployment environment. Controls security and feature settings."""

    debug: bool = Field(
        default=False,
        description="Enable debug mode",
    )
    """Debug mode flag. Must be False in production."""

    # =========================================================================
    # API Keys
    # =========================================================================

    openrouter_api_key: str | None = Field(
        default=None,
        description="OpenRouter API key (M3+)",
    )
    """API key for OpenRouter LLM service. Required for AI agent features."""

    voyage_api_key: str | None = Field(
        default=None,
        description="Voyage AI API key (M2+)",
    )
    """API key for Voyage AI embeddings. Required for semantic search."""

    # =========================================================================
    # Ollama Configuration (Local Development)
    # =========================================================================

    ollama_base_url: str = Field(
        default="http://localhost:11434",
        description="Ollama API base URL",
    )
    """Base URL for local Ollama instance."""

    ollama_model: str = Field(
        default="deepseek-r1:8b",
        description="Default Ollama model for agents",
    )
    """Default model to use for Ollama-based AI features."""

    # =========================================================================
    # Langfuse Monitoring (M3+)
    # =========================================================================

    langfuse_public_key: str | None = Field(
        default=None,
        description="Langfuse public key for monitoring",
    )
    """Langfuse public key for LLM observability."""

    langfuse_secret_key: str | None = Field(
        default=None,
        description="Langfuse secret key for monitoring",
    )
    """Langfuse secret key for LLM observability."""

    langfuse_host: str = Field(
        default="https://cloud.langfuse.com",
        description="Langfuse API host",
    )
    """Langfuse API host URL."""

    # =========================================================================
    # Error Tracking
    # =========================================================================

    sentry_dsn: str | None = Field(
        default=None,
        description="Sentry DSN for error tracking",
    )
    """Sentry DSN for error tracking. Recommended for production."""

    # =========================================================================
    # Security Settings
    # =========================================================================

    cors_origins: list[str] = Field(
        default=["https://lpxgp.com", "https://www.lpxgp.com"],
        description="Allowed CORS origins",
    )
    """List of allowed CORS origins. Add localhost for development."""

    rate_limit_default: str = Field(
        default="100/minute",
        description="Default rate limit (requests/period)",
    )
    """Default rate limit string in format 'count/period'."""

    session_timeout_minutes: int = Field(
        default=60,
        ge=5,
        le=1440,
        description="Session timeout in minutes",
    )
    """Session expiration time. Range: 5-1440 minutes."""

    max_login_attempts: int = Field(
        default=5,
        ge=3,
        le=10,
        description="Max failed login attempts before lockout",
    )
    """Number of failed login attempts before account lockout."""

    lockout_duration_minutes: int = Field(
        default=30,
        ge=5,
        le=1440,
        description="Account lockout duration in minutes",
    )
    """Duration of account lockout after max failed attempts."""

    # =========================================================================
    # File Upload Settings
    # =========================================================================

    max_file_upload_mb: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum file upload size in MB",
    )
    """Maximum allowed file upload size in megabytes."""

    allowed_upload_extensions: list[str] = Field(
        default=[".pdf", ".pptx", ".ppt"],
        description="Allowed file extensions for uploads",
    )
    """List of allowed file extensions for uploads."""

    # =========================================================================
    # Export Settings
    # =========================================================================

    max_export_rows: int = Field(
        default=500,
        ge=100,
        le=10000,
        description="Maximum rows in CSV export",
    )
    """Maximum number of rows allowed in CSV exports."""

    # =========================================================================
    # Feature Flags
    # =========================================================================

    enable_semantic_search: bool = Field(
        default=False,
        description="Enable semantic search (requires Voyage AI key)",
    )
    """Feature flag for semantic search. Requires voyage_api_key."""

    enable_agent_matching: bool = Field(
        default=False,
        description="Enable AI agent matching (requires OpenRouter key)",
    )
    """Feature flag for AI agent matching. Requires openrouter_api_key."""

    # =========================================================================
    # Validators
    # =========================================================================

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, v: str | None) -> str | None:
        """Validate PostgreSQL database URL format.

        Args:
            v: Database URL string or None.

        Returns:
            Validated URL or None.

        Raises:
            ValueError: If URL doesn't start with postgresql:// or postgres://
        """
        if v is None or v.strip() == "":
            return None
        if not v.startswith(("postgresql://", "postgres://")):
            raise ValueError(
                "Database URL must start with postgresql:// or postgres://"
            )
        return v

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v: list[str]) -> list[str]:
        """Validate CORS origins have valid URL schemes.

        Args:
            v: List of CORS origin URLs.

        Returns:
            Validated list of origins.

        Raises:
            ValueError: If any origin doesn't start with http:// or https://
        """
        for origin in v:
            if not origin.startswith(("http://", "https://")):
                raise ValueError(f"Invalid CORS origin: {origin}")
        return v

    # =========================================================================
    # Computed Properties
    # =========================================================================

    @property
    def database_configured(self) -> bool:
        """Check if any database is configured.

        Returns:
            True if database_url or test_database_url is set.
        """
        return self.database_url is not None or self.test_database_url is not None

    @property
    def is_production(self) -> bool:
        """Check if running in production environment.

        Returns:
            True if environment is 'production', False otherwise.
        """
        return self.environment == "production"

    @property
    def is_test_mode(self) -> bool:
        """Check if running in test mode.

        Test mode is detected by:
        1. PYTEST_CURRENT_TEST env var (set by pytest)
        2. Environment is 'development' and test_database_url is set

        Returns:
            True if in test mode, False otherwise.
        """
        import os
        return bool(os.environ.get("PYTEST_CURRENT_TEST"))

    @property
    def active_database_url(self) -> str | None:
        """Get the appropriate database URL based on context.

        SAFETY: In test mode or when explicitly requested, returns test_database_url.
        In production mode, returns database_url.

        Returns:
            The appropriate database URL for the current context.
        """
        import os

        # If pytest is running, ALWAYS use test database
        if os.environ.get("PYTEST_CURRENT_TEST"):
            return self.test_database_url

        # If USE_TEST_DATABASE env var is set, use test database
        if os.environ.get("USE_TEST_DATABASE", "").lower() in ("1", "true", "yes"):
            return self.test_database_url

        # In production, use production database
        if self.is_production:
            return self.database_url

        # In development without explicit test mode, prefer test_database_url if set
        # This provides an extra safety layer
        return self.test_database_url or self.database_url

    @property
    def test_database_configured(self) -> bool:
        """Check if test database is configured.

        Returns:
            True if test_database_url is set, False otherwise.
        """
        return self.test_database_url is not None

    @property
    def production_database_configured(self) -> bool:
        """Check if production database is configured.

        Returns:
            True if database_url is set, False otherwise.
        """
        return self.database_url is not None

    @property
    def max_file_upload_bytes(self) -> int:
        """Get maximum file upload size in bytes.

        Returns:
            max_file_upload_mb converted to bytes.
        """
        return self.max_file_upload_mb * 1024 * 1024


# =============================================================================
# Settings Factory
# =============================================================================


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Settings are loaded once and cached for performance.
    Use get_settings.cache_clear() to reload settings (testing only).

    Returns:
        Cached Settings instance.

    Example:
        >>> settings = get_settings()
        >>> print(settings.environment)
        'development'
    """
    return Settings()


# =============================================================================
# Startup Validation
# =============================================================================


def validate_settings_on_startup() -> None:
    """Validate all settings on application startup.

    Performs additional validation beyond Pydantic's built-in validation:
        - Production requires Sentry DSN (warning if missing)
        - Production requires debug=False
        - Production cannot have localhost in CORS origins
        - Feature flags require corresponding API keys

    Call this function early in your main.py to fail fast if
    configuration is invalid.

    Raises:
        ValueError: If configuration is invalid for the environment.

    Example:
        >>> # In main.py
        >>> from src.config import validate_settings_on_startup
        >>> validate_settings_on_startup()
        Configuration validated for environment: development
    """
    try:
        settings = get_settings()

        # Production-specific validations
        if settings.is_production:
            # Warn about missing Sentry
            if not settings.sentry_dsn:
                print("WARNING: Sentry DSN not configured for production")

            # Debug must be disabled
            if settings.debug:
                raise ValueError("Debug mode must be disabled in production")

            # No localhost in CORS
            if "localhost" in str(settings.cors_origins):
                raise ValueError(
                    "localhost not allowed in CORS origins for production"
                )

        # Feature flag dependency validation
        if settings.enable_semantic_search and not settings.voyage_api_key:
            raise ValueError(
                "Voyage AI key required when semantic search is enabled"
            )

        if settings.enable_agent_matching and not settings.openrouter_api_key:
            raise ValueError(
                "OpenRouter key required when agent matching is enabled"
            )

        print(f"Configuration validated for environment: {settings.environment}")

    except Exception as e:
        print(f"FATAL: Configuration validation failed: {e}")
        raise
