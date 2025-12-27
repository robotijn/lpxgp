"""Tests for admin dashboard and management pages.

IMPORTANT: Tests are the source of truth. Do NOT modify tests to make them pass.
If a test fails, fix the APPLICATION, not the test.

Based on BDD Gherkin specs from docs/prd/tests/*.feature.md

Test Categories:
- Admin authentication and authorization
- Admin dashboard content
- User management
- System health monitoring
- Admin API endpoints
- Admin navigation
- Edge cases and error handling
"""



# =============================================================================
# ADMIN DASHBOARD TESTS
# Gherkin Reference: F-ADMIN-01 - F-ADMIN-07
# =============================================================================


class TestAdminDashboardAuth:
    """Test admin dashboard authentication and authorization.

    Gherkin Reference: F-ADMIN-01: Admin Access Control
    """

    def test_admin_dashboard_requires_auth(self, client):
        """Admin dashboard should redirect unauthenticated users to login."""
        response = client.get("/admin", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/login"

    def test_admin_dashboard_requires_admin_role(self, client):
        """Admin dashboard should redirect non-admin users to dashboard."""
        # Login as GP (not admin)
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/admin", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/dashboard"

    def test_admin_dashboard_accessible_to_admin(self, client):
        """Admin dashboard should be accessible to admin users."""
        # Login as admin
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin")
        assert response.status_code == 200
        assert "Platform Dashboard" in response.text


class TestAdminDashboardContent:
    """Test admin dashboard content.

    Gherkin Reference: F-ADMIN-02: Platform Overview
    """

    def test_admin_dashboard_shows_stats(self, client):
        """Admin dashboard should display platform statistics."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin")
        assert "Companies" in response.text
        assert "Total Users" in response.text
        assert "LP Database" in response.text
        assert "Matches Generated" in response.text

    def test_admin_dashboard_shows_health_status(self, client):
        """Admin dashboard should show system health summary."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin")
        assert "System Health" in response.text

    def test_admin_dashboard_shows_admin_badge(self, client):
        """Admin dashboard should show Admin badge in header."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin")
        assert "Admin" in response.text


class TestAdminUsersPage:
    """Test admin users management page.

    Gherkin Reference: F-ADMIN-03: User Management
    """

    def test_admin_users_requires_auth(self, client):
        """Admin users page should require authentication."""
        response = client.get("/admin/users", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/login"

    def test_admin_users_requires_admin_role(self, client):
        """Admin users page should require admin role."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/admin/users", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/dashboard"

    def test_admin_users_accessible_to_admin(self, client):
        """Admin users page should be accessible to admins."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/users")
        assert response.status_code == 200
        assert "Users" in response.text

    def test_admin_users_lists_registered_users(self, client):
        """Admin users page should list registered users."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/users")
        # Demo users should be listed
        assert "gp@demo.com" in response.text or "Demo GP" in response.text

    def test_admin_users_shows_user_roles(self, client):
        """Admin users page should display user roles."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/users")
        # Should show role badges
        assert "GP" in response.text or "Admin" in response.text


class TestAdminHealthPage:
    """Test admin system health page.

    Gherkin Reference: F-ADMIN-04: System Health Monitoring
    """

    def test_admin_health_requires_auth(self, client):
        """Admin health page should require authentication."""
        response = client.get("/admin/health", follow_redirects=False)
        assert response.status_code == 303
        assert response.headers["location"] == "/login"

    def test_admin_health_requires_admin_role(self, client):
        """Admin health page should require admin role."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/admin/health", follow_redirects=False)
        assert response.status_code == 303

    def test_admin_health_accessible_to_admin(self, client):
        """Admin health page should be accessible to admins."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/health")
        assert response.status_code == 200
        assert "System Health" in response.text

    def test_admin_health_shows_database_status(self, client):
        """Admin health page should show database status."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/health")
        assert "Database" in response.text

    def test_admin_health_shows_auth_status(self, client):
        """Admin health page should show authentication status."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/health")
        assert "Authentication" in response.text


class TestAdminStatsApi:
    """Test admin stats API endpoint.

    Gherkin Reference: F-ADMIN-05: Admin API
    """

    def test_admin_stats_requires_auth(self, client):
        """Admin stats API should require authentication."""
        response = client.get("/api/admin/stats")
        assert response.status_code == 401

    def test_admin_stats_requires_admin_role(self, client):
        """Admin stats API should require admin role."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/api/admin/stats")
        assert response.status_code == 403
        assert "Admin access required" in response.json()["error"]

    def test_admin_stats_returns_data(self, client):
        """Admin stats API should return platform statistics."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/api/admin/stats")
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "stats" in data
        assert "companies" in data["stats"]
        assert "users" in data["stats"]
        assert "lps" in data["stats"]
        assert "matches" in data["stats"]

    def test_admin_stats_users_count(self, client):
        """Admin stats should include correct user count."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/api/admin/stats")
        data = response.json()
        # Should have at least the demo users
        assert data["stats"]["users"] >= 3  # gp, lp, admin


class TestAdminNavigation:
    """Test admin navigation consistency.

    Gherkin Reference: F-ADMIN-06: Admin Navigation
    """

    def test_admin_dashboard_has_navigation(self, client):
        """Admin dashboard should have navigation links."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin")
        assert "/admin/users" in response.text
        assert "/admin/health" in response.text
        assert "/dashboard" in response.text

    def test_admin_pages_have_back_to_app_link(self, client):
        """Admin pages should have link back to main app."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin")
        assert "Back to App" in response.text


