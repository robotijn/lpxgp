"""Tests for GP Health Dashboard and Mutual Interest detection.

IMPORTANT: Tests are the source of truth. Do NOT modify tests to make them pass.
If a test fails, fix the APPLICATION, not the test.
"""



def login_as_admin(client):
    """Helper to log in as admin user."""
    client.post(
        "/api/auth/login",
        data={"email": "admin@demo.com", "password": "admin123"},
    )


def login_as_gp(client):
    """Helper to log in as GP user."""
    client.post(
        "/api/auth/login",
        data={"email": "gp@demo.com", "password": "demo123"},
    )


# =============================================================================
# GP Health Dashboard Tests
# =============================================================================


class TestGPHealthDashboard:
    """Tests for the GP Health Dashboard page."""

    def test_gp_health_requires_admin(self, client):
        """GP Health dashboard should require admin access."""
        login_as_gp(client)
        response = client.get("/admin/gp-health", follow_redirects=False)
        assert response.status_code == 303  # Redirect to dashboard

    def test_gp_health_accessible_by_admin(self, client):
        """GP Health dashboard should be accessible to admins."""
        login_as_admin(client)
        response = client.get("/admin/gp-health")
        assert response.status_code == 200

    def test_gp_health_returns_html(self, client):
        """GP Health dashboard should return HTML."""
        login_as_admin(client)
        response = client.get("/admin/gp-health")
        assert "text/html" in response.headers["content-type"]

    def test_gp_health_has_title(self, client):
        """GP Health dashboard should have appropriate title."""
        login_as_admin(client)
        response = client.get("/admin/gp-health")
        assert "GP Health" in response.text

    def test_gp_health_has_funnel(self, client):
        """GP Health dashboard should have funnel visualization."""
        login_as_admin(client)
        response = client.get("/admin/gp-health")
        text = response.text
        assert "Funnel" in text or "funnel" in text.lower()

    def test_gp_health_has_recommendations_metric(self, client):
        """GP Health dashboard should show recommendations count."""
        login_as_admin(client)
        response = client.get("/admin/gp-health")
        assert "Recommendation" in response.text

    def test_gp_health_has_meetings_metric(self, client):
        """GP Health dashboard should show meetings count."""
        login_as_admin(client)
        response = client.get("/admin/gp-health")
        assert "Meeting" in response.text

    def test_gp_health_has_commitments_metric(self, client):
        """GP Health dashboard should show commitments count."""
        login_as_admin(client)
        response = client.get("/admin/gp-health")
        assert "Commitment" in response.text or "Committed" in response.text

    def test_gp_health_has_conversion_rates(self, client):
        """GP Health dashboard should show conversion rates."""
        login_as_admin(client)
        response = client.get("/admin/gp-health")
        text = response.text.lower()
        assert "conversion" in text or "%" in response.text

    def test_gp_health_has_mutual_interest_section(self, client):
        """GP Health dashboard should show mutual interest section."""
        login_as_admin(client)
        response = client.get("/admin/gp-health")
        assert "Mutual Interest" in response.text

    def test_gp_health_has_period_filter(self, client):
        """GP Health dashboard should have period filter."""
        login_as_admin(client)
        response = client.get("/admin/gp-health")
        assert "30" in response.text  # 30 days option

    def test_gp_health_accepts_period_parameter(self, client):
        """GP Health dashboard should accept period parameter."""
        login_as_admin(client)
        response = client.get("/admin/gp-health?period=90d")
        assert response.status_code == 200

    def test_gp_health_has_top_gps_section(self, client):
        """GP Health dashboard should show top performing GPs."""
        login_as_admin(client)
        response = client.get("/admin/gp-health")
        text = response.text
        assert "Top" in text and "GP" in text

    def test_gp_health_has_bottleneck_analysis(self, client):
        """GP Health dashboard should show bottleneck analysis."""
        login_as_admin(client)
        response = client.get("/admin/gp-health")
        assert "Bottleneck" in response.text


# =============================================================================
# Mutual Interest Detection Tests
# =============================================================================


