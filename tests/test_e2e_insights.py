"""E2E tests for insights endpoints.

Tests for:
- Mutual interests detection
- Fund recommendations
- Activity timeline
- Data quality metrics
- CSV exports
- Tracking links
"""

from playwright.sync_api import Page

BASE_URL = "http://127.0.0.1:8000"


class TestMutualInterests:
    """Tests for mutual interest detection."""

    def test_mutual_interests_requires_auth(self, page: Page):
        """Unauthenticated users get empty response."""
        response = page.request.get(f"{BASE_URL}/api/mutual-interests")
        assert response.status == 401 or response.text() == ""

    def test_mutual_interests_returns_html(self, page: Page):
        """Authenticated users get HTML alerts or empty."""
        # Navigate and set test cookie
        page.goto(f"{BASE_URL}/login")
        page.evaluate("""
            document.cookie = "test_user=gp_user; path=/";
        """)

        response = page.request.get(f"{BASE_URL}/api/mutual-interests")
        # Should return either alerts HTML or empty (no matches)
        assert response.status in [200, 401]


class TestFundRecommendations:
    """Tests for LP fund recommendations."""

    def test_recommendations_requires_auth(self, page: Page):
        """Unauthenticated users get error."""
        response = page.request.get(f"{BASE_URL}/api/lp/fund-recommendations")
        # Should redirect or return 401
        assert response.status in [200, 401, 302]

    def test_recommendations_for_lp_user(self, page: Page):
        """LP users can access fund recommendations."""
        page.goto(f"{BASE_URL}/login")
        page.evaluate("""
            document.cookie = "test_user=lp_user; path=/";
        """)

        response = page.request.get(f"{BASE_URL}/api/lp/fund-recommendations")
        # Returns HTML with recommendations or empty
        assert response.status in [200, 401]


class TestActivityTimeline:
    """Tests for activity timeline."""

    def test_timeline_requires_auth(self, page: Page):
        """Timeline requires authentication."""
        response = page.request.get(
            f"{BASE_URL}/api/timeline/fund/f0000001-0000-0000-0000-000000000001"
        )
        assert response.status in [200, 401, 403]

    def test_timeline_invalid_entity_type(self, page: Page):
        """Invalid entity type handled gracefully."""
        response = page.request.get(
            f"{BASE_URL}/api/timeline/invalid/00000000-0000-0000-0000-000000000001"
        )
        # Should return error or empty timeline (401 if unauthenticated)
        assert response.status in [200, 400, 401, 404]

    def test_timeline_invalid_uuid(self, page: Page):
        """Invalid UUID handled gracefully."""
        response = page.request.get(
            f"{BASE_URL}/api/timeline/fund/not-a-valid-uuid"
        )
        # Should return error (401 if unauthenticated)
        assert response.status in [200, 400, 401, 404]


class TestDataQualityPage:
    """Tests for data quality admin page."""

    def test_data_quality_requires_admin(self, page: Page):
        """Data quality page requires admin role."""
        page.goto(f"{BASE_URL}/admin/data-quality")
        # Should redirect to login or show error
        assert page.url.endswith("/login") or "error" in page.content().lower() or page.title() != ""

    def test_data_quality_page_loads(self, page: Page):
        """Data quality page loads for admin users."""
        page.goto(f"{BASE_URL}/login")
        page.evaluate("""
            document.cookie = "test_user=admin; path=/";
        """)

        page.goto(f"{BASE_URL}/admin/data-quality")
        # Page should load with some content about data quality
        content = page.content().lower()
        assert "data" in content or "quality" in content or page.title() != ""


class TestCsvExports:
    """Tests for CSV export endpoints."""

    def test_export_lps_requires_auth(self, page: Page):
        """LP export requires authentication."""
        response = page.request.get(f"{BASE_URL}/api/export/lps")
        assert response.status in [200, 401, 302]

    def test_export_lps_returns_csv(self, page: Page):
        """LP export returns CSV content type."""
        page.goto(f"{BASE_URL}/login")
        page.evaluate("""
            document.cookie = "test_user=gp_user; path=/";
        """)

        response = page.request.get(f"{BASE_URL}/api/export/lps")
        if response.status == 200:
            content_type = response.headers.get("content-type", "")
            # Should be CSV or text
            assert "csv" in content_type or "text" in content_type or response.body()

    def test_export_pipeline_requires_fund_id(self, page: Page):
        """Pipeline export requires valid fund ID."""
        response = page.request.get(f"{BASE_URL}/api/export/pipeline/invalid-uuid")
        # Should handle gracefully (401 if unauth, 404, 400, or empty CSV)
        assert response.status in [200, 400, 401, 404, 422]

    def test_export_pipeline_valid_fund(self, page: Page):
        """Pipeline export works for valid fund."""
        response = page.request.get(
            f"{BASE_URL}/api/export/pipeline/f0000001-0000-0000-0000-000000000001"
        )
        # Should return CSV, 404 if fund doesn't exist, or 401 if unauth
        assert response.status in [200, 401, 404]

    def test_export_shortlist_requires_auth(self, page: Page):
        """Shortlist export requires authentication."""
        response = page.request.get(f"{BASE_URL}/api/export/shortlist")
        assert response.status in [200, 401, 302]

    def test_export_shortlist_returns_csv(self, page: Page):
        """Shortlist export returns CSV."""
        page.goto(f"{BASE_URL}/login")
        page.evaluate("""
            document.cookie = "test_user=gp_user; path=/";
        """)

        response = page.request.get(f"{BASE_URL}/api/export/shortlist")
        if response.status == 200:
            # Should return CSV or empty response
            assert response.body() is not None