class TestAdminEdgeCases:
    """Test admin edge cases and error handling.

    Gherkin Reference: F-ADMIN-07: Admin Edge Cases
    """

    def test_admin_api_returns_json_on_error(self, client):
        """Admin API should return JSON error responses."""
        response = client.get("/api/admin/stats")
        assert "application/json" in response.headers["content-type"]
        assert "error" in response.json()

    def test_admin_pages_show_empty_state(self, client):
        """Admin pages should handle empty data gracefully."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin")
        # Should render without errors even with 0 counts
        assert response.status_code == 200


# =============================================================================
# NEW ADMIN PAGE TESTS (Phase 3)
# =============================================================================


class TestAdminDataHealth:
    """Tests for admin data health page (/admin/data-health).

    Gherkin Reference: F-ADMIN-08: Data Health Dashboard
    """

    def test_data_health_page_returns_200(self, client):
        """Data health page should return 200 OK for admin."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/data-health")
        assert response.status_code == 200

    def test_data_health_page_returns_html(self, client):
        """Data health page should return HTML."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/data-health")
        assert "text/html" in response.headers["content-type"]

    def test_data_health_page_has_title(self, client):
        """Data health page should have appropriate title."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/data-health")
        assert "Data Health" in response.text

    def test_data_health_shows_quality_metrics(self, client):
        """Data health page should show quality metrics."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/data-health")
        text = response.text.lower()
        assert "quality" in text or "score" in text or "health" in text


class TestAdminActivityLogs:
    """Tests for admin activity logs page (/admin/activity).

    Gherkin Reference: F-ADMIN-09: Activity Logs
    """

    def test_activity_logs_page_returns_200(self, client):
        """Activity logs page should return 200 OK for admin."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/activity")
        assert response.status_code == 200

    def test_activity_logs_page_returns_html(self, client):
        """Activity logs page should return HTML."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/activity")
        assert "text/html" in response.headers["content-type"]

    def test_activity_logs_page_has_title(self, client):
        """Activity logs page should have appropriate title."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/activity")
        assert "Activity" in response.text


class TestAdminSettings:
    """Tests for admin settings page (/admin/settings).

    Gherkin Reference: F-ADMIN-10: System Settings
    """

    def test_settings_page_returns_200(self, client):
        """Settings page should return 200 OK for admin."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/settings")
        assert response.status_code == 200

    def test_settings_page_returns_html(self, client):
        """Settings page should return HTML."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/settings")
        assert "text/html" in response.headers["content-type"]

    def test_settings_page_has_title(self, client):
        """Settings page should have appropriate title."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/settings")
        assert "Settings" in response.text

    def test_settings_page_has_form_elements(self, client):
        """Settings page should have form elements."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/settings")
        text = response.text.lower()
        assert "save" in text or "form" in text or "input" in text


class TestAdminPeople:
    """Tests for admin people page (/admin/people).

    Gherkin Reference: F-ADMIN-11: People Management
    """

    def test_people_page_returns_200(self, client):
        """People page should return 200 OK for admin."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/people")
        assert response.status_code == 200

    def test_people_page_returns_html(self, client):
        """People page should return HTML."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/people")
        assert "text/html" in response.headers["content-type"]

    def test_people_page_has_title(self, client):
        """People page should have appropriate title."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/people")
        assert "People" in response.text

    def test_people_page_has_stats(self, client):
        """People page should have statistics."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/people")
        text = response.text.lower()
        assert "total" in text or "contacts" in text

    def test_people_page_has_add_button(self, client):
        """People page should have add person button."""
        client.post(
            "/api/auth/login",
            data={"email": "admin@demo.com", "password": "admin123"},
        )
        response = client.get("/admin/people")
        text = response.text
        assert "Add Person" in text or "Add" in text


class TestAdminNewPagesAccessControl:
    """Access control tests for new admin pages.

    Ensures non-admin users are redirected from admin pages.
    """

    def test_data_health_redirects_gp_user(self, client):
        """Data health page should redirect GP user to dashboard."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/admin/data-health", follow_redirects=False)
        assert response.status_code == 303

    def test_activity_logs_redirects_gp_user(self, client):
        """Activity logs page should redirect GP user to dashboard."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/admin/activity", follow_redirects=False)
        assert response.status_code == 303

    def test_settings_redirects_gp_user(self, client):
        """Settings page should redirect GP user to dashboard."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/admin/settings", follow_redirects=False)
        assert response.status_code == 303

    def test_people_allows_gp_user(self, client):
        """People page should allow GP user (GPs can manage data)."""
        client.post(
            "/api/auth/login",
            data={"email": "gp@demo.com", "password": "demo123"},
        )
        response = client.get("/admin/people")
        # GP users are allowed to manage people data
        assert response.status_code == 200

    def test_people_redirects_lp_user(self, client):
        """People page should redirect LP user to dashboard."""
        client.post(
            "/api/auth/login",
            data={"email": "lp@demo.com", "password": "demo123"},
        )
        response = client.get("/admin/people", follow_redirects=False)
        assert response.status_code == 303