class TestMutualInterestDetection:
    """Tests for mutual interest detection functionality."""

    def test_shortlist_module_has_watchlist(self):
        """Shortlist module should have watchlist support."""
        from src.shortlists import get_lp_watchlist

        watchlist = get_lp_watchlist("test-user")
        assert isinstance(watchlist, list)

    def test_shortlist_module_has_mutual_interest(self):
        """Shortlist module should have mutual interest model."""
        from src.shortlists import MutualInterest

        mi = MutualInterest(
            lp_id="lp-001",
            lp_name="Test LP",
            gp_id="gp-001",
            gp_name="Test GP",
            fund_id="fund-001",
            fund_name="Test Fund",
            detected_at="2024-01-01T00:00:00Z",
        )
        assert mi.lp_id == "lp-001"
        assert mi.fund_name == "Test Fund"

    def test_add_to_watchlist(self):
        """Should be able to add funds to watchlist."""
        from src.shortlists import WatchlistItem, _watchlists, add_to_watchlist

        # Clear any existing watchlist
        _watchlists.clear()

        item = WatchlistItem(fund_id="fund-test", gp_id="gp-test")
        result = add_to_watchlist("lp-user-test", item)

        assert result.fund_id == "fund-test"
        assert result.added_at != ""

    def test_is_fund_in_watchlist(self):
        """Should detect if fund is in watchlist."""
        from src.shortlists import (
            WatchlistItem,
            _watchlists,
            add_to_watchlist,
            is_fund_in_watchlist,
        )

        _watchlists.clear()

        item = WatchlistItem(fund_id="fund-check", gp_id="gp-check")
        add_to_watchlist("lp-user-check", item)

        assert is_fund_in_watchlist("lp-user-check", "fund-check") is True
        assert is_fund_in_watchlist("lp-user-check", "fund-other") is False

    def test_detect_mutual_interests(self):
        """Should detect mutual interests correctly."""
        from src.shortlists import (
            ShortlistItem,
            WatchlistItem,
            detect_mutual_interests,
        )

        # GP shortlists LP
        gp_shortlists = {
            "gp-user-1": [ShortlistItem(lp_id="lp-org-1", fund_id="fund-1")]
        }

        # LP watches GP's fund
        lp_watchlists = {
            "lp-user-1": [WatchlistItem(fund_id="fund-1", gp_id="gp-org-1")]
        }

        lp_info = {"lp-user-1": {"name": "Test LP", "lp_id": "lp-org-1"}}
        gp_info = {"gp-user-1": {"name": "Test GP", "gp_id": "gp-org-1"}}
        fund_info = {"fund-1": {"name": "Test Fund", "gp_id": "gp-org-1"}}

        results = detect_mutual_interests(
            gp_shortlists, lp_watchlists, lp_info, gp_info, fund_info
        )

        assert len(results) == 1
        assert results[0].lp_name == "Test LP"
        assert results[0].gp_name == "Test GP"
        assert results[0].fund_name == "Test Fund"

    def test_no_mutual_interest_when_no_match(self):
        """Should return empty when no mutual interest."""
        from src.shortlists import (
            ShortlistItem,
            WatchlistItem,
            detect_mutual_interests,
        )

        # GP shortlists LP
        gp_shortlists = {
            "gp-user-1": [ShortlistItem(lp_id="lp-org-1", fund_id="fund-1")]
        }

        # LP watches different GP's fund
        lp_watchlists = {
            "lp-user-1": [WatchlistItem(fund_id="fund-2", gp_id="gp-org-2")]
        }

        lp_info = {"lp-user-1": {"name": "Test LP", "lp_id": "lp-org-1"}}
        gp_info = {"gp-user-1": {"name": "Test GP", "gp_id": "gp-org-1"}}
        fund_info = {
            "fund-1": {"name": "Test Fund 1", "gp_id": "gp-org-1"},
            "fund-2": {"name": "Test Fund 2", "gp_id": "gp-org-2"},
        }

        results = detect_mutual_interests(
            gp_shortlists, lp_watchlists, lp_info, gp_info, fund_info
        )

        assert len(results) == 0


class TestMutualInterestBadge:
    """Tests for mutual interest badge partial."""

    def test_badge_partial_exists(self):
        """Mutual interest badge partial should exist."""
        from pathlib import Path

        badge_path = Path("src/templates/partials/mutual-interest-badge.html")
        assert badge_path.exists()

    def test_gp_health_shows_mutual_interests(self, client):
        """GP Health should show mutual interest items."""
        login_as_admin(client)
        response = client.get("/admin/gp-health")
        # Should show at least the mock mutual interests
        assert "CalPERS" in response.text or "Mutual Interest" in response.text
