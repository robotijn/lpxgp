"""Health and status endpoints for monitoring and load balancers.

This router provides:
- /health: Basic health check (GET and HEAD)
- /api/status: Detailed status with feature flags
"""

from __future__ import annotations

from typing import Any

from fastapi import APIRouter
from fastapi.responses import JSONResponse

from src.config import get_settings

router = APIRouter(tags=["health"])


@router.api_route("/health", methods=["GET", "HEAD"], response_class=JSONResponse)
async def health_check() -> dict[str, str]:
    """Health check endpoint for load balancers and monitoring.

    Returns basic application health status. Supports both GET and HEAD
    methods for efficient health checking by load balancers.

    Returns:
        JSON object with 'status' and 'version' fields.
    """
    return {
        "status": "healthy",
        "version": "0.1.0",
    }


@router.get("/api/status", response_class=JSONResponse)
async def api_status() -> dict[str, Any]:
    """API status with non-sensitive configuration info.

    Returns current environment and feature flag status. Does not expose
    any sensitive configuration values like API keys.

    Returns:
        JSON object with status, environment, and feature flags.
    """
    settings = get_settings()
    return {
        "status": "ok",
        "environment": settings.environment,
        "features": {
            "semantic_search": settings.enable_semantic_search,
            "agent_matching": settings.enable_agent_matching,
        },
    }