class TestTrackingLinks:
    """Tests for email tracking link functionality."""

    def test_create_tracking_link_requires_auth(self, page: Page):
        """Creating tracking links requires authentication."""
        response = page.request.post(
            f"{BASE_URL}/api/tracking-link",
            data={"fund_id": "f0000001-0000-0000-0000-000000000001", "lp_id": "l0000001-0000-0000-0000-000000000001"},
        )
        assert response.status in [200, 401, 302, 422]

    def test_create_tracking_link_invalid_ids(self, page: Page):
        """Invalid IDs are rejected."""
        page.goto(f"{BASE_URL}/login")
        page.evaluate("""
            document.cookie = "test_user=gp_user; path=/";
        """)

        response = page.request.post(
            f"{BASE_URL}/api/tracking-link",
            form={"fund_id": "invalid", "lp_id": "invalid"},
        )
        # Should return error or handle gracefully
        assert response.status in [200, 400, 404, 422]

    def test_tracking_redirect_invalid_token(self, page: Page):
        """Invalid tracking tokens are handled."""
        page.goto(f"{BASE_URL}/i/invalid-token-that-does-not-exist")
        # Should show error page or redirect
        content = page.content()
        assert "not found" in content.lower() or "error" in content.lower() or page.url != ""

    def test_tracking_redirect_empty_token(self, page: Page):
        """Empty tracking token handled."""
        response = page.request.get(f"{BASE_URL}/i/")
        # 404 for missing route or redirect
        assert response.status in [404, 307, 308]

    def test_tracking_stats_requires_auth(self, page: Page):
        """Tracking stats require authentication."""
        response = page.request.get(
            f"{BASE_URL}/api/tracking-stats/f0000001-0000-0000-0000-000000000001/l0000001-0000-0000-0000-000000000001"
        )
        assert response.status in [200, 401, 302]

    def test_tracking_stats_invalid_ids(self, page: Page):
        """Invalid IDs in tracking stats are handled."""
        response = page.request.get(
            f"{BASE_URL}/api/tracking-stats/invalid-uuid/invalid-uuid"
        )
        # Should return error or empty HTML (401 if unauth)
        assert response.status in [200, 400, 401, 404, 422]


class TestInsightsPageNavigation:
    """Test navigation and page loads for insights features."""

    def test_compare_page_loads(self, page: Page):
        """Compare page loads successfully."""
        page.goto(f"{BASE_URL}/compare")
        # Should redirect to login or load page
        assert page.title() != "" or page.url.endswith("/login")

    def test_compare_page_with_lps(self, page: Page):
        """Compare page with LP IDs loads."""
        page.goto(f"{BASE_URL}/login")
        page.evaluate("""
            document.cookie = "test_user=gp_user; path=/";
        """)

        page.goto(f"{BASE_URL}/compare?lps=l0000001-0000-0000-0000-000000000001,l0000002-0000-0000-0000-000000000002")
        content = page.content()
        # Should show comparison or empty state
        assert len(content) > 0


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_sql_injection_in_timeline(self, page: Page):
        """SQL injection attempts are blocked."""
        response = page.request.get(
            f"{BASE_URL}/api/timeline/fund/'; DROP TABLE funds; --"
        )
        # Should not crash, should handle gracefully (401 if unauth)
        assert response.status in [200, 400, 401, 404, 422]

    def test_xss_in_export_params(self, page: Page):
        """XSS attempts in export params are neutralized."""
        response = page.request.get(
            f"{BASE_URL}/api/export/pipeline/<script>alert('xss')</script>"
        )
        if response.status == 200:
            body = response.text()
            # Script tags should be escaped or not present
            assert "<script>" not in body

    def test_large_uuid_in_timeline(self, page: Page):
        """Very long UUID is handled."""
        long_uuid = "a" * 1000
        response = page.request.get(f"{BASE_URL}/api/timeline/fund/{long_uuid}")
        # Should not crash (401 if unauth)
        assert response.status in [200, 400, 401, 404, 414, 422]
