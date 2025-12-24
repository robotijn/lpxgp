"""Application configuration with validation."""

import os
from functools import lru_cache
from typing import Literal

from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Application settings with validation.

    All required settings will raise an error on startup if not configured.
    """

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # -------------------------------------------------------------------------
    # Required Settings (fail fast if missing)
    # -------------------------------------------------------------------------

    # Supabase (optional in development for basic testing)
    supabase_url: str | None = Field(default=None, description="Supabase project URL")
    supabase_anon_key: str | None = Field(default=None, description="Supabase anon/public key")
    supabase_service_role_key: str | None = Field(default=None, description="Supabase service role key (for admin ops)")

    # -------------------------------------------------------------------------
    # Optional Settings with Defaults
    # -------------------------------------------------------------------------

    # Environment
    environment: Literal["development", "staging", "production"] = Field(
        default="development",
        description="Deployment environment",
    )
    debug: bool = Field(default=False, description="Enable debug mode")

    # API Keys (required for specific features)
    openrouter_api_key: str | None = Field(default=None, description="OpenRouter API key (M3+)")
    voyage_api_key: str | None = Field(default=None, description="Voyage AI API key (M2+)")

    # Langfuse (M3+ agent monitoring)
    langfuse_public_key: str | None = Field(default=None)
    langfuse_secret_key: str | None = Field(default=None)
    langfuse_host: str = Field(default="https://cloud.langfuse.com")

    # Sentry (error tracking)
    sentry_dsn: str | None = Field(default=None, description="Sentry DSN for error tracking")

    # -------------------------------------------------------------------------
    # Security Settings
    # -------------------------------------------------------------------------

    # CORS
    cors_origins: list[str] = Field(
        default=["https://lpxgp.com", "https://www.lpxgp.com"],
        description="Allowed CORS origins",
    )

    # Rate Limiting
    rate_limit_default: str = Field(
        default="100/minute",
        description="Default rate limit (requests/period)",
    )

    # Session
    session_timeout_minutes: int = Field(
        default=60,
        ge=5,
        le=1440,
        description="Session timeout in minutes",
    )

    # Account Lockout
    max_login_attempts: int = Field(
        default=5,
        ge=3,
        le=10,
        description="Max failed login attempts before lockout",
    )
    lockout_duration_minutes: int = Field(
        default=30,
        ge=5,
        le=1440,
        description="Account lockout duration in minutes",
    )

    # -------------------------------------------------------------------------
    # File Upload Settings
    # -------------------------------------------------------------------------

    max_file_upload_mb: int = Field(
        default=50,
        ge=1,
        le=100,
        description="Maximum file upload size in MB",
    )
    allowed_upload_extensions: list[str] = Field(
        default=[".pdf", ".pptx", ".ppt"],
        description="Allowed file extensions for uploads",
    )

    # -------------------------------------------------------------------------
    # Export Settings
    # -------------------------------------------------------------------------

    max_export_rows: int = Field(
        default=500,
        ge=100,
        le=10000,
        description="Maximum rows in CSV export",
    )

    # -------------------------------------------------------------------------
    # Feature Flags
    # -------------------------------------------------------------------------

    enable_semantic_search: bool = Field(
        default=False,
        description="Enable semantic search (requires Voyage AI key)",
    )
    enable_agent_matching: bool = Field(
        default=False,
        description="Enable AI agent matching (requires OpenRouter key)",
    )

    # -------------------------------------------------------------------------
    # Validators
    # -------------------------------------------------------------------------

    @field_validator("supabase_url")
    @classmethod
    def validate_supabase_url(cls, v: str | None) -> str | None:
        """Validate Supabase URL format."""
        if v is None:
            return None
        if not v.startswith("https://"):
            raise ValueError("Supabase URL must start with https://")
        if ".supabase.co" not in v and "localhost" not in v:
            raise ValueError("Invalid Supabase URL format")
        return v

    @field_validator("supabase_anon_key", "supabase_service_role_key")
    @classmethod
    def validate_supabase_key(cls, v: str | None) -> str | None:
        """Validate Supabase key format."""
        if v is None:
            return None
        if len(v) < 100:
            raise ValueError("Invalid Supabase key (too short)")
        return v

    @property
    def supabase_configured(self) -> bool:
        """Check if Supabase is fully configured."""
        return all([self.supabase_url, self.supabase_anon_key, self.supabase_service_role_key])

    @field_validator("cors_origins")
    @classmethod
    def validate_cors_origins(cls, v: list[str]) -> list[str]:
        """Validate CORS origins."""
        for origin in v:
            if not origin.startswith(("http://", "https://")):
                raise ValueError(f"Invalid CORS origin: {origin}")
        return v

    # -------------------------------------------------------------------------
    # Computed Properties
    # -------------------------------------------------------------------------

    @property
    def is_production(self) -> bool:
        """Check if running in production."""
        return self.environment == "production"

    @property
    def max_file_upload_bytes(self) -> int:
        """Get max file upload size in bytes."""
        return self.max_file_upload_mb * 1024 * 1024


@lru_cache
def get_settings() -> Settings:
    """Get cached settings instance.

    Raises ValueError on startup if required settings are missing.
    """
    return Settings()


def validate_settings_on_startup() -> None:
    """Validate all settings on application startup.

    Call this in your main.py to fail fast if configuration is invalid.
    """
    try:
        settings = get_settings()

        # Additional startup validations
        if settings.is_production:
            # In production, certain settings must be configured
            if not settings.sentry_dsn:
                print("WARNING: Sentry DSN not configured for production")

            if settings.debug:
                raise ValueError("Debug mode must be disabled in production")

            if "localhost" in str(settings.cors_origins):
                raise ValueError("localhost not allowed in CORS origins for production")

        # Validate feature flag dependencies
        if settings.enable_semantic_search and not settings.voyage_api_key:
            raise ValueError("Voyage AI key required when semantic search is enabled")

        if settings.enable_agent_matching and not settings.openrouter_api_key:
            raise ValueError("OpenRouter key required when agent matching is enabled")

        print(f"Configuration validated for environment: {settings.environment}")

    except Exception as e:
        print(f"FATAL: Configuration validation failed: {e}")
        raise
