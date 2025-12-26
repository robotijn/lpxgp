"""Tests for settings functionality.

IMPORTANT: Tests are the source of truth. Do NOT modify tests to make them pass.
If a test fails, fix the APPLICATION, not the test.

Based on BDD Gherkin specs from docs/prd/tests/*.feature.md

Test Categories:
- Settings page authentication
- Settings page content
- Settings preferences API
- Settings preferences toggle (HTMX)
- User isolation for settings
"""



# =============================================================================
# SETTINGS PAGE TESTS
# =============================================================================


class TestSettingsContent:
    """Test settings page content."""

    def test_settings_shows_user_info(self, client):
        """Settings should display user information."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/settings")
        assert "gp@demo.com" in response.text
        assert "Demo GP User" in response.text

    def test_settings_has_notification_options(self, client):
        """Settings should have notification preferences."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/settings")
        assert "Notifications" in response.text

    def test_settings_has_security_section(self, client):
        """Settings should have security section."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/settings")
        assert "Security" in response.text
        assert "Password" in response.text


class TestSettingsPageAuth:
    """Test settings page authentication requirements.

    Gherkin Reference: F-AUTH-02: Protected Settings Route
    """

    def test_settings_page_requires_auth(self, client):
        """Settings page should redirect unauthenticated users to login."""
        response = client.get("/settings", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/login"

    def test_settings_page_accessible_when_authenticated(self, client):
        """Settings page should be accessible when authenticated."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/settings")
        assert response.status_code == 200
        assert "Settings" in response.text


class TestSettingsPageContent:
    """Test settings page content.

    Gherkin Reference: F-SETTINGS-01: User Profile Display
    """

    def test_settings_page_shows_user_name(self, client):
        """Settings page should display user's name."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/settings")
        assert "Demo GP" in response.text

    def test_settings_page_shows_user_email(self, client):
        """Settings page should display user's email."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/settings")
        assert "gp@demo.com" in response.text

    def test_settings_page_shows_notification_preferences(self, client):
        """Settings page should show notification preferences section."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/settings")
        assert "Notifications" in response.text
        assert "Email me about new LP matches" in response.text


class TestSettingsPreferencesApi:
    """Test settings preferences API endpoints.

    Gherkin Reference: F-SETTINGS-02: Notification Preferences
    """

    def test_get_preferences_requires_auth(self, client):
        """GET /api/settings/preferences should require authentication."""
        response = client.get("/api/settings/preferences")
        assert response.status_code == 401

    def test_get_preferences_returns_defaults(self, client):
        """GET /api/settings/preferences should return default preferences."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/api/settings/preferences")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "preferences" in data
        # Default values
        assert data["preferences"]["email_new_matches"] is True
        assert data["preferences"]["email_weekly_summary"] is True
        assert data["preferences"]["email_marketing"] is False

    def test_update_preferences_requires_auth(self, client):
        """PUT /api/settings/preferences should require authentication."""
        response = client.put(
            "/api/settings/preferences",
            json={"email_new_matches": False},
        )
        assert response.status_code == 401

    def test_update_preferences_success(self, client):
        """PUT /api/settings/preferences should update preferences."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.put(
            "/api/settings/preferences",
            json={
                "email_new_matches": False,
                "email_weekly_summary": True,
                "email_marketing": True,
            },
        )
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["preferences"]["email_new_matches"] is False
        assert data["preferences"]["email_marketing"] is True

    def test_preferences_persist_across_requests(self, client):
        """Preferences should persist across requests."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Update preferences
        client.put(
            "/api/settings/preferences",
            json={
                "email_new_matches": False,
                "email_weekly_summary": False,
                "email_marketing": True,
            },
        )
        # Verify they persist
        response = client.get("/api/settings/preferences")
        data = response.json()
        assert data["preferences"]["email_new_matches"] is False
        assert data["preferences"]["email_weekly_summary"] is False
        assert data["preferences"]["email_marketing"] is True


class TestSettingsPreferencesToggle:
    """Test settings preferences toggle endpoint (HTMX).

    Gherkin Reference: F-SETTINGS-03: Toggle Preferences
    """

    def test_toggle_preference_requires_auth(self, client):
        """Toggle preference should require authentication."""
        response = client.post("/api/settings/preferences/toggle/email_new_matches")
        assert response.status_code == 401

    def test_toggle_preference_invalid_name(self, client):
        """Toggle should reject invalid preference names."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.post("/api/settings/preferences/toggle/invalid_pref")
        assert response.status_code == 400
        assert "Invalid preference" in response.text

    def test_toggle_preference_email_new_matches(self, client):
        """Toggle email_new_matches should flip the value."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Default is True, toggle should make it False
        response = client.post("/api/settings/preferences/toggle/email_new_matches")
        assert response.status_code == 200
        assert "checkbox" in response.text
        # Should now be unchecked (no 'checked' attribute)

        # Verify the preference actually changed
        prefs_response = client.get("/api/settings/preferences")
        assert prefs_response.json()["preferences"]["email_new_matches"] is False

    def test_toggle_preference_returns_html(self, client):
        """Toggle should return HTML checkbox for HTMX swap."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.post("/api/settings/preferences/toggle/email_weekly_summary")
        assert "text/html" in response.headers["content-type"]
        assert "input" in response.text
        assert "checkbox" in response.text

    def test_toggle_multiple_times(self, client):
        """Toggle should alternate between True and False."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        # Default is False for marketing
        prefs = client.get("/api/settings/preferences").json()
        assert prefs["preferences"]["email_marketing"] is False

        # Toggle once -> True
        client.post("/api/settings/preferences/toggle/email_marketing")
        prefs = client.get("/api/settings/preferences").json()
        assert prefs["preferences"]["email_marketing"] is True

        # Toggle again -> False
        client.post("/api/settings/preferences/toggle/email_marketing")
        prefs = client.get("/api/settings/preferences").json()
        assert prefs["preferences"]["email_marketing"] is False


class TestSettingsUserIsolation:
    """Test settings user isolation.

    Gherkin Reference: F-SETTINGS-04: User Data Isolation
    """

    def test_preferences_isolated_between_users(self, client):
        """Each user should have their own preferences."""
        # User 1: GP
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        client.put(
            "/api/settings/preferences",
            json={
                "email_new_matches": False,
                "email_weekly_summary": False,
                "email_marketing": True,
            },
        )

        # Logout and login as different user
        client.get("/logout")
        client.post(
            "/api/auth/login",
            data={"email": "lp@demo.com", "password": "demo123"},
        )

        # LP user should have default preferences
        response = client.get("/api/settings/preferences")
        prefs = response.json()["preferences"]
        assert prefs["email_new_matches"] is True
        assert prefs["email_weekly_summary"] is True
        assert prefs["email_marketing"] is False
