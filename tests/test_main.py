"""Tests for main FastAPI application."""

import pytest


class TestHealthEndpoint:
    """Test health check endpoint."""

    def test_health_returns_200(self, client):
        """Health endpoint should return 200 OK."""
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_returns_healthy_status(self, client):
        """Health endpoint should return healthy status."""
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data


class TestApiStatus:
    """Test API status endpoint."""

    def test_api_status_returns_200(self, client):
        """API status endpoint should return 200 OK."""
        response = client.get("/api/status")
        assert response.status_code == 200

    def test_api_status_contains_environment(self, client):
        """API status should contain environment info."""
        response = client.get("/api/status")
        data = response.json()
        assert "environment" in data
        assert "features" in data


class TestHomeRoute:
    """Test home page."""

    def test_home_returns_200(self, client):
        """Home page should return 200 OK."""
        response = client.get("/")
        assert response.status_code == 200

    def test_home_returns_html(self, client):
        """Home page should return HTML."""
        response = client.get("/")
        assert "text/html" in response.headers["content-type"]

    def test_home_contains_title(self, client):
        """Home page should contain LPxGP title."""
        response = client.get("/")
        assert "LPxGP" in response.text


class TestLoginRoute:
    """Test login page."""

    def test_login_returns_200(self, client):
        """Login page should return 200 OK."""
        response = client.get("/login")
        assert response.status_code == 200

    def test_login_contains_form(self, client):
        """Login page should contain a login form."""
        response = client.get("/login")
        assert "email" in response.text
        assert "password" in response.text


class Test404Handler:
    """Test 404 error handling."""

    def test_nonexistent_page_returns_404(self, client):
        """Non-existent page should return 404."""
        response = client.get("/nonexistent-page")
        assert response.status_code == 404

    def test_api_404_returns_json(self, client):
        """API 404 should return JSON."""
        response = client.get("/api/nonexistent")
        assert response.status_code == 404
        assert "application/json" in response.headers["content-type"]
